import fcntl
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class OCRBackend(ABC):
    """Abstract base class for OCR backends."""
    
    @abstractmethod
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            {
                'success': bool,
                'raw_text': str,  # All extracted text
                'metadata': {
                    'backend': str,
                    'model': str (if applicable),
                    'processing_time_seconds': float,
                    'confidence': float (0-1, if available)
                },
                'error': str (if success=False)
            }
        """
        pass



# ---------------------------------------------------------------------------
# Cross-process Ollama concurrency gate
#
# uvicorn runs with --workers 4, so each worker is a separate OS process with
# its own memory space.  A threading.Semaphore is per-process and invisible to
# the other three workers — all four can call Ollama simultaneously, which
# saturates the single T4 GPU and causes every request to time out.
#
# We use a non-blocking exclusive flock on a shared file so that exactly one
# worker process holds the lock at any time.  Workers that cannot acquire it
# immediately return a fast 503 + Retry-After to the caller rather than
# queuing and guaranteeing a timeout.
# ---------------------------------------------------------------------------
_OLLAMA_LOCK_PATH = "/tmp/ollama_inference.lock"


class OllamaOCR(OCRBackend):
    """OCR backend using Ollama vision models with lazy initialization."""
    
    def __init__(self, model: str = "llama3.2-vision", host: str = "http://localhost:11434",
                 timeout: int = 60):
        """
        Initialize Ollama OCR backend.
        
        Initialization does NOT verify Ollama availability - this allows the API
        to start even when Ollama is not ready. Availability is checked lazily
        when extract_text() is called.
        
        Args:
            model: Ollama model name (llama3.2-vision, llava, moondream)
            host: Ollama API host URL
            timeout: Request timeout in seconds passed to the ollama httpx client
        """
        self.model = model
        self.host = host
        self.timeout = timeout
        self._availability_checked = False
        self._is_available = False
        self._availability_error = None
        
        # Build an httpx.Timeout that separates concerns:
        #
        #   connect=10  — fail fast if Ollama isn't reachable at all
        #   read=timeout — how long to wait for the *first* streaming token.
        #
        # llama3.2-vision does substantial image-encoding work before it emits
        # any tokens, so first-token latency on a T4 can be 30-90s depending on
        # VRAM pressure. Using a plain integer timeout applies the same value to
        # every chunk read, which fires prematurely on that initial encoding
        # phase even though the model is working fine. By setting read= to the
        # full configured timeout we preserve the ability to catch a genuinely
        # hung Ollama while not cutting off a legitimately slow first token.
        try:
            import httpx
            import ollama
            self.ollama = ollama
            self._client = ollama.Client(
                host=host,
                timeout=httpx.Timeout(timeout=float(timeout), connect=10.0),
            )
        except ImportError:
            self._is_available = False
            self._availability_error = "ollama Python library not installed. Install with: pip install ollama"
    
    def check_availability(self) -> tuple[bool, Optional[str]]:
        """
        Check if Ollama is running and model is available.
        
        Returns:
            (is_available, error_message) tuple
        """
        import requests
        
        try:
            # Check if Ollama service is running via HTTP API
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            
            if response.status_code != 200:
                return False, f"Ollama not available: HTTP {response.status_code}"
            
            # Check if requested model is downloaded
            models_data = response.json()
            available_models = [m.get('name', '').split(':')[0] for m in models_data.get('models', [])]
            model_base = self.model.split(':')[0]
            
            if model_base not in available_models:
                return False, (
                    f"Model '{self.model}' not found. "
                    f"Available models: {', '.join(available_models) if available_models else 'none'}"
                )
            
            return True, None
                
        except requests.exceptions.RequestException as e:
            return False, f"Cannot connect to Ollama at {self.host}: {str(e)}"
    
    def _ensure_available(self):
        """
        Verify Ollama is available before use.

        Uses the sentinel file /etc/ollama_health/HEALTHY rather than a live
        HTTP call to Ollama. This keeps the verify path consistent with the
        /health endpoint and avoids a second independent availability check
        that could disagree with the cron-managed health state.

        Raises:
            RuntimeError: If the sentinel file is absent (model not in GPU)
        """
        from pathlib import Path
        sentinel = Path("/etc/ollama_health/HEALTHY")
        if not sentinel.exists():
            raise RuntimeError(
                "Ollama model not ready (sentinel /etc/ollama_health/HEALTHY absent — "
                "cron pre-warm pending)"
            )
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Ollama vision model.

        Acquires the module-level semaphore before calling Ollama so that only
        one inference runs at a time.  If the semaphore is already held (another
        request is in progress) this call returns immediately with a transient
        error that callers can surface as HTTP 503 + Retry-After rather than
        letting the request queue up and eventually hit the CloudFront timeout.

        A single automatic retry is attempted on httpx timeout errors because
        Ollama occasionally takes a few extra seconds when the model is in the
        middle of a memory operation; one retry absorbs that without user impact.
        """
        start_time = time.time()

        # --- availability check (sentinel file) ---
        try:
            self._ensure_available()
        except RuntimeError as e:
            return {
                'success': False,
                'error': str(e),
                'metadata': {
                    'backend': 'ollama',
                    'model': self.model,
                    'processing_time_seconds': time.time() - start_time
                }
            }

        # --- cross-process concurrency gate (flock) ---
        # Block waiting for the lock, but only up to _LOCK_WAIT_SECONDS.
        # Under normal conditions inference takes ~10s, so a request that
        # arrives mid-inference needs to wait at most that long.  Capping the
        # wait prevents worker threads from being held indefinitely if Ollama
        # is genuinely stuck — that still returns a clean 503.
        _LOCK_WAIT_SECONDS = 30
        lock_fd = open(_OLLAMA_LOCK_PATH, 'w')
        lock_acquired = False
        lock_deadline = time.time() + _LOCK_WAIT_SECONDS
        while time.time() < lock_deadline:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                lock_acquired = True
                break
            except BlockingIOError:
                time.sleep(0.2)

        if not lock_acquired:
            lock_fd.close()
            logger.warning("Ollama lock wait timed out after %ds", _LOCK_WAIT_SECONDS)
            return {
                'success': False,
                'error': "Ollama is busy. Please retry shortly.",
                'error_type': 'busy',
                'metadata': {
                    'backend': 'ollama',
                    'model': self.model,
                    'processing_time_seconds': time.time() - start_time
                }
            }

        try:
            return self._do_extract(image_path, start_time)
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()

    def _do_extract(self, image_path: str, start_time: float) -> Dict[str, Any]:
        """Inner extraction with timeout classification."""
        try:
            # Verify image exists
            img_path = Path(image_path)
            if not img_path.exists():
                return {
                    'success': False,
                    'error': f"Image not found: {image_path}"
                }

            # Prepare prompt for structured extraction
            prompt = """Extract ALL text from this alcohol beverage label image EXACTLY as it appears.

CRITICAL: Preserve the EXACT capitalization, spacing, and formatting of all text. Do not normalize or change the case of any words.

Please extract and list every piece of text you can see, line by line. Include:
- Brand name (EXACT case)
- Product type/class (e.g., "Bourbon Whiskey", "Pinot Noir", "IPA")
- Alcohol content (e.g., "13.5% alc./vol.", "40% ABV", "80 Proof")
- Net contents/volume (e.g., "750 mL", "12 fl oz")
- Bottler/producer information (e.g., "Bottled by...", "Imported by...", "Produced by...")
- Country of origin (e.g., "Product of France")
- Government warning text (preserve EXACT capitalization - if it says "GOVERNMENT WARNING:" in all caps, write it that way)
- Any other text visible on the label

Format your response as plain text, with each distinct text element on its own line. Do NOT add bullet points, asterisks, or markdown formatting."""

            # Call Ollama using the streaming API with keep_alive=-1.
            #
            # Why streaming:
            #   The non-streaming (blocking) call holds a single HTTP connection
            #   open until the full response is ready.  If our timeout fires and
            #   we close that connection, Ollama does NOT detect the disconnect —
            #   its internal runner keeps the inference running at full GPU
            #   utilisation until it finishes, then tries to write the response
            #   to a socket that no longer exists.  With many requests this
            #   causes the runner to accumulate minutes of backlogged work.
            #
            #   With stream=True, Ollama sends one chunk per generated token.
            #   The moment our side stops reading (timeout, cancelled request,
            #   process exit), the write() on Ollama's side raises a BrokenPipe
            #   and the runner aborts the current inference immediately, freeing
            #   VRAM and the GPU for the next request.
            #
            # Why keep_alive=-1:
            #   Keeps the model resident in VRAM between requests so there is no
            #   20-60s cold-load penalty on every call.  Safe to combine with
            #   streaming because the runner will still abort cleanly on pipe
            #   breaks regardless of the keep_alive setting.
            chunks = []
            for chunk in self._client.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [str(img_path)]
                }],
                options={
                    'temperature': 0.1,
                },
                keep_alive=-1,
                stream=True,
            ):
                chunks.append(chunk['message']['content'])

            extracted_text = ''.join(chunks).strip()
            processing_time = time.time() - start_time

            return {
                'success': True,
                'raw_text': extracted_text,
                'metadata': {
                    'backend': 'ollama',
                    'model': self.model,
                    'processing_time_seconds': processing_time,
                    'confidence': 0.85  # Ollama doesn't provide confidence, use estimate
                }
            }

        except Exception as e:
            # Distinguish timeout/connection errors from logic errors so callers
            # can return the right HTTP status and decide whether to retry.
            err_str = str(e)
            err_type_name = type(e).__name__

            is_timeout = (
                "ReadTimeout" in err_type_name
                or "ConnectTimeout" in err_type_name
                or "TimeoutException" in err_type_name
                or "timeout" in err_str.lower()
            )
            is_connection = (
                "ConnectError" in err_type_name
                or "RemoteProtocolError" in err_type_name
                or "Cannot connect" in err_str
            )

            if is_timeout:
                logger.warning(
                    "Ollama request timed out after %.1fs (limit: %ds) — %s",
                    time.time() - start_time, self.timeout, err_str
                )
                # No automatic retry: a retry sends a fresh request into Ollama's
                # internal queue while the previous one may still be running, which
                # doubles GPU pressure and makes saturation worse, not better.
                return {
                    'success': False,
                    'error': f"Ollama request timed out after {self.timeout}s. Please retry.",
                    'error_type': 'timeout',
                    'metadata': {
                        'backend': 'ollama',
                        'model': self.model,
                        'processing_time_seconds': time.time() - start_time
                    }
                }

            if is_connection:
                logger.error("Ollama connection error: %s", err_str)
                return {
                    'success': False,
                    'error': f"Cannot connect to Ollama at {self.host}: {err_str}",
                    'error_type': 'connection',
                    'metadata': {
                        'backend': 'ollama',
                        'model': self.model,
                        'processing_time_seconds': time.time() - start_time
                    }
                }

            logger.error("Ollama extraction error: %s", err_str, exc_info=True)
            return {
                'success': False,
                'error': f"Ollama extraction error: {err_str}",
                'error_type': 'error',
                'metadata': {
                    'backend': 'ollama',
                    'model': self.model,
                    'processing_time_seconds': time.time() - start_time
                }
            }


def get_ocr_backend(**kwargs) -> OCRBackend:
    """
    Factory function to get OCR backend instance.
    
    Args:
        **kwargs: Additional arguments for OllamaOCR initialization
        
    Returns:
        OllamaOCR instance
        
    Raises:
        RuntimeError: If Ollama is not available
    """
    return OllamaOCR(**kwargs)


# Example usage
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_backends.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        backend = get_ocr_backend()
        result = backend.extract_text(image_path)
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2))
        sys.exit(1)

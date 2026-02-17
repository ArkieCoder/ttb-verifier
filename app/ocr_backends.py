"""
OCR Backend Abstraction Layer

Provides unified interface for different OCR engines:
- OllamaOCR: Uses Ollama vision models (llama3.2-vision, llava)
- TesseractOCR: Uses Tesseract OCR engine (fallback)

All backends return standardized dictionary with extracted text and metadata.
"""

import json
import subprocess
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
import base64


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


class OllamaOCR(OCRBackend):
    """OCR backend using Ollama vision models with lazy initialization."""
    
    def __init__(self, model: str = "llama3.2-vision", host: str = "http://localhost:11434"):
        """
        Initialize Ollama OCR backend.
        
        Initialization does NOT verify Ollama availability - this allows the API
        to start even when Ollama is not ready. Availability is checked lazily
        when extract_text() is called.
        
        Args:
            model: Ollama model name (llama3.2-vision, llava, moondream)
            host: Ollama API host URL
        """
        self.model = model
        self.host = host
        self._availability_checked = False
        self._is_available = False
        self._availability_error = None
        
        # Import ollama library
        try:
            import ollama
            self.ollama = ollama
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
        Verify Ollama is available before use (lazy check).
        
        Raises:
            RuntimeError: If Ollama is not available
        """
        # Check cached availability (don't check repeatedly)
        if self._availability_checked and self._is_available:
            return
        
        # Perform availability check
        self._is_available, self._availability_error = self.check_availability()
        self._availability_checked = True
        
        if not self._is_available:
            raise RuntimeError(self._availability_error)
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Ollama vision model."""
        start_time = time.time()
        
        # Lazy availability check - only verify when actually used
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
        
        try:
            # Verify image exists
            img_path = Path(image_path)
            if not img_path.exists():
                return {
                    'success': False,
                    'error': f"Image not found: {image_path}"
                }
            
            # Prepare prompt for structured extraction
            prompt = """Extract ALL text from this alcohol beverage label image.

Please extract and list every piece of text you can see, maintaining the relative position and formatting. Include:
- Brand name
- Product type/class (e.g., "Bourbon Whiskey", "Pinot Noir", "IPA")
- Alcohol content (e.g., "13.5% alc./vol.", "40% ABV", "80 Proof")
- Net contents/volume (e.g., "750 mL", "12 fl oz")
- Bottler/producer information (e.g., "Bottled by...", "Imported by...", "Produced by...")
- Country of origin (e.g., "Product of France")
- Government warning text (the complete warning statement)
- Any other text visible on the label

Format your response as plain text, with each distinct text element on its own line."""

            # Call Ollama using Python library
            response = self.ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [str(img_path)]
                }],
                options={
                    'temperature': 0.1,  # Low temperature for consistent extraction
                }
            )
            
            extracted_text = response['message']['content'].strip()
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
            return {
                'success': False,
                'error': f"Ollama extraction error: {str(e)}",
                'metadata': {
                    'backend': 'ollama',
                    'model': self.model,
                    'processing_time_seconds': time.time() - start_time
                }
            }


class TesseractOCR(OCRBackend):
    """OCR backend using Tesseract OCR engine."""
    
    def __init__(self, lang: str = "eng"):
        """
        Initialize Tesseract OCR backend.
        
        Args:
            lang: Tesseract language code (default: eng)
        """
        self.lang = lang
        self._verify_tesseract_available()
    
    def _verify_tesseract_available(self):
        """Check if Tesseract is installed."""
        try:
            result = subprocess.run(
                ['tesseract', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                raise RuntimeError("Tesseract not available")
                
        except FileNotFoundError:
            raise RuntimeError(
                "Tesseract not installed. Install with: sudo apt-get install tesseract-ocr"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Tesseract not responding")
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text using Tesseract OCR."""
        start_time = time.time()
        
        try:
            # Verify image exists
            img_path = Path(image_path)
            if not img_path.exists():
                return {
                    'success': False,
                    'error': f"Image not found: {image_path}"
                }
            
            # Run Tesseract
            # Output to stdout, include confidence data
            result = subprocess.run(
                ['tesseract', str(img_path), 'stdout', '-l', self.lang],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': f"Tesseract extraction failed: {result.stderr}",
                    'metadata': {
                        'backend': 'tesseract',
                        'model': f'tesseract-{self.lang}',
                        'processing_time_seconds': time.time() - start_time
                    }
                }
            
            extracted_text = result.stdout.strip()
            processing_time = time.time() - start_time
            
            # Try to get confidence using TSV output
            confidence = self._get_confidence(img_path)
            
            return {
                'success': True,
                'raw_text': extracted_text,
                'metadata': {
                    'backend': 'tesseract',
                    'model': f'tesseract-{self.lang}',
                    'processing_time_seconds': processing_time,
                    'confidence': confidence
                }
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "Tesseract extraction timed out after 10 seconds",
                'metadata': {
                    'backend': 'tesseract',
                    'model': f'tesseract-{self.lang}',
                    'processing_time_seconds': time.time() - start_time
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Tesseract extraction error: {str(e)}",
                'metadata': {
                    'backend': 'tesseract',
                    'model': f'tesseract-{self.lang}',
                    'processing_time_seconds': time.time() - start_time
                }
            }
    
    def _get_confidence(self, image_path: Path) -> float:
        """Get average confidence from Tesseract TSV output."""
        try:
            result = subprocess.run(
                ['tesseract', str(image_path), 'stdout', '-l', self.lang, '--psm', '3', 'tsv'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return 0.5  # Default confidence
            
            # Parse TSV and calculate average confidence
            lines = result.stdout.strip().split('\n')
            confidences = []
            
            for line in lines[1:]:  # Skip header
                parts = line.split('\t')
                if len(parts) >= 11:  # TSV has 12 columns
                    try:
                        conf = float(parts[10])  # Confidence column
                        if conf >= 0:  # Valid confidence
                            confidences.append(conf)
                    except ValueError:
                        continue
            
            if confidences:
                return sum(confidences) / len(confidences) / 100.0  # Normalize to 0-1
            return 0.5
            
        except Exception:
            return 0.5  # Default if confidence extraction fails


def get_ocr_backend(backend_name: str = "ollama", **kwargs) -> OCRBackend:
    """
    Factory function to get OCR backend instance.
    
    Args:
        backend_name: 'ollama' or 'tesseract'
        **kwargs: Additional arguments for backend initialization
        
    Returns:
        OCRBackend instance
        
    Raises:
        ValueError: If backend_name is invalid
        RuntimeError: If backend is not available
    """
    backend_name = backend_name.lower()
    
    if backend_name == "ollama":
        return OllamaOCR(**kwargs)
    elif backend_name == "tesseract":
        return TesseractOCR(**kwargs)
    else:
        raise ValueError(
            f"Invalid backend: {backend_name}. "
            f"Valid options: 'ollama', 'tesseract'"
        )


# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ocr_backends.py <image_path> [backend]")
        print("  backend: 'ollama' (default) or 'tesseract'")
        sys.exit(1)
    
    image_path = sys.argv[1]
    backend_name = sys.argv[2] if len(sys.argv) > 2 else "ollama"
    
    try:
        backend = get_ocr_backend(backend_name)
        result = backend.extract_text(image_path)
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }, indent=2))
        sys.exit(1)

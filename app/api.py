"""
TTB Label Verifier - FastAPI Application

REST API for validating alcohol beverage labels against 27 CFR regulations.
Supports single label verification and batch processing.

Endpoints:
    POST /verify - Single label verification
    POST /verify/batch - Batch label verification
    GET /docs - Swagger UI documentation
    GET /redoc - ReDoc documentation
"""

import json
import logging
import tempfile
import zipfile
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from config import get_settings
from label_validator import LabelValidator
from auth import get_current_user
from middleware import HostCheckMiddleware


# ============================================================================
# Configuration & Logging
# ============================================================================

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ttb_api")


# ============================================================================
# Pydantic Models
# ============================================================================

class ValidationResult(BaseModel):
    """Single field validation result."""
    field: str
    valid: bool
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    error: Optional[str] = None
    similarity_score: Optional[float] = None


class GovernmentWarning(BaseModel):
    """Government warning validation details."""
    present: bool
    header_correct: Optional[bool] = None
    text_correct: Optional[bool] = None


class ExtractedFields(BaseModel):
    """Extracted fields from label OCR."""
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    abv: Optional[str] = None
    abv_numeric: Optional[float] = None
    net_contents: Optional[str] = None
    bottler: Optional[str] = None
    country: Optional[str] = None
    government_warning: Optional[GovernmentWarning] = None


class ValidationResults(BaseModel):
    """Validation results by tier."""
    structural: List[ValidationResult]
    accuracy: List[ValidationResult] = Field(default_factory=list)


class Violation(BaseModel):
    """Validation violation detail."""
    field: str
    type: str  # "structural" or "accuracy"
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


class VerifyResponse(BaseModel):
    """Response from single label verification."""
    status: str  # COMPLIANT, NON_COMPLIANT, PARTIAL_VALIDATION
    validation_level: str  # STRUCTURAL_ONLY, FULL_VALIDATION
    extracted_fields: ExtractedFields
    validation_results: ValidationResults
    violations: List[Violation]
    warnings: List[str] = Field(default_factory=list)
    processing_time_seconds: float
    image_path: Optional[str] = None
    error: Optional[str] = None


class BatchSummary(BaseModel):
    """Summary statistics for batch processing."""
    total: int
    compliant: int
    non_compliant: int
    errors: int
    total_processing_time_seconds: float


class BatchResponse(BaseModel):
    """Response from batch verification."""
    results: List[VerifyResponse]
    summary: BatchSummary


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: str
    correlation_id: str


# ============================================================================
# FastAPI Application
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    logger.info("Starting TTB Label Verifier API")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Max file size: {settings.max_file_size_mb}MB")
    logger.info(f"Max batch size: {settings.max_batch_size} images")
    logger.info(f"Default OCR backend: {settings.default_ocr_backend}")
    logger.info(f"Ollama host: {settings.ollama_host}")
    logger.info(f"Ollama timeout: {settings.ollama_timeout_seconds}s")
    yield
    logger.info("Shutting down TTB Label Verifier API")


app = FastAPI(
    title="TTB Label Verifier API",
    description="REST API for validating alcohol beverage labels against 27 CFR regulations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add host checking middleware
app.add_middleware(
    HostCheckMiddleware,
    allowed_hosts=settings.get_allowed_hosts()
)

# Mount UI routes
from ui_routes import router as ui_router
app.include_router(ui_router)


# ============================================================================
# Utility Functions
# ============================================================================

def get_correlation_id() -> str:
    """Generate unique correlation ID for request tracing."""
    return str(uuid.uuid4())


async def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """
    Save uploaded file to destination path.
    
    Args:
        upload_file: FastAPI UploadFile object
        destination: Path to save file
        
    Raises:
        HTTPException: If file write fails
    """
    try:
        content = await upload_file.read()
        with open(destination, "wb") as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save upload file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )


def validate_image_file(upload_file: UploadFile, correlation_id: str) -> None:
    """
    Validate uploaded image file.
    
    Args:
        upload_file: FastAPI UploadFile object
        correlation_id: Request correlation ID
        
    Raises:
        HTTPException: If validation fails
    """
    # Check content type
    if upload_file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        logger.warning(
            f"[{correlation_id}] Invalid file type: {upload_file.content_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Expected image/jpeg or image/png, got {upload_file.content_type}"
        )
    
    # Check file extension
    if upload_file.filename:
        ext = Path(upload_file.filename).suffix.lower()
        if ext not in [".jpg", ".jpeg", ".png"]:
            logger.warning(
                f"[{correlation_id}] Invalid file extension: {ext}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension. Expected .jpg, .jpeg, or .png, got {ext}"
            )


def parse_ground_truth(ground_truth_str: Optional[str], correlation_id: str) -> Optional[Dict[str, Any]]:
    """
    Parse ground truth JSON string.
    
    Args:
        ground_truth_str: JSON string with expected values
        correlation_id: Request correlation ID
        
    Returns:
        Parsed ground truth dictionary or None
        
    Raises:
        HTTPException: If JSON is invalid
    """
    if not ground_truth_str:
        return None
    
    try:
        data = json.loads(ground_truth_str)
        
        # Check if data has nested "ground_truth" key (from sample generator)
        if 'ground_truth' in data:
            data = data['ground_truth']
        
        # Validate it's a dictionary
        if not isinstance(data, dict):
            raise ValueError("Ground truth must be a JSON object")
        
        return data
    
    except json.JSONDecodeError as e:
        logger.warning(f"[{correlation_id}] Invalid ground truth JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ground truth JSON: {str(e)}"
        )
    except ValueError as e:
        logger.warning(f"[{correlation_id}] Invalid ground truth format: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def extract_zip_file(
    zip_file: UploadFile,
    temp_dir: Path,
    correlation_id: str
) -> List[Path]:
    """
    Extract ZIP file and return list of image paths.
    
    Args:
        zip_file: Uploaded ZIP file
        temp_dir: Temporary directory to extract to
        correlation_id: Request correlation ID
        
    Returns:
        List of image file paths
        
    Raises:
        HTTPException: If ZIP is invalid or contains too many files
    """
    zip_path = temp_dir / "batch.zip"
    await save_upload_file(zip_file, zip_path)
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check for zip bombs or too many files
            if len(zf.namelist()) > settings.max_batch_size * 2:  # Allow JSON files too
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ZIP file contains too many files (max: {settings.max_batch_size * 2})"
                )
            
            # Extract all files
            zf.extractall(temp_dir)
    
    except zipfile.BadZipFile:
        logger.warning(f"[{correlation_id}] Invalid ZIP file")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or corrupt ZIP file"
        )
    except Exception as e:
        logger.error(f"[{correlation_id}] Failed to extract ZIP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract ZIP file: {str(e)}"
        )
    
    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png'}
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(temp_dir.glob(f"**/*{ext}"))
    
    if not image_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No image files found in ZIP archive"
        )
    
    if len(image_files) > settings.max_batch_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many images in batch. Maximum: {settings.max_batch_size}, found: {len(image_files)}"
        )
    
    return sorted(image_files)


def find_ground_truth_file(image_path: Path) -> Optional[Path]:
    """
    Find corresponding ground truth JSON file for an image.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Path to JSON file if found, None otherwise
    """
    json_path = image_path.with_suffix('.json')
    return json_path if json_path.exists() else None


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/verify", response_model=VerifyResponse)
async def verify_label(
    image: UploadFile = File(..., description="Label image file (max 10MB)"),
    ground_truth: Optional[str] = Form(None, description="Ground truth JSON string"),
    ocr_backend: Optional[str] = Form(None, description="OCR backend: tesseract or ollama"),
    timeout: Optional[int] = Form(None, description="Timeout in seconds for OCR processing"),
    username: str = Depends(get_current_user)
) -> VerifyResponse:
    """
    Verify a single alcohol beverage label.
    
    Performs structural validation (Tier 1) and optional accuracy validation
    (Tier 2) if ground truth is provided.
    
    **Request:**
    - `image`: Label image file (JPEG or PNG, max 10MB)
    - `ground_truth`: Optional JSON with expected values
    - `ocr_backend`: Optional OCR engine ("tesseract" or "ollama")
    - `timeout`: Optional timeout in seconds (default: 60s for Ollama)
    
    **Response:**
    - `status`: COMPLIANT, NON_COMPLIANT, or PARTIAL_VALIDATION
    - `validation_level`: STRUCTURAL_ONLY or FULL_VALIDATION
    - `extracted_fields`: Fields extracted from label
    - `validation_results`: Detailed validation results
    - `violations`: List of compliance violations
    - `processing_time_seconds`: Time taken to process
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/verify \\
      -F "image=@label.jpg" \\
      -F 'ground_truth={"brand_name":"Ridge & Co.","abv":7.5}'
    ```
    """
    correlation_id = get_correlation_id()
    logger.info(f"[{correlation_id}] POST /verify - {image.filename}")
    
    # Validate image file
    validate_image_file(image, correlation_id)
    
    # Parse ground truth
    ground_truth_data = parse_ground_truth(ground_truth, correlation_id)
    
    # Determine OCR backend
    backend = ocr_backend or settings.default_ocr_backend
    if backend.lower() not in ["tesseract", "ollama"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OCR backend. Must be 'tesseract' or 'ollama', got '{backend}'"
        )
    
    # Determine timeout
    ocr_timeout = timeout if timeout is not None else settings.ollama_timeout_seconds
    
    # Create temporary file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / image.filename
        await save_upload_file(image, temp_path)
        
        try:
            # Initialize validator
            validator = LabelValidator(ocr_backend=backend.lower())
            
            # Set timeout for Ollama if applicable
            if backend.lower() == "ollama" and hasattr(validator.ocr, 'timeout'):
                validator.ocr.timeout = ocr_timeout
            
            # Validate label
            logger.info(
                f"[{correlation_id}] Processing with {backend} OCR "
                f"(timeout: {ocr_timeout}s)"
            )
            result = validator.validate_label(str(temp_path), ground_truth_data)
            
            logger.info(
                f"[{correlation_id}] Completed - Status: {result['status']}, "
                f"Time: {result['processing_time_seconds']:.2f}s"
            )
            
            return VerifyResponse(**result)
        
        except RuntimeError as e:
            # Handle Ollama unavailability specifically
            error_msg = str(e)
            if backend.lower() == "ollama" and ("Cannot connect" in error_msg or "not found" in error_msg):
                logger.warning(f"[{correlation_id}] Ollama backend unavailable: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "message": f"Ollama backend unavailable: {error_msg}",
                        "suggestion": "Try using 'tesseract' backend or wait for model download to complete",
                        "available_backends": ["tesseract"],
                        "retry_after": 60
                    }
                )
            # Re-raise if not Ollama-related
            raise
        
        except Exception as e:
            logger.error(f"[{correlation_id}] Verification failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Label verification failed: {str(e)}"
            )


@app.post("/verify/batch", response_model=BatchResponse)
async def verify_batch(
    batch_file: UploadFile = File(..., description="ZIP file containing label images"),
    ocr_backend: Optional[str] = Form(None, description="OCR backend: tesseract or ollama"),
    timeout: Optional[int] = Form(None, description="Timeout in seconds for OCR processing"),
    username: str = Depends(get_current_user)
) -> BatchResponse:
    """
    Verify multiple alcohol beverage labels in batch.
    
    Accepts a ZIP file containing label images and optional JSON ground truth files.
    Ground truth files should have the same name as images (e.g., label.jpg + label.json).
    
    **Request:**
    - `batch_file`: ZIP archive with images (max 50 images)
    - `ocr_backend`: Optional OCR engine ("tesseract" or "ollama")
    - `timeout`: Optional timeout in seconds per image (default: 60s for Ollama)
    
    **ZIP Structure:**
    ```
    batch.zip
    ├── label_001.jpg
    ├── label_001.json  (optional ground truth)
    ├── label_002.jpg
    └── label_002.json
    ```
    
    **Response:**
    - `results`: Array of verification results (one per image)
    - `summary`: Statistics (total, compliant, non_compliant, errors)
    
    **Example:**
    ```bash
    curl -X POST http://localhost:8000/verify/batch \\
      -F "batch_file=@labels.zip" \\
      -F "ocr_backend=tesseract"
    ```
    """
    correlation_id = get_correlation_id()
    logger.info(f"[{correlation_id}] POST /verify/batch - {batch_file.filename}")
    
    # Validate ZIP file
    if batch_file.content_type not in ["application/zip", "application/x-zip-compressed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Expected application/zip, got {batch_file.content_type}"
        )
    
    # Determine OCR backend
    backend = ocr_backend or settings.default_ocr_backend
    if backend.lower() not in ["tesseract", "ollama"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OCR backend. Must be 'tesseract' or 'ollama', got '{backend}'"
        )
    
    # Determine timeout
    ocr_timeout = timeout if timeout is not None else settings.ollama_timeout_seconds
    
    # Process batch
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Extract ZIP
        image_files = await extract_zip_file(batch_file, temp_path, correlation_id)
        logger.info(f"[{correlation_id}] Found {len(image_files)} images to process")
        
        try:
            # Initialize validator (reuse for all images)
            validator = LabelValidator(ocr_backend=backend.lower())
            
            # Set timeout for Ollama if applicable
            if backend.lower() == "ollama" and hasattr(validator.ocr, 'timeout'):
                validator.ocr.timeout = ocr_timeout
        
        except RuntimeError as e:
            # Handle Ollama unavailability specifically
            error_msg = str(e)
            if backend.lower() == "ollama" and ("Cannot connect" in error_msg or "not found" in error_msg):
                logger.warning(f"[{correlation_id}] Ollama backend unavailable: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "message": f"Ollama backend unavailable: {error_msg}",
                        "suggestion": "Try using 'tesseract' backend or wait for model download to complete",
                        "available_backends": ["tesseract"],
                        "retry_after": 60
                    }
                )
            # Re-raise if not Ollama-related
            raise
        
        # Process each image
        results = []
        total_time = 0.0
        
        for i, image_path in enumerate(image_files, 1):
            try:
                logger.info(
                    f"[{correlation_id}] [{i}/{len(image_files)}] "
                    f"Processing {image_path.name}"
                )
                
                # Look for ground truth JSON
                ground_truth_path = find_ground_truth_file(image_path)
                ground_truth_data = None
                
                if ground_truth_path:
                    try:
                        with open(ground_truth_path, 'r') as f:
                            ground_truth_data = json.load(f)
                        
                        # Handle nested ground_truth key
                        if 'ground_truth' in ground_truth_data:
                            ground_truth_data = ground_truth_data['ground_truth']
                    
                    except Exception as e:
                        logger.warning(
                            f"[{correlation_id}] Failed to load ground truth for "
                            f"{image_path.name}: {e}"
                        )
                
                # Validate label
                result = validator.validate_label(str(image_path), ground_truth_data)
                result['image_path'] = image_path.name
                results.append(result)
                total_time += result['processing_time_seconds']
            
            except Exception as e:
                logger.error(
                    f"[{correlation_id}] Failed to process {image_path.name}: {e}",
                    exc_info=True
                )
                # Add error result
                results.append({
                    "status": "ERROR",
                    "validation_level": "STRUCTURAL_ONLY",
                    "extracted_fields": {},
                    "validation_results": {"structural": [], "accuracy": []},
                    "violations": [],
                    "warnings": [],
                    "processing_time_seconds": 0.0,
                    "image_path": image_path.name,
                    "error": str(e)
                })
        
        # Calculate summary statistics
        compliant = sum(1 for r in results if r.get('status') == 'COMPLIANT')
        non_compliant = sum(1 for r in results if r.get('status') == 'NON_COMPLIANT')
        errors = sum(1 for r in results if r.get('status') == 'ERROR')
        
        summary = BatchSummary(
            total=len(results),
            compliant=compliant,
            non_compliant=non_compliant,
            errors=errors,
            total_processing_time_seconds=total_time
        )
        
        logger.info(
            f"[{correlation_id}] Batch complete - "
            f"Total: {summary.total}, Compliant: {summary.compliant}, "
            f"Non-compliant: {summary.non_compliant}, Errors: {summary.errors}, "
            f"Time: {summary.total_processing_time_seconds:.2f}s"
        )
        
        return BatchResponse(results=results, summary=summary)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions with structured error response."""
    correlation_id = get_correlation_id()
    error_code = f"HTTP_{exc.status_code}"
    
    logger.warning(
        f"[{correlation_id}] HTTP {exc.status_code}: {exc.detail}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": error_code,
            "correlation_id": correlation_id
        }
    )


# Import after app is defined to avoid circular imports
from auth import UnauthenticatedError
from fastapi.responses import RedirectResponse as FastAPIRedirectResponse

@app.exception_handler(UnauthenticatedError)
async def unauthenticated_handler(request, exc: UnauthenticatedError):
    """Handle unauthenticated UI access by redirecting to login."""
    logger.info(f"Redirecting unauthenticated user to login from {request.url.path}")
    return FastAPIRedirectResponse(url="/ui/login", status_code=status.HTTP_302_FOUND)


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    correlation_id = get_correlation_id()
    
    logger.error(
        f"[{correlation_id}] Unhandled exception: {exc}",
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "correlation_id": correlation_id
        }
    )


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - redirects to UI."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/ui/verify", status_code=status.HTTP_302_FOUND)


@app.get("/health")
async def health_check():
    """
    Health check endpoint that reports backend availability.
    
    Returns service health and available OCR backends. This endpoint always
    returns HTTP 200 as long as the API is running, even in degraded mode
    (Tesseract-only). This allows the load balancer to route traffic to the
    instance while Ollama model is still downloading.
    
    Returns:
        {
            "status": "healthy" | "degraded",
            "backends": {
                "tesseract": {"available": bool, "error": str|null},
                "ollama": {"available": bool, "error": str|null, "model": str}
            },
            "capabilities": {
                "ocr_backends": ["tesseract", "ollama"],  # Available backends
                "degraded_mode": bool  # True if any backend unavailable
            }
        }
    """
    from ocr_backends import TesseractOCR, OllamaOCR
    import os
    
    # Check Tesseract availability
    tesseract_available = True
    tesseract_error = None
    try:
        tesseract_ocr = TesseractOCR()
    except RuntimeError as e:
        tesseract_available = False
        tesseract_error = str(e)
    
    # Check Ollama availability (lazy check - no exception raised)
    ollama_host = settings.ollama_host
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2-vision")
    ollama_available = False
    ollama_error = None
    
    try:
        # Use short timeout for health check to avoid blocking
        import requests
        response = requests.get(f"{ollama_host}/api/tags", timeout=2)
        
        if response.status_code == 200:
            models_data = response.json()
            available_models = [m.get('name', '').split(':')[0] for m in models_data.get('models', [])]
            model_base = ollama_model.split(':')[0]
            
            if model_base in available_models:
                ollama_available = True
            else:
                ollama_error = f"Model '{ollama_model}' not found"
        else:
            ollama_error = f"Ollama not available: HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        ollama_error = "Ollama busy or slow to respond (timeout after 2s)"
    except Exception as e:
        ollama_error = str(e)
    
    # Determine available backends
    available_backends = []
    if tesseract_available:
        available_backends.append("tesseract")
    if ollama_available:
        available_backends.append("ollama")
    
    # Determine overall status
    degraded_mode = not ollama_available
    overall_status = "degraded" if degraded_mode else "healthy"
    
    return {
        "status": overall_status,
        "backends": {
            "tesseract": {
                "available": tesseract_available,
                "error": tesseract_error
            },
            "ollama": {
                "available": ollama_available,
                "error": ollama_error,
                "model": ollama_model
            }
        },
        "capabilities": {
            "ocr_backends": available_backends,
            "degraded_mode": degraded_mode
        }
    }

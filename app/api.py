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

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from config import get_settings
from label_validator import LabelValidator
from auth import get_current_user
from middleware import HostCheckMiddleware
from job_manager import JobManager, JobStatus


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

# Initialize job manager for async batch processing
job_manager = JobManager()


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


class BatchJobSubmitResponse(BaseModel):
    """Response from async batch job submission."""
    job_id: str
    status: str
    total_images: int
    message: str


class BatchJobStatusResponse(BaseModel):
    """Response from async batch job status query."""
    job_id: str
    status: str
    total_images: int
    processed_images: int
    results: List[VerifyResponse]
    summary: Optional[BatchSummary] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None


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
    import asyncio
    
    logger.info("Starting TTB Label Verifier API")
    logger.info(f"Log level: {settings.log_level}")
    logger.info(f"Max file size: {settings.max_file_size_mb}MB")
    logger.info(f"Max batch size: {settings.max_batch_size} images")
    logger.info(f"Ollama host: {settings.ollama_host}")
    logger.info(f"Ollama timeout: {settings.ollama_timeout_seconds}s")
    
    # Start background cleanup task
    cleanup_task = None
    try:
        cleanup_task = asyncio.create_task(_cleanup_jobs_loop())
        logger.info("Started job cleanup background task")
    except Exception as e:
        logger.error(f"Failed to start cleanup task: {e}")
    
    yield
    
    # Shutdown cleanup task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
    
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
    
    # Verify file is actually a valid image by trying to open it
    try:
        from PIL import Image
        upload_file.file.seek(0)  # Reset file pointer
        img = Image.open(upload_file.file)
        img.verify()  # Verify it's a valid image
        upload_file.file.seek(0)  # Reset again for later processing
    except Exception as e:
        logger.warning(
            f"[{correlation_id}] Invalid image file: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupted image file: {str(e)}"
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


async def _cleanup_jobs_loop():
    """Background task that periodically cleans up old jobs."""
    import asyncio
    
    cleanup_interval_seconds = settings.job_cleanup_interval_seconds
    retention_hours = settings.job_retention_hours
    
    while True:
        try:
            await asyncio.sleep(cleanup_interval_seconds)
            logger.debug("Running job cleanup task")
            deleted_count = job_manager.cleanup_old_jobs(retention_hours=retention_hours)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old jobs")
        except asyncio.CancelledError:
            logger.info("Job cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}", exc_info=True)


def process_batch_job(
    job_id: str,
    image_files: List[Path],
    ocr_timeout: int,
    correlation_id: str
):
    """
    Background task to process a batch job.
    
    Processes images sequentially, updating job state after each image.
    Continues on error to return partial results.
    
    Args:
        job_id: Job identifier
        image_files: List of image file paths
        ocr_timeout: Timeout for OCR processing
        correlation_id: Request correlation ID
    """
    logger.info(f"[{correlation_id}] Starting batch job {job_id} with {len(image_files)} images")
    
    try:
        # Update job status to PROCESSING
        job_manager.update_job(job_id, status=JobStatus.PROCESSING)
        
        # Initialize validator with Ollama (reuse for all images)
        try:
            validator = LabelValidator(timeout=ocr_timeout)
        
        except RuntimeError as e:
            # Handle Ollama unavailability
            error_msg = f"Ollama backend unavailable: {str(e)}"
            logger.error(f"[{correlation_id}] {error_msg}")
            job_manager.update_job(
                job_id,
                status=JobStatus.FAILED,
                error=error_msg
            )
            return
        
        # Process each image sequentially
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
                
                # Append result to job (atomic operation)
                job_manager.append_result(job_id, result)
                total_time += result['processing_time_seconds']
                
                logger.debug(
                    f"[{correlation_id}] [{i}/{len(image_files)}] "
                    f"Completed {image_path.name} - Status: {result['status']}"
                )
            
            except Exception as e:
                logger.error(
                    f"[{correlation_id}] Failed to process {image_path.name}: {e}",
                    exc_info=True
                )
                # Add error result and continue processing
                error_result = {
                    "status": "ERROR",
                    "validation_level": "STRUCTURAL_ONLY",
                    "extracted_fields": {},
                    "validation_results": {"structural": [], "accuracy": []},
                    "violations": [],
                    "warnings": [],
                    "processing_time_seconds": 0.0,
                    "image_path": image_path.name,
                    "error": str(e)
                }
                job_manager.append_result(job_id, error_result)
        
        # Get final job state to calculate summary
        job = job_manager.get_job(job_id)
        if not job:
            logger.error(f"[{correlation_id}] Job {job_id} not found after processing")
            return
        
        # Calculate summary statistics
        results = job.results
        compliant = sum(1 for r in results if r.get('status') == 'COMPLIANT')
        non_compliant = sum(1 for r in results if r.get('status') == 'NON_COMPLIANT')
        errors = sum(1 for r in results if r.get('status') == 'ERROR')
        
        summary = {
            "total": len(results),
            "compliant": compliant,
            "non_compliant": non_compliant,
            "errors": errors,
            "total_processing_time_seconds": total_time
        }
        
        # Mark job as completed with summary
        job_manager.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            summary=summary
        )
        
        logger.info(
            f"[{correlation_id}] Batch job {job_id} complete - "
            f"Total: {summary['total']}, Compliant: {summary['compliant']}, "
            f"Non-compliant: {summary['non_compliant']}, Errors: {summary['errors']}, "
            f"Time: {summary['total_processing_time_seconds']:.2f}s"
        )
    
    except Exception as e:
        logger.error(
            f"[{correlation_id}] Batch job {job_id} failed: {e}",
            exc_info=True
        )
        job_manager.update_job(
            job_id,
            status=JobStatus.FAILED,
            error=str(e)
        )


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/verify", response_model=VerifyResponse)
async def verify_label(
    image: UploadFile = File(..., description="Label image file (max 10MB)"),
    ground_truth: Optional[str] = Form(None, description="Ground truth JSON string"),
    timeout: Optional[int] = Form(None, description="Timeout in seconds for OCR processing"),
    username: str = Depends(get_current_user)
) -> VerifyResponse:
    """
    Verify a single alcohol beverage label using Ollama vision OCR.
    
    Performs structural validation (Tier 1) and optional accuracy validation
    (Tier 2) if ground truth is provided.
    
    **Request:**
    - `image`: Label image file (JPEG or PNG, max 10MB)
    - `ground_truth`: Optional JSON with expected values
    - `timeout`: Optional timeout in seconds (default: 60s)
    
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
    
    # Determine timeout
    ocr_timeout = timeout if timeout is not None else settings.ollama_timeout_seconds
    
    # Create temporary file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / image.filename
        await save_upload_file(image, temp_path)
        
        try:
            # Initialize validator with Ollama, passing timeout at construction
            # so the httpx client inside OllamaOCR enforces it on every request.
            validator = LabelValidator(timeout=ocr_timeout)
            
            # Validate label
            logger.info(
                f"[{correlation_id}] Processing with Ollama OCR "
                f"(timeout: {ocr_timeout}s)"
            )
            result = validator.validate_label(str(temp_path), ground_truth_data)
            
            logger.info(
                f"[{correlation_id}] Completed - Status: {result['status']}, "
                f"Time: {result['processing_time_seconds']:.2f}s"
            )
            
            return VerifyResponse(**result)
        
        except RuntimeError as e:
            # Handle Ollama unavailability
            error_msg = str(e)
            if "Cannot connect" in error_msg or "not found" in error_msg or "not available" in error_msg:
                logger.warning(f"[{correlation_id}] Ollama backend unavailable: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={
                        "message": f"Ollama backend unavailable: {error_msg}",
                        "suggestion": "Wait for Ollama model to load or check system health at /health",
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


@app.post("/verify/batch", response_model=BatchJobSubmitResponse)
async def submit_batch_job(
    batch_file: UploadFile = File(..., description="ZIP file containing label images"),
    timeout: Optional[int] = Form(None, description="Timeout in seconds for OCR processing"),
    background_tasks: BackgroundTasks = None,
    username: str = Depends(get_current_user)
) -> BatchJobSubmitResponse:
    """
    Submit a batch verification job for asynchronous processing.
    
    Accepts a ZIP file containing label images and optional JSON ground truth files.
    Returns immediately with a job_id that can be used to poll for status and results.
    
    **Request:**
    - `batch_file`: ZIP archive with images (max 50 images)
    - `timeout`: Optional timeout in seconds per image (default: 60s)
    
    **ZIP Structure:**
    ```
    batch.zip
    ├── label_001.jpg
    ├── label_001.json  (optional ground truth)
    ├── label_002.jpg
    └── label_002.json
    ```
    
    **Response:**
    - `job_id`: Job identifier (use to poll GET /verify/batch/{job_id})
    - `status`: Job status (pending)
    - `total_images`: Number of images to process
    - `message`: Instructions for polling
    
    **Example:**
    ```bash
    # Submit job
    curl -X POST http://localhost:8000/verify/batch \\
      -F "batch_file=@labels.zip"
    
    # Poll for status (use job_id from response)
    curl http://localhost:8000/verify/batch/{job_id}
    ```
    """
    correlation_id = get_correlation_id()
    logger.info(f"[{correlation_id}] POST /verify/batch - {batch_file.filename}")
    
    # Validate file is a ZIP
    if not batch_file.filename.endswith('.zip'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Batch file must be a ZIP archive"
        )
    
    # Determine timeout
    ocr_timeout = timeout if timeout is not None else settings.ollama_timeout_seconds
    
    # Extract ZIP to permanent location for background processing
    # We need to keep files accessible for the background task
    persistent_dir = Path("/app/tmp/jobs") / str(uuid.uuid4())
    persistent_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Extract ZIP
        image_files = await extract_zip_file(batch_file, persistent_dir, correlation_id)
        logger.info(f"[{correlation_id}] Found {len(image_files)} images to process")
        
        # Create job
        job_id = job_manager.create_job(total_images=len(image_files))
        
        # Start background processing
        background_tasks.add_task(
            process_batch_job,
            job_id=job_id,
            image_files=image_files,
            ocr_timeout=ocr_timeout,
            correlation_id=correlation_id
        )
        
        logger.info(
            f"[{correlation_id}] Batch job {job_id} submitted with "
            f"{len(image_files)} images"
        )
        
        return BatchJobSubmitResponse(
            job_id=job_id,
            status="pending",
            total_images=len(image_files),
            message=f"Job submitted. Poll GET /verify/batch/{job_id} for status and results."
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (e.g. 400 for invalid ZIP) without wrapping
        import shutil
        if persistent_dir.exists():
            shutil.rmtree(persistent_dir, ignore_errors=True)
        raise
    
    except Exception as e:
        # Cleanup persistent dir on error
        import shutil
        if persistent_dir.exists():
            shutil.rmtree(persistent_dir, ignore_errors=True)
        
        logger.error(f"[{correlation_id}] Failed to submit batch job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit batch job: {str(e)}"
        )


@app.get("/verify/batch/{job_id}", response_model=BatchJobStatusResponse)
async def get_batch_job_status(
    job_id: str,
    username: str = Depends(get_current_user)
) -> BatchJobStatusResponse:
    """
    Get status and results of a batch verification job.
    
    Poll this endpoint to check job progress and retrieve results as they
    become available. Results are returned incrementally as each image completes.
    
    **Job Status Values:**
    - `pending`: Job queued, not yet started
    - `processing`: Job in progress
    - `completed`: Job finished successfully
    - `failed`: Job failed due to error
    - `cancelled`: Job was cancelled
    
    **Response:**
    - `job_id`: Job identifier
    - `status`: Current job status
    - `total_images`: Total number of images to process
    - `processed_images`: Number of images processed so far
    - `results`: Array of verification results (grows as images complete)
    - `summary`: Summary statistics (only when status is completed)
    - `error`: Error message (only when status is failed)
    
    **Example:**
    ```bash
    curl http://localhost:8000/verify/batch/abc123-def456
    ```
    """
    correlation_id = get_correlation_id()
    logger.debug(f"[{correlation_id}] GET /verify/batch/{job_id}")
    
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Convert results to VerifyResponse objects
    results = [VerifyResponse(**r) for r in job.results]
    
    # Convert summary if present
    summary = None
    if job.summary:
        summary = BatchSummary(**job.summary)
    
    return BatchJobStatusResponse(
        job_id=job.job_id,
        status=job.status.value,
        total_images=job.total_images,
        processed_images=job.processed_images,
        results=results,
        summary=summary,
        error=job.error,
        created_at=job.created_at.isoformat(),
        updated_at=job.updated_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None
    )


@app.delete("/verify/batch/{job_id}")
async def delete_batch_job(
    job_id: str,
    username: str = Depends(get_current_user)
):
    """
    Cancel or delete a batch verification job.
    
    If the job is still processing, it will be marked as cancelled (processing
    may continue for the current image but will stop after that). Completed jobs
    will simply be deleted.
    
    **Example:**
    ```bash
    curl -X DELETE http://localhost:8000/verify/batch/abc123-def456
    ```
    """
    correlation_id = get_correlation_id()
    logger.info(f"[{correlation_id}] DELETE /verify/batch/{job_id}")
    
    job = job_manager.get_job(job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # If job is still processing, mark as cancelled
    if job.status in (JobStatus.PENDING, JobStatus.PROCESSING):
        job_manager.update_job(job_id, status=JobStatus.CANCELLED)
        logger.info(f"[{correlation_id}] Job {job_id} marked as cancelled")
    
    # Delete job
    success = job_manager.delete_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete job {job_id}"
        )
    
    return {"message": f"Job {job_id} deleted successfully"}


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

# Path to the Ollama health sentinel file written by the host cron job
# scripts/ollama-health-cron.sh runs every 5 minutes and writes this file
# when the model is in GPU RAM. The app never touches Ollama directly from
# the health check — all the blocking network calls are gone.
_OLLAMA_HEALTHY_FILE = Path("/etc/OLLAMA_HEALTHY")


def get_health_status() -> Dict[str, Any]:
    """
    Check health of the Ollama backend and return status.

    Shared function used by both /health (JSON) and /ui/health (HTML) endpoints.

    Ollama health is determined solely by the presence of /etc/OLLAMA_HEALTHY,
    which is written by the host cron job (scripts/ollama-health-cron.sh) when
    the model is confirmed to be in GPU RAM.  This avoids any synchronous network
    calls to Ollama inside the FastAPI event loop, which was the root cause of
    the /health endpoint blocking and cascading 503s from CloudFront.

    Returns:
        {
            "status": "healthy" | "initializing",
            "backends": {
                "ollama": {"available": bool, "error": str|null, "model": str}
            },
            "capabilities": {
                "ocr_backends": ["ollama"]
            }
        }
    """
    import os
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2-vision")

    ollama_available = _OLLAMA_HEALTHY_FILE.exists()
    ollama_error = None if ollama_available else "Model not in GPU (cron pre-warm pending)"

    return {
        "status": "healthy" if ollama_available else "initializing",
        "backends": {
            "ollama": {
                "available": ollama_available,
                "error": ollama_error,
                "model": ollama_model
            }
        },
        "capabilities": {
            "ocr_backends": ["ollama"] if ollama_available else []
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint that reports Ollama backend availability.

    Returns HTTP 200 as long as the API process is running, even when Ollama
    is initializing.  Ollama is reported as available only when the sentinel
    file /etc/OLLAMA_HEALTHY is present on the host; that file is maintained
    by the scripts/ollama-health-cron.sh cron job running every 5 minutes.

    Returns:
        {
            "status": "healthy" | "initializing",
            "backends": {
                "ollama": {"available": bool, "error": str|null, "model": str}
            },
            "capabilities": {
                "ocr_backends": ["ollama"]
            }
        }
    """
    return get_health_status()

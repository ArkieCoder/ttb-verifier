"""
TTB Label Verifier - UI Routes

Web interface routes for label verification with session-based authentication.
Provides single image and batch verification through Bootstrap 5 UI.
"""

import json
import logging
import tempfile
import zipfile
import uuid
import shutil
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from PIL import Image

from auth import (
    create_session_cookie, 
    get_current_user,
    get_current_user_ui,
    get_current_user_optional,
    verify_credentials,
    SESSION_COOKIE_NAME
)
from config import get_settings
from label_validator import LabelValidator, OllamaBusyError, OllamaTimeoutError
from ocr_backends import OllamaOCR

logger = logging.getLogger("ttb_ui")
settings = get_settings()

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Create UI router
router = APIRouter()

# Temporary upload directory for batch processing
TEMP_UPLOAD_DIR = Path("/tmp/ttb-uploads")
TEMP_FILE_RETENTION_HOURS = 1


# ============================================================================
# Utility Functions
# ============================================================================

def cleanup_old_temp_files():
    """Remove temporary upload files older than retention period."""
    if not TEMP_UPLOAD_DIR.exists():
        return
    
    cutoff_time = datetime.now() - timedelta(hours=TEMP_FILE_RETENTION_HOURS)
    removed_count = 0
    
    for batch_dir in TEMP_UPLOAD_DIR.iterdir():
        if batch_dir.is_dir():
            try:
                # Check modification time
                mod_time = datetime.fromtimestamp(batch_dir.stat().st_mtime)
                if mod_time < cutoff_time:
                    shutil.rmtree(batch_dir)
                    removed_count += 1
            except Exception as e:
                logger.warning(f"Failed to remove old temp directory {batch_dir}: {e}")
    
    if removed_count > 0:
        logger.info(f"Cleaned up {removed_count} old temporary upload directories")


def create_temp_batch_dir() -> Path:
    """Create temporary directory for batch processing."""
    cleanup_old_temp_files()
    
    TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    batch_id = str(uuid.uuid4())
    batch_dir = TEMP_UPLOAD_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    return batch_dir


def create_thumbnail(image_path: Path, size: tuple = (100, 100)) -> str:
    """
    Create base64-encoded thumbnail of image.
    
    Args:
        image_path: Path to source image
        size: Thumbnail size (width, height)
        
    Returns:
        Base64 data URL for thumbnail
    """
    import base64
    from io import BytesIO
    
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        logger.error(f"Failed to create thumbnail for {image_path}: {e}")
        return ""


# ============================================================================
# UI Routes
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def ui_root(request: Request, username: Optional[str] = Depends(get_current_user_optional)):
    """
    Root UI page - redirects to login or main verification page.
    """
    if username:
        return RedirectResponse(url="/ui/verify", status_code=status.HTTP_302_FOUND)
    else:
        return RedirectResponse(url="/ui/login", status_code=status.HTTP_302_FOUND)


@router.get("/ui/login", response_class=HTMLResponse)
async def ui_login_page(request: Request):
    """
    Display login page.
    """
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
    )


@router.post("/ui/login", response_class=HTMLResponse)
async def ui_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """
    Process login form submission.
    """
    if verify_credentials(username, password):
        session_cookie = create_session_cookie(username)
        
        # Redirect to main verification page
        response = RedirectResponse(url="/ui/verify", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_cookie,
            httponly=True,
            secure=True,  # Only over HTTPS
            samesite="lax",
            max_age=4 * 60 * 60  # 4 hours
        )
        return response
    else:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )


@router.get("/ui/logout")
async def ui_logout(request: Request):
    """
    Logout user by deleting session cookie.
    """
    response = RedirectResponse(url="/ui/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@router.get("/ui/verify", response_class=HTMLResponse)
async def ui_verify_page(request: Request, username: str = Depends(get_current_user_ui)):
    """
    Main verification page for single image upload.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "username": username,
            "ollama_host": settings.ollama_host,
            "default_timeout": settings.ollama_timeout_seconds
        }
    )


@router.post("/ui/verify", response_class=HTMLResponse)
async def ui_verify_submit(
    request: Request,
    image: UploadFile = File(...),
    brand_name: Optional[str] = Form(None),
    abv: Optional[str] = Form(None),
    net_contents: Optional[str] = Form(None),
    bottler: Optional[str] = Form(None),
    product_type: Optional[str] = Form(None),
    ollama_timeout: Optional[int] = Form(None),
    username: str = Depends(get_current_user_ui)
):
    """
    Process single image verification form using Ollama OCR.
    """
    # Validate image file
    if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "username": username,
                "error": f"Invalid file type: {image.content_type}. Please upload JPEG or PNG.",
                "error_field": "image",
                "form_data": {
                    "brand_name": brand_name,
                    "product_type": product_type,
                    "abv": abv,
                    "net_contents": net_contents,
                    "bottler": bottler,
                    "ollama_timeout": ollama_timeout
                },
                "ollama_host": settings.ollama_host,
                "default_timeout": settings.ollama_timeout_seconds
            }
        )
    
    # Build ground truth if metadata provided
    ground_truth = {}
    if brand_name:
        ground_truth["brand_name"] = brand_name
    if abv:
        try:
            ground_truth["abv"] = float(abv)
        except ValueError:
            ground_truth["abv"] = abv
    if net_contents:
        ground_truth["net_contents"] = net_contents
    if bottler:
        ground_truth["bottler"] = bottler
    if product_type:
        ground_truth["product_type"] = product_type
    
    # Determine timeout
    timeout = ollama_timeout or settings.ollama_timeout_seconds
    
    # Create temporary file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / image.filename
        content = await image.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        try:
            # Initialize validator with the resolved timeout so the httpx client
            # inside OllamaOCR is constructed with the correct value.  Mutating
            # validator.ocr.timeout after construction does NOT propagate to the
            # already-built httpx.Client, so timeout must be passed here.
            validator = LabelValidator(timeout=timeout)
            
            # Validate label
            result = validator.validate_label(
                str(temp_path),
                ground_truth if ground_truth else None
            )
            
            # Encode image as base64 for display in results
            image_base64 = base64.b64encode(content).decode('utf-8')
            image_mime = image.content_type or 'image/jpeg'
            
            return templates.TemplateResponse(
                "results.html",
                {
                    "request": request,
                    "username": username,
                    "result": result,
                    "filename": image.filename,
                    "image_data": f"data:{image_mime};base64,{image_base64}"
                }
            )
        
        except (OllamaBusyError, OllamaTimeoutError) as e:
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "username": username,
                    "error": f"Ollama is temporarily unavailable: {str(e)} Please retry in a few seconds.",
                    "error_field": "image",
                    "form_data": {
                        "brand_name": brand_name,
                        "product_type": product_type,
                        "abv": abv,
                        "net_contents": net_contents,
                        "bottler": bottler,
                        "ollama_timeout": ollama_timeout
                    },
                    "ollama_host": settings.ollama_host,
                    "default_timeout": settings.ollama_timeout_seconds
                }
            )
        
        except RuntimeError as e:
            error_msg = str(e)
            if "Cannot connect" in error_msg or "not found" in error_msg:
                error_msg = f"Ollama backend unavailable: {error_msg}. Please use Tesseract or wait for model download."
            
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "username": username,
                    "error": error_msg,
                    "error_field": "image",
                    "form_data": {
                        "brand_name": brand_name,
                        "product_type": product_type,
                        "abv": abv,
                        "net_contents": net_contents,
                        "bottler": bottler,
                        "ollama_timeout": ollama_timeout
                    },
                    "ollama_host": settings.ollama_host,
                    "default_timeout": settings.ollama_timeout_seconds
                }
            )
        
        except Exception as e:
            logger.error(f"Verification failed: {e}", exc_info=True)
            return templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "username": username,
                    "error": f"Verification failed: {str(e)}",
                    "form_data": {
                        "brand_name": brand_name,
                        "product_type": product_type,
                        "abv": abv,
                        "net_contents": net_contents,
                        "bottler": bottler,
                        "ollama_timeout": ollama_timeout
                    },
                    "ollama_host": settings.ollama_host,
                    "default_timeout": settings.ollama_timeout_seconds
                }
            )


@router.get("/ui/batch", response_class=HTMLResponse)
async def ui_batch_page(request: Request, username: str = Depends(get_current_user_ui)):
    """
    Batch verification page for ZIP upload.
    """
    return templates.TemplateResponse(
        "batch.html",
        {
            "request": request,
            "username": username,
            "max_batch_size": settings.max_batch_size,
            "ollama_host": settings.ollama_host,
            "default_timeout": settings.ollama_timeout_seconds
        }
    )


@router.post("/ui/batch", response_class=HTMLResponse)
async def ui_batch_submit(
    request: Request,
    batch_file: UploadFile = File(...),
    ollama_timeout: Optional[int] = Form(None),
    background_tasks = None,
    username: str = Depends(get_current_user_ui)
):
    """
    Submit batch ZIP file for asynchronous verification.
    Redirects to results page that polls for status.
    """
    from fastapi import BackgroundTasks
    from job_manager import JobManager
    from api import extract_zip_file, process_batch_job, job_manager
    
    # Validate ZIP file
    if batch_file.content_type not in ["application/zip", "application/x-zip-compressed"]:
        return templates.TemplateResponse(
            "batch.html",
            {
                "request": request,
                "username": username,
                "error": f"Invalid file type: {batch_file.content_type}. Please upload a ZIP file.",
                "error_field": "batch_file",
                "form_data": {
                    "ollama_timeout": ollama_timeout
                },
                "max_batch_size": settings.max_batch_size,
                "ollama_host": settings.ollama_host,
                "default_timeout": settings.ollama_timeout_seconds
            }
        )
    
    ocr_timeout = ollama_timeout or settings.ollama_timeout_seconds
    correlation_id = str(uuid.uuid4())
    
    # Extract ZIP to persistent directory for background processing
    persistent_dir = Path("/app/tmp/jobs") / str(uuid.uuid4())
    persistent_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        image_files = await extract_zip_file(batch_file, persistent_dir, correlation_id)
        
        job_id = job_manager.create_job(total_images=len(image_files))
        
        request.state.background_tasks = BackgroundTasks()
        request.state.background_tasks.add_task(
            process_batch_job,
            job_id=job_id,
            image_files=image_files,
            ocr_timeout=ocr_timeout,
            correlation_id=correlation_id
        )
        
        # Schedule via starlette background (attached to response)
        from starlette.background import BackgroundTask
        bg = BackgroundTask(
            process_batch_job,
            job_id=job_id,
            image_files=image_files,
            ocr_timeout=ocr_timeout,
            correlation_id=correlation_id
        )
        
        return RedirectResponse(
            url=f"/ui/batch/results/{job_id}",
            status_code=status.HTTP_303_SEE_OTHER,
            background=bg
        )
    
    except HTTPException as e:
        import shutil
        shutil.rmtree(persistent_dir, ignore_errors=True)
        return templates.TemplateResponse(
            "batch.html",
            {
                "request": request,
                "username": username,
                "error": e.detail if isinstance(e.detail, str) else str(e.detail),
                "error_field": "batch_file",
                "form_data": {"ollama_timeout": ollama_timeout},
                "max_batch_size": settings.max_batch_size,
                "ollama_host": settings.ollama_host,
                "default_timeout": settings.ollama_timeout_seconds
            }
        )
    
    except Exception as e:
        import shutil
        shutil.rmtree(persistent_dir, ignore_errors=True)
        logger.error(f"Batch submission failed: {e}", exc_info=True)
        error_msg = str(e)
        if "Cannot connect" in error_msg or "unavailable" in error_msg:
            error_msg = "Ollama backend unavailable. Please wait for model to load."
        return templates.TemplateResponse(
            "batch.html",
            {
                "request": request,
                "username": username,
                "error": error_msg,
                "error_field": "batch_file",
                "form_data": {"ollama_timeout": ollama_timeout},
                "max_batch_size": settings.max_batch_size,
                "ollama_host": settings.ollama_host,
                "default_timeout": settings.ollama_timeout_seconds
            }
        )


@router.get("/ui/batch/results/{job_id}", response_class=HTMLResponse)
async def ui_batch_results(
    request: Request,
    job_id: str,
    username: str = Depends(get_current_user_ui)
):
    """
    Display batch results page with live polling for job status.
    """
    return templates.TemplateResponse(
        "batch_results.html",
        {
            "request": request,
            "username": username,
            "job_id": job_id
        }
    )


@router.get("/ui/health", response_class=HTMLResponse)
async def ui_health(request: Request):
    """
    System health page - displays OCR backend status in a user-friendly HTML format.
    Accessible without authentication.
    """
    from api import get_health_status
    
    # Get health status directly (no HTTP call needed)
    health_data = get_health_status()
    
    # Pretty print JSON for display
    health_json = json.dumps(health_data, indent=2)
    
    return templates.TemplateResponse(
        "health.html",
        {
            "request": request,
            "health": health_data,
            "health_json": health_json
        }
    )

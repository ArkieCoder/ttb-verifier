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
from label_validator import LabelValidator
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
    use_ollama: Optional[str] = Form(None),
    ollama_timeout: Optional[int] = Form(None),
    username: str = Depends(get_current_user_ui)
):
    """
    Process single image verification form.
    """
    # Validate image file
    if image.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "username": username,
                "error": f"Invalid file type: {image.content_type}. Please upload JPEG or PNG.",
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
    
    # Determine OCR backend
    ocr_backend = "ollama" if use_ollama == "on" else "tesseract"
    timeout = ollama_timeout or settings.ollama_timeout_seconds
    
    # Create temporary file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / image.filename
        content = await image.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        try:
            # Initialize validator
            validator = LabelValidator(ocr_backend=ocr_backend)
            
            # Set timeout for Ollama
            if ocr_backend == "ollama" and hasattr(validator.ocr, 'timeout'):
                validator.ocr.timeout = timeout
            
            # Validate label
            result = validator.validate_label(
                str(temp_path),
                ground_truth if ground_truth else None
            )
            
            return templates.TemplateResponse(
                "results.html",
                {
                    "request": request,
                    "username": username,
                    "result": result,
                    "filename": image.filename
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
    use_ollama: Optional[str] = Form(None),
    ollama_timeout: Optional[int] = Form(None),
    username: str = Depends(get_current_user_ui)
):
    """
    Process batch ZIP file verification.
    """
    # Validate ZIP file
    if batch_file.content_type not in ["application/zip", "application/x-zip-compressed"]:
        return templates.TemplateResponse(
            "batch.html",
            {
                "request": request,
                "username": username,
                "error": f"Invalid file type: {batch_file.content_type}. Please upload a ZIP file.",
                "max_batch_size": settings.max_batch_size,
                "ollama_host": settings.ollama_host,
                "default_timeout": settings.ollama_timeout_seconds
            }
        )
    
    # Determine OCR backend
    ocr_backend = "ollama" if use_ollama == "on" else "tesseract"
    timeout = ollama_timeout or settings.ollama_timeout_seconds
    
    # Create temporary batch directory
    batch_dir = create_temp_batch_dir()
    
    try:
        # Save and extract ZIP
        zip_path = batch_dir / "batch.zip"
        content = await batch_file.read()
        with open(zip_path, "wb") as f:
            f.write(content)
        
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check file count
            if len(zf.namelist()) > settings.max_batch_size * 2:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"ZIP contains too many files (max: {settings.max_batch_size * 2})"
                )
            zf.extractall(batch_dir)
        
        # Find all image files
        image_extensions = {'.jpg', '.jpeg', '.png'}
        image_files = []
        for ext in image_extensions:
            image_files.extend(batch_dir.glob(f"**/*{ext}"))
        
        if not image_files:
            raise ValueError("No image files found in ZIP archive")
        
        if len(image_files) > settings.max_batch_size:
            raise ValueError(f"Too many images: {len(image_files)} (max: {settings.max_batch_size})")
        
        # Initialize validator
        validator = LabelValidator(ocr_backend=ocr_backend)
        if ocr_backend == "ollama" and hasattr(validator.ocr, 'timeout'):
            validator.ocr.timeout = timeout
        
        # Process each image
        results = []
        total_time = 0.0
        
        for i, image_path in enumerate(sorted(image_files), 1):
            try:
                logger.info(f"Processing {i}/{len(image_files)}: {image_path.name}")
                
                # Look for ground truth JSON
                json_path = image_path.with_suffix('.json')
                ground_truth = None
                
                if json_path.exists():
                    try:
                        with open(json_path, 'r') as f:
                            ground_truth = json.load(f)
                        if 'ground_truth' in ground_truth:
                            ground_truth = ground_truth['ground_truth']
                    except Exception as e:
                        logger.warning(f"Failed to load ground truth for {image_path.name}: {e}")
                
                # Validate label
                result = validator.validate_label(str(image_path), ground_truth)
                result['image_path'] = image_path.name
                result['thumbnail'] = create_thumbnail(image_path)
                results.append(result)
                total_time += result['processing_time_seconds']
            
            except Exception as e:
                logger.error(f"Failed to process {image_path.name}: {e}", exc_info=True)
                results.append({
                    "status": "ERROR",
                    "validation_level": "STRUCTURAL_ONLY",
                    "extracted_fields": {},
                    "validation_results": {"structural": [], "accuracy": []},
                    "violations": [],
                    "warnings": [],
                    "processing_time_seconds": 0.0,
                    "image_path": image_path.name,
                    "thumbnail": "",
                    "error": str(e)
                })
        
        # Calculate summary
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
        
        return templates.TemplateResponse(
            "batch_results.html",
            {
                "request": request,
                "username": username,
                "results": results,
                "summary": summary,
                "filename": batch_file.filename
            }
        )
    
    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        error_msg = str(e)
        
        if "Cannot connect" in error_msg or "not found" in error_msg:
            error_msg = f"Ollama backend unavailable: {error_msg}. Please use Tesseract or wait for model download."
        
        return templates.TemplateResponse(
            "batch.html",
            {
                "request": request,
                "username": username,
                "error": error_msg,
                "max_batch_size": settings.max_batch_size,
                "ollama_host": settings.ollama_host,
                "default_timeout": settings.ollama_timeout_seconds
            }
        )
    
    finally:
        # Cleanup will happen automatically via cleanup_old_temp_files()
        pass

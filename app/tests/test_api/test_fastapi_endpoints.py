"""API tests for FastAPI endpoints."""
import pytest
import json
import zipfile
import io
from pathlib import Path
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient

from api import app
from config import get_settings


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    """
    FastAPI test client with authenticated session.
    
    Creates a session and adds the session cookie to the client.
    """
    from auth import create_session_cookie, SESSION_COOKIE_NAME
    
    # Create a session for test user (no AWS secrets needed - just a session)
    session_cookie = create_session_cookie("testuser")
    
    # Add session cookie to client
    client.cookies.set(SESSION_COOKIE_NAME, session_cookie)
    
    return client


@pytest.fixture
def sample_image_bytes(good_label_path):
    """Load sample image as bytes."""
    if not good_label_path.exists():
        pytest.skip(f"Sample image not found: {good_label_path}")
    
    with open(good_label_path, 'rb') as f:
        return f.read()


@pytest.fixture
def sample_ground_truth_json():
    """Sample ground truth as JSON string."""
    return json.dumps({
        'brand_name': 'Ridge & Co.',
        'abv': 7.5,
        'net_contents': '64 fl oz',
        'bottler': 'Imported by Black Brewing, San Francisco, CA',
        'product_type': 'Hefeweizen'
    })


@pytest.fixture
def sample_batch_zip(samples_dir):
    """Create a sample batch ZIP file with 3 images."""
    if not samples_dir.exists():
        pytest.skip(f"Samples directory not found: {samples_dir}")
    
    # Find first 3 good labels
    good_labels = sorted(samples_dir.glob("label_good_*.jpg"))[:3]
    if len(good_labels) < 3:
        pytest.skip("Not enough sample images for batch test")
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for label_path in good_labels:
            # Add image
            zf.write(label_path, arcname=label_path.name)
            
            # Add corresponding JSON if exists
            json_path = label_path.with_suffix('.json')
            if json_path.exists():
                zf.write(json_path, arcname=json_path.name)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


@pytest.fixture
def invalid_zip_bytes():
    """Create invalid ZIP file (just random bytes)."""
    return b"This is not a valid ZIP file content"


@pytest.fixture
def empty_zip_bytes():
    """Create empty ZIP file with no images."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add a text file but no images
        zf.writestr("readme.txt", "No images here")
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


@pytest.fixture
def large_image_bytes():
    """Create a fake large image (exceeds size limit)."""
    settings = get_settings()
    # Create bytes larger than max_file_size_mb
    return b"x" * (settings.max_file_size_bytes + 1000)


# ============================================================================
# Single Verify Endpoint Tests
# ============================================================================

def test_verify_success_no_ground_truth(authenticated_client, sample_image_bytes):
    """Test single label verification without ground truth (structural only)."""
    response = authenticated_client.post(
        "/verify",
        files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "status" in data
    assert data["status"] in ["COMPLIANT", "NON_COMPLIANT", "PARTIAL_VALIDATION"]
    assert "validation_level" in data
    assert "extracted_fields" in data
    assert "validation_results" in data
    assert "violations" in data
    assert "processing_time_seconds" in data
    
    # Should be structural only without ground truth
    assert data["validation_level"] == "STRUCTURAL_ONLY"


def test_verify_success_with_ground_truth(authenticated_client, sample_image_bytes, sample_ground_truth_json):
    """Test single label verification with ground truth (full validation)."""
    response = authenticated_client.post(
        "/verify",
        files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")},
        data={
            "ground_truth": sample_ground_truth_json
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should perform full validation with ground truth
    assert data["validation_level"] == "FULL_VALIDATION"
    assert "accuracy" in data["validation_results"]


@patch('api.LabelValidator')
def test_verify_with_ollama_backend(mock_validator_class, authenticated_client, sample_image_bytes):
    """Test single label verification (uses Ollama as the only backend)."""
    # Mock the validator to avoid actual Ollama call
    mock_validator = Mock()
    mock_validator.validate_label.return_value = {
        "status": "COMPLIANT",
        "validation_level": "STRUCTURAL_ONLY",
        "extracted_fields": {
            "brand_name": "Test Brand",
            "abv_numeric": 12.5,
            "government_warning": {"present": True}
        },
        "validation_results": {
            "structural": [],
            "accuracy": []
        },
        "violations": [],
        "warnings": [],
        "processing_time_seconds": 1.5
    }
    mock_validator_class.return_value = mock_validator
    
    response = authenticated_client.post(
        "/verify",
        files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLIANT"
    
    # Verify validator was called (now without ocr_backend parameter)
    mock_validator_class.assert_called_once()


def test_verify_with_custom_timeout(authenticated_client, sample_image_bytes):
    """Test single label verification with custom timeout."""
    response = authenticated_client.post(
        "/verify",
        files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")},
        data={
            "timeout": 30
        }
    )
    
    # Should succeed regardless of timeout
    assert response.status_code == 200


def test_verify_invalid_file_type(authenticated_client):
    """Test verification with invalid file type (not an image)."""
    text_content = b"This is a text file, not an image"
    
    response = authenticated_client.post(
        "/verify",
        files={"image": ("document.txt", text_content, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid file type" in data["detail"]


def test_verify_invalid_ground_truth_json(authenticated_client, sample_image_bytes):
    """Test verification with invalid ground truth JSON."""
    response = authenticated_client.post(
        "/verify",
        files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")},
        data={"ground_truth": "this is not valid JSON{"}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid ground truth JSON" in data["detail"]


def test_verify_missing_image(authenticated_client):
    """Test verification without image file."""
    response = authenticated_client.post("/verify")
    
    assert response.status_code == 422  # Validation error


@patch('api.LabelValidator')
def test_verify_ocr_failure(mock_validator_class, authenticated_client, sample_image_bytes):
    """Test verification when OCR processing fails."""
    # Mock validator to raise an exception
    mock_validator = Mock()
    mock_validator.validate_label.side_effect = Exception("OCR processing failed")
    mock_validator_class.return_value = mock_validator
    
    response = authenticated_client.post(
        "/verify",
        files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 500
    data = response.json()
    assert "verification failed" in data["detail"].lower()


# ============================================================================
# Batch Verify Endpoint Tests
# ============================================================================

def test_batch_success(authenticated_client, sample_batch_zip):
    """Test batch verification with valid ZIP file."""
    response = authenticated_client.post(
        "/verify/batch",
        files={"batch_file": ("batch.zip", sample_batch_zip, "application/zip")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "results" in data
    assert "summary" in data
    
    # Check summary
    summary = data["summary"]
    assert "total" in summary
    assert "compliant" in summary
    assert "non_compliant" in summary
    assert "errors" in summary
    assert "total_processing_time_seconds" in summary
    
    # Should have processed 3 images
    assert summary["total"] == 3
    assert len(data["results"]) == 3
    
    # Each result should have required fields
    for result in data["results"]:
        assert "status" in result
        assert "validation_level" in result
        assert "image_path" in result


def test_batch_with_ground_truth(authenticated_client, sample_batch_zip):
    """Test batch verification with ground truth JSON files in ZIP."""
    # The sample_batch_zip fixture includes JSON files
    response = authenticated_client.post(
        "/verify/batch",
        files={"batch_file": ("batch.zip", sample_batch_zip, "application/zip")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # At least some results should have full validation
    full_validations = [
        r for r in data["results"]
        if r.get("validation_level") == "FULL_VALIDATION"
    ]
    assert len(full_validations) > 0


def test_batch_invalid_zip(authenticated_client, invalid_zip_bytes):
    """Test batch verification with invalid/corrupt ZIP file."""
    response = authenticated_client.post(
        "/verify/batch",
        files={"batch_file": ("batch.zip", invalid_zip_bytes, "application/zip")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Invalid" in data["detail"] or "corrupt" in data["detail"].lower()


def test_batch_empty_zip(authenticated_client, empty_zip_bytes):
    """Test batch verification with ZIP containing no images."""
    response = authenticated_client.post(
        "/verify/batch",
        files={"batch_file": ("batch.zip", empty_zip_bytes, "application/zip")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "No image files found" in data["detail"]


def test_batch_invalid_file_type(authenticated_client):
    """Test batch verification with non-ZIP file."""
    response = authenticated_client.post(
        "/verify/batch",
        files={"batch_file": ("document.txt", b"not a zip", "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert ("Invalid file type" in data["detail"] or "ZIP archive" in data["detail"])


@pytest.mark.parametrize("num_images", [51, 100])
def test_batch_too_many_images(authenticated_client, samples_dir, num_images):
    """Test batch verification with too many images."""
    settings = get_settings()
    
    # Skip if we don't have enough samples
    good_labels = list(samples_dir.glob("label_good_*.jpg"))
    if len(good_labels) < 10:
        pytest.skip("Not enough sample images for this test")
    
    # Create ZIP with more images than allowed
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add same images multiple times with different names
        for i in range(min(num_images, settings.max_batch_size + 1)):
            label_path = good_labels[i % len(good_labels)]
            zf.write(label_path, arcname=f"label_{i:03d}.jpg")
    
    zip_buffer.seek(0)
    
    response = authenticated_client.post(
        "/verify/batch",
        files={"batch_file": ("batch.zip", zip_buffer.getvalue(), "application/zip")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Too many images" in data["detail"]


# ============================================================================
# CORS & Documentation Tests
# ============================================================================

def test_cors_headers(authenticated_client, sample_image_bytes):
    """Test that CORS headers are present in responses."""
    response = authenticated_client.post(
        "/verify",
        files={"image": ("label.jpg", sample_image_bytes, "image/jpeg")},
        headers={"Origin": "http://example.com"}
    )
    
    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers


def test_docs_endpoint(client):
    """Test that Swagger UI documentation endpoint is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_redoc_endpoint_removed(client):
    """Test that the ReDoc endpoint is disabled."""
    response = client.get("/redoc")
    assert response.status_code == 404


def test_root_endpoint(client):
    """Test root endpoint redirects to UI."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    # Root redirects to /ui/verify which then redirects to /ui/login (requires auth)
    # We're just testing the first redirect here
    assert response.headers["location"] in ["/ui/verify", "/ui/login"]


def test_health_endpoint(client):
    """Test health endpoint returns backend status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "status" in data
    assert "backends" in data
    assert "capabilities" in data
    
    # Check backends - only Ollama now
    assert "ollama" in data["backends"]
    
    # Check capabilities
    assert "ocr_backends" in data["capabilities"]
    assert isinstance(data["capabilities"]["ocr_backends"], list)



# ============================================================================
# Error Response Tests
# ============================================================================

def test_error_response_structure(authenticated_client):
    """Test that error responses have consistent structure."""
    # Trigger a 400 error
    response = authenticated_client.post(
        "/verify",
        files={"image": ("document.txt", b"not an image", "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    
    # Check error response structure
    assert "detail" in data
    assert "error_code" in data
    assert "correlation_id" in data


# ============================================================================
# Edge Cases
# ============================================================================

def test_verify_with_png_image(authenticated_client, samples_dir):
    """Test verification with PNG image (if available)."""
    # Try to find a PNG sample or skip
    png_files = list(samples_dir.glob("*.png"))
    if not png_files:
        pytest.skip("No PNG samples available")
    
    with open(png_files[0], 'rb') as f:
        png_bytes = f.read()
    
    response = authenticated_client.post(
        "/verify",
        files={"image": ("label.png", png_bytes, "image/png")}
    )
    
    assert response.status_code == 200


def test_batch_with_custom_timeout(authenticated_client, sample_batch_zip):
    """Test batch verification with custom timeout."""
    response = authenticated_client.post(
        "/verify/batch",
        files={"batch_file": ("batch.zip", sample_batch_zip, "application/zip")},
        data={
            "timeout": 30
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total"] == 3


@patch('api.LabelValidator')
def test_batch_partial_failure(mock_validator_class, authenticated_client, sample_batch_zip):
    """Test batch processing when some images fail (should return partial results)."""
    # Mock validator to fail on second image
    mock_validator = Mock()
    call_count = [0]
    
    def side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 2:
            raise Exception("Processing failed for this image")
        return {
            "status": "COMPLIANT",
            "validation_level": "STRUCTURAL_ONLY",
            "extracted_fields": {},
            "validation_results": {"structural": [], "accuracy": []},
            "violations": [],
            "warnings": [],
            "processing_time_seconds": 1.0
        }
    
    mock_validator.validate_label.side_effect = side_effect
    mock_validator_class.return_value = mock_validator
    
    response = authenticated_client.post(
        "/verify/batch",
        files={"batch_file": ("batch.zip", sample_batch_zip, "application/zip")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 3 results (2 success + 1 error)
    assert data["summary"]["total"] == 3
    assert data["summary"]["errors"] == 1
    
    # Check that error result has error field
    error_results = [r for r in data["results"] if r.get("status") == "ERROR"]
    assert len(error_results) == 1
    assert "error" in error_results[0]

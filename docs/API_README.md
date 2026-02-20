# TTB Label Verifier - API Documentation

## Overview

REST API for validating alcohol beverage labels against 27 CFR regulations. Supports single label verification and batch processing with file uploads.

**Base URL:** `http://localhost:8000` (development)  
**Version:** 1.0.0  
**Status:** Prototype (Open Access)

---

## Quick Start

### Start the API

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Check status
curl http://localhost:8000/docs
```

### Test Single Label Verification

```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@samples/label_good_001.jpg" \
  -F "ocr_backend=tesseract"
```

---

## Endpoints

### 1. Single Label Verification

**Endpoint:** `POST /verify`

**Description:** Verifies a single alcohol beverage label image against 27 CFR regulations.

#### Request

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Label image (max 10MB, .jpg/.jpeg/.png) |
| `ground_truth` | String (JSON) | No | Expected values for Tier 2 validation |
| `ocr_backend` | String | No | OCR engine: `tesseract` (fast, default) or `ollama` (accurate) |

**Ground Truth JSON Format:**
```json
{
  "brand_name": "Ridge & Co.",
  "abv": 7.5,
  "net_contents": "64 fl oz",
  "bottler": "Imported by Black Brewing, San Francisco, CA",
  "product_type": "Hefeweizen"
}
```

#### Response

**Status Code:** `200 OK`

**Content-Type:** `application/json`

**Response Body:**
```json
{
  "status": "NON_COMPLIANT",
  "validation_level": "FULL_VALIDATION",
  "extracted_fields": {
    "brand_name": "Hefeweizen",
    "product_type": "Hefeweizen",
    "abv": "7.5% ABV",
    "abv_numeric": 7.5,
    "net_contents": "64 fl oz",
    "bottler": "Imported by Black Brewing, San Francisco, CA",
    "country": "Product of Italy",
    "government_warning": {
      "present": true,
      "header_correct": true,
      "text_correct": true
    }
  },
  "validation_results": {
    "structural": [
      {
        "field": "brand_name",
        "valid": true,
        "expected": null,
        "actual": "Hefeweizen"
      },
      {
        "field": "abv",
        "valid": true,
        "expected": null,
        "actual": "7.5%"
      }
    ],
    "accuracy": [
      {
        "field": "brand_name",
        "valid": false,
        "expected": "Ridge & Co.",
        "actual": "Hefeweizen",
        "error": "Brand name mismatch (similarity: 9.5%)",
        "similarity_score": 0.095
      }
    ]
  },
  "violations": [
    {
      "field": "brand_name",
      "type": "accuracy",
      "message": "Brand name mismatch (similarity: 9.5%)",
      "expected": "Ridge & Co.",
      "actual": "Hefeweizen"
    }
  ],
  "warnings": [],
  "processing_time_seconds": 0.827
}
```

**Status Values:**
- `COMPLIANT` - Label passes all validation checks
- `NON_COMPLIANT` - Label has one or more violations
- `PARTIAL_VALIDATION` - Only structural validation performed (no ground truth)

**Validation Levels:**
- `STRUCTURAL_ONLY` - Tier 1 validation (presence of required fields)
- `FULL_VALIDATION` - Tier 1 + Tier 2 (accuracy against ground truth)

#### Example Requests

**Basic Verification (Tesseract):**
```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@label.jpg"
```

**With Ground Truth:**
```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@label.jpg" \
  -F 'ground_truth={"brand_name":"Ridge & Co.","abv":7.5,"net_contents":"64 fl oz","bottler":"Imported by Black Brewing, San Francisco, CA","product_type":"Hefeweizen"}'
```

**Using Ollama AI (Slower, More Accurate):**
```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@label.jpg" \
  -F "ocr_backend=ollama"
```

**Python Client Example:**
```python
import requests

url = "http://localhost:8000/verify"
files = {"image": open("label.jpg", "rb")}
data = {
    "ground_truth": '{"brand_name":"Ridge & Co.","abv":7.5}',
    "ocr_backend": "tesseract"
}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Status: {result['status']}")
print(f"Violations: {len(result['violations'])}")
```

---

### 2. Batch Label Verification

**Endpoint:** `POST /verify/batch`

**Description:** Verifies multiple label images in a single request. Accepts a ZIP file containing images and optional JSON metadata files.

#### Request

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `batch_file` | File (ZIP) | Yes | ZIP file containing images and optional JSON files (max 50 images) |
| `ocr_backend` | String | No | OCR engine: `tesseract` (default) or `ollama` |

**ZIP File Structure:**
```
batch.zip
├── label_001.jpg           # Required: image file
├── label_001.json          # Optional: ground truth metadata
├── label_002.jpg
├── label_002.json
├── label_003.jpg
└── ...
```

**Naming Convention:**
- JSON files must match image filenames (e.g., `label_001.jpg` → `label_001.json`)
- If JSON file missing, only structural validation performed
- Maximum 50 images per batch
- Each image max 10MB

**JSON Metadata Format (Same as Single Verification):**
```json
{
  "brand_name": "Ridge & Co.",
  "abv": 7.5,
  "net_contents": "64 fl oz",
  "bottler": "Imported by Black Brewing, San Francisco, CA",
  "product_type": "Hefeweizen"
}
```

#### Response

**Status Code:** `200 OK`

**Content-Type:** `application/json`

**Response Body:**
```json
{
  "results": [
    {
      "filename": "label_001.jpg",
      "status": "NON_COMPLIANT",
      "validation_level": "FULL_VALIDATION",
      "extracted_fields": {...},
      "validation_results": {...},
      "violations": [...],
      "warnings": [],
      "processing_time_seconds": 0.72
    },
    {
      "filename": "label_002.jpg",
      "status": "COMPLIANT",
      "validation_level": "STRUCTURAL_ONLY",
      "extracted_fields": {...},
      "validation_results": {...},
      "violations": [],
      "warnings": ["No ground truth provided - only structural validation performed"],
      "processing_time_seconds": 0.68
    }
  ],
  "summary": {
    "total": 2,
    "compliant": 1,
    "non_compliant": 1,
    "total_time_seconds": 1.40,
    "average_time_seconds": 0.70
  }
}
```

#### Example Requests

**Create Batch ZIP:**
```bash
# Create ZIP with images and metadata
cd samples
zip batch.zip label_good_001.jpg label_good_001.json \
              label_bad_001.jpg label_bad_001.json
```

**Upload Batch:**
```bash
curl -X POST http://localhost:8000/verify/batch \
  -F "batch_file=@batch.zip" \
  -F "ocr_backend=tesseract"
```

**Python Client Example:**
```python
import requests
import zipfile
import os

# Create ZIP file
with zipfile.ZipFile('batch.zip', 'w') as zf:
    for img in ['label_001.jpg', 'label_002.jpg']:
        zf.write(img)
        json_file = img.replace('.jpg', '.json')
        if os.path.exists(json_file):
            zf.write(json_file)

# Upload batch
url = "http://localhost:8000/verify/batch"
files = {"batch_file": open("batch.zip", "rb")}
data = {"ocr_backend": "tesseract"}

response = requests.post(url, files=files, data=data)
result = response.json()

print(f"Total: {result['summary']['total']}")
print(f"Compliant: {result['summary']['compliant']}")
print(f"Non-compliant: {result['summary']['non_compliant']}")
```

---

## Error Responses

### 400 Bad Request

**Causes:**
- Invalid file format (not .jpg, .jpeg, or .png)
- Malformed JSON in ground truth
- Invalid ZIP file structure
- Missing required parameters

**Example:**
```json
{
  "error": "Invalid file format",
  "detail": "Only .jpg, .jpeg, and .png files are supported",
  "timestamp": "2026-02-16T12:00:00Z"
}
```

### 413 Payload Too Large

**Causes:**
- Image file >10MB
- Batch >50 images
- ZIP file too large

**Example:**
```json
{
  "error": "File too large",
  "detail": "Maximum file size is 10MB",
  "timestamp": "2026-02-16T12:00:00Z"
}
```

### 422 Unprocessable Entity

**Causes:**
- Validation error (Pydantic model validation)
- Invalid enum value (e.g., ocr_backend not 'tesseract' or 'ollama')

**Example:**
```json
{
  "error": "Validation error",
  "detail": "ocr_backend must be 'tesseract' or 'ollama'",
  "timestamp": "2026-02-16T12:00:00Z"
}
```

### 500 Internal Server Error

**Causes:**
- OCR backend failure
- Unexpected exception
- File I/O error

**Example:**
```json
{
  "error": "Internal server error",
  "detail": "OCR processing failed",
  "timestamp": "2026-02-16T12:00:00Z"
}
```

---

## Interactive API Documentation

FastAPI provides auto-generated interactive documentation:

### Swagger UI
**URL:** http://localhost:8000/docs

Features:
- Try endpoints directly in browser
- See request/response schemas
- Download OpenAPI spec
- Test file uploads

---

## Performance

### Processing Times (Tesseract Backend)

| Scenario | Average Time | Notes |
|----------|--------------|-------|
| Single label (Tesseract) | 0.7s | Meets 5-second requirement |
| Single label (Ollama) | 58s | High accuracy, slow |
| Batch 10 labels | 7s | ~0.7s per label |
| Batch 50 labels | 36s | ~0.72s per label |

### Recommendations

**For Fast Results:**
- Use Tesseract backend (default)
- Average 0.7s per label
- Suitable for real-time validation

**For High Accuracy:**
- Use Ollama backend
- Average 58s per label
- Better for decorative fonts
- Recommended for critical validation

**For Large Batches:**
- Use batch endpoint
- Process up to 50 labels at once
- Consider splitting batches >20 labels if using Ollama

---

## Configuration

### Environment Variables

Configure via `.env` file or environment:

```bash
# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.2-vision

# App Configuration
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=10
MAX_BATCH_SIZE=50
DEFAULT_OCR_BACKEND=tesseract

# CORS Configuration
CORS_ORIGINS=["*"]
```

### CORS Policy

**Current:** Allow all origins (`*`)

**Production Recommendation:**
```bash
# Restrict to specific domains
CORS_ORIGINS=["https://ttb.gov","https://cola.ttb.gov"]
```

---

## Production Considerations

### This is a Prototype

Current API is designed for demonstration and development:

✅ **Included:**
- File upload validation
- Error handling
- Logging to stdout
- CORS support

❌ **Not Included (Add in Production):**
- Authentication (API keys, JWT)
- Rate limiting
- Request tracing
- Metrics (Prometheus)
- API versioning

### Recommended Production Architecture

```
Internet
   ↓
AWS API Gateway
   ├── Authentication (API keys)
   ├── Rate limiting
   ├── Request throttling
   ├── CloudWatch metrics
   ↓
EC2 / ECS / Lambda
   ↓
Docker Container (TTB Verifier)
```

**Why API Gateway?**
- ✅ Handles authentication/authorization
- ✅ Built-in rate limiting
- ✅ Request validation
- ✅ CloudWatch integration
- ✅ Usage plans and quotas
- ✅ No code changes needed

### Adding Features Later

**Authentication (Commented in Code):**
```python
# from fastapi.security import APIKeyHeader
# api_key_header = APIKeyHeader(name="X-API-Key")
# 
# @app.post("/verify")
# async def verify_label(api_key: str = Depends(api_key_header)):
#     # Validate API key
#     pass
```

**Rate Limiting (Commented in Code):**
```python
# from slowapi import Limiter
# limiter = Limiter(key_func=get_remote_address)
# 
# @limiter.limit("100/hour")
# @app.post("/verify")
# async def verify_label(...):
#     pass
```

**Metrics (Commented in Code):**
```python
# from prometheus_fastapi_instrumentator import Instrumentator
# Instrumentator().instrument(app).expose(app)
```

---

## Troubleshooting

### Ollama Not Available

**Symptom:** API works but Ollama backend fails

**Solution:**
```bash
# Check Ollama status
docker-compose ps ollama

# Check if model downloaded
docker-compose exec ollama ollama list

# Pull model if missing
docker-compose exec ollama ollama pull llama3.2-vision

# Restart services
docker-compose restart
```

### File Upload Fails

**Symptom:** 413 or 400 errors on upload

**Check:**
- File size <10MB: `ls -lh label.jpg`
- Valid format (.jpg, .jpeg, .png)
- Not corrupted: `file label.jpg`

### Slow Processing

**Symptom:** Requests timeout or take >60s

**Cause:** Using Ollama backend

**Solution:**
- Use Tesseract for fast results (0.7s)
- Increase client timeout to 120s for Ollama
- Consider batch processing for multiple labels

### CORS Errors

**Symptom:** Browser blocks requests from frontend

**Solution:**
```bash
# Update CORS_ORIGINS in .env
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# Restart services
docker-compose restart verifier
```

---

## Code Examples

### Complete Python Client

```python
#!/usr/bin/env python3
"""TTB Label Verifier API Client"""
import requests
import json
from pathlib import Path

class TTBVerifierClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def verify_single(self, image_path, ground_truth=None, ocr_backend="tesseract"):
        """Verify a single label."""
        url = f"{self.base_url}/verify"
        
        files = {"image": open(image_path, "rb")}
        data = {"ocr_backend": ocr_backend}
        
        if ground_truth:
            data["ground_truth"] = json.dumps(ground_truth)
        
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        return response.json()
    
    def verify_batch(self, zip_path, ocr_backend="tesseract"):
        """Verify a batch of labels."""
        url = f"{self.base_url}/verify/batch"
        
        files = {"batch_file": open(zip_path, "rb")}
        data = {"ocr_backend": ocr_backend}
        
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        return response.json()

# Example usage
if __name__ == "__main__":
    client = TTBVerifierClient()
    
    # Single label
    result = client.verify_single(
        "label.jpg",
        ground_truth={"brand_name": "Ridge & Co.", "abv": 7.5}
    )
    print(f"Status: {result['status']}")
    print(f"Violations: {len(result['violations'])}")
    
    # Batch
    batch_result = client.verify_batch("batch.zip")
    print(f"Total: {batch_result['summary']['total']}")
    print(f"Compliant: {batch_result['summary']['compliant']}")
```

### cURL Script

```bash
#!/bin/bash
# verify_label.sh - Verify label via API

API_URL="http://localhost:8000"
IMAGE_FILE="$1"
GROUND_TRUTH="$2"

if [ -z "$IMAGE_FILE" ]; then
    echo "Usage: $0 <image_file> [ground_truth_json]"
    exit 1
fi

if [ -n "$GROUND_TRUTH" ]; then
    # With ground truth
    curl -X POST "$API_URL/verify" \
        -F "image=@$IMAGE_FILE" \
        -F "ground_truth=$GROUND_TRUTH" \
        | python3 -m json.tool
else
    # Without ground truth
    curl -X POST "$API_URL/verify" \
        -F "image=@$IMAGE_FILE" \
        | python3 -m json.tool
fi
```

---

## API Reference Summary

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/verify` | POST | Single label verification | No |
| `/verify/batch` | POST | Batch label verification | No |
| `/docs` | GET | Swagger UI documentation | No |

**Request Limits:**
- Max file size: 10MB per image
- Max batch size: 50 images
- Allowed formats: .jpg, .jpeg, .png

**OCR Backends:**
- `tesseract` (default): Fast (~0.7s), moderate accuracy
- `ollama`: Slow (~58s), high accuracy

**Validation Tiers:**
- Tier 1 (Structural): Checks presence of required fields
- Tier 2 (Accuracy): Compares against ground truth (requires metadata)

---

## Support & Resources

- **Project Repository:** (Add GitHub URL)
- **Docker Hub:** (Add Docker Hub URL when published)
- **Issue Tracker:** (Add GitHub Issues URL)
- **Documentation:** `docs/` directory in repository

---

**Last Updated:** 2026-02-16  
**API Version:** 1.0.0  
**Status:** Prototype - Open Access

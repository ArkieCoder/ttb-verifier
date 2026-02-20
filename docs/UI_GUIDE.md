# TTB Label Verifier - Web UI Guide

Comprehensive guide for using the TTB Label Verifier web interface.

## Table of Contents

- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Single Label Verification](#single-label-verification)
- [Batch Verification](#batch-verification)
- [OCR Backend Selection](#ocr-backend-selection)
- [Understanding Results](#understanding-results)
- [Troubleshooting](#troubleshooting)
- [API Access](#api-access)

---

## Quick Start

1. **Navigate to:** `https://<your-domain>`
2. **Login** with credentials configured in AWS Secrets Manager
3. **Upload** a label image or batch ZIP file
4. **Review** compliance results

---

## Authentication

### Login Process

The UI uses **session-based authentication** with secure httponly cookies.

**Access:** `https://<your-domain>/ui/login`

**Credentials:**
- Stored in AWS Secrets Manager: `TTB_DEFAULT_USER` and `TTB_DEFAULT_PASS`
- Configure via: `./scripts/setup_secrets.sh <username> <password>`

**Session Details:**
- Duration: 4 hours
- Cookie: `session_id` (httponly, secure, SameSite=Lax)
- Automatic logout on expiration

### Host Restriction

The service is **only accessible** via:
- ✅ Your configured domain (e.g., `ttb-verifier.example.com`)
- ✅ `localhost` / `127.0.0.1` (development)

Direct access via ALB DNS or IP address will result in **403 Forbidden**.

### Logout

Click your username in the top-right corner → **Logout**

---

## Single Label Verification

### Step 1: Upload Image

1. Navigate to **Single Verification** (default home page)
2. Click **Choose File** and select a label image
   - Supported: JPEG, PNG
   - Max size: 10MB
   - Recommended: Clear, well-lit photos

### Step 2: Add Metadata (Optional)

For **Tier 2 accuracy validation**, provide expected values:

| Field | Description | Example |
|-------|-------------|---------|
| Brand Name | Official brand/product name | `Ridge & Co.` |
| Product Type | Beverage category | `Whiskey`, `Beer`, `Wine` |
| ABV | Alcohol by volume percentage | `7.5` |
| Net Contents | Volume with unit | `750 ML` |
| Bottler | Company name | `Acme Distillery` |

**Without metadata:** Only Tier 1 (structural) validation is performed.

### Step 3: Choose OCR Backend

- **Tesseract** (default): Fast (~1s), good recall, moderate precision
- **Ollama Vision AI**: Accurate (~10-30s), better for complex labels
  - Automatically disabled if model is downloading
  - Adjust timeout for large images (default: 60s)

### Step 4: Submit & Review Results

Click **Verify Label** and wait for processing.

**Results show:**
- ✅ **COMPLIANT** / ❌ **NON-COMPLIANT** / ⚠️ **PARTIAL**
- Extracted fields (brand, ABV, warning, etc.)
- Violations with expected vs. actual values
- Processing time

---

## Batch Verification

### Step 1: Prepare ZIP File

Create a ZIP archive with:

```
batch.zip
├── label_001.jpg           # Required: Image file
├── label_001.json          # Optional: Ground truth
├── label_002.png
├── label_002.json
└── ...
```

**Limits:**
- Max 50 images per batch
- Supported: JPEG, PNG
- Ground truth format: `{"brand_name": "...", "abv": 7.5, ...}`

**Ground Truth JSON Example:**
```json
{
  "brand_name": "Ridge & Co.",
  "abv": 7.5,
  "net_contents": "750 ML",
  "product_type": "Whiskey",
  "bottler": "Acme Distillery LLC"
}
```

### Step 2: Upload & Process

1. Navigate to **Batch Verification**
2. Select your ZIP file
3. Choose OCR backend (Tesseract or Ollama)
4. Click **Upload & Process Batch**

**Important:** Batch processing is **synchronous**. Expect:
- Tesseract: 2-5 seconds per image
- Ollama: 10-30 seconds per image

For 50 images with Ollama, processing may take **15-25 minutes**.

### Step 3: Review Results

**Summary Statistics:**
- Total labels processed
- Compliant / Non-compliant / Errors

**Results Table:**
- Thumbnail preview (100x100px)
- Filename
- Status badge
- Processing time
- Violations (hover for details)

**Hover over violations** to see detailed popover with:
- Field name
- Violation message
- Expected vs. actual values

---

## OCR Backend Selection

### Tesseract OCR

**Best for:**
- Fast processing (< 1 second)
- Batch operations with many images
- Simple, well-structured labels

**Characteristics:**
- 100% recall (finds all fields)
- ~50% precision (may have false positives)
- No GPU required
- Always available

### Ollama Vision AI (llama3.2-vision)

**Best for:**
- Complex layouts
- Handwritten or stylized text
- Maximum accuracy requirements

**Characteristics:**
- ~58 seconds per label
- Excellent accuracy
- Requires model download (first-time: 5-10 minutes)
- Shows "Not Ready" while downloading

**Status Indicator:**
- 🟢 **Available** - Model loaded, ready to use
- 🔴 **Unavailable** - Model downloading or service offline
- 🟡 **Checking...** - Querying health endpoint

The UI automatically **polls `/health`** every 30 seconds to update status.

---

## Understanding Results

### Compliance Status

| Status | Meaning |
|--------|---------|
| ✅ **COMPLIANT** | All validation checks passed |
| ❌ **NON-COMPLIANT** | One or more violations found |
| ⚠️ **PARTIAL_VALIDATION** | Completed with warnings |
| ❓ **ERROR** | Processing failed |

### Validation Levels

- **STRUCTURAL_ONLY**: Tier 1 validation (required fields present)
- **FULL_VALIDATION**: Tier 1 + Tier 2 (accuracy checks with metadata)

### Extracted Fields

All OCR-extracted information from the label:

- **Brand Name**: Product identifier
- **Product Type**: Beverage category (beer, wine, spirits)
- **ABV**: Alcohol by volume percentage
- **ABV Numeric**: Parsed numeric value
- **Net Contents**: Volume (e.g., "750 ML")
- **Bottler**: Bottling company
- **Country**: Country of origin
- **Government Warning**: Presence and correctness

### Violations

Each violation shows:

- **Type**: `STRUCTURAL` or `ACCURACY`
- **Field**: Name of violating field
- **Message**: Human-readable description
- **Expected**: Ground truth value (if provided)
- **Actual**: OCR-extracted value

**Example:**
```
Type: ACCURACY
Field: abv
Message: ABV tolerance exceeded
Expected: 7.5%
Actual: 8.2%
```

### Detailed Validation Results

**Tier 1 (Structural):**
- Checks for presence of required fields
- Government warning format validation
- Basic field extraction

**Tier 2 (Accuracy):**
- Fuzzy string matching (90% threshold for brand names)
- ABV tolerance checks (product-specific)
- Exact or near-exact matches for other fields

---

## Troubleshooting

### "Service Temporarily Unavailable" (503)

**Causes:**
- Application is starting up (2-3 minutes)
- Ollama model is downloading (5-10 minutes)
- Instance reboot or deployment in progress

**Solution:**
- Wait and refresh (page auto-refreshes every 30 seconds)
- Check `/health` endpoint for backend status

### "403 Forbidden"

**Causes:**
- Accessing via ALB DNS or IP address instead of configured domain
- Host header mismatch

**Solution:**
- Use your configured domain (set via `domain_name` Terraform variable)
- For local development: use `localhost` or `127.0.0.1`

### "401 Unauthorized"

**Causes:**
- Session expired (after 4 hours)
- Cookie blocked by browser

**Solution:**
- Re-login via `/ui/login`
- Ensure cookies are enabled
- Check browser console for errors

### Ollama Shows "Unavailable"

**Causes:**
- Model still downloading (first-time setup)
- Ollama service offline

**Solution:**
- Wait 5-10 minutes for model download
- Use Tesseract backend as fallback
- Check `/health` endpoint: `curl https://ttb-verifier.unitedentropy.com/health`

### Batch Processing Hangs

**Causes:**
- Too many images (> 50)
- Very large images
- Ollama timeout too short

**Solution:**
- Reduce batch size to ≤ 50 images
- Resize images to < 2MB each
- Increase Ollama timeout (default: 60s)
- Use Tesseract for large batches

### Images Won't Upload

**Causes:**
- File size > 10MB
- Invalid file type (not JPEG/PNG)
- Corrupted image file

**Solution:**
- Compress images to < 10MB
- Convert to JPEG or PNG
- Verify file integrity

---

## API Access

### Using the API Programmatically

The web UI is built on top of the REST API. You can access the same functionality programmatically.

**Login and get session cookie:**
```bash
curl -c cookies.txt -X POST https://<your-domain>/ui/login \
  -d "username=<user>&password=<pass>"
```

**Verify a label with session:**
```bash
curl -b cookies.txt -X POST https://<your-domain>/verify \
  -F "image=@label.jpg" \
  -F "ocr_backend=tesseract"
```

**Batch verification:**
```bash
curl -b cookies.txt -X POST https://<your-domain>/verify/batch \
  -F "batch_file=@labels.zip"
```

### Test Script

Use the included test script to verify API functionality:

```bash
./scripts/test_api.sh https://<your-domain> <username> <password>
```

**Tests performed:**
1. Health check (no auth)
2. Login and session creation
3. Protected endpoint without auth (should fail)
4. Protected endpoint with auth (should succeed)
5. Logout

### API Documentation

- **Swagger UI:** `https://<your-domain>/docs`
- **ReDoc:** `https://<your-domain>/redoc`

---

## Production Recommendations

### Authentication

For **production deployments**, migrate to:

- **AWS Cognito** for enterprise-grade authentication
- Multi-factor authentication (MFA)
- User management and role-based access control (RBAC)
- SSO integration

See `docs/FUTURE_ENHANCEMENTS.md` for implementation guidance.

### Session Storage

Current implementation uses **in-memory sessions** (acceptable for prototype).

For production:
- Migrate to **Redis** or **DynamoDB** for persistence
- Enable session replication across instances
- Implement session cleanup background task

### Monitoring

- CloudWatch metrics for login attempts, API usage
- CloudFront access logs for traffic analysis
- Application logs in CloudWatch Logs

### Security

- Enforce HTTPS only (already configured)
- Regular credential rotation in Secrets Manager
- Rate limiting on login endpoint
- CAPTCHA for brute-force protection

---

## Architecture

### Components

```
┌──────────────────────────────────────┐
│         CloudFront CDN               │
│  (Custom Error Pages, SSL Termination)│
└────────────┬─────────────────────────┘
             │ HTTPS
             ▼
┌──────────────────────────────────────┐
│     Application Load Balancer        │
│   (Health Checks, Target Groups)     │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│       EC2 Instance (t3.xlarge)       │
│  ┌────────────────────────────────┐  │
│  │    FastAPI Application         │  │
│  │  - Host Check Middleware       │  │
│  │  - Session Auth (4h duration)  │  │
│  │  - Jinja2 Templates            │  │
│  └────────┬───────────────┬────────┘  │
│           │               │           │
│           ▼               ▼           │
│    ┌──────────┐    ┌──────────┐      │
│    │Tesseract │    │  Ollama  │      │
│    │   OCR    │    │ llama3.2 │      │
│    └──────────┘    └──────────┘      │
└──────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│      AWS Secrets Manager             │
│  (TTB_DEFAULT_USER, TTB_DEFAULT_PASS)│
└──────────────────────────────────────┘
```

### Data Flow

1. **User** navigates to configured domain
2. **CloudFront** forwards request to ALB
3. **ALB** routes to healthy EC2 instance
4. **Middleware** checks Host header
5. **Auth** validates session cookie
6. **Application** processes label with OCR backend
7. **Response** rendered via Jinja2 template

---

## Support

For issues or questions:
- Check [docs/OPERATIONS_RUNBOOK.md](../docs/OPERATIONS_RUNBOOK.md) for troubleshooting
- Review [docs/ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [infrastructure/README.md](../infrastructure/README.md) for deployment

---

**TTB Label Verifier UI Guide** | Last Updated: 2026-02-17

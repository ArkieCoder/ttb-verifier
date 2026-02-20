# TTB Label Verifier

AI-powered alcohol beverage label verification system for the U.S. Treasury Department's Alcohol and Tobacco Tax and Trade Bureau (TTB). Validates label compliance with 27 CFR regulations using OCR and fuzzy matching.

## Quick Start

### Using Docker (Recommended)

**Start the API:**
```bash
docker compose -f docker-compose.dev.yml up -d
```

**Test the API:**
```bash
# Verify a single label
curl -X POST http://localhost:8000/verify \
  -F "image=@samples/label_good_001.jpg"

# View API documentation
open http://localhost:8000/docs
```

**Stop services:**
```bash
docker compose down
```

## Web UI Access

The service includes a web-based UI for easy label verification without using the API directly.

**Production:** `https://<your-domain>`

**Configuration:**
- Set your domain via `DOMAIN_NAME` environment variable or Terraform `domain_name` variable
- Default allowed hosts: `localhost`, `127.0.0.1`
- For custom hosts: Set `ALLOWED_HOSTS` environment variable as JSON array

**Login Credentials:**
- Stored securely in AWS Secrets Manager:
  - `TTB_DEFAULT_USER` - UI login username
  - `TTB_DEFAULT_PASS` - UI login password  
  - `TTB_SESSION_SECRET_KEY` - Signed cookie secret key
- Configure via: `./scripts/setup_secrets.sh <username> <password>`

**Features:**
- 🖼️ **Single Label Verification** - Upload individual images with optional metadata
- 📦 **Batch Processing** - Upload ZIP files with up to 50 labels
- ⏱️ **Real-time Status** - Live monitoring of Ollama availability
- 📊 **Results Dashboard** - Visual compliance status with detailed violations

**System Status Banner:**

The web UI includes an intelligent system status banner that automatically manages Ollama backend availability:

- **Automatically shown** when Ollama backend is initializing or unavailable
- **Cannot be dismissed** when system is not ready (submit buttons disabled, forms remain editable)
- **Can be dismissed** when system becomes ready (green "System Ready" banner)
- **Stays dismissed** until system becomes unavailable again (state persisted in browser localStorage)
- **Smart visibility** - Only shows "System Ready" banner after experiencing an unavailability event
- **Adaptive polling** - Checks every 10 seconds when initializing, every 30 seconds when healthy

**User Experience:**
- Form fields remain editable while waiting for Ollama to initialize
- Submit buttons are automatically disabled until backend is available
- Banner state is shared across browser tabs via localStorage

**Testing the UI API:**
```bash
# Run comprehensive API test suite (11 tests)
./scripts/api_smoketests.sh https://<your-domain> <username> <password>

# Example:
./scripts/api_smoketests.sh https://ttb-verifier.example.com hireme please
```

**Test Coverage:**
- Health check and backend availability
- Authentication and session management  
- Single label verification (compliant & non-compliant)
- Metadata-enhanced verification
- Ollama backend testing
- Batch verification with ZIP files
- Error handling (invalid images, file sizes)

The test script uses real sample images from the `samples/` directory and validates end-to-end functionality.

### Using Python Directly

**Install dependencies:**
```bash
pip install -r app/requirements.txt
```

**Verify a label (CLI):**
```bash
# Basic verification
python app/verify_label.py test_samples/label_good_001.jpg

# With ground truth for accuracy check
python app/verify_label.py test_samples/label_good_001.jpg \
  --ground-truth test_samples/label_good_001.json
```

## Features

- ✅ **Web UI** with Bootstrap 5, session authentication, and batch processing
- ✅ **AI OCR** with Ollama llama3.2-vision for accurate text extraction
- ✅ **REST API** with FastAPI for web integration (requires authentication)
- ✅ **Batch processing** for up to 50 labels at once
- ✅ **Fuzzy matching** for brand names with 90% threshold
- ✅ **Government warning validation** with exact format checking
- ✅ **Product-specific tolerances** for ABV (wine: ±1.0%, spirits: ±0.3%)
- ✅ **Docker support** with multi-stage builds and testing
- ✅ **Comprehensive testing** with 76.9% code coverage
- ✅ **CloudFront + S3** custom error pages for graceful degradation

## Architecture

```
┌─────────────────┐
│   Web Client    │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  FastAPI REST   │ ← Port 8000
│      API        │
└────────┬────────┘
         │
         ▼
     ┌─────────┐
     │ Ollama  │ ← Port 11434
     │  (AI)   │
     └─────────┘
```

## API Endpoints

**Note:** API endpoints require authentication. Login via `/ui/login` to obtain a session cookie, or use the test script at `scripts/api_smoketests.sh`.

### POST /verify
Verify a single label image.

**Request:**
```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@label.jpg" \
  -F 'ground_truth={"brand_name":"Ridge & Co.","abv":7.5}'
```

**Response:**
```json
{
  "status": "COMPLIANT",
  "validation_level": "FULL_VALIDATION",
  "extracted_fields": {
    "brand_name": "Ridge & Co.",
    "abv_numeric": 7.5,
    "government_warning": {"present": true}
  },
  "violations": [],
  "processing_time_seconds": 0.85
}
```

### POST /verify/batch
Verify multiple labels from a ZIP file.

**Request:**
```bash
curl -X POST http://localhost:8000/verify/batch \
  -F "batch_file=@labels.zip"
```

**Response:**
```json
{
  "results": [...],
  "summary": {
    "total": 50,
    "compliant": 45,
    "non_compliant": 5,
    "errors": 0
  }
}
```

See [API_README.md](docs/API_README.md) for complete API documentation.

## Documentation

### Getting Started
- **[docs/UI_GUIDE.md](docs/UI_GUIDE.md)** - Complete web UI guide with authentication
- **[docs/API_README.md](docs/API_README.md)** - Complete REST API reference
- **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Running tests (bash + pytest)

### Architecture & Operations
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and fail-open design
- **[docs/OPERATIONS.md](docs/OPERATIONS.md)** - Operational runbook and troubleshooting
- **[infrastructure/README.md](infrastructure/README.md)** - Infrastructure deployment guide
- **[infrastructure/FUTURE_ENHANCEMENTS.md](infrastructure/FUTURE_ENHANCEMENTS.md)** - Planned improvements

### Development & Tools
- **[docs/DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md)** - Requirements, implementation phases, and project history
- **[tools/generator/](tools/generator/)** - Sample label generator tool and specifications

### Reference
- **[docs/TTB_REGULATORY_SUMMARY.md](docs/TTB_REGULATORY_SUMMARY.md)** - 27 CFR regulations summary
- **[docs/OCR_ANALYSIS.md](docs/OCR_ANALYSIS.md)** - OCR performance analysis
- **[docs/DECISION_LOG.md](docs/DECISION_LOG.md)** - Architectural decisions

## Requirements

### System Requirements
- Docker 20.10+ (recommended) OR
- Python 3.12+
- 2GB RAM minimum
- 10GB disk space (for Ollama models)

### Performance
- **Ollama**: ~10s per label (with llama3.2-vision model)
- **Batch limit**: 50 labels per request (configurable)
- **File size limit**: 10MB per image (configurable)

## Testing

**Run all tests:**
```bash
# Using Docker (recommended - what CI/CD runs)
docker build --target test -t ttb-verifier:test .

# Using Python directly (from app directory)
cd app && pytest tests/ --cov=. --cov-fail-under=50 -v
```

**Test suite:**
- 55 tests (53 passed, 1 skipped)
- 76.9% code coverage
- API tests: 95% coverage
- Unit tests for validators, extractors, CLI

See [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) for details.

## Configuration

Set environment variables in `.env` (see `.env.example`):

```bash
# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.2-vision  # Change to use custom models
OLLAMA_TIMEOUT_SECONDS=60

# App Configuration
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=10
MAX_BATCH_SIZE=50

# CORS Configuration
CORS_ORIGINS=["*"]

# Domain Configuration (for production)
DOMAIN_NAME=your-domain.com  # Leave empty for local dev (allows localhost)
```

### Domain Configuration

The `DOMAIN_NAME` environment variable configures which domain is allowed to access the UI:

- **Local Development**: Leave empty or set to `localhost` - allows `localhost` and `127.0.0.1`
- **Production**: Set to your actual domain (e.g., `ttb-verifier.example.com`)
- **Terraform**: Automatically configured from `infrastructure/terraform.tfvars`

The domain restriction is enforced by `HostCheckMiddleware` to prevent unauthorized access. The `/health` endpoint is always accessible for ALB health checks.

### Using Custom Ollama Models

To use a custom Ollama model:

1. **Set the model name** in `.env` or `docker-compose.dev.yml`:
   ```bash
   OLLAMA_MODEL=my-custom-model
   ```

2. **For production (EC2):**
   - Upload your model tarball to S3: `s3://ttb-verifier-ollama-models-{account}/models/my-custom-model.tar.gz`
   - The tarball should contain the `models/` directory from `.ollama` (created with: `tar czf my-custom-model.tar.gz -C /root/.ollama models`)
   - Or let the system download it from Ollama registry on first boot (slower)

3. **For local development:**
   - The model will be pulled from Ollama registry automatically on first use

## Project Structure

```
.
├── app/                      # Application code
│   ├── api.py               # FastAPI REST API
│   ├── ui_routes.py         # Web UI routes
│   ├── config.py            # Configuration management
│   ├── label_validator.py   # Main validation orchestrator
│   ├── field_validators.py  # Field-level validation logic
│   ├── label_extractor.py   # OCR text extraction
│   ├── ocr_backends.py      # Ollama OCR backend
│   ├── verify_label.py      # CLI interface
│   ├── templates/           # Jinja2 templates for web UI
│   ├── requirements.txt     # Python dependencies
│   ├── pytest.ini           # Pytest configuration
│   └── tests/               # Test suite (pytest)
│       ├── test_api/        # API endpoint tests
│       ├── test_unit/       # Unit tests
│       └── test_integration/ # Integration tests
├── infrastructure/           # Terraform/Terragrunt IaC
├── docker-compose.dev.yml   # Local development (CPU mode, builds from source)
├── Dockerfile               # Multi-stage build (test, production)
├── scripts/                  # Utility scripts
│   ├── workflow_deploy.sh   # Deployment automation
│   ├── gen_samples.py       # Generate test label images
│   ├── cli_smoketests.sh    # CLI smoke tests
│   ├── setup_secrets.sh     # AWS secrets configuration
│   ├── api_smoketests.sh    # API smoke tests
│   └── verify_samples.py    # Golden dataset validation
├── samples/                  # Golden dataset (40 test labels)
├── tools/                    # Additional tooling
└── docs/                     # Documentation
```

## Development Workflow

1. **Make changes** to Python files in `app/`
2. **Run tests**: `cd app && pytest tests/` (or use Docker: `docker build --target test .`)
3. **Build Docker** image: `docker build -t ttb-verifier:latest .`
4. **Test in Docker**: `docker run -p 8000:8000 ttb-verifier:latest`
5. **Commit** changes with descriptive message

## Deployment

### Local Development
```bash
docker compose -f docker-compose.dev.yml up -d
```

### Production (EC2)
See [infrastructure/README.md](infrastructure/README.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for:
- GitHub Actions CI/CD pipeline
- Infrastructure deployment with Terraform/Terragrunt
- EC2 instance configuration
- Monitoring and health checks

## Known Limitations

1. **Batch processing timeout**: CloudFront 30s timeout limits batch processing to ~2-3 images (async processing planned for future)
2. **Ollama speed**: ~10s per label (batch processing needs async implementation)
3. **No cloud API integration**: Government firewall restrictions
4. **Standalone system**: Not integrated with COLA registration system

## Regulatory Compliance

Validates labels against **27 CFR** regulations:

- **Brand name** presence (fuzzy match ≥90%)
- **ABV accuracy** with product-specific tolerances
  - Wine: ±1.0% (27 CFR § 4.36)
  - Spirits: ±0.3% (27 CFR § 5.37)
  - Beer/Malt: ±0.3% (27 CFR § 7.71)
- **Net contents** statement validation
- **Bottler information** presence
- **Government warning** exact format validation
- **Country of origin** for imports

See [docs/TTB_REGULATORY_SUMMARY.md](docs/TTB_REGULATORY_SUMMARY.md) for complete requirements.

## License

This is a prototype system developed for the U.S. Treasury Department TTB.

## Support

For questions or issues:
1. Check documentation in `/docs` directory
2. Review [docs/DECISION_LOG.md](docs/DECISION_LOG.md) for architectural decisions
3. See [docs/DEVELOPMENT_HISTORY.md](docs/DEVELOPMENT_HISTORY.md) for implementation details

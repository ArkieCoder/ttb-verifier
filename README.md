# TTB Label Verifier

AI-powered alcohol beverage label verification system for the U.S. Treasury Department's Alcohol and Tobacco Tax and Trade Bureau (TTB). Validates label compliance with 27 CFR regulations using OCR and fuzzy matching.

## Quick Start

### Using Docker (Recommended)

**Start the API:**
```bash
docker compose up -d
```

**Test the API:**
```bash
# Verify a single label
curl -X POST http://localhost:8000/verify \
  -F "image=@samples/label_good_001.jpg" \
  -F "ocr_backend=tesseract"

# View API documentation
open http://localhost:8000/docs
```

**Stop services:**
```bash
docker compose down
```

### Using Python Directly

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Verify a label:**
```bash
python verify_label.py samples/label_good_001.jpg
```

## Features

- ✅ **Fast OCR** with Tesseract (< 1 second per label)
- ✅ **AI OCR** with Ollama llama3.2-vision (~58s, higher accuracy)
- ✅ **REST API** with FastAPI for web integration
- ✅ **Batch processing** for up to 50 labels at once
- ✅ **Fuzzy matching** for brand names with 90% threshold
- ✅ **Government warning validation** with exact format checking
- ✅ **Product-specific tolerances** for ABV (wine: ±1.0%, spirits: ±0.3%)
- ✅ **Docker support** with multi-stage builds and testing
- ✅ **Comprehensive testing** with 76.9% code coverage

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
    ┌────┴─────┐
    │          │
    ▼          ▼
┌──────┐   ┌─────────┐
│Tess- │   │ Ollama  │ ← Port 11434
│eract │   │  (AI)   │
└──────┘   └─────────┘
```

## API Endpoints

### POST /verify
Verify a single label image.

**Request:**
```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@label.jpg" \
  -F 'ground_truth={"brand_name":"Ridge & Co.","abv":7.5}' \
  -F "ocr_backend=tesseract"
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
  -F "batch_file=@labels.zip" \
  -F "ocr_backend=tesseract"
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
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for CLI and API usage
- **[docs/API_README.md](docs/API_README.md)** - Complete REST API reference
- **[VERIFIER_README.md](VERIFIER_README.md)** - CLI tool documentation

### Development
- **[docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md)** - Docker build and deployment guide
- **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Running tests (bash + pytest)
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Development phases and progress

### Reference
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Complete project overview
- **[TTB_REGULATORY_SUMMARY.md](TTB_REGULATORY_SUMMARY.md)** - 27 CFR regulations summary
- **[OCR_ANALYSIS.md](OCR_ANALYSIS.md)** - OCR performance analysis
- **[DECISION_LOG.md](DECISION_LOG.md)** - Architectural decisions

## Requirements

### System Requirements
- Docker 20.10+ (recommended) OR
- Python 3.12+
- Tesseract OCR 5.0+
- 2GB RAM minimum
- 10GB disk space (if using Ollama)

### Performance
- **Tesseract**: ~0.7s per label, 100% recall, 50% precision
- **Ollama**: ~58s per label, excellent accuracy, 12x slower
- **Batch limit**: 50 labels per request (configurable)
- **File size limit**: 10MB per image (configurable)

## Testing

**Run all tests:**
```bash
# Using Docker (recommended)
docker build --target test -t ttb-verifier:test .

# Using Python directly
pytest tests/ --cov=. --cov-fail-under=75 -v
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
OLLAMA_MODEL=llama3.2-vision
OLLAMA_TIMEOUT_SECONDS=60

# App Configuration
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=10
MAX_BATCH_SIZE=50
DEFAULT_OCR_BACKEND=tesseract

# CORS Configuration
CORS_ORIGINS=["*"]
```

## Project Structure

```
.
├── api.py                    # FastAPI REST API
├── config.py                 # Configuration management
├── label_validator.py        # Main validation orchestrator
├── field_validators.py       # Field-level validation logic
├── label_extractor.py        # OCR text extraction
├── ocr_backends.py          # Tesseract & Ollama OCR
├── verify_label.py          # CLI interface
├── samples/                  # 40 golden test samples
├── tests/                    # Test suite (pytest)
│   ├── test_api/            # API endpoint tests
│   ├── test_unit/           # Unit tests
│   └── test_integration/    # Integration tests
└── docs/                     # Documentation
```

## Development Workflow

1. **Make changes** to Python files
2. **Run tests** locally: `pytest tests/`
3. **Build Docker** image: `docker build -t ttb-verifier:latest .`
4. **Test in Docker**: `docker run -p 8000:8000 ttb-verifier:latest`
5. **Commit** changes with descriptive message

## Deployment

### Local Development
```bash
docker compose up -d
```

### Production (EC2)
See [docs/DOCKER_DEPLOYMENT.md](docs/DOCKER_DEPLOYMENT.md) for:
- GitHub Actions CI/CD pipeline
- Container registry setup (GHCR or AWS ECR)
- EC2 deployment configuration
- Monitoring and logging

## Known Limitations

1. **Tesseract OCR accuracy**: 50% precision due to decorative fonts on labels
2. **Ollama speed**: ~58s per label (12x slower than requirement)
3. **No cloud API integration**: Government firewall restrictions
4. **Standalone system**: Not integrated with COLA registration system
5. **No authentication**: API is open (add API Gateway for production)

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

See [TTB_REGULATORY_SUMMARY.md](TTB_REGULATORY_SUMMARY.md) for complete requirements.

## License

This is a prototype system developed for the U.S. Treasury Department TTB.

## Support

For questions or issues:
1. Check documentation in `/docs` directory
2. Review [DECISION_LOG.md](DECISION_LOG.md) for architectural decisions
3. See [QUICKSTART.md](QUICKSTART.md) for common use cases

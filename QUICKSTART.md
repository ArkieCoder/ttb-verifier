# TTB Label Verifier - Quick Start

## What We Built

A production-ready REST API that validates alcohol beverage labels against TTB regulations in **under 1 second** (0.72s average), with Docker support and comprehensive testing.

## Quick Start with Docker (Recommended)

```bash
# 1. Start the API server
docker compose up -d

# 2. Verify API is running
curl http://localhost:8000/

# 3. Test single label verification
curl -X POST http://localhost:8000/verify \
  -F "image=@samples/label_good_001.jpg" \
  -F "ocr_backend=tesseract"

# 4. View interactive API docs
open http://localhost:8000/docs

# 5. Stop services
docker compose down
```

## Quick Start with CLI

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test a single label (fast - uses Tesseract)
python3 verify_label.py samples/label_good_001.jpg --ground-truth samples/label_good_001.json

# 3. Test a bad label
python3 verify_label.py samples/label_bad_001.jpg --ground-truth samples/label_bad_001.json

# 4. Batch process all 40 samples
python3 verify_label.py --batch samples/ --ground-truth-dir samples/ --verbose

# 5. Run comprehensive test suite
pytest tests/ -v
```

## API Examples

### Single Label Verification

**Basic verification (Tesseract OCR):**
```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@samples/label_good_001.jpg"
```

**With ground truth for full validation:**
```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@samples/label_good_001.jpg" \
  -F 'ground_truth={"brand_name":"Ridge & Co.","abv":7.5,"net_contents":"64 fl oz"}'
```

**Using Ollama AI for higher accuracy:**
```bash
curl -X POST http://localhost:8000/verify \
  -F "image=@samples/label_good_001.jpg" \
  -F "ocr_backend=ollama" \
  -F "timeout=90"
```

**Response:**
```json
{
  "status": "COMPLIANT",
  "validation_level": "FULL_VALIDATION",
  "extracted_fields": {
    "brand_name": "Ridge & Co.",
    "abv_numeric": 7.5,
    "net_contents": "64 fl oz",
    "government_warning": {
      "present": true,
      "header_correct": true,
      "text_correct": true
    }
  },
  "violations": [],
  "warnings": [],
  "processing_time_seconds": 0.85
}
```

### Batch Processing

**Create a ZIP file with labels:**
```bash
# Create ZIP with 3 sample labels
cd samples
zip labels.zip label_good_001.jpg label_good_001.json \
               label_good_002.jpg label_good_002.json \
               label_good_003.jpg label_good_003.json
cd ..
```

**Submit batch for verification:**
```bash
curl -X POST http://localhost:8000/verify/batch \
  -F "batch_file=@samples/labels.zip" \
  -F "ocr_backend=tesseract"
```

**Response:**
```json
{
  "results": [
    {
      "status": "COMPLIANT",
      "image_path": "label_good_001.jpg",
      "processing_time_seconds": 0.82
    },
    ...
  ],
  "summary": {
    "total": 3,
    "compliant": 3,
    "non_compliant": 0,
    "errors": 0,
    "total_processing_time_seconds": 2.47
  }
}
```

## Key Results

- **Processing Speed**: 0.72s per label (86% faster than 5s requirement)
- **API Response Time**: < 1s for single labels, ~30s for 50 labels
- **Test Coverage**: 76.9% overall, 86.7% for API
- **Recall**: 100% (catches all bad labels)
- **Docker Image**: ~500MB production, includes 40 test samples
- **Local Execution**: No cloud APIs needed

## API Features

✅ **REST API** with FastAPI  
✅ **Single label** verification  
✅ **Batch processing** (up to 50 labels)  
✅ **Configurable timeout** for Ollama  
✅ **Auto-generated docs** at `/docs`  
✅ **CORS support** for web integration  
✅ **Error handling** with correlation IDs

## What It Validates

✅ Brand name  
✅ Alcohol content (ABV) with tolerances  
✅ Net contents  
✅ Bottler information  
✅ Government warning (format + text)  
✅ Product type

## Two OCR Modes

**Fast Mode (default)**: Tesseract - 0.7s per label
```bash
# CLI
python3 verify_label.py label.jpg

# API
curl -X POST http://localhost:8000/verify -F "image=@label.jpg"
```

**Accurate Mode**: Ollama AI - 58s per label
```bash
# CLI
python3 verify_label.py label.jpg --ocr-backend ollama

# API  
curl -X POST http://localhost:8000/verify \
  -F "image=@label.jpg" \
  -F "ocr_backend=ollama" \
  -F "timeout=90"
```

## Output Format

JSON to stdout - ready for API integration:
```json
{
  "status": "NON_COMPLIANT",
  "validation_level": "FULL_VALIDATION",
  "violations": [...],
  "processing_time_seconds": 0.723
}
```

## Documentation

- **README.md** - Main documentation with Docker quick start
- **docs/API_README.md** - Complete REST API reference
- **PROJECT_SUMMARY.md** - Complete project overview
- **VERIFIER_README.md** - CLI user guide
- **docs/DOCKER_DEPLOYMENT.md** - Docker build and deployment
- **docs/TESTING_GUIDE.md** - Running tests
- **TTB_REGULATORY_SUMMARY.md** - 27 CFR requirements
- **DECISION_LOG.md** - Architecture decisions
- **OCR_ANALYSIS.md** - OCR testing results

## Known Issue

Tesseract OCR has accuracy issues with decorative fonts, causing false positives on GOOD labels. Use `--ocr-backend ollama` for higher accuracy (80x slower).

## Testing

```bash
# Run all tests with Docker
docker build --target test -t ttb-verifier:test .

# Run tests locally
pytest tests/ --cov=. --cov-fail-under=75 -v

# Test suite: 55 tests (53 passed, 1 skipped, 1 expected fail)
# Coverage: 76.9% overall, 86.7% for API
```

## Next Steps

1. **Production deployment**: Use GitHub Actions to deploy to AWS EC2
2. **Add authentication**: Integrate with API Gateway
3. **Monitoring**: Add Prometheus metrics and CloudWatch logs
4. **Scale**: Deploy behind load balancer for high traffic

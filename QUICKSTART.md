# TTB Label Verifier - Quick Start

## What We Built

A working prototype that validates alcohol beverage labels against TTB regulations in **under 1 second** (0.72s average).

## Try It Now

```bash
# 1. Test a single label (fast - uses Tesseract)
python3 verify_label.py samples/label_good_001.jpg --ground-truth samples/label_good_001.json

# 2. Test a bad label
python3 verify_label.py samples/label_bad_001.jpg --ground-truth samples/label_bad_001.json

# 3. Batch process all 40 samples
python3 verify_label.py --batch samples/ --ground-truth-dir samples/ --verbose

# 4. Run comprehensive test suite
python3 test_verifier.py --ocr-backend tesseract --summary-only
```

## Key Results

- **Processing Speed**: 0.72s per label (86% faster than 5s requirement)
- **Recall**: 100% (catches all bad labels)
- **Batch Processing**: 40 labels in 29 seconds
- **Local Execution**: No cloud APIs needed

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
python3 verify_label.py label.jpg
```

**Accurate Mode**: Ollama AI - 58s per label
```bash
python3 verify_label.py label.jpg --ocr-backend ollama
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

- **PROJECT_SUMMARY.md** - Complete project overview
- **VERIFIER_README.md** - Full user guide
- **TTB_REGULATORY_SUMMARY.md** - 27 CFR requirements
- **DECISION_LOG.md** - Architecture decisions
- **OCR_ANALYSIS.md** - OCR testing results

## Known Issue

Tesseract OCR has accuracy issues with decorative fonts, causing false positives on GOOD labels. Use `--ocr-backend ollama` for higher accuracy (80x slower).

## Next Steps

Ready for FastAPI web interface and deployment to AWS EC2.

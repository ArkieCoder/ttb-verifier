# TTB Label Verifier - User Guide

## Overview

The TTB Label Verifier validates alcohol beverage labels against 27 CFR regulations. It performs OCR text extraction, field parsing, and compliance checking in under 5 seconds per label.

## Quick Start

### Single Label Verification

```bash
# Structural validation only (checks presence of required fields)
python3 verify_label.py label.jpg

# Full validation with ground truth (checks accuracy against expected values)
python3 verify_label.py label.jpg --ground-truth metadata.json

# Use AI OCR for better accuracy (slower: ~60s vs ~1s)
python3 verify_label.py label.jpg --ocr-backend ollama --ground-truth metadata.json
```

### Batch Processing

```bash
# Process all images in a directory
python3 verify_label.py --batch samples/ --ground-truth-dir samples/ --verbose

# Save results to file
python3 verify_label.py --batch samples/ --ground-truth-dir samples/ -o results.json
```

### Testing

```bash
# Run comprehensive test on golden dataset (40 samples)
python3 test_verifier.py --ocr-backend tesseract --summary-only

# Generate detailed results
python3 test_verifier.py --ocr-backend tesseract -o test_results.json
```

## Architecture

### Two-Tier Validation Strategy

The verifier implements a graceful degradation approach:

#### Tier 1: Structural Validation (Always Performed)
- **No ground truth required**
- Checks presence of mandatory fields:
  - Brand name
  - Alcohol content (ABV)
  - Net contents
  - Bottler information
  - Government warning
- Validates government warning format:
  - Header must be "GOVERNMENT WARNING:" (all caps)
  - Warning text must match required text (85% similarity threshold for OCR tolerance)

#### Tier 2: Accuracy Validation (Requires Ground Truth)
- **Ground truth data required**
- Validates extracted values against expected values:
  - **Brand name**: 90% fuzzy match threshold
  - **ABV**: Product-specific tolerance (wine: ±1.0%, spirits/beer: ±0.3%)
  - **Net contents**: 90% fuzzy match threshold
  - **Bottler info**: 90% fuzzy match threshold
  - **Product type**: 90% fuzzy match threshold

### OCR Backend Options

#### Tesseract OCR (Default)
- **Speed**: ~0.7 seconds per label ✅
- **Accuracy**: Moderate - struggles with decorative fonts ⚠️
- **Use case**: Fast structural validation, batch processing
- **Installation**: `sudo apt-get install tesseract-ocr`

#### Ollama AI Vision (Optional)
- **Speed**: ~58 seconds per label ❌
- **Accuracy**: Excellent - handles decorative fonts well ✅
- **Use case**: High-stakes validation, difficult labels
- **Installation**: `ollama pull llama3.2-vision`

## Output Format

**Note**: As of Phase 4, the verifier outputs **compact JSON only** to stdout. The `--pretty` flag has been removed to ensure consistency with the REST API.

All commands output JSON to stdout (suitable for piping to other tools or APIs). For pretty-printing, pipe through `jq` or `python -m json.tool`:

### Example Output

```json
{
  "status": "NON_COMPLIANT",
  "validation_level": "FULL_VALIDATION",
  "extracted_fields": {
    "brand_name": "Ridge & Co.",
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
      {"field": "brand_name", "valid": true, "actual": "Ridge & Co."},
      {"field": "abv", "valid": true, "actual": "7.5%"},
      ...
    ],
    "accuracy": [
      {"field": "brand_name", "valid": true, "expected": "Ridge & Co.", "actual": "Ridge & Co.", "similarity_score": 1.0},
      ...
    ]
  },
  "violations": [
    {
      "field": "brand_name",
      "type": "accuracy",
      "message": "Brand name mismatch (similarity: 85.0%)",
      "expected": "Ridge & Co.",
      "actual": "Ridge and Co."
    }
  ],
  "warnings": [],
  "processing_time_seconds": 0.723,
  "image_path": "samples/label_good_001.jpg"
}
```

### Status Values

- **COMPLIANT**: Label passes all validation checks
- **NON_COMPLIANT**: Label has one or more violations
- **PARTIAL_VALIDATION**: Only structural validation performed (no ground truth)
- **ERROR**: Processing error occurred

## Ground Truth Format

Ground truth files should be JSON with the following structure:

```json
{
  "ground_truth": {
    "brand_name": "Ridge & Co.",
    "alcohol_content_numeric": 7.5,
    "net_contents": "64 fl oz",
    "bottler_info": "Imported by Black Brewing, San Francisco, CA",
    "class_type": "Hefeweizen"
  }
}
```

The verifier also accepts flat JSON without nesting:

```json
{
  "brand_name": "Ridge & Co.",
  "abv": 7.5,
  "net_contents": "64 fl oz",
  "bottler": "Imported by Black Brewing, San Francisco, CA",
  "product_type": "Hefeweizen"
}
```

## Performance Benchmarks

Tested on golden dataset (40 samples):

### Tesseract Backend
- **Average time**: 0.72s per label
- **Total time (40 labels)**: 29s
- **Recall**: 100% (catches all bad labels)
- **Precision**: 50% (false positives due to OCR errors)
- **Best for**: Fast batch processing, structural validation

### Ollama Backend
- **Average time**: ~58s per label (estimated)
- **Total time (40 labels)**: ~38 minutes (estimated)
- **Accuracy**: Expected higher due to better OCR
- **Best for**: Critical validation, difficult fonts

## Known Limitations

### OCR Accuracy Issues
1. **Decorative fonts**: Tesseract struggles with stylized brand names
2. **Brand name extraction**: Often picks up product type instead of brand
3. **Government warning**: Minor OCR errors in long text blocks
4. **Embellishments**: Ornamental elements confuse text detection

### Mitigation Strategies
1. Use `--ocr-backend ollama` for higher accuracy (trade speed for quality)
2. Provide ground truth data for Tier 2 validation
3. Review violations manually for false positives
4. Consider pre-processing images (contrast enhancement, denoising)

## CLI Reference

### verify_label.py

```
usage: verify_label.py [-h] [--batch DIR] [--ground-truth FILE]
                       [--ground-truth-dir DIR]
                       [--ocr-backend {tesseract,ollama}]
                       [--verbose] [--output FILE]
                       [image_path]

positional arguments:
  image_path            Path to label image file

optional arguments:
  --batch DIR           Process all images in directory
  --ground-truth FILE   Path to ground truth JSON file
  --ground-truth-dir DIR
                        Directory with ground truth JSON files (batch mode)
  --ocr-backend {tesseract,ollama}
                        OCR backend (default: tesseract)
  --verbose, -v         Print progress to stderr
  --output FILE, -o FILE
                        Write output to file (compact JSON)

Note: The --pretty flag has been removed. Use `python -m json.tool` or `jq` for formatting.
```

### test_verifier.py

```
usage: test_verifier.py [-h] [--ocr-backend {tesseract,ollama}]
                        [--samples-dir DIR] [--output FILE]
                        [--summary-only]

optional arguments:
  --ocr-backend {tesseract,ollama}
                        OCR backend to test (default: tesseract)
  --samples-dir DIR     Golden dataset directory (default: samples/)
  --output FILE, -o FILE
                        Write detailed JSON results to file
  --summary-only        Only print summary, no detailed JSON
```

## Integration with FastAPI

The verifier outputs JSON directly to stdout, making it easy to integrate with a web API:

```python
import subprocess
import json

def verify_label_api(image_path, ground_truth=None):
    cmd = ["python3", "verify_label.py", image_path]
    if ground_truth:
        cmd.extend(["--ground-truth", ground_truth])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)
```

## Troubleshooting

### "Tesseract not installed"
```bash
sudo apt-get install tesseract-ocr
```

### "Ollama not available"
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull vision model
ollama pull llama3.2-vision
```

### "All labels flagged as non-compliant"
This is expected with Tesseract backend due to OCR errors. Options:
1. Use `--ocr-backend ollama` for better accuracy
2. Adjust fuzzy matching thresholds in `field_validators.py`
3. Only use structural validation (no ground truth)

### Slow processing
- Tesseract should be <1s per label
- Ollama is intentionally slow (~60s) for better accuracy
- Check if running on GPU vs CPU for Ollama

## Exit Codes

- **0**: Success (COMPLIANT status)
- **1**: Failure (NON_COMPLIANT or ERROR status)

For batch processing:
- **0**: All labels processed successfully
- **1**: One or more labels non-compliant or errors

## Future Enhancements

1. FastAPI web interface with file upload
2. Pre-processing pipeline (contrast, denoising, deskew)
3. Hybrid OCR (Tesseract + AI for difficult regions)
4. Confidence scores for extracted fields
5. Support for COLA system integration
6. Multi-language label support
7. Additional violation types (sulfites, allergens, etc.)

# Sample Label Generator - Quick Start

## Overview
`gen_samples.py` generates realistic alcohol beverage labels for testing the TTB Label Verification system.

## Requirements
```bash
pip install Pillow
```

## Usage

### Generate Labels
```bash
# Generate 50 GOOD (compliant) and 50 BAD (non-compliant) labels
python3 gen_samples.py --good 50 --bad 50

# Generate only GOOD labels
python3 gen_samples.py --good 100

# Generate only BAD labels
python3 gen_samples.py --bad 20

# Use random seed for reproducibility
python3 gen_samples.py --good 10 --bad 10 --seed 42
```

### Output Files
For each label, three files are generated:
- `label_good_001.jpg` - JPEG image (< 750 KB)
- `label_good_001.tif` - TIFF image (< 750 KB)
- `label_good_001.json` - Metadata with ground truth

All files are written to the current directory.

## What It Generates

### GOOD Labels (Compliant)
- All required fields present (brand, class/type, ABV, net contents, bottler info, government warning)
- Proper formatting (warning header in all caps and bold, body not bold)
- Type sizes meet regulatory minimums
- Randomized but compliant values

### BAD Labels (Non-Compliant)
Each BAD label has 1-3 intentional violations:
- Missing government warning
- Warning header not all caps
- Warning body text in bold
- Wrong warning text
- Missing required fields (brand, ABV, net contents, etc.)
- ABV outside tolerance
- Wrong net contents
- Type size too small
- Missing import phrases

## JSON Metadata
Each label includes complete metadata:
```json
{
  "generated_at": "2026-02-15T16:28:33.250166",
  "label_type": "GOOD",
  "product_type": "distilled_spirits",
  "container_size": 750,
  "ground_truth": {
    "brand_name": "Mountain Heritage Distillery",
    "class_type": "Kentucky Straight Bourbon Whiskey",
    "alcohol_content": "45% alc./vol.",
    ...
  },
  "violations_introduced": [],
  "expected_validation": {
    "overall_status": "COMPLIANT",
    ...
  }
}
```

## Examples

```bash
# Quick test - generate 5 of each
python3 gen_samples.py --good 5 --bad 5

# Large test set
python3 gen_samples.py --good 100 --bad 100

# Reproducible test set
python3 gen_samples.py --good 20 --bad 20 --seed 123
```

## Technical Details

See `SAMPLE_GENERATOR.md` for complete technical specification including:
- Architecture and component design
- Regulatory requirements implemented
- Violation types and descriptions
- Implementation phases

## Regulatory Compliance

Labels are generated based on requirements from:
- 27 CFR Part 4 (Wine Labeling)
- 27 CFR Part 5 (Distilled Spirits Labeling)
- 27 CFR Part 7 (Malt Beverages Labeling)
- 27 CFR Part 16 (Health Warning Statement)

See `TTB_REGULATORY_SUMMARY.md` for complete regulatory analysis.

# Golden Samples Documentation

## Overview

The golden sample dataset consists of 40 alcohol beverage label images (20 GOOD, 20 BAD) with corresponding JSON metadata files. These samples serve as ground truth for testing, validation, and demonstration.

**Location:** `samples/` directory  
**Purpose:** Testing, validation, CI/CD, demonstrations

---

## Dataset Composition



### File Naming Convention

```
samples/
├── label_good_001.jpg          # Image file
├── label_good_001.json         # Metadata with ground truth
├── label_good_002.jpg
├── label_good_002.json
├── ...
├── label_bad_001.jpg
├── label_bad_001.json
└── ...
```

**Pattern:**
- Images: `label_{type}_{number}.jpg`
- Metadata: `label_{type}_{number}.json`
- Type: `good` or `bad`
- Number: 001-020 (zero-padded)

---

## Label Characteristics

### GOOD Labels (Compliant)

**Characteristics:**
- ✅ All required fields present (brand, ABV, net contents, bottler)
- ✅ Government warning with correct format and text
- ✅ ABV within regulatory tolerances
- ✅ Proper capitalization ("GOVERNMENT WARNING:")
- ✅ Clean, high-contrast design
- ✅ No embellishments that obscure text

**Product Types:**
- Wine: Cabernet Sauvignon, Pinot Noir, Chardonnay
- Spirits: Bourbon Whiskey, Vodka, Gin, Rum
- Beer: IPA, Porter, Lager, Hefeweizen

**Container Sizes:**
- Wine: 375mL, 500mL, 750mL, 1L, 1.5L
- Spirits: 50mL, 200mL, 375mL, 750mL, 1L
- Beer: 12 fl oz, 16 fl oz, 22 fl oz, 32 fl oz, 64 fl oz

### BAD Labels (Non-Compliant)

**Violation Types:**

1. **Missing Fields:**
   - Missing ABV (most common)
   - Missing net contents
   - Missing bottler information
   - Missing government warning

2. **ABV Tolerance Violations:**
   - Wine: ABV differs by >1.0% from stated value
   - Spirits/Beer: ABV differs by >0.3% from stated value

3. **Government Warning Issues:**
   - Warning text missing
   - Wrong warning text
   - Header not all caps (e.g., "Government Warning:")
   - Incomplete warning text

4. **Brand Name Mismatches:**
   - OCR extracts wrong text (decorative fonts)
   - Brand name not prominent enough

5. **Format Issues:**
   - Wrong units (e.g., "mL" vs "ml")
   - Missing required information

**Distribution:**
- Missing ABV: 8 samples
- Missing gov warning: 5 samples
- ABV tolerance violation: 4 samples
- Government warning format issue: 3 samples

---

## Metadata Format

### JSON Structure

Each `.json` file contains:

```json
{
  "generated_at": "2026-02-16T08:56:39.359308",
  "label_type": "GOOD",
  "product_type": "wine",
  "container_size": 750,
  "is_import": false,
  "ground_truth": {
    "product_type": "wine",
    "container_size": 750,
    "is_import": false,
    "brand_name": "Ridge & Co.",
    "class_type": "Cabernet Sauvignon",
    "alcohol_content": "13.5% ABV",
    "alcohol_content_numeric": 13.5,
    "net_contents": "750 mL",
    "bottler_info": "Bottled by Ridge & Co., Napa Valley, CA",
    "country_of_origin": "Product of USA",
    "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
    "sulfites": "Contains Sulfites",
    "other_disclosures": []
  },
  "violations": [],
  "generation_params": {
    "embellishment_level": "moderate",
    "font_family": "Playfair Display",
    "brand_font": "Playfair Display",
    "warning_font": "Arial"
  }
}
```

### Key Fields

#### Top-Level Metadata

| Field | Type | Description |
|-------|------|-------------|
| `generated_at` | string | ISO 8601 timestamp |
| `label_type` | string | "GOOD" or "BAD" |
| `product_type` | string | wine, spirits, beer, malt_beverage |
| `container_size` | number | Size in mL or fl oz |
| `is_import` | boolean | Imported product |

#### Ground Truth Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `brand_name` | string | Yes | Brand name as it should appear |
| `class_type` | string | Yes | Product class (e.g., "Cabernet Sauvignon") |
| `alcohol_content` | string | Yes | ABV as text (e.g., "13.5% ABV") |
| `alcohol_content_numeric` | number | Yes | ABV as number for tolerance checks |
| `net_contents` | string | Yes | Volume with units (e.g., "750 mL") |
| `bottler_info` | string | Yes | Bottler/producer information |
| `country_of_origin` | string | No | Country of origin if applicable |
| `government_warning` | string | Yes | Complete government warning text |
| `sulfites` | string | No | Sulfites declaration if applicable |

#### Violations Array (BAD labels only)

```json
"violations": [
  {
    "type": "missing_abv",
    "description": "Alcohol content field intentionally omitted"
  }
]
```

---

## Usage in Testing

### Pytest Fixtures

Golden samples are loaded via fixtures in `conftest.py`:

```python
@pytest.fixture
def golden_samples_dir():
    """Path to golden sample images."""
    return Path(__file__).parent.parent / "samples"

@pytest.fixture
def good_label_path(golden_samples_dir):
    """Path to a known good label."""
    return golden_samples_dir / "label_good_001.jpg"

@pytest.fixture
def good_ground_truth(golden_samples_dir):
    """Load ground truth for good label."""
    with open(golden_samples_dir / "label_good_001.json") as f:
        data = json.load(f)
    return data['ground_truth']
```

### Example Test

```python
def test_good_label_compliant(good_label_path, good_ground_truth):
    """Test that GOOD label is detected as compliant."""
    validator = LabelValidator(ocr_backend="tesseract")
    result = validator.validate_label(
        str(good_label_path),
        good_ground_truth
    )
    
    # Note: May be NON_COMPLIANT due to OCR accuracy issues
    # but should have no structural violations
    structural = result['validation_results']['structural']
    structural_failures = [r for r in structural if not r['valid']]
    
    # At minimum, all required fields should be present
    assert len(structural_failures) <= 2  # Allow minor OCR errors
```

### Batch Testing

```python
def test_all_good_labels():
    """Test all GOOD labels."""
    samples_dir = Path("samples")
    good_labels = sorted(samples_dir.glob("label_good_*.jpg"))
    
    validator = LabelValidator(ocr_backend="tesseract")
    results = []
    
    for label_path in good_labels:
        json_path = label_path.with_suffix('.json')
        with open(json_path) as f:
            metadata = json.load(f)
        
        result = validator.validate_label(
            str(label_path),
            metadata['ground_truth']
        )
        results.append(result)
    
    # Check statistics
    compliant = sum(1 for r in results if r['status'] == 'COMPLIANT')
    print(f"Compliant: {compliant}/{len(results)}")
```

---

## Replacing Golden Samples

### Why Replace?

- **Custom Products:** Test with your specific product types
- **Different Fonts:** Test with fonts used in your labels
- **Different Sizes:** Test with your container sizes
- **Real Labels:** Test with actual label images from your catalog

### Option 1: Generate New Samples

Use the sample generator to create custom labels:

```bash
# Generate 10 new samples
python gen_samples.py --count 10 --output my_samples/

# Generate with specific settings
python gen_samples.py \
    --count 20 \
    --good-ratio 0.5 \
    --embellishment-level prominent \
    --output my_samples/
```

**Result:** Creates images + JSON metadata in the same format as golden samples.

### Option 2: Use Real Label Images

#### Step 1: Prepare Images

```bash
mkdir custom_samples/

# Copy your label images
cp /path/to/real/labels/*.jpg custom_samples/

# Rename to match convention
cd custom_samples/
for i in *.jpg; do
    mv "$i" "label_real_$(printf '%03d' $((++n))).jpg"
done
```

#### Step 2: Create Metadata Files

For each image, create a corresponding JSON file:

**Template:** `label_real_001.json`
```json
{
  "generated_at": "2026-02-16T12:00:00Z",
  "label_type": "GOOD",
  "product_type": "wine",
  "container_size": 750,
  "is_import": false,
  "ground_truth": {
    "brand_name": "Your Brand Name",
    "class_type": "Cabernet Sauvignon",
    "alcohol_content": "13.5% ABV",
    "alcohol_content_numeric": 13.5,
    "net_contents": "750 mL",
    "bottler_info": "Bottled by Your Winery, Napa Valley, CA",
    "country_of_origin": "Product of USA",
    "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
    "sulfites": "Contains Sulfites"
  },
  "violations": []
}
```

**Script to Generate Metadata:**
```python
#!/usr/bin/env python3
"""Generate metadata JSON files for custom label images."""
import json
from datetime import datetime
from pathlib import Path

def create_metadata(image_path, brand_name, abv, net_contents, bottler):
    """Create metadata JSON for a label image."""
    return {
        "generated_at": datetime.now().isoformat(),
        "label_type": "GOOD",  # or "BAD" if known non-compliant
        "product_type": "wine",  # or "spirits", "beer"
        "container_size": 750,
        "is_import": False,
        "ground_truth": {
            "brand_name": brand_name,
            "class_type": "Cabernet Sauvignon",
            "alcohol_content": f"{abv}% ABV",
            "alcohol_content_numeric": abv,
            "net_contents": net_contents,
            "bottler_info": bottler,
            "country_of_origin": "Product of USA",
            "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."
        },
        "violations": []
    }

# Example usage
samples_dir = Path("custom_samples")
for image_path in samples_dir.glob("*.jpg"):
    metadata = create_metadata(
        image_path,
        brand_name="Ridge & Co.",
        abv=13.5,
        net_contents="750 mL",
        bottler="Bottled by Ridge & Co., Napa Valley, CA"
    )
    
    json_path = image_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Created {json_path}")
```

#### Step 3: Update Tests

**Option A: Replace golden samples directory:**
```bash
# Backup original samples
mv samples samples_original

# Use custom samples
mv custom_samples samples

# Run tests
pytest tests/
```

**Option B: Configure via environment variable:**
```bash
# In conftest.py
@pytest.fixture
def golden_samples_dir():
    """Path to golden sample images."""
    custom_dir = os.getenv('GOLDEN_SAMPLES_DIR')
    if custom_dir:
        return Path(custom_dir)
    return Path(__file__).parent.parent / "samples"

# Run tests with custom samples
GOLDEN_SAMPLES_DIR=/path/to/custom_samples pytest tests/
```

**Option C: Parametrize tests:**
```python
@pytest.mark.parametrize("samples_dir", [
    "samples",           # Original golden samples
    "custom_samples",    # Your custom samples
])
def test_with_multiple_datasets(samples_dir):
    """Test against multiple sample datasets."""
    # Test logic
    pass
```

---



---



---



---

## Resources

- **Sample Generator:** [`gen_samples.py`](gen_samples.py)
- **Generator Docs:** [`SAMPLE_GENERATOR.md`](SAMPLE_GENERATOR.md), [`GENERATOR_README.md`](GENERATOR_README.md)
- **Test Fixtures:** [`tests/conftest.py`](../tests/conftest.py)
- **AWS S3 Documentation:** [https://docs.aws.amazon.com/s3/](https://docs.aws.amazon.com/s3/)

---



---

**Last Updated:** 2026-02-16  
**Golden Dataset Version:** 1.0

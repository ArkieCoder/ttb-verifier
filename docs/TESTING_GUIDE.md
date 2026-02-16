# Testing Guide - TTB Label Verifier

## Overview

The TTB Label Verifier uses a dual testing strategy:
1. **Bash Tests** (`run_tests.sh`) - Quick smoke tests for local development
2. **Pytest Suite** (`tests/`) - Comprehensive unit, integration, and API tests

**Coverage Target:** 80% minimum (enforced in Docker build)

---

## Quick Reference

```bash
# Bash smoke tests (30 seconds)
./run_tests.sh --quick

# Pytest all tests (2 minutes)
pytest tests/ -v

# Pytest with coverage
pytest tests/ --cov=. --cov-report=html

# Docker build with tests
docker build --target test -t ttb-verifier:test .

# Run tests in Docker container
docker-compose exec verifier pytest tests/ -v
```

---

## Bash Test Suite

### Overview

**File:** `run_tests.sh`  
**Tests:** 24 tests across 8 categories  
**Runtime:** ~30 seconds (--quick mode)

**Purpose:**
- Quick smoke tests for local development
- Human-readable colored output
- Direct CLI behavior testing
- Fast feedback loop

### Running Bash Tests

```bash
# All tests including slow Ollama tests
./run_tests.sh

# Quick mode (skip Ollama tests) - recommended
./run_tests.sh --quick

# Verbose mode (show command output)
./run_tests.sh --quick --verbose

# Stop at first failure
./run_tests.sh --quick --stop-on-error

# Clean up test artifacts after run
./run_tests.sh --quick --cleanup

# Show help
./run_tests.sh --help
```

### Test Categories

1. **Single Label Verification** (5 tests)
   - GOOD label with ground truth
   - BAD label with ground truth
   - Structural validation only
   - Error handling (missing file, invalid JSON)

2. **Output Format** (4 tests)
   - JSON to file
   - Compact JSON output (no pretty-print)
   - Verbose mode
   - Pipeline compatibility

3. **Batch Processing** (4 tests)
   - Small batch (6 samples)
   - Full batch (40 samples)
   - Verbose output with summary
   - Output to file

4. **OCR Backend** (3 tests)
   - Tesseract backend
   - Invalid backend name
   - Ollama backend (slow, skipped in --quick mode)

5. **Comprehensive Test Suite** (2 tests)
   - test_verifier.py with summary
   - JSON output with metrics

6. **Performance** (2 tests)
   - Single label <5 seconds
   - Batch average <1 second per label

7. **Help & Documentation** (2 tests)
   - verify_label.py --help
   - test_verifier.py --help

8. **Field Extraction** (3 tests)
   - Extract required fields
   - Detect violations
   - Government warning validation

### Expected Output

```
========================================
TTB Label Verifier - Comprehensive Test Suite
========================================

[TEST 1] Single GOOD label with ground truth
  ✓ PASS Exit code 1 (non-compliant due to OCR), valid JSON

[TEST 2] Single BAD label with ground truth
  ✓ PASS Exit code 1 (non-compliant), valid JSON

...

========================================
TEST SUMMARY
========================================

Total tests run:   24
Passed:            24
Failed:            0
Skipped:           1

✓ All tests passed!
```

---

## Pytest Suite

### Overview

**Structure:**
```
tests/
├── __init__.py
├── conftest.py                       # Shared fixtures
├── test_unit/                        # Unit tests (fast)
│   ├── test_field_validators.py
│   ├── test_label_extractor.py
│   ├── test_ocr_backends.py
│   └── test_label_validator.py
├── test_integration/                 # Integration tests
│   ├── test_cli.py
│   └── test_end_to_end.py
└── test_api/                         # API tests
    └── test_fastapi_endpoints.py
```

**Total:** ~15 test files, ~1000 lines of test code

### Running Pytest Tests

#### Basic Commands

```bash
# Run all tests
pytest tests/

# Verbose output
pytest tests/ -v

# Stop at first failure
pytest tests/ -x

# Run specific test file
pytest tests/test_unit/test_field_validators.py -v

# Run specific test function
pytest tests/test_unit/test_field_validators.py::test_fuzzy_match_exact -v

# Run tests matching pattern
pytest tests/ -k "test_brand"
```

#### With Coverage

```bash
# Run with coverage
pytest tests/ --cov=.

# With HTML report
pytest tests/ --cov=. --cov-report=html

# With missing lines highlighted
pytest tests/ --cov=. --cov-report=term-missing

# Fail if coverage below 80%
pytest tests/ --cov=. --cov-fail-under=80
```

#### By Category

```bash
# Unit tests only
pytest tests/test_unit/ -v

# Integration tests only
pytest tests/test_integration/ -v

# API tests only
pytest tests/test_api/ -v

# Using markers
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m api -v
```

### Test Fixtures

Shared fixtures defined in `tests/conftest.py`:

#### Path Fixtures
```python
@pytest.fixture
def golden_samples_dir():
    """Path to golden sample images (samples/)"""
    return Path(__file__).parent.parent / "samples"

@pytest.fixture
def good_label_path(golden_samples_dir):
    """Path to label_good_001.jpg"""
    return golden_samples_dir / "label_good_001.jpg"

@pytest.fixture
def bad_label_path(golden_samples_dir):
    """Path to label_bad_001.jpg"""
    return golden_samples_dir / "label_bad_001.jpg"
```

#### Ground Truth Fixtures
```python
@pytest.fixture
def good_ground_truth(golden_samples_dir):
    """Load ground truth for good label"""
    # Returns: {"brand_name": "Ridge & Co.", "abv": 7.5, ...}

@pytest.fixture
def bad_ground_truth(golden_samples_dir):
    """Load ground truth for bad label"""
```

#### Mock OCR Fixtures
```python
@pytest.fixture
def mock_ocr_text_good():
    """Mock OCR output for compliant label"""
    # Returns: Multi-line string with all fields

@pytest.fixture
def mock_ocr_text_missing_abv():
    """Mock OCR output with missing ABV"""
```

### Using Fixtures

```python
def test_extract_brand_name(good_label_path, good_ground_truth):
    """Test brand name extraction."""
    # Use fixtures in test
    extractor = LabelExtractor()
    # ... test code
```

---

## Test Coverage

### Current Coverage Targets

| Module | Target | Actual | Status |
|--------|--------|--------|--------|
| `field_validators.py` | 90% | TBD | 🔄 |
| `label_extractor.py` | 85% | TBD | 🔄 |
| `ocr_backends.py` | 70% | TBD | 🔄 |
| `label_validator.py` | 90% | TBD | 🔄 |
| `verify_label.py` | 60% | TBD | 🔄 |
| `api.py` | 95% | TBD | 🔄 |
| **Overall** | **80%** | **TBD** | **🔄** |

### Viewing Coverage Reports

#### Terminal Output
```bash
pytest tests/ --cov=. --cov-report=term-missing
```

Example output:
```
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
field_validators.py          150     15    90%   45-47, 89-92
label_extractor.py           200     30    85%   120-125, 180-185
ocr_backends.py              100     30    70%   45-60, 85-90
label_validator.py           150     15    90%   110-112
verify_label.py              120     48    60%   150-170, 200-220
api.py                       180      9    95%   89-92
--------------------------------------------------------
TOTAL                        900     147   84%
```

#### HTML Report
```bash
# Generate report
pytest tests/ --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html
```

Features:
- ✅ Color-coded coverage
- ✅ Click through to source
- ✅ See uncovered lines highlighted
- ✅ Branch coverage details

### Improving Coverage

**Identify uncovered code:**
```bash
# Show missing lines
pytest tests/ --cov=. --cov-report=term-missing

# Focus on specific module
pytest tests/ --cov=field_validators --cov-report=term-missing
```

**Write targeted tests:**
```python
# Example: Cover edge case
def test_fuzzy_match_with_none():
    """Test fuzzy match handles None gracefully."""
    validator = FieldValidator()
    score = validator.fuzzy_match(None, "test")
    assert score == 0.0
```

**Run only new tests:**
```bash
# Run tests that cover specific function
pytest tests/ -k "fuzzy_match" --cov=field_validators
```

---

## Golden Sample Dataset

### Overview

**Location:** `samples/` directory  
**Size:** 4.9MB (40 images + 40 JSON files)  
**Composition:**
- 20 GOOD labels (compliant)
- 20 BAD labels (various violations)

**Usage:**
- Integration tests verify against known good/bad labels
- End-to-end tests validate full pipeline
- Bash tests process entire dataset

### Sample Structure

Each sample consists of:
1. **Image file** (`label_good_001.jpg`)
2. **Metadata file** (`label_good_001.json`)

**Metadata Format:**
```json
{
  "generated_at": "2026-02-16T08:56:39.359308",
  "label_type": "GOOD",
  "product_type": "malt_beverage",
  "container_size": 64,
  "is_import": true,
  "ground_truth": {
    "brand_name": "Ridge & Co.",
    "class_type": "Hefeweizen",
    "alcohol_content_numeric": 7.5,
    "net_contents": "64 fl oz",
    "bottler_info": "Imported by Black Brewing, San Francisco, CA",
    "country_of_origin": "Product of Italy",
    "government_warning": "GOVERNMENT WARNING: ..."
  }
}
```

### Using Golden Samples in Tests

```python
def test_good_label_passes_structural(good_label_path):
    """Test that GOOD label passes structural validation."""
    validator = LabelValidator(ocr_backend="tesseract")
    result = validator.validate_label(str(good_label_path))
    
    # Check all required fields present
    assert result['extracted_fields']['brand_name'] is not None
    assert result['extracted_fields']['abv_numeric'] is not None
    assert result['extracted_fields']['net_contents'] is not None
```

### Replacing Golden Samples

**For Custom Testing:**

1. **Generate new samples:**
```bash
python gen_samples.py --count 10 --output my_samples/
```

2. **Update test fixtures:**
```python
# In conftest.py
@pytest.fixture
def custom_samples_dir():
    return Path("my_samples/")
```

3. **Run tests:**
```bash
pytest tests/ --custom-samples my_samples/
```

See `docs/GOLDEN_SAMPLES.md` for detailed instructions.

---

## Writing Tests

### Unit Test Example

```python
# tests/test_unit/test_field_validators.py

import pytest
from field_validators import FieldValidator

class TestFuzzyMatching:
    """Test fuzzy matching functionality."""
    
    def test_exact_match(self):
        """Test exact string match returns 1.0."""
        validator = FieldValidator()
        score = validator.fuzzy_match("Ridge & Co.", "Ridge & Co.")
        assert score == 1.0
    
    def test_case_insensitive(self):
        """Test case insensitive matching."""
        validator = FieldValidator()
        score = validator.fuzzy_match("ridge & co.", "RIDGE & CO.")
        assert score == 1.0
    
    def test_90_percent_threshold(self):
        """Test that 90% similarity is acceptable."""
        validator = FieldValidator()
        score = validator.fuzzy_match("Ridge & Co.", "Ridge and Co.")
        assert score >= 0.90
    
    def test_below_threshold(self):
        """Test that <90% similarity fails."""
        validator = FieldValidator()
        score = validator.fuzzy_match("Ridge & Co.", "Completely Different")
        assert score < 0.90
    
    @pytest.mark.parametrize("text1,text2,expected_min", [
        ("Ridge & Co.", "Ridge and Co.", 0.85),
        ("Black Brewing", "Black Brewery", 0.90),
        ("", "something", 0.0),
    ])
    def test_parametrized_fuzzy_match(self, text1, text2, expected_min):
        """Test fuzzy matching with multiple inputs."""
        validator = FieldValidator()
        score = validator.fuzzy_match(text1, text2)
        assert score >= expected_min
```

### Integration Test Example

```python
# tests/test_integration/test_end_to_end.py

import subprocess
import json

def test_cli_good_label_with_ground_truth(good_label_path, good_ground_truth):
    """Test full pipeline via CLI."""
    # Write ground truth to temp file
    gt_path = "/tmp/ground_truth.json"
    with open(gt_path, 'w') as f:
        json.dump({"ground_truth": good_ground_truth}, f)
    
    # Run CLI
    result = subprocess.run(
        ["python3", "verify_label.py", str(good_label_path), 
         "--ground-truth", gt_path],
        capture_output=True,
        text=True
    )
    
    # Parse JSON output
    output = json.loads(result.stdout)
    
    # Verify results
    assert output['status'] in ['COMPLIANT', 'NON_COMPLIANT']
    assert output['validation_level'] == 'FULL_VALIDATION'
    assert 'extracted_fields' in output
    assert 'violations' in output
```

### API Test Example

```python
# tests/test_api/test_fastapi_endpoints.py

from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_verify_endpoint_success(good_label_path):
    """Test /verify endpoint with valid image."""
    with open(good_label_path, 'rb') as f:
        response = client.post(
            "/verify",
            files={"image": ("label.jpg", f, "image/jpeg")},
            data={"ocr_backend": "tesseract"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "extracted_fields" in data

def test_verify_endpoint_file_too_large():
    """Test /verify rejects files >10MB."""
    # Create 11MB file
    large_file = b"x" * (11 * 1024 * 1024)
    
    response = client.post(
        "/verify",
        files={"image": ("large.jpg", large_file, "image/jpeg")}
    )
    
    assert response.status_code == 413
    assert "too large" in response.json()["error"].lower()
```

---

## Test-Driven Development (TDD)

### TDD Workflow

1. **Write failing test:**
```python
def test_new_feature():
    """Test new feature that doesn't exist yet."""
    result = new_feature("input")
    assert result == "expected"
```

2. **Run test (should fail):**
```bash
pytest tests/test_unit/test_new.py::test_new_feature -v
# FAILED - AttributeError: 'module' object has no attribute 'new_feature'
```

3. **Implement minimal code to pass:**
```python
def new_feature(input):
    return "expected"
```

4. **Run test again (should pass):**
```bash
pytest tests/test_unit/test_new.py::test_new_feature -v
# PASSED
```

5. **Refactor and improve:**
```python
def new_feature(input):
    # Better implementation
    processed = process(input)
    return format_output(processed)
```

6. **Verify test still passes:**
```bash
pytest tests/test_unit/test_new.py::test_new_feature -v
# PASSED
```

---

## Continuous Integration

### Docker Build (Automatic Testing)

Tests run automatically during Docker build:

```bash
# Build fails if tests fail or coverage <80%
docker build --target test -t ttb-verifier:test .
```

**Test Stage Output:**
```
Step 10/15 : RUN pytest tests/ --cov=. --cov-fail-under=80 -v
---> Running in abc123def456

============================= test session starts ==============================
collected 87 items

tests/test_unit/test_field_validators.py::test_fuzzy_match PASSED      [  1%]
tests/test_unit/test_field_validators.py::test_abv_tolerance PASSED    [  2%]
...
tests/test_api/test_fastapi_endpoints.py::test_batch PASSED            [100%]

---------- coverage: platform linux, python 3.12.3 -----------
Name                       Stmts   Miss  Cover
----------------------------------------------
field_validators.py          150     12    92%
label_extractor.py           200     25    88%
...
----------------------------------------------
TOTAL                        900    120    87%

Required test coverage of 80% reached. Total coverage: 87.00%
============================== 87 passed in 45.23s =============================
```

### GitHub Actions (Future)

**Workflow:** `.github/workflows/test.yml`

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and test
        run: docker build --target test .
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## Troubleshooting Tests

### Test Failures

**View detailed error:**
```bash
pytest tests/test_unit/test_field_validators.py::test_fuzzy_match -vv
```

**Debug with print statements:**
```python
def test_something():
    result = function_under_test()
    print(f"DEBUG: result = {result}")  # Shows in pytest -s output
    assert result == expected
```

**Run with print output:**
```bash
pytest tests/ -v -s  # -s shows print statements
```

### Fixture Issues

**List available fixtures:**
```bash
pytest --fixtures
```

**Debug fixture:**
```python
def test_debug_fixture(good_label_path):
    """Debug fixture value."""
    print(f"Path: {good_label_path}")
    print(f"Exists: {good_label_path.exists()}")
    assert False  # Intentional failure to see output
```

### Coverage Not Updating

**Clear cache and re-run:**
```bash
rm -rf .pytest_cache/ .coverage htmlcov/
pytest tests/ --cov=. --cov-report=html
```

### Slow Tests

**Profile test execution:**
```bash
pytest tests/ --durations=10  # Show 10 slowest tests
```

**Skip slow tests:**
```bash
pytest tests/ -m "not slow"
```

### Import Errors

**Check Python path:**
```bash
pytest tests/ -vv  # Shows import paths
```

**Run from project root:**
```bash
cd /path/to/takehome
pytest tests/  # Not from tests/ directory
```

---

## Best Practices

### Test Naming

```python
# Good: Descriptive, explains what's tested
def test_fuzzy_match_returns_one_for_exact_match():
    pass

# Good: Test specific behavior
def test_validate_abv_rejects_value_outside_tolerance():
    pass

# Bad: Vague
def test_validator():
    pass
```

### Test Organization

```python
class TestABVValidation:
    """Group related tests."""
    
    def test_wine_tolerance(self):
        """Wine has ±1.0% tolerance."""
        pass
    
    def test_spirits_tolerance(self):
        """Spirits have ±0.3% tolerance."""
        pass
```

### Assertions

```python
# Good: Specific assertion messages
assert result == expected, f"Expected {expected}, got {result}"

# Good: Multiple assertions for clarity
assert 'status' in result
assert result['status'] in ['COMPLIANT', 'NON_COMPLIANT']
assert isinstance(result['violations'], list)

# Bad: Generic assertion
assert result
```

### Mocking

```python
from unittest.mock import patch, MagicMock

def test_ocr_backend_failure():
    """Test graceful handling of OCR failure."""
    with patch('ocr_backends.TesseractOCR') as mock_ocr:
        mock_ocr.return_value.extract_text.side_effect = Exception("OCR failed")
        
        validator = LabelValidator()
        result = validator.validate_label("test.jpg")
        
        assert result['status'] == 'ERROR'
```

---

## Resources

- **Pytest Documentation:** https://docs.pytest.org/
- **Coverage.py:** https://coverage.readthedocs.io/
- **FastAPI Testing:** https://fastapi.tiangolo.com/tutorial/testing/
- **Mocking Guide:** https://docs.python.org/3/library/unittest.mock.html

---

**Last Updated:** 2026-02-16  
**Pytest Version:** 8.0.0  
**Coverage Target:** 80%

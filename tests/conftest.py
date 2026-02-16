"""Shared pytest fixtures for TTB Label Verifier tests."""
import pytest
import json
from pathlib import Path
from typing import Dict, Any


# Paths
@pytest.fixture
def project_root():
    """Project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def samples_dir(project_root):
    """Golden samples directory."""
    return project_root / "samples"


@pytest.fixture
def good_label_path(samples_dir):
    """Path to first good label."""
    return samples_dir / "label_good_001.jpg"


@pytest.fixture
def bad_label_path(samples_dir):
    """Path to first bad label."""
    return samples_dir / "label_bad_001.jpg"


@pytest.fixture
def good_ground_truth(samples_dir) -> Dict[str, Any]:
    """Load ground truth for good label."""
    json_path = samples_dir / "label_good_001.json"
    if not json_path.exists():
        pytest.skip(f"Golden sample not found: {json_path}")
    
    with open(json_path) as f:
        data = json.load(f)
    return data['ground_truth']


@pytest.fixture
def bad_ground_truth(samples_dir) -> Dict[str, Any]:
    """Load ground truth for bad label."""
    json_path = samples_dir / "label_bad_001.json"
    if not json_path.exists():
        pytest.skip(f"Golden sample not found: {json_path}")
    
    with open(json_path) as f:
        data = json.load(f)
    return data['ground_truth']


# Mock OCR outputs
@pytest.fixture
def mock_ocr_text_good():
    """Mock OCR text for a compliant label."""
    return """Ridge & Co.
Hefeweizen
7.5% ABV
64 fl oz
Imported by Black Brewing, San Francisco, CA
Product of Italy

GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."""


@pytest.fixture
def mock_ocr_text_missing_abv():
    """Mock OCR text missing ABV."""
    return """Black Brewing
Pinot Noir
375 mL
Packed by Cedar Cellars, San Diego, CA

GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."""


# Test data
@pytest.fixture
def sample_extracted_fields():
    """Sample extracted fields for testing validators."""
    return {
        'brand_name': 'Ridge & Co.',
        'abv': 7.5,
        'net_contents': '64 fl oz',
        'bottler': 'Imported by Black Brewing, San Francisco, CA',
        'product_type': 'Hefeweizen'
    }


@pytest.fixture
def sample_ground_truth():
    """Sample ground truth for testing validators."""
    return {
        'brand_name': 'Ridge & Co.',
        'abv': 7.5,
        'net_contents': '64 fl oz',
        'bottler': 'Imported by Black Brewing, San Francisco, CA',
        'product_type': 'Hefeweizen'
    }

"""Unit tests for field_validators.py"""
import pytest
from field_validators import FieldValidator, ValidationResult


class TestFuzzyMatching:
    """Test fuzzy matching functionality."""
    
    def test_exact_match_returns_one(self):
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
        assert score >= 0.85  # Should be very similar
    
    def test_below_threshold(self):
        """Test that low similarity scores work."""
        validator = FieldValidator()
        score = validator.fuzzy_match("Ridge & Co.", "Completely Different")
        assert score < 0.50
    
    def test_none_handling(self):
        """Test fuzzy match handles None gracefully."""
        validator = FieldValidator()
        assert validator.fuzzy_match(None, "test") == 0.0
        assert validator.fuzzy_match("test", None) == 0.0
        assert validator.fuzzy_match(None, None) == 0.0
    
    def test_empty_string(self):
        """Test fuzzy match handles empty strings."""
        validator = FieldValidator()
        assert validator.fuzzy_match("", "test") == 0.0
        assert validator.fuzzy_match("test", "") == 0.0


class TestABVValidation:
    """Test ABV validation with product-specific tolerances."""
    
    def test_wine_tolerance_within_range(self):
        """Test wine ABV within ±1.0% tolerance."""
        validator = FieldValidator()
        result = validator.validate_abv(13.5, 13.0, "wine")
        assert result.is_valid is True  # Within 1.0%
    
    def test_wine_tolerance_outside_range(self):
        """Test wine ABV outside ±1.0% tolerance."""
        validator = FieldValidator()
        result = validator.validate_abv(15.5, 13.0, "wine")
        assert result.is_valid is False  # 2.5% difference
    
    def test_spirits_tolerance_within_range(self):
        """Test spirits ABV within ±0.3% tolerance."""
        validator = FieldValidator()
        result = validator.validate_abv(40.2, 40.0, "spirits")
        assert result.is_valid is True
    
    def test_spirits_tolerance_outside_range(self):
        """Test spirits ABV outside ±0.3% tolerance."""
        validator = FieldValidator()
        result = validator.validate_abv(40.5, 40.0, "spirits")
        assert result.is_valid is False
    
    def test_missing_abv(self):
        """Test missing ABV is detected."""
        validator = FieldValidator()
        result = validator.validate_abv(None, 13.0, "wine")
        assert result.is_valid is False
        assert "not found" in result.error_message.lower()
    
    def test_unknown_product_type(self):
        """Test unknown product type defaults to 0.3% tolerance."""
        validator = FieldValidator()
        result = validator.validate_abv(13.25, 13.0, "unknown")
        assert result.is_valid is True  # 0.25% within 0.3%


class TestBrandNameValidation:
    """Test brand name validation."""
    
    def test_exact_match(self):
        """Test exact brand name match."""
        validator = FieldValidator()
        result = validator.validate_brand_name("Ridge & Co.", "Ridge & Co.")
        assert result.is_valid is True
        assert result.similarity_score == 1.0
    
    def test_near_match(self):
        """Test near match above threshold."""
        validator = FieldValidator()
        result = validator.validate_brand_name("Ridge and Co.", "Ridge & Co.")
        assert result.is_valid is True
        assert result.similarity_score >= 0.90
    
    def test_mismatch(self):
        """Test brand name mismatch."""
        validator = FieldValidator()
        result = validator.validate_brand_name("Different Brand", "Ridge & Co.")
        assert result.is_valid is False
        assert result.similarity_score < 0.90
    
    def test_missing_brand(self):
        """Test missing brand name."""
        validator = FieldValidator()
        result = validator.validate_brand_name(None, "Ridge & Co.")
        assert result.is_valid is False


class TestNetContentsValidation:
    """Test net contents validation."""
    
    def test_exact_match(self):
        """Test exact net contents match."""
        validator = FieldValidator()
        result = validator.validate_net_contents("750 mL", "750 mL")
        assert result.is_valid is True
    
    def test_case_variations(self):
        """Test case variations in net contents."""
        validator = FieldValidator()
        result = validator.validate_net_contents("750 ML", "750 mL")
        assert result.is_valid is True  # Should handle case
    
    def test_missing_contents(self):
        """Test missing net contents."""
        validator = FieldValidator()
        result = validator.validate_net_contents(None, "750 mL")
        assert result.is_valid is False


class TestValidationResult:
    """Test ValidationResult model."""
    
    def test_to_dict(self):
        """Test ValidationResult to_dict conversion."""
        result = ValidationResult(
            field_name="brand_name",
            is_valid=True,
            expected="Test Brand",
            actual="Test Brand",
            similarity_score=1.0
        )
        data = result.to_dict()
        
        assert data['field'] == 'brand_name'
        assert data['valid'] is True
        assert data['expected'] == 'Test Brand'
        assert data['actual'] == 'Test Brand'
        assert data['similarity_score'] == 1.0
    
    def test_to_dict_with_error(self):
        """Test ValidationResult with error message."""
        result = ValidationResult(
            field_name="abv",
            is_valid=False,
            error_message="ABV not found"
        )
        data = result.to_dict()
        
        assert data['valid'] is False
        assert data['error'] == "ABV not found"

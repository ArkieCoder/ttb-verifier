"""
Field-level validators for TTB label verification.

This module implements Tier 2 validation: comparing extracted fields
against ground truth/application data with appropriate tolerance and
fuzzy matching rules per 27 CFR regulations.
"""

from typing import Optional, Dict, Any, List, Tuple
from difflib import SequenceMatcher


class ValidationResult:
    """Result of a field validation check."""
    
    def __init__(self, 
                 field_name: str,
                 is_valid: bool,
                 expected: Optional[str] = None,
                 actual: Optional[str] = None,
                 error_message: Optional[str] = None,
                 similarity_score: Optional[float] = None):
        self.field_name = field_name
        self.is_valid = is_valid
        self.expected = expected
        self.actual = actual
        self.error_message = error_message
        self.similarity_score = similarity_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        result = {
            "field": self.field_name,
            "valid": self.is_valid,
            "expected": self.expected,
            "actual": self.actual
        }
        if self.error_message:
            result["error"] = self.error_message
        if self.similarity_score is not None:
            result["similarity_score"] = round(self.similarity_score, 3)
        return result


class FieldValidator:
    """Validates extracted label fields against ground truth data."""
    
    # Fuzzy matching threshold (90% similarity)
    FUZZY_MATCH_THRESHOLD = 0.90
    
    # ABV tolerance by product type (27 CFR regulations)
    ABV_TOLERANCE = {
        "wine": 1.0,      # ±1.0% for wine (27 CFR § 4.36)
        "spirits": 0.3,   # ±0.3% for spirits (27 CFR § 5.37)
        "beer": 0.3,      # ±0.3% for beer (27 CFR § 7.71)
        "malt": 0.3       # ±0.3% for malt beverages
    }
    
    @staticmethod
    def fuzzy_match(text1: str, text2: str) -> float:
        """
        Calculate similarity score between two strings.
        
        Returns a value between 0.0 (no match) and 1.0 (perfect match).
        Uses SequenceMatcher with case-insensitive comparison.
        """
        if text1 is None or text2 is None:
            return 0.0
        
        # Normalize: strip whitespace, lowercase
        normalized1 = str(text1).strip().lower()
        normalized2 = str(text2).strip().lower()
        
        if not normalized1 or not normalized2:
            return 0.0
        
        # Calculate similarity ratio
        return SequenceMatcher(None, normalized1, normalized2).ratio()
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison (lowercase, strip, collapse whitespace)."""
        if not text:
            return ""
        # Collapse multiple spaces into one
        import re
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        return normalized
    
    def validate_brand_name(self, 
                           extracted: Optional[str],
                           expected: str) -> ValidationResult:
        """
        Validate brand name with fuzzy matching.
        
        Args:
            extracted: Brand name extracted from label
            expected: Brand name from ground truth/application
            
        Returns:
            ValidationResult indicating if match passes threshold
        """
        if not extracted:
            return ValidationResult(
                field_name="brand_name",
                is_valid=False,
                expected=expected,
                actual=extracted,
                error_message="Brand name not found in label"
            )
        
        similarity = self.fuzzy_match(extracted, expected)
        is_valid = similarity >= self.FUZZY_MATCH_THRESHOLD
        
        return ValidationResult(
            field_name="brand_name",
            is_valid=is_valid,
            expected=expected,
            actual=extracted,
            error_message=None if is_valid else f"Brand name mismatch (similarity: {similarity:.1%})",
            similarity_score=similarity
        )
    
    def validate_abv(self,
                    extracted: Optional[float],
                    expected: float,
                    product_type: str) -> ValidationResult:
        """
        Validate alcohol by volume with product-specific tolerance.
        
        Args:
            extracted: ABV extracted from label (as percentage, e.g., 13.5)
            expected: ABV from ground truth/application
            product_type: One of "wine", "spirits", "beer", "malt"
            
        Returns:
            ValidationResult indicating if ABV is within tolerance
        """
        if extracted is None:
            return ValidationResult(
                field_name="abv",
                is_valid=False,
                expected=f"{expected}%",
                actual=None,
                error_message="ABV not found in label"
            )
        
        # Get tolerance for product type (default to wine tolerance if unknown)
        if product_type:
            tolerance = self.ABV_TOLERANCE.get(product_type.lower(), 0.3)
        else:
            tolerance = 1.0  # Default to most lenient (wine)
        
        # Check if within tolerance
        difference = abs(extracted - expected)
        is_valid = difference <= tolerance
        
        return ValidationResult(
            field_name="abv",
            is_valid=is_valid,
            expected=f"{expected}%",
            actual=f"{extracted}%",
            error_message=None if is_valid else f"ABV outside tolerance (±{tolerance}%): difference is {difference:.2f}%"
        )
    
    def validate_net_contents(self,
                            extracted: Optional[str],
                            expected: str) -> ValidationResult:
        """
        Validate net contents with fuzzy matching.
        
        Args:
            extracted: Net contents extracted from label
            expected: Net contents from ground truth/application
            
        Returns:
            ValidationResult indicating if match passes threshold
        """
        if not extracted:
            return ValidationResult(
                field_name="net_contents",
                is_valid=False,
                expected=expected,
                actual=extracted,
                error_message="Net contents not found in label"
            )
        
        similarity = self.fuzzy_match(extracted, expected)
        is_valid = similarity >= self.FUZZY_MATCH_THRESHOLD
        
        return ValidationResult(
            field_name="net_contents",
            is_valid=is_valid,
            expected=expected,
            actual=extracted,
            error_message=None if is_valid else f"Net contents mismatch (similarity: {similarity:.1%})",
            similarity_score=similarity
        )
    
    def validate_bottler(self,
                        extracted: Optional[str],
                        expected: str) -> ValidationResult:
        """
        Validate bottler/producer information with fuzzy matching.
        
        Args:
            extracted: Bottler info extracted from label
            expected: Bottler info from ground truth/application
            
        Returns:
            ValidationResult indicating if match passes threshold
        """
        if not extracted:
            return ValidationResult(
                field_name="bottler",
                is_valid=False,
                expected=expected,
                actual=extracted,
                error_message="Bottler information not found in label"
            )
        
        similarity = self.fuzzy_match(extracted, expected)
        is_valid = similarity >= self.FUZZY_MATCH_THRESHOLD
        
        return ValidationResult(
            field_name="bottler",
            is_valid=is_valid,
            expected=expected,
            actual=extracted,
            error_message=None if is_valid else f"Bottler mismatch (similarity: {similarity:.1%})",
            similarity_score=similarity
        )
    
    def validate_product_type(self,
                             extracted: Optional[str],
                             expected: str) -> ValidationResult:
        """
        Validate product type with fuzzy matching.
        
        Args:
            extracted: Product type extracted from label
            expected: Product type from ground truth/application
            
        Returns:
            ValidationResult indicating if match passes threshold
        """
        if not extracted:
            return ValidationResult(
                field_name="product_type",
                is_valid=False,
                expected=expected,
                actual=extracted,
                error_message="Product type not found in label"
            )
        
        similarity = self.fuzzy_match(extracted, expected)
        is_valid = similarity >= self.FUZZY_MATCH_THRESHOLD
        
        return ValidationResult(
            field_name="product_type",
            is_valid=is_valid,
            expected=expected,
            actual=extracted,
            error_message=None if is_valid else f"Product type mismatch (similarity: {similarity:.1%})",
            similarity_score=similarity
        )
    
    def validate_all_fields(self,
                           extracted_fields: Dict[str, Any],
                           ground_truth: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate all fields against ground truth.
        
        Args:
            extracted_fields: Dictionary of fields extracted from label
            ground_truth: Dictionary of expected values from application
            
        Returns:
            List of ValidationResult objects for each field
        """
        results = []
        
        # Validate brand name
        if "brand_name" in ground_truth:
            result = self.validate_brand_name(
                extracted_fields.get("brand_name"),
                ground_truth["brand_name"]
            )
            results.append(result)
        
        # Validate ABV
        if "abv" in ground_truth:
            extracted_abv = extracted_fields.get("abv")
            # Convert to float if it's a string
            if isinstance(extracted_abv, str):
                try:
                    extracted_abv = float(extracted_abv.rstrip('%'))
                except (ValueError, AttributeError):
                    extracted_abv = None
            
            result = self.validate_abv(
                extracted_abv,
                float(ground_truth["abv"]),
                ground_truth.get("product_type", "wine")
            )
            results.append(result)
        
        # Validate net contents
        if "net_contents" in ground_truth:
            result = self.validate_net_contents(
                extracted_fields.get("net_contents"),
                ground_truth["net_contents"]
            )
            results.append(result)
        
        # Validate bottler
        if "bottler" in ground_truth:
            result = self.validate_bottler(
                extracted_fields.get("bottler"),
                ground_truth["bottler"]
            )
            results.append(result)
        
        # Validate product type
        if "product_type" in ground_truth:
            result = self.validate_product_type(
                extracted_fields.get("product_type"),
                ground_truth["product_type"]
            )
            results.append(result)
        
        return results

"""
TTB Label Validator - Main orchestration module.

Implements two-tier validation strategy:
- Tier 1: Structural validation (no ground truth needed)
- Tier 2: Accuracy validation (requires ground truth)

Outputs unified JSON format for CLI and API.
"""

import os
import time
from typing import Dict, Any, Optional, List
from enum import Enum

from ocr_backends import OCRBackend, TesseractOCR, OllamaOCR
from label_extractor import LabelExtractor, GOVERNMENT_WARNING_TEXT
from field_validators import FieldValidator


class ValidationStatus(Enum):
    """Overall validation status."""
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PARTIAL_VALIDATION = "PARTIAL_VALIDATION"


class ValidationLevel(Enum):
    """Level of validation performed."""
    STRUCTURAL_ONLY = "STRUCTURAL_ONLY"  # Tier 1 only
    FULL_VALIDATION = "FULL_VALIDATION"  # Tier 1 + Tier 2


class LabelValidator:
    """Main validator orchestrating OCR, extraction, and validation."""
    
    def __init__(self, ocr_backend: str = "tesseract", ollama_host: Optional[str] = None):
        """
        Initialize validator with specified OCR backend.
        
        Args:
            ocr_backend: "tesseract" (fast) or "ollama" (accurate)
            ollama_host: Ollama API host URL (defaults to OLLAMA_HOST env var or http://localhost:11434)
        """
        # Initialize OCR backend
        if ocr_backend.lower() == "ollama":
            host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
            self.ocr = OllamaOCR(host=host)
        else:
            self.ocr = TesseractOCR()
        
        # Initialize extractor and validator
        self.extractor = LabelExtractor()
        self.validator = FieldValidator()
    
    def validate_label(self,
                      image_path: str,
                      ground_truth: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate a label image.
        
        Args:
            image_path: Path to label image file
            ground_truth: Optional dictionary with expected values:
                {
                    "brand_name": str,
                    "abv": float,
                    "net_contents": str,
                    "bottler": str,
                    "product_type": str (wine/spirits/beer/malt)
                }
        
        Returns:
            JSON-serializable dictionary with validation results:
            {
                "status": "COMPLIANT" | "NON_COMPLIANT" | "PARTIAL_VALIDATION",
                "validation_level": "STRUCTURAL_ONLY" | "FULL_VALIDATION",
                "extracted_fields": {...},
                "validation_results": {
                    "structural": [...],
                    "accuracy": [...]
                },
                "violations": [...],
                "warnings": [...],
                "processing_time_seconds": float
            }
        """
        start_time = time.time()
        
        # Step 1: OCR
        ocr_result = self.ocr.extract_text(image_path)
        
        # Check if OCR was successful
        if not ocr_result.get('success', False):
            return {
                "status": "ERROR",
                "error": ocr_result.get('error', 'OCR extraction failed'),
                "processing_time_seconds": round(time.time() - start_time, 3)
            }
        
        raw_text = ocr_result['raw_text']
        
        # Step 2: Extract fields
        extracted_fields = self.extractor.extract_fields(raw_text)
        
        # Step 3: Tier 1 - Structural validation
        structural_results = self._validate_structural(extracted_fields)
        
        # Step 4: Tier 2 - Accuracy validation (if ground truth provided)
        accuracy_results = []
        validation_level = ValidationLevel.STRUCTURAL_ONLY
        
        if ground_truth:
            validation_level = ValidationLevel.FULL_VALIDATION
            accuracy_results = self._validate_accuracy(extracted_fields, ground_truth)
        
        # Step 5: Determine overall status
        violations = self._collect_violations(structural_results, accuracy_results)
        warnings = self._collect_warnings(extracted_fields, ground_truth)
        status = self._determine_status(violations, ground_truth)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Build response
        return {
            "status": status.value,
            "validation_level": validation_level.value,
            "extracted_fields": self._format_extracted_fields(extracted_fields),
            "validation_results": {
                "structural": [r.to_dict() for r in structural_results],
                "accuracy": [r.to_dict() for r in accuracy_results] if accuracy_results else []
            },
            "violations": violations,
            "warnings": warnings,
            "processing_time_seconds": round(processing_time, 3)
        }
    
    def _validate_structural(self, extracted_fields: Dict[str, Any]) -> List[Any]:
        """
        Tier 1: Structural validation - check presence and format of required fields.
        
        Returns list of validation result objects.
        """
        from field_validators import ValidationResult
        
        results = []
        
        # Check brand name presence
        if not extracted_fields.get('brand_name'):
            results.append(ValidationResult(
                field_name="brand_name",
                is_valid=False,
                expected=None,
                actual=None,
                error_message="Brand name not found on label"
            ))
        else:
            results.append(ValidationResult(
                field_name="brand_name",
                is_valid=True,
                expected=None,
                actual=extracted_fields['brand_name'],
                error_message=None
            ))
        
        # Check ABV presence
        if extracted_fields.get('alcohol_content_numeric') is None:
            results.append(ValidationResult(
                field_name="abv",
                is_valid=False,
                expected=None,
                actual=None,
                error_message="Alcohol content not found on label"
            ))
        else:
            results.append(ValidationResult(
                field_name="abv",
                is_valid=True,
                expected=None,
                actual=f"{extracted_fields['alcohol_content_numeric']}%",
                error_message=None
            ))
        
        # Check net contents presence
        if not extracted_fields.get('net_contents'):
            results.append(ValidationResult(
                field_name="net_contents",
                is_valid=False,
                expected=None,
                actual=None,
                error_message="Net contents not found on label"
            ))
        else:
            results.append(ValidationResult(
                field_name="net_contents",
                is_valid=True,
                expected=None,
                actual=extracted_fields['net_contents'],
                error_message=None
            ))
        
        # Check bottler info presence
        if not extracted_fields.get('bottler_info'):
            results.append(ValidationResult(
                field_name="bottler",
                is_valid=False,
                expected=None,
                actual=None,
                error_message="Bottler information not found on label"
            ))
        else:
            results.append(ValidationResult(
                field_name="bottler",
                is_valid=True,
                expected=None,
                actual=extracted_fields['bottler_info'],
                error_message=None
            ))
        
        # Check government warning
        warning = extracted_fields.get('government_warning', {})
        
        if not warning.get('present'):
            results.append(ValidationResult(
                field_name="government_warning",
                is_valid=False,
                expected="Government warning required",
                actual=None,
                error_message="Government warning not found on label"
            ))
        else:
            # Check header capitalization
            if not warning.get('header_all_caps'):
                results.append(ValidationResult(
                    field_name="government_warning_header",
                    is_valid=False,
                    expected="GOVERNMENT WARNING:",
                    actual="Government Warning:" if warning.get('header_all_caps') is False else None,
                    error_message="Warning header must be all caps: 'GOVERNMENT WARNING:'"
                ))
            else:
                results.append(ValidationResult(
                    field_name="government_warning_header",
                    is_valid=True,
                    expected="GOVERNMENT WARNING:",
                    actual="GOVERNMENT WARNING:",
                    error_message=None
                ))
            
            # Check text match
            if not warning.get('text_matches'):
                results.append(ValidationResult(
                    field_name="government_warning_text",
                    is_valid=False,
                    expected=GOVERNMENT_WARNING_TEXT,
                    actual=warning.get('text', ''),
                    error_message="Warning text does not match required text (27 CFR § 16.21)"
                ))
            else:
                results.append(ValidationResult(
                    field_name="government_warning_text",
                    is_valid=True,
                    expected=GOVERNMENT_WARNING_TEXT,
                    actual=warning.get('text', ''),
                    error_message=None
                ))
        
        return results
    
    def _validate_accuracy(self,
                          extracted_fields: Dict[str, Any],
                          ground_truth: Dict[str, Any]) -> List[Any]:
        """
        Tier 2: Accuracy validation - compare extracted fields against ground truth.
        
        Returns list of validation result objects.
        """
        # Map extracted field names to ground truth keys
        mapped_fields = {
            'brand_name': extracted_fields.get('brand_name'),
            'abv': extracted_fields.get('alcohol_content_numeric'),
            'net_contents': extracted_fields.get('net_contents'),
            'bottler': extracted_fields.get('bottler_info'),
            'product_type': extracted_fields.get('class_type')
        }
        
        return self.validator.validate_all_fields(mapped_fields, ground_truth)
    
    def _collect_violations(self,
                          structural_results: List[Any],
                          accuracy_results: List[Any]) -> List[Dict[str, str]]:
        """Collect all validation violations into a list."""
        violations = []
        
        # Collect structural violations
        for result in structural_results:
            if not result.is_valid:
                violations.append({
                    "field": result.field_name,
                    "type": "structural",
                    "message": result.error_message
                })
        
        # Collect accuracy violations
        for result in accuracy_results:
            if not result.is_valid:
                violations.append({
                    "field": result.field_name,
                    "type": "accuracy",
                    "message": result.error_message,
                    "expected": str(result.expected),
                    "actual": str(result.actual)
                })
        
        return violations
    
    def _collect_warnings(self,
                         extracted_fields: Dict[str, Any],
                         ground_truth: Optional[Dict[str, Any]]) -> List[str]:
        """Collect warnings about validation limitations."""
        warnings = []
        
        # Warn if no ground truth provided
        if not ground_truth:
            warnings.append(
                "No ground truth provided - only structural validation performed. "
                "Provide ground truth data to enable full accuracy validation."
            )
        
        # Warn about OCR quality if fields missing
        missing_count = 0
        if not extracted_fields.get('brand_name'):
            missing_count += 1
        if extracted_fields.get('alcohol_content_numeric') is None:
            missing_count += 1
        if not extracted_fields.get('net_contents'):
            missing_count += 1
        if not extracted_fields.get('bottler_info'):
            missing_count += 1
        
        if missing_count >= 2:
            warnings.append(
                f"OCR extracted {missing_count} missing fields. "
                "Consider using --ocr-backend=ollama for better accuracy (slower)."
            )
        
        return warnings
    
    def _determine_status(self,
                         violations: List[Dict[str, str]],
                         ground_truth: Optional[Dict[str, Any]]) -> ValidationStatus:
        """Determine overall validation status."""
        if not violations:
            return ValidationStatus.COMPLIANT
        
        # If we have violations but no ground truth, it's partial validation
        if not ground_truth:
            # Check if any structural violations exist
            structural_violations = [v for v in violations if v.get('type') == 'structural']
            if structural_violations:
                return ValidationStatus.NON_COMPLIANT
            return ValidationStatus.PARTIAL_VALIDATION
        
        # Full validation with violations = non-compliant
        return ValidationStatus.NON_COMPLIANT
    
    def _format_extracted_fields(self, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Format extracted fields for JSON output."""
        return {
            "brand_name": extracted_fields.get('brand_name'),
            "product_type": extracted_fields.get('class_type'),
            "abv": extracted_fields.get('alcohol_content'),
            "abv_numeric": extracted_fields.get('alcohol_content_numeric'),
            "net_contents": extracted_fields.get('net_contents'),
            "bottler": extracted_fields.get('bottler_info'),
            "country": extracted_fields.get('country_of_origin'),
            "government_warning": {
                "present": extracted_fields.get('government_warning', {}).get('present', False),
                "header_correct": extracted_fields.get('government_warning', {}).get('header_all_caps'),
                "text_correct": extracted_fields.get('government_warning', {}).get('text_matches')
            }
        }


# Example usage
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python label_validator.py <image_path> [ground_truth.json]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    ground_truth = None
    
    if len(sys.argv) >= 3:
        with open(sys.argv[2], 'r') as f:
            ground_truth = json.load(f)
    
    validator = LabelValidator(ocr_backend="tesseract")
    result = validator.validate_label(image_path, ground_truth)
    
    print(json.dumps(result, indent=2))

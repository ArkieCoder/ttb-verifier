"""Unit tests for label_extractor.py"""
import pytest
from label_extractor import LabelExtractor, GOVERNMENT_WARNING_TEXT


class TestFieldExtraction:
    """Test field extraction from OCR text."""
    
    def test_extract_brand_name(self, mock_ocr_text_good):
        """Test brand name extraction."""
        extractor = LabelExtractor()
        fields = extractor.extract_fields(mock_ocr_text_good)
        assert fields['brand_name'] is not None
        assert 'Ridge' in fields['brand_name']
    
    def test_extract_abv(self, mock_ocr_text_good):
        """Test ABV extraction."""
        extractor = LabelExtractor()
        fields = extractor.extract_fields(mock_ocr_text_good)
        assert fields['alcohol_content_numeric'] == 7.5
    
    def test_extract_net_contents(self, mock_ocr_text_good):
        """Test net contents extraction."""
        extractor = LabelExtractor()
        fields = extractor.extract_fields(mock_ocr_text_good)
        assert '64 fl oz' in fields['net_contents']
    
    def test_missing_abv(self, mock_ocr_text_missing_abv):
        """Test detection of missing ABV."""
        extractor = LabelExtractor()
        fields = extractor.extract_fields(mock_ocr_text_missing_abv)
        assert fields['alcohol_content_numeric'] is None


class TestGovernmentWarning:
    """Test government warning extraction and validation."""
    
    def test_warning_present(self, mock_ocr_text_good):
        """Test government warning detection."""
        extractor = LabelExtractor()
        fields = extractor.extract_fields(mock_ocr_text_good)
        warning = fields['government_warning']
        assert warning['present'] is True
    
    def test_warning_header_caps(self, mock_ocr_text_good):
        """Test government warning header capitalization."""
        extractor = LabelExtractor()
        fields = extractor.extract_fields(mock_ocr_text_good)
        warning = fields['government_warning']
        assert warning['header_all_caps'] is True
    
    def test_warning_text_similarity(self, mock_ocr_text_good):
        """Test government warning text matching with similarity."""
        extractor = LabelExtractor()
        fields = extractor.extract_fields(mock_ocr_text_good)
        warning = fields['government_warning']
        # Should match or be very similar
        assert warning['text_matches'] is True or warning.get('similarity_score', 0) >= 0.85
    
    def test_missing_warning(self):
        """Test detection of missing warning."""
        extractor = LabelExtractor()
        text = "Ridge & Co.\n7.5% ABV\n750 mL"
        fields = extractor.extract_fields(text)
        warning = fields['government_warning']
        assert warning['present'] is False

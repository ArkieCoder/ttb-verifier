"""
Label Text Extractor

Parses raw OCR text into structured label fields.
Uses pattern matching and heuristics to identify:
- Brand name
- Class/type designation  
- Alcohol content
- Net contents
- Bottler information
- Country of origin
- Government warning
"""

import re
from typing import Dict, Any, Optional, List


# Government warning constant (from 27 CFR § 16.21)
GOVERNMENT_WARNING_TEXT = "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."


class LabelExtractor:
    """Extract structured fields from raw OCR text."""
    
    def __init__(self):
        """Initialize label extractor with regex patterns."""
        # Alcohol content patterns
        self.abv_patterns = [
            r'(\d+\.?\d*)\s*%\s*(?:ABV|alc\.?/?vol\.?)',  # 13.5% ABV, 13% alc./vol.
            r'(\d+\.?\d*)\s*%\s*alcohol',  # 13.5% alcohol
            r'(\d+)\s*proof',  # 80 Proof
        ]
        
        # Net contents patterns
        self.net_contents_patterns = [
            r'(\d+\.?\d*)\s*mL',  # 750 mL
            r'(\d+\.?\d*)\s*ml',  # 750 ml
            r'(\d+\.?\d*)\s*fl\s*oz',  # 12 fl oz
            r'(\d+\.?\d*)\s*fluid\s*ounces?',  # 12 fluid ounces
            r'(\d+\.?\d*)\s*L',  # 1.5 L
        ]
        
        # Bottler phrases
        self.bottler_phrases = [
            'bottled by',
            'imported by',
            'packed by',
            'produced by',
            'distilled by',
            'brewed by',
            'distributed by',
        ]
        
        # Country of origin patterns
        self.country_patterns = [
            r'product of ([a-z\s]+)',  # Product of Italy
            r'made in ([a-z\s]+)',  # Made in France
            r'imported from ([a-z\s]+)',  # Imported from Spain
        ]
    
    def extract_fields(self, raw_text: str) -> Dict[str, Any]:
        """
        Extract structured fields from raw OCR text.
        
        Args:
            raw_text: Raw text from OCR
            
        Returns:
            {
                'brand_name': str or None,
                'class_type': str or None,
                'alcohol_content': str or None,
                'alcohol_content_numeric': float or None,
                'net_contents': str or None,
                'bottler_info': str or None,
                'country_of_origin': str or None,
                'government_warning': {
                    'present': bool,
                    'text': str or None,
                    'header_all_caps': bool or None,
                    'text_matches': bool or None
                }
            }
        """
        # Normalize text for easier matching
        text_lower = raw_text.lower()
        lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
        
        result = {
            'brand_name': self._extract_brand_name(lines),
            'class_type': self._extract_class_type(lines, raw_text),
            'alcohol_content': self._extract_alcohol_content(text_lower, raw_text),
            'alcohol_content_numeric': self._extract_alcohol_numeric(text_lower),
            'net_contents': self._extract_net_contents(text_lower, raw_text),
            'bottler_info': self._extract_bottler_info(lines, raw_text),
            'country_of_origin': self._extract_country_of_origin(text_lower, raw_text),
            'government_warning': self._extract_government_warning(raw_text),
        }
        
        return result
    
    def _extract_brand_name(self, lines: List[str]) -> Optional[str]:
        """
        Extract brand name - typically first significant line of text.
        
        Heuristic: Brand is usually the first line that isn't a small label
        like "LIMITED EDITION" or single word.
        """
        if not lines:
            return None
        
        # First line is often the brand
        # Skip very short lines (< 3 chars) as they're likely decorative
        for line in lines[:5]:  # Check first 5 lines
            # Remove markdown formatting that OCR might add
            clean_line = re.sub(r'\*\*', '', line).strip()
            
            # Skip if too short or looks like a descriptor
            if len(clean_line) < 2:
                continue
            
            if clean_line.lower() in ['limited edition', 'reserve', 'premium', 'aged']:
                continue
            
            # Check if it's a government warning header
            if 'government warning' in clean_line.lower():
                continue
            
            # Check if it looks like ABV or net contents
            if re.search(r'\d+\.?\d*\s*%', clean_line, re.IGNORECASE):
                continue
            if re.search(r'\d+\.?\d*\s*(ml|fl oz|L)', clean_line, re.IGNORECASE):
                continue
            
            return clean_line
        
        return lines[0] if lines else None
    
    def _extract_class_type(self, lines: List[str], raw_text: str) -> Optional[str]:
        """
        Extract product class/type (e.g., "Cabernet Sauvignon", "Bourbon Whiskey").
        
        Common types:
        - Wine: Pinot Noir, Chardonnay, Cabernet Sauvignon, Merlot
        - Spirits: Bourbon Whiskey, Vodka, Gin, Rum, Tequila, Cognac
        - Beer: IPA, Lager, Stout, Hefeweizen, Pale Ale
        """
        # Common type keywords
        wine_types = ['chardonnay', 'pinot noir', 'cabernet', 'merlot', 'sauvignon', 
                      'zinfandel', 'riesling', 'syrah', 'shiraz', 'malbec', 'white wine', 'red wine']
        spirit_types = ['whiskey', 'bourbon', 'vodka', 'gin', 'rum', 'tequila', 'cognac',
                       'scotch', 'brandy', 'liqueur']
        beer_types = ['ipa', 'lager', 'ale', 'stout', 'porter', 'pilsner', 'hefeweizen',
                     'wheat', 'amber']
        
        text_lower = raw_text.lower()
        
        # Check for wine types
        for wine_type in wine_types:
            if wine_type in text_lower:
                # Extract the line containing this type
                for line in lines:
                    if wine_type in line.lower():
                        return re.sub(r'\*\*', '', line).strip()
        
        # Check for spirit types
        for spirit_type in spirit_types:
            if spirit_type in text_lower:
                for line in lines:
                    if spirit_type in line.lower():
                        return re.sub(r'\*\*', '', line).strip()
        
        # Check for beer types
        for beer_type in beer_types:
            if beer_type in text_lower:
                for line in lines:
                    if beer_type in line.lower():
                        return re.sub(r'\*\*', '', line).strip()
        
        # Fallback: second non-trivial line (after brand)
        if len(lines) >= 2:
            for line in lines[1:4]:
                clean_line = re.sub(r'\*\*', '', line).strip()
                if len(clean_line) > 3 and 'warning' not in clean_line.lower():
                    # Check it's not ABV or net contents
                    if not re.search(r'\d+\.?\d*\s*%', clean_line, re.IGNORECASE):
                        if not re.search(r'\d+\.?\d*\s*(ml|fl oz|L)', clean_line, re.IGNORECASE):
                            return clean_line
        
        return None
    
    def _extract_alcohol_content(self, text_lower: str, raw_text: str) -> Optional[str]:
        """Extract alcohol content as a string (e.g., '13.5% alc./vol.')."""
        for pattern in self.abv_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Find the actual text in original (preserving case)
                # Get the position and extract from raw_text
                start = match.start()
                end = match.end()
                
                # Find this in raw text (case insensitive search)
                for i in range(len(raw_text) - len(match.group())):
                    substr = raw_text[i:i+len(match.group())]
                    if substr.lower() == match.group().lower():
                        return substr
                
                return match.group()
        
        return None
    
    def _extract_alcohol_numeric(self, text_lower: str) -> Optional[float]:
        """Extract numeric alcohol content value."""
        for pattern in self.abv_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                abv_str = match.group(1)
                try:
                    # Convert proof to ABV if needed
                    if 'proof' in match.group().lower():
                        return float(abv_str) / 2.0  # Proof = 2 * ABV
                    return float(abv_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_net_contents(self, text_lower: str, raw_text: str) -> Optional[str]:
        """Extract net contents (e.g., '750 mL', '12 fl oz')."""
        for pattern in self.net_contents_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Find in original text preserving case
                for i in range(len(raw_text) - len(match.group())):
                    substr = raw_text[i:i+len(match.group())]
                    if substr.lower() == match.group().lower():
                        return substr
                return match.group()
        
        return None
    
    def _extract_bottler_info(self, lines: List[str], raw_text: str) -> Optional[str]:
        """Extract bottler/producer information."""
        text_lower = raw_text.lower()
        
        # Look for bottler phrases
        for phrase in self.bottler_phrases:
            if phrase in text_lower:
                # Find the line containing this phrase
                for line in lines:
                    if phrase in line.lower():
                        return re.sub(r'\*\*', '', line).strip()
        
        return None
    
    def _extract_country_of_origin(self, text_lower: str, raw_text: str) -> Optional[str]:
        """Extract country of origin."""
        for pattern in self.country_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Find in original text preserving case
                for i in range(len(raw_text) - len(match.group())):
                    substr = raw_text[i:i+len(match.group())]
                    if substr.lower() == match.group().lower():
                        return substr
                return match.group()
        
        return None
    
    def _extract_government_warning(self, raw_text: str) -> Dict[str, Any]:
        """
        Extract and validate government warning.
        
        Returns:
            {
                'present': bool,
                'text': str or None,
                'header_all_caps': bool or None,
                'text_matches': bool or None,
                'similarity_score': float or None
            }
        """
        # Check if warning is present
        if 'government warning' not in raw_text.lower():
            return {
                'present': False,
                'text': None,
                'header_all_caps': None,
                'text_matches': None,
                'similarity_score': None
            }
        
        # Find warning header
        header_match = re.search(r'(GOVERNMENT WARNING:|Government Warning:)', raw_text)
        header_all_caps = None
        if header_match:
            header = header_match.group(1)
            header_all_caps = header == 'GOVERNMENT WARNING:'
        
        # Extract warning text (everything after header)
        warning_start = raw_text.lower().find('government warning')
        if warning_start == -1:
            return {
                'present': True,
                'text': None,
                'header_all_caps': header_all_caps,
                'text_matches': None,
                'similarity_score': None
            }
        
        warning_text = raw_text[warning_start:]
        
        # Check text similarity using fuzzy matching (allow OCR errors)
        # Normalize for comparison (remove extra whitespace, newlines, punctuation variations)
        warning_normalized = ' '.join(warning_text.split())
        expected_normalized = ' '.join(GOVERNMENT_WARNING_TEXT.split())
        
        # Calculate similarity
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, warning_normalized.lower(), expected_normalized.lower()).ratio()
        
        # Consider it a match if similarity >= 85% (allowing for OCR errors)
        text_matches = similarity >= 0.85
        
        return {
            'present': True,
            'text': warning_text,
            'header_all_caps': header_all_caps,
            'text_matches': text_matches,
            'similarity_score': similarity
        }


# Example usage
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 2:
        print("Usage: python label_extractor.py <text_file>")
        print("  Or pipe text: echo 'label text' | python label_extractor.py -")
        sys.exit(1)
    
    if sys.argv[1] == '-':
        raw_text = sys.stdin.read()
    else:
        with open(sys.argv[1], 'r') as f:
            raw_text = f.read()
    
    extractor = LabelExtractor()
    fields = extractor.extract_fields(raw_text)
    
    print(json.dumps(fields, indent=2))

#!/usr/bin/env python3
"""
Sample Label Generator for TTB Label Verification Testing

Generates realistic alcohol beverage labels (JPEG/TIFF) with JSON metadata
for testing the AI-Powered Alcohol Label Verification system.

Usage:
    python gen_samples.py --good 50 --bad 50
    python gen_samples.py --good 100 --bad 0
    python gen_samples.py --seed 42  # optional reproducibility
"""

from PIL import Image, ImageDraw, ImageFont
import random
import json
import argparse
from datetime import datetime
from pathlib import Path
import requests


# ============================================================================
# GOOGLE FONTS DOWNLOADER
# ============================================================================

class GoogleFontDownloader:
    """Download and cache Google Fonts from GitHub repository.
    
    Downloads fonts lazily (on-demand) from the google/fonts GitHub repo
    and caches them locally. Falls back silently to system fonts if download fails.
    """
    
    FONT_CACHE_DIR = Path(__file__).parent / 'fonts'
    GITHUB_RAW_BASE = 'https://github.com/google/fonts/raw/main'
    LICENSE_DIRS = ['ofl', 'apache', 'ufl']  # OFL = Open Font License (most fonts)
    
    def __init__(self):
        """Initialize downloader with connectivity check."""
        self.FONT_CACHE_DIR.mkdir(exist_ok=True)
        self.download_enabled = self._check_connectivity()
        self.failed_downloads = set()  # Don't retry failed downloads in same session
    
    def _check_connectivity(self):
        """Quick connectivity check to GitHub."""
        try:
            requests.head('https://github.com', timeout=2)
            return True
        except:
            return False
    
    def get_font_path(self, family_name, variant='Regular'):
        """Get path to font file, downloading if necessary.
        
        Args:
            family_name: Font family name (e.g., "Playfair Display")
            variant: Font variant (e.g., "Regular", "Bold", "Italic")
        
        Returns:
            str: Path to TTF file, or None if unavailable
        """
        # 1. Check cache first (fastest)
        cached = self._find_in_cache(family_name, variant)
        if cached:
            return cached
        
        # 2. Try to download (if enabled and not previously failed)
        if self.download_enabled and family_name not in self.failed_downloads:
            downloaded = self._download_font(family_name, variant)
            if downloaded:
                return downloaded
            else:
                self.failed_downloads.add(family_name)
        
        # 3. Return None (caller will fallback to system fonts)
        return None
    
    def _find_in_cache(self, family_name, variant):
        """Search local cache for font file."""
        family_dir = self.FONT_CACHE_DIR / self._sanitize_name(family_name)
        if not family_dir.exists():
            return None
        
        # Try different filename patterns Google Fonts might use
        patterns = [
            # Static font files (specific variants)
            f"{family_name.replace(' ', '')}-{variant}.ttf",
            f"{self._sanitize_name(family_name)}-{variant}.ttf",
            f"{family_name.replace(' ', '')}_{variant}.ttf",
            # Variable font files (work for all weights)
            f"{family_name.replace(' ', '')}[wght].ttf",
            f"{self._sanitize_name(family_name)}[wght].ttf",
        ]
        
        for pattern in patterns:
            font_file = family_dir / pattern
            if font_file.exists():
                return str(font_file)
        
        return None
    
    def _download_font(self, family_name, variant):
        """Download font from GitHub google/fonts repository.
        
        Tries each license directory (ofl, apache, ufl) until successful.
        Attempts both static font files and variable fonts.
        """
        family_dir = self.FONT_CACHE_DIR / self._sanitize_name(family_name)
        family_dir.mkdir(exist_ok=True)
        
        # Try each license directory
        for license_dir in self.LICENSE_DIRS:
            # Try 1: Static font file (e.g., PlayfairDisplay-Bold.ttf)
            url = self._build_url(family_name, variant, license_dir, variable=False)
            
            try:
                response = requests.get(url, timeout=10, stream=True)
                if response.status_code == 200:
                    # Save font file with sanitized name
                    filename = f"{family_name.replace(' ', '')}-{variant}.ttf"
                    filepath = family_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    return str(filepath)
            except:
                pass
            
            # Try 2: Variable font file (e.g., PlayfairDisplay[wght].ttf)
            # Variable fonts work for all weights, so we can use them for any variant
            url = self._build_url(family_name, variant, license_dir, variable=True)
            
            try:
                response = requests.get(url, timeout=10, stream=True)
                if response.status_code == 200:
                    # Save variable font with [wght] suffix
                    filename = f"{family_name.replace(' ', '')}[wght].ttf"
                    filepath = family_dir / filename
                    
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    return str(filepath)
            except:
                # Silently continue to next license dir
                continue
        
        # All attempts failed
        return None
    
    def _build_url(self, family_name, variant, license_dir, variable=False):
        """Build GitHub raw URL for font file.
        
        Examples:
          Static: https://github.com/google/fonts/raw/main/ofl/crimsontext/CrimsonText-Bold.ttf
          Variable: https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay[wght].ttf
        """
        # Convert "Playfair Display" -> "playfairdisplay" for directory name
        dir_name = family_name.lower().replace(' ', '')
        
        # Convert "Playfair Display" -> "PlayfairDisplay" for file prefix
        file_prefix = family_name.replace(' ', '')
        
        # Build full URL
        if variable:
            # Variable fonts: FontFamily[wght].ttf
            return f"{self.GITHUB_RAW_BASE}/{license_dir}/{dir_name}/{file_prefix}[wght].ttf"
        else:
            # Static fonts: FontFamily-Variant.ttf
            return f"{self.GITHUB_RAW_BASE}/{license_dir}/{dir_name}/{file_prefix}-{variant}.ttf"
    
    @staticmethod
    def _sanitize_name(name):
        """Sanitize font name for filesystem."""
        return name.replace(' ', '_').replace('-', '_')


# ============================================================================
# CONSTANTS & REFERENCE DATA
# ============================================================================

PRODUCT_TYPES = ['distilled_spirits', 'wine', 'malt_beverage']

BRAND_NAME_PREFIXES = [
    "Old", "New", "Stone", "River", "Mountain", "Valley",
    "Highland", "Coastal", "Heritage", "Legacy", "Craft",
    "Artisan", "Premium", "Golden", "Silver", "Blue",
    "Red", "Black", "White", "Eagle", "Bear", "Wolf",
    "Oak", "Pine", "Cedar", "Maple", "Summit", "Ridge",
    "Creek", "Lake", "Bay", "Harbor"
]

BRAND_NAME_SUFFIXES = [
    "Distillery", "Winery", "Brewing", "Cellars", "Estate",
    "Reserve", "Hills", "Creek", "House", "Brothers",
    "& Co.", "Family", "Craft", "Works", "Company",
    "Valley", "Ridge", "Peak", "Spirits", "Wines"
]

SPIRIT_CLASSES = [
    "Bourbon Whiskey",
    "Kentucky Straight Bourbon Whiskey",
    "Tennessee Whiskey",
    "Rye Whiskey",
    "Straight Rye Whiskey",
    "Vodka",
    "Gin",
    "Rum",
    "Light Rum",
    "Dark Rum",
    "Tequila",
    "Scotch Whisky",
    "Irish Whiskey",
    "Brandy",
    "Cognac"
]

WINE_CLASSES = [
    "Red Wine",
    "White Wine",
    "Chardonnay",
    "Cabernet Sauvignon",
    "Pinot Noir",
    "Merlot",
    "Zinfandel",
    "Sauvignon Blanc",
    "Riesling",
    "Pinot Grigio",
    "Syrah",
    "Malbec",
    "Sparkling Wine",
    "Dessert Wine",
    "Table Wine"
]

BEER_CLASSES = [
    "Beer",
    "Ale",
    "Lager",
    "India Pale Ale",
    "IPA",
    "Stout",
    "Porter",
    "Pilsner",
    "Wheat Beer",
    "Amber Ale",
    "Pale Ale",
    "Hefeweizen"
]

US_CITIES_STATES = [
    ("Louisville", "KY"), ("Napa", "CA"), ("Sonoma", "CA"),
    ("Portland", "OR"), ("Denver", "CO"), ("Austin", "TX"),
    ("Brooklyn", "NY"), ("Seattle", "WA"), ("San Francisco", "CA"),
    ("Boston", "MA"), ("Chicago", "IL"), ("Milwaukee", "WI"),
    ("St. Louis", "MO"), ("Nashville", "TN"), ("Atlanta", "GA"),
    ("Phoenix", "AZ"), ("San Diego", "CA"), ("Philadelphia", "PA"),
    ("Detroit", "MI"), ("Boulder", "CO"), ("Asheville", "NC"),
    ("Burlington", "VT"), ("Eugene", "OR"), ("Santa Fe", "NM"),
    ("Bend", "OR"), ("Paso Robles", "CA"), ("Walla Walla", "WA"),
    ("Willamette", "OR"), ("Lodi", "CA"), ("Healdsburg", "CA")
]

IMPORT_COUNTRIES = [
    "Scotland", "Ireland", "France", "Italy", "Spain",
    "Mexico", "Canada", "Japan", "Germany", "Australia",
    "New Zealand", "Argentina", "Chile", "Portugal"
]

# Standard container sizes
STANDARD_FILLS = {
    'distilled_spirits': [50, 100, 200, 375, 500, 750, 1000, 1750],  # mL
    'wine': [50, 100, 187, 375, 500, 750, 1000, 1500, 3000],  # mL
    'malt_beverage': [8, 12, 16, 22, 32, 40, 64, 128]  # fl oz
}

# Government warning text (27 CFR § 16.21)
GOVERNMENT_WARNING_TEXT = "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."

# Type size requirements (minimums in millimeters)
WARNING_TYPE_SIZE = {
    'small': 1.0,   # <= 237ml (8 fl oz)
    'medium': 2.0,  # 238ml - 3L
    'large': 3.0    # > 3L
}

GENERAL_TYPE_SIZE = {
    'distilled_spirits': {
        'small': 1.0,   # <= 200ml
        'large': 2.0    # > 200ml
    },
    'wine': {
        'small': 1.0,   # <= 187ml
        'large': 2.0    # > 187ml
    },
    'malt_beverage': {
        'small': 1.0,   # <= 0.5 pint (8 fl oz)
        'large': 2.0    # > 0.5 pint
    }
}

# ABV ranges by product type
ABV_RANGES = {
    'wine': (7.0, 24.0),
    'distilled_spirits': (30.0, 60.0),
    'malt_beverage': (3.0, 12.0)
}

# ABV tolerances (27 CFR)
ABV_TOLERANCES = {
    'wine_high': 1.0,      # > 14% ABV
    'wine_low': 1.5,       # <= 14% ABV
    'distilled_spirits': 0.3,
    'malt_beverage': 0.3
}

# Violation types for BAD labels
VIOLATION_TYPES = [
    # Critical - Government Warning
    'missing_warning',
    'warning_not_all_caps',
    'warning_body_bold',
    'wrong_warning_text',
    
    # Critical - Missing Required Fields
    'missing_brand',
    'missing_class_type',
    'missing_abv',
    'missing_net_contents',
    'missing_bottler_info',
    'missing_country_origin',  # for imports
    
    # Critical - Value Mismatches
    'abv_outside_tolerance',
    'wrong_net_contents',
    'brand_name_mismatch',
    
    # Critical - Format Issues
    'type_size_too_small',
    'missing_import_phrase',
]


# ============================================================================
# FIELD RANDOMIZER
# ============================================================================

class FieldRandomizer:
    """Generate random but valid label field values."""
    
    @staticmethod
    def random_product_type():
        """Random product type."""
        return random.choice(PRODUCT_TYPES)
    
    @staticmethod
    def random_container_size(product_type):
        """Random standard container size for product type."""
        return random.choice(STANDARD_FILLS[product_type])
    
    @staticmethod
    def random_brand_name():
        """Generate random brand name (Prefix + Suffix)."""
        prefix = random.choice(BRAND_NAME_PREFIXES)
        suffix = random.choice(BRAND_NAME_SUFFIXES)
        return f"{prefix} {suffix}"
    
    @staticmethod
    def random_class_type(product_type):
        """Random class/type designation for product type."""
        if product_type == 'distilled_spirits':
            return random.choice(SPIRIT_CLASSES)
        elif product_type == 'wine':
            return random.choice(WINE_CLASSES)
        else:  # malt_beverage
            return random.choice(BEER_CLASSES)
    
    @staticmethod
    def random_abv(product_type):
        """Random ABV within range for product type."""
        min_abv, max_abv = ABV_RANGES[product_type]
        return round(random.uniform(min_abv, max_abv), 1)
    
    @staticmethod
    def format_alcohol_content(abv, product_type):
        """Format ABV as label text."""
        formats = [
            f"{abv}% alc./vol.",
            f"{abv}% ABV",
            f"Alcohol {abv}% by volume"
        ]
        return random.choice(formats)
    
    @staticmethod
    def format_net_contents(container_size, product_type):
        """Format net contents as label text."""
        if product_type == 'malt_beverage':
            # US customary units required
            return f"{container_size} fl oz"
        else:
            # Metric for wine/spirits
            if container_size >= 1000:
                liters = container_size / 1000.0
                if liters == int(liters):
                    return f"{int(liters)} L"
                else:
                    return f"{liters} L"
            else:
                return f"{container_size} mL"
    
    @staticmethod
    def random_bottler_info(product_type, is_import):
        """Generate random bottler/importer information."""
        name = FieldRandomizer.random_brand_name()
        city, state = random.choice(US_CITIES_STATES)
        
        if is_import:
            phrase = "Imported by"
            country = random.choice(IMPORT_COUNTRIES)
        else:
            if product_type == 'distilled_spirits':
                phrase = random.choice([
                    "Distilled by", "Bottled by", "Produced by"
                ])
            elif product_type == 'wine':
                phrase = random.choice(["Bottled by", "Packed by"])
            else:  # malt_beverage
                phrase = random.choice([
                    "Brewed by", "Produced by", ""
                ])  # phrase optional for malt
            country = None
        
        return {
            'name': name,
            'city': city,
            'state': state,
            'phrase': phrase,
            'country': country
        }
    
    @staticmethod
    def random_is_import():
        """Randomly decide if product is import (~20% chance)."""
        return random.random() < 0.2
    
    @staticmethod
    def should_include_sulfites(product_type):
        """Random decision to include sulfite disclosure (~50% for wine)."""
        if product_type == 'wine':
            return random.random() < 0.5
        return False


# ============================================================================
# LABEL DATA STRUCTURE
# ============================================================================

class Label:
    """Represents a single alcohol beverage label with all fields."""
    
    def __init__(self, product_type, container_size):
        self.product_type = product_type
        self.container_size = container_size
        self.is_import = False
        
        # Required fields
        self.brand_name = None
        self.class_type = None
        self.alcohol_content = None
        self.alcohol_content_numeric = None
        self.net_contents = None
        self.bottler_info = None
        self.bottler_name = None
        self.bottler_city = None
        self.bottler_state = None
        self.bottler_phrase = None
        self.country_of_origin = None
        
        # Government warning
        self.government_warning = GOVERNMENT_WARNING_TEXT
        self.warning_header_all_caps = True
        self.warning_header_bold = True
        self.warning_body_bold = False
        
        # Optional fields
        self.sulfites = None
        self.other_disclosures = []
        
        # Rendering metadata
        self.background_color = None
        self.text_color = None
        self.canvas_size = None
        
        # Violation flag
        self._type_size_violation = False
    
    def to_dict(self):
        """Convert to dictionary for JSON export."""
        return {
            'product_type': self.product_type,
            'container_size': self.container_size,
            'is_import': self.is_import,
            'brand_name': self.brand_name,
            'class_type': self.class_type,
            'alcohol_content': self.alcohol_content,
            'alcohol_content_numeric': self.alcohol_content_numeric,
            'net_contents': self.net_contents,
            'bottler_info': self.bottler_info,
            'country_of_origin': self.country_of_origin,
            'government_warning': self.government_warning,
            'sulfites': self.sulfites,
            'other_disclosures': self.other_disclosures
        }
    
    def get_required_warning_type_size_mm(self):
        """Get minimum warning type size based on container size."""
        size_ml = self.container_size
        if self.product_type == 'malt_beverage':
            # Convert fl oz to mL
            size_ml = self.container_size * 29.5735
        
        if size_ml <= 237:
            return WARNING_TYPE_SIZE['small']
        elif size_ml <= 3000:
            return WARNING_TYPE_SIZE['medium']
        else:
            return WARNING_TYPE_SIZE['large']
    
    def get_required_general_type_size_mm(self):
        """Get minimum general text type size based on container and product."""
        size_thresholds = GENERAL_TYPE_SIZE[self.product_type]
        
        if self.product_type == 'distilled_spirits':
            threshold_ml = 200
        elif self.product_type == 'wine':
            threshold_ml = 187
        else:  # malt_beverage
            threshold_ml = 8 * 29.5735  # 8 fl oz to mL
        
        size_ml = self.container_size
        if self.product_type == 'malt_beverage':
            size_ml = self.container_size * 29.5735
        
        if size_ml <= threshold_ml:
            return size_thresholds['small']
        else:
            return size_thresholds['large']


# ============================================================================
# VIOLATION GENERATOR
# ============================================================================

class ViolationGenerator:
    """Generate label violations for testing."""
    
    @staticmethod
    def choose_violations(count=None):
        """Choose random violations.
        
        Args:
            count: Number of violations. If None, randomly choose 1 (70%) or 2-3 (30%)
        
        Returns:
            List of violation type strings
        """
        if count is None:
            # 70% single violation, 30% multiple (2-3)
            if random.random() < 0.7:
                count = 1
            else:
                count = random.randint(2, 3)
        
        return random.sample(VIOLATION_TYPES, min(count, len(VIOLATION_TYPES)))
    
    @staticmethod
    def apply_violations(label, violation_types):
        """Apply violations to label.
        
        Args:
            label: Label object to modify
            violation_types: List of violation types to apply
        
        Returns:
            List of violation metadata dicts
        """
        violations = []
        for vtype in violation_types:
            violation_info = ViolationGenerator._apply_single_violation(label, vtype)
            violations.append(violation_info)
        return violations
    
    @staticmethod
    def _apply_single_violation(label, vtype):
        """Apply a single violation and return metadata."""
        
        if vtype == 'missing_warning':
            label.government_warning = None
            return {
                'type': vtype,
                'regulation': '27 CFR § 16.21',
                'description': 'Government warning statement missing'
            }
        
        elif vtype == 'warning_not_all_caps':
            label.warning_header_all_caps = False
            return {
                'type': vtype,
                'regulation': '27 CFR § 16.22(a)(2)',
                'description': 'Warning header not in all capital letters'
            }
        
        elif vtype == 'warning_body_bold':
            label.warning_body_bold = True
            return {
                'type': vtype,
                'regulation': '27 CFR § 16.22(a)(2)',
                'description': 'Warning body text rendered in bold'
            }
        
        elif vtype == 'wrong_warning_text':
            # Modify warning text slightly
            label.government_warning = label.government_warning.replace(
                "According to the Surgeon General",
                "The Surgeon General warns that"
            )
            return {
                'type': vtype,
                'regulation': '27 CFR § 16.21',
                'description': 'Warning text does not match required wording'
            }
        
        elif vtype == 'missing_brand':
            label.brand_name = None
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.64 / § 4.33 / § 7.64',
                'description': 'Brand name missing'
            }
        
        elif vtype == 'missing_class_type':
            label.class_type = None
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.63(a)(2) / § 4.32(a)(2) / § 7.63(a)(2)',
                'description': 'Class/type designation missing'
            }
        
        elif vtype == 'missing_abv':
            label.alcohol_content = None
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.65 / § 4.36 / § 7.65',
                'description': 'Alcohol content missing (when required)'
            }
        
        elif vtype == 'missing_net_contents':
            label.net_contents = None
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.70 / § 4.37 / § 7.70',
                'description': 'Net contents missing'
            }
        
        elif vtype == 'missing_bottler_info':
            label.bottler_info = None
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.66 / § 4.35 / § 7.66',
                'description': 'Bottler/importer information missing'
            }
        
        elif vtype == 'missing_country_origin':
            # Only apply if it's an import
            if label.is_import:
                label.country_of_origin = None
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.66 / § 4.35',
                'description': 'Country of origin missing for import'
            }
        
        elif vtype == 'abv_outside_tolerance':
            # Change ABV to be outside tolerance
            tolerance = ABV_TOLERANCES.get('distilled_spirits', 0.3)
            if label.product_type == 'wine':
                tolerance = ABV_TOLERANCES['wine_high'] if label.alcohol_content_numeric > 14 else ABV_TOLERANCES['wine_low']
            
            # Add tolerance + 0.5% to ensure violation
            new_abv = label.alcohol_content_numeric + tolerance + 0.5
            label.alcohol_content_numeric = new_abv
            label.alcohol_content = f"{new_abv}% alc./vol."
            
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.65(c) / § 4.36(c) / § 7.65(b)',
                'description': f'ABV outside tolerance (off by {tolerance + 0.5}%)'
            }
        
        elif vtype == 'wrong_net_contents':
            # Change to different standard size
            sizes = STANDARD_FILLS[label.product_type]
            different_size = random.choice([s for s in sizes if s != label.container_size])
            label.net_contents = FieldRandomizer.format_net_contents(
                different_size, label.product_type
            )
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.70 / § 4.37 / § 7.70',
                'description': 'Net contents does not match actual container size'
            }
        
        elif vtype == 'brand_name_mismatch':
            # Generate different brand name
            label.brand_name = FieldRandomizer.random_brand_name()
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.64 / § 4.33 / § 7.64',
                'description': 'Brand name does not match application'
            }
        
        elif vtype == 'type_size_too_small':
            # This will be handled in rendering
            label._type_size_violation = True
            return {
                'type': vtype,
                'regulation': '27 CFR § 16.22(b) / § 5.53 / § 4.38(b) / § 7.53',
                'description': 'Type size below regulatory minimum'
            }
        
        elif vtype == 'missing_import_phrase':
            # Only apply if it's an import
            if label.is_import and label.bottler_phrase:
                label.bottler_phrase = ""  # Remove "Imported by"
            return {
                'type': vtype,
                'regulation': '27 CFR § 5.66 / § 4.35 / § 7.66',
                'description': 'Missing "imported by" phrase for import'
            }
        
        else:
            # Unknown violation type
            return {
                'type': vtype,
                'regulation': 'Unknown',
                'description': f'Unknown violation type: {vtype}'
            }


# ============================================================================

# ============================================================================
# LABEL RENDERER (ENHANCED)
# ============================================================================

class LabelRenderer:
    """Render Label object to PIL Image with enhanced visuals."""
    
    DPI = 300
    MM_TO_PX = DPI / 25.4  # ~11.8 pixels per mm
    
    # Font families - Google Fonts (tuples) with system font fallbacks (strings)
    # Format: ('Font Family', 'Variant') for Google Fonts, 'FontName' for system fonts
    
    BRAND_FONTS_DISPLAY = [
        # Google Fonts - Elegant display fonts for wine/spirits
        ('Playfair Display', 'Bold'),
        ('Cinzel', 'Bold'),
        ('Abril Fatface', 'Regular'),
        ('Bebas Neue', 'Regular'),
        ('Righteous', 'Regular'),
        ('Oswald', 'Bold'),
        
        # System fallbacks
        'DejaVuSerif-Bold',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
    ]
    
    BRAND_FONTS_SERIF = [
        # Google Fonts - Traditional serif fonts
        ('Playfair Display', 'Regular'),
        ('Merriweather', 'Bold'),
        ('Lora', 'Bold'),
        ('Crimson Text', 'Bold'),
        ('Libre Baskerville', 'Bold'),
        ('EB Garamond', 'Bold'),
        
        # System fallbacks
        'DejaVuSerif',
        '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',
        'LiberationSerif-Bold',
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
    ]
    
    BRAND_FONTS_SANS = [
        # Google Fonts - Modern sans-serif fonts
        ('Montserrat', 'Bold'),
        ('Open Sans', 'Bold'),
        ('Raleway', 'Bold'),
        ('Source Sans Pro', 'Bold'),
        ('Oswald', 'Bold'),
        ('Roboto', 'Bold'),
        
        # System fallbacks
        'DejaVuSans-Bold',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        'LiberationSans-Bold',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    ]
    
    BRAND_FONTS_SCRIPT = [
        # Google Fonts - Script/handwritten fonts (brand names only)
        ('Parisienne', 'Regular'),
        ('Dancing Script', 'Bold'),
        ('Great Vibes', 'Regular'),
        ('Satisfy', 'Regular'),
        ('Allura', 'Regular'),
        ('Tangerine', 'Bold'),
        
        # No system script font fallbacks (they don't exist)
    ]
    
    BODY_FONTS = [
        # Google Fonts - Clean, readable body text
        ('Open Sans', 'Regular'),
        ('Roboto', 'Regular'),
        ('Lato', 'Regular'),
        ('Montserrat', 'Regular'),
        
        # System fallbacks
        'DejaVuSans',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        'LiberationSans-Regular',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        'FreeSans',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    ]
    
    def __init__(self, label):
        self.label = label
        self.image = None
        self.draw = None
        self.occupied_regions = []  # Track occupied space for collision detection
        self.accent_color = None  # For metallic/color accents
        self.font_downloader = GoogleFontDownloader()  # Initialize font downloader
    
    def render(self):
        """Main rendering pipeline with enhancements."""
        # 1. Create canvas (with potential gradient)
        self.image = self._create_canvas()
        self.draw = ImageDraw.Draw(self.image, 'RGBA')  # RGBA for transparency effects
        
        # 2. Draw background enhancements (textures, gradients)
        self._draw_background_enhancements()
        
        # 3. Draw decorative elements (badges, ornaments, dividers)
        self._draw_decorative_elements()
        
        # 4. Calculate layout with collision detection
        layout = self._calculate_layout_with_spacing()
        
        # 5. Draw all text fields
        self._draw_all_fields(layout)
        
        return self.image
    
    @staticmethod
    def _calculate_luminance(hex_color):
        """Calculate relative luminance for a hex color (0-255 scale).
        
        Uses formula: L = 0.299*R + 0.587*G + 0.114*B
        Returns value 0-255 where >128 is "light" background.
        """
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        # Convert to RGB
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        # Calculate luminance
        return 0.299 * r + 0.587 * g + 0.114 * b
    
    def _create_canvas(self):
        """Create canvas with background color or gradient."""
        # Determine canvas size
        base_sizes = {
            'small': (800, 600),
            'medium': (1200, 900),
            'large': (1600, 1200)
        }
        
        size_ml = self.label.container_size
        if self.label.product_type == 'malt_beverage':
            size_ml = self.label.container_size * 29.5735
        
        if size_ml < 200:
            base_size = base_sizes['small']
        elif size_ml <= 1000:
            base_size = base_sizes['medium']
        else:
            base_size = base_sizes['large']
        
        width = int(base_size[0] * random.uniform(0.9, 1.1))
        height = int(base_size[1] * random.uniform(0.9, 1.1))
        
        self.label.canvas_size = (width, height)
        
        # Expanded background colors - light, mid-tone, and dark
        bg_colors_light = [
            '#F5F5DC', '#FFFACD', '#FFE4B5', '#F0E68C', '#FAFAD2',
            '#FFE4E1', '#F5DEB3', '#FFF8DC', '#FFFFFF', '#E6E6FA',
            '#FFF0F5', '#F0FFF0', '#F5FFFA', '#FDF5E6', '#FFFAF0'
        ]
        bg_colors_mid = [
            '#9DC183', '#D4A5A5', '#E07A5F', '#81B29A', '#8B7D6B',
            '#A8DADC', '#B5838D', '#C9ADA7', '#9A8C98', '#A57548'
        ]
        bg_colors_dark = [
            '#3D0C02', '#1B263B', '#2D4A3E', '#2C2C2C', '#4A1942',
            '#1C1C1C', '#1E3A3A', '#2F2504', '#1A1423', '#3E2723',
            '#0D1B2A', '#1B4332'
        ]
        
        # Choose from all background categories
        all_bg_colors = bg_colors_light + bg_colors_mid + bg_colors_dark
        bg_color = random.choice(all_bg_colors)
        self.label.background_color = bg_color
        
        # Determine text color based on background luminance
        luminance = self._calculate_luminance(bg_color)
        
        if luminance > 128:  # Light background
            # Dark text colors
            text_colors = ['#2C1810', '#000000', '#1A1A1A', '#4A4A4A', '#8B4513', '#2F4F4F']
            self.label.text_color = random.choice(text_colors)
        else:  # Dark background
            # Light text colors
            text_colors = ['#F5F5DC', '#FFFEF2', '#FFD700', '#C0C0C0', '#FFFACD', '#E6E6FA']
            self.label.text_color = random.choice(text_colors)
        
        # Accent colors for decorations (metallic effects) - adapt to background
        if luminance > 128:
            accent_colors = ['#DAA520', '#8B4513', '#B87333', '#8B7355', '#CD7F32']
        else:
            accent_colors = ['#FFD700', '#C0C0C0', '#DEB887', '#F4A460', '#FFA500']
        self.accent_color = random.choice(accent_colors)
        
        return Image.new('RGB', (width, height), bg_color)
    
    def _draw_background_enhancements(self):
        """Draw subtle background enhancements (gradients, textures)."""
        width, height = self.label.canvas_size
        
        # 60% chance of subtle gradient overlay (increased from 40%)
        if random.random() < 0.6:
            # Create subtle radial gradient from center
            for y in range(height):
                for x in range(width):
                    dx = x - width/2
                    dy = y - height/2
                    dist = (dx*dx + dy*dy) ** 0.5
                    max_dist = ((width/2)**2 + (height/2)**2) ** 0.5
                    alpha = int(20 * (dist / max_dist))  # Very subtle
                    if alpha > 0:
                        self.draw.point((x, y), fill=(0, 0, 0, alpha))
        
        # 30% chance of subtle texture (dots pattern)
        if random.random() < 0.3:
            for _ in range(width * height // 5000):  # Sparse dots
                x = random.randint(0, width-1)
                y = random.randint(0, height-1)
                alpha = random.randint(5, 15)
                self.draw.point((x, y), fill=(0, 0, 0, alpha))
    
    def _draw_decorative_elements(self):
        """Draw comprehensive decorative elements."""
        width, height = self.label.canvas_size
        color = self.label.text_color
        
        # 1. Outer border with possible double-line effect (70% chance - increased)
        if random.random() < 0.7:
            border_style = random.choice(['single', 'double', 'ornate'])
            
            if border_style == 'single':
                border_width = random.randint(3, 6)
                margin = 10
                self.draw.rectangle(
                    [(margin, margin), (width - margin, height - margin)],
                    outline=color,
                    width=border_width
                )
            
            elif border_style == 'double':
                # Double border
                outer = 8
                self.draw.rectangle(
                    [(outer, outer), (width - outer, height - outer)],
                    outline=color,
                    width=2
                )
                inner = 14
                self.draw.rectangle(
                    [(inner, inner), (width - inner, height - inner)],
                    outline=color,
                    width=2
                )
            
            elif border_style == 'ornate':
                # Ornate border with corner embellishments
                margin = 10
                self.draw.rectangle(
                    [(margin, margin), (width - margin, height - margin)],
                    outline=self.accent_color,
                    width=4
                )
        
        # 2. Decorative frame (NEW - 30% chance)
        if random.random() < 0.3:
            self._draw_decorative_frame()
        
        # 3. Corner ornaments (70% chance - increased from 50%)
        if random.random() < 0.7:
            self._draw_corner_ornaments()
        
        # 4. Vintage badge/seal (60% chance - increased from 30%)
        if random.random() < 0.6:
            self._draw_vintage_badge(width // 2, int(height * 0.08))
        
        # 5. Seal/medallion (NEW - 40% chance)
        if random.random() < 0.4:
            self._draw_seal_medallion()
        
        # 6. Ornamental dividers (60% chance - increased from 40%)
        if random.random() < 0.6:
            self._draw_ornamental_divider(int(height * 0.38))
        
        # 7. Product-appropriate icon (50% chance - increased from 30%, larger size)
        if random.random() < 0.5:
            self._draw_product_icon()
    
    def _draw_corner_ornaments(self):
        """Draw decorative corner elements."""
        width, height = self.label.canvas_size
        color = self.accent_color
        size = random.randint(25, 40)
        offset = 15
        
        style = random.choice(['simple', 'flourish', 'bracket'])
        
        if style == 'simple':
            # Simple L-shaped corners
            # Top left
            self.draw.line([(offset, offset), (offset + size, offset)], fill=color, width=3)
            self.draw.line([(offset, offset), (offset, offset + size)], fill=color, width=3)
            # Top right
            self.draw.line([(width - offset - size, offset), (width - offset, offset)], fill=color, width=3)
            self.draw.line([(width - offset, offset), (width - offset, offset + size)], fill=color, width=3)
            # Bottom left
            self.draw.line([(offset, height - offset - size), (offset, height - offset)], fill=color, width=3)
            self.draw.line([(offset, height - offset), (offset + size, height - offset)], fill=color, width=3)
            # Bottom right
            self.draw.line([(width - offset - size, height - offset), (width - offset, height - offset)], fill=color, width=3)
            self.draw.line([(width - offset, height - offset - size), (width - offset, height - offset)], fill=color, width=3)
        
        elif style == 'flourish':
            # Curved flourish corners
            for corner_x, corner_y in [(offset, offset), (width-offset, offset), 
                                        (offset, height-offset), (width-offset, height-offset)]:
                # Draw small arc/curve
                self.draw.arc(
                    [(corner_x - size//2, corner_y - size//2), 
                     (corner_x + size//2, corner_y + size//2)],
                    start=0, end=90, fill=color, width=2
                )
        
        elif style == 'bracket':
            # Bracket-style corners
            bracket_len = size
            bracket_width = size // 3
            # Top left
            pts = [(offset, offset + bracket_len), (offset, offset), (offset + bracket_width, offset)]
            self.draw.line(pts, fill=color, width=3, joint='curve')
            # Similar for other corners (abbreviated for brevity)
    
    def _draw_vintage_badge(self, x, y):
        """Draw a vintage circular badge or seal (40% larger)."""
        radius = random.randint(42, 70)  # Increased from 30-50
        color = self.accent_color
        
        style = random.choice(['circle', 'shield', 'star'])
        
        if style == 'circle':
            # Double circle badge
            self.draw.ellipse(
                [(x - radius, y - radius), (x + radius, y + radius)],
                outline=color,
                width=3
            )
            self.draw.ellipse(
                [(x - radius + 5, y - radius + 5), (x + radius - 5, y + radius - 5)],
                outline=color,
                width=2
            )
        
        elif style == 'shield':
            # Shield shape
            pts = [
                (x, y - radius),
                (x + radius*0.6, y - radius*0.3),
                (x + radius*0.6, y + radius*0.5),
                (x, y + radius),
                (x - radius*0.6, y + radius*0.5),
                (x - radius*0.6, y - radius*0.3),
            ]
            self.draw.polygon(pts, outline=color, width=3)
        
        elif style == 'star':
            # 6-point star badge
            import math
            points = []
            for i in range(12):
                angle = i * math.pi / 6
                r = radius if i % 2 == 0 else radius * 0.5
                px = x + r * math.cos(angle - math.pi/2)
                py = y + r * math.sin(angle - math.pi/2)
                points.append((px, py))
            self.draw.polygon(points, outline=color, width=2)
    
    def _draw_ornamental_divider(self, y):
        """Draw ornamental horizontal divider."""
        width = self.label.canvas_size[0]
        color = self.accent_color
        
        style = random.choice(['simple', 'decorated', 'flourish'])
        
        center_x = width // 2
        line_len = int(width * 0.6)
        start_x = center_x - line_len // 2
        end_x = center_x + line_len // 2
        
        if style == 'simple':
            # Simple line with end caps
            self.draw.line([(start_x, y), (end_x, y)], fill=color, width=2)
            # End decorations
            self.draw.ellipse([(start_x-3, y-3), (start_x+3, y+3)], fill=color)
            self.draw.ellipse([(end_x-3, y-3), (end_x+3, y+3)], fill=color)
        
        elif style == 'decorated':
            # Line with center diamond
            self.draw.line([(start_x, y), (center_x - 15, y)], fill=color, width=2)
            self.draw.line([(center_x + 15, y), (end_x, y)], fill=color, width=2)
            # Center diamond
            diamond_pts = [
                (center_x, y - 8),
                (center_x + 8, y),
                (center_x, y + 8),
                (center_x - 8, y)
            ]
            self.draw.polygon(diamond_pts, outline=color, width=2)
        
        elif style == 'flourish':
            # Wavy decorative line
            self.draw.line([(start_x, y), (end_x, y)], fill=color, width=1)
            # Small decorative circles along line
            for i in range(5):
                cx = start_x + (end_x - start_x) * i // 4
                self.draw.ellipse([(cx-2, y-2), (cx+2, y+2)], fill=color)
    
    def _draw_decorative_frame(self):
        """Draw ornate decorative frame around entire label."""
        width, height = self.label.canvas_size
        color = self.accent_color
        margin = 20
        
        # Draw main frame rectangle
        self.draw.rectangle(
            [(margin, margin), (width - margin, height - margin)],
            outline=color,
            width=3
        )
        
        # Add corner flourishes
        corner_size = 30
        corners = [
            (margin, margin),  # Top left
            (width - margin, margin),  # Top right
            (margin, height - margin),  # Bottom left
            (width - margin, height - margin)  # Bottom right
        ]
        
        for i, (cx, cy) in enumerate(corners):
            # Draw small ornamental corner piece
            if i == 0:  # Top left
                pts = [(cx, cy + corner_size), (cx, cy), (cx + corner_size, cy)]
            elif i == 1:  # Top right
                pts = [(cx - corner_size, cy), (cx, cy), (cx, cy + corner_size)]
            elif i == 2:  # Bottom left
                pts = [(cx, cy - corner_size), (cx, cy), (cx + corner_size, cy)]
            else:  # Bottom right
                pts = [(cx - corner_size, cy), (cx, cy), (cx, cy - corner_size)]
            
            self.draw.line(pts, fill=color, width=4, joint='curve')
    
    def _draw_seal_medallion(self):
        """Draw circular seal/medallion with text."""
        import math
        width, height = self.label.canvas_size
        color = self.accent_color
        
        # Position in lower right corner
        x = int(width * 0.15)
        y = int(height * 0.85)
        radius = 45
        
        # Outer circle
        self.draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            outline=color,
            width=3
        )
        
        # Inner circle
        self.draw.ellipse(
            [(x - radius + 8, y - radius + 8), (x + radius - 8, y + radius - 8)],
            outline=color,
            width=2
        )
        
        # Draw small stars or dots around the perimeter (between circles)
        num_stars = 8
        star_radius = radius - 4
        for i in range(num_stars):
            angle = i * (2 * math.pi / num_stars)
            sx = x + star_radius * math.cos(angle)
            sy = y + star_radius * math.sin(angle)
            # Small star shape
            star_size = 3
            self.draw.line(
                [(sx - star_size, sy), (sx + star_size, sy)],
                fill=color, width=2
            )
            self.draw.line(
                [(sx, sy - star_size), (sx, sy + star_size)],
                fill=color, width=2
            )
    
    def _draw_product_icon(self):
        """Draw product-appropriate icon (2x larger than before)."""
        width, height = self.label.canvas_size
        color = self.accent_color
        
        # Position in corner or near product type
        icon_x = int(width * 0.85)
        icon_y = int(height * 0.12)
        size = 50  # Doubled from 25
        
        if self.label.product_type == 'wine':
            # Grape cluster (2x larger)
            for i in range(3):
                for j in range(2):
                    cx = icon_x + i * 16 - 16  # Doubled spacing
                    cy = icon_y + j * 16
                    self.draw.ellipse(
                        [(cx-8, cy-8), (cx+8, cy+8)],  # Doubled radius
                        outline=color,
                        width=3  # Thicker lines
                    )
        
        elif self.label.product_type == 'malt_beverage':
            # Barley/wheat stalks (2x larger)
            for i in range(3):
                x = icon_x + (i - 1) * 16  # Doubled spacing
                self.draw.line([(x, icon_y + size), (x, icon_y)], fill=color, width=3)
                # Grain kernels
                for j in range(4):
                    y = icon_y + j * 12  # Doubled spacing
                    self.draw.ellipse([(x-4, y-4), (x+4, y+4)], fill=color)  # Doubled size
        
        elif self.label.product_type == 'distilled_spirits':
            # Barrel shape (2x larger)
            barrel_w = 40  # Doubled
            barrel_h = 50  # Doubled
            # Barrel outline
            self.draw.arc(
                [(icon_x - barrel_w//2, icon_y), 
                 (icon_x + barrel_w//2, icon_y + barrel_h)],
                start=270, end=450, fill=color, width=2
            )
            # Barrel bands
            for i in [0.3, 0.7]:
                y = icon_y + int(barrel_h * i)
                self.draw.line(
                    [(icon_x - barrel_w//2, y), (icon_x + barrel_w//2, y)],
                    fill=color, width=1
                )
    
    def _calculate_layout_with_spacing(self):
        """Calculate layout positions with collision detection."""
        width, height = self.label.canvas_size
        
        # Reserve regions with minimum spacing
        SPACING = 40  # Minimum pixels between fields
        
        # Calculate positions top to bottom, ensuring no overlap
        current_y = int(height * 0.08)
        
        layout = {}
        
        # Brand name (top)
        brand_height = self._estimate_text_height(6.0)  # 6mm font
        layout['brand'] = (width // 2, current_y + brand_height // 2)
        self.occupied_regions.append((current_y, current_y + brand_height))
        current_y += brand_height + SPACING
        
        # Class/type
        class_height = self._estimate_text_height(4.0)
        layout['class_type'] = (width // 2, current_y + class_height // 2)
        self.occupied_regions.append((current_y, current_y + class_height))
        current_y += class_height + SPACING
        
        # ABV
        abv_height = self._estimate_text_height(3.5)
        layout['abv'] = (width // 2, current_y + abv_height // 2)
        self.occupied_regions.append((current_y, current_y + abv_height))
        current_y += abv_height + int(SPACING * 0.7)
        
        # Net contents
        contents_height = self._estimate_text_height(3.0)
        layout['net_contents'] = (width // 2, current_y + contents_height // 2)
        self.occupied_regions.append((current_y, current_y + contents_height))
        current_y += contents_height + SPACING
        
        # Bottler info
        bottler_height = self._estimate_text_height(2.5) * 2  # May wrap to 2 lines
        layout['bottler'] = (width // 2, current_y + bottler_height // 2)
        self.occupied_regions.append((current_y, current_y + bottler_height))
        current_y += bottler_height + int(SPACING * 0.7)
        
        # Sulfites (if present) - between bottler and warning
        if self.label.sulfites:
            sulfite_height = self._estimate_text_height(2.0)
            layout['sulfites'] = (width // 2, current_y + sulfite_height // 2)
            self.occupied_regions.append((current_y, current_y + sulfite_height))
            current_y += sulfite_height + SPACING
        
        # Government warning - reserve ample space at bottom
        warning_start = max(current_y, int(height * 0.70))
        warning_space = height - warning_start - 20  # 20px bottom margin
        layout['warning'] = (width // 2, warning_start + warning_space // 2)
        
        return layout
    
    def _estimate_text_height(self, font_size_mm):
        """Estimate text height in pixels."""
        return int(font_size_mm * self.MM_TO_PX * 1.4)  # 1.4x for line height
    
    def _draw_all_fields(self, layout):
        """Draw all label text fields with enhanced fonts."""
        # Brand name (display font, bold, large) - can use script fonts
        if self.label.brand_name:
            brand_font_list = random.choice([
                self.BRAND_FONTS_DISPLAY,
                self.BRAND_FONTS_SERIF,
                self.BRAND_FONTS_SANS,
                self.BRAND_FONTS_SCRIPT  # NEW: Script fonts for brand names
            ])
            self._draw_text_centered(
                self.label.brand_name,
                layout['brand'],
                font_size_mm=6.0,
                bold=True,
                font_family_list=brand_font_list
            )
        
        # Class/type (serif or sans)
        if self.label.class_type:
            self._draw_text_centered(
                self.label.class_type,
                layout['class_type'],
                font_size_mm=4.0,
                bold=False,
                font_family_list=self.BRAND_FONTS_SERIF if random.random() < 0.5 else self.BODY_FONTS
            )
        
        # ABV (bold, emphasis)
        if self.label.alcohol_content:
            self._draw_text_centered(
                self.label.alcohol_content,
                layout['abv'],
                font_size_mm=3.5,
                bold=True
            )
        
        # Net contents
        if self.label.net_contents:
            self._draw_text_centered(
                self.label.net_contents,
                layout['net_contents'],
                font_size_mm=3.0,
                bold=False
            )
        
        # Bottler info
        if self.label.bottler_info:
            self._draw_text_centered(
                self.label.bottler_info,
                layout['bottler'],
                font_size_mm=2.5,
                bold=False
            )
        
        # Country of origin
        if self.label.country_of_origin:
            # Position directly below bottler
            country_y = layout['bottler'][1] + self._estimate_text_height(2.5) // 2 + 5
            self._draw_text_centered(
                self.label.country_of_origin,
                (layout['bottler'][0], country_y),
                font_size_mm=2.5,
                bold=False
            )
        
        # Sulfites (if present and in layout)
        if self.label.sulfites and 'sulfites' in layout:
            self._draw_text_centered(
                self.label.sulfites,
                layout['sulfites'],
                font_size_mm=2.0,
                bold=False
            )
        
        # Government warning (special handling)
        if self.label.government_warning:
            self._draw_government_warning(layout['warning'])
    
    def _draw_government_warning(self, position):
        """Draw government warning with proper formatting."""
        # Check for type size violation
        if self.label._type_size_violation:
            min_size = self.label.get_required_warning_type_size_mm()
            font_size_mm = min_size * 0.7
        else:
            font_size_mm = self.label.get_required_warning_type_size_mm()
        
        # Split warning into header and body
        parts = self.label.government_warning.split(': ', 1)
        if len(parts) == 2:
            header = parts[0] + ':'
            body = parts[1]
        else:
            header = self.label.government_warning
            body = ""
        
        # Determine header format
        if not self.label.warning_header_all_caps:
            header = "Government Warning:"
        
        # Calculate position for header (above body with spacing)
        header_y = position[1] - 35
        
        # Draw header
        self._draw_text_centered(
            header,
            (position[0], header_y),
            font_size_mm=font_size_mm,
            bold=self.label.warning_header_bold
        )
        
        # Draw body (wrapped, below header)
        if body:
            body_y = header_y + self._estimate_text_height(font_size_mm) // 2 + 10
            self._draw_text_wrapped(
                body,
                (position[0], body_y),
                font_size_mm=font_size_mm,
                bold=self.label.warning_body_bold,
                max_width=self.label.canvas_size[0] * 0.85
            )
    
    def _draw_text_centered(self, text, position, font_size_mm, bold, font_family_list=None):
        """Draw centered text with font selection."""
        if font_family_list is None:
            font_family_list = self.BODY_FONTS
        
        font = self._get_font(font_size_mm, bold, font_family_list)
        
        # Get text bounding box
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = position[0] - text_width // 2
        y = position[1] - text_height // 2
        
        self.draw.text((x, y), text, fill=self.label.text_color, font=font)
    
    def _draw_text_wrapped(self, text, position, font_size_mm, bold, max_width):
        """Draw text with wrapping."""
        font = self._get_font(font_size_mm, bold, self.BODY_FONTS)
        
        # Word wrapping
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = self.draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate line height
        bbox = self.draw.textbbox((0, 0), "A", font=font)
        line_height = bbox[3] - bbox[1] + 5
        
        # Start position
        start_y = position[1]
        
        # Draw each line
        for i, line in enumerate(lines):
            bbox = self.draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = position[0] - line_width // 2
            y = start_y + i * line_height
            self.draw.text((x, y), line, fill=self.label.text_color, font=font)
    
    def _get_font(self, size_mm, bold, font_family_list=None):
        """Get font with Google Fonts support and system font fallbacks."""
        size_px = int(size_mm * self.MM_TO_PX)
        
        if font_family_list is None:
            font_family_list = self.BODY_FONTS
        
        # Try each font in the list
        for font_spec in font_family_list:
            # Check if it's a Google Font tuple: ('Font Family', 'Variant')
            if isinstance(font_spec, tuple):
                family, variant = font_spec
                font_path = self.font_downloader.get_font_path(family, variant)
                if font_path:
                    try:
                        return ImageFont.truetype(font_path, size_px)
                    except:
                        continue
            
            # Otherwise try as system font name or path (string)
            else:
                try:
                    return ImageFont.truetype(font_spec, size_px)
                except:
                    continue
        
        # Try adding Bold suffix to system fonts if not already there
        if bold:
            for font_spec in font_family_list:
                if isinstance(font_spec, str):  # Only for system fonts
                    for suffix in ['-Bold', ' Bold', 'Bold']:
                        try:
                            return ImageFont.truetype(font_spec + suffix, size_px)
                        except:
                            continue
        
        # Final fallback to default font
        try:
            return ImageFont.load_default()
        except:
            return ImageFont.load_default()


# LABEL GENERATOR
# ============================================================================

class LabelGenerator:
    """Main generator orchestrating label creation."""
    
    def __init__(self):
        self.field_randomizer = FieldRandomizer()
        self.violation_generator = ViolationGenerator()
    
    def generate_good_label(self):
        """Generate compliant label.
        
        Returns:
            (PIL.Image, metadata_dict)
        """
        # 1. Generate random fields
        product_type = FieldRandomizer.random_product_type()
        container_size = FieldRandomizer.random_container_size(product_type)
        
        label = Label(product_type, container_size)
        
        # 2. Populate all required fields
        label.brand_name = FieldRandomizer.random_brand_name()
        label.class_type = FieldRandomizer.random_class_type(product_type)
        
        label.alcohol_content_numeric = FieldRandomizer.random_abv(product_type)
        label.alcohol_content = FieldRandomizer.format_alcohol_content(
            label.alcohol_content_numeric, product_type
        )
        
        label.net_contents = FieldRandomizer.format_net_contents(
            container_size, product_type
        )
        
        label.is_import = FieldRandomizer.random_is_import()
        bottler = FieldRandomizer.random_bottler_info(product_type, label.is_import)
        
        label.bottler_name = bottler['name']
        label.bottler_city = bottler['city']
        label.bottler_state = bottler['state']
        label.bottler_phrase = bottler['phrase']
        label.country_of_origin = bottler['country']
        
        # Format bottler info string
        if label.bottler_phrase:
            label.bottler_info = f"{label.bottler_phrase} {label.bottler_name}, {label.bottler_city}, {label.bottler_state}"
        else:
            label.bottler_info = f"{label.bottler_name}, {label.bottler_city}, {label.bottler_state}"
        
        if label.country_of_origin:
            label.country_of_origin = f"Product of {label.country_of_origin}"
        
        # Optional fields
        if FieldRandomizer.should_include_sulfites(product_type):
            label.sulfites = "Contains Sulfites"
        
        # 3. Render to image
        renderer = LabelRenderer(label)
        image = renderer.render()
        
        # 4. Create metadata
        metadata = self._create_metadata(label, 'GOOD', [])
        
        return image, metadata
    
    def generate_bad_label(self):
        """Generate non-compliant label.
        
        Returns:
            (PIL.Image, metadata_dict)
        """
        # 1. Start with good label
        product_type = FieldRandomizer.random_product_type()
        container_size = FieldRandomizer.random_container_size(product_type)
        
        label = Label(product_type, container_size)
        
        # Populate all fields (same as good label)
        label.brand_name = FieldRandomizer.random_brand_name()
        label.class_type = FieldRandomizer.random_class_type(product_type)
        label.alcohol_content_numeric = FieldRandomizer.random_abv(product_type)
        label.alcohol_content = FieldRandomizer.format_alcohol_content(
            label.alcohol_content_numeric, product_type
        )
        label.net_contents = FieldRandomizer.format_net_contents(
            container_size, product_type
        )
        label.is_import = FieldRandomizer.random_is_import()
        bottler = FieldRandomizer.random_bottler_info(product_type, label.is_import)
        label.bottler_name = bottler['name']
        label.bottler_city = bottler['city']
        label.bottler_state = bottler['state']
        label.bottler_phrase = bottler['phrase']
        label.country_of_origin = bottler['country']
        
        if label.bottler_phrase:
            label.bottler_info = f"{label.bottler_phrase} {label.bottler_name}, {label.bottler_city}, {label.bottler_state}"
        else:
            label.bottler_info = f"{label.bottler_name}, {label.bottler_city}, {label.bottler_state}"
        
        if label.country_of_origin:
            label.country_of_origin = f"Product of {label.country_of_origin}"
        
        if FieldRandomizer.should_include_sulfites(product_type):
            label.sulfites = "Contains Sulfites"
        
        # 2. Apply violations
        violation_types = ViolationGenerator.choose_violations()
        violations = ViolationGenerator.apply_violations(label, violation_types)
        
        # 3. Render to image
        renderer = LabelRenderer(label)
        image = renderer.render()
        
        # 4. Create metadata
        metadata = self._create_metadata(label, 'BAD', violations)
        
        return image, metadata
    
    def _create_metadata(self, label, label_type, violations):
        """Create metadata dictionary."""
        metadata = {
            'generated_at': datetime.now().isoformat(),
            'label_type': label_type,
            'product_type': label.product_type,
            'container_size': label.container_size,
            'is_import': label.is_import,
            'ground_truth': label.to_dict(),
            'label_format': {
                'warning_header_all_caps': label.warning_header_all_caps,
                'warning_header_bold': label.warning_header_bold,
                'warning_body_bold': label.warning_body_bold,
                'canvas_size_px': label.canvas_size,
                'background_color': label.background_color,
                'text_color': label.text_color
            },
            'violations_introduced': violations
        }
        
        # Expected validation
        if label_type == 'GOOD':
            metadata['expected_validation'] = {
                'overall_status': 'COMPLIANT',
                'critical_violations': [],
                'warnings': []
            }
        else:  # BAD
            critical_violations = [
                {
                    'field': v.get('description', '').split()[0].lower(),
                    'issue': v.get('description', ''),
                    'severity': 'CRITICAL'
                }
                for v in violations
            ]
            metadata['expected_validation'] = {
                'overall_status': 'NON_COMPLIANT',
                'critical_violations': critical_violations,
                'warnings': []
            }
        
        return metadata
    
    def save_label(self, image, metadata, filename_base):
        """Save label as JPEG, TIFF, and JSON."""
        # Save JPEG
        jpeg_path = f"{filename_base}.jpg"
        quality = 90
        
        # Ensure < 750 KB
        while True:
            image.save(jpeg_path, 'JPEG', quality=quality)
            size_kb = Path(jpeg_path).stat().st_size / 1024
            
            if size_kb < 750 or quality < 50:
                break
            quality -= 5
        
        # Save TIFF (with compression)
        tiff_path = f"{filename_base}.tif"
        image.save(tiff_path, 'TIFF', compression='tiff_lzw')
        
        # Verify TIFF size
        tiff_size_kb = Path(tiff_path).stat().st_size / 1024
        if tiff_size_kb >= 750:
            # If TIFF still too large, resize image
            scale = 0.9
            while tiff_size_kb >= 750 and scale > 0.5:
                new_size = (int(image.width * scale), int(image.height * scale))
                resized = image.resize(new_size, Image.Resampling.LANCZOS)
                resized.save(tiff_path, 'TIFF', compression='tiff_lzw')
                tiff_size_kb = Path(tiff_path).stat().st_size / 1024
                scale -= 0.1
        
        # Save metadata
        metadata['filename'] = f"{filename_base}.jpg"
        json_path = f"{filename_base}.json"
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def generate_batch(self, good_count, bad_count):
        """Generate batch of labels."""
        print(f"Generating {good_count} GOOD labels and {bad_count} BAD labels...")
        
        # Generate GOOD labels
        for i in range(good_count):
            print(f"  Generating GOOD label {i+1}/{good_count}...", end=' ')
            image, metadata = self.generate_good_label()
            filename = f"label_good_{i+1:03d}"
            self.save_label(image, metadata, filename)
            print("✓")
        
        # Generate BAD labels
        for i in range(bad_count):
            print(f"  Generating BAD label {i+1}/{bad_count}...", end=' ')
            image, metadata = self.generate_bad_label()
            filename = f"label_bad_{i+1:03d}"
            self.save_label(image, metadata, filename)
            print("✓")
        
        print("\nComplete!")
        print(f"Generated {good_count + bad_count} labels total")
        print(f"  - {good_count} GOOD labels")
        print(f"  - {bad_count} BAD labels")
        print(f"  - {(good_count + bad_count) * 3} files total (jpg, tif, json)")


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Generate sample alcohol beverage labels for testing'
    )
    parser.add_argument('--good', type=int, default=0,
                       help='Number of compliant labels to generate')
    parser.add_argument('--bad', type=int, default=0,
                       help='Number of non-compliant labels to generate')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed for reproducibility (optional)')
    
    args = parser.parse_args()
    
    if args.good == 0 and args.bad == 0:
        parser.error("Must specify --good and/or --bad with count > 0")
    
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")
    
    generator = LabelGenerator()
    generator.generate_batch(args.good, args.bad)


if __name__ == '__main__':
    main()

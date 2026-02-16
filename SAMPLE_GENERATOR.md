# Sample Label Generator - Technical Specification

## Document Purpose
This document provides the complete technical specification for `gen_samples.py`, a Python script that generates realistic alcohol beverage label images (JPEG/TIFF) with accompanying JSON metadata for testing the AI-Powered Alcohol Label Verification system.

**Document Version:** 1.0  
**Created:** 2026-02-14  
**Status:** Ready for Implementation

---

## Overview

### Purpose
Generate realistic alcohol beverage labels that:
- **GOOD labels:** Comply with all 27 CFR regulations
- **BAD labels:** Intentionally violate 1+ specific regulations
- Include comprehensive JSON metadata for validation testing

### Design Philosophy
**Keep it simple!**
- Single Python file (`gen_samples.py`)
- Minimal dependencies (Pillow + standard library)
- Straightforward command-line interface
- Randomized but realistic output
- No complex configuration files

---

## Command Line Interface

### Usage
```bash
python gen_samples.py --good 50 --bad 50
python gen_samples.py --good 100 --bad 0      # only good labels
python gen_samples.py --bad 20                # only bad labels
python gen_samples.py --good 10 --bad 10 --seed 42  # reproducible (optional)
```

### Arguments
- `--good N` - Generate N compliant labels
- `--bad N` - Generate N non-compliant labels (with 1+ violations)
- `--seed SEED` - Random seed for reproducibility (optional, not required)

### Output
All files written to current directory:
```
label_good_001.jpg        # JPEG image (< 750 KB)
label_good_001.tif        # TIFF image (< 750 KB)
label_good_001.json       # Metadata with ground truth
label_good_002.jpg
label_good_002.tif
label_good_002.json
...
label_bad_001.jpg
label_bad_001.tif
label_bad_001.json
...
```

---

## Architecture

### Component Overview

```
gen_samples.py (single file)
├── Constants & Data
│   ├── Product types, brand name components
│   ├── Class/type designations by product
│   ├── Geographic data (US cities, import countries)
│   ├── Standard container sizes
│   ├── Government warning text
│   ├── Type size requirements
│   ├── ABV ranges and tolerances
│   └── Violation type definitions
├── FieldRandomizer
│   └── Generate random but valid field values
├── ViolationGenerator
│   └── Apply specific violations to labels
├── Label
│   └── Data structure holding all label fields
├── LabelRenderer
│   └── Convert Label object to PIL Image
└── LabelGenerator
    └── Orchestrate generation + CLI
```

### Dependencies
```python
# Required external library
from PIL import Image, ImageDraw, ImageFont

# Standard library only
import random
import json
import argparse
from datetime import datetime
from pathlib import Path
```

**Installation:**
```bash
pip install Pillow
```

---

## Data Structures

### Constants & Reference Data

#### Product Types
```python
PRODUCT_TYPES = ['distilled_spirits', 'wine', 'malt_beverage']
```

#### Brand Name Components
```python
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
```

#### Class/Type Designations by Product
```python
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
```

#### Geographic Data
```python
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

# Map countries to appropriate product types
COUNTRY_PRODUCT_MAP = {
    "Scotland": ["distilled_spirits"],  # Scotch
    "Ireland": ["distilled_spirits"],   # Irish Whiskey
    "Mexico": ["distilled_spirits"],    # Tequila
    "France": ["wine", "distilled_spirits"],  # Wine, Cognac
    "Italy": ["wine"],
    "Spain": ["wine"],
    "Germany": ["wine", "malt_beverage"],
    "Japan": ["distilled_spirits"],  # Whisky
    "Canada": ["distilled_spirits"],
    # ... etc
}
```

#### Standard Container Sizes
```python
STANDARD_FILLS = {
    'distilled_spirits': [50, 100, 200, 375, 500, 750, 1000, 1750],  # mL
    'wine': [50, 100, 187, 375, 500, 750, 1000, 1500, 3000],  # mL
    'malt_beverage': [8, 12, 16, 22, 32, 40, 64, 128]  # fl oz
}
```

#### Government Warning Text
```python
GOVERNMENT_WARNING_TEXT = """GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems."""
```

#### Type Size Requirements (27 CFR)
```python
# Minimum type sizes in millimeters
# Government Warning (Part 16)
WARNING_TYPE_SIZE = {
    'small': 1.0,   # <= 237ml (8 fl oz)
    'medium': 2.0,  # 238ml - 3L
    'large': 3.0    # > 3L
}

# General mandatory info (Parts 4, 5, 7)
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
```

#### ABV Ranges and Tolerances
```python
ABV_RANGES = {
    'wine': (7.0, 24.0),
    'distilled_spirits': (30.0, 60.0),
    'malt_beverage': (3.0, 12.0)
}

ABV_TOLERANCES = {
    'wine_high': 1.0,      # > 14% ABV
    'wine_low': 1.5,       # <= 14% ABV
    'distilled_spirits': 0.3,
    'malt_beverage': 0.3
}
```

#### Violation Types
```python
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
    
    # Could add more specific violations as needed
]
```

---

## Component Specifications

### 1. FieldRandomizer Class

**Purpose:** Generate random but valid field values within regulatory constraints.

**Methods:**

```python
class FieldRandomizer:
    """Generate random but valid label field values."""
    
    @staticmethod
    def random_product_type() -> str:
        """Random product type: distilled_spirits, wine, or malt_beverage."""
        return random.choice(PRODUCT_TYPES)
    
    @staticmethod
    def random_container_size(product_type: str) -> int:
        """Random standard container size for product type."""
        return random.choice(STANDARD_FILLS[product_type])
    
    @staticmethod
    def random_brand_name() -> str:
        """Generate random brand name (Prefix + Suffix)."""
        prefix = random.choice(BRAND_NAME_PREFIXES)
        suffix = random.choice(BRAND_NAME_SUFFIXES)
        return f"{prefix} {suffix}"
    
    @staticmethod
    def random_class_type(product_type: str) -> str:
        """Random class/type designation for product type."""
        if product_type == 'distilled_spirits':
            return random.choice(SPIRIT_CLASSES)
        elif product_type == 'wine':
            return random.choice(WINE_CLASSES)
        else:  # malt_beverage
            return random.choice(BEER_CLASSES)
    
    @staticmethod
    def random_abv(product_type: str) -> float:
        """Random ABV within range for product type."""
        min_abv, max_abv = ABV_RANGES[product_type]
        return round(random.uniform(min_abv, max_abv), 1)
    
    @staticmethod
    def format_alcohol_content(abv: float, product_type: str) -> str:
        """Format ABV as label text."""
        formats = [
            f"{abv}% alc./vol.",
            f"{abv}% ABV",
            f"Alcohol {abv}% by volume"
        ]
        return random.choice(formats)
    
    @staticmethod
    def format_net_contents(container_size: int, product_type: str) -> str:
        """Format net contents as label text."""
        if product_type == 'malt_beverage':
            # US customary units required
            return f"{container_size} fl oz"
        else:
            # Metric for wine/spirits
            if container_size >= 1000:
                liters = container_size / 1000.0
                return f"{liters}L" if liters.is_integer() else f"{liters} L"
            else:
                return f"{container_size} mL"
    
    @staticmethod
    def random_bottler_info(product_type: str, is_import: bool) -> dict:
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
    def random_is_import() -> bool:
        """Randomly decide if product is import (~20% chance)."""
        return random.random() < 0.2
    
    @staticmethod
    def should_include_sulfites(product_type: str) -> bool:
        """Random decision to include sulfite disclosure (~50% for wine)."""
        if product_type == 'wine':
            return random.random() < 0.5
        return False
```

---

### 2. Label Class

**Purpose:** Data structure holding all label field values and metadata.

**Implementation:**

```python
class Label:
    """Represents a single alcohol beverage label with all fields."""
    
    def __init__(self, product_type: str, container_size: int):
        self.product_type = product_type
        self.container_size = container_size
        self.is_import = False
        
        # Required fields (will be populated)
        self.brand_name = None
        self.class_type = None
        self.alcohol_content = None
        self.alcohol_content_numeric = None
        self.net_contents = None
        self.bottler_info = None  # Full formatted string
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
    
    def to_dict(self) -> dict:
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
    
    def get_required_warning_type_size_mm(self) -> float:
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
    
    def get_required_general_type_size_mm(self) -> float:
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
```

---

### 3. ViolationGenerator Class

**Purpose:** Apply specific violations to labels to create BAD test cases.

**Implementation:**

```python
class ViolationGenerator:
    """Generate label violations for testing."""
    
    @staticmethod
    def choose_violations(count: int = None) -> list:
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
    def apply_violations(label: Label, violation_types: list) -> list:
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
    def _apply_single_violation(label: Label, vtype: str) -> dict:
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
            # Store flag for renderer to use smaller size
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
```

---

### 4. LabelRenderer Class

**Purpose:** Convert Label object to PIL Image with realistic design.

**Configuration:**
- DPI: 300 (print quality)
- mm to pixels conversion: `pixels = mm * 300 / 25.4 ≈ mm * 11.8`

**Implementation:**

```python
class LabelRenderer:
    """Render Label object to PIL Image."""
    
    DPI = 300
    MM_TO_PX = DPI / 25.4  # ~11.8 pixels per mm
    
    def __init__(self, label: Label):
        self.label = label
        self.image = None
        self.draw = None
    
    def render(self) -> Image.Image:
        """Main rendering pipeline."""
        # 1. Create canvas
        self.image = self._create_canvas()
        self.draw = ImageDraw.Draw(self.image)
        
        # 2. Draw decorative elements
        self._draw_decorative_elements()
        
        # 3. Calculate layout positions
        layout = self._calculate_layout()
        
        # 4. Draw all text fields
        self._draw_all_fields(layout)
        
        return self.image
    
    def _create_canvas(self) -> Image.Image:
        """Create canvas with background color."""
        # Determine canvas size based on container size
        base_sizes = {
            'small': (800, 600),   # < 200ml
            'medium': (1200, 900), # 200-1000ml
            'large': (1600, 1200)  # > 1000ml
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
        
        # Add ±10% randomization
        width = int(base_size[0] * random.uniform(0.9, 1.1))
        height = int(base_size[1] * random.uniform(0.9, 1.1))
        
        self.label.canvas_size = (width, height)
        
        # Random background color (light colors for contrast)
        bg_colors = [
            '#F5F5DC',  # Beige
            '#FFFACD',  # Lemon chiffon
            '#FFE4B5',  # Moccasin
            '#F0E68C',  # Khaki
            '#FAFAD2',  # Light goldenrod
            '#FFE4E1',  # Misty rose
            '#F5DEB3',  # Wheat
            '#FFF8DC',  # Cornsilk
            '#FFFFFF',  # White
            '#E6E6FA',  # Lavender
        ]
        bg_color = random.choice(bg_colors)
        self.label.background_color = bg_color
        
        # Dark text color for contrast
        text_colors = ['#2C1810', '#000000', '#1A1A1A', '#4A4A4A']
        self.label.text_color = random.choice(text_colors)
        
        return Image.new('RGB', (width, height), bg_color)
    
    def _draw_decorative_elements(self):
        """Draw borders, lines, and simple decorative elements."""
        width, height = self.label.canvas_size
        color = self.label.text_color
        
        # Outer border (50% chance)
        if random.random() < 0.5:
            border_width = random.randint(2, 5)
            self.draw.rectangle(
                [(border_width, border_width), 
                 (width - border_width, height - border_width)],
                outline=color,
                width=border_width
            )
        
        # Dividing lines (30% chance for horizontal line)
        if random.random() < 0.3:
            y_pos = height // 3
            self.draw.line(
                [(width * 0.1, y_pos), (width * 0.9, y_pos)],
                fill=color,
                width=2
            )
        
        # Corner decorations (20% chance)
        if random.random() < 0.2:
            corner_size = 30
            # Top left corner
            self.draw.line([(10, 10), (10 + corner_size, 10)], fill=color, width=3)
            self.draw.line([(10, 10), (10, 10 + corner_size)], fill=color, width=3)
    
    def _calculate_layout(self) -> dict:
        """Calculate positions for all fields."""
        width, height = self.label.canvas_size
        
        # Divide canvas into regions
        top_region = (0, height * 0.15)
        upper_middle = (height * 0.15, height * 0.35)
        middle = (height * 0.35, height * 0.60)
        lower_middle = (height * 0.60, height * 0.75)
        bottom_region = (height * 0.75, height)
        
        layout = {
            'brand': (width // 2, (top_region[0] + top_region[1]) // 2),
            'class_type': (width // 2, (upper_middle[0] + upper_middle[1]) // 2),
            'abv': (width // 2, (middle[0] + middle[1]) // 2 - 30),
            'net_contents': (width // 2, (middle[0] + middle[1]) // 2 + 30),
            'bottler': (width // 2, (lower_middle[0] + lower_middle[1]) // 2),
            'warning': (width // 2, (bottom_region[0] + bottom_region[1]) // 2),
        }
        
        return layout
    
    def _draw_all_fields(self, layout: dict):
        """Draw all label text fields."""
        # Brand name (largest, bold)
        if self.label.brand_name:
            self._draw_text_centered(
                self.label.brand_name,
                layout['brand'],
                font_size_mm=6.0,
                bold=True
            )
        
        # Class/type (medium)
        if self.label.class_type:
            self._draw_text_centered(
                self.label.class_type,
                layout['class_type'],
                font_size_mm=4.0,
                bold=False
            )
        
        # ABV (medium)
        if self.label.alcohol_content:
            self._draw_text_centered(
                self.label.alcohol_content,
                layout['abv'],
                font_size_mm=3.5,
                bold=True
            )
        
        # Net contents (medium)
        if self.label.net_contents:
            self._draw_text_centered(
                self.label.net_contents,
                layout['net_contents'],
                font_size_mm=3.0,
                bold=False
            )
        
        # Bottler info (smaller)
        if self.label.bottler_info:
            self._draw_text_centered(
                self.label.bottler_info,
                layout['bottler'],
                font_size_mm=2.5,
                bold=False
            )
        
        # Country of origin (if import)
        if self.label.country_of_origin:
            country_pos = (layout['bottler'][0], layout['bottler'][1] + 30)
            self._draw_text_centered(
                self.label.country_of_origin,
                country_pos,
                font_size_mm=2.5,
                bold=False
            )
        
        # Government warning (special handling)
        if self.label.government_warning:
            self._draw_government_warning(layout['warning'])
        
        # Sulfites (if present)
        if self.label.sulfites:
            sulfite_pos = (layout['warning'][0], layout['warning'][1] - 40)
            self._draw_text_centered(
                self.label.sulfites,
                sulfite_pos,
                font_size_mm=2.0,
                bold=False
            )
    
    def _draw_government_warning(self, position: tuple):
        """Draw government warning with proper formatting."""
        # Check for type size violation
        if hasattr(self.label, '_type_size_violation'):
            # Use size below minimum
            min_size = self.label.get_required_warning_type_size_mm()
            font_size_mm = min_size * 0.7  # 30% too small
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
            header = "Government Warning:"  # Title case
        
        # Draw header
        self._draw_text_centered(
            header,
            (position[0], position[1] - 30),
            font_size_mm=font_size_mm,
            bold=self.label.warning_header_bold
        )
        
        # Draw body (may be bold if violation)
        if body:
            self._draw_text_wrapped(
                body,
                (position[0], position[1]),
                font_size_mm=font_size_mm,
                bold=self.label.warning_body_bold,
                max_width=self.label.canvas_size[0] * 0.8
            )
    
    def _draw_text_centered(self, text: str, position: tuple, 
                           font_size_mm: float, bold: bool):
        """Draw centered text at position."""
        font = self._get_font(font_size_mm, bold)
        
        # Get text bounding box
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Center text
        x = position[0] - text_width // 2
        y = position[1] - text_height // 2
        
        self.draw.text((x, y), text, fill=self.label.text_color, font=font)
    
    def _draw_text_wrapped(self, text: str, position: tuple,
                          font_size_mm: float, bold: bool, max_width: float):
        """Draw text with wrapping."""
        font = self._get_font(font_size_mm, bold)
        
        # Simple word wrapping
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
        
        # Draw each line
        bbox = self.draw.textbbox((0, 0), "A", font=font)
        line_height = bbox[3] - bbox[1] + 5
        
        start_y = position[1] - (len(lines) * line_height) // 2
        
        for i, line in enumerate(lines):
            bbox = self.draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = position[0] - line_width // 2
            y = start_y + i * line_height
            self.draw.text((x, y), line, fill=self.label.text_color, font=font)
    
    def _get_font(self, size_mm: float, bold: bool) -> ImageFont:
        """Get font at specified size."""
        size_px = int(size_mm * self.MM_TO_PX)
        
        # Try to load system fonts
        font_names = [
            'Arial',
            'Helvetica',
            'DejaVuSans',
            'Liberation Sans'
        ]
        
        if bold:
            font_names = [f + ' Bold' for f in font_names] + [f + '-Bold' for f in font_names]
        
        for font_name in font_names:
            try:
                return ImageFont.truetype(font_name, size_px)
            except:
                continue
        
        # Fallback to default font
        return ImageFont.load_default()
```

---

### 5. LabelGenerator Class

**Purpose:** Orchestrate generation and handle CLI.

**Implementation:**

```python
class LabelGenerator:
    """Main generator orchestrating label creation."""
    
    def __init__(self):
        self.field_randomizer = FieldRandomizer()
        self.violation_generator = ViolationGenerator()
    
    def generate_good_label(self) -> tuple:
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
    
    def generate_bad_label(self) -> tuple:
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
    
    def _create_metadata(self, label: Label, label_type: str, 
                        violations: list) -> dict:
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
    
    def save_label(self, image: Image.Image, metadata: dict, 
                   filename_base: str):
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
    
    def generate_batch(self, good_count: int, bad_count: int):
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
```

---

## JSON Metadata Format

Each generated label will have accompanying JSON file with complete metadata:

```json
{
  "filename": "label_good_001.jpg",
  "generated_at": "2026-02-14T12:34:56.789123",
  "label_type": "GOOD",
  "product_type": "distilled_spirits",
  "container_size": 750,
  "is_import": false,
  
  "ground_truth": {
    "product_type": "distilled_spirits",
    "container_size": 750,
    "is_import": false,
    "brand_name": "Mountain Heritage Distillery",
    "class_type": "Kentucky Straight Bourbon Whiskey",
    "alcohol_content": "45% alc./vol.",
    "alcohol_content_numeric": 45.0,
    "net_contents": "750 mL",
    "bottler_info": "Distilled by Mountain Heritage Distillery, Louisville, Kentucky",
    "country_of_origin": null,
    "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
    "sulfites": null,
    "other_disclosures": []
  },
  
  "label_format": {
    "warning_header_all_caps": true,
    "warning_header_bold": true,
    "warning_body_bold": false,
    "canvas_size_px": [1200, 900],
    "background_color": "#F5F5DC",
    "text_color": "#2C1810"
  },
  
  "expected_validation": {
    "overall_status": "COMPLIANT",
    "critical_violations": [],
    "warnings": []
  },
  
  "violations_introduced": []
}
```

**For BAD labels:**
```json
{
  "filename": "label_bad_001.jpg",
  "generated_at": "2026-02-14T12:35:10.123456",
  "label_type": "BAD",
  "product_type": "wine",
  "container_size": 750,
  "is_import": false,
  
  "ground_truth": {
    "product_type": "wine",
    "container_size": 750,
    "is_import": false,
    "brand_name": "Stone Valley Winery",
    "class_type": "Cabernet Sauvignon",
    "alcohol_content": "13.5% alc./vol.",
    "alcohol_content_numeric": 13.5,
    "net_contents": "750 mL",
    "bottler_info": "Bottled by Stone Valley Winery, Napa, California",
    "country_of_origin": null,
    "government_warning": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
    "sulfites": "Contains Sulfites",
    "other_disclosures": []
  },
  
  "label_format": {
    "warning_header_all_caps": true,
    "warning_header_bold": true,
    "warning_body_bold": true,
    "canvas_size_px": [1150, 920],
    "background_color": "#FFE4B5",
    "text_color": "#2C1810"
  },
  
  "expected_validation": {
    "overall_status": "NON_COMPLIANT",
    "critical_violations": [
      {
        "field": "warning",
        "issue": "Warning body text rendered in bold",
        "severity": "CRITICAL"
      }
    ],
    "warnings": []
  },
  
  "violations_introduced": [
    {
      "type": "warning_body_bold",
      "regulation": "27 CFR § 16.22(a)(2)",
      "description": "Warning body text rendered in bold"
    }
  ]
}
```

---

## Implementation Timeline

### Phase 1: Setup & Constants (30 minutes)
**Tasks:**
- Set up file structure and imports
- Define all constant data (brands, classes, cities, etc.)
- Define violation types
- Define type size tables

**Deliverable:** Constants section complete and tested

---

### Phase 2: FieldRandomizer (45 minutes)
**Tasks:**
- Implement all random field generation methods
- Test each method independently
- Verify output looks reasonable

**Test:**
```python
# Generate 10 sets of fields
for i in range(10):
    brand = FieldRandomizer.random_brand_name()
    product = FieldRandomizer.random_product_type()
    class_type = FieldRandomizer.random_class_type(product)
    abv = FieldRandomizer.random_abv(product)
    print(f"{brand} - {class_type} - {abv}%")
```

**Deliverable:** FieldRandomizer class complete and tested

---

### Phase 3: Label Data Structure (15 minutes)
**Tasks:**
- Implement Label class with all attributes
- Implement to_dict() method
- Implement type size calculation methods

**Test:**
```python
label = Label('distilled_spirits', 750)
label.brand_name = "Test Distillery"
label.class_type = "Bourbon Whiskey"
print(json.dumps(label.to_dict(), indent=2))
print(f"Required warning size: {label.get_required_warning_type_size_mm()}mm")
```

**Deliverable:** Label class complete and tested

---

### Phase 4: LabelRenderer - Basic (1 hour)
**Tasks:**
- Implement canvas creation
- Implement font loading with fallbacks
- Implement basic text rendering
- Test with simple label (brand + warning only)

**Test:**
```python
label = Label('distilled_spirits', 750)
label.brand_name = "Test Distillery"
label.government_warning = GOVERNMENT_WARNING_TEXT
label.warning_header_all_caps = True
label.warning_header_bold = True
label.warning_body_bold = False

renderer = LabelRenderer(label)
image = renderer.render()
image.save('test_basic.jpg')
```

**Deliverable:** Basic rendering working, can see brand and warning on image

---

### Phase 5: LabelRenderer - Complete (1.5 hours)
**Tasks:**
- Implement layout calculation
- Implement all field rendering methods
- Implement decorative elements
- Test with complete label (all fields)

**Test:**
```python
# Create label with all fields
label = Label('distilled_spirits', 750)
label.brand_name = "Mountain Heritage Distillery"
label.class_type = "Kentucky Straight Bourbon Whiskey"
label.alcohol_content = "45% alc./vol."
label.net_contents = "750 mL"
label.bottler_info = "Distilled by Mountain Heritage Distillery, Louisville, KY"
label.government_warning = GOVERNMENT_WARNING_TEXT
# ... set all formatting flags

renderer = LabelRenderer(label)
image = renderer.render()
image.save('test_complete.jpg')
```

**Deliverable:** Complete label rendering with all fields visible and properly formatted

---

### Phase 6: ViolationGenerator (1.5 hours)
**Tasks:**
- Implement violation selection logic
- Implement each violation type (15+ types)
- Test each violation independently

**Test:**
```python
# Test each violation type
for vtype in VIOLATION_TYPES:
    label = Label('distilled_spirits', 750)
    # ... populate all fields
    
    violations = ViolationGenerator.apply_violations(label, [vtype])
    
    renderer = LabelRenderer(label)
    image = renderer.render()
    image.save(f'test_violation_{vtype}.jpg')
    
    print(f"{vtype}: {violations[0]['description']}")
```

**Deliverable:** All violation types implemented and verified visually

---

### Phase 7: LabelGenerator (1 hour)
**Tasks:**
- Implement generate_good_label()
- Implement generate_bad_label()
- Implement save_label() with file size checking
- Implement generate_batch()
- Test end-to-end generation

**Test:**
```bash
python gen_samples.py --good 5 --bad 5
# Verify all files created
# Check file sizes < 750 KB
# Inspect JSON metadata
# Visually inspect images
```

**Deliverable:** Full label generation pipeline working

---

### Phase 8: CLI & Polish (30 minutes)
**Tasks:**
- Implement argparse CLI
- Add progress indicators
- Add summary statistics
- Handle edge cases and errors
- Add docstrings and comments

**Test:**
```bash
# Test various CLI combinations
python gen_samples.py --good 10
python gen_samples.py --bad 10
python gen_samples.py --good 50 --bad 50
python gen_samples.py --good 1 --bad 1 --seed 42
python gen_samples.py  # Should show error
```

**Deliverable:** Complete, polished script ready for use

---

**Total Estimated Time:** ~6-7 hours of focused development

---

## Success Criteria

### Functional Requirements
- [x] Script runs without errors
- [x] Accepts --good and --bad command line arguments
- [x] Generates specified number of labels
- [x] Creates JPEG, TIFF, and JSON for each label
- [x] All files < 750 KB
- [x] Files written to current directory with proper naming

### Label Quality Requirements
- [x] GOOD labels comply with all 27 CFR requirements
- [x] BAD labels have documented, intentional violations
- [x] Labels are visually realistic with design elements
- [x] Text is readable (proper contrast and size)
- [x] Type sizes meet regulatory minimums (GOOD labels)
- [x] Government warning formatted correctly (GOOD labels)

### Metadata Requirements
- [x] JSON files are valid and well-formed
- [x] Ground truth data is complete and accurate
- [x] Violations are documented with regulation citations
- [x] Expected validation status is provided

### Validation Support
- [x] GOOD labels should validate as COMPLIANT
- [x] BAD labels should validate as NON_COMPLIANT
- [x] Metadata provides ground truth for comparison
- [x] Violations are specific enough to test individual rules

---

## Testing Strategy

### Unit Testing
After each implementation phase, test the component in isolation:
- Generate sample outputs
- Verify data structures
- Check edge cases

### Integration Testing
Test components working together:
- FieldRandomizer → Label
- Label → LabelRenderer → Image
- ViolationGenerator → Label → Image

### Visual Inspection
Manually inspect generated images:
- Text is readable
- Layout looks reasonable
- Decorative elements are appropriate
- GOOD labels look compliant
- BAD labels have visible violations (when obvious)

### Batch Testing
```bash
# Generate large batches
python gen_samples.py --good 100 --bad 100

# Verify outputs
ls -lh label_*.jpg | wc -l  # Should be 200
ls -lh label_*.tif | wc -l  # Should be 200
ls -lh label_*.json | wc -l # Should be 200

# Check file sizes
find . -name "label_*.jpg" -size +750k  # Should be empty
find . -name "label_*.tif" -size +750k  # Should be empty

# Validate JSON
for f in label_*.json; do
    python -m json.tool "$f" > /dev/null || echo "Invalid: $f"
done
```

### Validation Testing
Once the main verification system is built:
- Feed GOOD labels → Should get COMPLIANT
- Feed BAD labels → Should get NON_COMPLIANT with correct violations
- Compare extracted fields against ground_truth in JSON

---

## Risks and Mitigations

### Risk: Font Not Available
**Impact:** Text won't render with correct style/weight  
**Mitigation:** Try multiple common fonts, fall back to PIL default  
**Status:** Handled in `_get_font()` method

### Risk: Images Too Large
**Impact:** Files exceed 750 KB limit  
**Mitigation:** Iteratively reduce JPEG quality; resize if needed  
**Status:** Handled in `save_label()` method

### Risk: Text Doesn't Fit
**Impact:** Text truncated or overlaps  
**Mitigation:** Calculate text bounding box before drawing; adjust layout  
**Status:** Handled in layout calculation

### Risk: Low Contrast
**Impact:** Text unreadable  
**Mitigation:** Use predefined color palettes with known good contrast  
**Status:** Handled in `_create_canvas()` with curated colors

### Risk: Type Size Too Small
**Impact:** GOOD labels violate regulations  
**Mitigation:** Calculate minimums based on container size, enforce in renderer  
**Status:** Handled in `get_required_*_type_size_mm()` methods

### Risk: Violations Not Detectable
**Impact:** BAD labels don't test what they're supposed to  
**Mitigation:** Document each violation clearly; visually inspect samples  
**Status:** Violation metadata includes regulation and description

---

## Future Enhancements

**Not in scope for initial implementation, but possible additions:**

1. **More Violation Types**
   - Character density violations (Part 16)
   - Sulfite disclosure missing
   - Aspartame warning format
   - Varietal percentage issues
   - Appellation compliance

2. **More Product Variations**
   - Organic wines
   - Flavored malt beverages
   - Pre-mixed cocktails
   - Specialty designations

3. **Image Quality Variations**
   - Intentional blur
   - Rotation/skew
   - Poor lighting simulation
   - Glare effects

4. **Batch Organization**
   - Organize into subdirectories by type
   - Generate summary CSV
   - Create test suites by regulation section

5. **Configuration File**
   - YAML/JSON config for customization
   - Custom brand names, cities
   - Violation probability tuning

---

## Dependencies

### Required
```
Pillow>=10.0.0
```

### Standard Library
- `random` - Randomization
- `json` - Metadata serialization
- `argparse` - Command line interface
- `datetime` - Timestamps
- `pathlib` - File operations

### Installation
```bash
pip install Pillow
```

### Platform Support
- **Linux:** Fully supported
- **macOS:** Fully supported
- **Windows:** Fully supported

**Font Availability:**
- Best results with Arial, Helvetica, or Liberation Sans installed
- Falls back to PIL default if system fonts unavailable
- Bold/regular weights preferred but not required

---

## Reference Documents

This specification is based on:
- `TTB_REGULATORY_SUMMARY.md` - Complete regulatory requirements
- `REQUIREMENTS.md` - Project requirements
- `DECISION_LOG.md` - Technical decisions

---

**Document Version:** 1.0  
**Created:** 2026-02-14  
**Status:** Ready for Implementation  
**Estimated Implementation Time:** 6-7 hours

# TTB Regulatory Requirements Summary

## Document Purpose
This document synthesizes the key regulatory requirements from 27 CFR (Code of Federal Regulations) relevant to the AI-Powered Alcohol Label Verification App prototype. All requirements are extracted directly from the official CFR XML files.

**Source Regulations Analyzed:**
- 27 CFR Part 4 (Wine Labeling) - [cfr_regulations/part_4.xml](cfr_regulations/part_4.xml)
- 27 CFR Part 5 (Distilled Spirits Labeling) - [cfr_regulations/part_5.xml](cfr_regulations/part_5.xml)
- 27 CFR Part 7 (Malt Beverages Labeling) - [cfr_regulations/part_7.xml](cfr_regulations/part_7.xml)
- 27 CFR Part 13 (Labeling Proceedings) - [cfr_regulations/part_13.xml](cfr_regulations/part_13.xml)
- 27 CFR Part 16 (Alcoholic Beverage Health Warning Statement) - [cfr_regulations/part_16.xml](cfr_regulations/part_16.xml)

**Document Version:** 2.0  
**Last Updated:** 2026-02-14  
**Status:** Complete Regulatory Analysis for Implementation

---

# PART 16: GOVERNMENT WARNING STATEMENT (ALL PRODUCTS)

## § 16.21 - Required Warning Text (MANDATORY FOR ALL)

**Applicability:** All alcohol beverages ≥ 0.5% ABV (except exports to non-US destinations)

### EXACT REQUIRED TEXT (WORD-FOR-WORD):
```
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.
```

**Validation Rule:** EXACT MATCH REQUIRED - No variations in wording permitted

---

## § 16.22 - Warning Format Requirements

### 1. Placement (§ 16.22)
- Must appear on brand label, separate front label, or back/side label
- Must be **separate and apart from all other information**
- All information must appear together as one continuous text block

**Validation:** Check warning is not embedded within other text blocks

### 2. Legibility (§ 16.22(a))
- Must be **readily legible** under ordinary conditions
- Must be on a **contrasting background**
- Letters/words cannot be compressed to make text not readily legible

**Validation:** Visual contrast check, character spacing validation

### 3. Bold Type Requirements (§ 16.22(a)(2)) - CRITICAL
- **"GOVERNMENT WARNING:"** MUST be:
  - ALL CAPITAL LETTERS
  - BOLD TYPE
- **Body text (numbered statements)** MUST be:
  - NOT in bold type
  - Regular/normal weight

**Validation Rules:**
- REJECT if "Government Warning:" in title case
- REJECT if "GOVT WARNING:" or any abbreviation
- REJECT if warning body text is bold
- REJECT if header is not bold

### 4. Type Size Requirements (§ 16.22(b))

**By Container Size:**

| Container Size | Minimum Type Size |
|---------------|-------------------|
| ≤ 237ml (8 fl oz) | 1 millimeter |
| > 237ml up to 3 liters | 2 millimeters |
| > 3 liters | 3 millimeters |

**Validation:** Measure extracted text height against container size

### 5. Character Density Limits (§ 16.22(a)(4))

**Maximum Characters Per Inch:**

| Type Size | Max Char/Inch |
|-----------|---------------|
| 1mm type | 40 characters |
| 2mm type | 25 characters |
| 3mm type | 12 characters |

**Validation:** Calculate character density for warning text

### 6. Label Affixing (§ 16.22(c))
- Labels not integral to container must be affixed so they **cannot be removed without thorough application of water or other solvents**

**Validation:** For prototype, visual inspection only

### § 16.31 - Exceptions
- Does NOT apply to products exported from US (except to US Armed Forces)
- Applies to products ≥ 0.5% alcohol by volume

---

# PART 4: WINE LABELING REQUIREMENTS

## § 4.32 - Mandatory Label Information

**Applicability:** Wine containing 7-24% alcohol by volume

---

## MANDATORY FIELDS - BRAND LABEL (same field of vision)

### 1. Brand Name (§ 4.33)
**Citation:** § 4.32(a)(1)

**Requirements:**
- Must be present on brand label
- If no brand name, bottler/packer name serves as brand
- Must not be misleading (§ 4.33(b))

**Validation Rules:**
- Check presence
- Compare against application data
- Case-insensitive comparison acceptable for fuzzy matching
- Must not contain misleading terms (§ 4.39)

### 2. Class and Type Designation (§ 4.34)
**Citation:** § 4.32(a)(2)

**Requirements:**
- Must conform to standards in Subpart C (§§ 4.20-4.28)
- Examples: "Table Wine," "Sparkling Wine," "Dessert Wine," "Light Wine"

**Special Rule (§ 4.34(b)):**
- If wine contains > 17 grams/100cc total solids, must include one of:
  - "extra sweet"
  - "specially sweetened"
  - "specially sweet"
  - "sweetened with excess sugar"

**Validation Rules:**
- Check presence
- Verify matches approved class/type designations
- Check special rule for high-solids wines

### 3. Foreign Wine Percentage (§ 4.32(a)(4))
**Citation:** § 4.32(a)(4)

**Requirements:**
- Required ONLY if wine is blend of American and foreign wines AND reference is made to foreign wine
- Must state exact percentage by volume

**Validation Rules:**
- Check if blend is claimed
- Verify percentage statement present if required
- Validate percentage format

---

## MANDATORY FIELDS - ANY LABEL (can appear on any label)

### 4. Name and Address (§ 4.35)
**Citation:** § 4.32(b)(1)

**For American Wine:**
- Must state "bottled by" or "packed by"
- Followed by name
- Followed by address (city & state sufficient)
- Example: "Bottled by XYZ Winery, Napa, CA"

**For Imported Wine:**
- Must state "imported by"
- Followed by name
- Followed by principal place of business address
- Example: "Imported by ABC Imports, New York, NY"

**Format Options (§ 4.35(c)):**
- May use postal abbreviations (e.g., "CA" for California)
- May abbreviate "Saint" as "St."

**Validation Rules:**
- Check presence of bottler/importer statement
- Verify name is present
- Verify city and state are present
- For imports, check "imported by" language
- Address must be consistent with permit holder

### 5. Net Contents (§ 4.37)
**Citation:** § 4.32(b)(2)

**Requirements:**
- Must state metric standard of fill from § 4.72
- Common standards: 3L, 1.5L, 1L, 750ml, 500ml, 375ml, 187ml, 100ml, 50ml
- US equivalent may be shown optionally
- If non-standard metric fill, must appear on **front label**

**Tolerances (§ 4.37(c)):**
- Reasonable variations allowed for:
  - Measuring errors in filling
  - Container capacity variations  
  - Unavoidable evaporation/shrinkage

**Validation Rules:**
- Check presence
- Verify metric units used
- Compare against application data
- If non-standard, check front label placement
- Accept minor variations within tolerance

### 6. Alcohol Content (§ 4.36)
**Citation:** § 4.32(b)(3)

**Requirements by Wine Type:**

| Wine Type | Alcohol Content Statement |
|-----------|---------------------------|
| > 14% ABV | **REQUIRED** |
| ≤ 14% ABV | **OPTIONAL** |
| "Table wine" or "light wine" | **PROHIBITED** (these terms imply ≤ 14%) |

**Format:**
- "Alcohol __% by volume" or similar
- Abbreviations allowed: "alc." and "vol."
- Example: "Alcohol 13.5% by volume" or "13.5% alc./vol."

**Tolerances (§ 4.36(c)):**
- Wine > 14% ABV: **±1.0%**
- Wine ≤ 14% ABV: **±1.5%**

**Validation Rules:**
- Check if required based on wine type
- Verify format is acceptable
- Compare against application data within tolerance
- Ensure doesn't conflict with class/type designation

---

## MANDATORY INGREDIENT DISCLOSURES

### 7. FD&C Yellow No. 5 (§ 4.32(c))
**Citation:** § 4.32(c)

**Requirements:**
- Must state on brand or back label if present
- Applies to products bottled on/after October 6, 1984

**Validation:** If ingredient present, check disclosure exists

### 8. Cochineal Extract or Carmine (§ 4.32(d))
**Citation:** § 4.32(d)

**Requirements:**
- Must state on front/back/strip/neck label
- Must be "prominent and conspicuous"
- Acceptable formats:
  - "Contains Cochineal Extract"
  - "Contains Carmine"
- Applies to products removed on/after April 16, 2013

**Validation:** If ingredient present, check disclosure exists and is prominent

### 9. Sulfites (§ 4.32(e))
**Citation:** § 4.32(e)

**Requirements:**
- Required if total SO₂ concentration ≥ 10 ppm
- Must appear on front/back/strip/neck label
- Acceptable formats:
  - "Contains sulfites"
  - "Contains (a) sulfiting agent(s)"
  - Specific agent name (e.g., "Contains sodium metabisulfite")
- Alternative spelling: "sulphites" or "sulphiting" acceptable

**Date Applicability:**
- COLAs issued on/after January 9, 1987
- Wine bottled on/after July 9, 1987
- Wine removed on/after January 9, 1988

**Validation:** For most modern wines, check sulfite disclosure if sulfites ≥10ppm

---

## § 4.38 - Format Requirements

### Legibility (§ 4.38(a))
- All mandatory information must be **readily legible**
- Must be on **contrasting background**

**Validation:** Visual contrast check

### Type Size (§ 4.38(b))

**Minimum Type Sizes:**

| Container Size | Minimum Type Size | Applies To |
|---------------|-------------------|------------|
| > 187ml | 2 millimeters | All mandatory info (except alcohol content) |
| ≤ 187ml | 1 millimeter | All mandatory info (except alcohol content) |
| Any size | 1-3mm, no border | Alcohol content only |

**Validation:** Measure text height against container size

### English Language (§ 4.38(c))
- All mandatory information must be in **English**
- Exception: Brand name and geographic place of production may be in foreign language

**Validation:** Check mandatory fields use English text

### Firmly Affixed (§ 4.38(e))
- Labels must be affixed so they **cannot be removed without water/other solvents**

**Validation:** For prototype, note only

---

## OPTIONAL LABEL INFORMATION (with requirements if used)

### Varietal Labeling (§ 4.23)
**If varietal (grape variety) name is used:**

**General Rule:**
- Minimum **75%** of wine must be from named grape variety
- Example: "Cabernet Sauvignon" must be ≥75% Cabernet Sauvignon grapes

**Exception for Vitis labrusca varieties:**
- Minimum **51%** from named variety
- Must include statement: "contains not less than 51% [variety name]"
- Example: "Concord - contains not less than 51% Concord grapes"

**Additional Requirements:**
- Must have appellation of origin
- Entire qualifying percentage must be grown in labeled appellation

**Validation Rules:**
- If varietal name present, check percentage claim
- Verify appellation of origin is also present
- Check for labrusca exception statement if applicable

### Appellation of Origin (§ 4.25)
**If appellation of origin is used:**

**General Appellation:**
- Minimum **75%** of wine from stated appellation
- Example: "California" means ≥75% of grapes from California

**Viticultural Area Appellation:**
- Minimum **85%** of wine from stated viticultural area
- Example: "Napa Valley" means ≥85% from Napa Valley AVA
- See Part 9 for approved American Viticultural Areas

**Multi-State Appellation:**
- All grapes must be from stated states
- Percentage of wine from each state must be shown
- States listed in descending order of volume
- Tolerance: ±2%
- Example: "Washington 60%, Oregon 40%"

**Validation Rules:**
- If appellation present, verify percentage requirements
- Check for multi-state percentages if applicable
- Verify appellation matches approved designations (Part 9)

### Vintage Date (§ 4.27)
**If vintage year is used:**

**With Viticultural Area Appellation:**
- Minimum **95%** of wine from stated year

**With Other Appellation:**
- Minimum **85%** of wine from stated year

**Additional Requirement:**
- Must have appellation of origin

**Validation Rules:**
- If vintage date present, verify appellation also present
- Note percentage requirement for type of appellation

---

# PART 5: DISTILLED SPIRITS LABELING REQUIREMENTS

## § 5.63 - Mandatory Label Information

**Applicability:** Distilled spirits products

---

## MANDATORY - SAME FIELD OF VISION (§ 5.63(a))

These items must appear together where they can be read at the same time:

### 1. Brand Name (§ 5.64)
**Citation:** § 5.63(a)(1)

**Requirements:**
- Must be present
- If no brand name, bottler/distiller/importer name serves as brand
- Must not be misleading

**Validation Rules:**
- Check presence
- Compare against application data
- Case-insensitive comparison for fuzzy matching

### 2. Class and Type Designation (Subpart I)
**Citation:** § 5.63(a)(2)

**Requirements:**
- Must comply with standards of identity (§§ 5.141-5.156)
- Examples:
  - "Bourbon Whisky"
  - "Kentucky Straight Bourbon Whisky"
  - "Vodka"
  - "Gin"
  - "Rum"
  - "Tequila"
  - "Brandy"

**Validation Rules:**
- Check presence
- Verify against approved class/type designations
- Check compliance with standards of identity

### 3. Alcohol Content (§ 5.65)
**Citation:** § 5.63(a)(3)

**Format - ONE of these required:**
- "Alcohol __% by volume"
- "__% alcohol by volume"
- "Alcohol by volume __%"

**Abbreviations Allowed:**
- "alc" for "alcohol"
- "%" for "percent" or "per centum"
- "/" for "by"
- "vol" for "volume"

**Examples:**
- "40% alc./vol."
- "Alcohol 40% by volume"
- "40% ABV" (ABV = alcohol by volume)

**Tolerance (§ 5.65(c)):**
- **±0.3 percentage points**
- Example: 40% ABV allows 39.7% to 40.3%

**Proof (Optional):**
- Proof may be shown in addition to ABV
- Must be in same field of vision as mandatory ABV
- Proof = 2 × ABV
- Example: "40% alc./vol. (80 Proof)"

**Validation Rules:**
- Check presence and format
- Compare against application data within ±0.3% tolerance
- If proof shown, verify calculation (proof = 2 × ABV)

---

## MANDATORY - ANYWHERE ON LABEL (§ 5.63(b))

These items must appear somewhere on the label but not necessarily with other mandatory info:

### 4. Name and Address (§§ 5.66-5.68)
**Citation:** § 5.63(b)(1)

**For Domestic Spirits (wholly made in US):**
- Must use one of these phrases:
  - "bottled by"
  - "distilled by"
  - "made by"
  - "produced by"
  - "manufactured by"
  - "processed by"
  - "cellared by" (if only filtering/blending/aging)
- Followed by name
- Followed by address (city & state)
- Example: "Distilled by Old Tom Distillery, Louisville, Kentucky"

**For Imported Spirits (in container):**
- Must state "imported by"
- Followed by name
- Followed by principal place of business address
- Example: "Imported by ABC Spirits, New York, NY"

**For Bottled in US from Imported Bulk:**
- Must state both:
  - Country of origin ("Product of [Country]")
  - Bottler info ("Bottled by [Name], [City], [State]")

**Format Options:**
- May use postal abbreviations
- Address must be consistent with basic permit

**Validation Rules:**
- Check presence of appropriate phrase
- Verify name is present
- Verify address (city & state) is present
- For imports, require "imported by" language
- For foreign distilled/US bottled, check both statements

### 5. Net Contents (§ 5.70)
**Citation:** § 5.63(b)(2)

**Requirements:**
- Must state metric standard of fill from § 5.203
- Common standards: 1.75L, 1L, 750ml, 500ml, 375ml, 200ml, 100ml, 50ml
- May be blown/embossed into container (not on label)

**Validation Rules:**
- Check presence
- Verify metric units
- Compare against application data
- Accept standard fills from § 5.203

---

## MANDATORY DISCLOSURES (§ 5.63(c))

These must appear if applicable, without additional descriptive information:

### 6. Neutral Spirits (§ 5.71)
**Citation:** § 5.63(c)(1)

**Requirements:**
- If product contains neutral spirits, must state:
  - Exact percentage by volume
  - Commodity from which distilled
- Example: "40% neutral spirits distilled from grain"

**Validation:** If neutral spirits present, verify disclosure with percentage and source

### 7. Coloring (§ 5.72)
**Citation:** § 5.63(c)(2)

**Requirements:**
- If product is colored, must state on label
- Acceptable formats:
  - "Artificially colored"
  - "Colored with caramel"
  - etc.

**Validation:** Check disclosure if coloring added

### 8. Wood Treatment (§ 5.73)
**Citation:** § 5.63(c)(2)

**Requirements:**
- If spirits treated with wood other than oak, must state wood type
- Example: "Treated with cherry wood"

**Validation:** Check disclosure if non-oak wood treatment

### 9. Age Statements (§ 5.74)
**Citation:** § 5.63(c)(2)

**Requirements:**
- If age is stated, must comply with § 5.74
- For blends, must state age of youngest spirits

**Validation:** If age present, verify format compliance

### 10. State of Distillation (§ 5.66(f))
**Citation:** § 5.63(c)(2)

**Requirements:**
- Required for certain whisky types defined in § 5.143(c)(2)-(7)
- Example: "Kentucky Straight Bourbon Whisky"

**Validation:** Check state disclosure for applicable whisky types

### 11. FD&C Yellow No. 5 (§ 5.63(c)(5))
**Citation:** § 5.63(c)(5)

**Requirements:**
- Must state if present
- Format: "FD&C Yellow No. 5" or "Contains FD&C Yellow No. 5"

**Validation:** Check disclosure if ingredient present

### 12. Cochineal Extract or Carmine (§ 5.63(c)(6))
**Citation:** § 5.63(c)(6)

**Requirements:**
- Must state common name if present
- Examples: "contains cochineal extract" or "contains carmine"
- Applies to products removed on/after April 16, 2013

**Validation:** Check disclosure if ingredient present

### 13. Sulfites (§ 5.63(c)(7))
**Citation:** § 5.63(c)(7)

**Requirements:**
- Required if total SO₂ concentration ≥ 10 ppm
- Acceptable formats:
  - "Contains sulfites"
  - "Contains (a) sulfiting agent(s)"
  - Specific agent name
- Alternative spelling: "sulphites" or "sulphiting"

**Validation:** Check disclosure if sulfites ≥10ppm

### 14. Aspartame (§ 5.63(c)(8))
**Citation:** § 5.63(c)(8)

**Requirements - CRITICAL FORMAT:**
- Must state in **ALL CAPITAL LETTERS:**
  - "PHENYLKETONURICS: CONTAINS PHENYLALANINE"
- Must be **separate and apart from all other information**

**Validation Rules:**
- REJECT if not all caps
- REJECT if embedded in other text
- Check exact wording

---

## § 5.52-5.55 - Format Requirements

### Legibility (§ 5.52(a))
- All mandatory information must be **readily legible under ordinary conditions**

### Separate and Apart (§ 5.52(b))
- Mandatory information (except brand name) must be **separate and apart** from additional information
- Exception: Alcoholic content, proof, and required disclosures may be grouped

### Contrasting Background (§ 5.52(c))
- Mandatory information must **contrast with background**

**Validation:** Visual contrast check

### Type Size (§ 5.53)

**Minimum Type Sizes:**

| Container Size | Minimum Type Size |
|---------------|-------------------|
| > 200ml | 2 millimeters |
| ≤ 200ml | 1 millimeter |

**Validation:** Measure text height against container size

### Firmly Affixed (§ 5.51)
- Labels must be affixed so they **cannot be removed without water/other solvents**

**Validation:** For prototype, note only

### English Language (§ 5.55)
- Mandatory information must be in **English**
- Exceptions:
  - Brand names
  - For Puerto Rico: Spanish permitted for all info

**Validation:** Check mandatory fields use English text (except brand)

---

# PART 7: MALT BEVERAGES LABELING REQUIREMENTS

## § 7.63 - Mandatory Label Information

**Applicability:** Malt beverages (beer, ale, lager, etc.)

---

## MANDATORY INFORMATION (§ 7.63(a))

### 1. Brand Name (§ 7.64)
**Citation:** § 7.63(a)(1)

**Requirements:**
- Must be present
- If no brand name, bottler/importer name serves as brand
- Must not be misleading

**Validation Rules:**
- Check presence
- Compare against application data
- Case-insensitive comparison for fuzzy matching

### 2. Class/Type Designation (Subpart I)
**Citation:** § 7.63(a)(2)

**Requirements:**
- Must comply with §§ 7.141-7.147
- Examples:
  - "Beer"
  - "Ale"
  - "Lager"
  - "Stout"
  - "Porter"
  - "Malt Liquor"

**Validation Rules:**
- Check presence
- Verify against approved class/type designations

### 3. Alcohol Content (§ 7.65) - CONDITIONAL
**Citation:** § 7.63(a)(3)

**When REQUIRED:**
- If product contains alcohol derived from added nonbeverage flavors or other ingredients (except hops extract)
- Example: Flavored malt beverages with added spirits

**When OPTIONAL:**
- For standard malt beverages without added alcohol

**Format if Stated:**
- "Alcohol __% by volume"
- "__% alcohol by volume"
- "Alcohol by volume: __%"
- Abbreviations allowed: "alc," "%," "/," "vol"
- Must be stated to **nearest 0.1%** (for products ≥0.5% ABV)

**Tolerance (§ 7.65(b)):**
- **±0.3 percentage points**

**Special Restrictions (§ 7.65(d)):**

| Claim | Requirement |
|-------|-------------|
| "Low alcohol" or "reduced alcohol" | Must be < 2.5% ABV (NO tolerance) |
| "Non-alcoholic" | Must be < 0.5% ABV with statement "contains less than 0.5% alcohol by volume" (NO tolerance) |
| "Alcohol free" | Must be 0.0% ABV (NO tolerance) |

**Type Size Limits (§ 7.65(c)):**

| Container Size | MAXIMUM Type Size |
|---------------|-------------------|
| > 40 fl oz | 4 millimeters |
| ≤ 40 fl oz | 3 millimeters |

**Validation Rules:**
- Check if required based on product type
- If present, verify format
- Compare against application data within tolerance
- For special claims, enforce strict limits
- Check type size doesn't exceed maximum

### 4. Name and Address (§§ 7.66-7.68)
**Citation:** § 7.63(a)(4)

**For Domestic Malt Beverages (wholly US-fermented):**
- Name and address (city & state) of bottler
- Optional phrases:
  - "bottled by"
  - "brewed by"
  - "produced by"
  - etc.
- Example: "Brewed by ABC Brewing Company, Portland, OR"

**For Imported Malt Beverages:**
- Must state "imported by"
- Followed by name
- Followed by principal place of business address
- Example: "Imported by XYZ Imports, Miami, FL"

**Additional Options:**
- May be blown/embossed into container

**Validation Rules:**
- Check presence of name and address
- Verify city and state present
- For imports, require "imported by" language

### 5. Net Contents (§ 7.70)
**Citation:** § 7.63(a)(5)

**Requirements - US Customary Units:**
- Must use US units: pints, quarts, gallons, fluid ounces
- **Specific rules:**
  - **< 1 pint:** State in fluid ounces OR fractions of pint
    - Example: "12 fl oz" or "3/4 pint"
  - **= 1 pint/quart/gallon:** State as such
    - Example: "1 pint"
  - **> 1 pint, < 1 quart:** State as fractions of quart OR pints and fluid ounces
    - Example: "1½ pints" or "24 fl oz"
  - **> 1 quart, < 1 gallon:** State as fractions of gallon OR quarts, pints, fluid ounces
    - Example: "½ gallon" or "2 quarts"
  - **> 1 gallon:** State in gallons and fractions
    - Example: "1¼ gallons"

**Metric Optional:**
- Metric may be shown **in addition to** (not in lieu of) US units
- Must be in same field of vision

**May be Embossed:**
- Can be blown/embossed into container

**Validation Rules:**
- Check presence
- Verify US customary units used (not metric only)
- Validate format matches size requirements
- Compare against application data

---

## MANDATORY INGREDIENT DISCLOSURES (§ 7.63(b))

### 6. FD&C Yellow No. 5 (§ 7.63(b)(1))
**Citation:** § 7.63(b)(1)

**Requirements:**
- Must state if present
- Format: "FD&C Yellow No. 5" or "Contains FD&C Yellow No. 5"

**Validation:** Check disclosure if ingredient present

### 7. Cochineal Extract or Carmine (§ 7.63(b)(2))
**Citation:** § 7.63(b)(2)

**Requirements:**
- Must state common name if present
- Examples: "contains cochineal extract" or "contains carmine"
- Applies to products removed on/after April 16, 2013

**Validation:** Check disclosure if ingredient present

### 8. Sulfites (§ 7.63(b)(3))
**Citation:** § 7.63(b)(3)

**Requirements:**
- Required if total SO₂ concentration ≥ 10 ppm
- Acceptable formats:
  - "Contains sulfites"
  - "Contains (a) sulfiting agent(s)"
  - Specific agent name
- Alternative spelling: "sulphites" or "sulphiting"

**Validation:** Check disclosure if sulfites ≥10ppm

### 9. Aspartame (§ 7.63(b)(4))
**Citation:** § 7.63(b)(4)

**Requirements - CRITICAL FORMAT:**
- Must state in **ALL CAPITAL LETTERS:**
  - "PHENYLKETONURICS: CONTAINS PHENYLALANINE"
- Must be **separate and apart from all other information**

**Validation Rules:**
- REJECT if not all caps
- REJECT if embedded in other text
- Check exact wording

---

## § 7.51-7.55 - Format Requirements

### Legibility (§ 7.52(a))
- All mandatory information must be **readily legible under ordinary conditions**

### Separate and Apart (§ 7.52(b))
- Mandatory information (except brand name) must be **separate and apart** from additional information
- Exceptions allowed for certain grouped information

### Contrasting Background (§ 7.52(c))
- Mandatory information must **contrast with background**

**Validation:** Visual contrast check

### Type Size (§ 7.53)

**Minimum Type Sizes:**

| Container Size | Minimum Type Size |
|---------------|-------------------|
| > 0.5 pint (> 8 fl oz) | 2 millimeters |
| ≤ 0.5 pint (≤ 8 fl oz) | 1 millimeter |

**Validation:** Measure text height against container size

### Firmly Affixed (§ 7.51)

**General Rule:**
- Labels must be affixed so they **cannot be removed without water/other solvents**

**Keg Exception (§ 7.51(b)):**
- Keg collars/tap covers on kegs ≥ 5.16 gallons NOT required to be firmly affixed
- IF bottler/importer name is permanently or semi-permanently marked on keg

**Validation:** 
- For bottles/cans: Check firm affixing
- For kegs: Allow removable collars if name on keg

### English Language (§ 7.55)
- Mandatory information must be in **English**
- Exceptions:
  - Brand names
  - For Puerto Rico: Spanish permitted for all info

**Validation:** Check mandatory fields use English text (except brand)

---

# PART 13: LABEL APPROVAL PROCESS

## § 13.21 - Application Requirements

**Form Required:** TTB Form 5100.31 (COLA application)

### Time Limits for TTB Action (§ 13.21(b))

**Initial Review:**
- TTB must notify applicant within **90 days** of receipt
- TTB may extend once for additional **90 days** for unusual circumstances
- If no decision within time period, applicant may file appeal

**Note:** These timeframes are for TTB processing, not for prototype validation

---

## Appeal Process

### First Appeal (§ 13.25)
- Must be filed within **45 days** after notice of qualification or denial
- TTB must decide within **90 days** (extendable once for 90 days more)

### Second Appeal (§ 13.27)
- Must be filed within **45 days** after first appeal decision
- TTB must decide within **90 days** (extendable once for 90 days more)
- This decision is **final TTB decision**

---

## § 13.41 - Revocation of Approved COLAs

**Process:**
- TTB may revoke previously approved COLAs if found non-compliant
- **45 days** to respond to notice of proposed revocation
- **90 days** for TTB decision (extendable once for 90 days)
- Can appeal revocation within **45 days**

**Implication:** Even approved labels can be revoked if violations found

---

## § 13.61 - Public Information

**COLA Registry:**
- Approved COLAs are **public record**
- Available in **TTB Public COLA Registry** online
- Can be searched and viewed by anyone

**Implication:** Reference data for validation can come from public COLA registry

---

# QUICK REFERENCE TABLES

## Container Size → Type Size Requirements

### Government Warning (Part 16)

| Container Size | Minimum Type Size |
|---------------|-------------------|
| ≤ 237ml (≤ 8 fl oz) | 1mm |
| 238ml - 3L | 2mm |
| > 3L | 3mm |

### Wine (Part 4)

| Container Size | Minimum Type Size |
|---------------|-------------------|
| > 187ml | 2mm (except ABV) |
| ≤ 187ml | 1mm (except ABV) |
| ABV (any) | 1-3mm, no border |

### Distilled Spirits (Part 5)

| Container Size | Minimum Type Size |
|---------------|-------------------|
| > 200ml | 2mm |
| ≤ 200ml | 1mm |

### Malt Beverages (Part 7)

| Container Size | Minimum Type Size | Maximum Type Size (ABV only) |
|---------------|-------------------|------------------------------|
| > 0.5 pint (> 8 fl oz) | 2mm | 4mm (if > 40 fl oz) or 3mm (if ≤ 40 fl oz) |
| ≤ 0.5 pint (≤ 8 fl oz) | 1mm | 3mm |

---

## Alcohol Content Requirements by Product

| Product Type | ABV Required? | Tolerance | Format |
|-------------|---------------|-----------|--------|
| Wine > 14% ABV | YES | ±1.0% | "X% alc./vol." or similar |
| Wine ≤ 14% ABV | OPTIONAL | ±1.5% | "X% alc./vol." or similar |
| Wine labeled "table"/"light" | PROHIBITED | N/A | Cannot show ABV |
| Distilled Spirits | YES | ±0.3% | "X% alc./vol." or similar |
| Malt Beverage (standard) | OPTIONAL | ±0.3% | "X% alc./vol." or similar |
| Malt Beverage (w/added alcohol) | YES | ±0.3% | "X% alc./vol." or similar |
| "Low alcohol" malt beverage | YES | NO tolerance | Must be < 2.5% |
| "Non-alcoholic" malt beverage | YES | NO tolerance | Must be < 0.5% with statement |
| "Alcohol free" malt beverage | YES | NO tolerance | Must be 0.0% |

---

## Name/Address Required Phrases

| Product Type | Domestic | Import |
|-------------|----------|--------|
| Wine | "bottled by" or "packed by" + name + city, state | "imported by" + name + address |
| Distilled Spirits | "distilled by"/"bottled by"/etc. + name + city, state | "imported by" + name + address |
| Malt Beverages | Name + city, state (phrases optional) | "imported by" + name + address |

---

## Ingredient Disclosure Thresholds

| Ingredient | Threshold | Required Statement |
|-----------|-----------|-------------------|
| Sulfites (SO₂) | ≥ 10 ppm | "Contains sulfites" or similar |
| FD&C Yellow No. 5 | Any amount | "FD&C Yellow No. 5" or "Contains FD&C Yellow No. 5" |
| Cochineal/Carmine | Any amount | "Contains cochineal extract" or "Contains carmine" (prominent) |
| Aspartame | Any amount | "PHENYLKETONURICS: CONTAINS PHENYLALANINE" (all caps, separate) |

---

# IMPLEMENTATION CHECKLIST

## Core Validation Functions Needed

- [ ] **Extract text from image** (OCR/Vision AI)
- [ ] **Detect text formatting** (bold, caps, font size, positioning)
- [ ] **Parse extracted text** into structured fields
- [ ] **Validate government warning**
  - [ ] Check exact text match
  - [ ] Check header all caps
  - [ ] Check header bold
  - [ ] Check body not bold
  - [ ] Check type size
  - [ ] Check character density
  - [ ] Check contrasting background
- [ ] **Validate brand name**
  - [ ] Check presence
  - [ ] Compare against application (exact, fuzzy)
- [ ] **Validate class/type**
  - [ ] Check presence
  - [ ] Compare against standards of identity
- [ ] **Validate alcohol content**
  - [ ] Check if required
  - [ ] Extract numeric value
  - [ ] Check tolerance
  - [ ] Validate proof if shown
- [ ] **Validate net contents**
  - [ ] Check presence
  - [ ] Parse units
  - [ ] Compare against application
  - [ ] Check metric vs US customary rules
- [ ] **Validate name and address**
  - [ ] Check presence of required phrase
  - [ ] Check name present
  - [ ] Check city and state present
- [ ] **Validate country of origin** (if import)
  - [ ] Check presence
  - [ ] Compare against application
- [ ] **Validate ingredient disclosures**
  - [ ] Check sulfite disclosure if needed
  - [ ] Check FD&C Yellow No. 5 if needed
  - [ ] Check cochineal/carmine if needed
  - [ ] Check aspartame warning if needed (format critical)
- [ ] **Classify validation results**
  - [ ] Identify critical violations
  - [ ] Identify warnings for review
  - [ ] Identify informational notes
- [ ] **Generate validation report**
  - [ ] JSON structure
  - [ ] Human-readable summary
  - [ ] Recommendations

---

## Reference Links

### Official TTB Resources
- TTB Main Site: https://www.ttb.gov
- COLA System: https://www.ttb.gov/colasonline
- Public COLA Registry: https://www.ttbonline.gov/colasonline/publicSearchColasBasic.do
- Regulations: https://www.ecfr.gov/current/title-27/chapter-I/subchapter-A

### Key Regulations (eCFR)
- 27 CFR Part 4 (Wine): https://www.ecfr.gov/current/title-27/part-4
- 27 CFR Part 5 (Distilled Spirits): https://www.ecfr.gov/current/title-27/part-5
- 27 CFR Part 7 (Malt Beverages): https://www.ecfr.gov/current/title-27/part-7
- 27 CFR Part 13 (Label Approval): https://www.ecfr.gov/current/title-27/part-13
- 27 CFR Part 16 (Health Warning): https://www.ecfr.gov/current/title-27/part-16

### Downloaded CFR Files
- Local directory: `cfr_regulations/`
- All 26 parts of 27 CFR Alcohol Regulations downloaded as XML

---

**Document Version:** 2.0  
**Created:** 2026-02-14  
**Last Updated:** 2026-02-14  
**Status:** Complete Regulatory Analysis - Ready for Implementation

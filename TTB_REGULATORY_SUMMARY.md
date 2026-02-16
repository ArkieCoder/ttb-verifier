# TTB Regulatory Requirements Summary

## Document Purpose
This document synthesizes the key regulatory requirements from 27 CFR (Code of Federal Regulations) relevant to the AI-Powered Alcohol Label Verification App prototype. All requirements are extracted directly from the official CFR XML files.

**Source Regulations Analyzed:**
- 27 CFR Part 4 (Wine Labeling)
- 27 CFR Part 5 (Distilled Spirits Labeling)
- 27 CFR Part 7 (Malt Beverages Labeling)
- 27 CFR Part 13 (Labeling Proceedings)
- 27 CFR Part 16 (Alcoholic Beverage Health Warning Statement)

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

# VALIDATION IMPLEMENTATION GUIDE

## Exact Match Requirements (Zero Tolerance)

**These fields require word-for-word matching:**

1. **Government Warning Text (Part 16)**
   - Exact wording required
   - No variations permitted

2. **Aspartame Warning (Parts 4, 5, 7)**
   - Must be exactly: "PHENYLKETONURICS: CONTAINS PHENYLALANINE"
   - All caps required

**Implementation:**
```python
# Pseudo-code
def validate_warning_text(extracted_text, required_text):
    # Remove extra whitespace but preserve line breaks
    extracted_clean = normalize_whitespace(extracted_text)
    required_clean = normalize_whitespace(required_text)
    
    if extracted_clean == required_clean:
        return PASS
    else:
        return FAIL
```

---

## Format Validation Requirements

**These fields require format/style checking:**

1. **Warning Header Formatting (Part 16)**
   - "GOVERNMENT WARNING:" must be ALL CAPS
   - "GOVERNMENT WARNING:" must be BOLD
   - Body text must NOT be bold

2. **Aspartame Warning (Parts 4, 5, 7)**
   - Must be ALL CAPS
   - Must be separate and apart from other text

3. **Type Size Minimums**
   - Varies by product type and container size
   - See tables above for specific requirements

4. **Contrasting Background**
   - All mandatory information
   - Visual/programmatic contrast check needed

**Implementation:**
```python
# Pseudo-code
def validate_warning_format(extracted_data):
    issues = []
    
    # Check header capitalization
    if not extracted_data.header.isupper():
        issues.append("Header not all caps")
    
    # Check header bold
    if not extracted_data.header_is_bold:
        issues.append("Header not bold")
    
    # Check body not bold
    if extracted_data.body_is_bold:
        issues.append("Body text is bold")
    
    return issues
```

---

## Numeric Validation with Tolerances

**Alcohol Content Tolerances:**

| Product Type | Tolerance |
|-------------|-----------|
| Wine > 14% ABV | ±1.0% |
| Wine ≤ 14% ABV | ±1.5% |
| Distilled Spirits | ±0.3% |
| Malt Beverages (general) | ±0.3% |
| Malt Beverages ("low alcohol" claim) | NO tolerance (must be < 2.5%) |
| Malt Beverages ("non-alcoholic" claim) | NO tolerance (must be < 0.5%) |
| Malt Beverages ("alcohol free" claim) | NO tolerance (must be 0.0%) |

**Implementation:**
```python
# Pseudo-code
def validate_alcohol_content(label_abv, application_abv, product_type):
    tolerance = get_tolerance(product_type)
    
    diff = abs(label_abv - application_abv)
    
    if diff <= tolerance:
        return PASS
    else:
        return FAIL, f"ABV mismatch: {diff}% exceeds tolerance of {tolerance}%"
```

---

## Percentage Requirements for Wine

**Varietal Wine:**
- General: ≥75% from named grape
- Labrusca: ≥51% with disclosure statement

**Appellation:**
- General: ≥75% from stated appellation
- Viticultural area: ≥85% from stated AVA
- Multi-state: Must show percentages (±2% tolerance)

**Vintage:**
- With viticultural area: ≥95% from stated year
- With other appellation: ≥85% from stated year

**Implementation:**
```python
# Pseudo-code
def validate_varietal_wine(label_data):
    if label_data.varietal_name:
        # Check appellation present
        if not label_data.appellation:
            return FAIL, "Varietal name requires appellation"
        
        # Check percentage requirement met
        if label_data.is_labrusca:
            min_pct = 51
            requires_statement = True
        else:
            min_pct = 75
            requires_statement = False
        
        # Note: Actual percentage verification requires production data
        # Label validation focuses on required disclosures
        
        if requires_statement and not label_data.has_percentage_statement:
            return FAIL, "Labrusca varietal requires percentage statement"
    
    return PASS
```

---

## Conditional Requirements

**These requirements apply only in specific circumstances:**

### Alcohol Content Statement

| Product | Condition | Requirement |
|---------|-----------|-------------|
| Wine | > 14% ABV | REQUIRED |
| Wine | ≤ 14% ABV | OPTIONAL |
| Wine | "Table wine" or "light wine" label | PROHIBITED |
| Distilled Spirits | All | REQUIRED |
| Malt Beverages | Contains added alcohol from non-malt sources | REQUIRED |
| Malt Beverages | Standard fermentation only | OPTIONAL |

### Ingredient Disclosures

| Ingredient | Threshold | Requirement |
|-----------|-----------|-------------|
| Sulfites | ≥10 ppm | Must disclose |
| FD&C Yellow No. 5 | Any amount | Must disclose |
| Cochineal/Carmine | Any amount | Must disclose (prominent) |
| Aspartame | Any amount | Must disclose (all caps, separate) |

### Name/Address Phrasing

| Product Origin | Required Phrase |
|---------------|----------------|
| US-made spirits | "distilled by" / "bottled by" / etc. |
| Imported spirits | "imported by" |
| US-made wine | "bottled by" / "packed by" |
| Imported wine | "imported by" |
| US-made malt beverage | Name + address (optional phrases) |
| Imported malt beverage | "imported by" |

**Implementation:**
```python
# Pseudo-code
def validate_name_address(label_data, product_type, is_import):
    if is_import:
        required_phrase = "imported by"
    else:
        required_phrase = get_required_phrase(product_type)
    
    if required_phrase and required_phrase not in label_data.bottler_statement.lower():
        return FAIL, f"Missing required phrase: {required_phrase}"
    
    if not label_data.has_name:
        return FAIL, "Missing bottler/importer name"
    
    if not label_data.has_address:
        return FAIL, "Missing city and state"
    
    return PASS
```

---

## Fuzzy Matching Considerations

**Case-Insensitive Matching (Acceptable):**
- Brand names: "STONE'S THROW" vs "Stone's Throw"
- Bottler names: "ABC WINERY" vs "Abc Winery"

**Punctuation Tolerance (Acceptable):**
- Minor differences: "O'Brien" vs "O'Brien" (different apostrophe styles)
- Spacing: "Saint James" vs "St. James" (if officially recognized abbreviation)

**Format Variations (Acceptable):**
- Alcohol content: "45% alc./vol." vs "45% ABV" vs "Alcohol 45% by volume"
- State abbreviations: "California" vs "CA"

**NOT Acceptable:**
- Different words: "Old Tom Distillery" vs "Old Tom Distilling"
- Different numbers: "45%" vs "40%"
- Missing required words: "Bourbon Whisky" vs "Whisky"

**Implementation:**
```python
# Pseudo-code
def fuzzy_match_brand(label_brand, application_brand):
    # Normalize case
    label_norm = label_brand.lower().strip()
    app_norm = application_brand.lower().strip()
    
    # Exact match
    if label_norm == app_norm:
        return EXACT_MATCH
    
    # Punctuation normalization
    label_no_punct = remove_punctuation(label_norm)
    app_no_punct = remove_punctuation(app_norm)
    
    if label_no_punct == app_no_punct:
        return CASE_OR_PUNCT_VARIATION
    
    # Similarity check
    similarity = calculate_similarity(label_norm, app_norm)
    if similarity > 0.90:  # 90% threshold
        return SIMILAR_NEEDS_REVIEW
    
    return MISMATCH
```

---

## Field Presence Validation

**Always Required (All Products):**
- Brand name
- Class/type designation
- Name and address
- Net contents
- Government warning statement (Part 16)

**Conditionally Required:**
- Alcohol content (see tables above)
- Country of origin (imports only)
- Appellation (if varietal, vintage, or geographic designation used)
- Various ingredient disclosures (if ingredient present)

**Implementation:**
```python
# Pseudo-code
def validate_required_fields(label_data, product_type):
    issues = []
    
    # Always required
    if not label_data.brand_name:
        issues.append(CRITICAL, "Missing brand name")
    
    if not label_data.class_type:
        issues.append(CRITICAL, "Missing class/type designation")
    
    if not label_data.name_address:
        issues.append(CRITICAL, "Missing bottler/importer name and address")
    
    if not label_data.net_contents:
        issues.append(CRITICAL, "Missing net contents")
    
    if not label_data.government_warning:
        issues.append(CRITICAL, "Missing government warning")
    
    # Conditional requirements
    if requires_alcohol_content(product_type, label_data):
        if not label_data.alcohol_content:
            issues.append(CRITICAL, "Missing required alcohol content")
    
    if label_data.is_import and not label_data.country_of_origin:
        issues.append(CRITICAL, "Missing country of origin for import")
    
    if has_sulfites(label_data) and not label_data.sulfite_disclosure:
        issues.append(CRITICAL, "Missing sulfite disclosure")
    
    return issues
```

---

## Severity Classification

**CRITICAL (Auto-Reject):**
- Missing government warning
- Incorrect government warning text
- Incorrect government warning format (not all caps, body bold, etc.)
- Missing required field (brand, class, net contents, etc.)
- Wrong alcohol content (outside tolerance)
- Missing required ingredient disclosure

**WARNING (Human Review):**
- Case variation in brand name
- Punctuation differences
- Format variations in acceptable fields
- Slightly unclear text extraction
- Minor spacing issues

**INFO (Note Only):**
- Optional fields present
- Additional approved information
- Format exceeds minimum requirements

**Implementation:**
```python
# Pseudo-code
def classify_issue_severity(issue_type, details):
    if issue_type == "missing_warning":
        return CRITICAL, "Government warning missing - REJECT"
    
    if issue_type == "warning_format":
        return CRITICAL, "Government warning format incorrect - REJECT"
    
    if issue_type == "missing_required_field":
        return CRITICAL, f"Missing required field: {details} - REJECT"
    
    if issue_type == "case_variation":
        return WARNING, "Case variation detected - REVIEW"
    
    if issue_type == "format_variation":
        return WARNING, "Format variation - REVIEW"
    
    return INFO, "Informational note"
```

---

## Validation Output Structure

**Recommended JSON structure for validation results:**

```json
{
  "validation_id": "VAL-2026-001234",
  "timestamp": "2026-02-14T12:00:00Z",
  "label_image": "path/to/image.jpg",
  "product_type": "distilled_spirits",
  "container_size_ml": 750,
  
  "overall_status": "COMPLIANT" | "NON_COMPLIANT" | "REVIEW_REQUIRED",
  
  "validation_results": {
    "government_warning": {
      "present": true,
      "text_extracted": "GOVERNMENT WARNING: (1) According to...",
      "text_match": true,
      "header_all_caps": true,
      "header_bold": true,
      "body_not_bold": true,
      "type_size_mm": 2.1,
      "type_size_requirement_mm": 2.0,
      "status": "PASS",
      "issues": []
    },
    
    "brand_name": {
      "present": true,
      "extracted_value": "STONE'S THROW",
      "application_value": "Stone's Throw",
      "match_type": "CASE_VARIATION",
      "confidence": 0.95,
      "status": "REVIEW_REQUIRED",
      "issues": [
        {
          "severity": "WARNING",
          "message": "Case variation detected between label and application",
          "recommendation": "Human review recommended"
        }
      ]
    },
    
    "class_type": {
      "present": true,
      "extracted_value": "Kentucky Straight Bourbon Whiskey",
      "application_value": "Kentucky Straight Bourbon Whiskey",
      "match_type": "EXACT",
      "status": "PASS",
      "issues": []
    },
    
    "alcohol_content": {
      "present": true,
      "extracted_value": "45% alc./vol.",
      "extracted_abv_numeric": 45.0,
      "application_abv_numeric": 45.0,
      "tolerance": 0.3,
      "within_tolerance": true,
      "proof_shown": true,
      "proof_value": 90,
      "proof_correct": true,
      "status": "PASS",
      "issues": []
    },
    
    "net_contents": {
      "present": true,
      "extracted_value": "750 mL",
      "application_value": "750ml",
      "match_type": "FORMAT_VARIATION",
      "status": "PASS",
      "issues": []
    },
    
    "name_address": {
      "present": true,
      "extracted_value": "Distilled by Old Tom Distillery, Louisville, KY",
      "has_required_phrase": true,
      "required_phrase": "distilled by",
      "has_name": true,
      "has_city": true,
      "has_state": true,
      "status": "PASS",
      "issues": []
    },
    
    "country_of_origin": {
      "required": false,
      "present": false,
      "extracted_value": null,
      "application_value": null,
      "status": "NOT_APPLICABLE",
      "issues": []
    },
    
    "sulfite_disclosure": {
      "required": false,
      "present": false,
      "status": "NOT_APPLICABLE",
      "issues": []
    }
  },
  
  "violations": [
    {
      "field": "government_warning",
      "severity": "CRITICAL",
      "issue": "Warning text is in bold",
      "regulation": "27 CFR § 16.22(a)(2)",
      "recommendation": "Remove bold formatting from warning body text"
    }
  ],
  
  "warnings": [
    {
      "field": "brand_name",
      "severity": "WARNING",
      "issue": "Case variation detected",
      "regulation": "27 CFR § 5.64",
      "recommendation": "Human review recommended for brand name match"
    }
  ],
  
  "info": [
    {
      "field": "alcohol_content",
      "message": "Proof shown in addition to ABV (optional but correct)",
      "regulation": "27 CFR § 5.65"
    }
  ],
  
  "summary": {
    "total_fields_checked": 12,
    "fields_passed": 9,
    "fields_failed": 1,
    "fields_review_required": 2,
    "critical_violations": 1,
    "warnings": 1,
    "processing_time_ms": 3247
  },
  
  "recommendation": "NON_COMPLIANT - Critical violations must be corrected before approval",
  
  "agent_notes": "Government warning body text appears to be bold. This violates 27 CFR § 16.22(a)(2). Label must be rejected until corrected."
}
```

---

# TESTING SCENARIOS

## GOOD Label Test Cases

### 1. Perfect Compliance - Distilled Spirits
**All fields present, exact matches, perfect formatting**

```
Brand: "Old Tom Distillery"
Class: "Kentucky Straight Bourbon Whiskey"
ABV: "45% Alc./Vol. (90 Proof)"
Net: "750 mL"
Bottler: "Distilled by Old Tom Distillery, Louisville, Kentucky"
Warning: [Exact text, GOVERNMENT WARNING in all caps bold, body not bold]
```

**Expected:** COMPLIANT, all checks PASS

### 2. Format Variations - Wine
**Acceptable format differences**

```
Brand: "STONE'S THROW" (application: "Stone's Throw")
Class: "Cabernet Sauvignon"
ABV: "13.5% ABV" (application: "13.5% alc./vol.")
Net: "750ml" (application: "750 mL")
Bottler: "Bottled by Stone's Throw Winery, Napa, CA"
Warning: [Correct]
Sulfites: "Contains Sulfites"
```

**Expected:** REVIEW_REQUIRED, case variation in brand

### 3. Minimum Required - Malt Beverage
**Only mandatory fields, no optional info**

```
Brand: "Hop Valley Brewing"
Class: "India Pale Ale"
Net: "12 fl oz"
Brewer: "Hop Valley Brewing Company, Eugene, OR"
Warning: [Correct]
```

**Expected:** COMPLIANT (alcohol content optional for standard malt beverage)

### 4. Import Label - Spirits
**Includes country of origin and import statement**

```
Brand: "Highland Reserve"
Class: "Scotch Whisky"
ABV: "43% alc./vol."
Net: "750 mL"
Importer: "Imported by Premium Spirits Inc., New York, NY"
Country: "Product of Scotland"
Warning: [Correct]
```

**Expected:** COMPLIANT

### 5. High ABV Wine
**Wine > 14% requires alcohol content**

```
Brand: "Vino Rosso"
Class: "Dessert Wine"
ABV: "18% alc./vol."
Net: "375 mL"
Bottler: "Bottled by Vino Rosso Winery, Paso Robles, CA"
Warning: [Correct]
Sulfites: "Contains Sulfites"
```

**Expected:** COMPLIANT

---

## BAD Label Test Cases

### Critical Violations (Auto-Reject)

#### 1. Missing Government Warning
**No warning statement present**

```
Brand: "Old Tom Distillery"
Class: "Bourbon Whiskey"
ABV: "45% alc./vol."
Net: "750 mL"
Bottler: "Distilled by Old Tom Distillery, Louisville, KY"
[NO WARNING]
```

**Expected:** NON_COMPLIANT - CRITICAL: Missing government warning

#### 2. Warning Header Not All Caps
**"Government Warning:" instead of "GOVERNMENT WARNING:"**

```
Brand: "Bad Label Spirits"
Class: "Vodka"
ABV: "40% alc./vol."
Net: "750 mL"
Bottler: "Bottled by Bad Label Spirits, Portland, OR"
Warning: "Government Warning: (1) According to the Surgeon General..."
```

**Expected:** NON_COMPLIANT - CRITICAL: Warning header not all caps

#### 3. Warning Body in Bold
**Entire warning is bold**

```
Brand: "Bold Spirits"
Class: "Gin"
ABV: "47% alc./vol."
Net: "750 mL"
Bottler: "Distilled by Bold Spirits, San Francisco, CA"
Warning: [All text in bold including body]
```

**Expected:** NON_COMPLIANT - CRITICAL: Warning body must not be bold

#### 4. Incorrect Warning Text
**Modified or abbreviated warning text**

```
Brand: "Wrong Text Distillery"
Class: "Rum"
ABV: "40% alc./vol."
Net: "750 mL"
Bottler: "Bottled by Wrong Text Distillery, Miami, FL"
Warning: "GOVERNMENT WARNING: Pregnant women should not drink. Alcohol impairs driving."
```

**Expected:** NON_COMPLIANT - CRITICAL: Warning text does not match required wording

#### 5. Missing Brand Name
**No brand name present**

```
[NO BRAND]
Class: "Beer"
Net: "12 fl oz"
Brewer: "Unknown Brewing, Denver, CO"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - CRITICAL: Missing required brand name

#### 6. Missing Alcohol Content (Required Case)
**High-ABV wine without alcohol content**

```
Brand: "Sweet Port"
Class: "Dessert Wine"
[NO ABV - but > 14% so REQUIRED]
Net: "750 mL"
Bottler: "Bottled by Sweet Port Winery, Lodi, CA"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - CRITICAL: Missing required alcohol content

#### 7. Missing Net Contents
**No volume statement**

```
Brand: "Incomplete Label"
Class: "Whiskey"
ABV: "40% alc./vol."
[NO NET CONTENTS]
Bottler: "Bottled by Incomplete Distillery, Louisville, KY"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - CRITICAL: Missing net contents

#### 8. Missing Country of Origin (Import)
**Imported product without country statement**

```
Brand: "Foreign Spirit"
Class: "Vodka"
ABV: "40% alc./vol."
Net: "750 mL"
Importer: "Imported by XYZ Imports, New York, NY"
[NO COUNTRY OF ORIGIN]
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - CRITICAL: Missing country of origin for import

---

### Format Violations (Should Flag)

#### 9. ABV Outside Tolerance
**Label shows 40%, application says 45%**

```
Brand: "Wrong Proof"
Class: "Vodka"
ABV: "40% alc./vol." (application: 45%)
Net: "750 mL"
Bottler: "Bottled by Wrong Proof Distillery, Portland, OR"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - CRITICAL: ABV mismatch exceeds tolerance

#### 10. Wrong Net Contents
**Label shows 750mL, application says 1L**

```
Brand: "Size Mismatch"
Class: "Gin"
ABV: "47% alc./vol."
Net: "750 mL" (application: 1L)
Bottler: "Distilled by Size Mismatch, Seattle, WA"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - CRITICAL: Net contents mismatch

#### 11. Brand Name Completely Different
**Not just case variation, different words**

```
Brand: "Old Tom Distilling" (application: "Old Tom Distillery")
Class: "Bourbon"
ABV: "45% alc./vol."
Net: "750 mL"
Bottler: "Distilled by Old Tom Distilling, Louisville, KY"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT or REVIEW_REQUIRED - Brand name mismatch

#### 12. Wrong Class/Type
**Label says "Whiskey", application says "Bourbon Whiskey"**

```
Brand: "Bourbon Brand"
Class: "Whiskey" (application: "Bourbon Whiskey")
ABV: "45% alc./vol."
Net: "750 mL"
Bottler: "Distilled by Bourbon Brand, Louisville, KY"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - Class/type designation mismatch

---

### Nuanced Cases (Human Review)

#### 13. Case Variation Only
**Same words, different capitalization**

```
Brand: "STONE'S THROW" (application: "Stone's Throw")
Class: "Cabernet Sauvignon"
ABV: "13% alc./vol."
Net: "750 mL"
Bottler: "Bottled by Stone's Throw Winery, Napa, CA"
Warning: [Correct]
```

**Expected:** REVIEW_REQUIRED - Case variation in brand name

#### 14. ABV Format Variation
**Different format but same value**

```
Brand: "Format Test"
Class: "Bourbon"
ABV: "45% ABV" (application: "45% alc./vol.")
Net: "750 mL"
Bottler: "Distilled by Format Test, Louisville, KY"
Warning: [Correct]
```

**Expected:** REVIEW_REQUIRED or PASS - Acceptable format variation

#### 15. State Abbreviation
**"CA" vs "California"**

```
Brand: "West Coast Winery"
Class: "Chardonnay"
ABV: "13.5% alc./vol."
Net: "750 mL"
Bottler: "Bottled by West Coast Winery, Napa, CA" (application: "California")
Warning: [Correct]
```

**Expected:** PASS or REVIEW_REQUIRED - Postal abbreviation acceptable

#### 16. Minor Punctuation
**Apostrophe style differences**

```
Brand: "O'Brien's Brewery" (application: "O'Brien's Brewery")
Class: "Stout"
Net: "12 fl oz"
Brewer: "O'Brien's Brewery, Boston, MA"
Warning: [Correct]
```

**Expected:** REVIEW_REQUIRED - Minor punctuation variation

---

## Special Test Cases

#### 17. Type Size Too Small
**Warning text < 2mm on 750mL bottle**

```
Brand: "Tiny Text"
Class: "Vodka"
ABV: "40% alc./vol."
Net: "750 mL"
Bottler: "Bottled by Tiny Text, Portland, OR"
Warning: [Correct text but 1mm type on 750mL bottle - requires 2mm]
```

**Expected:** NON_COMPLIANT - Warning type size too small

#### 18. Missing "Imported By" Language
**Import without proper phrasing**

```
Brand: "Foreign Vodka"
Class: "Vodka"
ABV: "40% alc./vol."
Net: "750 mL"
Bottler: "XYZ Imports, New York, NY" [missing "imported by"]
Country: "Product of Russia"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - Missing required "imported by" phrase

#### 19. Sulfites Missing (Wine with Sulfites ≥10ppm)
**Application indicates sulfites but not on label**

```
Brand: "Missing Sulfites"
Class: "Pinot Noir"
ABV: "14% alc./vol."
Net: "750 mL"
Bottler: "Bottled by Missing Sulfites Winery, Willamette, OR"
Warning: [Correct]
[NO SULFITE DISCLOSURE - but application indicates ≥10ppm]
```

**Expected:** NON_COMPLIANT - CRITICAL: Missing required sulfite disclosure

#### 20. Malt Beverage Net Contents in Metric Only
**No US customary units**

```
Brand: "Metric Only Brewing"
Class: "Lager"
Net: "355 mL" [MUST have US units: "12 fl oz"]
Brewer: "Metric Only Brewing, Portland, OR"
Warning: [Correct]
```

**Expected:** NON_COMPLIANT - Malt beverages require US customary units

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

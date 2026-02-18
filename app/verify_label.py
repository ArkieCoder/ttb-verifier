#!/usr/bin/env python3
"""
TTB Label Verification CLI

Command-line interface for validating alcohol beverage labels
against 27 CFR regulations.

Usage:
    verify_label.py <image_path> [options]
    verify_label.py --batch <directory> [options]

Examples:
    # Structural validation only (fast)
    verify_label.py label.jpg

    # Full validation with ground truth
    verify_label.py label.jpg --ground-truth metadata.json

    # Use AI OCR for better accuracy (slower)
    verify_label.py label.jpg --ocr-backend ollama

    # Batch process directory
    verify_label.py --batch samples/ --ground-truth-dir samples/
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

from label_validator import LabelValidator


def load_ground_truth(ground_truth_path: Optional[str]) -> Optional[Dict[str, Any]]:
    """Load ground truth data from JSON file."""
    if not ground_truth_path:
        return None
    
    try:
        with open(ground_truth_path, 'r') as f:
            data = json.load(f)
        
        # Check if data has nested "ground_truth" key (from sample generator)
        if 'ground_truth' in data:
            data = data['ground_truth']
        
        # Map expected fields from sample generator format
        # Generator uses: brand_name, alcohol_content_numeric, net_contents, bottler_info, class_type
        ground_truth = {}
        
        if 'brand_name' in data:
            ground_truth['brand_name'] = data['brand_name']
        
        # Try multiple ABV field names
        if 'alcohol_content_numeric' in data:
            abv = data['alcohol_content_numeric']
            if isinstance(abv, str):
                abv = float(abv.rstrip('%'))
            ground_truth['abv'] = abv
        elif 'abv' in data:
            abv = data['abv']
            if isinstance(abv, str):
                abv = float(abv.rstrip('%'))
            ground_truth['abv'] = abv
        
        if 'net_contents' in data:
            ground_truth['net_contents'] = data['net_contents']
        
        # Try multiple bottler field names
        if 'bottler_info' in data:
            ground_truth['bottler'] = data['bottler_info']
        elif 'bottled_by' in data:
            ground_truth['bottler'] = data['bottled_by']
        
        if 'class_type' in data:
            ground_truth['product_type'] = data['class_type']
        elif 'product_type' in data:
            ground_truth['product_type'] = data['product_type']
        
        return ground_truth
    
    except FileNotFoundError:
        print(f"Error: Ground truth file not found: {ground_truth_path}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in ground truth file: {ground_truth_path}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error loading ground truth: {e}", file=sys.stderr)
        return None


def validate_single_label(image_path: str,
                         ground_truth_path: Optional[str],
                         ocr_backend: str,
                         verbose: bool = False) -> Dict[str, Any]:
    """Validate a single label image."""
    # Check if image exists
    if not os.path.exists(image_path):
        return {
            "status": "ERROR",
            "error": f"Image file not found: {image_path}",
            "validation_level": "STRUCTURAL_ONLY",
            "extracted_fields": {},
            "validation_results": {
                "structural": [],
                "accuracy": []
            },
            "violations": [],
            "processing_time_seconds": 0.0
        }
    
    # Load ground truth if provided
    ground_truth = load_ground_truth(ground_truth_path)
    
    # Initialize validator
    if verbose:
        print(f"Initializing {ocr_backend} OCR backend...", file=sys.stderr)
    
    validator = LabelValidator(ocr_backend=ocr_backend)
    
    # Validate
    if verbose:
        print(f"Processing {image_path}...", file=sys.stderr)
    
    result = validator.validate_label(image_path, ground_truth)
    
    # Add image path to result
    result['image_path'] = image_path
    
    return result


def validate_batch(directory: str,
                  ground_truth_dir: Optional[str],
                  ocr_backend: str,
                  verbose: bool = False) -> List[Dict[str, Any]]:
    """Validate all images in a directory."""
    results = []
    
    # Find all image files
    image_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
    image_files = []
    
    dir_path = Path(directory)
    for ext in image_extensions:
        image_files.extend(dir_path.glob(f"*{ext}"))
    
    if not image_files:
        print(f"No image files found in {directory}", file=sys.stderr)
        return []
    
    if verbose:
        print(f"Found {len(image_files)} images to process", file=sys.stderr)
    
    # Process each image
    for i, image_path in enumerate(sorted(image_files), 1):
        if verbose:
            print(f"\n[{i}/{len(image_files)}] Processing {image_path.name}...", file=sys.stderr)
        
        # Look for corresponding ground truth JSON
        ground_truth_path = None
        if ground_truth_dir:
            json_path = Path(ground_truth_dir) / f"{image_path.stem}.json"
            if json_path.exists():
                ground_truth_path = str(json_path)
            elif verbose:
                print(f"  No ground truth found: {json_path}", file=sys.stderr)
        
        # Validate
        result = validate_single_label(
            str(image_path),
            ground_truth_path,
            ocr_backend,
            verbose=False  # Don't duplicate verbose output
        )
        
        results.append(result)
        
        # Show quick status
        if verbose:
            status = result.get('status', 'UNKNOWN')
            processing_time = result.get('processing_time_seconds', 0)
            print(f"  Status: {status} ({processing_time:.2f}s)", file=sys.stderr)
    
    return results


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print batch processing summary."""
    total = len(results)
    compliant = sum(1 for r in results if r.get('status') == 'COMPLIANT')
    non_compliant = sum(1 for r in results if r.get('status') == 'NON_COMPLIANT')
    partial = sum(1 for r in results if r.get('status') == 'PARTIAL_VALIDATION')
    errors = sum(1 for r in results if r.get('status') == 'ERROR')
    
    total_time = sum(r.get('processing_time_seconds', 0) for r in results)
    avg_time = total_time / total if total > 0 else 0
    
    print("\n" + "="*60, file=sys.stderr)
    print("BATCH PROCESSING SUMMARY", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"Total images processed: {total}", file=sys.stderr)
    print(f"  Compliant:            {compliant}", file=sys.stderr)
    print(f"  Non-compliant:        {non_compliant}", file=sys.stderr)
    print(f"  Partial validation:   {partial}", file=sys.stderr)
    print(f"  Errors:               {errors}", file=sys.stderr)
    print(f"\nTotal processing time: {total_time:.2f}s", file=sys.stderr)
    print(f"Average time per label: {avg_time:.2f}s", file=sys.stderr)
    print("="*60, file=sys.stderr)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TTB Label Verification Tool - Validate alcohol beverage labels against 27 CFR regulations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Structural validation only (fast)
  %(prog)s label.jpg

  # Full validation with ground truth
  %(prog)s label.jpg --ground-truth metadata.json

  # Use AI OCR for better accuracy (slower)
  %(prog)s label.jpg --ocr-backend ollama

  # Batch process directory
  %(prog)s --batch samples/ --ground-truth-dir samples/
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('image_path', nargs='?', help='Path to label image file')
    input_group.add_argument('--batch', metavar='DIR', help='Process all images in directory')
    
    # Validation options
    parser.add_argument('--ground-truth', metavar='FILE',
                       help='Path to ground truth JSON file (enables Tier 2 validation)')
    parser.add_argument('--ground-truth-dir', metavar='DIR',
                       help='Directory containing ground truth JSON files for batch processing')
    
    # OCR options
    parser.add_argument('--ocr-backend', choices=['tesseract', 'ollama'],
                       default='tesseract',
                       help='OCR backend: tesseract (fast, ~1s) or ollama (accurate, ~60s). Default: tesseract')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Print verbose progress information to stderr')
    parser.add_argument('--output', '-o', metavar='FILE',
                       help='Write output to file instead of stdout')
    
    args = parser.parse_args()
    
    # Process single image or batch
    results = None
    result = None
    
    if args.batch:
        # Batch processing
        results = validate_batch(
            args.batch,
            args.ground_truth_dir,
            args.ocr_backend,
            args.verbose
        )
        
        # Print summary to stderr
        if args.verbose:
            print_summary(results)
        
        # Output results as JSON array (compact)
        output = json.dumps(results)
    else:
        # Single image processing
        result = validate_single_label(
            args.image_path,
            args.ground_truth,
            args.ocr_backend,
            args.verbose
        )
        
        # Output result as JSON object (compact)
        output = json.dumps(result)
    
    # Write output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
            f.write('\n')
        if args.verbose:
            print(f"\nOutput written to {args.output}", file=sys.stderr)
    else:
        print(output)
    
    # Exit with appropriate code
    if args.batch:
        # Exit 0 if all successful, 1 if any non-compliant or errors
        if results:
            has_issues = any(r.get('status') in ['NON_COMPLIANT', 'ERROR'] for r in results)
            sys.exit(1 if has_issues else 0)
        else:
            sys.exit(1)
    else:
        # Exit 0 if compliant, 1 if non-compliant or error
        if result:
            status = result.get('status')
            sys.exit(0 if status == 'COMPLIANT' else 1)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()

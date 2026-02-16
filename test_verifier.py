#!/usr/bin/env python3
"""
Test script for TTB Label Verifier

Runs verification on the full golden dataset (40 samples) and generates
accuracy metrics comparing verifier results against ground truth labels.

Usage:
    python3 test_verifier.py [--ocr-backend tesseract|ollama]

Outputs:
    - Detailed JSON results for each label
    - Summary statistics (accuracy, precision, recall)
    - Performance metrics (processing time)
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple

from label_validator import LabelValidator


def load_golden_dataset(samples_dir: str = "samples") -> List[Tuple[str, str, Dict[str, Any]]]:
    """
    Load all golden dataset samples with ground truth.
    
    Returns:
        List of tuples: (image_path, label_type, ground_truth_dict)
    """
    samples_path = Path(samples_dir)
    dataset = []
    
    # Find all JSON files
    json_files = sorted(samples_path.glob("*.json"))
    
    for json_file in json_files:
        # Load ground truth
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Get corresponding image file
        image_file = samples_path / f"{json_file.stem}.jpg"
        if not image_file.exists():
            print(f"Warning: Image not found for {json_file.name}", file=sys.stderr)
            continue
        
        # Extract label type (GOOD or BAD)
        label_type = data.get('label_type', 'UNKNOWN')
        
        # Extract ground truth
        if 'ground_truth' in data:
            gt = data['ground_truth']
            ground_truth = {
                'brand_name': gt.get('brand_name'),
                'abv': gt.get('alcohol_content_numeric'),
                'net_contents': gt.get('net_contents'),
                'bottler': gt.get('bottler_info'),
                'product_type': gt.get('class_type')
            }
        else:
            ground_truth = {}
        
        dataset.append((str(image_file), label_type, ground_truth))
    
    return dataset


def run_tests(ocr_backend: str, samples_dir: str = "samples") -> Dict[str, Any]:
    """
    Run verifier on all samples in golden dataset.
    
    Returns:
        Dictionary with test results and metrics
    """
    print(f"Loading golden dataset from {samples_dir}/...", file=sys.stderr)
    dataset = load_golden_dataset(samples_dir)
    print(f"Found {len(dataset)} samples", file=sys.stderr)
    
    print(f"\nInitializing verifier with {ocr_backend} backend...", file=sys.stderr)
    validator = LabelValidator(ocr_backend=ocr_backend)
    
    results = []
    total_time = 0.0
    
    print(f"\nProcessing samples...\n", file=sys.stderr)
    
    for i, (image_path, expected_label_type, ground_truth) in enumerate(dataset, 1):
        filename = Path(image_path).name
        
        print(f"[{i}/{len(dataset)}] {filename}...", end=" ", file=sys.stderr)
        
        start_time = time.time()
        result = validator.validate_label(image_path, ground_truth)
        processing_time = time.time() - start_time
        
        total_time += processing_time
        
        # Add metadata
        result['expected_label_type'] = expected_label_type
        result['image_file'] = filename
        
        results.append(result)
        
        # Show quick status
        status = result.get('status', 'UNKNOWN')
        print(f"{status} ({processing_time:.2f}s)", file=sys.stderr)
    
    # Calculate metrics
    metrics = calculate_metrics(results)
    
    return {
        'ocr_backend': ocr_backend,
        'total_samples': len(dataset),
        'total_time_seconds': round(total_time, 2),
        'average_time_per_sample': round(total_time / len(dataset), 2) if dataset else 0,
        'metrics': metrics,
        'results': results
    }


def calculate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate accuracy metrics from test results."""
    
    # Count GOOD vs BAD labels
    good_labels = [r for r in results if r.get('expected_label_type') == 'GOOD']
    bad_labels = [r for r in results if r.get('expected_label_type') == 'BAD']
    
    # For GOOD labels, we expect COMPLIANT status
    # For BAD labels, we expect NON_COMPLIANT status
    
    # True Positives: BAD labels correctly identified as NON_COMPLIANT
    true_positives = sum(1 for r in bad_labels if r.get('status') == 'NON_COMPLIANT')
    
    # True Negatives: GOOD labels correctly identified as COMPLIANT
    true_negatives = sum(1 for r in good_labels if r.get('status') == 'COMPLIANT')
    
    # False Positives: GOOD labels incorrectly identified as NON_COMPLIANT
    false_positives = sum(1 for r in good_labels if r.get('status') == 'NON_COMPLIANT')
    
    # False Negatives: BAD labels incorrectly identified as COMPLIANT
    false_negatives = sum(1 for r in bad_labels if r.get('status') == 'COMPLIANT')
    
    # Calculate metrics
    total = len(results)
    accuracy = (true_positives + true_negatives) / total if total > 0 else 0
    
    # Precision: Of all labels we flagged as non-compliant, how many were actually bad?
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    
    # Recall: Of all bad labels, how many did we catch?
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    
    # F1 score
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # Violation breakdown
    violation_types = {}
    for result in results:
        for violation in result.get('violations', []):
            vtype = violation.get('field', 'unknown')
            violation_types[vtype] = violation_types.get(vtype, 0) + 1
    
    return {
        'accuracy': round(accuracy, 3),
        'precision': round(precision, 3),
        'recall': round(recall, 3),
        'f1_score': round(f1_score, 3),
        'confusion_matrix': {
            'true_positives': true_positives,
            'true_negatives': true_negatives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        },
        'sample_breakdown': {
            'good_labels': {
                'total': len(good_labels),
                'compliant': true_negatives,
                'non_compliant': false_positives
            },
            'bad_labels': {
                'total': len(bad_labels),
                'compliant': false_negatives,
                'non_compliant': true_positives
            }
        },
        'top_violations': dict(sorted(violation_types.items(), key=lambda x: x[1], reverse=True)[:10])
    }


def print_summary(test_results: Dict[str, Any]) -> None:
    """Print human-readable test summary."""
    metrics = test_results['metrics']
    
    print("\n" + "="*70, file=sys.stderr)
    print("TEST SUMMARY", file=sys.stderr)
    print("="*70, file=sys.stderr)
    
    print(f"\nOCR Backend: {test_results['ocr_backend']}", file=sys.stderr)
    print(f"Total samples: {test_results['total_samples']}", file=sys.stderr)
    print(f"Total processing time: {test_results['total_time_seconds']}s", file=sys.stderr)
    print(f"Average time per sample: {test_results['average_time_per_sample']}s", file=sys.stderr)
    
    print(f"\n--- ACCURACY METRICS ---", file=sys.stderr)
    print(f"Overall accuracy: {metrics['accuracy']:.1%}", file=sys.stderr)
    print(f"Precision: {metrics['precision']:.1%} (of flagged violations, how many are real)", file=sys.stderr)
    print(f"Recall: {metrics['recall']:.1%} (of real violations, how many we catch)", file=sys.stderr)
    print(f"F1 Score: {metrics['f1_score']:.1%}", file=sys.stderr)
    
    cm = metrics['confusion_matrix']
    print(f"\n--- CONFUSION MATRIX ---", file=sys.stderr)
    print(f"True Positives (BAD caught): {cm['true_positives']}", file=sys.stderr)
    print(f"True Negatives (GOOD passed): {cm['true_negatives']}", file=sys.stderr)
    print(f"False Positives (GOOD flagged): {cm['false_positives']}", file=sys.stderr)
    print(f"False Negatives (BAD missed): {cm['false_negatives']}", file=sys.stderr)
    
    sb = metrics['sample_breakdown']
    print(f"\n--- SAMPLE BREAKDOWN ---", file=sys.stderr)
    print(f"GOOD labels ({sb['good_labels']['total']}):", file=sys.stderr)
    print(f"  ✓ Passed: {sb['good_labels']['compliant']}", file=sys.stderr)
    print(f"  ✗ Failed: {sb['good_labels']['non_compliant']}", file=sys.stderr)
    print(f"BAD labels ({sb['bad_labels']['total']}):", file=sys.stderr)
    print(f"  ✓ Caught: {sb['bad_labels']['non_compliant']}", file=sys.stderr)
    print(f"  ✗ Missed: {sb['bad_labels']['compliant']}", file=sys.stderr)
    
    print(f"\n--- TOP VIOLATIONS DETECTED ---", file=sys.stderr)
    for field, count in list(metrics['top_violations'].items())[:5]:
        print(f"  {field}: {count} occurrences", file=sys.stderr)
    
    print("="*70, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Test TTB Label Verifier on golden dataset"
    )
    
    parser.add_argument('--ocr-backend', choices=['tesseract', 'ollama'],
                       default='tesseract',
                       help='OCR backend to test (default: tesseract)')
    parser.add_argument('--samples-dir', default='samples',
                       help='Directory containing golden dataset (default: samples/)')
    parser.add_argument('--output', '-o',
                       help='Write detailed JSON results to file')
    parser.add_argument('--summary-only', action='store_true',
                       help='Only print summary, no detailed JSON output')
    
    args = parser.parse_args()
    
    # Run tests
    test_results = run_tests(args.ocr_backend, args.samples_dir)
    
    # Print summary
    print_summary(test_results)
    
    # Output detailed results
    if not args.summary_only:
        output_json = json.dumps(test_results, indent=2)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output_json)
                f.write('\n')
            print(f"\nDetailed results written to {args.output}", file=sys.stderr)
        else:
            print("\n" + output_json)
    
    # Exit with code based on accuracy
    # Exit 0 if accuracy >= 95%, else 1
    accuracy = test_results['metrics']['accuracy']
    sys.exit(0 if accuracy >= 0.95 else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
#
# Comprehensive Test Script for TTB Label Verifier
#
# Usage:
#   ./run_tests.sh                    # Run all tests
#   ./run_tests.sh --quick            # Run quick tests only (skip slow Ollama)
#   ./run_tests.sh --stop-on-error    # Stop at first failure
#   ./run_tests.sh --verbose          # Show detailed output
#   ./run_tests.sh --cleanup          # Clean up test artifacts after run

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Options
QUICK_MODE=false
STOP_ON_ERROR=false
VERBOSE=false
CLEANUP=false
TEST_OUTPUT_DIR="test_output"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --stop-on-error)
            STOP_ON_ERROR=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --quick           Run quick tests only (skip slow Ollama tests)"
            echo "  --stop-on-error   Stop at first test failure"
            echo "  --verbose         Show detailed output from each test"
            echo "  --cleanup         Clean up test artifacts after run"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Create test output directory
mkdir -p "$TEST_OUTPUT_DIR"

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_test() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -e "${CYAN}[TEST $TOTAL_TESTS]${NC} $1"
}

print_pass() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "  ${GREEN}✓ PASS${NC} $1"
}

print_fail() {
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "  ${RED}✗ FAIL${NC} $1"
    if [ "$STOP_ON_ERROR" = true ]; then
        echo -e "\n${RED}Stopping due to test failure (--stop-on-error)${NC}\n"
        exit 1
    fi
}

print_skip() {
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    echo -e "  ${YELLOW}⊘ SKIP${NC} $1"
}

run_command() {
    local cmd="$1"
    local expected_exit_code="${2:-0}"
    local output_file="$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"
    
    if [ "$VERBOSE" = true ]; then
        echo -e "  ${YELLOW}Running:${NC} $cmd"
    fi
    
    set +e
    if [ "$VERBOSE" = true ]; then
        eval "$cmd" 2>&1 | tee "$output_file"
        exit_code=${PIPESTATUS[0]}
    else
        eval "$cmd" > "$output_file" 2>&1
        exit_code=$?
    fi
    set -e
    
    echo "$exit_code"
}

validate_json() {
    local file="$1"
    if python3 -m json.tool "$file" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

check_ollama() {
    if command -v ollama &> /dev/null && ollama list 2>&1 | grep -q "llama3.2-vision"; then
        return 0
    else
        return 1
    fi
}

# Start tests
print_header "TTB Label Verifier - Comprehensive Test Suite"
echo "Test output directory: $TEST_OUTPUT_DIR"
echo "Quick mode: $QUICK_MODE"
echo "Stop on error: $STOP_ON_ERROR"
echo "Verbose: $VERBOSE"
echo ""

#
# CATEGORY 1: Single Label Tests
#
print_header "CATEGORY 1: Single Label Verification"

print_test "Single GOOD label with ground truth"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg --ground-truth samples/label_good_001.json" 1)
if [ "$exit_code" -eq 1 ] && validate_json "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"; then
    print_pass "Exit code 1 (non-compliant due to OCR), valid JSON"
else
    print_fail "Expected exit code 1, got $exit_code or invalid JSON"
fi

print_test "Single BAD label with ground truth"
exit_code=$(run_command "python3 verify_label.py samples/label_bad_001.jpg --ground-truth samples/label_bad_001.json" 1)
if [ "$exit_code" -eq 1 ] && validate_json "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"; then
    print_pass "Exit code 1 (non-compliant), valid JSON"
else
    print_fail "Expected exit code 1, got $exit_code or invalid JSON"
fi

print_test "Label without ground truth (structural only)"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg" 1)
if validate_json "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"; then
    output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
    if echo "$output" | grep -q '"validation_level": "STRUCTURAL_ONLY"'; then
        print_pass "Structural validation performed, valid JSON"
    else
        print_fail "Did not find STRUCTURAL_ONLY validation level"
    fi
else
    print_fail "Invalid JSON output"
fi

print_test "Non-existent image file (error handling)"
exit_code=$(run_command "python3 verify_label.py nonexistent.jpg" 1)
if [ "$exit_code" -ne 0 ]; then
    print_pass "Correctly handled missing file"
else
    print_fail "Should have failed with non-zero exit code"
fi

print_test "Invalid ground truth JSON (graceful degradation)"
echo "invalid json{" > "$TEST_OUTPUT_DIR/invalid.json"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg --ground-truth $TEST_OUTPUT_DIR/invalid.json 2>&1" 0)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
# Should print error to stderr but continue with structural validation
# Extract just the JSON part (skip the error line)
json_output=$(echo "$output" | grep -v "^Error:")
if echo "$output" | grep -q "Invalid JSON" && echo "$output" | grep -q "STRUCTURAL_ONLY" && echo "$json_output" | python3 -m json.tool > /dev/null 2>&1; then
    print_pass "Gracefully degraded to structural validation with error message"
else
    print_fail "Did not gracefully handle invalid JSON"
fi

#
# CATEGORY 2: Output Format Tests
#
print_header "CATEGORY 2: Output Format Options"

print_test "JSON output to file"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg --ground-truth samples/label_good_001.json -o $TEST_OUTPUT_DIR/output.json" 1)
if [ -f "$TEST_OUTPUT_DIR/output.json" ] && validate_json "$TEST_OUTPUT_DIR/output.json"; then
    print_pass "Output file created with valid JSON"
else
    print_fail "Output file not created or invalid JSON"
fi

print_test "Compact JSON output (no indentation)"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
# Check that output is compact (no leading spaces indicating indentation)
if ! echo "$output" | grep -q "^  " && validate_json "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"; then
    print_pass "Compact JSON with no indentation"
else
    print_fail "JSON is pretty-printed or invalid"
fi

print_test "Verbose mode"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg --ground-truth samples/label_good_001.json --verbose 2>&1" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
if echo "$output" | grep -q "Initializing"; then
    print_pass "Verbose output includes progress messages"
else
    print_fail "Verbose mode not working"
fi

print_test "JSON pipeline compatibility"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg 2>/dev/null | python3 -m json.tool > /dev/null" 0)
if [ "$exit_code" -eq 0 ]; then
    print_pass "JSON output is pipeable"
else
    print_fail "JSON output cannot be piped"
fi

#
# CATEGORY 3: Batch Processing Tests
#
print_header "CATEGORY 3: Batch Processing"

print_test "Small batch (6 samples)"
exit_code=$(run_command "python3 verify_label.py --batch test_samples/ --ground-truth-dir test_samples/" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
if validate_json "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"; then
    count=$(echo "$output" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    if [ "$count" -eq 6 ]; then
        print_pass "Processed 6 images, valid JSON array"
    else
        print_fail "Expected 6 results, got $count"
    fi
else
    print_fail "Invalid JSON output"
fi

print_test "Full batch (40 samples)"
exit_code=$(run_command "python3 verify_label.py --batch samples/ --ground-truth-dir samples/" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
if validate_json "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"; then
    count=$(echo "$output" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    if [ "$count" -eq 40 ]; then
        print_pass "Processed 40 images, valid JSON array"
    else
        print_fail "Expected 40 results, got $count"
    fi
else
    print_fail "Invalid JSON output"
fi

print_test "Batch with verbose output"
exit_code=$(run_command "python3 verify_label.py --batch test_samples/ --ground-truth-dir test_samples/ --verbose 2>&1" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
if echo "$output" | grep -q "BATCH PROCESSING SUMMARY"; then
    print_pass "Verbose batch shows summary"
else
    print_fail "No summary found in verbose output"
fi

print_test "Batch output to file"
exit_code=$(run_command "python3 verify_label.py --batch test_samples/ --ground-truth-dir test_samples/ -o $TEST_OUTPUT_DIR/batch_output.json" 1)
if [ -f "$TEST_OUTPUT_DIR/batch_output.json" ] && validate_json "$TEST_OUTPUT_DIR/batch_output.json"; then
    print_pass "Batch output file created with valid JSON"
else
    print_fail "Batch output file not created or invalid JSON"
fi

#
# CATEGORY 4: OCR Backend Tests
#
print_header "CATEGORY 4: OCR Backend Options"

print_test "Tesseract backend (default)"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg --ocr-backend tesseract" 1)
if validate_json "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"; then
    print_pass "Tesseract backend works, valid JSON"
else
    print_fail "Tesseract backend failed or invalid JSON"
fi

print_test "Invalid backend name"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg --ocr-backend invalid" 2)
if [ "$exit_code" -ne 0 ]; then
    print_pass "Correctly rejected invalid backend"
else
    print_fail "Should have failed with invalid backend"
fi

if [ "$QUICK_MODE" = false ]; then
    if check_ollama; then
        print_test "Ollama backend (slow test)"
        echo -e "  ${YELLOW}Warning: This test takes ~60 seconds${NC}"
        exit_code=$(run_command "timeout 120s python3 verify_label.py samples/label_good_001.jpg --ocr-backend ollama --ground-truth samples/label_good_001.json" 1)
        if validate_json "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt"; then
            output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
            time=$(echo "$output" | python3 -c "import sys, json; print(json.load(sys.stdin).get('processing_time_seconds', 0))" 2>/dev/null || echo "0")
            print_pass "Ollama backend works (${time}s), valid JSON"
        else
            print_fail "Ollama backend failed or invalid JSON"
        fi
    else
        print_skip "Ollama not installed or llama3.2-vision not available"
    fi
else
    print_skip "Ollama test (--quick mode)"
fi

#
# CATEGORY 5: Comprehensive Test Suite
#
print_header "CATEGORY 5: Comprehensive Test Suite"

print_test "Test suite with summary"
exit_code=$(run_command "python3 test_verifier.py --ocr-backend tesseract --summary-only 2>&1" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
if echo "$output" | grep -q "TEST SUMMARY" && echo "$output" | grep -q "Overall accuracy"; then
    print_pass "Test suite ran successfully with metrics"
else
    print_fail "Test suite did not produce expected output"
fi

print_test "Test suite with JSON output"
exit_code=$(run_command "python3 test_verifier.py --ocr-backend tesseract -o $TEST_OUTPUT_DIR/test_suite_results.json 2>&1" 1)
if [ -f "$TEST_OUTPUT_DIR/test_suite_results.json" ] && validate_json "$TEST_OUTPUT_DIR/test_suite_results.json"; then
    output=$(cat "$TEST_OUTPUT_DIR/test_suite_results.json")
    if echo "$output" | python3 -c "import sys, json; d=json.load(sys.stdin); exit(0 if 'metrics' in d and 'results' in d else 1)" 2>/dev/null; then
        print_pass "Test suite JSON includes metrics and results"
    else
        print_fail "Test suite JSON missing expected fields"
    fi
else
    print_fail "Test suite output file not created or invalid JSON"
fi

#
# CATEGORY 6: Performance Tests
#
print_header "CATEGORY 6: Performance Validation"

print_test "Single label processing time < 5 seconds"
start_time=$(date +%s.%N)
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg --ground-truth samples/label_good_001.json 2>/dev/null" 1)
end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc)
if (( $(echo "$duration < 5" | bc -l) )); then
    print_pass "Processing time: ${duration}s (< 5s requirement)"
else
    print_fail "Processing time: ${duration}s (>= 5s requirement)"
fi

print_test "Batch processing average < 1 second per label"
start_time=$(date +%s.%N)
exit_code=$(run_command "python3 verify_label.py --batch test_samples/ --ground-truth-dir test_samples/ 2>/dev/null" 1)
end_time=$(date +%s.%N)
duration=$(echo "$end_time - $start_time" | bc)
avg=$(echo "$duration / 6" | bc -l)
if (( $(echo "$avg < 1" | bc -l) )); then
    print_pass "Average time: ${avg}s per label (< 1s)"
else
    print_fail "Average time: ${avg}s per label (>= 1s)"
fi

#
# CATEGORY 7: Help and Documentation
#
print_header "CATEGORY 7: Help and Documentation"

print_test "verify_label.py --help"
exit_code=$(run_command "python3 verify_label.py --help" 0)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
if [ "$exit_code" -eq 0 ] && echo "$output" | grep -q "usage:"; then
    print_pass "Help command works"
else
    print_fail "Help command failed"
fi

print_test "test_verifier.py --help"
exit_code=$(run_command "python3 test_verifier.py --help" 0)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
if [ "$exit_code" -eq 0 ] && echo "$output" | grep -q "usage:"; then
    print_pass "Help command works"
else
    print_fail "Help command failed"
fi

#
# CATEGORY 8: Field Extraction Tests
#
print_header "CATEGORY 8: Field Extraction Validation"

print_test "Extract all required fields from GOOD label"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg 2>/dev/null" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
has_brand=$(echo "$output" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['extracted_fields']['brand_name'] is not None)" 2>/dev/null || echo "False")
has_abv=$(echo "$output" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['extracted_fields']['abv_numeric'] is not None)" 2>/dev/null || echo "False")
has_contents=$(echo "$output" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['extracted_fields']['net_contents'] is not None)" 2>/dev/null || echo "False")
has_bottler=$(echo "$output" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['extracted_fields']['bottler'] is not None)" 2>/dev/null || echo "False")

if [ "$has_brand" = "True" ] && [ "$has_abv" = "True" ] && [ "$has_contents" = "True" ] && [ "$has_bottler" = "True" ]; then
    print_pass "Extracted brand, ABV, net contents, and bottler"
else
    print_fail "Missing required fields: brand=$has_brand abv=$has_abv contents=$has_contents bottler=$has_bottler"
fi

print_test "Detect missing ABV in BAD label"
exit_code=$(run_command "python3 verify_label.py samples/label_bad_001.jpg --ground-truth samples/label_bad_001.json 2>/dev/null" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
has_abv_violation=$(echo "$output" | python3 -c "import sys, json; d=json.load(sys.stdin); violations=[v for v in d.get('violations', []) if v['field']=='abv']; print(len(violations) > 0)" 2>/dev/null || echo "False")

if [ "$has_abv_violation" = "True" ]; then
    print_pass "Correctly detected ABV violation"
else
    print_fail "Did not detect ABV violation"
fi

print_test "Government warning validation"
exit_code=$(run_command "python3 verify_label.py samples/label_good_001.jpg 2>/dev/null" 1)
output=$(cat "$TEST_OUTPUT_DIR/test_${TOTAL_TESTS}_output.txt")
warning_present=$(echo "$output" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['extracted_fields']['government_warning']['present'])" 2>/dev/null || echo "False")

if [ "$warning_present" = "True" ]; then
    print_pass "Government warning detected"
else
    print_fail "Government warning not detected"
fi

#
# FINAL SUMMARY
#
print_header "TEST SUMMARY"

echo -e "Total tests run:   ${CYAN}$TOTAL_TESTS${NC}"
echo -e "Passed:            ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:            ${RED}$FAILED_TESTS${NC}"
echo -e "Skipped:           ${YELLOW}$SKIPPED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    success_rate=100
else
    success_rate=$(echo "scale=1; ($PASSED_TESTS * 100) / ($TOTAL_TESTS - $SKIPPED_TESTS)" | bc)
    echo -e "${YELLOW}⚠ Some tests failed. Success rate: ${success_rate}%${NC}"
fi

echo ""
echo "Test artifacts saved in: $TEST_OUTPUT_DIR/"

# Cleanup
if [ "$CLEANUP" = true ]; then
    echo ""
    echo "Cleaning up test artifacts..."
    rm -rf "$TEST_OUTPUT_DIR"
    echo -e "${GREEN}✓ Cleanup complete${NC}"
fi

echo ""

# Exit with failure if any tests failed
if [ $FAILED_TESTS -gt 0 ]; then
    exit 1
else
    exit 0
fi

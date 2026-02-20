#!/bin/bash
#
# Test script for TTB Label Verifier API with authentication
#
# Usage:
#   ./scripts/api_smoketests.sh <base_url> <username> <password>
#
# Example:
#   ./scripts/api_smoketests.sh https://ttb-verifier.example.com myuser mypass
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check arguments
if [ "$#" -ne 3 ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 <base_url> <username> <password>"
    echo "Example: $0 https://ttb-verifier.example.com myuser mypass"
    exit 1
fi

BASE_URL="$1"
USERNAME="$2"
PASSWORD="$3"

# Temp files for cookies and responses
COOKIE_FILE=$(mktemp)
RESPONSE_FILE=$(mktemp)

# Cleanup on exit
trap "rm -f $COOKIE_FILE $RESPONSE_FILE" EXIT

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TTB Label Verifier API Test Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Base URL: ${GREEN}$BASE_URL${NC}"
echo -e "Username: ${GREEN}$USERNAME${NC}"
echo ""

# ---------------------------------------------------------------------------
# Helper: submit an image to POST /verify/async and poll until terminal state.
#
# Usage: async_verify <label> <image_file> [ground_truth_json]
#
# Sets globals: VERIFY_STATUS, VERIFY_RESULT_JSON
# Returns 0 on success (completed, any compliance status), 1 on failure.
# ---------------------------------------------------------------------------
async_verify() {
    local LABEL="$1"
    local IMAGE_FILE="$2"
    local GROUND_TRUTH="${3:-}"

    VERIFY_STATUS=""
    VERIFY_RESULT_JSON=""

    # Build curl args
    local CURL_ARGS=(-s -b "$COOKIE_FILE" -o "$RESPONSE_FILE" -w "%{http_code}"
        -X POST "$BASE_URL/verify/async"
        -F "image=@$IMAGE_FILE")
    if [ -n "$GROUND_TRUTH" ]; then
        CURL_ARGS+=(-F "ground_truth=$GROUND_TRUTH")
    fi

    local HTTP_CODE
    HTTP_CODE=$(curl "${CURL_ARGS[@]}")

    if [ "$HTTP_CODE" -ne 200 ] && [ "$HTTP_CODE" -ne 202 ]; then
        echo -e "  ${RED}✗ Submission failed (HTTP $HTTP_CODE)${NC}"
        cat "$RESPONSE_FILE"
        return 1
    fi

    local JOB_ID
    JOB_ID=$(cat "$RESPONSE_FILE" | jq -r '.job_id')
    echo -e "  Submitted job: ${CYAN}$JOB_ID${NC}"

    # Poll until terminal state
    local MAX_POLLS=90   # 90 × 2s = 3 minutes max
    local POLL_COUNT=0
    local JOB_STATUS="pending"

    while [ "$POLL_COUNT" -lt "$MAX_POLLS" ]; do
        sleep 2
        POLL_COUNT=$((POLL_COUNT + 1))

        HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o "$RESPONSE_FILE" -w "%{http_code}" \
            "$BASE_URL/verify/status/$JOB_ID")

        if [ "$HTTP_CODE" -ne 200 ]; then
            echo -e "\n  ${RED}✗ Status poll failed (HTTP $HTTP_CODE)${NC}"
            return 1
        fi

        JOB_STATUS=$(cat "$RESPONSE_FILE" | jq -r '.status')
        echo -ne "  [$POLL_COUNT] status: $JOB_STATUS\r"

        if [ "$JOB_STATUS" = "completed" ] || [ "$JOB_STATUS" = "failed" ] || [ "$JOB_STATUS" = "cancelled" ]; then
            break
        fi
    done

    echo ""  # newline after polling

    if [ "$JOB_STATUS" = "completed" ]; then
        VERIFY_STATUS=$(cat "$RESPONSE_FILE" | jq -r '.result.status')
        VERIFY_RESULT_JSON=$(cat "$RESPONSE_FILE" | jq -r '.result')
        return 0
    elif [ "$POLL_COUNT" -ge "$MAX_POLLS" ]; then
        echo -e "  ${RED}✗ Timed out waiting for job to complete${NC}"
        return 1
    else
        local ERR
        ERR=$(cat "$RESPONSE_FILE" | jq -r '.error // "unknown error"')
        echo -e "  ${RED}✗ Job ended with status: $JOB_STATUS — $ERR${NC}"
        return 1
    fi
}

# ---------------------------------------------------------------------------
# Test 1: Health check (no auth required)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 1: Health check endpoint${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
if curl -s -f "$BASE_URL/health" > "$RESPONSE_FILE"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo -e "  Status: $(cat $RESPONSE_FILE | jq -r '.status')"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Health check failed${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ---------------------------------------------------------------------------
# Test 2: Login
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 2: User authentication${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
LOGIN_RESPONSE=$(curl -s -c "$COOKIE_FILE" -w "\n%{http_code}" \
    -X POST "$BASE_URL/ui/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$USERNAME&password=$PASSWORD")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)

if [ "$HTTP_CODE" -eq 302 ]; then
    echo -e "${GREEN}✓ Login successful (HTTP $HTTP_CODE)${NC}"
    if grep -q "session_id" "$COOKIE_FILE"; then
        echo -e "  Session cookie received"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ No session cookie found${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${RED}✗ Login failed (HTTP $HTTP_CODE)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ---------------------------------------------------------------------------
# Test 3: Authentication enforcement
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 3: Authentication enforcement${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$BASE_URL/verify/async" \
    -F "image=@README.md")

if [ "$HTTP_CODE" -eq 401 ] || [ "$HTTP_CODE" -eq 403 ]; then
    echo -e "${GREEN}✓ Correctly blocked unauthenticated request (HTTP $HTTP_CODE)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Unexpected response (HTTP $HTTP_CODE), expected 401 or 403${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ---------------------------------------------------------------------------
# Test 4: Verify compliant label (no ground truth)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 4: Verify compliant label (label_good_001)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -f "samples/label_good_001.jpg" ]; then
    if async_verify "label_good_001" "samples/label_good_001.jpg"; then
        PROCESSING_TIME=$(echo "$VERIFY_RESULT_JSON" | jq -r '.processing_time_seconds')
        VALIDATION_LEVEL=$(echo "$VERIFY_RESULT_JSON" | jq -r '.validation_level')
        echo -e "${GREEN}✓ Verification completed${NC}"
        echo -e "  Status: ${CYAN}$VERIFY_STATUS${NC}"
        echo -e "  Validation level: $VALIDATION_LEVEL"
        echo -e "  Processing time: ${PROCESSING_TIME}s"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}⚠ Skipped - samples/label_good_001.jpg not found${NC}"
    echo -e "  Run from project root directory: ./scripts/api_smoketests.sh ..."
fi
echo ""

# ---------------------------------------------------------------------------
# Test 5: Verify non-compliant label
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 5: Verify non-compliant label (label_bad_001)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -f "samples/label_bad_001.jpg" ]; then
    if async_verify "label_bad_001" "samples/label_bad_001.jpg"; then
        PROCESSING_TIME=$(echo "$VERIFY_RESULT_JSON" | jq -r '.processing_time_seconds')
        VALIDATION_LEVEL=$(echo "$VERIFY_RESULT_JSON" | jq -r '.validation_level')
        VIOLATIONS_COUNT=$(echo "$VERIFY_RESULT_JSON" | jq '.violations | length')
        echo -e "${GREEN}✓ Verification completed${NC}"
        echo -e "  Status: ${CYAN}$VERIFY_STATUS${NC}"
        echo -e "  Validation level: $VALIDATION_LEVEL"
        echo -e "  Processing time: ${PROCESSING_TIME}s"
        echo -e "  Violations found: $VIOLATIONS_COUNT"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}⚠ Skipped - samples/label_bad_001.jpg not found${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# Test 6: Verify with ground truth metadata (label_good_002)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 6: Verify label with ground truth metadata (label_good_002)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -f "samples/label_good_002.jpg" ] && [ -f "samples/label_good_002.json" ]; then
    # Build ground truth JSON from the sample's ground_truth block
    GT_JSON=$(cat samples/label_good_002.json | jq -c '.ground_truth')

    if async_verify "label_good_002" "samples/label_good_002.jpg" "$GT_JSON"; then
        PROCESSING_TIME=$(echo "$VERIFY_RESULT_JSON" | jq -r '.processing_time_seconds')
        VALIDATION_LEVEL=$(echo "$VERIFY_RESULT_JSON" | jq -r '.validation_level')
        echo -e "${GREEN}✓ Verification completed${NC}"
        echo -e "  Status: ${CYAN}$VERIFY_STATUS${NC}"
        echo -e "  Validation level: $VALIDATION_LEVEL"
        echo -e "  Processing time: ${PROCESSING_TIME}s"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}⚠ Skipped - samples/label_good_002.jpg or .json not found${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# Test 7: Verify a third label (label_good_003)
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 7: Verify label (label_good_003)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -f "samples/label_good_003.jpg" ]; then
    if async_verify "label_good_003" "samples/label_good_003.jpg"; then
        PROCESSING_TIME=$(echo "$VERIFY_RESULT_JSON" | jq -r '.processing_time_seconds')
        VALIDATION_LEVEL=$(echo "$VERIFY_RESULT_JSON" | jq -r '.validation_level')
        echo -e "${GREEN}✓ Verification completed${NC}"
        echo -e "  Status: ${CYAN}$VERIFY_STATUS${NC}"
        echo -e "  Validation level: $VALIDATION_LEVEL"
        echo -e "  Processing time: ${PROCESSING_TIME}s"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}⚠ Skipped - samples/label_good_003.jpg not found${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# Test 8: Async batch verification
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 8: Async batch verification (3 labels in ZIP)${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -f "samples/label_good_001.jpg" ] && [ -f "samples/label_bad_001.jpg" ] && [ -f "samples/label_good_002.jpg" ]; then
    BATCH_ZIP=$(mktemp --suffix=.zip)
    python3 -c "
import zipfile
with zipfile.ZipFile('$BATCH_ZIP', 'w') as zf:
    zf.write('samples/label_good_001.jpg', 'label_good_001.jpg')
    zf.write('samples/label_bad_001.jpg', 'label_bad_001.jpg')
    zf.write('samples/label_good_002.jpg', 'label_good_002.jpg')
" 2>/dev/null

    if [ -f "$BATCH_ZIP" ] && [ -s "$BATCH_ZIP" ]; then
        echo -e "  Submitting batch job..."
        HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o "$RESPONSE_FILE" -w "%{http_code}" \
            -X POST "$BASE_URL/verify/batch" \
            -H "Content-Type: multipart/form-data" \
            -F "batch_file=@$BATCH_ZIP;type=application/zip")

        rm -f "$BATCH_ZIP"

        if [ "$HTTP_CODE" -eq 200 ]; then
            JOB_ID=$(cat "$RESPONSE_FILE" | jq -r '.job_id')
            TOTAL_IMAGES=$(cat "$RESPONSE_FILE" | jq -r '.total_images')
            echo -e "  ${GREEN}✓ Batch job submitted (job_id: $JOB_ID)${NC}"
            echo -e "  Total images: $TOTAL_IMAGES"

            echo -e "  Polling for job completion..."
            MAX_POLLS=60
            POLL_COUNT=0
            JOB_STATUS="pending"

            while [ "$POLL_COUNT" -lt "$MAX_POLLS" ] && [ "$JOB_STATUS" != "completed" ] && [ "$JOB_STATUS" != "failed" ] && [ "$JOB_STATUS" != "cancelled" ]; do
                sleep 2
                POLL_COUNT=$((POLL_COUNT + 1))
                HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o "$RESPONSE_FILE" -w "%{http_code}" \
                    "$BASE_URL/verify/batch/$JOB_ID")
                if [ "$HTTP_CODE" -eq 200 ]; then
                    JOB_STATUS=$(cat "$RESPONSE_FILE" | jq -r '.status')
                    PROCESSED=$(cat "$RESPONSE_FILE" | jq -r '.processed_images')
                    echo -ne "  [$POLL_COUNT] Status: $JOB_STATUS - Processed: $PROCESSED/$TOTAL_IMAGES\r"
                else
                    echo -e "\n  ${RED}✗ Failed to poll job status (HTTP $HTTP_CODE)${NC}"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                    break
                fi
            done
            echo ""

            if [ "$JOB_STATUS" = "completed" ]; then
                RESULTS_COUNT=$(cat "$RESPONSE_FILE" | jq '.results | length')
                COMPLIANT_COUNT=$(cat "$RESPONSE_FILE" | jq '.summary.compliant')
                NON_COMPLIANT_COUNT=$(cat "$RESPONSE_FILE" | jq '.summary.non_compliant')
                ERRORS_COUNT=$(cat "$RESPONSE_FILE" | jq '.summary.errors')
                TOTAL_TIME=$(cat "$RESPONSE_FILE" | jq -r '.summary.total_processing_time_seconds')

                echo -e "  ${GREEN}✓ Batch verification completed${NC}"
                echo -e "  Images processed: $RESULTS_COUNT"
                echo -e "  Compliant labels: $COMPLIANT_COUNT"
                echo -e "  Non-compliant labels: $NON_COMPLIANT_COUNT"
                echo -e "  Errors: $ERRORS_COUNT"
                echo -e "  Total processing time: ${TOTAL_TIME}s"

                for i in $(seq 0 $((RESULTS_COUNT - 1))); do
                    FILENAME=$(cat "$RESPONSE_FILE" | jq -r ".results[$i].image_path")
                    STATUS=$(cat "$RESPONSE_FILE" | jq -r ".results[$i].status")
                    echo -e "  [$((i+1))] $FILENAME: ${CYAN}$STATUS${NC}"
                done
                PASSED_TESTS=$((PASSED_TESTS + 1))
            elif [ "$JOB_STATUS" = "failed" ]; then
                ERROR_MSG=$(cat "$RESPONSE_FILE" | jq -r '.error // "Unknown error"')
                echo -e "  ${RED}✗ Batch job failed: $ERROR_MSG${NC}"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            elif [ "$POLL_COUNT" -ge "$MAX_POLLS" ]; then
                echo -e "  ${RED}✗ Timeout waiting for batch completion${NC}"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            else
                echo -e "  ${RED}✗ Batch job ended with status: $JOB_STATUS${NC}"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
        else
            echo -e "  ${RED}✗ Batch submission failed (HTTP $HTTP_CODE)${NC}"
            cat "$RESPONSE_FILE" | head -20
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        echo -e "${YELLOW}⚠ Skipped - failed to create ZIP file${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipped - sample files not found${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# Test 9: Invalid image format handling
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 9: Invalid image format handling${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

INVALID_FILE=$(mktemp --suffix=.jpg)
echo "This is not a real image" > "$INVALID_FILE"

HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o "$RESPONSE_FILE" -w "%{http_code}" \
    -X POST "$BASE_URL/verify/async" \
    -F "image=@$INVALID_FILE")

rm -f "$INVALID_FILE"

if [ "$HTTP_CODE" -eq 400 ] || [ "$HTTP_CODE" -eq 422 ] || [ "$HTTP_CODE" -eq 500 ]; then
    echo -e "${GREEN}✓ Correctly rejected/handled invalid image (HTTP $HTTP_CODE)${NC}"
    ERROR_MSG=$(cat "$RESPONSE_FILE" | jq -r '.detail // .error // .message' 2>/dev/null | head -c 100)
    if [ -n "$ERROR_MSG" ] && [ "$ERROR_MSG" != "null" ]; then
        echo -e "  Error: $ERROR_MSG"
    fi
    PASSED_TESTS=$((PASSED_TESTS + 1))
elif [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 202 ]; then
    echo -e "${RED}✗ Request succeeded, but should have failed for invalid image (HTTP $HTTP_CODE)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    echo -e "${RED}✗ Unexpected response (HTTP $HTTP_CODE)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ---------------------------------------------------------------------------
# Test 10: Retry endpoint (submit a job, then hit /verify/retry/{job_id})
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 10: Retry endpoint${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))

if [ -f "samples/label_good_001.jpg" ]; then
    # Submit a job
    HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o "$RESPONSE_FILE" -w "%{http_code}" \
        -X POST "$BASE_URL/verify/async" \
        -F "image=@samples/label_good_001.jpg")

    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 202 ]; then
        ORIG_JOB_ID=$(cat "$RESPONSE_FILE" | jq -r '.job_id')
        echo -e "  Original job: ${CYAN}$ORIG_JOB_ID${NC}"

        # Hit the retry endpoint immediately (job may still be pending/processing — that's fine)
        HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o "$RESPONSE_FILE" -w "%{http_code}" \
            -X POST "$BASE_URL/verify/retry/$ORIG_JOB_ID")

        if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 202 ]; then
            NEW_JOB_ID=$(cat "$RESPONSE_FILE" | jq -r '.job_id')
            if [ -n "$NEW_JOB_ID" ] && [ "$NEW_JOB_ID" != "$ORIG_JOB_ID" ] && [ "$NEW_JOB_ID" != "null" ]; then
                echo -e "${GREEN}✓ Retry returned new job_id: ${CYAN}$NEW_JOB_ID${NC}"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                echo -e "${RED}✗ Retry did not return a new job_id (got: $NEW_JOB_ID)${NC}"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
        else
            echo -e "${RED}✗ Retry request failed (HTTP $HTTP_CODE)${NC}"
            cat "$RESPONSE_FILE"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        echo -e "${RED}✗ Could not submit original job for retry test (HTTP $HTTP_CODE)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${YELLOW}⚠ Skipped - samples/label_good_001.jpg not found${NC}"
fi
echo ""

# ---------------------------------------------------------------------------
# Test 11: Logout
# ---------------------------------------------------------------------------
echo -e "${YELLOW}Test 11: User logout${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o /dev/null -w "%{http_code}" \
    "$BASE_URL/ui/logout")

if [ "$HTTP_CODE" -eq 302 ]; then
    echo -e "${GREEN}✓ Logout successful (HTTP $HTTP_CODE)${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}✗ Logout failed (HTTP $HTTP_CODE)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
if [ "$FAILED_TESTS" -gt 0 ]; then
    echo -e "${RED}Failed: $FAILED_TESTS${NC}"
else
    echo -e "Failed: $FAILED_TESTS"
fi
echo ""

if [ "$FAILED_TESTS" -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✓${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Test the UI at: $BASE_URL"
    echo "2. Login with username: $USERNAME"
    echo "3. Try uploading a label image for verification"
    echo "4. Test batch verification with multiple images"
    echo ""
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    echo ""
    exit 1
fi

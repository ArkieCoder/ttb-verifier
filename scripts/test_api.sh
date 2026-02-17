#!/bin/bash
#
# Test script for TTB Label Verifier API with authentication
#
# Usage:
#   ./scripts/test_api.sh <base_url> <username> <password>
#
# Example:
#   ./scripts/test_api.sh https://ttb-verifier.example.com myuser mypass
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}TTB Label Verifier API Test Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Base URL: ${GREEN}$BASE_URL${NC}"
echo -e "Username: ${GREEN}$USERNAME${NC}"
echo ""

# Test 1: Health check (no auth required)
echo -e "${YELLOW}[1/5] Testing health endpoint...${NC}"
if curl -s -f "$BASE_URL/health" > "$RESPONSE_FILE"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo -e "Response: $(cat $RESPONSE_FILE | jq -c '.status, .backends')"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi
echo ""

# Test 2: Login
echo -e "${YELLOW}[2/5] Testing login...${NC}"
LOGIN_RESPONSE=$(curl -s -c "$COOKIE_FILE" -w "\n%{http_code}" \
    -X POST "$BASE_URL/ui/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$USERNAME&password=$PASSWORD")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n 1)
BODY=$(echo "$LOGIN_RESPONSE" | head -n -1)

if [ "$HTTP_CODE" -eq 302 ]; then
    echo -e "${GREEN}✓ Login successful (HTTP $HTTP_CODE)${NC}"
    
    # Check if session cookie was set
    if grep -q "session_id" "$COOKIE_FILE"; then
        echo -e "${GREEN}✓ Session cookie received${NC}"
    else
        echo -e "${RED}✗ No session cookie found${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Login failed (HTTP $HTTP_CODE)${NC}"
    echo "$BODY"
    exit 1
fi
echo ""

# Test 3: Access protected endpoint without auth (should fail)
echo -e "${YELLOW}[3/5] Testing protected endpoint without auth (should fail)...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "$BASE_URL/verify" \
    -F "image=@README.md")

if [ "$HTTP_CODE" -eq 401 ] || [ "$HTTP_CODE" -eq 403 ]; then
    echo -e "${GREEN}✓ Correctly blocked unauthenticated request (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ Unexpected response (HTTP $HTTP_CODE), expected 401 or 403${NC}"
    exit 1
fi
echo ""

# Test 4: Access protected endpoint with auth (should succeed or fail with validation error)
echo -e "${YELLOW}[4/5] Testing protected endpoint with auth...${NC}"

# Create a simple test image (1x1 pixel PNG)
TEST_IMAGE=$(mktemp --suffix=.png)
echo "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==" | base64 -d > "$TEST_IMAGE"

HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o "$RESPONSE_FILE" -w "%{http_code}" \
    -X POST "$BASE_URL/verify" \
    -F "image=@$TEST_IMAGE" \
    -F "ocr_backend=tesseract")

rm -f "$TEST_IMAGE"

if [ "$HTTP_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Authenticated request accepted (HTTP $HTTP_CODE)${NC}"
    echo -e "Response status: $(cat $RESPONSE_FILE | jq -r '.status')"
    echo -e "Validation level: $(cat $RESPONSE_FILE | jq -r '.validation_level')"
    echo -e "Processing time: $(cat $RESPONSE_FILE | jq -r '.processing_time_seconds')s"
else
    echo -e "${RED}✗ Request failed (HTTP $HTTP_CODE)${NC}"
    cat "$RESPONSE_FILE"
    exit 1
fi
echo ""

# Test 5: Logout
echo -e "${YELLOW}[5/5] Testing logout...${NC}"
HTTP_CODE=$(curl -s -b "$COOKIE_FILE" -o /dev/null -w "%{http_code}" \
    "$BASE_URL/ui/logout")

if [ "$HTTP_CODE" -eq 302 ]; then
    echo -e "${GREEN}✓ Logout successful (HTTP $HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ Logout failed (HTTP $HTTP_CODE)${NC}"
    exit 1
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All tests passed! ✓${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Test the UI at: $BASE_URL"
echo "2. Login with username: $USERNAME"
echo "3. Try uploading a label image for verification"
echo ""

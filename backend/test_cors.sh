#!/bin/bash

# CORS Configuration Test Script
# Tests CORS headers from the FastAPI backend

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-http://localhost:5173}"

echo -e "${BLUE}🧪 Testing CORS Configuration${NC}"
echo -e "${BLUE}Backend URL: ${BACKEND_URL}${NC}"
echo -e "${BLUE}Frontend Origin: ${FRONTEND_ORIGIN}${NC}"
echo ""

# Test 1: Preflight request (OPTIONS)
echo -e "${YELLOW}Test 1: Preflight Request (OPTIONS)${NC}"
echo "Simulating browser preflight for POST request..."
RESPONSE=$(curl -s -X OPTIONS "${BACKEND_URL}/optimize" \
  -H "Origin: ${FRONTEND_ORIGIN}" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type" \
  -i)

echo "$RESPONSE"
echo ""

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin: ${FRONTEND_ORIGIN}"; then
    echo -e "${GREEN}✓ Allow-Origin header present${NC}"
else
    echo -e "${RED}✗ Allow-Origin header missing or incorrect${NC}"
fi

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Methods.*POST"; then
    echo -e "${GREEN}✓ POST method allowed${NC}"
else
    echo -e "${RED}✗ POST method not allowed${NC}"
fi

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Headers.*content-type"; then
    echo -e "${GREEN}✓ Content-Type header allowed${NC}"
else
    echo -e "${RED}✗ Content-Type header not allowed${NC}"
fi

echo ""

# Test 2: Actual GET request
echo -e "${YELLOW}Test 2: Actual GET Request${NC}"
echo "Testing GET /health endpoint..."
RESPONSE=$(curl -s -X GET "${BACKEND_URL}/health" \
  -H "Origin: ${FRONTEND_ORIGIN}" \
  -i)

echo "$RESPONSE"
echo ""

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin"; then
    echo -e "${GREEN}✓ CORS headers present on GET request${NC}"
else
    echo -e "${RED}✗ CORS headers missing on GET request${NC}"
fi

echo ""

# Test 3: Disallowed origin
echo -e "${YELLOW}Test 3: Disallowed Origin${NC}"
echo "Testing request from disallowed origin..."
RESPONSE=$(curl -s -X GET "${BACKEND_URL}/health" \
  -H "Origin: http://evil.com" \
  -i)

echo "$RESPONSE"
echo ""

if echo "$RESPONSE" | grep -q "Access-Control-Allow-Origin: http://evil.com"; then
    echo -e "${RED}✗ SECURITY ISSUE: Disallowed origin accepted!${NC}"
else
    echo -e "${GREEN}✓ Disallowed origin correctly rejected${NC}"
fi

echo ""
echo -e "${BLUE}CORS test complete!${NC}"

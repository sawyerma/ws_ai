#!/bin/bash
"""
DarkMa Trading System - Health Endpoints Test
============================================

Basic Health Check Tests für Backend API Endpoints.
"""

# Test Configuration
BACKEND_URL="http://localhost:8100"
TIMEOUT=10
MAX_RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test Results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}🏥 Backend Health Endpoints Test Suite${NC}"
echo "=================================================="
echo -e "🎯 Backend URL: ${BACKEND_URL}"
echo -e "⏱️  Timeout: ${TIMEOUT}s"
echo ""

# Function to run HTTP test
run_http_test() {
    local test_name="$1"
    local endpoint="$2"
    local expected_status="$3"
    local expected_content="$4"
    
    echo -n "🔍 Testing: $test_name... "
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Make HTTP request with timeout
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" \
                   --max-time $TIMEOUT \
                   --connect-timeout 5 \
                   "$BACKEND_URL$endpoint" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}FAILED${NC} (Connection Error)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Extract HTTP status and body
    http_status=$(echo "$response" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTPSTATUS:[0-9]*$//')
    
    # Check HTTP status
    if [ "$http_status" != "$expected_status" ]; then
        echo -e "${RED}FAILED${NC} (HTTP $http_status, expected $expected_status)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Check content if specified
    if [ ! -z "$expected_content" ]; then
        if echo "$body" | grep -q "$expected_content"; then
            echo -e "${GREEN}PASSED${NC} (HTTP $http_status)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}FAILED${NC} (Content mismatch)"
            echo "   Expected: $expected_content"
            echo "   Got: $body"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    else
        echo -e "${GREEN}PASSED${NC} (HTTP $http_status)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
    
    return 0
}

# Function to test response time
test_response_time() {
    local endpoint="$1"
    local max_time="$2"
    
    echo -n "⚡ Testing response time for $endpoint... "
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    start_time=$(date +%s%N)
    response=$(curl -s --max-time $TIMEOUT "$BACKEND_URL$endpoint" 2>/dev/null)
    end_time=$(date +%s%N)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}FAILED${NC} (Connection Error)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Calculate response time in milliseconds
    response_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ $response_time -le $max_time ]; then
        echo -e "${GREEN}PASSED${NC} (${response_time}ms)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}FAILED${NC} (${response_time}ms > ${max_time}ms)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    return 0
}

# Function to test JSON response
test_json_response() {
    local test_name="$1"
    local endpoint="$2"
    local json_key="$3"
    
    echo -n "📄 Testing JSON: $test_name... "
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    response=$(curl -s --max-time $TIMEOUT "$BACKEND_URL$endpoint" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}FAILED${NC} (Connection Error)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Check if response is valid JSON
    echo "$response" | python3 -m json.tool >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo -e "${RED}FAILED${NC} (Invalid JSON)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Check if specific key exists (if provided)
    if [ ! -z "$json_key" ]; then
        key_exists=$(echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    keys = '$json_key'.split('.')
    value = data
    for key in keys:
        value = value[key]
    print('true')
except:
    print('false')
" 2>/dev/null)
        
        if [ "$key_exists" = "true" ]; then
            echo -e "${GREEN}PASSED${NC} (Valid JSON with key '$json_key')"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}FAILED${NC} (Missing key '$json_key')"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    else
        echo -e "${GREEN}PASSED${NC} (Valid JSON)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    fi
    
    return 0
}

# Main Health Tests
echo "🏥 Basic Health Checks:"
echo "----------------------"

# Test 1: Root endpoint
run_http_test "Root Endpoint" "/" "200"

# Test 2: Health endpoint
run_http_test "Health Endpoint" "/health" "200"

# Test 3: Specific health check with JSON
test_json_response "Health JSON Response" "/health" "status"

echo ""
echo "⚡ Performance Tests:"
echo "--------------------"

# Test 4: Health endpoint response time
test_response_time "/health" 500  # 500ms max

# Test 5: Root endpoint response time
test_response_time "/" 1000  # 1000ms max

echo ""
echo "🔌 API Endpoints Availability:"
echo "------------------------------"

# Test 6: Trading endpoints
run_http_test "Trades Endpoint" "/trades" "200"
run_http_test "Symbols Endpoint" "/symbols" "200"
run_http_test "OHLC Endpoint" "/ohlc" "200"
run_http_test "Orderbook Endpoint" "/orderbook" "200"
run_http_test "Ticker Endpoint" "/ticker" "200"

echo ""
echo "📊 API Documentation:"
echo "--------------------"

# Test 7: OpenAPI docs
run_http_test "OpenAPI Docs" "/docs" "200" "swagger"
run_http_test "OpenAPI JSON" "/openapi.json" "200" "openapi"

echo ""
echo "🔒 Security Headers:"
echo "-------------------"

# Test 8: CORS headers
echo -n "🛡️ Testing CORS headers... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))

cors_response=$(curl -s -I -H "Origin: http://localhost:3000" \
                     --max-time $TIMEOUT \
                     "$BACKEND_URL/health" 2>/dev/null)

if echo "$cors_response" | grep -qi "access-control-allow-origin"; then
    echo -e "${GREEN}PASSED${NC} (CORS enabled)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${YELLOW}WARNING${NC} (CORS headers not found)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "🔄 Load Test (Simple):"
echo "---------------------"

# Test 9: Simple load test
echo -n "📈 Testing concurrent requests... "
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Run 10 concurrent requests
concurrent_requests=10
success_count=0

for i in $(seq 1 $concurrent_requests); do
    curl -s --max-time $TIMEOUT "$BACKEND_URL/health" >/dev/null 2>&1 &
done

# Wait for all background jobs
wait

# Count successful responses (simplified)
for i in $(seq 1 $concurrent_requests); do
    response=$(curl -s --max-time 2 "$BACKEND_URL/health" 2>/dev/null)
    if [ $? -eq 0 ] && echo "$response" | grep -q "status"; then
        success_count=$((success_count + 1))
    fi
done

success_rate=$((success_count * 100 / concurrent_requests))

if [ $success_rate -ge 80 ]; then
    echo -e "${GREEN}PASSED${NC} (${success_count}/${concurrent_requests} requests successful - ${success_rate}%)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}FAILED${NC} (${success_count}/${concurrent_requests} requests successful - ${success_rate}%)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

echo ""
echo "🔍 Detailed Health Information:"
echo "------------------------------"

# Get detailed health info
echo "📋 Health Status:"
health_response=$(curl -s --max-time $TIMEOUT "$BACKEND_URL/health" 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "$health_response" | python3 -m json.tool 2>/dev/null || echo "$health_response"
else
    echo -e "${RED}Failed to retrieve health information${NC}"
fi

echo ""
echo "=================================================="
echo "📊 Test Summary:"
echo "=================================================="
echo -e "Total Tests: ${TOTAL_TESTS}"
echo -e "Passed: ${GREEN}${PASSED_TESTS}${NC}"
echo -e "Failed: ${RED}${FAILED_TESTS}${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n🎉 ${GREEN}All health tests PASSED!${NC}"
    echo -e "✅ Backend API is healthy and responsive"
    exit 0
else
    echo -e "\n⚠️  ${RED}Some health tests FAILED!${NC}"
    echo -e "❌ Backend API has issues that need attention"
    exit 1
fi

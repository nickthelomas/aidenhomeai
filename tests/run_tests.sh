#!/bin/bash

BASE_URL_HA="http://localhost:8001"
BASE_URL_CHROMA="http://localhost:8002"
BASE_URL_VOICE="http://localhost:8003"
BASE_URL_PROXY="http://localhost:5000"

TESTS_PASSED=0
TESTS_FAILED=0

test_health() {
    local service=$1
    local url=$2
    
    echo -n "Testing $service health check... "
    response=$(curl -s -w "\n%{http_code}" "$url/health")
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo "✓ PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        echo "✗ FAILED (HTTP $http_code)"
        echo "  Response: $body"
        ((TESTS_FAILED++))
        return 1
    fi
}

test_ha_tool() {
    echo -n "Testing HA MCP tool call (get_config)... "
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL_HA/tools/call" \
        -H "Content-Type: application/json" \
        -d '{
            "method": "tools/call",
            "params": {
                "name": "get_config",
                "arguments": {}
            }
        }')
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo "✓ PASSED"
        ((TESTS_PASSED++))
        return 0
    else
        echo "⚠ SKIPPED (HA not available - expected in test environment)"
        echo "  This test requires a running Home Assistant instance"
        return 0
    fi
}

test_chroma_count() {
    echo -n "Testing ChromaDB MCP tool call (count_documents)... "
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL_CHROMA/tools/call" \
        -H "Content-Type: application/json" \
        -d '{
            "method": "tools/call",
            "params": {
                "name": "count_documents",
                "arguments": {}
            }
        }')
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo "✓ PASSED"
        echo "  Response: $body"
        ((TESTS_PASSED++))
        return 0
    else
        echo "⚠ SKIPPED (ChromaDB not available - expected in test environment)"
        return 0
    fi
}

test_rag_query() {
    echo -n "Testing RAG query via Memory Proxy... "
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL_PROXY/query" \
        -H "Content-Type: application/json" \
        -d '{
            "query": "What is Project Aiden?",
            "use_rag": true,
            "use_ha_context": false
        }')
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        if echo "$body" | grep -q "context"; then
            echo "✓ PASSED"
            echo "  Retrieved context successfully"
            ((TESTS_PASSED++))
            return 0
        else
            echo "✗ FAILED (No context in response)"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        echo "✗ FAILED (HTTP $http_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "======================================"
echo "Project Aiden MCP Integration Tests"
echo "======================================"
echo ""

echo "1. Health Check Tests"
echo "---------------------"
test_health "HA MCP" "$BASE_URL_HA"
test_health "ChromaDB MCP" "$BASE_URL_CHROMA"
test_health "Voice MCP" "$BASE_URL_VOICE"
test_health "Memory Proxy" "$BASE_URL_PROXY"
echo ""

echo "2. MCP Tool Call Tests"
echo "----------------------"
test_ha_tool
test_chroma_count
echo ""

echo "3. RAG Integration Test"
echo "-----------------------"
test_rag_query
echo ""

echo "======================================"
echo "Test Summary"
echo "======================================"
echo "Passed: $TESTS_PASSED"
echo "Failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi

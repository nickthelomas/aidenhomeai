#!/bin/bash

export HA_URL=${HA_URL:-"http://homeassistant.local:8123"}
export HA_TOKEN=${HA_TOKEN:-"dev_token"}
export CHROMA_URL=${CHROMA_URL:-"http://localhost:8002"}
export COLLECTION_NAME=${COLLECTION_NAME:-"aiden"}
export WYOMING_HOST=${WYOMING_HOST:-"localhost"}
export WYOMING_PORT=${WYOMING_PORT:-"10300"}
export OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-""}
export MODEL_NAME=${MODEL_NAME:-"anthropic/claude-3-haiku"}

export HA_MCP_PORT=8001
export CHROMA_MCP_PORT=8002
export VOICE_MCP_PORT=8003
export MEMORY_PROXY_PORT=5000

export HA_MCP_URL="http://localhost:${HA_MCP_PORT}"
export CHROMA_MCP_URL="http://localhost:${CHROMA_MCP_PORT}"
export VOICE_MCP_URL="http://localhost:${VOICE_MCP_PORT}"

echo "Starting Project Aiden MCP Services..."
echo "======================================"
echo "HA MCP:        http://localhost:${HA_MCP_PORT}"
echo "ChromaDB MCP:  http://localhost:${CHROMA_MCP_PORT}"
echo "Voice MCP:     http://localhost:${VOICE_MCP_PORT}"
echo "Memory Proxy:  http://localhost:${MEMORY_PROXY_PORT}"
echo "======================================"

python servers/ha_mcp/main.py &
HA_PID=$!
echo "Started HA MCP (PID: $HA_PID)"

python servers/chroma_mcp/main.py &
CHROMA_PID=$!
echo "Started ChromaDB MCP (PID: $CHROMA_PID)"

python servers/voice_mcp/main.py &
VOICE_PID=$!
echo "Started Voice MCP (PID: $VOICE_PID)"

sleep 2

python services/memory_proxy/main.py

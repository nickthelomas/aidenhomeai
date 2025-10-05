#!/bin/bash

set -e

export HA_MCP_PORT=8001
export CHROMA_MCP_PORT=8002
export VOICE_MCP_PORT=8003
export MEMORY_PROXY_PORT=8000

export HA_MCP_URL="http://localhost:${HA_MCP_PORT}"
export CHROMA_MCP_URL="http://localhost:${CHROMA_MCP_PORT}"
export VOICE_MCP_URL="http://localhost:${VOICE_MCP_PORT}"

if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

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

python services/memory_proxy/main.py &
PROXY_PID=$!
echo "Started Memory Proxy (PID: $PROXY_PID)"

echo ""
echo "All services started. Press Ctrl+C to stop all services."

trap "kill $HA_PID $CHROMA_PID $VOICE_PID $PROXY_PID 2>/dev/null; exit" INT TERM

wait

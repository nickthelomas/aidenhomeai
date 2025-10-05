# Project Aiden Integration Tests

This directory contains curl-based integration tests for all MCP services.

## Test Endpoints

### Health Checks
All services expose a `/health` endpoint:
- HA MCP: `http://localhost:8001/health`
- ChromaDB MCP: `http://localhost:8002/health`
- Voice MCP: `http://localhost:8003/health`
- Memory Proxy: `http://localhost:8000/health`

### MCP Tool Calls

All MCP servers expose tools at `/tools/call` via HTTP/SSE.

#### HA MCP Tools (Port 8001)
```bash
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_config",
      "arguments": {}
    }
  }'
```

Available tools:
- `get_entity_state` - Get entity state
- `call_service` - Call HA service
- `get_states` - Get all states
- `get_config` - Get HA configuration

#### ChromaDB MCP Tools (Port 8002)
```bash
curl -X POST http://localhost:8002/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "count_documents",
      "arguments": {}
    }
  }'
```

Available tools:
- `query_documents` - RAG query
- `get_document` - Get by ID
- `count_documents` - Count docs
- `search_by_metadata` - Metadata search

#### Voice MCP Tools (Port 8003)
```bash
curl -X POST http://localhost:8003/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_wyoming_info",
      "arguments": {}
    }
  }'
```

Available tools:
- `transcribe_audio` - Transcribe audio
- `get_wyoming_info` - Get server info
- `test_wyoming_connection` - Test connection

#### Memory Proxy Orchestrator (Port 8000)
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Project Aiden?",
    "use_rag": true,
    "use_ha_context": false
  }'
```

## Running Tests

### Prerequisites
1. Start all services: `./run_all.sh`
2. Ingest sample documents: `python ingestion/ingest.py`

### Execute Tests
```bash
cd tests
chmod +x run_tests.sh
./run_tests.sh
```

## Test Sequence

1. **Health Checks** - Verify all 4 services are running
2. **MCP Tool Calls** - Test HA and ChromaDB tool execution
3. **RAG Integration** - Verify document retrieval through Memory Proxy

## Expected Behavior

- Health checks should return HTTP 200 with JSON status
- Tool calls require external dependencies (HA, ChromaDB) - may be skipped in test environment
- RAG query should aggregate context from ChromaDB and return structured response

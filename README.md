# Project Aiden: MCP-Integrated Smart Home AI

A service-oriented architecture implementing Model Context Protocol (MCP) for smart home automation, RAG, and voice processing.

## Architecture

This system implements a distributed MCP architecture with:
- **3 MCP Servers** exposing tools via FastAPI + FastMCP (HTTP/SSE transport)
- **1 Memory Proxy** orchestrator that aggregates context and calls LLM
- **1 Ingestion CLI** for seeding the vector database

All services communicate via HTTP/SSE following MCP protocol standards.

## Services & Ports

| Service | Port | Purpose | Endpoints |
|---------|------|---------|-----------|
| **HA MCP** | 8101 | Home Assistant integration | `/tools`, `/healthz` |
| **ChromaDB MCP** | 8102 | Vector database RAG | `/tools`, `/healthz` |
| **Voice MCP** | 8103 | Wyoming-Whisper voice processing | `/tools`, `/healthz` |
| **Memory Proxy** | 8104 | Orchestrator & LLM integration | `/query`, `/healthz` |

## Folder Structure

```
/opt/aiden/
├── ha_mcp/main.py          # Home Assistant MCP server
├── chroma_mcp/main.py      # ChromaDB MCP server
├── voice_mcp/main.py       # Wyoming MCP server
├── memory_proxy/main.py    # Orchestrator
├── ingestion/ingest.py     # ChromaDB ingestion CLI
├── documents/              # Document source for RAG
├── tests/run_tests.sh      # Integration tests
├── run_all.sh              # Start all services
├── requirements.txt        # Pinned dependencies
└── .env                    # Environment configuration
```

## Environment Variables

All configuration via environment variables (copy `.env.example` to `.env`):

### Required for Production
- `HA_URL` - Home Assistant URL (default: `http://homeassistant.local:8123`)
- `HA_TOKEN` - Home Assistant long-lived access token
- `CHROMA_URL` - ChromaDB URL (default: `http://chromadb:8000`)
- `WYOMING_HOST` - Wyoming server host (default: `wyoming`)
- `WYOMING_PORT` - Wyoming server port (default: `10300`)

### Optional
- `OPENROUTER_API_KEY` - OpenRouter API key for LLM
- `MODEL_NAME` - LLM model (default: `anthropic/claude-3-haiku`)
- `COLLECTION_NAME` - ChromaDB collection (default: `aiden`)

### Service Ports (configured via env)
- `HA_MCP_PORT=8101`
- `CHROMA_MCP_PORT=8102`
- `VOICE_MCP_PORT=8103`
- `MEMORY_PROXY_PORT=8104`

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Ingest Documents
```bash
python ingestion/ingest.py --docs ./documents --collection aiden
```

### 4. Start All Services
```bash
chmod +x run_all.sh
./run_all.sh
```

### 5. Run Tests
```bash
chmod +x tests/run_tests.sh
./tests/run_tests.sh
```

## Service Details

### Home Assistant MCP (`ha_mcp`)
Exposes Home Assistant capabilities as MCP tools:
- `get_entity_state(entity_id)` - Get entity state
- `call_service(domain, service, entity_id, service_data)` - Call HA service
- `get_states()` - Get all entity states
- `get_config()` - Get HA configuration

**Health Check**: `GET /healthz` → `{"ok": true}`

### ChromaDB MCP (`chroma_mcp`)
Provides vector database RAG functionality:
- `query_documents(query_text, n_results)` - Semantic search
- `get_document(document_id)` - Retrieve by ID
- `count_documents()` - Get total count
- `search_by_metadata(metadata_filter, n_results)` - Metadata search

**Health Check**: `GET /healthz` → `{"ok": true}`

### Voice MCP (`voice_mcp`)
Wyoming-Whisper integration for voice:
- `transcribe_audio(audio_base64)` - Transcribe audio
- `get_wyoming_info()` - Server info
- `test_wyoming_connection()` - Connection test

**Health Check**: `GET /healthz` → `{"ok": true}`

### Memory Proxy (`memory_proxy`)
Orchestrates MCP tools and LLM:
- `POST /query` - Main query endpoint
  - Aggregates RAG context from ChromaDB MCP
  - Gathers HA context from HA MCP
  - Calls LLM with combined context

**Health Check**: `GET /healthz` → `{"ok": true}`

### Ingestion CLI (`ingestion`)
Seeds ChromaDB with documents:
```bash
python ingestion/ingest.py --docs ./documents --collection aiden
```

Uses MiniLM embedding model (all-MiniLM-L6-v2) for semantic search.

## Testing

See `tests/README.md` for detailed test documentation.

Tests verify:
1. Health checks (`/healthz`) for all 4 services → `{"ok": true}`
2. MCP tool calls to HA and ChromaDB
3. RAG ingestion and retrieval (echoes actual retrieved text)

## Transfer to Ubuntu Server

See `DEPLOY_NOTES.md` for complete deployment instructions targeting `/opt/aiden` on Ubuntu Server with Docker Compose.

## MCP Protocol

All MCP servers expose tools at `/tools` via HTTP/SSE transport following MCP specification:
- Tool discovery via SSE
- Tool calls via POST to `/tools/call`
- Standard JSON-RPC 2.0 message format

## Version Pins

See `requirements.txt` for pinned dependency versions to avoid drift:
- fastapi==0.118.0
- fastmcp==2.12.4
- chromadb==1.1.0
- httpx==0.28.1
- pydantic==2.11.10
- uvicorn==0.37.0
- python-dotenv==1.1.1
- sse-starlette==3.0.2
- sentence-transformers==3.3.1

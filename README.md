# Project Aiden: MCP-Integrated Smart Home AI

A service-oriented architecture implementing Model Context Protocol (MCP) for smart home automation, RAG, and voice processing.

## Architecture

This system implements a distributed MCP architecture with:
- **3 MCP Servers** exposing tools via FastAPI + FastMCP (HTTP/SSE transport)
- **1 Memory Proxy** orchestrator that aggregates context and calls LLM
- **1 Ingestion CLI** for seeding the vector database

All services communicate via HTTP/SSE following MCP protocol standards.

## Services & Ports

| Service | Port | Purpose | MCP Tools Endpoint |
|---------|------|---------|-------------------|
| **Memory Proxy** | 8000 | Orchestrator & LLM integration | N/A (client) |
| **HA MCP** | 8001 | Home Assistant integration | `/tools` |
| **ChromaDB MCP** | 8002 | Vector database RAG | `/tools` |
| **Voice MCP** | 8003 | Wyoming-Whisper voice processing | `/tools` |

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

### Service Ports (auto-configured)
- `HA_MCP_PORT=8001`
- `CHROMA_MCP_PORT=8002`
- `VOICE_MCP_PORT=8003`
- `MEMORY_PROXY_PORT=8000`

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

### 3. Create Sample Documents
```bash
mkdir -p documents
echo "Project Aiden is a privacy-focused smart home AI system." > documents/intro.txt
echo "It uses MCP protocol for service communication." > documents/architecture.txt
```

### 4. Ingest Documents
```bash
python ingestion/ingest.py
```

### 5. Start All Services
```bash
chmod +x run_all.sh
./run_all.sh
```

### 6. Run Tests
```bash
chmod +x tests/run_tests.sh
./tests/run_tests.sh
```

## Service Details

### Home Assistant MCP (`servers/ha_mcp`)
Exposes Home Assistant capabilities as MCP tools:
- `get_entity_state(entity_id)` - Get entity state
- `call_service(domain, service, entity_id, **kwargs)` - Call HA service
- `get_states()` - Get all entity states
- `get_config()` - Get HA configuration

### ChromaDB MCP (`servers/chroma_mcp`)
Provides vector database RAG functionality:
- `query_documents(query_text, n_results)` - Semantic search
- `get_document(document_id)` - Retrieve by ID
- `count_documents()` - Get total count
- `search_by_metadata(metadata_filter, n_results)` - Metadata search

### Voice MCP (`servers/voice_mcp`)
Wyoming-Whisper integration for voice:
- `transcribe_audio(audio_base64)` - Transcribe audio
- `get_wyoming_info()` - Server info
- `test_wyoming_connection()` - Connection test

### Memory Proxy (`services/memory_proxy`)
Orchestrates MCP tools and LLM:
- `POST /query` - Main query endpoint
  - Aggregates RAG context from ChromaDB MCP
  - Gathers HA context from HA MCP
  - Calls LLM with combined context

## Testing

See `tests/README.md` for detailed test documentation.

Tests verify:
1. Health checks for all 4 services
2. MCP tool calls to HA and ChromaDB
3. RAG functionality (ingest → query → verify retrieval)

## Transfer to Ubuntu Server

See `DEPLOY_NOTES.md` for complete deployment instructions targeting `/opt/aiden` on Ubuntu Server with Docker Compose.

## Project Structure
```
.
├── servers/
│   ├── ha_mcp/main.py          # Home Assistant MCP server
│   ├── chroma_mcp/main.py      # ChromaDB MCP server
│   └── voice_mcp/main.py       # Wyoming MCP server
├── services/
│   └── memory_proxy/main.py    # Orchestrator
├── ingestion/
│   └── ingest.py               # ChromaDB ingestion CLI
├── tests/
│   ├── run_tests.sh            # Integration tests
│   └── README.md               # Test documentation
├── documents/                  # Document source for RAG
├── run_all.sh                  # Start all services
├── .env.example                # Environment template
├── README.md                   # This file
└── DEPLOY_NOTES.md            # Ubuntu deployment guide
```

## MCP Protocol

All MCP servers expose tools at `/tools` via HTTP/SSE transport following MCP specification:
- Tool discovery via SSE
- Tool calls via POST to `/tools/call`
- Standard JSON-RPC 2.0 message format

## License

See Project Aiden documentation for license details.

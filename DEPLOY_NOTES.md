# Project Aiden: Ubuntu Server Deployment Guide

This guide provides exact instructions for transferring Project Aiden to Ubuntu Server at `/opt/aiden`.

## Target Environment

- **OS**: Ubuntu Server 24.04 LTS
- **Docker**: Required for ChromaDB and Wyoming containers
- **Python**: 3.11+
- **Base Path**: `/opt/aiden`

## Exact Directory Structure on Ubuntu Server

```
/opt/aiden/
├── ha_mcp/              # Home Assistant MCP service
│   └── main.py
├── chroma_mcp/          # ChromaDB MCP service
│   └── main.py
├── voice_mcp/           # Wyoming MCP service
│   └── main.py
├── memory_proxy/        # Memory Proxy orchestrator
│   └── main.py
├── ingestion/           # Ingestion CLI
│   └── ingest.py
├── documents/           # Document source directory
├── .env                 # Environment configuration
├── requirements.txt     # Pinned dependencies
├── run_all.sh           # Service launcher
└── docker-compose.yml   # ChromaDB & Wyoming containers
```

## Transfer Steps

### 1. Create Base Directory
```bash
sudo mkdir -p /opt/aiden/{ha_mcp,chroma_mcp,voice_mcp,memory_proxy,ingestion,documents}
sudo chown -R $USER:$USER /opt/aiden
```

### 2. Copy Service Files

From this Replit project, copy files to Ubuntu Server (1:1 path matching):

```bash
# Copy MCP servers
scp ha_mcp/main.py user@ubuntu:/opt/aiden/ha_mcp/
scp chroma_mcp/main.py user@ubuntu:/opt/aiden/chroma_mcp/
scp voice_mcp/main.py user@ubuntu:/opt/aiden/voice_mcp/

# Copy orchestrator and ingestion
scp memory_proxy/main.py user@ubuntu:/opt/aiden/memory_proxy/
scp ingestion/ingest.py user@ubuntu:/opt/aiden/ingestion/

# Copy configuration and scripts
scp requirements.txt user@ubuntu:/opt/aiden/
scp run_all.sh user@ubuntu:/opt/aiden/
scp .env.example user@ubuntu:/opt/aiden/
scp -r documents/* user@ubuntu:/opt/aiden/documents/
```

### 3. Install Python Dependencies

```bash
cd /opt/aiden
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Create Docker Compose File

Create `/opt/aiden/docker-compose.yml`:

```yaml
version: '3.8'

services:
  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    ports:
      - "8000:8000"
    volumes:
      - chromadb_data:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
    networks:
      - aiden_net

  wyoming:
    image: rhasspy/wyoming-whisper:latest
    container_name: wyoming
    ports:
      - "10300:10300"
    command: --model tiny --language en
    networks:
      - aiden_net

volumes:
  chromadb_data:

networks:
  aiden_net:
    driver: bridge
```

### 5. Configure Environment Variables

Create `/opt/aiden/.env`:

```bash
# Home Assistant Configuration
HA_URL=http://192.168.1.100:8123
HA_TOKEN=your_actual_home_assistant_token

# ChromaDB Configuration (use Docker service name)
CHROMA_URL=http://chromadb:8000
COLLECTION_NAME=aiden

# Wyoming Configuration (use Docker service name)
WYOMING_HOST=wyoming
WYOMING_PORT=10300

# LLM Configuration (Optional)
OPENROUTER_API_KEY=your_openrouter_api_key
MODEL_NAME=anthropic/claude-3-haiku

# Service Ports
HA_MCP_PORT=8101
CHROMA_MCP_PORT=8102
VOICE_MCP_PORT=8103
MEMORY_PROXY_PORT=8104

# Internal Service URLs
HA_MCP_URL=http://localhost:8101
CHROMA_MCP_URL=http://localhost:8102
VOICE_MCP_URL=http://localhost:8103
```

## Required Environment Variables

### Mandatory
- `HA_URL` - Full URL to your Home Assistant instance
- `HA_TOKEN` - Long-lived access token from HA
- `CHROMA_URL` - ChromaDB URL (use Docker service name: `http://chromadb:8000`)
- `WYOMING_HOST` - Wyoming container hostname (use Docker service name: `wyoming`)
- `WYOMING_PORT` - Wyoming TCP port (default: `10300`)
- `COLLECTION_NAME` - ChromaDB collection name (default: `aiden`)

### Optional
- `OPENROUTER_API_KEY` - For LLM integration
- `MODEL_NAME` - LLM model selection

### Docker Compose Service Names
When services reference each other in Docker:
- **chromadb** - ChromaDB container (resolves to container in aiden_net)
- **wyoming** - Wyoming-Whisper container (resolves to container in aiden_net)

## Starting Services

### 1. Start Docker Containers
```bash
cd /opt/aiden
docker-compose up -d
```

### 2. Verify Container Status
```bash
docker-compose ps
docker-compose logs chromadb
docker-compose logs wyoming
```

### 3. Ingest Documents
```bash
source venv/bin/activate
cd /opt/aiden

# Ingest with CLI arguments
CHROMA_URL=http://localhost:8000 python ingestion/ingest.py --docs ./documents --collection aiden
```

### 4. Start MCP Services

```bash
chmod +x /opt/aiden/run_all.sh
/opt/aiden/run_all.sh
```

## Systemd Service (Production)

Create `/etc/systemd/system/aiden-ha-mcp.service`:

```ini
[Unit]
Description=Aiden HA MCP Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=aiden
WorkingDirectory=/opt/aiden
EnvironmentFile=/opt/aiden/.env
ExecStart=/opt/aiden/venv/bin/python /opt/aiden/ha_mcp/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Repeat for each service: `aiden-chroma-mcp.service`, `aiden-voice-mcp.service`, `aiden-memory-proxy.service`.

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aiden-ha-mcp aiden-chroma-mcp aiden-voice-mcp aiden-memory-proxy
sudo systemctl start aiden-ha-mcp aiden-chroma-mcp aiden-voice-mcp aiden-memory-proxy
```

## Verification

### Test Health Endpoints
```bash
curl http://localhost:8101/healthz  # HA MCP → {"ok":true}
curl http://localhost:8102/healthz  # ChromaDB MCP → {"ok":true}
curl http://localhost:8103/healthz  # Voice MCP → {"ok":true}
curl http://localhost:8104/healthz  # Memory Proxy → {"ok":true}
```

### Test MCP Tool Call
```bash
curl -X POST http://localhost:8102/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "count_documents",
      "arguments": {}
    }
  }'
```

### Test RAG Query
```bash
curl -X POST http://localhost:8104/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Project Aiden?",
    "use_rag": true,
    "use_ha_context": false
  }'
```

## Code Modification Requirements

**NONE** - All services are configured via environment variables. No code edits required after transfer.

Only required changes on Ubuntu:
1. Update `.env` with actual values (HA_URL, HA_TOKEN, etc.)
2. Ensure `docker-compose.yml` service names match env vars (chromadb, wyoming)
3. Configure systemd services for production

## Ports Summary

| Service | Port | Use |
|---------|------|-----|
| HA MCP | 8101 | Home Assistant integration |
| ChromaDB MCP | 8102 | Vector database RAG |
| Voice MCP | 8103 | Wyoming voice processing |
| Memory Proxy | 8104 | Orchestrator |

All services expose:
- `GET /healthz` → `{"ok": true}`
- `POST /tools/call` (MCP servers only)

## Security Notes

1. **Never commit `.env`** - Contains sensitive tokens
2. **Use restrictive permissions**: `chmod 600 /opt/aiden/.env`
3. **Run services as non-root user**
4. **Use firewall rules** to restrict MCP service access
5. **Rotate HA tokens** regularly

## Expected Service Behavior

- All services expose `/healthz` returning `{"ok": true}`
- MCP servers expose tools at `/tools` via SSE
- Memory Proxy orchestrates tool calls and aggregates context
- ChromaDB persists data in Docker volume
- Wyoming provides real-time transcription via TCP socket
- Ingestion CLI uses MiniLM embedding model (all-MiniLM-L6-v2)

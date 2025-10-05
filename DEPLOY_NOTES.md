# Project Aiden: Ubuntu Server Deployment Guide

This guide provides exact instructions for transferring Project Aiden to Ubuntu Server at `/opt/aiden`.

## Target Environment

- **OS**: Ubuntu Server 24.04 LTS
- **Docker**: Required for ChromaDB and Wyoming containers
- **Python**: 3.11+
- **Base Path**: `/opt/aiden`

## Directory Structure on Ubuntu Server

```
/opt/aiden/
├── ha_mcp/              # Home Assistant MCP service
├── chroma_mcp/          # ChromaDB MCP service
├── voice_mcp/           # Wyoming MCP service
├── memory_proxy/        # Memory Proxy orchestrator
├── ingestion/           # Ingestion CLI
├── documents/           # Document source directory
├── .env                 # Environment configuration
└── docker-compose.yml   # ChromaDB & Wyoming containers
```

## Transfer Steps

### 1. Create Base Directory
```bash
sudo mkdir -p /opt/aiden/{ha_mcp,chroma_mcp,voice_mcp,memory_proxy,ingestion,documents}
sudo chown -R $USER:$USER /opt/aiden
```

### 2. Copy Service Files

From this Replit project, copy files to Ubuntu Server:

```bash
# On your local machine or via scp
scp -r servers/ha_mcp/main.py user@ubuntu:/opt/aiden/ha_mcp/
scp -r servers/chroma_mcp/main.py user@ubuntu:/opt/aiden/chroma_mcp/
scp -r servers/voice_mcp/main.py user@ubuntu:/opt/aiden/voice_mcp/
scp -r services/memory_proxy/main.py user@ubuntu:/opt/aiden/memory_proxy/
scp -r ingestion/ingest.py user@ubuntu:/opt/aiden/ingestion/
```

### 3. Install Python Dependencies

```bash
cd /opt/aiden
python3 -m venv venv
source venv/bin/activate
pip install fastapi fastmcp httpx chromadb uvicorn python-dotenv sse-starlette
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

# ChromaDB Configuration
CHROMA_URL=http://chromadb:8000
COLLECTION_NAME=aiden

# Wyoming Configuration
WYOMING_HOST=wyoming
WYOMING_PORT=10300

# LLM Configuration (Optional)
OPENROUTER_API_KEY=your_openrouter_api_key
MODEL_NAME=anthropic/claude-3-haiku

# Service Ports
HA_MCP_PORT=8001
CHROMA_MCP_PORT=8002
VOICE_MCP_PORT=8003
MEMORY_PROXY_PORT=8000

# Internal Service URLs
HA_MCP_URL=http://localhost:8001
CHROMA_MCP_URL=http://localhost:8002
VOICE_MCP_URL=http://localhost:8003
```

## Required Environment Variables

### Mandatory
- `HA_URL` - Full URL to your Home Assistant instance
- `HA_TOKEN` - Long-lived access token from HA
- `CHROMA_URL` - ChromaDB URL (use Docker service name)
- `WYOMING_HOST` - Wyoming container hostname
- `WYOMING_PORT` - Wyoming TCP port

### Optional
- `OPENROUTER_API_KEY` - For LLM integration
- `MODEL_NAME` - LLM model selection
- `COLLECTION_NAME` - ChromaDB collection name

### Docker Compose Service Names
When services reference each other in Docker:
- ChromaDB: `chromadb` (resolves to container)
- Wyoming: `wyoming` (resolves to container)

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

# Add sample documents
echo "Project Aiden documentation content" > documents/sample.txt

# Run ingestion
CHROMA_URL=http://localhost:8000 python ingestion/ingest.py
```

### 4. Start MCP Services

Create `/opt/aiden/start_services.sh`:

```bash
#!/bin/bash

source /opt/aiden/venv/bin/activate
cd /opt/aiden

export $(cat .env | grep -v '^#' | xargs)

python ha_mcp/main.py &
python chroma_mcp/main.py &
python voice_mcp/main.py &
sleep 2
python memory_proxy/main.py &

echo "All services started"
```

Make executable and run:
```bash
chmod +x /opt/aiden/start_services.sh
/opt/aiden/start_services.sh
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

Repeat for each service (chroma_mcp, voice_mcp, memory_proxy).

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aiden-ha-mcp
sudo systemctl start aiden-ha-mcp
```

## Network Configuration

### Firewall Rules
```bash
# Allow MCP services (if needed from other hosts)
sudo ufw allow 8000/tcp  # Memory Proxy
sudo ufw allow 8001/tcp  # HA MCP
sudo ufw allow 8002/tcp  # ChromaDB MCP
sudo ufw allow 8003/tcp  # Voice MCP
```

### Docker Network
Services use `aiden_net` bridge network for inter-container communication.

## Verification

### Test Health Endpoints
```bash
curl http://localhost:8001/health  # HA MCP
curl http://localhost:8002/health  # ChromaDB MCP
curl http://localhost:8003/health  # Voice MCP
curl http://localhost:8000/health  # Memory Proxy
```

### Test MCP Tool Call
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

### Test RAG Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Project Aiden?",
    "use_rag": true,
    "use_ha_context": false
  }'
```

## Troubleshooting

### ChromaDB Connection Issues
- Verify Docker container: `docker ps | grep chromadb`
- Check logs: `docker-compose logs chromadb`
- Ensure CHROMA_URL uses container name in .env

### Home Assistant Connection
- Verify HA_URL is accessible from Ubuntu server
- Test token: `curl -H "Authorization: Bearer $HA_TOKEN" $HA_URL/api/`
- Check firewall rules on HA host

### Wyoming Connection
- Verify container: `docker ps | grep wyoming`
- Test TCP port: `nc -zv wyoming 10300`
- Check Wyoming logs: `docker-compose logs wyoming`

## Code Modification Requirements

**NONE** - All services are configured via environment variables. No code edits required after transfer.

Only required changes on Ubuntu:
1. Update `.env` with actual values
2. Ensure `docker-compose.yml` matches your network setup
3. Configure systemd services for production

## Backup & Restore

### Backup ChromaDB Data
```bash
docker run --rm -v aiden_chromadb_data:/data -v $(pwd):/backup ubuntu tar czf /backup/chromadb-backup.tar.gz /data
```

### Restore ChromaDB Data
```bash
docker run --rm -v aiden_chromadb_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/chromadb-backup.tar.gz -C /
```

## Security Notes

1. **Never commit `.env`** - Contains sensitive tokens
2. **Use restrictive permissions**: `chmod 600 /opt/aiden/.env`
3. **Run services as non-root user**
4. **Use firewall rules** to restrict MCP service access
5. **Rotate HA tokens** regularly

## Expected Service Behavior

- All services expose `/health` returning `{"status": "healthy", "service": "..."}`
- MCP servers expose tools at `/tools` via SSE
- Memory Proxy orchestrates tool calls and aggregates context
- ChromaDB persists data in Docker volume
- Wyoming provides real-time transcription via TCP socket

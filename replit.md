# Project Aiden: MCP-Integrated Smart Home AI

## Overview

Project Aiden is a privacy-focused, service-oriented smart home AI system built on the Model Context Protocol (MCP). The system implements a distributed architecture where independent microservices expose their capabilities as MCP tools, enabling seamless orchestration and AI-powered automation.

The system consists of three core MCP servers (Home Assistant, ChromaDB, Wyoming Voice), a Memory Proxy orchestrator that aggregates context and coordinates with LLMs, and an ingestion CLI for seeding the vector database. All services communicate via HTTP/SSE following MCP protocol standards.

**Key Technologies**: Python 3.11+, FastAPI, FastMCP, ChromaDB, Home Assistant, Wyoming-Whisper, Docker

**Deployment Target**: Ubuntu Server 24.04 LTS at `/opt/aiden`

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Service-Oriented MCP Architecture

The system implements a **microservices architecture** where each service exposes MCP tools via HTTP/SSE transport rather than traditional stdio. This design decision enables:
- Network-accessible tools across distributed hardware (AI Workhorse, Raspberry Pi satellites)
- Independent scaling and deployment of individual services
- Clear separation of concerns between tool providers and consumers

**Core Services & Ports**:
- **Memory Proxy** (Port 8000): Orchestrator that aggregates context from all MCP servers and coordinates LLM calls
- **Home Assistant MCP** (Port 8001): Device control and state management
- **ChromaDB MCP** (Port 8002): Vector database for RAG (Retrieval Augmented Generation)
- **Wyoming Voice MCP** (Port 8003): Speech-to-text transcription

### MCP Protocol Implementation

All custom MCP servers use **FastMCP framework** with FastAPI, implementing JSON-RPC 2.0 message format at `/tools/call` endpoint. This choice provides:
- RESTful HTTP interface instead of stdio, enabling multi-client access
- Server-Sent Events (SSE) for streaming responses
- Standard FastAPI middleware for authentication, logging, and error handling

Each MCP server exposes **tools** (executable functions), **resources** (data abstractions), and **prompts** (reusable templates) following MCP primitives.

### Data Layer

**ChromaDB** serves as the vector database for semantic search and RAG capabilities:
- Runs in Docker container for isolation
- HTTP client connection from ChromaDB MCP server
- Documents ingested from `/documents` directory via ingestion CLI
- Collection-based organization (default: "aiden" collection)

**Design Rationale**: Vector database enables context-aware responses by retrieving relevant documentation and historical information based on semantic similarity rather than keyword matching.

### Home Assistant Integration

The HA MCP server acts as a **proxy layer** between the AI system and Home Assistant:
- HTTP API calls with bearer token authentication
- Tools for entity state queries, service calls, and configuration retrieval
- Async HTTP client (httpx) for non-blocking operations

**Why a separate MCP server**: Decouples HA-specific logic from the orchestrator, enabling independent updates and potential reuse across multiple AI agents.

### Voice Processing Pipeline

Wyoming-Whisper integration via **TCP socket protocol**:
- Binary audio data transmission with length-prefixed framing
- Synchronous transcription workflow (send audio → receive text)
- Base64-encoded audio input from clients

**Trade-off**: Synchronous socket communication chosen for simplicity and reliability over async streaming, acceptable given typical voice command latency requirements.

### Memory Proxy Orchestration

The Memory Proxy implements a **context aggregation pattern**:
1. Receives user query
2. Optionally fetches RAG context from ChromaDB MCP
3. Optionally fetches Home Assistant state from HA MCP
4. Combines context into enriched prompt
5. Calls LLM via OpenRouter API
6. Returns AI-generated response

**Architectural Choice**: Centralized orchestrator provides single entry point for AI interactions while maintaining loose coupling with tool providers through MCP protocol.

### Environment-Based Configuration

All services use **environment variables** for configuration rather than config files:
- `.env` file for local development
- Supports containerized deployment with environment variable injection
- No hardcoded credentials or URLs

**Required Variables**:
- `HA_URL`, `HA_TOKEN`: Home Assistant connection
- `CHROMA_URL`: ChromaDB endpoint
- `WYOMING_HOST`, `WYOMING_PORT`: Voice server connection
- `OPENROUTER_API_KEY`, `MODEL_NAME`: LLM provider configuration

### Hardware Distribution Strategy

Multi-tier hardware architecture optimized for specific workloads:
- **AI Workhorse** (GMKtec K8 Plus, 32GB RAM): Heavy computation (LLM, NVR, Docker containers)
- **Control Hub** (Raspberry Pi 5): Real-time device control with Home Assistant OS
- **Satellites** (Pi 5 + Pi Zero 2W): Distributed sensing and voice interaction

**Design Rationale**: Dedicated hardware prevents resource contention—LLM inference doesn't impact real-time automation, and vision processing offloads to Google Coral TPU.

## External Dependencies

### Third-Party Services

- **OpenRouter API**: LLM inference provider
  - Default model: `anthropic/claude-3-haiku`
  - Requires API key via `OPENROUTER_API_KEY`
  - Used by Memory Proxy for generating AI responses

- **Home Assistant**: Smart home platform
  - Self-hosted at configurable URL (default: `http://homeassistant.local:8123`)
  - Long-lived access token authentication
  - REST API integration via HA MCP server

### Docker Containers

- **ChromaDB**: Vector database (official chromadb/chroma image)
  - Port 8000 (configurable)
  - HTTP API for document storage and semantic search
  - Persistent volume for data storage

- **Wyoming-Whisper**: Speech-to-text service
  - Custom Wyoming protocol over TCP
  - Port 10300 (configurable)
  - Whisper model for transcription

### Python Libraries

- **FastAPI**: Web framework for MCP servers and Memory Proxy
- **FastMCP**: MCP protocol implementation framework
- **chromadb**: Python client for ChromaDB HTTP API
- **httpx**: Async HTTP client for inter-service communication
- **python-dotenv**: Environment variable management
- **Pydantic**: Request/response validation

### Hardware Integrations

- **Google Coral TPU**: USB-connected AI accelerator for vision processing in Frigate NVR
- **ZBT-1 Dongle**: Zigbee/Thread radio for smart device communication via Home Assistant

### Network Requirements

- Gigabit Ethernet for AI Workhorse and Control Hub (stability and throughput)
- Local network accessibility between all services (no cloud dependencies for core functions)
- Static IPs or DNS resolution for service discovery (e.g., `homeassistant.local`)
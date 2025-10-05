import os
import json
from typing import Any, Optional
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

HA_MCP_URL = os.getenv("HA_MCP_URL", "http://localhost:8101")
CHROMA_MCP_URL = os.getenv("CHROMA_MCP_URL", "http://localhost:8102")
VOICE_MCP_URL = os.getenv("VOICE_MCP_URL", "http://localhost:8103")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "anthropic/claude-3-haiku")

app = FastAPI(title="Memory Proxy Orchestrator")

class QueryRequest(BaseModel):
    query: str
    use_rag: bool = True
    use_ha_context: bool = True

class ToolCall(BaseModel):
    tool_name: str
    arguments: dict

async def call_mcp_tool(base_url: str, tool_name: str, arguments: dict) -> Any:
    """Call an MCP tool via HTTP/SSE."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/tools/call",
            json={
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
        )
        response.raise_for_status()
        result = response.json()
        
        if "result" in result:
            return result["result"]
        return result

async def get_rag_context(query: str) -> str:
    """Query ChromaDB MCP for relevant context."""
    try:
        result = await call_mcp_tool(
            CHROMA_MCP_URL,
            "query_documents",
            {"query_text": query, "n_results": 3}
        )
        
        if "documents" in result and result["documents"]:
            context_parts = []
            for doc in result["documents"][:3]:
                context_parts.append(doc)
            return "\n\n".join(context_parts)
        return ""
    except Exception as e:
        print(f"RAG query error: {e}")
        return ""

async def get_ha_context() -> str:
    """Get current Home Assistant states via HA MCP."""
    try:
        result = await call_mcp_tool(
            HA_MCP_URL,
            "get_states",
            {}
        )
        
        states = result.get("states", []) if isinstance(result, dict) else result
        
        if isinstance(states, list):
            context_parts = []
            for entity in states[:10]:
                if isinstance(entity, dict):
                    entity_id = entity.get("entity_id", "")
                    state = entity.get("state", "")
                    context_parts.append(f"{entity_id}: {state}")
            return "\n".join(context_parts)
        return ""
    except Exception as e:
        print(f"HA context error: {e}")
        return ""

async def call_llm(prompt: str, context: str) -> str:
    """Call LLM with aggregated context."""
    if not OPENROUTER_API_KEY:
        return "LLM not configured (OPENROUTER_API_KEY missing). Context gathered: " + context[:200]
    
    try:
        full_prompt = f"Context:\n{context}\n\nUser Query: {prompt}\n\nResponse:"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            return "No response from LLM"
    except Exception as e:
        return f"LLM error: {str(e)}\n\nContext: {context[:200]}"

@app.post("/query")
async def query(request: QueryRequest):
    """Main query endpoint that orchestrates MCP tool calls and LLM."""
    context_parts = []
    
    if request.use_rag:
        rag_context = await get_rag_context(request.query)
        if rag_context:
            context_parts.append(f"Relevant Documents:\n{rag_context}")
    
    if request.use_ha_context:
        ha_context = await get_ha_context()
        if ha_context:
            context_parts.append(f"Home Assistant States:\n{ha_context}")
    
    full_context = "\n\n".join(context_parts)
    
    llm_response = await call_llm(request.query, full_context)
    
    return {
        "query": request.query,
        "context": full_context,
        "response": llm_response
    }

@app.post("/tool/call")
async def call_tool(tool_call: ToolCall):
    """Generic tool call endpoint for manual MCP tool invocation."""
    service_map = {
        "ha": HA_MCP_URL,
        "chroma": CHROMA_MCP_URL,
        "voice": VOICE_MCP_URL
    }
    
    service_prefix = tool_call.tool_name.split("_")[0]
    base_url = service_map.get(service_prefix)
    
    if not base_url:
        raise HTTPException(status_code=400, detail="Unknown tool service")
    
    result = await call_mcp_tool(base_url, tool_call.tool_name, tool_call.arguments)
    return {"result": result}

@app.get("/healthz")
async def healthz():
    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MEMORY_PROXY_PORT", "8104"))
    uvicorn.run(app, host="0.0.0.0", port=port)

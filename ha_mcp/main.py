import os
from typing import Any
import httpx
from fastapi import FastAPI
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

HA_URL = os.getenv("HA_URL", "http://homeassistant.local:8123")
HA_TOKEN = os.getenv("HA_TOKEN", "")

app = FastAPI(title="Home Assistant MCP Server")
mcp = FastMCP("Home Assistant MCP")

async def ha_api_call(method: str, endpoint: str, data: dict | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }
    url = f"{HA_URL}/api/{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, headers=headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()

@mcp.tool()
async def get_entity_state(entity_id: str) -> dict:
    """Get the current state of a Home Assistant entity.
    
    Args:
        entity_id: The entity ID to query (e.g., 'light.living_room')
    
    Returns:
        Dictionary containing entity state and attributes
    """
    return await ha_api_call("GET", f"states/{entity_id}")

@mcp.tool()
async def call_service(domain: str, service: str, entity_id: str | None = None, service_data: dict | None = None) -> dict:
    """Call a Home Assistant service.
    
    Args:
        domain: The domain of the service (e.g., 'light', 'switch')
        service: The service to call (e.g., 'turn_on', 'turn_off')
        entity_id: Optional entity ID to target
        service_data: Optional additional service data as JSON dict
    
    Returns:
        Service call response
    """
    data = service_data.copy() if service_data else {}
    if entity_id:
        data["entity_id"] = entity_id
    
    return await ha_api_call("POST", f"services/{domain}/{service}", data)

@mcp.tool()
async def get_states() -> dict:
    """Get all entity states from Home Assistant.
    
    Returns:
        List of all entity states
    """
    result = await ha_api_call("GET", "states")
    return {"states": result if isinstance(result, list) else []}

@mcp.tool()
async def get_config() -> dict:
    """Get Home Assistant configuration.
    
    Returns:
        Home Assistant configuration dictionary
    """
    return await ha_api_call("GET", "config")

@app.get("/healthz")
async def healthz():
    return {"ok": True}

app.mount("/tools", mcp.sse_app())

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("HA_MCP_PORT", "8101"))
    uvicorn.run(app, host="0.0.0.0", port=port)

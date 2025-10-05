import os
import struct
import socket
from typing import Optional
from fastapi import FastAPI, UploadFile, File
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

WYOMING_HOST = os.getenv("WYOMING_HOST", "wyoming")
WYOMING_PORT = int(os.getenv("WYOMING_PORT", "10300"))

app = FastAPI(title="Wyoming-Whisper MCP Server")
mcp = FastMCP("Wyoming Voice MCP")

def wyoming_transcribe(audio_data: bytes) -> str:
    """Send audio to Wyoming server for transcription via TCP protocol."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30.0)
        sock.connect((WYOMING_HOST, WYOMING_PORT))
        
        header = struct.pack("<I", len(audio_data))
        sock.sendall(header + audio_data)
        
        response_header = sock.recv(4)
        if len(response_header) < 4:
            raise ValueError("Invalid response from Wyoming server")
        
        response_length = struct.unpack("<I", response_header)[0]
        response_data = b""
        while len(response_data) < response_length:
            chunk = sock.recv(min(4096, response_length - len(response_data)))
            if not chunk:
                break
            response_data += chunk
        
        sock.close()
        
        return response_data.decode("utf-8")
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
async def transcribe_audio(audio_base64: str) -> dict:
    """Transcribe audio using Wyoming-Whisper server.
    
    Args:
        audio_base64: Base64-encoded audio data (WAV format)
    
    Returns:
        Dictionary containing transcribed text
    """
    import base64
    
    try:
        audio_data = base64.b64decode(audio_base64)
        transcription = wyoming_transcribe(audio_data)
        
        return {
            "text": transcription,
            "success": True
        }
    except Exception as e:
        return {
            "text": "",
            "success": False,
            "error": str(e)
        }

@mcp.tool()
async def get_wyoming_info() -> dict:
    """Get Wyoming server connection information.
    
    Returns:
        Dictionary with Wyoming server details
    """
    return {
        "host": WYOMING_HOST,
        "port": WYOMING_PORT,
        "status": "configured"
    }

@mcp.tool()
async def test_wyoming_connection() -> dict:
    """Test connection to Wyoming server.
    
    Returns:
        Dictionary with connection status
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((WYOMING_HOST, WYOMING_PORT))
        sock.close()
        return {
            "connected": True,
            "host": WYOMING_HOST,
            "port": WYOMING_PORT
        }
    except Exception as e:
        return {
            "connected": False,
            "host": WYOMING_HOST,
            "port": WYOMING_PORT,
            "error": str(e)
        }

@app.get("/healthz")
async def healthz():
    return {"ok": True}

app.mount("/tools", mcp.sse_app())

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VOICE_MCP_PORT", "8103"))
    uvicorn.run(app, host="0.0.0.0", port=port)

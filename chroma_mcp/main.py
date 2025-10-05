import os
from typing import Any, Optional
import chromadb
from fastapi import FastAPI
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

CHROMA_URL = os.getenv("CHROMA_URL", "http://chromadb:8000")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "aiden")

app = FastAPI(title="ChromaDB MCP Server")
mcp = FastMCP("ChromaDB MCP")

def get_chroma_client():
    return chromadb.HttpClient(host=CHROMA_URL.replace("http://", "").split(":")[0], 
                               port=int(CHROMA_URL.split(":")[-1]))

def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)

@mcp.tool()
async def query_documents(query_text: str, n_results: int = 5) -> dict:
    """Query the ChromaDB vector database for relevant documents.
    
    Args:
        query_text: The text to search for
        n_results: Number of results to return (default: 5)
    
    Returns:
        Dictionary containing matching documents, metadata, and distances
    """
    collection = get_collection()
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    
    return {
        "documents": results["documents"][0] if results["documents"] else [],
        "metadatas": results["metadatas"][0] if results["metadatas"] else [],
        "distances": results["distances"][0] if results["distances"] else [],
        "ids": results["ids"][0] if results["ids"] else []
    }

@mcp.tool()
async def get_document(document_id: str) -> dict:
    """Retrieve a specific document by ID.
    
    Args:
        document_id: The ID of the document to retrieve
    
    Returns:
        Dictionary containing document content and metadata
    """
    collection = get_collection()
    result = collection.get(ids=[document_id])
    
    if not result["documents"]:
        return {"error": "Document not found"}
    
    return {
        "document": result["documents"][0],
        "metadata": result["metadatas"][0] if result["metadatas"] else {},
        "id": result["ids"][0]
    }

@mcp.tool()
async def count_documents() -> dict:
    """Get the total number of documents in the collection.
    
    Returns:
        Dictionary with document count
    """
    collection = get_collection()
    return {"count": collection.count()}

@mcp.tool()
async def search_by_metadata(metadata_filter: dict, n_results: int = 10) -> dict:
    """Search documents by metadata filters.
    
    Args:
        metadata_filter: Dictionary of metadata filters
        n_results: Number of results to return (default: 10)
    
    Returns:
        Dictionary containing matching documents and metadata
    """
    collection = get_collection()
    results = collection.get(
        where=metadata_filter,
        limit=n_results
    )
    
    return {
        "documents": results["documents"],
        "metadatas": results["metadatas"],
        "ids": results["ids"]
    }

@app.get("/healthz")
async def healthz():
    return {"ok": True}

app.mount("/tools", mcp.sse_app())

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("CHROMA_MCP_PORT", "8102"))
    uvicorn.run(app, host="0.0.0.0", port=port)

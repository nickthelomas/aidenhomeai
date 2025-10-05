#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_URL = os.getenv("CHROMA_URL", "http://localhost:8000")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "aiden")
DOCUMENTS_DIR = os.getenv("DOCUMENTS_DIR", "./documents")

def get_chroma_client():
    host = CHROMA_URL.replace("http://", "").replace("https://", "").split(":")[0]
    port = int(CHROMA_URL.split(":")[-1]) if ":" in CHROMA_URL else 8000
    return chromadb.HttpClient(host=host, port=port)

def ingest_documents():
    """Ingest documents from the documents directory into ChromaDB."""
    docs_path = Path(DOCUMENTS_DIR)
    
    if not docs_path.exists():
        print(f"Documents directory not found: {DOCUMENTS_DIR}")
        sys.exit(1)
    
    text_files = list(docs_path.glob("*.txt")) + list(docs_path.glob("*.md"))
    
    if not text_files:
        print(f"No .txt or .md files found in {DOCUMENTS_DIR}")
        sys.exit(1)
    
    print(f"Found {len(text_files)} documents to ingest")
    
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        documents = []
        metadatas = []
        ids = []
        
        for idx, file_path in enumerate(text_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if content.strip():
                    documents.append(content)
                    metadatas.append({
                        "filename": file_path.name,
                        "path": str(file_path)
                    })
                    ids.append(f"doc_{idx}_{file_path.stem}")
                    print(f"  ✓ Loaded: {file_path.name}")
            except Exception as e:
                print(f"  ✗ Error reading {file_path.name}: {e}")
        
        if documents:
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"\n✓ Successfully ingested {len(documents)} documents into collection '{COLLECTION_NAME}'")
            print(f"  Total documents in collection: {collection.count()}")
        else:
            print("No valid documents to ingest")
            
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ingest_documents()

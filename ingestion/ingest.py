#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB for RAG")
    parser.add_argument("--docs", type=str, default=os.getenv("DOCUMENTS_DIR", "./documents"),
                       help="Directory containing documents to ingest (default: ./documents)")
    parser.add_argument("--collection", type=str, default=os.getenv("COLLECTION_NAME", "aiden"),
                       help="ChromaDB collection name (default: aiden)")
    
    args = parser.parse_args()
    
    chroma_url = os.getenv("CHROMA_URL", "http://localhost:8000")
    docs_path = Path(args.docs)
    collection_name = args.collection
    
    if not docs_path.exists():
        print(f"Error: Documents directory not found: {args.docs}")
        sys.exit(1)
    
    text_files = list(docs_path.glob("*.txt")) + list(docs_path.glob("*.md"))
    
    if not text_files:
        print(f"Error: No .txt or .md files found in {args.docs}")
        sys.exit(1)
    
    print(f"Found {len(text_files)} documents to ingest")
    print(f"Target collection: {collection_name}")
    print(f"ChromaDB URL: {chroma_url}")
    
    try:
        host = chroma_url.replace("http://", "").replace("https://", "").split(":")[0]
        port = int(chroma_url.split(":")[-1]) if ":" in chroma_url else 8000
        
        client = chromadb.HttpClient(host=host, port=port)
        
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        collection = client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_fn
        )
        
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
            print(f"\n✓ Successfully ingested {len(documents)} documents into collection '{collection_name}'")
            print(f"  Total documents in collection: {collection.count()}")
            print(f"  Embedding model: all-MiniLM-L6-v2")
        else:
            print("No valid documents to ingest")
            
    except Exception as e:
        print(f"Error connecting to ChromaDB: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

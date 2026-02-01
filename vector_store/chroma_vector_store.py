"""
ChromaDB-based vector store for RAG pipeline.
"""
import chromadb
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
load_dotenv()

CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", "db/chroma_db")

class ChromaVectorStore:
    def __init__(self, collection_name: str = "rag_docs"):
        # Use PersistentClient for automatic persistence
        self.client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        self.collection = self.client.get_or_create_collection(collection_name)

    def add(self, ids: List[str], vectors: List[list], metadatas: List[Dict[str, Any]]):
        try:
            self.collection.add(ids=ids, embeddings=vectors, metadatas=metadatas)
        except Exception as e:
            print(f"Vector store add error: {str(e)}")
            raise ValueError("Failed to store document vectors. Please try again.")

    def search(self, query_vector: list, top_k: int = 5):
        try:
            results = self.collection.query(query_embeddings=[query_vector], n_results=top_k)
            hits = []
            for i in range(len(results["ids"][0])):
                hit = {
                    "id": results["ids"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
                hits.append(hit)
            return hits
        except Exception as e:
            print(f"Vector store search error: {str(e)}")
            raise ValueError("Failed to search vector database. Please try again.")

# Example usage:
# store = ChromaVectorStore()
# store.add(ids, vectors, metadatas)
# results = store.search(query_vector, top_k=3)

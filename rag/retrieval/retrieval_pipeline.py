"""
retrieval_pipeline.py

Handles query embedding, vector search, and retrieval of relevant document chunks for RAG.
"""
from typing import List, Dict, Any
from rag.embedding.embedding_pipeline import EmbeddingModel
from vector_store.chroma_vector_store import ChromaVectorStore


class RetrievalPipeline:
    def __init__(self, embedding_model: EmbeddingModel, vector_store: ChromaVectorStore, top_k: int = 5):
        self.embedding_model = embedding_model
        self.vector_store = vector_store
        self.top_k = top_k

    def retrieve(self, query: str, filters: dict = None, deduplicate: bool = True) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant chunks for a query, with optional metadata filters and deduplication.
        filters: dict, e.g. {"Priority": "P0", "Type": "Process"}
        """
        try:
            query_vector = self.embedding_model.embed([query])[0]
            results = self.vector_store.search(query_vector, top_k=self.top_k * 2)  # Overfetch for filtering/dedup
        except ValueError as ve:
            # Re-raise ValueError from embedding (user-friendly message)
            raise ve
        except Exception as e:
            print(f"Retrieval error: {str(e)}")
            raise ValueError("Failed to search documents. Please try again.")
        formatted = []
        seen_chunks = set()
        for hit in results:
            meta = hit["metadata"]
            # Apply metadata filters if provided
            if filters:
                skip = False
                for k, v in filters.items():
                    if meta.get(k) != v:
                        skip = True
                        break
                if skip:
                    continue
            # Load chunk text
            chunk_text = meta.get("chunk_text")
            if not chunk_text and "chunk_file" in meta:
                try:
                    with open(meta["chunk_file"], "r", encoding="utf-8") as f:
                        chunk_text = f.read()
                except Exception:
                    chunk_text = "[Chunk text unavailable]"
            # Deduplicate by chunk text
            if deduplicate:
                chunk_hash = hash(chunk_text)
                if chunk_hash in seen_chunks:
                    continue
                seen_chunks.add(chunk_hash)
            formatted.append({
                "id": hit["id"],
                "score": 1.0 - hit["distance"],
                "chunk": chunk_text,
                "metadata": meta
            })
            if len(formatted) >= self.top_k:
                break
        return formatted

# Example usage:
# retrieval = RetrievalPipeline(embedding_model, vector_store)
# top_chunks = retrieval.retrieve("How do I reset my password?")

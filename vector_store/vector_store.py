"""
vector_store.py

Handles storage and retrieval of vector embeddings and metadata for RAG.
"""
from typing import List, Dict, Any, Tuple
import numpy as np

class VectorStore:
    def __init__(self):
        self.vectors = []  # List of np.ndarray
        self.metadata = []  # List of dicts

    def add(self, vectors: List[list], metadatas: List[Dict[str, Any]]):
        for v, m in zip(vectors, metadatas):
            self.vectors.append(np.array(v))
            self.metadata.append(m)

    def search(self, query_vector: list, top_k: int = 5) -> List[Tuple[Dict[str, Any], float]]:
        query = np.array(query_vector)
        scores = [self._cosine_similarity(query, v) for v in self.vectors]
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [(self.metadata[i], float(scores[i])) for i in top_indices]

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        if np.linalg.norm(a) == 0 or np.linalg.norm(b) == 0:
            return 0.0
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# Example usage:
# store = VectorStore()
# store.add(vectors, metadatas)
# results = store.search(query_vector, top_k=3)

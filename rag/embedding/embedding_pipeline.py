
import os
"""
embedding_pipeline.py

Handles embedding and vectorization of document chunks for RAG.
"""
from typing import List


from dotenv import load_dotenv
load_dotenv()
from langchain_openai import OpenAIEmbeddings


class EmbeddingModel:
    def __init__(self, model_name: str = 'text-embedding-3-small', openai_api_key: str = None):
        self.model_name = model_name
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.embedder = OpenAIEmbeddings(model=self.model_name, openai_api_key=self.openai_api_key)

    def embed(self, texts: List[str]) -> List[list]:
        """
        Returns a list of vector embeddings for the input texts using LangChain OpenAIEmbeddings.
        """
        return self.embedder.embed_documents(texts)

# Example usage:
# model = EmbeddingModel()
# vectors = model.embed([chunk.text for chunk in chunks])

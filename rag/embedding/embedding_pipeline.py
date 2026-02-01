
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
        try:
            if not self.openai_api_key or self.openai_api_key == 'your-api-key-here':
                raise ValueError("OpenAI API key is not configured")
            return self.embedder.embed_documents(texts)
        except Exception as e:
            error_msg = str(e)
            if '401' in error_msg or 'invalid_api_key' in error_msg:
                raise ValueError("Invalid OpenAI API key. Please check your configuration.")
            elif '429' in error_msg or 'rate_limit' in error_msg:
                raise ValueError("Rate limit exceeded. Please wait a moment and try again.")
            else:
                print(f"Embedding error: {error_msg}")
                raise ValueError("Failed to generate embeddings. Please try again.")

# Example usage:
# model = EmbeddingModel()
# vectors = model.embed([chunk.text for chunk in chunks])

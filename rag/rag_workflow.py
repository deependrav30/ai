"""
rag_workflow.py

Wires together ingestion, embedding, vector storage, and retrieval for end-to-end RAG indexing and query.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
from rag.ingestion.ingestion_pipeline import IngestionPipeline
from rag.embedding.embedding_pipeline import EmbeddingModel
from vector_store.chroma_vector_store import ChromaVectorStore
from rag.retrieval.retrieval_pipeline import RetrievalPipeline

load_dotenv()

# Initialize components (replace with real model in production)
ingestion = IngestionPipeline(chunk_size=500, chunk_overlap=50)
embedding_model = EmbeddingModel(model_name='text-embedding-3-small')
vector_store = ChromaVectorStore()
retrieval = RetrievalPipeline(embedding_model, vector_store, top_k=5)


def index_document(file_path: str, metadata: dict):
    # 1. Ingest and chunk document
    chunk_texts, chunk_metadatas = ingestion.ingest(file_path, metadata)
    if not chunk_texts:
        print(f"[WARNING] No text chunks extracted from {file_path}. Skipping embedding and vector store.")
        return
    # 2. Embed chunks using OpenAI
    vectors = embedding_model.embed(chunk_texts)
    if not vectors:
        print(f"[WARNING] No embeddings generated for {file_path}. Skipping vector store.")
        return
    # 3. Add chunk text to metadata for retrieval
    for i, chunk_meta in enumerate(chunk_metadatas):
        chunk_meta['chunk_text'] = chunk_texts[i]
    # 4. Store vectors and metadata in vector DB
    ids = [f"{os.path.basename(file_path)}_chunk_{i+1}" for i in range(len(chunk_texts))]
    vector_store.add(ids, vectors, chunk_metadatas)
    print(f"Indexed {len(chunk_texts)} chunks from {file_path}")

def query_rag(query: str):
    # 4. Retrieve top-k relevant chunks
    results = retrieval.retrieve(query)
    print(f"Top results for query: '{query}'")
    for i, res in enumerate(results, 1):
        print(f"[{i}] Score: {res['score']:.4f}, Metadata: {res}")

def generate_response(query: str, chunks: list) -> str:
    """
    Generate a final response using OpenAI GPT-4 based on retrieved chunks.
    
    Args:
        query: User's question
        chunks: List of relevant chunk results from retrieval
    
    Returns:
        Generated response string
    """
    if not chunks:
        return "No relevant information found to answer your question."
    
    # Prepare context from chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        chunk_text = chunk.get('chunk', chunk.get('chunk_text', '[No text]'))
        context_parts.append(f"[Source {i}]: {chunk_text}")
    
    context = "\n\n".join(context_parts)
    
    # Create prompt for GPT-4
    prompt = f"""Based on the following context from our document knowledge base, please answer the user's question. Be concise, accurate, and cite sources using [Source X] notation when referencing specific information.

Context:
{context}

User Question: {query}

Answer (include source citations like [Source 1] when appropriate):"""
    
    # Call OpenAI GPT-4
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context. Be concise and accurate."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"

# Example usage:
# index_document('/path/to/file.pdf', {'Type': 'Process', 'Subtype': 'KYC', 'Priority': 'P1', 'Uploaded By': 'Admin', 'Timestamp': '2026-01-31'})
# query_rag('How do I verify my identity?')

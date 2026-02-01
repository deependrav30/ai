"""
Retrieval Agent - RAG Knowledge Search

Integrates with existing RAG pipeline to search knowledge base.
Filters results by metadata (category, urgency, date).
Returns ranked results with relevance scores.
"""
from typing import Dict, Any, List
import time
from .base_agent import BaseAgent, logger

# Import existing RAG retrieval
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.rag_workflow import retrieval


class RetrievalAgent(BaseAgent):
    """
    Searches knowledge base using RAG for relevant documents.
    Integrates with existing ChromaDB vector store.
    """
    
    def __init__(self):
        super().__init__("RetrievalAgent")
        self.top_k = 5  # Number of results to retrieve
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search knowledge base for relevant documents.
        
        Args:
            state: Must contain 'user_input', optionally 'intent', 'category'
            
        Returns:
            State updated with:
            - retrieved_docs: List of relevant documents
            - doc_scores: Relevance scores
            - doc_count: Number of documents found
        """
        start_time = time.time()
        
        try:
            user_input = state.get("user_input", "")
            if not user_input:
                logger.error("RetrievalAgent: No user_input in state")
                state["retrieved_docs"] = []
                return state
            
            # Build search query (optionally enhance with intent/category)
            search_query = self.build_search_query(state)
            
            logger.info(f"Searching knowledge base for: {search_query[:100]}...")
            
            # Use retrieval module directly (already imported at top of file)
            results = retrieval.retrieve(search_query)
            
            # Extract documents and metadata
            retrieved_docs = []
            doc_scores = []
            
            if results:
                for result in results:
                    # Retrieval pipeline returns 'chunk' field, map to 'content' for agents
                    chunk_text = result.get("chunk", result.get("chunk_text", ""))
                    metadata = result.get("metadata", {})
                    
                    # Extract source from metadata if available
                    source = metadata.get("file_name", metadata.get("Timestamp", "unknown"))
                    
                    retrieved_docs.append({
                        "content": chunk_text,
                        "source": source,
                        "score": result.get("score", 0.0),
                        "metadata": metadata
                    })
                    doc_scores.append(result.get("score", 0.0))
            
            # Update state
            state["retrieved_docs"] = retrieved_docs
            state["doc_scores"] = doc_scores
            state["doc_count"] = len(retrieved_docs)
            
            # Calculate confidence based on relevance scores
            if doc_scores:
                avg_score = sum(doc_scores) / len(doc_scores)
                retrieval_confidence = min(avg_score, 0.95)  # Cap at 0.95
            else:
                retrieval_confidence = 0.3  # Low confidence if no results
            
            self.update_confidence(state, retrieval_confidence)
            
            logger.info(f"Retrieved {len(retrieved_docs)} documents, avg score: {avg_score if doc_scores else 0:.2f}")
            
            # Log execution time
            execution_time = time.time() - start_time
            state = self.log_execution(state, execution_time)
            
            return state
            
        except Exception as e:
            logger.error(f"RetrievalAgent error: {str(e)}")
            state["retrieved_docs"] = []
            state["doc_count"] = 0
            state["error"] = f"Knowledge retrieval failed: {str(e)}"
            self.update_confidence(state, 0.3)
            return state
    
    def build_search_query(self, state: Dict[str, Any]) -> str:
        """
        Build enhanced search query using intent and category.
        
        Args:
            state: State with user_input, optionally intent/category
            
        Returns:
            Enhanced search query string
        """
        query = state.get("user_input", "")
        intent = state.get("intent", "")
        category = state.get("category", "")
        
        # Add intent/category keywords to improve search
        if intent and intent != "question":
            query = f"{intent} {query}"
        
        if category:
            query = f"{category} {query}"
        
        return query
    
    def filter_by_metadata(self, docs: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        """
        Filter documents by metadata criteria.
        
        Args:
            docs: List of document dictionaries
            filters: Dict of metadata filters (e.g., {"category": "technical"})
            
        Returns:
            Filtered list of documents
        """
        filtered = []
        
        for doc in docs:
            metadata = doc.get("metadata", {})
            matches = True
            
            for key, value in filters.items():
                if metadata.get(key) != value:
                    matches = False
                    break
            
            if matches:
                filtered.append(doc)
        
        return filtered
    
    def get_retrieval_summary(self, state: Dict[str, Any]) -> str:
        """Generate summary of retrieval results"""
        doc_count = state.get("doc_count", 0)
        avg_score = sum(state.get("doc_scores", [0])) / max(len(state.get("doc_scores", [1])), 1)
        
        if doc_count == 0:
            return "No relevant documents found"
        elif doc_count == 1:
            return f"1 document found (score: {avg_score:.2f})"
        else:
            return f"{doc_count} documents found (avg score: {avg_score:.2f})"

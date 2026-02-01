"""
Duplicate Detector Agent

Detects duplicate or similar tickets using semantic embeddings and ChromaDB.
Helps prevent redundant work and route new tickets to existing solutions.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import chromadb
from openai import AsyncOpenAI
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class DuplicateDetectorAgent(BaseAgent):
    """Agent for detecting duplicate/similar tickets using semantic search"""
    
    # Similarity thresholds for duplicate detection
    THRESHOLDS = {
        'exact_duplicate': 0.95,  # >95% similarity = exact duplicate
        'very_similar': 0.85,      # 85-95% = very similar, likely duplicate
        'similar': 0.70,            # 70-85% = similar, potentially related
        'related': 0.60             # 60-70% = related, worth reviewing
    }
    
    def __init__(self):
        super().__init__(name="DuplicateDetectorAgent")
        self.client = AsyncOpenAI()
        self.chroma_client = chromadb.PersistentClient(path="db/chroma_db")
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure ticket_history collection exists"""
        try:
            self.ticket_collection = self.chroma_client.get_or_create_collection(
                name="ticket_history",
                metadata={"description": "Historical tickets for duplicate detection"}
            )
            logger.info(f"Ticket history collection ready: {self.ticket_collection.count()} tickets")
        except Exception as e:
            logger.error(f"Failed to initialize ticket collection: {e}")
            raise
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect duplicate tickets for a new ticket
        
        Args:
            context: Contains 'ticket_title', 'ticket_description', 'ticket_id' (optional)
        
        Returns:
            Dict with 'duplicates' list containing similar tickets
        """
        start_time = datetime.now()
        
        try:
            ticket_title = context.get('ticket_title', '')
            ticket_description = context.get('ticket_description', '')
            ticket_id = context.get('ticket_id', 'unknown')
            
            # Combine title and description for semantic search
            ticket_text = f"{ticket_title}\n{ticket_description}"
            
            logger.info(f"Searching for duplicates of ticket: {ticket_id}")
            
            # Get embedding for the new ticket
            embedding = await self._get_embedding(ticket_text)
            
            # Search for similar tickets
            duplicates = await self._search_similar_tickets(
                embedding=embedding,
                ticket_id=ticket_id,
                ticket_text=ticket_text
            )
            
            # Classify similarity levels
            categorized_duplicates = self._categorize_duplicates(duplicates)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'duplicates': categorized_duplicates,
                'total_found': len(duplicates),
                'exact_duplicates': len(categorized_duplicates.get('exact_duplicate', [])),
                'very_similar': len(categorized_duplicates.get('very_similar', [])),
                'similar': len(categorized_duplicates.get('similar', [])),
                'related': len(categorized_duplicates.get('related', []))
            }
            
            logger.info(f"DuplicateDetectorAgent executed in {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in DuplicateDetectorAgent: {e}")
            raise
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text using OpenAI"""
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-3-small",  # Faster and cheaper
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to get embedding: {e}")
            raise
    
    async def _search_similar_tickets(
        self, 
        embedding: List[float], 
        ticket_id: str,
        ticket_text: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar tickets using ChromaDB"""
        try:
            # Query ChromaDB for similar tickets
            results = self.ticket_collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                include=['metadatas', 'documents', 'distances']
            )
            
            if not results['ids'][0]:
                logger.info("No similar tickets found")
                return []
            
            # Format results
            similar_tickets = []
            for i, ticket_id_found in enumerate(results['ids'][0]):
                # Skip if it's the same ticket
                if ticket_id_found == ticket_id:
                    continue
                
                # ChromaDB returns L2 distance, convert to cosine similarity
                # For normalized embeddings: similarity = 1 - (distance^2 / 2)
                distance = results['distances'][0][i]
                similarity = 1 - (distance ** 2 / 2)
                
                similar_tickets.append({
                    'ticket_id': ticket_id_found,
                    'similarity': round(similarity, 3),
                    'metadata': results['metadatas'][0][i],
                    'text': results['documents'][0][i],
                    'distance': round(distance, 3)
                })
            
            return similar_tickets
            
        except Exception as e:
            logger.error(f"Failed to search similar tickets: {e}")
            return []
    
    def _categorize_duplicates(self, duplicates: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize duplicates by similarity threshold"""
        categorized = {
            'exact_duplicate': [],
            'very_similar': [],
            'similar': [],
            'related': []
        }
        
        for ticket in duplicates:
            similarity = ticket['similarity']
            
            if similarity >= self.THRESHOLDS['exact_duplicate']:
                categorized['exact_duplicate'].append(ticket)
            elif similarity >= self.THRESHOLDS['very_similar']:
                categorized['very_similar'].append(ticket)
            elif similarity >= self.THRESHOLDS['similar']:
                categorized['similar'].append(ticket)
            elif similarity >= self.THRESHOLDS['related']:
                categorized['related'].append(ticket)
        
        return categorized
    
    async def add_ticket_to_history(
        self, 
        ticket_id: str, 
        ticket_title: str,
        ticket_description: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a ticket to the history collection for future duplicate detection
        
        Args:
            ticket_id: Unique ticket identifier
            ticket_title: Ticket title
            ticket_description: Ticket description
            metadata: Additional metadata (status, resolution, timestamps, etc.)
        """
        try:
            ticket_text = f"{ticket_title}\n{ticket_description}"
            embedding = await self._get_embedding(ticket_text)
            
            # Prepare metadata
            ticket_metadata = metadata or {}
            ticket_metadata.update({
                'title': ticket_title,
                'added_at': datetime.now().isoformat()
            })
            
            # Add to ChromaDB
            self.ticket_collection.add(
                ids=[ticket_id],
                embeddings=[embedding],
                documents=[ticket_text],
                metadatas=[ticket_metadata]
            )
            
            logger.info(f"Added ticket {ticket_id} to history collection")
            
        except Exception as e:
            logger.error(f"Failed to add ticket to history: {e}")
            raise
    
    def get_duplicate_summary(self, duplicates: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generate human-readable summary of duplicates"""
        summary_parts = []
        
        if duplicates.get('exact_duplicate'):
            summary_parts.append(
                f"🔴 {len(duplicates['exact_duplicate'])} exact duplicate(s) found (>95% similar)"
            )
        
        if duplicates.get('very_similar'):
            summary_parts.append(
                f"🟠 {len(duplicates['very_similar'])} very similar ticket(s) (85-95% similar)"
            )
        
        if duplicates.get('similar'):
            summary_parts.append(
                f"🟡 {len(duplicates['similar'])} similar ticket(s) (70-85% similar)"
            )
        
        if duplicates.get('related'):
            summary_parts.append(
                f"🟢 {len(duplicates['related'])} related ticket(s) (60-70% similar)"
            )
        
        if not summary_parts:
            return "✅ No duplicates found - this appears to be a unique ticket"
        
        return "\n".join(summary_parts)

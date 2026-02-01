"""
Memory Agent - Three Memory Types

Manages three types of memory:
1. Working Memory (Redis): Current task context, temporary data
2. Episodic Memory (PostgreSQL): Past tickets, resolutions, outcomes
3. Semantic Memory (ChromaDB): Document embeddings, knowledge base

For now, implements basic functionality with SQLite fallback.
Full Redis/PostgreSQL integration via Docker Compose later.
"""
from typing import Dict, Any, List
import time
import sqlite3
import json
from datetime import datetime
from .base_agent import BaseAgent, logger

# Import existing chat storage for episodic memory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.chat_storage import ChatStorage


class MemoryAgent(BaseAgent):
    """
    Manages three types of memory for the agent system.
    """
    
    def __init__(self):
        super().__init__("MemoryAgent")
        self.chat_storage = ChatStorage()
        
        # Working memory (in-memory dict for now, Redis later)
        self.working_memory = {}
        
        # Initialize episodic memory database
        self.episodic_db_path = "db/episodic_memory.db"
        self._init_episodic_memory()
    
    def _init_episodic_memory(self):
        """Initialize episodic memory database"""
        os.makedirs("db", exist_ok=True)
        
        conn = sqlite3.connect(self.episodic_db_path)
        cursor = conn.cursor()
        
        # Table for past tickets and resolutions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS past_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT,
                user_input TEXT,
                intent TEXT,
                category TEXT,
                urgency TEXT,
                resolution TEXT,
                outcome TEXT,
                confidence REAL,
                timestamp TEXT,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Episodic memory database initialized")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search past tickets and store working memory.
        
        Args:
            state: Must contain 'user_input', optionally 'intent', 'category'
            
        Returns:
            State updated with:
            - past_tickets: Similar past tickets
            - past_resolutions: Successful resolutions
            - memory_matches: Number of matches found
        """
        start_time = time.time()
        
        try:
            user_input = state.get("user_input", "")
            
            # Store current context in working memory
            self.store_working_memory(state)
            
            # Search episodic memory for similar past tickets
            past_tickets = self.search_episodic_memory(state)
            
            state["past_tickets"] = past_tickets
            state["memory_matches"] = len(past_tickets)
            
            # Extract successful resolutions
            past_resolutions = [
                {
                    "input": ticket["user_input"],
                    "resolution": ticket["resolution"],
                    "outcome": ticket["outcome"]
                }
                for ticket in past_tickets
                if ticket.get("outcome") == "success"
            ]
            
            state["past_resolutions"] = past_resolutions
            
            # Calculate confidence based on similarity
            if past_tickets:
                memory_confidence = 0.8  # High confidence if we have past examples
            else:
                memory_confidence = 0.6  # Medium confidence if no history
            
            self.update_confidence(state, memory_confidence)
            
            logger.info(f"Found {len(past_tickets)} similar past tickets")
            
            # Log execution time
            execution_time = time.time() - start_time
            state = self.log_execution(state, execution_time)
            
            return state
            
        except Exception as e:
            logger.error(f"MemoryAgent error: {str(e)}")
            state["past_tickets"] = []
            state["past_resolutions"] = []
            state["memory_matches"] = 0
            state["error"] = f"Memory search failed: {str(e)}"
            return state
    
    def store_working_memory(self, state: Dict[str, Any]):
        """
        Store current task context in working memory.
        
        Args:
            state: Current state
        """
        task_id = state.get("task_id", f"task_{datetime.now().timestamp()}")
        
        self.working_memory[task_id] = {
            "user_input": state.get("user_input", ""),
            "intent": state.get("intent", ""),
            "category": state.get("category", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Stored working memory for {task_id}")
    
    def search_episodic_memory(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search episodic memory for similar past tickets.
        
        Args:
            state: Current state with user_input, intent, category
            
        Returns:
            List of similar past tickets
        """
        intent = state.get("intent", "")
        category = state.get("category", "")
        
        conn = sqlite3.connect(self.episodic_db_path)
        cursor = conn.cursor()
        
        # Search by intent and category
        query = '''
            SELECT * FROM past_tickets
            WHERE 1=1
        '''
        params = []
        
        if intent:
            query += " AND intent = ?"
            params.append(intent)
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY timestamp DESC LIMIT 5"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to dictionaries
        past_tickets = []
        for row in rows:
            past_tickets.append({
                "ticket_id": row[1],
                "user_input": row[2],
                "intent": row[3],
                "category": row[4],
                "urgency": row[5],
                "resolution": row[6],
                "outcome": row[7],
                "confidence": row[8],
                "timestamp": row[9]
            })
        
        return past_tickets
    
    def store_episodic_memory(self, state: Dict[str, Any]):
        """
        Store completed ticket in episodic memory.
        Call this after ticket resolution.
        
        Args:
            state: Final state with resolution and outcome
        """
        conn = sqlite3.connect(self.episodic_db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO past_tickets 
            (ticket_id, user_input, intent, category, urgency, resolution, outcome, confidence, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            state.get("ticket_id", f"ticket_{datetime.now().timestamp()}"),
            state.get("user_input", ""),
            state.get("intent", ""),
            state.get("category", ""),
            state.get("urgency", ""),
            state.get("response", ""),
            state.get("outcome", "success"),
            state.get("confidence", 0.5),
            datetime.now().isoformat(),
            json.dumps(state.get("metadata", {}))
        ))
        
        conn.commit()
        conn.close()
        logger.info("Stored ticket in episodic memory")
    
    def get_working_memory(self, task_id: str) -> Dict[str, Any]:
        """Get working memory for a task"""
        return self.working_memory.get(task_id, {})
    
    def clear_working_memory(self, task_id: str):
        """Clear working memory after task completion"""
        if task_id in self.working_memory:
            del self.working_memory[task_id]
            logger.info(f"Cleared working memory for {task_id}")
    
    def get_memory_summary(self, state: Dict[str, Any]) -> str:
        """Generate summary of memory search results"""
        matches = state.get("memory_matches", 0)
        resolutions = len(state.get("past_resolutions", []))
        
        if matches == 0:
            return "No similar past tickets found"
        elif resolutions == 0:
            return f"{matches} similar tickets found (no successful resolutions)"
        else:
            return f"{matches} similar tickets found ({resolutions} successful resolutions)"

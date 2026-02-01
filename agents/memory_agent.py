"""
Memory Agent - Three Memory Types

Manages three types of memory:
1. Working Memory (Redis): Current task context, temporary data
2. Episodic Memory (PostgreSQL): Past tickets, resolutions, outcomes
3. Semantic Memory (ChromaDB): Document embeddings, knowledge base

Now using Redis and PostgreSQL via Docker Compose (ports: 6380, 5433).
Falls back to in-memory/SQLite if services unavailable.
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

# Import Redis and PostgreSQL libraries
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis library not available, using in-memory fallback")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    logger.warning("psycopg2 library not available, using SQLite fallback")


class MemoryAgent(BaseAgent):
    """
    Manages three types of memory for the agent system.
    """
    
    def __init__(self):
        super().__init__("MemoryAgent")
        self.chat_storage = ChatStorage()
        
        # Working memory - Try Redis first, fallback to in-memory dict
        self.redis_client = None
        self.working_memory = {}
        self._init_redis()
        
        # Episodic memory - Try PostgreSQL first, fallback to SQLite
        self.postgres_conn = None
        self.episodic_db_path = "db/episodic_memory.db"
        self._init_episodic_memory()
    
    def _init_redis(self):
        """Initialize Redis connection for working memory"""
        if not REDIS_AVAILABLE:
            logger.info("Using in-memory working memory (Redis not available)")
            return
        
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6380,
                db=0,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            logger.info("✓ Connected to Redis for working memory (port 6380)")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory fallback: {e}")
            self.redis_client = None
    
    def _init_episodic_memory(self):
        """Initialize episodic memory - PostgreSQL with SQLite fallback"""
        
        # Try PostgreSQL first
        if POSTGRES_AVAILABLE:
            try:
                self.postgres_conn = psycopg2.connect(
                    host='localhost',
                    port=5433,
                    database='episodic_memory',
                    user='ai_agent',
                    password='ai_agent_password',
                    connect_timeout=2
                )
                logger.info("✓ Connected to PostgreSQL for episodic memory (port 5433)")
                return
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed, using SQLite fallback: {e}")
                self.postgres_conn = None
        
        # Fallback to SQLite
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
        logger.info("✓ Episodic memory using SQLite fallback")
    
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
        Store current task context in working memory (Redis or in-memory).
        
        Args:
            state: Current state
        """
        task_id = state.get("task_id", f"task_{datetime.now().timestamp()}")
        
        memory_data = {
            "user_input": state.get("user_input", ""),
            "intent": state.get("intent", ""),
            "category": state.get("category", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.setex(
                    f"working_memory:{task_id}",
                    3600,  # 1 hour TTL
                    json.dumps(memory_data)
                )
                logger.info(f"Stored working memory in Redis for {task_id}")
                return
            except Exception as e:
                logger.warning(f"Redis store failed: {e}, using in-memory fallback")
        
        # Fallback to in-memory
        self.working_memory[task_id] = memory_data
        logger.info(f"Stored working memory (in-memory) for {task_id}")
    
    def search_episodic_memory(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search episodic memory for similar past tickets (PostgreSQL or SQLite).
        
        Args:
            state: Current state with user_input, intent, category
            
        Returns:
            List of similar past tickets
        """
        intent = state.get("intent", "")
        category = state.get("category", "")
        
        # Try PostgreSQL first
        if self.postgres_conn:
            try:
                cursor = self.postgres_conn.cursor(cursor_factory=RealDictCursor)
                
                query = '''
                    SELECT * FROM past_tickets
                    WHERE 1=1
                '''
                params = []
                
                if intent:
                    query += " AND intent = %s"
                    params.append(intent)
                
                if category:
                    query += " AND category = %s"
                    params.append(category)
                
                query += " ORDER BY created_at DESC LIMIT 5"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                cursor.close()
                
                # Convert to list of dicts
                past_tickets = [dict(row) for row in rows]
                logger.info(f"Retrieved {len(past_tickets)} tickets from PostgreSQL")
                return past_tickets
                
            except Exception as e:
                logger.warning(f"PostgreSQL search failed: {e}, using SQLite fallback")
        
        # Fallback to SQLite
        conn = sqlite3.connect(self.episodic_db_path)
        cursor = conn.cursor()
        
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
        
        logger.info(f"Retrieved {len(past_tickets)} tickets from SQLite")
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
        """Get working memory for a task (Redis or in-memory)"""
        
        # Try Redis first
        if self.redis_client:
            try:
                data = self.redis_client.get(f"working_memory:{task_id}")
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
        
        # Fallback to in-memory
        return self.working_memory.get(task_id, {})
    
    def clear_working_memory(self, task_id: str):
        """Clear working memory after task completion (Redis or in-memory)"""
        
        # Try Redis first
        if self.redis_client:
            try:
                self.redis_client.delete(f"working_memory:{task_id}")
                logger.info(f"Cleared working memory from Redis for {task_id}")
                return
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
        
        # Fallback to in-memory
        if task_id in self.working_memory:
            del self.working_memory[task_id]
            logger.info(f"Cleared working memory (in-memory) for {task_id}")
    
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

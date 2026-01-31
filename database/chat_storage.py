"""
chat_storage.py

SQLite database for storing chat sessions and user interactions.
Used for session management and collecting training data from user interactions.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os


class ChatStorage:
    def __init__(self, db_path: str = "db/chat_history.db"):
        """Initialize chat storage with SQLite database."""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                title TEXT,
                message_count INTEGER DEFAULT 0
            )
        """)
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                reformulated_query TEXT,
                sources TEXT,
                relevance_scores TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # User interactions table (for training data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                message_id INTEGER,
                interaction_type TEXT NOT NULL,
                feedback TEXT,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id),
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(self, session_id: str, title: Optional[str] = None) -> bool:
        """Create a new chat session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO sessions (session_id, created_at, updated_at, title, message_count)
                VALUES (?, ?, ?, ?, 0)
            """, (session_id, now, now, title or f"Chat {session_id[:8]}"))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    def save_message(self, session_id: str, role: str, content: str, 
                     reformulated_query: Optional[str] = None,
                     sources: Optional[List[Dict]] = None) -> Optional[int]:
        """Save a message to the session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # Convert sources to JSON string
            sources_json = json.dumps(sources) if sources else None
            scores_json = json.dumps([s.get('score') for s in (sources or [])]) if sources else None
            
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, timestamp, reformulated_query, sources, relevance_scores)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, role, content, now, reformulated_query, sources_json, scores_json))
            
            message_id = cursor.lastrowid
            
            # Update session
            cursor.execute("""
                UPDATE sessions 
                SET updated_at = ?, message_count = message_count + 1
                WHERE session_id = ?
            """, (now, session_id))
            
            conn.commit()
            conn.close()
            return message_id
        except Exception as e:
            print(f"Error saving message: {e}")
            return None
    
    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Retrieve all messages for a session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, role, content, timestamp, reformulated_query, sources, relevance_scores
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row[0],
                    'role': row[1],
                    'content': row[2],
                    'timestamp': row[3],
                    'reformulated_query': row[4],
                    'sources': json.loads(row[5]) if row[5] else None,
                    'relevance_scores': json.loads(row[6]) if row[6] else None
                })
            
            conn.close()
            return messages
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def get_all_sessions(self, limit: int = 50) -> List[Dict]:
        """Get all chat sessions ordered by most recent."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT session_id, created_at, updated_at, title, message_count
                FROM sessions
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'created_at': row[1],
                    'updated_at': row[2],
                    'title': row[3],
                    'message_count': row[4]
                })
            
            conn.close()
            return sessions
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM user_interactions WHERE session_id = ?", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def log_interaction(self, session_id: str, message_id: Optional[int],
                       interaction_type: str, feedback: Optional[str] = None,
                       metadata: Optional[Dict] = None) -> bool:
        """Log user interaction for training data collection."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO user_interactions (session_id, message_id, interaction_type, feedback, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, message_id, interaction_type, feedback, metadata_json, now))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error logging interaction: {e}")
            return False
    
    def get_training_data(self, limit: Optional[int] = None) -> List[Dict]:
        """Export all interactions for training purposes."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT 
                    ui.id, ui.session_id, ui.message_id, ui.interaction_type,
                    ui.feedback, ui.metadata, ui.timestamp,
                    m.role, m.content, m.reformulated_query, m.sources
                FROM user_interactions ui
                LEFT JOIN messages m ON ui.message_id = m.id
                ORDER BY ui.timestamp DESC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            
            training_data = []
            for row in cursor.fetchall():
                training_data.append({
                    'interaction_id': row[0],
                    'session_id': row[1],
                    'message_id': row[2],
                    'interaction_type': row[3],
                    'feedback': row[4],
                    'metadata': json.loads(row[5]) if row[5] else None,
                    'timestamp': row[6],
                    'message_role': row[7],
                    'message_content': row[8],
                    'reformulated_query': row[9],
                    'sources': json.loads(row[10]) if row[10] else None
                })
            
            conn.close()
            return training_data
        except Exception as e:
            print(f"Error getting training data: {e}")
            return []
    
    def export_training_data(self, output_file: str) -> bool:
        """Export training data to JSON file."""
        try:
            data = self.get_training_data()
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting training data: {e}")
            return False

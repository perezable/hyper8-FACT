"""
Database initializer for Railway deployment.
Loads knowledge base from SQLite file on startup.
"""

import os
import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseInitializer:
    """Initialize database with pre-loaded knowledge base."""
    
    def __init__(self, db_path: str = "data/knowledge.db"):
        self.db_path = db_path
        self.initialized = False
        
    def check_database_exists(self) -> bool:
        """Check if the database file exists."""
        return os.path.exists(self.db_path)
    
    def load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load knowledge base from SQLite database."""
        if not self.check_database_exists():
            logger.warning(f"Database not found at {self.db_path}")
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Load all knowledge entries
            cursor.execute("""
                SELECT id, question, answer, category, state, tags, 
                       priority, difficulty, personas, source
                FROM knowledge_base
                ORDER BY id
            """)
            
            entries = []
            for row in cursor.fetchall():
                entry = dict(row)
                # Parse JSON fields
                import json
                if entry.get('tags'):
                    try:
                        entry['tags'] = json.loads(entry['tags'])
                    except:
                        entry['tags'] = []
                if entry.get('personas'):
                    try:
                        entry['personas'] = json.loads(entry['personas'])
                    except:
                        entry['personas'] = []
                entries.append(entry)
            
            conn.close()
            logger.info(f"Loaded {len(entries)} knowledge entries from database")
            return entries
            
        except Exception as e:
            logger.error(f"Error loading database: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        if not self.check_database_exists():
            return {"error": "Database not found"}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM knowledge_base")
            stats['total_entries'] = cursor.fetchone()[0]
            
            # Categories
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM knowledge_base 
                GROUP BY category
            """)
            stats['categories'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # States
            cursor.execute("""
                SELECT state, COUNT(*) as count 
                FROM knowledge_base 
                WHERE state IS NOT NULL 
                GROUP BY state
            """)
            stats['states'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Priorities
            cursor.execute("""
                SELECT priority, COUNT(*) as count 
                FROM knowledge_base 
                GROUP BY priority
            """)
            stats['priorities'] = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {"error": str(e)}

# Global instance
db_initializer = DatabaseInitializer()
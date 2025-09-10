"""
PostgreSQL adapter for Railway deployment.
Provides persistent storage for knowledge base data.
"""

import os
import json
import asyncio
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = structlog.get_logger(__name__)

# Try to import PostgreSQL libraries
try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
    logger.warning("asyncpg not available, falling back to psycopg2")

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 not available")


class PostgresAdapter:
    """Adapter for PostgreSQL database operations."""
    
    def __init__(self):
        """Initialize PostgreSQL adapter."""
        self.connection_string = os.getenv("DATABASE_URL")
        self.pool = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize database connection and create tables."""
        if not self.connection_string:
            logger.warning("No DATABASE_URL found, PostgreSQL not available")
            return False
            
        try:
            if ASYNCPG_AVAILABLE:
                await self._init_asyncpg()
            elif PSYCOPG2_AVAILABLE:
                self._init_psycopg2()
            else:
                logger.error("No PostgreSQL driver available")
                return False
                
            await self._create_tables()
            self.initialized = True
            logger.info("PostgreSQL adapter initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            return False
    
    async def _init_asyncpg(self):
        """Initialize asyncpg connection pool."""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        logger.info("asyncpg connection pool created")
    
    def _init_psycopg2(self):
        """Initialize psycopg2 connection."""
        # For psycopg2, we'll create connections on demand
        logger.info("Using psycopg2 for PostgreSQL")
    
    async def _create_tables(self):
        """Create knowledge base tables if they don't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id VARCHAR(50) PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category VARCHAR(100),
            state VARCHAR(10),
            tags TEXT,
            priority VARCHAR(20) DEFAULT 'normal',
            difficulty VARCHAR(20) DEFAULT 'basic',
            personas TEXT,
            source VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category);
        CREATE INDEX IF NOT EXISTS idx_kb_state ON knowledge_base(state);
        CREATE INDEX IF NOT EXISTS idx_kb_priority ON knowledge_base(priority);
        
        -- Full text search index for better search performance
        CREATE INDEX IF NOT EXISTS idx_kb_question_gin ON knowledge_base 
        USING gin(to_tsvector('english', question));
        
        CREATE INDEX IF NOT EXISTS idx_kb_answer_gin ON knowledge_base 
        USING gin(to_tsvector('english', answer));
        """
        
        if ASYNCPG_AVAILABLE and self.pool:
            async with self.pool.acquire() as conn:
                await conn.execute(create_table_sql)
        else:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()
            cursor.close()
            conn.close()
            
        logger.info("Knowledge base tables created/verified")
    
    async def get_all_entries(self) -> List[Dict[str, Any]]:
        """Get all knowledge base entries."""
        if not self.initialized:
            return []
            
        query = """
        SELECT id, question, answer, category, state, tags, 
               priority, difficulty, personas, source
        FROM knowledge_base
        ORDER BY priority, id
        """
        
        try:
            if ASYNCPG_AVAILABLE and self.pool:
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(query)
                    return [dict(row) for row in rows]
            else:
                conn = psycopg2.connect(self.connection_string)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                return rows
                
        except Exception as e:
            logger.error(f"Failed to get entries: {e}")
            return []
    
    async def insert_entries(self, entries: List[Dict[str, Any]], clear_existing: bool = False):
        """Insert knowledge base entries."""
        if not self.initialized:
            return False
            
        try:
            if clear_existing:
                await self.clear_all_entries()
            
            insert_query = """
            INSERT INTO knowledge_base 
            (id, question, answer, category, state, tags, priority, difficulty, personas, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ON CONFLICT (id) DO UPDATE SET
                question = EXCLUDED.question,
                answer = EXCLUDED.answer,
                category = EXCLUDED.category,
                state = EXCLUDED.state,
                tags = EXCLUDED.tags,
                priority = EXCLUDED.priority,
                difficulty = EXCLUDED.difficulty,
                personas = EXCLUDED.personas,
                source = EXCLUDED.source,
                updated_at = CURRENT_TIMESTAMP
            """
            
            if ASYNCPG_AVAILABLE and self.pool:
                async with self.pool.acquire() as conn:
                    for entry in entries:
                        await conn.execute(
                            insert_query,
                            entry.get('id', f'KB_{datetime.now().timestamp()}'),
                            entry.get('question', ''),
                            entry.get('answer', ''),
                            entry.get('category'),
                            entry.get('state'),
                            entry.get('tags'),
                            entry.get('priority', 'normal'),
                            entry.get('difficulty', 'basic'),
                            entry.get('personas'),
                            entry.get('source')
                        )
            else:
                conn = psycopg2.connect(self.connection_string)
                cursor = conn.cursor()
                for entry in entries:
                    cursor.execute(
                        insert_query.replace('$1', '%s').replace('$2', '%s').replace('$3', '%s')
                                   .replace('$4', '%s').replace('$5', '%s').replace('$6', '%s')
                                   .replace('$7', '%s').replace('$8', '%s').replace('$9', '%s')
                                   .replace('$10', '%s'),
                        (
                            entry.get('id', f'KB_{datetime.now().timestamp()}'),
                            entry.get('question', ''),
                            entry.get('answer', ''),
                            entry.get('category'),
                            entry.get('state'),
                            entry.get('tags'),
                            entry.get('priority', 'normal'),
                            entry.get('difficulty', 'basic'),
                            entry.get('personas'),
                            entry.get('source')
                        )
                    )
                conn.commit()
                cursor.close()
                conn.close()
                
            logger.info(f"Inserted {len(entries)} entries into PostgreSQL")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert entries: {e}")
            return False
    
    async def clear_all_entries(self):
        """Clear all knowledge base entries."""
        if not self.initialized:
            return
            
        try:
            if ASYNCPG_AVAILABLE and self.pool:
                async with self.pool.acquire() as conn:
                    await conn.execute("DELETE FROM knowledge_base")
            else:
                conn = psycopg2.connect(self.connection_string)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM knowledge_base")
                conn.commit()
                cursor.close()
                conn.close()
                
            logger.info("Cleared all knowledge base entries")
            
        except Exception as e:
            logger.error(f"Failed to clear entries: {e}")
    
    async def search_entries(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge base with full-text search."""
        if not self.initialized:
            return []
            
        search_query = """
        SELECT id, question, answer, category, state, tags, 
               priority, difficulty, personas, source,
               ts_rank(
                   to_tsvector('english', question || ' ' || answer),
                   plainto_tsquery('english', $1)
               ) as rank
        FROM knowledge_base
        WHERE to_tsvector('english', question || ' ' || answer) @@ plainto_tsquery('english', $1)
           OR question ILIKE '%' || $1 || '%'
           OR answer ILIKE '%' || $1 || '%'
        ORDER BY rank DESC, priority, id
        LIMIT $2
        """
        
        try:
            if ASYNCPG_AVAILABLE and self.pool:
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(search_query, query, limit)
                    return [dict(row) for row in rows]
            else:
                conn = psycopg2.connect(self.connection_string)
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(
                    search_query.replace('$1', '%s').replace('$2', '%s'),
                    (query, limit)
                )
                rows = cursor.fetchall()
                cursor.close()
                conn.close()
                return rows
                
        except Exception as e:
            logger.error(f"Failed to search entries: {e}")
            return []
    
    async def close(self):
        """Close database connections."""
        if ASYNCPG_AVAILABLE and self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")


# Global instance
postgres_adapter = PostgresAdapter()
"""
FACT System PostgreSQL Connection Management
Handles PostgreSQL database connections for Railway deployment.
"""

import os
import asyncpg
import asyncio
import time
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
import structlog

logger = structlog.get_logger(__name__)

class PostgreSQLManager:
    """
    Manages PostgreSQL database connections for the FACT system.
    Designed for Railway deployment with connection pooling.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize PostgreSQL manager.
        
        Args:
            database_url: PostgreSQL connection string
        """
        # Use Railway's DATABASE_URL environment variable
        self.database_url = database_url or os.getenv("DATABASE_URL")
        
        # For Railway internal connections
        if not self.database_url:
            # Try to construct from Railway environment
            host = os.getenv("PGHOST", "postgres.railway.internal")
            port = os.getenv("PGPORT", "5432")
            database = os.getenv("PGDATABASE", "railway")
            user = os.getenv("PGUSER", "postgres")
            password = os.getenv("PGPASSWORD")
            
            if password:
                self.database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            else:
                logger.error("No PostgreSQL connection configuration found")
                raise ValueError("DATABASE_URL environment variable not set")
        
        self.pool = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize connection pool and database schema."""
        if self._initialized:
            return
            
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60
            )
            
            # Ensure knowledge_base table exists
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_base (
                        id SERIAL PRIMARY KEY,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        category TEXT NOT NULL,
                        tags TEXT,
                        metadata TEXT,
                        state TEXT,
                        priority TEXT DEFAULT 'normal',
                        personas TEXT,
                        source TEXT,
                        difficulty TEXT DEFAULT 'basic',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes if they don't exist
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category);
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_kb_state ON knowledge_base(state);
                """)
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_kb_priority ON knowledge_base(priority);
                """)
                
                # Check entry count
                result = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")
                logger.info(f"PostgreSQL initialized with {result} knowledge base entries")
            
            self._initialized = True
            logger.info("PostgreSQL connection pool initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            
        Returns:
            List of result rows as dictionaries
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *args)
                execution_time = (time.time() - start_time) * 1000
                
                # Convert to list of dicts
                results = [dict(row) for row in rows]
                
                logger.debug(f"Query executed in {execution_time:.2f}ms, returned {len(results)} rows")
                return results
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def get_knowledge_entries(self, 
                                   category: Optional[str] = None,
                                   state: Optional[str] = None,
                                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get knowledge base entries with optional filtering.
        
        Args:
            category: Filter by category
            state: Filter by state
            limit: Maximum number of results
            
        Returns:
            List of knowledge entries
        """
        query = "SELECT * FROM knowledge_base WHERE 1=1"
        params = []
        param_count = 0
        
        if category:
            param_count += 1
            query += f" AND category = ${param_count}"
            params.append(category)
        
        if state:
            param_count += 1
            query += f" AND state = ${param_count}"
            params.append(state)
        
        query += f" LIMIT ${param_count + 1}"
        params.append(limit)
        
        return await self.execute_query(query, *params)
    
    async def search_knowledge(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search knowledge base using full text search.
        
        Args:
            search_term: Term to search for
            limit: Maximum number of results
            
        Returns:
            List of matching knowledge entries
        """
        query = """
            SELECT * FROM knowledge_base
            WHERE question ILIKE $1 OR answer ILIKE $1
            ORDER BY 
                CASE 
                    WHEN question ILIKE $1 THEN 1
                    ELSE 2
                END,
                priority DESC
            LIMIT $2
        """
        
        search_pattern = f"%{search_term}%"
        return await self.execute_query(query, search_pattern, limit)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self._initialized:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            stats = {}
            
            # Total entries
            stats['total_entries'] = await conn.fetchval(
                "SELECT COUNT(*) FROM knowledge_base"
            )
            
            # Entries by category
            category_results = await conn.fetch("""
                SELECT category, COUNT(*) as count
                FROM knowledge_base
                GROUP BY category
                ORDER BY count DESC
            """)
            stats['by_category'] = {row['category']: row['count'] for row in category_results}
            
            # Entries by state
            state_results = await conn.fetch("""
                SELECT state, COUNT(*) as count
                FROM knowledge_base
                WHERE state IS NOT NULL
                GROUP BY state
                ORDER BY count DESC
            """)
            stats['by_state'] = {row['state']: row['count'] for row in state_results}
            
            # Entries by priority
            priority_results = await conn.fetch("""
                SELECT priority, COUNT(*) as count
                FROM knowledge_base
                GROUP BY priority
            """)
            stats['by_priority'] = {row['priority']: row['count'] for row in priority_results}
            
            return stats
    
    async def insert_knowledge_entry(self, entry: Dict[str, Any]) -> int:
        """
        Insert a new knowledge base entry.
        
        Args:
            entry: Dictionary with entry data
            
        Returns:
            ID of inserted entry
        """
        query = """
            INSERT INTO knowledge_base 
            (question, answer, category, tags, metadata, state, priority, personas, source, difficulty)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
        """
        
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                entry.get('question'),
                entry.get('answer'),
                entry.get('category'),
                entry.get('tags'),
                entry.get('metadata'),
                entry.get('state'),
                entry.get('priority', 'normal'),
                entry.get('personas'),
                entry.get('source'),
                entry.get('difficulty', 'basic')
            )
            return result
    
    async def bulk_insert_knowledge(self, entries: List[Dict[str, Any]]) -> int:
        """
        Bulk insert knowledge base entries.
        
        Args:
            entries: List of entry dictionaries
            
        Returns:
            Number of inserted entries
        """
        if not entries:
            return 0
        
        async with self.pool.acquire() as conn:
            # Prepare data for bulk insert
            records = [
                (
                    entry.get('question'),
                    entry.get('answer'),
                    entry.get('category'),
                    entry.get('tags'),
                    entry.get('metadata'),
                    entry.get('state'),
                    entry.get('priority', 'normal'),
                    entry.get('personas'),
                    entry.get('source'),
                    entry.get('difficulty', 'basic')
                )
                for entry in entries
            ]
            
            # Use COPY for efficient bulk insert
            result = await conn.copy_records_to_table(
                'knowledge_base',
                records=records,
                columns=['question', 'answer', 'category', 'tags', 'metadata', 
                        'state', 'priority', 'personas', 'source', 'difficulty']
            )
            
            # Parse result to get count
            count = int(result.split()[-1]) if result else len(records)
            logger.info(f"Bulk inserted {count} knowledge entries")
            return count
    
    async def cleanup(self):
        """Close all database connections."""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get a database connection context manager.
        
        Yields:
            asyncpg.Connection: Database connection
        """
        if not self._initialized:
            await self.initialize()
        
        conn = await self.pool.acquire()
        try:
            yield conn
        finally:
            await self.pool.release(conn)
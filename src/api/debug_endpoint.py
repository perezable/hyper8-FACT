"""
Debug endpoint to check PostgreSQL data.
"""

from fastapi import APIRouter
import asyncpg
import os
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/postgres-check")
async def check_postgres():
    """Check what's actually in PostgreSQL."""
    
    if not os.getenv("DATABASE_URL"):
        return {"error": "No DATABASE_URL"}
    
    try:
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        
        try:
            # Count total entries
            total_count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")
            
            # Count by state
            state_query = """
            SELECT state, COUNT(*) as count 
            FROM knowledge_base 
            GROUP BY state 
            ORDER BY count DESC
            """
            state_rows = await conn.fetch(state_query)
            state_counts = {row['state']: row['count'] for row in state_rows}
            
            # Get sample entries
            sample_query = """
            SELECT id, question, answer, state 
            FROM knowledge_base 
            WHERE state = 'GA' 
            LIMIT 3
            """
            samples = await conn.fetch(sample_query)
            sample_list = [dict(row) for row in samples]
            
            # Search for specific query
            search_query = """
            SELECT id, question, answer, state
            FROM knowledge_base
            WHERE LOWER(question) LIKE '%contractor license%'
            OR LOWER(answer) LIKE '%contractor license%'
            LIMIT 5
            """
            search_results = await conn.fetch(search_query)
            search_list = [dict(row) for row in search_results]
            
            return {
                "total_entries": total_count,
                "state_counts": state_counts,
                "georgia_samples": sample_list,
                "search_results": search_list,
                "database_connected": True
            }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Debug check failed: {e}")
        return {"error": str(e)}
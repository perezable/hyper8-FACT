"""
Debug endpoint to see actual errors in query processing
"""

import os
from fastapi import APIRouter
import structlog
from datetime import datetime
import traceback

router = APIRouter(prefix="/api", tags=["debug"])
logger = structlog.get_logger(__name__)

@router.post("/debug-query")
async def debug_query(query: str):
    """Debug a query to see what's actually happening"""
    
    from shared_state import get_driver
    
    driver = get_driver()
    
    if not driver:
        return {
            "status": "error",
            "message": "Driver not initialized",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    try:
        # Try to process the query with detailed error tracking
        result = await driver.process_fact_query(query)
        
        return {
            "status": "success",
            "query": query,
            "response": result,
            "driver_initialized": driver._initialized,
            "has_groq_key": bool(driver.groq_api_key),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Get full traceback
        tb = traceback.format_exc()
        
        return {
            "status": "error",
            "query": query,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": tb,
            "driver_initialized": driver._initialized if driver else False,
            "has_groq_key": bool(driver.groq_api_key) if driver else False,
            "timestamp": datetime.utcnow().isoformat()
        }
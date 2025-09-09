"""
FACT System Web Server

This module provides a FastAPI web interface for the FACT system,
suitable for deployment on Railway and other cloud platforms.
"""

import os
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog

from core.driver import get_driver, shutdown_driver
from core.config import get_config
from core.errors import FACTError, ConfigurationError

logger = structlog.get_logger(__name__)


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    query: str = Field(..., description="Natural language query to process")
    cache_mode: Optional[str] = Field("read", description="Cache mode: 'read' or 'write'")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    response: str = Field(..., description="Generated response from FACT system")
    cached: bool = Field(False, description="Whether response was from cache")
    query_id: str = Field(..., description="Unique query identifier")
    timestamp: str = Field(..., description="Response timestamp")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    initialized: bool = Field(..., description="Whether system is initialized")
    version: str = Field(..., description="System version")
    timestamp: str = Field(..., description="Current timestamp")
    metrics: Optional[Dict[str, Any]] = Field(None, description="System metrics")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")
    timestamp: str = Field(..., description="Error timestamp")


# Global driver instance
_driver = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup and shutdown events.
    """
    global _driver
    
    # Startup
    logger.info("Starting FACT web server")
    try:
        config = get_config()
        _driver = await get_driver(config)
        logger.info("FACT system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize FACT system: {e}")
        # Don't prevent startup, allow health checks to report unhealthy
    
    yield
    
    # Shutdown
    logger.info("Shutting down FACT web server")
    if _driver:
        await shutdown_driver()
    logger.info("FACT web server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="FACT System API",
    description="Fast-Access Cached Tools system for intelligent query processing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint returns health status."""
    return await health()


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    
    Returns system status and metrics.
    """
    global _driver
    
    timestamp = datetime.utcnow().isoformat()
    
    if _driver is None:
        return HealthResponse(
            status="unhealthy",
            initialized=False,
            version="1.0.0",
            timestamp=timestamp,
            metrics=None
        )
    
    try:
        metrics = _driver.get_metrics()
        return HealthResponse(
            status="healthy",
            initialized=_driver._initialized,
            version="1.0.0",
            timestamp=timestamp,
            metrics=metrics
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="degraded",
            initialized=_driver._initialized if _driver else False,
            version="1.0.0",
            timestamp=timestamp,
            metrics=None
        )


@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    """
    Process a natural language query through the FACT system.
    
    Args:
        request: Query request containing the user's question
        background_tasks: FastAPI background tasks for async operations
        
    Returns:
        QueryResponse with the generated answer
        
    Raises:
        HTTPException: If query processing fails
    """
    global _driver
    
    if _driver is None or not _driver._initialized:
        raise HTTPException(
            status_code=503,
            detail="FACT system not initialized. Please try again later."
        )
    
    query_id = f"web_{int(datetime.utcnow().timestamp() * 1000)}"
    timestamp = datetime.utcnow().isoformat()
    
    try:
        logger.info(f"Processing web query: {query_id}")
        
        # Process the query
        response = await _driver.process_query(request.query)
        
        # Check if response was cached (simplified check)
        cached = "cache hit" in response.lower() if isinstance(response, str) else False
        
        return QueryResponse(
            response=response,
            cached=cached,
            query_id=query_id,
            timestamp=timestamp
        )
        
    except FACTError as e:
        logger.error(f"FACT error processing query {query_id}: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error processing query {query_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing your query."
        )


@app.get("/metrics", response_model=Dict[str, Any])
async def get_metrics():
    """
    Get detailed system metrics.
    
    Returns:
        Dictionary containing performance metrics
    """
    global _driver
    
    if _driver is None:
        raise HTTPException(
            status_code=503,
            detail="FACT system not initialized"
        )
    
    try:
        metrics = _driver.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve system metrics"
        )


@app.post("/initialize")
async def initialize_system():
    """
    Manually initialize the FACT system.
    
    This endpoint can be used to retry initialization if it failed on startup.
    """
    global _driver
    
    try:
        if _driver and _driver._initialized:
            return {"status": "already_initialized", "message": "System is already initialized"}
        
        config = get_config()
        _driver = await get_driver(config)
        
        return {
            "status": "success",
            "message": "FACT system initialized successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ConfigurationError as e:
        logger.error(f"Configuration error during initialization: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Initialization failed: {str(e)}"
        )


def start_server(host: str = "0.0.0.0", port: int = None):
    """
    Start the FastAPI server.
    
    Args:
        host: Host to bind to (default: 0.0.0.0 for all interfaces)
        port: Port to listen on (default: from PORT env var or 8000)
    """
    # Get port from environment or use default
    if port is None:
        port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting FACT web server on {host}:{port}")
    
    # Configure uvicorn
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        use_colors=True
    )
    
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    """
    Run the web server directly.
    
    Usage:
        python web_server.py
    """
    start_server()
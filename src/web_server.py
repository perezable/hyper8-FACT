"""
FACT System Web Server

This module provides a FastAPI web interface for the FACT system,
suitable for deployment on Railway and other cloud platforms.
"""

import os
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
from datetime import datetime
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import structlog
import tempfile
import json

from core.driver import get_driver, shutdown_driver
from core.config import get_config
from core.errors import FACTError, ConfigurationError, ValidationError
from data_upload import DataUploader

# Import the knowledge API router
try:
    from api.knowledge_api import router as knowledge_router
    KNOWLEDGE_API_AVAILABLE = True
except ImportError:
    KNOWLEDGE_API_AVAILABLE = False
    logger = structlog.get_logger(__name__)
    logger.warning("Knowledge API module not available")

# Import the VAPI webhook router
try:
    from api.vapi_webhook import router as vapi_router
    VAPI_WEBHOOK_AVAILABLE = True
except ImportError:
    VAPI_WEBHOOK_AVAILABLE = False
    logger = structlog.get_logger(__name__)
    logger.warning("VAPI webhook module not available")

# Import the enhanced retriever
try:
    from retrieval.enhanced_search import EnhancedRetriever
    ENHANCED_SEARCH_AVAILABLE = True
except ImportError:
    ENHANCED_SEARCH_AVAILABLE = False
    logger = structlog.get_logger(__name__)
    logger.warning("Enhanced search module not available")

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


class KnowledgeSearchRequest(BaseModel):
    """Request model for knowledge base search."""
    query: str = Field(..., description="Search query for knowledge base")
    category: Optional[str] = Field(None, description="Filter by category")
    state: Optional[str] = Field(None, description="Filter by state")
    difficulty: Optional[str] = Field(None, description="Filter by difficulty level")
    limit: Optional[int] = Field(10, description="Maximum number of results")


class KnowledgeEntry(BaseModel):
    """Model for knowledge base entry."""
    id: int = Field(..., description="Entry ID")
    question: str = Field(..., description="Question or topic")
    answer: str = Field(..., description="Answer or explanation")
    category: str = Field(..., description="Category")
    tags: Optional[str] = Field(None, description="Tags")
    state: Optional[str] = Field(None, description="State code")
    priority: str = Field(..., description="Priority level")
    difficulty: str = Field(..., description="Difficulty level")
    personas: Optional[str] = Field(None, description="Target personas")
    source: Optional[str] = Field(None, description="Source reference")


class KnowledgeSearchResponse(BaseModel):
    """Response model for knowledge base search."""
    results: List[KnowledgeEntry] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of results found")
    query: str = Field(..., description="Original search query")
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


class DataUploadRequest(BaseModel):
    """Request model for data upload endpoint."""
    data_type: str = Field(..., description="Type of data: 'companies', 'financial_records', or 'knowledge_base'")
    data: List[Dict[str, Any]] = Field(..., description="Array of data records")
    clear_existing: bool = Field(False, description="Whether to clear existing data first")


class DataUploadResponse(BaseModel):
    """Response model for data upload endpoint."""
    status: str = Field(..., description="Upload status")
    records_uploaded: int = Field(..., description="Number of records uploaded")
    cleared_existing: bool = Field(..., description="Whether existing data was cleared")
    timestamp: str = Field(..., description="Upload timestamp")


class DataTemplateResponse(BaseModel):
    """Response model for data template endpoint."""
    description: str = Field(..., description="Template description")
    required_fields: List[str] = Field(..., description="Required fields")
    optional_fields: List[str] = Field(..., description="Optional fields")
    example_data: List[Dict[str, Any]] = Field(..., description="Example data records")
    field_descriptions: Dict[str, str] = Field(..., description="Field descriptions")


# Global driver instance
_driver = None
# Global enhanced retriever instance
_enhanced_retriever = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup and shutdown events.
    """
    global _driver, _enhanced_retriever
    
    # Startup
    logger.info("Starting FACT web server")
    try:
        config = get_config()
        _driver = await get_driver(config)
        logger.info("FACT system initialized successfully")
        
        # Initialize enhanced retriever if available
        if ENHANCED_SEARCH_AVAILABLE:
            try:
                # Initialize with None - the retriever will load data directly from database
                _enhanced_retriever = EnhancedRetriever(None)
                await _enhanced_retriever.initialize()
                logger.info("Enhanced retriever initialized successfully")
            except Exception as e:
                logger.warning(f"Enhanced retriever initialization failed: {e}")
                _enhanced_retriever = None
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
# Configure CORS based on environment - defaults to permissive for testing
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if cors_origins_env:
    # If CORS_ORIGINS is explicitly set, use it
    cors_origins = cors_origins_env.split(",")
else:
    # Default to permissive CORS for testing
    cors_origins = ["*"]
    logger.warning("CORS is permissive (allowing all origins). Set CORS_ORIGINS env var for production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if cors_origins != ["*"] else False,  # Credentials not allowed with wildcard
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include the knowledge API router if available
if KNOWLEDGE_API_AVAILABLE:
    app.include_router(knowledge_router)
    logger.info("Knowledge API endpoints loaded")

# Include the VAPI webhook router if available
if VAPI_WEBHOOK_AVAILABLE:
    app.include_router(vapi_router)
    logger.info("VAPI webhook endpoints loaded")


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


@app.post("/upload-data", response_model=DataUploadResponse)
async def upload_data(request: DataUploadRequest):
    """
    Upload custom data to replace sample data.
    
    Supports uploading companies, financial records, or knowledge base data.
    """
    try:
        uploader = DataUploader()
        
        if request.data_type == "companies":
            result = await uploader.upload_companies(
                request.data, 
                clear_existing=request.clear_existing
            )
        elif request.data_type == "financial_records":
            result = await uploader.upload_financial_records(
                request.data,
                clear_existing=request.clear_existing
            )
        elif request.data_type == "knowledge_base":
            result = await uploader.upload_knowledge_base(
                request.data,
                clear_existing=request.clear_existing
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid data_type. Must be 'companies', 'financial_records', or 'knowledge_base'"
            )
        
        return DataUploadResponse(
            status=result["status"],
            records_uploaded=result.get("companies_uploaded", result.get("records_uploaded", 0)),
            cleared_existing=result["cleared_existing"],
            timestamp=result["timestamp"]
        )
        
    except ValidationError as e:
        logger.error(f"Data validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Data upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Data upload failed: {str(e)}"
        )


@app.post("/upload-file")
async def upload_file(
    data_type: str = Form(...),
    clear_existing: bool = Form(False),
    file: UploadFile = File(...)
):
    """
    Upload data from CSV or JSON file.
    
    Args:
        data_type: Type of data ('companies', 'financial_records', or 'knowledge_base')
        clear_existing: Whether to clear existing data first
        file: CSV or JSON file containing data
    """
    if data_type not in ["companies", "financial_records", "knowledge_base"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid data_type. Must be 'companies', 'financial_records', or 'knowledge_base'"
        )
    
    # Check file type
    filename = file.filename.lower() if file.filename else ""
    if not (filename.endswith('.csv') or filename.endswith('.json')):
        raise HTTPException(
            status_code=400,
            detail="File must be CSV or JSON format"
        )
    
    try:
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            uploader = DataUploader()
            
            if filename.endswith('.csv'):
                result = await uploader.load_from_csv(
                    temp_file_path, 
                    data_type, 
                    clear_existing
                )
            else:  # JSON
                result = await uploader.load_from_json(
                    temp_file_path, 
                    data_type, 
                    clear_existing
                )
            
            return {
                "status": result["status"],
                "records_uploaded": result.get("companies_uploaded", result.get("records_uploaded", 0)),
                "cleared_existing": result["cleared_existing"],
                "filename": file.filename,
                "timestamp": result["timestamp"]
            }
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except ValidationError as e:
        logger.error(f"File upload validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )


@app.get("/data-template/{data_type}", response_model=DataTemplateResponse)
async def get_data_template(data_type: str):
    """
    Get data upload template with example data and field descriptions.
    
    Args:
        data_type: Type of template ('companies', 'financial_records', or 'knowledge_base')
    """
    try:
        uploader = DataUploader()
        template = await uploader.get_upload_template(data_type)
        
        return DataTemplateResponse(**template)
        
    except ValidationError as e:
        logger.error(f"Invalid template request: {e}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get template: {str(e)}"
        )


@app.delete("/data/{data_type}")
async def clear_data(data_type: str):
    """
    Clear existing data from specified table.
    
    Args:
        data_type: Type of data to clear ('companies', 'financial_records', or 'all')
    """
    valid_types = {"companies", "financial_records", "all"}
    
    if data_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid data_type. Must be one of: {valid_types}"
        )
    
    try:
        uploader = DataUploader()
        
        if data_type == "all":
            # Clear all data tables
            await uploader.clear_existing_data("financial_records")
            await uploader.clear_existing_data("financial_data")
            await uploader.clear_existing_data("companies")
            message = "All data cleared successfully"
        else:
            await uploader.clear_existing_data(data_type)
            if data_type == "financial_records":
                # Also clear financial_data for consistency
                await uploader.clear_existing_data("financial_data")
            message = f"{data_type} data cleared successfully"
        
        return {
            "status": "success",
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear data: {str(e)}"
        )


@app.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge_base(request: KnowledgeSearchRequest):
    """
    Search the knowledge base for relevant Q&A entries.
    
    Supports filtering by category, state, difficulty, and text search.
    Uses enhanced retriever when available for better matching.
    """
    try:
        global _driver, _enhanced_retriever
        if _driver is None:
            raise HTTPException(
                status_code=503,
                detail="FACT system not initialized"
            )
        
        # Use enhanced retriever if available
        if _enhanced_retriever and request.query:
            # Use enhanced search for better matching
            search_results = await _enhanced_retriever.search(
                query=request.query,
                category=request.category,
                state=request.state,
                limit=request.limit
            )
            
            # Convert search results to response format
            results = []
            for sr in search_results:
                results.append(KnowledgeEntry(
                    id=sr.id,
                    question=sr.question,
                    answer=sr.answer,
                    category=sr.category,
                    tags=sr.metadata.get("tags"),
                    state=sr.state,
                    priority=sr.metadata.get("priority", "normal"),
                    difficulty=sr.metadata.get("difficulty", "basic"),
                    personas=sr.metadata.get("personas"),
                    source=sr.metadata.get("source"),
                    metadata={
                        "score": sr.score,
                        "confidence": sr.confidence,
                        "match_type": sr.match_type,
                        "retrieval_time_ms": sr.retrieval_time_ms
                    }
                ))
            
            return KnowledgeSearchResponse(
                results=results,
                total_count=len(results),
                query=request.query,
                timestamp=datetime.utcnow().isoformat()
            )
        
        # Fall back to SQL search if enhanced retriever not available
        # Build SQL query with filters
        query_parts = ["SELECT * FROM knowledge_base WHERE 1=1"]
        
        # Add text search on question and answer fields
        if request.query:
            query_parts.append("AND (question LIKE '%{}%' OR answer LIKE '%{}%' OR tags LIKE '%{}%')".format(
                request.query.replace("'", "''"),  # Basic SQL injection prevention
                request.query.replace("'", "''"),
                request.query.replace("'", "''")
            ))
        
        # Add category filter
        if request.category:
            safe_category = request.category.replace("'", "''")
            query_parts.append(f"AND category = '{safe_category}'")
        
        # Add state filter
        if request.state:
            safe_state = request.state.upper().replace("'", "''")
            query_parts.append(f"AND state = '{safe_state}'")
        
        # Add difficulty filter
        if request.difficulty:
            safe_difficulty = request.difficulty.lower().replace("'", "''")
            query_parts.append(f"AND difficulty = '{safe_difficulty}'")
        
        # Order by priority and limit results
        query_parts.append("ORDER BY CASE priority WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END, id")
        query_parts.append(f"LIMIT {min(request.limit, 1000)}")  # Cap at 1000 results for larger knowledge bases
        
        sql_query = " ".join(query_parts)
        
        # Execute query
        db_result = await _driver.database_manager.execute_query(sql_query)
        
        # Convert to response format
        results = []
        for row in db_result.rows:
            results.append(KnowledgeEntry(
                id=row["id"],
                question=row["question"],
                answer=row["answer"],
                category=row["category"],
                tags=row.get("tags"),
                state=row.get("state"),
                priority=row["priority"],
                difficulty=row["difficulty"],
                personas=row.get("personas"),
                source=row.get("source")
            ))
        
        return KnowledgeSearchResponse(
            results=results,
            total_count=len(results),
            query=request.query,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Knowledge base search failed: {str(e)}"
        )


@app.get("/knowledge/categories")
async def get_knowledge_categories():
    """
    Get all available knowledge base categories with counts.
    """
    try:
        global _driver
        if _driver is None:
            raise HTTPException(
                status_code=503,
                detail="FACT system not initialized"
            )
        
        # Get category counts
        sql_query = """
            SELECT category, 
                   COUNT(*) as count,
                   COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical_count,
                   COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_count
            FROM knowledge_base 
            GROUP BY category 
            ORDER BY count DESC
        """
        
        result = await _driver.database_manager.execute_query(sql_query)
        
        categories = []
        for row in result.rows:
            categories.append({
                "category": row["category"],
                "count": row["count"],
                "critical_count": row["critical_count"],
                "high_count": row["high_count"]
            })
        
        return {
            "categories": categories,
            "total_categories": len(categories),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get categories: {str(e)}"
        )


@app.get("/knowledge/states")
async def get_knowledge_states():
    """
    Get all states that have knowledge base entries.
    """
    try:
        global _driver
        if _driver is None:
            raise HTTPException(
                status_code=503,
                detail="FACT system not initialized"
            )
        
        sql_query = """
            SELECT state, COUNT(*) as count
            FROM knowledge_base 
            WHERE state IS NOT NULL AND state != ''
            GROUP BY state 
            ORDER BY count DESC
        """
        
        result = await _driver.database_manager.execute_query(sql_query)
        
        states = []
        for row in result.rows:
            states.append({
                "state": row["state"],
                "count": row["count"]
            })
        
        return {
            "states": states,
            "total_states": len(states),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get states: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get states: {str(e)}"
        )


@app.get("/knowledge/stats")
async def get_knowledge_stats():
    """
    Get knowledge base statistics and overview.
    """
    try:
        global _driver
        if _driver is None:
            raise HTTPException(
                status_code=503,
                detail="FACT system not initialized"
            )
        
        # Get overall stats
        stats_query = """
            SELECT 
                COUNT(*) as total_entries,
                COUNT(DISTINCT category) as total_categories,
                COUNT(DISTINCT state) as total_states,
                COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical_priority,
                COUNT(CASE WHEN priority = 'high' THEN 1 END) as high_priority,
                COUNT(CASE WHEN priority = 'normal' THEN 1 END) as normal_priority,
                COUNT(CASE WHEN difficulty = 'basic' THEN 1 END) as basic_difficulty,
                COUNT(CASE WHEN difficulty = 'intermediate' THEN 1 END) as intermediate_difficulty,
                COUNT(CASE WHEN difficulty = 'advanced' THEN 1 END) as advanced_difficulty
            FROM knowledge_base
        """
        
        result = await _driver.database_manager.execute_query(stats_query)
        
        if result.rows:
            stats = result.rows[0]
            return {
                "total_entries": stats["total_entries"],
                "total_categories": stats["total_categories"],
                "total_states": stats["total_states"],
                "priority_breakdown": {
                    "critical": stats["critical_priority"],
                    "high": stats["high_priority"],
                    "normal": stats["normal_priority"]
                },
                "difficulty_breakdown": {
                    "basic": stats["basic_difficulty"],
                    "intermediate": stats["intermediate_difficulty"],
                    "advanced": stats["advanced_difficulty"]
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "total_entries": 0,
                "message": "No knowledge base entries found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get knowledge stats: {str(e)}"
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
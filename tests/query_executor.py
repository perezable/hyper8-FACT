"""
Query Executor for FACT System Testing

Handles multiple query methods including direct database access,
VAPI webhook calls, and API endpoint calls with retry logic and error handling.
"""

import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import asyncpg
import aiosqlite
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)


class QueryMethod(Enum):
    """Available query methods for testing"""
    DATABASE = "database"
    VAPI = "vapi"
    API = "api"


@dataclass 
class QueryResult:
    """Result from a single query execution"""
    query_id: str
    method: str
    query_text: str
    success: bool
    response: Optional[Dict[str, Any]]
    response_time_ms: float
    error_message: Optional[str] = None
    attempt_count: int = 1
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class TestQuestion:
    """Test question with metadata"""
    id: str
    text: str
    category: str
    state: Optional[str] = None
    expected_keywords: List[str] = None
    difficulty: str = "medium"
    
    def __post_init__(self):
        if self.expected_keywords is None:
            self.expected_keywords = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class RetryHandler:
    """Handles retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 30.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt == self.max_retries:
                    break
                
                # Calculate delay with exponential backoff
                delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
                logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        raise last_exception


class DatabaseQueryExecutor:
    """Executes queries against the database directly"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.is_postgres = False
        self.retry_handler = RetryHandler(
            max_retries=config.max_retries,
            base_delay=config.retry_delay
        )
    
    async def initialize(self):
        """Initialize database connection"""
        try:
            database_url = self.config.database_url
            if not database_url:
                raise ValueError("No database URL configured")
            
            if database_url.startswith("postgresql://") or database_url.startswith("postgres://"):
                # PostgreSQL connection
                self.is_postgres = True
                self.connection = await asyncpg.connect(database_url)
                logger.info("Connected to PostgreSQL database")
            
            elif database_url.startswith("sqlite://"):
                # SQLite connection
                db_path = database_url.replace("sqlite:///", "").replace("sqlite://", "")
                if not Path(db_path).exists():
                    # Try alternative paths
                    if Path(f"data/{db_path}").exists():
                        db_path = f"data/{db_path}"
                    elif Path("fact_system.db").exists():
                        db_path = "fact_system.db"
                
                self.connection = await aiosqlite.connect(db_path)
                logger.info(f"Connected to SQLite database: {db_path}")
            
            else:
                raise ValueError(f"Unsupported database URL format: {database_url}")
                
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def execute_query(self, question: TestQuestion) -> QueryResult:
        """Execute query against database using enhanced search"""
        start_time = time.time()
        query_id = f"db_{question.id}_{int(time.time())}"
        
        try:
            result = await self.retry_handler.execute_with_retry(
                self._perform_database_query, question
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return QueryResult(
                query_id=query_id,
                method="database",
                query_text=question.text,
                success=True,
                response=result,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return QueryResult(
                query_id=query_id,
                method="database",
                query_text=question.text,
                success=False,
                response=None,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
    
    async def _perform_database_query(self, question: TestQuestion) -> Dict[str, Any]:
        """Perform the actual database query using enhanced retriever"""
        try:
            # Import enhanced retriever
            from retrieval.enhanced_search import EnhancedRetriever
            
            # Create retriever instance
            retriever = EnhancedRetriever(None)
            
            # Initialize with current database connection
            if self.is_postgres:
                # For PostgreSQL, load entries directly
                import os
                os.environ["DATABASE_URL"] = self.config.database_url
                await retriever.initialize()
            else:
                # For SQLite, set the connection
                retriever.db_manager = type('MockDBManager', (), {
                    'get_connection': lambda: type('MockConn', (), {
                        'execute': self.connection.execute,
                        '__aenter__': lambda: self,
                        '__aexit__': lambda *args: None
                    })()
                })()
                await retriever.initialize()
            
            # Perform search
            search_results = await retriever.search(
                query=question.text,
                category=question.category if hasattr(question, 'category') else None,
                state=question.state,
                limit=3
            )
            
            if search_results:
                best_result = search_results[0]
                return {
                    "answer": best_result.answer,
                    "question": best_result.question,
                    "category": best_result.category,
                    "state": best_result.state,
                    "confidence": best_result.confidence,
                    "score": best_result.score,
                    "match_type": best_result.match_type,
                    "retrieval_time_ms": best_result.retrieval_time_ms,
                    "source": "database_direct"
                }
            else:
                return {
                    "answer": "No relevant information found in the knowledge base.",
                    "confidence": 0.0,
                    "source": "database_direct",
                    "query": question.text
                }
                
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup database connection"""
        try:
            if self.connection:
                if self.is_postgres:
                    await self.connection.close()
                else:
                    await self.connection.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")


class VAPIQueryExecutor:
    """Executes queries via VAPI webhook"""
    
    def __init__(self, config):
        self.config = config
        self.session = None
        self.retry_handler = RetryHandler(
            max_retries=config.max_retries,
            base_delay=config.retry_delay
        )
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info("VAPI query executor initialized")
    
    async def execute_query(self, question: TestQuestion) -> QueryResult:
        """Execute query via VAPI webhook"""
        start_time = time.time()
        query_id = f"vapi_{question.id}_{int(time.time())}"
        
        try:
            result = await self.retry_handler.execute_with_retry(
                self._perform_vapi_query, question
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return QueryResult(
                query_id=query_id,
                method="vapi",
                query_text=question.text,
                success=True,
                response=result,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return QueryResult(
                query_id=query_id,
                method="vapi",
                query_text=question.text,
                success=False,
                response=None,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
    
    async def _perform_vapi_query(self, question: TestQuestion) -> Dict[str, Any]:
        """Perform the actual VAPI webhook call"""
        if not self.config.vapi_webhook_url:
            raise ValueError("VAPI webhook URL not configured")
        
        # Prepare VAPI webhook payload
        payload = {
            "message": {
                "type": "function-call",
                "functionCall": {
                    "name": "searchKnowledge",
                    "parameters": {
                        "query": question.text,
                        "state": question.state,
                        "category": question.category if hasattr(question, 'category') else None,
                        "limit": 3
                    }
                }
            },
            "call": {
                "id": f"test_call_{question.id}",
                "assistantId": "test_assistant",
                "phoneNumber": "+1234567890"
            },
            "metadata": {
                "test_mode": True,
                "question_id": question.id
            }
        }
        
        # Remove None values
        if payload["message"]["functionCall"]["parameters"]["state"] is None:
            del payload["message"]["functionCall"]["parameters"]["state"]
        if payload["message"]["functionCall"]["parameters"]["category"] is None:
            del payload["message"]["functionCall"]["parameters"]["category"]
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FACT-Test-Runner/1.0"
        }
        
        async with self.session.post(
            self.config.vapi_webhook_url,
            json=payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                # Extract result from VAPI response format
                if "result" in data:
                    result = data["result"]
                    result["source"] = "vapi_webhook"
                    result["vapi_metadata"] = data.get("metadata", {})
                    return result
                else:
                    return {
                        "answer": str(data),
                        "source": "vapi_webhook",
                        "raw_response": data
                    }
            else:
                error_text = await response.text()
                raise Exception(f"VAPI webhook returned {response.status}: {error_text}")
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        try:
            if self.session:
                await self.session.close()
                logger.info("VAPI session closed")
        except Exception as e:
            logger.error(f"Error during VAPI cleanup: {e}")


class APIQueryExecutor:
    """Executes queries via REST API endpoints"""
    
    def __init__(self, config):
        self.config = config
        self.session = None
        self.retry_handler = RetryHandler(
            max_retries=config.max_retries,
            base_delay=config.retry_delay
        )
    
    async def initialize(self):
        """Initialize HTTP session"""
        timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info("API query executor initialized")
    
    async def execute_query(self, question: TestQuestion) -> QueryResult:
        """Execute query via REST API"""
        start_time = time.time()
        query_id = f"api_{question.id}_{int(time.time())}"
        
        try:
            result = await self.retry_handler.execute_with_retry(
                self._perform_api_query, question
            )
            
            response_time_ms = (time.time() - start_time) * 1000
            
            return QueryResult(
                query_id=query_id,
                method="api",
                query_text=question.text,
                success=True,
                response=result,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return QueryResult(
                query_id=query_id,
                method="api",
                query_text=question.text,
                success=False,
                response=None,
                response_time_ms=response_time_ms,
                error_message=str(e)
            )
    
    async def _perform_api_query(self, question: TestQuestion) -> Dict[str, Any]:
        """Perform the actual API call"""
        if not self.config.api_base_url:
            raise ValueError("API base URL not configured")
        
        # Try multiple possible API endpoints
        endpoints = [
            "/search",
            "/api/search", 
            "/knowledge/search",
            "/v1/search"
        ]
        
        for endpoint in endpoints:
            url = self.config.api_base_url.rstrip('/') + endpoint
            
            try:
                # Prepare API payload
                payload = {
                    "query": question.text,
                    "limit": 3
                }
                
                # Add optional parameters
                if question.state:
                    payload["state"] = question.state
                if hasattr(question, 'category') and question.category:
                    payload["category"] = question.category
                
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "FACT-Test-Runner/1.0"
                }
                
                async with self.session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Normalize API response format
                        if isinstance(data, dict):
                            result = data.copy()
                            result["source"] = "api_endpoint"
                            result["endpoint"] = endpoint
                            return result
                        elif isinstance(data, list) and data:
                            return {
                                "results": data,
                                "answer": data[0].get("answer", str(data[0])),
                                "source": "api_endpoint",
                                "endpoint": endpoint
                            }
                        else:
                            return {
                                "answer": str(data),
                                "source": "api_endpoint",
                                "endpoint": endpoint,
                                "raw_response": data
                            }
                    
                    elif response.status == 404:
                        # Try next endpoint
                        continue
                    else:
                        error_text = await response.text()
                        logger.warning(f"API endpoint {endpoint} returned {response.status}: {error_text}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Failed to query endpoint {endpoint}: {e}")
                continue
        
        # If all endpoints failed
        raise Exception("All API endpoints failed or returned errors")
    
    async def cleanup(self):
        """Cleanup HTTP session"""
        try:
            if self.session:
                await self.session.close()
                logger.info("API session closed")
        except Exception as e:
            logger.error(f"Error during API cleanup: {e}")


class QueryExecutor:
    """
    Main query executor that manages different query methods.
    
    Provides a unified interface for executing queries against
    the FACT system using various methods.
    """
    
    def __init__(self, config):
        self.config = config
        self.executors = {}
        
        # Initialize executors for configured methods
        if "database" in config.query_methods:
            self.executors["database"] = DatabaseQueryExecutor(config)
        if "vapi" in config.query_methods:
            self.executors["vapi"] = VAPIQueryExecutor(config) 
        if "api" in config.query_methods:
            self.executors["api"] = APIQueryExecutor(config)
    
    async def initialize(self):
        """Initialize all configured executors"""
        logger.info("Initializing query executors...")
        
        for method, executor in self.executors.items():
            try:
                await executor.initialize()
                logger.info(f"Initialized {method} executor")
            except Exception as e:
                logger.error(f"Failed to initialize {method} executor: {e}")
                # Remove failed executor
                del self.executors[method]
        
        if not self.executors:
            raise Exception("No query executors could be initialized")
        
        logger.info(f"Query executor ready with methods: {list(self.executors.keys())}")
    
    async def execute_query(self, method: QueryMethod, question: TestQuestion) -> QueryResult:
        """Execute query using specified method"""
        method_name = method.value
        
        if method_name not in self.executors:
            return QueryResult(
                query_id=f"error_{question.id}",
                method=method_name,
                query_text=question.text,
                success=False,
                response=None,
                response_time_ms=0.0,
                error_message=f"Query method {method_name} not available"
            )
        
        try:
            return await self.executors[method_name].execute_query(question)
        except Exception as e:
            logger.error(f"Query execution failed for method {method_name}: {e}")
            return QueryResult(
                query_id=f"error_{question.id}",
                method=method_name,
                query_text=question.text,
                success=False,
                response=None,
                response_time_ms=0.0,
                error_message=str(e)
            )
    
    async def execute_multiple_methods(self, question: TestQuestion) -> List[QueryResult]:
        """Execute query using all available methods"""
        results = []
        
        for method_name in self.executors.keys():
            method = QueryMethod(method_name)
            result = await self.execute_query(method, question)
            results.append(result)
        
        return results
    
    def get_available_methods(self) -> List[str]:
        """Get list of available query methods"""
        return list(self.executors.keys())
    
    async def cleanup(self):
        """Cleanup all executors"""
        logger.info("Cleaning up query executors...")
        
        for method, executor in self.executors.items():
            try:
                await executor.cleanup()
                logger.info(f"Cleaned up {method} executor")
            except Exception as e:
                logger.error(f"Error cleaning up {method} executor: {e}")


# Convenience functions for testing individual components
async def test_database_query():
    """Test database query executor"""
    from fact_test_runner import create_default_config
    
    config = create_default_config("local")
    executor = DatabaseQueryExecutor(config)
    
    try:
        await executor.initialize()
        
        question = TestQuestion(
            id="test_1",
            text="What are the requirements for a contractor license in Georgia?",
            category="state_licensing_requirements",
            state="GA"
        )
        
        result = await executor.execute_query(question)
        print(f"Database Query Result: {result}")
        
    finally:
        await executor.cleanup()


async def test_vapi_query():
    """Test VAPI query executor"""
    from fact_test_runner import create_default_config
    
    config = create_default_config("railway")
    executor = VAPIQueryExecutor(config)
    
    try:
        await executor.initialize()
        
        question = TestQuestion(
            id="test_2",
            text="How much does a Georgia contractor license cost?",
            category="state_licensing_requirements", 
            state="GA"
        )
        
        result = await executor.execute_query(question)
        print(f"VAPI Query Result: {result}")
        
    finally:
        await executor.cleanup()


if __name__ == "__main__":
    # Test individual executors
    import asyncio
    
    print("Testing Database Query Executor...")
    asyncio.run(test_database_query())
    
    print("\nTesting VAPI Query Executor...")
    asyncio.run(test_vapi_query())
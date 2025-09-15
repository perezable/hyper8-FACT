"""
FACT System Core Driver with Groq API Integration
Modified version using Groq instead of Anthropic for faster, cost-effective inference.
"""

import asyncio
import json
import os
import time
import uuid
import hashlib
from typing import Dict, List, Any, Optional
import structlog

# Import Groq adapter instead of Anthropic
from .groq_client import GroqAdapter

from .config import Config, get_config, validate_configuration
from .errors import (
    FACTError, ConfigurationError, ConnectionError, ToolExecutionError,
    classify_error, create_user_friendly_message, log_error_with_context,
    provide_graceful_degradation, CacheError
)

try:
    from ..db.connection import DatabaseManager
    from ..tools.decorators import get_tool_registry
    from ..tools.connectors.sql import initialize_sql_tool
    from ..monitoring.metrics import get_metrics_collector
    from ..cache import initialize_cache_system, get_cache_system, FACTCacheSystem
    from ..cache.resilience import ResilientCacheWrapper, CacheCircuitBreaker
except ImportError:
    import sys
    from pathlib import Path
    src_path = str(Path(__file__).parent.parent)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    from db.connection import DatabaseManager
    from tools.decorators import get_tool_registry
    from tools.connectors.sql import initialize_sql_tool
    from monitoring.metrics import get_metrics_collector
    from cache import initialize_cache_system, get_cache_system, FACTCacheSystem
    from cache.resilience import ResilientCacheWrapper, CacheCircuitBreaker

logger = structlog.get_logger(__name__)

def create_groq_client(api_key: str):
    """
    Create a Groq client with Anthropic-compatible interface.
    
    Args:
        api_key: Groq API key
        
    Returns:
        Configured Groq client with Anthropic-compatible interface
    """
    try:
        client = GroqAdapter(api_key=api_key)
        logger.debug("Successfully created Groq client")
        return client
    except Exception as e:
        logger.error(f"Failed to create Groq client: {e}")
        raise

class FACTDriver:
    """
    Core driver for the FACT system using Groq API.
    Modified to use Groq's fast inference instead of Anthropic.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize FACT driver with optional configuration."""
        self.config = config or get_config()
        self.database_manager: Optional[DatabaseManager] = None
        self.tool_registry = get_tool_registry()
        self.metrics_collector = get_metrics_collector()
        self.cache_system: Optional[FACTCacheSystem] = None
        self._initialized = False
        
        # Track conversation history
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Groq-specific configuration
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not found, will use fallback responses")
        
        logger.info("FACT driver initialized with Groq integration")
    
    async def initialize(self) -> None:
        """Initialize all FACT system components."""
        if self._initialized:
            logger.debug("Driver already initialized, skipping")
            return
        
        try:
            logger.info("Starting FACT driver initialization")
            
            # Initialize database
            self.database_manager = DatabaseManager(self.config.database_path)
            await self.database_manager.initialize_database()
            logger.info("Database initialized")
            
            # Initialize tools
            initialize_sql_tool(self.database_manager)
            logger.info(f"Tools initialized: {len(self.tool_registry.list_tools())} tools registered")
            
            # Initialize cache system
            try:
                cache_config = {
                    "redis_url": os.getenv("REDIS_URL"),
                    "ttl_seconds": 3600,
                    "max_size_mb": 100,
                    "circuit_breaker_threshold": 5,
                    "circuit_breaker_timeout": 60
                }
                self.cache_system = await initialize_cache_system(cache_config)
                logger.info("Cache system initialized")
            except Exception as e:
                logger.warning(f"Cache initialization failed (non-critical): {e}")
                self.cache_system = None
            
            # Test connections
            await self._test_connections()
            
            self._initialized = True
            logger.info("FACT driver initialization completed successfully")
            
        except Exception as e:
            log_error_with_context(e, {"phase": "initialization"})
            raise ConfigurationError(f"Failed to initialize FACT driver: {e}")
    
    async def _test_connections(self) -> None:
        """Test database and LLM connections."""
        try:
            # Test database
            if self.database_manager:
                test_query = "SELECT 1"
                result = await self.database_manager.execute_query(test_query)
                logger.info("Database connection test passed")
            
            # Test Groq LLM connection
            if self.groq_api_key:
                max_retries = 3
                retry_delay = 2
                
                for attempt in range(max_retries):
                    try:
                        client = create_groq_client(self.groq_api_key)
                        test_response = client.messages.create(
                            model="openai/gpt-oss-120b",
                            messages=[{"role": "user", "content": "Test"}],
                            max_tokens=10
                        )
                        logger.info("Groq LLM connection test passed")
                        break
                    except Exception as e:
                        error_str = str(e)
                        if "rate_limit" in error_str.lower():
                            if attempt < max_retries - 1:
                                wait_time = retry_delay * (attempt + 1)
                                logger.warning(f"Groq API rate limited, retrying in {wait_time}s")
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                logger.warning("Groq API rate limited after retries")
                                break
                        else:
                            logger.warning(f"Groq LLM test failed: {e}")
                            break
            else:
                logger.warning("Skipping Groq LLM test - no API key")
                
        except Exception as e:
            logger.warning(f"Connection tests failed (non-critical): {e}")
    
    async def process_fact_query(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        cache_mode: str = "read"
    ) -> str:
        """
        Process a FACT query using Groq API.
        
        Args:
            user_input: The user's query
            context: Optional context for the query
            cache_mode: Cache mode (read/write/bypass)
            
        Returns:
            The response text
        """
        query_id = f"query_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            if not self._initialized:
                await self.initialize()
            
            # Check cache first
            if self.cache_system and cache_mode in ["read", "write"]:
                cache_key = f"fact_query:{hashlib.md5(user_input.encode()).hexdigest()}"
                cached_response = await self.cache_system.get(cache_key)
                
                if cached_response and cache_mode == "read":
                    logger.info("Cache hit for query", query_id=query_id)
                    return cached_response.get("response", "")
            
            # Prepare messages
            messages = [{"role": "user", "content": user_input}]
            
            # Add conversation history if available
            if self.conversation_history:
                messages = self.conversation_history[-10:] + messages
            
            # Make LLM call with Groq
            if not self.groq_api_key:
                # Fallback response when no API key
                response_text = "I apologize, but I'm unable to process your request at the moment. The Groq API key is not configured."
            else:
                client = create_groq_client(self.groq_api_key)
                
                response = client.messages.create(
                    model="openai/gpt-oss-120b",  # Using GPT-OSS-120B as requested
                    system=self.config.system_prompt,
                    messages=messages,
                    max_tokens=2048,
                    temperature=0.7,
                    tools=self._get_tool_definitions() if self.tool_registry else None
                )
                
                # Handle tool calls if present
                tool_use_blocks = []
                if hasattr(response, 'content') and response.content:
                    for content_block in response.content:
                        if content_block.get("type") == "tool_use":
                            tool_use_blocks.append(content_block)
                
                # Execute tools if needed
                if tool_use_blocks:
                    tool_results = []
                    for tool_block in tool_use_blocks:
                        tool_name = tool_block.get("name")
                        tool_input = tool_block.get("input", {})
                        tool_id = tool_block.get("id")
                        
                        result = await self._execute_tool(tool_name, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": json.dumps(result) if not isinstance(result, str) else result
                        })
                    
                    # Get final response with tool results
                    messages.append({
                        "role": "assistant",
                        "content": response.content
                    })
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                    
                    response = client.messages.create(
                        model="openai/gpt-oss-120b",
                        system=self.config.system_prompt,
                        messages=messages,
                        max_tokens=2048,
                        temperature=0.7
                    )
                
                # Extract response text
                response_text = ""
                if hasattr(response, 'content') and response.content:
                    for content_block in response.content:
                        if content_block.get("type") == "text":
                            response_text += content_block.get("text", "")
                
                if not response_text:
                    response_text = str(response) if response else "No response generated"
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Cache the response
            if self.cache_system and cache_mode == "write":
                await self.cache_system.set(
                    cache_key,
                    {"response": response_text, "timestamp": time.time()},
                    ttl=3600
                )
            
            # Record metrics
            execution_time = (time.time() - start_time) * 1000
            self.metrics_collector.record_query(
                query_id=query_id,
                execution_time_ms=execution_time,
                cache_hit=False,
                tokens_used=len(response_text.split())
            )
            
            logger.info(
                "Query processed successfully",
                query_id=query_id,
                execution_time_ms=execution_time
            )
            
            return response_text
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            log_error_with_context(e, {
                "query_id": query_id,
                "user_input": user_input[:100],
                "execution_time_ms": execution_time
            })
            
            # Classify and handle error
            error_type, error_category = classify_error(e)
            
            # Record error metric
            self.metrics_collector.record_error(
                error_type=error_type,
                error_category=error_category,
                context={"query_id": query_id}
            )
            
            # Provide graceful degradation
            fallback_response = provide_graceful_degradation(error_category)
            if fallback_response:
                return fallback_response
            
            # Create user-friendly message
            user_message = create_user_friendly_message(error_category, str(e))
            return user_message
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions in format expected by Groq."""
        tools = []
        for tool_name in self.tool_registry.list_tools():
            tool_def = self.tool_registry.get_tool(tool_name)
            if tool_def and hasattr(tool_def, 'metadata'):
                metadata = tool_def.metadata
                tools.append({
                    "name": metadata.get("name"),
                    "description": metadata.get("description", ""),
                    "input_schema": metadata.get("inputSchema", {})
                })
        return tools
    
    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a tool and return its result."""
        start_time = time.time()
        
        try:
            tool_definition = self.tool_registry.get_tool(tool_name)
            if not tool_definition:
                raise ToolExecutionError(f"Tool '{tool_name}' not found")
            
            # Add driver context for tools that need it
            if "context" not in tool_input:
                tool_input["context"] = {"driver": self}
            
            # Execute tool
            if asyncio.iscoroutinefunction(tool_definition.function):
                result = await tool_definition.function(**tool_input)
            else:
                result = tool_definition.function(**tool_input)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Record successful execution
            self.metrics_collector.record_tool_execution(
                tool_name=tool_name,
                execution_time_ms=execution_time,
                success=True
            )
            
            logger.info(
                "Tool executed successfully",
                tool_name=tool_name,
                execution_time_ms=execution_time
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Record failed execution
            self.metrics_collector.record_tool_execution(
                tool_name=tool_name,
                execution_time_ms=execution_time,
                success=False
            )
            
            logger.error(
                "Tool execution failed",
                tool_name=tool_name,
                error=str(e),
                execution_time_ms=execution_time
            )
            
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics.
        
        Returns:
            Dictionary containing system metrics
        """
        if self.metrics_collector:
            system_metrics = self.metrics_collector.get_system_metrics()
            return {
                "total_executions": system_metrics.total_executions,
                "successful_executions": system_metrics.successful_executions,
                "failed_executions": system_metrics.failed_executions,
                "average_execution_time": system_metrics.average_execution_time,
                "error_rate": system_metrics.error_rate,
                "executions_per_minute": system_metrics.executions_per_minute,
                "initialized": self._initialized
            }
        return {
            "initialized": self._initialized,
            "message": "Metrics not available"
        }
    
    async def shutdown(self) -> None:
        """Shutdown the FACT driver and cleanup resources."""
        try:
            if self.database_manager:
                await self.database_manager.cleanup()
            
            if self.cache_system:
                await self.cache_system.close()
            
            self._initialized = False
            logger.info("FACT driver shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Global driver instance
_driver_instance: Optional[FACTDriver] = None

def get_driver(config: Optional[Config] = None) -> FACTDriver:
    """Get or create the global FACT driver instance."""
    global _driver_instance
    if _driver_instance is None:
        _driver_instance = FACTDriver(config)
    return _driver_instance

async def shutdown_driver():
    """Shutdown the global driver instance."""
    global _driver_instance
    if _driver_instance:
        await _driver_instance.shutdown()
        _driver_instance = None
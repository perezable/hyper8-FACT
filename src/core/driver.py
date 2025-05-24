"""
FACT System Main Driver

This module implements the central orchestrator for the FACT system,
managing cache, queries, and tool execution following the architecture specification.
"""

import asyncio
import time
import os
from typing import Dict, List, Any, Optional
import structlog

# Import Anthropic SDK directly (LiteLLM has compatibility issues)
import anthropic

from .config import Config, get_config, validate_configuration
from .errors import (
    FACTError, ConfigurationError, ConnectionError, ToolExecutionError,
    classify_error, create_user_friendly_message, log_error_with_context,
    provide_graceful_degradation
)
try:
    # Try relative imports first (when used as package)
    from ..db.connection import DatabaseManager
    from ..tools.decorators import get_tool_registry
    from ..tools.connectors.sql import initialize_sql_tool
    from ..monitoring.metrics import get_metrics_collector
    from ..cache import initialize_cache_system, get_cache_system, FACTCacheSystem
except ImportError:
    # Fall back to absolute imports (when run as script)
    import sys
    from pathlib import Path
    # Add src to path if not already there
    src_path = str(Path(__file__).parent.parent)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    from db.connection import DatabaseManager
    from tools.decorators import get_tool_registry
    from tools.connectors.sql import initialize_sql_tool
    from monitoring.metrics import get_metrics_collector
    from cache import initialize_cache_system, get_cache_system, FACTCacheSystem


logger = structlog.get_logger(__name__)

class FACTDriver:
    """
    
    Manages cache control, query processing, tool execution, and system coordination
    following the FACT architecture principles.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize FACT driver with configuration.
        
        Args:
            config: Optional configuration instance (creates default if None)
        """
        self.config = config or get_config()
        self.database_manager: Optional[DatabaseManager] = None
        self.tool_registry = get_tool_registry()
        self.cache_system: Optional[FACTCacheSystem] = None
        self._initialized = False
        
        # Monitoring and metrics
        self.metrics_collector = get_metrics_collector()
        
    async def initialize(self) -> None:
        """
        Initialize the FACT system components.
        
        Raises:
            ConfigurationError: If configuration is invalid
            ConnectionError: If service connections fail
        """
        if self._initialized:
            logger.info("FACT driver already initialized")
            return
            
        try:
            logger.info("Initializing FACT system")
            
            # Validate configuration
            validate_configuration(self.config)
            
            # Initialize database
            await self._initialize_database()
            
            # Initialize cache system
            await self._initialize_cache()
            
            # Initialize tools
            await self._initialize_tools()
            
            # Test connections
            await self._test_connections()
            
            self._initialized = True
            logger.info("FACT system initialized successfully")
            
        except Exception as e:
            logger.error("FACT system initialization failed", error=str(e))
            raise ConfigurationError(f"System initialization failed: {e}")
    
    async def process_query(self, user_input: str) -> str:
        """
        Process a user query through the FACT pipeline.
        
        Args:
            user_input: Natural language query from user
            
        Returns:
            Generated response string
            
        Raises:
            FACTError: If query processing fails
        """
        if not self._initialized:
            await self.initialize()
            
        query_id = f"query_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            logger.info("Processing user query", query_id=query_id, query=user_input[:100])
            
            # Step 1: Check cache first (cache-first pattern)
            cached_response = None
            if self.cache_system:
                cached_response = await self.cache_system.get_cached_response(user_input)
            
            if cached_response:
                # Cache hit - return cached response
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                
                logger.info("Cache hit - returning cached response",
                           query_id=query_id,
                           latency_ms=latency)
                
                return cached_response
            
            # Step 2: Cache miss - process query normally
            logger.info("Cache miss - processing query with LLM", query_id=query_id)
            
            # Prepare messages for LLM
            messages = [
                {
                    "role": "user",
                    "content": user_input
                }
            ]
            
            # Get tool schemas for LLM
            tool_schemas = self.tool_registry.export_all_schemas()
            
            # Make initial LLM call with cache control
            response = await self._call_llm_with_cache(
                messages=messages,
                tools=tool_schemas,
                cache_mode="read"
            )
            
            # Handle tool calls if present
            if hasattr(response, 'tool_calls') and response.tool_calls:
                logger.info("Processing tool calls", count=len(response.tool_calls))
                
                # Execute tool calls
                tool_results = await self._execute_tool_calls(response.tool_calls)
                
                # Add tool results to message history
                messages.extend(tool_results)
                
                # Get final response with tool results
                response = await self._call_llm_with_cache(
                    messages=messages,
                    tools=tool_schemas,
                    cache_mode="read"
                )
            
            # Extract response content from Anthropic SDK response
            if hasattr(response, 'content') and response.content:
                response_text = response.content[0].text
            else:
                response_text = str(response)
            
            # Step 3: Store response in cache for future use
            if self.cache_system and response_text:
                cache_stored = await self.cache_system.store_response(user_input, response_text)
                if cache_stored:
                    logger.debug("Response stored in cache", query_id=query_id)
                else:
                    logger.debug("Response not suitable for caching", query_id=query_id)
            
            # Log performance metrics
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            logger.info("Query processed successfully",
                       query_id=query_id,
                       latency_ms=latency,
                       response_length=len(response_text))
            
            return response_text
            
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            # Record error in metrics collector
            self.metrics_collector.record_tool_execution(
                tool_name="fact_query",
                success=False,
                execution_time=latency,
                error_type=type(e).__name__,
                metadata={"query_id": query_id}
            )
            
            # Log error with context
            log_error_with_context(e, {
                "query_id": query_id,
                "user_input": user_input[:100],
                "latency_ms": latency
            })
            
            # Handle error with graceful degradation
            error_category = classify_error(e)
            
            if error_category in ["connectivity", "tool_execution"]:
                return provide_graceful_degradation(error_category)
            else:
                return create_user_friendly_message(e)
    
    async def _initialize_database(self) -> None:
        """Initialize database connection and schema."""
        try:
            self.database_manager = DatabaseManager(self.config.database_path)
            await self.database_manager.initialize_database()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error("Database initialization failed", error=str(e))
            raise ConfigurationError(f"Database initialization failed: {e}")
    
    async def _initialize_cache(self) -> None:
        """Initialize cache system with configuration."""
        try:
            cache_config = self.config.cache_config
            self.cache_system = await initialize_cache_system(
                config=cache_config,
                enable_background_tasks=True
            )
            logger.info("Cache system initialized successfully",
                       prefix=cache_config["prefix"],
                       max_size=cache_config["max_size"])
            
        except Exception as e:
            logger.error("Cache system initialization failed", error=str(e))
            raise ConfigurationError(f"Cache system initialization failed: {e}")
    
    async def _initialize_tools(self) -> None:
        """Initialize and register system tools."""
        try:
            # Initialize SQL tool with database manager
            initialize_sql_tool(self.database_manager)
            
            # Log registered tools
            tool_info = self.tool_registry.get_tool_info()
            logger.info("Tools initialized", **tool_info)
            
        except Exception as e:
            logger.error("Tool initialization failed", error=str(e))
            raise ConfigurationError(f"Tool initialization failed: {e}")
    
    async def _test_connections(self) -> None:
        """Test connections to external services."""
        try:
            # Test database connection
            if self.database_manager:
                await self.database_manager.get_database_info()
                logger.info("Database connection test passed")
            
            # Test LLM connection with direct Anthropic SDK
            client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
            test_response = client.messages.create(
                model=self.config.claude_model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            
            if test_response:
                logger.info("LLM connection test passed")
            
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            raise ConnectionError(f"Service connection test failed: {e}")
    
    async def _call_llm_with_cache(self, 
                                   messages: List[Dict[str, Any]], 
                                   tools: List[Dict[str, Any]], 
                                   cache_mode: str = "read") -> Any:
        """
        Call LLM with cache control and tool support.
        
        Args:
            messages: Message history for LLM
            tools: Available tools for LLM
            cache_mode: Cache mode ('read' or 'write')
            
        Returns:
            LLM response object
        """
        try:
            # Configure cache control
            cache_control = {
                "mode": cache_mode,
                "prefix": self.config.cache_prefix
            }
            
            # Track cache behavior
            # Cache hits/misses can be tracked via tool execution metadata if needed
            
            # Make LLM call with direct Anthropic SDK
            client = anthropic.Anthropic(api_key=self.config.anthropic_api_key)
            
            # Anthropic API requires system prompt as separate parameter, not in messages
            response = client.messages.create(
                model=self.config.claude_model,
                system=self.config.system_prompt,
                messages=messages,
                max_tokens=4096,
                timeout=self.config.request_timeout,
                # Note: tools parameter would be added when tool integration is complete
                # tools=tools if tools else None,
            )
            
            return response
            
        except Exception as e:
            logger.error("LLM call failed", error=str(e), cache_mode=cache_mode)
            raise ConnectionError(f"LLM call failed: {e}")
    
    async def _execute_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """
        Execute tool calls and format results as messages.
        
        Args:
            tool_calls: List of tool calls from LLM
            
        Returns:
            List of tool result messages
        """
        tool_messages = []
        
        for call in tool_calls:
            try:
                # Record tool execution in metrics_collector
                
                # Extract tool information
                tool_name = call.function.name if hasattr(call, 'function') else call.name
                tool_args = call.function.arguments if hasattr(call, 'function') else call.arguments
                
                # Parse arguments if they're a string
                if isinstance(tool_args, str):
                    import json
                    tool_args = json.loads(tool_args)
                
                # Get tool definition
                tool_definition = self.tool_registry.get_tool(tool_name)
                
                # Execute tool
                result = await tool_definition.function(**tool_args)
                
                # Format as tool message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": getattr(call, 'id', f"call_{int(time.time())}"),
                    "content": str(result) if not isinstance(result, str) else result
                }
                
                logger.info("Tool executed successfully",
                           tool_name=tool_name,
                           execution_time=result.get("execution_time_ms", 0))
                self.metrics_collector.record_tool_execution(
                    tool_name=tool_name,
                    success=True,
                    execution_time=result.get("execution_time_ms", 0),
                    metadata={"args": tool_args}
                )
                
            except Exception as e:
                logger.error("Tool execution failed",
                           tool_name=tool_name,
                           error=str(e))
                self.metrics_collector.record_tool_execution(
                    tool_name=tool_name,
                    success=False,
                    execution_time=0,
                    error_type=str(e),
                    metadata={"args": tool_args}
                )
                
                # Format error as tool message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": getattr(call, 'id', f"call_{int(time.time())}"),
                    "content": str({
                        "error": "Tool execution failed",
                        "details": str(e),
                        "status": "failed"
                    })
                }
            
            tool_messages.append(tool_message)
        
        return tool_messages
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system performance metrics.
        
        Returns:
            Dictionary containing performance metrics
        """
        # Use the unified metrics collector for system metrics
        sys_metrics = self.metrics_collector.get_system_metrics()
        
        # Get cache metrics if cache system is available
        cache_metrics = {}
        if self.cache_system:
            try:
                # Get basic cache metrics directly
                basic_cache_metrics = self.cache_system.cache_manager.get_metrics()
                cache_metrics = {
                    "cache_hit_rate": basic_cache_metrics.hit_rate,
                    "cache_hits": basic_cache_metrics.cache_hits,
                    "cache_misses": basic_cache_metrics.cache_misses,
                    "cache_total_entries": basic_cache_metrics.total_entries,
                    "cache_total_size": basic_cache_metrics.total_size,
                    "cache_token_efficiency": basic_cache_metrics.token_efficiency
                }
            except Exception as e:
                logger.warning("Failed to get cache metrics", error=str(e))
                cache_metrics = {
                    "cache_hit_rate": 0,
                    "cache_hits": 0,
                    "cache_misses": 0
                }
        else:
            cache_metrics = {
                "cache_hit_rate": 0,
                "cache_hits": 0,
                "cache_misses": 0
            }
        
        return {
            "total_queries": sys_metrics.total_executions,
            "tool_executions": sys_metrics.total_executions,
            "error_rate": sys_metrics.error_rate,
            "initialized": self._initialized,
            **cache_metrics
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the FACT system."""
        logger.info("Shutting down FACT system")
        
        # Shutdown cache system
        if self.cache_system:
            await self.cache_system.shutdown()
            self.cache_system = None
        
        # Close database connections
        if self.database_manager:
            # Database manager handles its own cleanup
            pass
        
        self._initialized = False
        logger.info("FACT system shutdown complete")


# Global driver instance
_driver_instance: Optional[FACTDriver] = None


async def get_driver(config: Optional[Config] = None) -> FACTDriver:
    """
    Get or create the global FACT driver instance.
    
    Args:
        config: Optional configuration (only used for first creation)
        
    Returns:
        Initialized FACTDriver instance
    """
    global _driver_instance
    
    if _driver_instance is None:
        _driver_instance = FACTDriver(config)
        await _driver_instance.initialize()
    
    return _driver_instance


async def shutdown_driver() -> None:
    """Shutdown the global driver instance."""
    global _driver_instance
    
    if _driver_instance:
        await _driver_instance.shutdown()
        _driver_instance = None


async def process_user_query(query: str) -> str:
    """
    Process user query using the global driver instance.
    
    This is a compatibility wrapper for the benchmarking framework.
    
    Args:
        query: User query string
        
    Returns:
        Response string
    """
    driver = await get_driver()
    return await driver.process_query(query)
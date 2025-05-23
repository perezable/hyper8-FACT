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

# Import OpenAI for LLM calls
import openai

from src.core.config import Config, get_config, validate_configuration
from src.core.errors import (
    FACTError, ConfigurationError, ConnectionError, ToolExecutionError,
    classify_error, create_user_friendly_message, log_error_with_context,
    provide_graceful_degradation
)
from src.core.conversation import get_conversation_manager
from src.db.connection import DatabaseManager
from src.tools.decorators import get_tool_registry
from src.tools.connectors.sql import initialize_sql_tool
from src.monitoring.metrics import get_metrics_collector


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
        self._initialized = False
        
        # Initialize OpenAI client
        self.openai_client = openai.AsyncOpenAI(api_key=self.config.openai_api_key)
        
        # Monitoring and metrics
        self.metrics_collector = get_metrics_collector()
        
        # Conversation management
        self.conversation_manager = get_conversation_manager()
        self.conversation_id = self.conversation_manager.start_conversation()
        
        # Agentic flow orchestrator (lazy import to avoid circular dependency)
        self._agentic_orchestrator = None
        
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
            
            # Initialize tools
            await self._initialize_tools()
            
            # Test connections
            await self._test_connections()
            
            self._initialized = True
            logger.info("FACT system initialized successfully")
            
        except Exception as e:
            logger.error("FACT system initialization failed", error=str(e))
            raise ConfigurationError(f"System initialization failed: {e}")
    
    def _get_agentic_orchestrator(self):
        """Get or create agentic flow orchestrator."""
        if self._agentic_orchestrator is None:
            from src.core.agentic_flow import AgenticFlowOrchestrator
            self._agentic_orchestrator = AgenticFlowOrchestrator(self)
        return self._agentic_orchestrator
    
    async def process_query(self, user_input: str, use_agentic_flow: bool = True) -> str:
        """
        Process a user query through the FACT pipeline.
        
        Args:
            user_input: Natural language query from user
            use_agentic_flow: Whether to use agentic flow for complex queries (default: True)
            
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
            logger.info("Processing user query", query_id=query_id, query=(user_input[:100] if user_input else None))
            
            # Check if this is a complex query that needs orchestrated flow
            if use_agentic_flow:
                orchestrator = self._get_agentic_orchestrator()
                is_complex, _ = orchestrator.analyze_query_complexity(user_input)
                
                if is_complex:
                    logger.info("Using agentic flow for complex query")
                    response_text = await orchestrator.execute_flow(user_input)
                    
                    # Add to conversation history
                    self.conversation_manager.add_turn(
                        user_input=user_input,
                        assistant_response=response_text,
                        tool_calls=[],
                        tool_results=[]
                    )
                    
                    # Log performance metrics
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000
                    
                    logger.info("Complex query processed successfully",
                               query_id=query_id,
                               latency_ms=latency,
                               response_length=len(response_text) if response_text else 0)
                    
                    return response_text
            
            # Standard processing for simple queries or when agentic flow is disabled
            logger.info("Using standard processing")
            
            # Standard processing for simple queries
            # Increment metrics
            # Metrics: total_queries is tracked as executions in metrics_collector
            
            # Prepare messages for LLM with enhanced system prompt
            enhanced_system_prompt = self.conversation_manager.enhance_system_prompt(
                self.config.system_prompt, user_input
            )
            
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
                cache_mode="read",
                system_prompt=enhanced_system_prompt
            )
            
            # Handle tool calls if present
            tool_calls = None
            tool_results = None
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_calls = response.tool_calls
            elif hasattr(response, 'choices') and response.choices and hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                tool_calls = response.choices[0].message.tool_calls
                
            if tool_calls:
                logger.info("Processing tool calls", count=len(tool_calls))
                
                # Add the assistant's tool call message to history
                messages.append({
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": call.type,
                            "function": {
                                "name": call.function.name,
                                "arguments": call.function.arguments
                            }
                        } for call in tool_calls
                    ]
                })
                
                # Execute tool calls
                tool_results = await self._execute_tool_calls(tool_calls)
                
                # Add tool results to message history
                messages.extend(tool_results)
                
                # Get final response with tool results (without tools to force a text response)
                response = await self._call_llm_with_cache(
                    messages=messages,
                    tools=None,  # Don't provide tools for final response to force text output
                    cache_mode="read"
                )
            
            # Extract response content
            logger.debug("Processing LLM response", response_type=type(response).__name__, has_content=hasattr(response, 'content'), has_choices=hasattr(response, 'choices'))
            
            # Debug the full response structure
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                message = choice.message
                logger.debug("Response structure",
                           message_content=message.content,
                           has_tool_calls=hasattr(message, 'tool_calls'),
                           tool_calls_value=getattr(message, 'tool_calls', None))
            
            if hasattr(response, 'content'):
                response_text = response.content
                logger.debug("Using response.content", content_length=len(response_text) if response_text else 0)
            elif hasattr(response, 'choices') and response.choices:
                response_text = response.choices[0].message.content
                logger.debug("Using choices[0].message.content", content_length=len(response_text) if response_text else 0)
            else:
                response_text = str(response)
                logger.debug("Using str(response)", content_length=len(response_text) if response_text else 0)
            
            # Handle None response - check if we have tool results to extract content from
            if response_text is None:
                # If we executed tools successfully, try to extract meaningful content from tool results
                if tool_calls and tool_results:
                    logger.info("LLM response content is None but tools were executed, extracting content from tool results")
                    response_text = self._extract_content_from_tool_results(tool_results)
                
                # If we still don't have content, use fallback
                if response_text is None:
                    logger.warning("LLM response content is None and no tool results available, using fallback message")
                    response_text = "I apologize, but I encountered an issue processing your request. Please try again."
            
            # Check if response seems incomplete
            if self.conversation_manager.detect_incomplete_response(user_input, response_text):
                logger.info("Detected incomplete response, attempting continuation")
                
                # Add continuation prompt and try again
                continuation_messages = messages + [
                    {
                        "role": "assistant",
                        "content": response_text
                    },
                    {
                        "role": "user",
                        "content": self.conversation_manager.get_continuation_prompt()
                    }
                ]
                
                # Make continuation call
                continuation_response = await self._call_llm_with_cache(
                    messages=continuation_messages,
                    tools=tool_schemas,
                    cache_mode="read",
                    system_prompt=enhanced_system_prompt
                )
                
                # Extract continuation content
                if hasattr(continuation_response, 'choices') and continuation_response.choices:
                    continuation_text = continuation_response.choices[0].message.content
                    if continuation_text:
                        response_text = continuation_text
                        logger.info("Successfully generated continuation response")
            
            # Add conversation turn
            self.conversation_manager.add_turn(
                user_input=user_input,
                assistant_response=response_text,
                tool_calls=[{
                    "name": call.function.name if hasattr(call, 'function') else call.name,
                    "arguments": call.function.arguments if hasattr(call, 'function') else call.arguments
                } for call in (tool_calls or [])],
                tool_results=tool_results
            )
            
            # Log performance metrics
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            logger.info("Query processed successfully",
                       query_id=query_id,
                       latency_ms=latency,
                       response_length=len(response_text) if response_text else 0)
            
            return response_text
            
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            
            # Record error metrics
            self.metrics_collector.record_tool_execution(
                tool_name="system_error",
                success=False,
                execution_time=0,
                error_type=str(e),
                metadata={"query": user_input[:100] if user_input else None}
            )
            
            # Log error with context
            log_error_with_context(e, {
                "query_id": query_id,
                "user_input": user_input[:100] if user_input else None,
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
            
            # Test LLM connection with a simple call using OpenAI client
            test_response = await self.openai_client.chat.completions.create(
                model=self.config.claude_model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )
            
            if test_response:
                logger.info("LLM connection test passed")
            
        except Exception as e:
            logger.error("Connection test failed", error=str(e))
            logger.warning("LLM connection test failed, but system will continue initialization")
            # Don't raise the error - allow system to continue without LLM validation
            # This allows the system to be used for database operations even if LLM is misconfigured
    
    async def _call_llm_with_cache(self,
                                   messages: List[Dict[str, Any]],
                                   tools: List[Dict[str, Any]],
                                   cache_mode: str = "read",
                                   system_prompt: Optional[str] = None) -> Any:
        """
        Call LLM with cache control and tool support.
        
        Args:
            messages: Message history for LLM
            tools: Available tools for LLM
            cache_mode: Cache mode ('read' or 'write')
            system_prompt: Optional override for system prompt
            
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
            
            # Use provided system prompt or default
            effective_system_prompt = system_prompt or self.config.system_prompt
            
            # Make LLM call with OpenAI client
            response = await self.openai_client.chat.completions.create(
                model=self.config.claude_model,
                messages=[
                    {"role": "system", "content": effective_system_prompt},
                    *messages
                ],
                tools=tools if tools else None,
                timeout=self.config.request_timeout,
                # Note: Cache control would be implemented based on actual OpenAI API support
                # cache_control=cache_control
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
                
                # Convert underscores back to dots for registry lookup
                registry_tool_name = tool_name.replace('_', '.')
                
                # Get tool definition
                tool_definition = self.tool_registry.get_tool(registry_tool_name)
                
                # Execute tool (handle both sync and async functions)
                result = tool_definition.function(**tool_args)
                
                # Check if result is a coroutine and await it if so
                if asyncio.iscoroutine(result):
                    result = await result
                
                # Format as tool message
                tool_message = {
                    "role": "tool",
                    "tool_call_id": getattr(call, 'id', f"call_{int(time.time())}"),
                    "content": str(result) if not isinstance(result, str) else result
                }
                
                logger.info("Tool executed successfully",
                           tool_name=registry_tool_name,
                           execution_time=result.get("execution_time_ms", 0))
                self.metrics_collector.record_tool_execution(
                    tool_name=registry_tool_name,
                    success=True,
                    execution_time=result.get("execution_time_ms", 0),
                    metadata={"args": tool_args}
                )
                
            except Exception as e:
                logger.error("Tool execution failed",
                           tool_name=registry_tool_name,
                           error=str(e))
                self.metrics_collector.record_tool_execution(
                    tool_name=registry_tool_name,
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
    
    def _extract_content_from_tool_results(self, tool_results: List[Dict[str, Any]]) -> Optional[str]:
        """
        Extract meaningful content from tool execution results.
        
        Args:
            tool_results: List of tool result messages
            
        Returns:
            Formatted content string or None if no meaningful content found
        """
        if not tool_results:
            return None
            
        meaningful_results = []
        
        for result in tool_results:
            if result.get("role") == "tool" and result.get("content"):
                content = result["content"]
                
                # Try to parse JSON content for better formatting
                try:
                    import json
                    parsed_content = json.loads(content)
                    
                    # Check if it's a structured result with data
                    if isinstance(parsed_content, dict):
                        if "data" in parsed_content and parsed_content["data"]:
                            # Format database results nicely
                            data = parsed_content["data"]
                            if isinstance(data, list) and len(data) > 0:
                                if isinstance(data[0], dict):
                                    # Format as a table-like structure
                                    meaningful_results.append(self._format_database_results(data))
                                else:
                                    meaningful_results.append(f"Results: {data}")
                            elif data:
                                meaningful_results.append(f"Result: {data}")
                        elif "result" in parsed_content:
                            meaningful_results.append(str(parsed_content["result"]))
                        elif "message" in parsed_content:
                            meaningful_results.append(parsed_content["message"])
                        else:
                            # Include the full parsed content if no specific field found
                            meaningful_results.append(str(parsed_content))
                    else:
                        meaningful_results.append(str(parsed_content))
                        
                except (json.JSONDecodeError, TypeError):
                    # If not JSON, use content as-is
                    meaningful_results.append(content)
        
        if meaningful_results:
            return "\n\n".join(meaningful_results)
        
        return None
    
    def _format_database_results(self, data: List[Dict[str, Any]]) -> str:
        """
        Format database results for user display.
        
        Args:
            data: List of database result dictionaries
            
        Returns:
            Formatted string representation of results
        """
        if not data:
            return "No results found."
            
        # Get all unique columns
        columns = set()
        for row in data:
            columns.update(row.keys())
        columns = sorted(list(columns))
        
        # Create header
        result_lines = []
        if len(data) == 1:
            result_lines.append("Found 1 result:")
        else:
            result_lines.append(f"Found {len(data)} results:")
        
        # Format each row
        for i, row in enumerate(data, 1):
            result_lines.append(f"\nResult {i}:")
            for col in columns:
                value = row.get(col, "N/A")
                result_lines.append(f"  {col}: {value}")
        
        return "\n".join(result_lines)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system performance metrics.
        
        Returns:
            Dictionary containing performance metrics
        """
        # Use the unified metrics collector for system metrics
        sys_metrics = self.metrics_collector.get_system_metrics()
        return {
            "total_queries": sys_metrics.total_executions,
            "cache_hit_rate": 0,  # Not tracked here; could be added via metadata if needed
            "tool_executions": sys_metrics.total_executions,
            "error_rate": sys_metrics.error_rate,
            "cache_hits": 0,
            "cache_misses": 0,
            "initialized": self._initialized
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the FACT system."""
        logger.info("Shutting down FACT system")
        
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
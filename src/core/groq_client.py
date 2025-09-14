"""
Groq API Client for FACT System
Uses Groq's fast inference API as a replacement for Anthropic
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
import structlog
from groq import Groq

logger = structlog.get_logger(__name__)

def create_groq_client(api_key: str) -> Groq:
    """
    Create a Groq client instance.
    
    Args:
        api_key: Groq API key
        
    Returns:
        Configured Groq client
    """
    try:
        client = Groq(api_key=api_key)
        logger.debug("Successfully created Groq client")
        return client
    except Exception as e:
        logger.error(f"Failed to create Groq client: {e}")
        raise

class GroqLLMClient:
    """
    Groq-based LLM client that mimics Anthropic's interface
    for compatibility with existing FACT system.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq client.
        
        Args:
            api_key: Optional Groq API key (defaults to GROQ_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = create_groq_client(self.api_key)
        self.model = "openai/gpt-oss-120b"  # Using the specific model requested
        logger.info(f"Groq client initialized with model: {self.model}")
    
    def create_message(self, 
                      messages: List[Dict[str, Any]], 
                      system: Optional[str] = None,
                      max_tokens: int = 4096,
                      temperature: float = 0.7,
                      tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Create a message using Groq API, mimicking Anthropic's interface.
        
        Args:
            messages: List of message dictionaries
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            tools: Tool definitions (converted to functions for Groq)
            
        Returns:
            Response in Anthropic-like format
        """
        try:
            # Prepare messages for Groq format
            groq_messages = []
            
            # Add system message if provided
            if system:
                groq_messages.append({
                    "role": "system",
                    "content": system
                })
            
            # Convert messages to Groq format
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # Handle tool results
                if role == "user" and isinstance(content, list):
                    # Extract text content from tool results
                    text_parts = []
                    for item in content:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text_parts.append(item.get("text", ""))
                            elif item.get("type") == "tool_result":
                                text_parts.append(f"Tool result: {item.get('content', '')}")
                    content = "\n".join(text_parts)
                
                groq_messages.append({
                    "role": role if role != "assistant" else "assistant",
                    "content": content
                })
            
            # Convert tools to functions if provided
            functions = None
            if tools:
                functions = []
                for tool in tools:
                    functions.append({
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {})
                    })
            
            # Make the API call
            start_time = time.time()
            
            if functions:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=groq_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    functions=functions,
                    function_call="auto"
                )
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=groq_messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            
            execution_time = (time.time() - start_time) * 1000
            
            # Convert Groq response to Anthropic-like format
            message = response.choices[0].message
            
            # Build content array
            content = []
            
            # Add text content if present
            if message.content:
                content.append({
                    "type": "text",
                    "text": message.content
                })
            
            # Add tool calls if present
            if hasattr(message, 'function_call') and message.function_call:
                content.append({
                    "type": "tool_use",
                    "id": f"tool_{int(time.time() * 1000)}",
                    "name": message.function_call.name,
                    "input": json.loads(message.function_call.arguments)
                })
            
            # Return in Anthropic-like format
            result = {
                "id": f"msg_{int(time.time() * 1000)}",
                "type": "message",
                "role": "assistant",
                "content": content,
                "model": self.model,
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens
                }
            }
            
            logger.info(f"Groq API call completed in {execution_time:.2f}ms")
            return result
            
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

class GroqMessage:
    """Wrapper class to mimic Anthropic's Message object."""
    
    def __init__(self, response_dict: Dict[str, Any]):
        self.id = response_dict.get("id")
        self.type = response_dict.get("type")
        self.role = response_dict.get("role")
        self.content = response_dict.get("content", [])
        self.model = response_dict.get("model")
        self.usage = response_dict.get("usage", {})
    
    def __str__(self):
        text_content = []
        for item in self.content:
            if item.get("type") == "text":
                text_content.append(item.get("text", ""))
        return " ".join(text_content)

class GroqAdapter:
    """
    Adapter class that provides Anthropic-compatible interface using Groq.
    Drop-in replacement for anthropic.Anthropic client.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = GroqLLMClient(api_key)
        self.messages = self  # Self-reference for messages.create pattern
    
    def create(self, 
               model: str,
               messages: List[Dict[str, Any]],
               system: Optional[str] = None,
               max_tokens: int = 4096,
               temperature: float = 0.7,
               tools: Optional[List[Dict]] = None,
               **kwargs) -> GroqMessage:
        """
        Create a message using Groq, with Anthropic-compatible interface.
        
        Args:
            model: Model name (ignored, uses Groq's models)
            messages: List of messages
            system: System prompt
            max_tokens: Maximum tokens
            temperature: Temperature
            tools: Tool definitions
            **kwargs: Additional arguments (ignored)
            
        Returns:
            GroqMessage object mimicking Anthropic's response
        """
        # Map model names if needed
        if "gpt" in model.lower() or "120b" in model.lower():
            self.client.model = "openai/gpt-oss-120b"  # Use the requested GPT-OSS-120B model
        elif "llama" in model.lower():
            self.client.model = "llama3-70b-8192"
        else:
            self.client.model = "openai/gpt-oss-120b"  # Default to GPT-OSS-120B
        
        response_dict = self.client.create_message(
            messages=messages,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=tools
        )
        
        return GroqMessage(response_dict)
"""
VAPI Webhook Handler for FACT System

This module provides webhook endpoints specifically designed for VAPI
voice agent integration, handling function calls and returning
formatted responses optimized for voice interactions.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Response, Depends, Header
from pydantic import BaseModel, Field
import json
import asyncio
import structlog
import os

logger = structlog.get_logger(__name__)

# Create VAPI webhook router
router = APIRouter(prefix="/vapi", tags=["vapi"])

# Import security module if available
try:
    from .vapi_security import verify_vapi_request, init_security
    SECURITY_AVAILABLE = True
    # Initialize security on module load
    init_security()
except ImportError:
    SECURITY_AVAILABLE = False
    logger.warning("VAPI security module not available, webhooks will be unprotected")
    # Dummy function when security not available
    async def verify_vapi_request(request: Request, 
                                 x_vapi_signature: Optional[str] = Header(None),
                                 x_api_key: Optional[str] = Header(None)):
        return True


class VAPIFunctionCall(BaseModel):
    """VAPI function call structure."""
    name: str = Field(..., description="Function name")
    parameters: Dict[str, Any] = Field(..., description="Function parameters")


class VAPIMessage(BaseModel):
    """VAPI message structure."""
    type: str = Field(..., description="Message type")
    functionCall: Optional[VAPIFunctionCall] = Field(None, description="Function call details")
    content: Optional[str] = Field(None, description="Message content")


class VAPICall(BaseModel):
    """VAPI call information."""
    id: str = Field(..., description="Call ID")
    assistantId: Optional[str] = Field(None, description="Assistant ID")
    squadId: Optional[str] = Field(None, description="Squad ID")
    phoneNumber: Optional[str] = Field(None, description="Caller phone number")


class VAPIWebhookRequest(BaseModel):
    """VAPI webhook request structure."""
    message: VAPIMessage = Field(..., description="Message details")
    call: VAPICall = Field(..., description="Call information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class VAPIWebhookResponse(BaseModel):
    """VAPI webhook response structure."""
    result: Dict[str, Any] = Field(..., description="Function result")
    error: Optional[str] = Field(None, description="Error message if any")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


# In-memory cache for conversation context (use Redis in production)
conversation_cache = {}


async def search_knowledge_base(query: str, state: Optional[str] = None, 
                               category: Optional[str] = None, 
                               limit: int = 3) -> Dict[str, Any]:
    """
    Search the REAL knowledge base using enhanced retriever.
    Connected to actual contractor licensing Q&A database.
    """
    try:
        # Use PostgreSQL if available on Railway
        import os
        if os.getenv("DATABASE_URL"):
            logger.info("DATABASE_URL detected, using PostgreSQL for search")
            # Don't import postgres_adapter - it creates a new instance
            # Instead, get entries directly from the database
            import asyncpg
            conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
            
            try:
                query = """
                SELECT id, question, answer, category, state, tags, 
                       priority, difficulty, personas, source
                FROM knowledge_base
                ORDER BY priority, id
                """
                rows = await conn.fetch(query)
                entries = [dict(row) for row in rows]
                logger.info(f"Loaded {len(entries)} entries directly from PostgreSQL")
            finally:
                await conn.close()
            
            # Create enhanced retriever and build index
            from retrieval.enhanced_search import EnhancedRetriever
            _enhanced_retriever = EnhancedRetriever(None)
            _enhanced_retriever.in_memory_index.build_index(entries)
            logger.info(f"Enhanced retriever index built with {len(_enhanced_retriever.in_memory_index.entries)} entries")
        else:
            # Fallback to SQLite
            logger.info("Creating enhanced retriever with SQLite")
            from retrieval.enhanced_search import EnhancedRetriever
            _enhanced_retriever = EnhancedRetriever(None)
            await _enhanced_retriever.initialize()
            logger.info(f"Enhanced retriever initialized with {len(_enhanced_retriever.in_memory_index.entries)} entries")
        
        # Check if enhanced retriever is available
        if _enhanced_retriever and len(_enhanced_retriever.in_memory_index.entries) > 0:
            logger.info(f"Using enhanced retriever for query: {query}")
            logger.info(f"Retriever has {len(_enhanced_retriever.in_memory_index.entries)} entries in memory")
            
            # Use the REAL enhanced retriever (96.7% accuracy)
            search_results = await _enhanced_retriever.search(
                query=query,
                category=category,
                state=state,
                limit=limit
            )
            
            logger.info(f"Search returned {len(search_results) if search_results else 0} results")
            
            if search_results and len(search_results) > 0:
                best_result = search_results[0]
                logger.info(f"Found result with score: {best_result.score}, question: {best_result.question[:50]}...")
                
                return {
                    "answer": best_result.answer,
                    "category": best_result.category or category or "general",
                    "confidence": best_result.score,
                    "source": "knowledge_base",  # Fixed: source is not a field in SearchResult
                    "state": best_result.state or state,  # Use result's state if available
                    "voice_optimized": True,
                    "match_type": best_result.match_type,
                    "metadata": {
                        "question_id": best_result.id,
                        "retrieval_time_ms": best_result.retrieval_time_ms
                    }
                }
            else:
                logger.warning(f"No results found for query: {query}")
        else:
            if _enhanced_retriever:
                logger.warning(f"Enhanced retriever has no entries loaded (has {len(_enhanced_retriever.in_memory_index.entries)} entries)")
            else:
                logger.warning("Enhanced retriever is None")
        
        # Fallback to direct SQL query if enhanced retriever not available
        from shared_state import get_driver
        _driver = get_driver()
        if not _enhanced_retriever and _driver and _driver.database_manager:
            logger.info(f"Using SQL fallback for query: {query}")
            
            # Escape query for SQL
            safe_query = query.replace("'", "''")
            
            # Build SQL query
            sql = f"""
                SELECT id, question, answer, category, state, tags, priority
                FROM knowledge_base 
                WHERE (question LIKE '%{safe_query}%' OR answer LIKE '%{safe_query}%')
            """
            
            # Add filters if provided
            if state:
                sql += f" AND state = '{state.upper()}'"
            if category:
                sql += f" AND category = '{category}'"
            
            sql += f" ORDER BY priority DESC, id LIMIT {limit}"
            
            result = await _driver.database_manager.execute_query(sql)
            
            if result.rows and len(result.rows) > 0:
                row = result.rows[0]
                return {
                    "answer": row["answer"],
                    "category": row.get("category", "general"),
                    "confidence": 0.8,  # Fixed confidence for SQL search
                    "source": "knowledge_base",
                    "state": row.get("state") or state,
                    "voice_optimized": True,
                    "metadata": {
                        "question_id": row["id"],
                        "priority": row.get("priority", "normal")
                    }
                }
        
        logger.warning("No retriever available, using default response")
        
    except ImportError as e:
        logger.error(f"Import error accessing retriever: {e}")
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
    
    # Default response if no results or error
    default_answer = "I can help you with contractor licensing information. "
    if state:
        default_answer += f"For {state}, "
    default_answer += "could you be more specific about what you'd like to know?"
    
    return {
        "answer": default_answer,
        "category": category or "general",
        "confidence": 0.5,
        "source": "default",
        "state": state,
        "voice_optimized": True
    }


async def detect_persona(conversation_text: str, call_id: str, 
                       assistant_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Enhanced persona detection using the advanced routing system.
    """
    try:
        # Import routing system
        from .vapi_routing import detect_persona_webhook
        
        # Get conversation history from cache
        cached_data = conversation_cache.get(call_id, {})
        conversation_history = cached_data.get("history", [])
        
        # Add current text to history
        conversation_history.append(conversation_text)
        
        # Update cache
        if call_id not in conversation_cache:
            conversation_cache[call_id] = {}
        conversation_cache[call_id]["history"] = conversation_history[-20:]  # Keep last 20 messages
        
        # Use advanced routing system
        result = await detect_persona_webhook(
            text=conversation_text,
            conversation_history=conversation_history,
            current_assistant=assistant_id
        )
        
        # Cache detected persona
        conversation_cache[call_id].update({
            "persona": result["detected_persona"],
            "confidence": result["confidence"],
            "detected_at": datetime.utcnow().isoformat()
        })
        
        return result
        
    except ImportError:
        # Fallback to simple detection if routing module unavailable
        logger.warning("Advanced routing unavailable, using simple detection")
        text_lower = conversation_text.lower()
        
        if any(phrase in text_lower for phrase in ["overwhelmed", "drowning", "too much", "can't keep up"]):
            persona = "overwhelmed_veteran"
        elif any(phrase in text_lower for phrase in ["confused", "don't understand", "new to this", "where do i start"]):
            persona = "confused_newcomer"
        elif any(phrase in text_lower for phrase in ["quickly", "right now", "urgent", "immediately"]):
            persona = "urgent_operator"
        elif any(phrase in text_lower for phrase in ["business", "money", "income", "opportunity", "network"]):
            persona = "qualifier_network_specialist"
        else:
            persona = "confused_newcomer"  # Default to newcomer guide
        
        return {
            "detected_persona": persona,
            "confidence": 0.6,
            "reasoning": "Simple keyword-based detection (fallback)",
            "transfer_recommended": False
        }


async def calculate_trust_score(call_id: str, events: List[Dict]) -> Dict[str, Any]:
    """
    Calculate trust score based on conversation events.
    """
    # Get current score from cache or start at baseline
    cached_data = conversation_cache.get(call_id, {})
    current_score = cached_data.get("trust_score", 45.0)
    
    # Process events
    for event in events:
        if event.get("type") == "positive":
            current_score = min(100, current_score + 5)
        elif event.get("type") == "negative":
            current_score = max(0, current_score - 5)
    
    # Update cache
    if call_id not in conversation_cache:
        conversation_cache[call_id] = {}
    conversation_cache[call_id]["trust_score"] = current_score
    
    # Determine response strategy
    if current_score >= 70:
        strategy = "move_to_close"
        message = "The caller is engaged. Consider moving toward commitment."
    elif current_score >= 50:
        strategy = "build_value"
        message = "Continue building value and addressing concerns."
    else:
        strategy = "rebuild_trust"
        message = "Focus on rebuilding trust and rapport."
    
    return {
        "trust_score": current_score,
        "strategy": strategy,
        "message": message,
        "threshold_for_close": current_score >= 70
    }


@router.post("/webhook", response_model=VAPIWebhookResponse, dependencies=[Depends(verify_vapi_request)])
async def vapi_webhook(request: VAPIWebhookRequest):
    """
    Main VAPI webhook handler for function calls.
    
    Processes VAPI function calls and returns voice-optimized responses.
    Secured with signature verification and optional API key.
    """
    try:
        logger.info(f"VAPI webhook called", 
                   function=request.message.functionCall.name if request.message.functionCall else None,
                   call_id=request.call.id)
        
        # Handle different function calls
        if request.message.type == "function-call" and request.message.functionCall:
            function_name = request.message.functionCall.name
            parameters = request.message.functionCall.parameters
            
            if function_name == "searchKnowledge":
                # Search knowledge base
                result = await search_knowledge_base(
                    query=parameters.get("query", ""),
                    state=parameters.get("state"),
                    category=parameters.get("category"),
                    limit=parameters.get("limit", 3)
                )
                
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": request.call.id, "function": "searchKnowledge"}
                )
            
            elif function_name == "detectPersona":
                # Detect caller persona with enhanced routing
                result = await detect_persona(
                    conversation_text=parameters.get("text", ""),
                    call_id=request.call.id,
                    assistant_id=request.call.assistantId
                )
                
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": request.call.id, "function": "detectPersona"}
                )
            
            elif function_name == "calculateTrust":
                # Calculate trust score
                result = await calculate_trust_score(
                    call_id=request.call.id,
                    events=parameters.get("events", [])
                )
                
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": request.call.id, "function": "calculateTrust"}
                )
            
            elif function_name == "getStateRequirements":
                # Get state-specific requirements
                state = parameters.get("state", "").upper()
                result = await search_knowledge_base(
                    query=f"{state} contractor license requirements",
                    state=state,
                    category="state_licensing_requirements"
                )
                
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": request.call.id, "function": "getStateRequirements"}
                )
            
            elif function_name == "handleObjection":
                # Handle objection
                objection_type = parameters.get("type", "general")
                persona = conversation_cache.get(request.call.id, {}).get("persona", "general_inquirer")
                
                objection_responses = {
                    "too_expensive": "I understand cost is important. Most contractors recover their licensing investment within 2 months. Would you like to hear how?",
                    "need_time": "Of course, this is an important decision. What specific information would help you decide?",
                    "not_sure": "I appreciate your honesty. What's your biggest concern about getting licensed?",
                    "general": "I understand. Let me help address your specific concerns."
                }
                
                return VAPIWebhookResponse(
                    result={
                        "response": objection_responses.get(objection_type, objection_responses["general"]),
                        "follow_up": "Would you like to hear from someone who had similar concerns?",
                        "persona_adjusted": persona != "general_inquirer"
                    },
                    metadata={"call_id": request.call.id, "function": "handleObjection"}
                )
            
            else:
                # Unknown function
                logger.warning(f"Unknown function called: {function_name}")
                return VAPIWebhookResponse(
                    result={"message": "I can help you with contractor licensing information."},
                    error=f"Unknown function: {function_name}",
                    metadata={"call_id": request.call.id}
                )
        
        # Handle other message types
        return VAPIWebhookResponse(
            result={"message": "Message received"},
            metadata={"call_id": request.call.id, "message_type": request.message.type}
        )
        
    except Exception as e:
        logger.error(f"VAPI webhook error: {e}")
        return VAPIWebhookResponse(
            result={"message": "I'm having trouble accessing that information right now."},
            error=str(e),
            metadata={"call_id": request.call.id if request.call else "unknown"}
        )


@router.post("/webhook/call-status", dependencies=[Depends(verify_vapi_request)])
async def vapi_call_status(request: Request):
    """
    Handle VAPI call status updates (started, ended, etc.).
    Secured with signature verification.
    """
    try:
        data = await request.json()
        
        call_id = data.get("call", {}).get("id")
        status = data.get("status")
        
        logger.info(f"VAPI call status update", call_id=call_id, status=status)
        
        if status == "ended":
            # Clean up conversation cache
            if call_id in conversation_cache:
                del conversation_cache[call_id]
                logger.info(f"Cleaned up cache for call {call_id}")
        
        return {"status": "received", "call_id": call_id}
        
    except Exception as e:
        logger.error(f"Call status webhook error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/webhook/health")
async def webhook_health():
    """
    Health check for VAPI webhook endpoint.
    Public endpoint - does not expose sensitive information.
    """
    return {
        "status": "healthy",
        "endpoint": "VAPI Webhook Handler",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/webhook/schema")
async def webhook_schema():
    """
    Return function schemas for VAPI integration.
    This endpoint tells VAPI what functions are available and their parameters.
    """
    return {
        "functions": [
            {
                "name": "searchKnowledge",
                "description": "Search the contractor licensing knowledge base for accurate information",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "additionalProperties": False,  # This is what VAPI needs
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for contractor licensing information"
                        },
                        "state": {
                            "type": "string",
                            "description": "Two-letter US state code (e.g., GA, CA, TX)",
                            "pattern": "^[A-Z]{2}$"
                        },
                        "category": {
                            "type": "string",
                            "description": "Category to filter results",
                            "enum": [
                                "state_licensing_requirements",
                                "exam_preparation_testing",
                                "qualifier_network_programs",
                                "business_formation_operations",
                                "insurance_bonding",
                                "financial_planning_roi",
                                "success_stories_case_studies",
                                "troubleshooting_problem_resolution"
                            ]
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 3
                        }
                    }
                }
            },
            {
                "name": "detectPersona",
                "description": "Detect the caller's persona to adjust conversation style",
                "parameters": {
                    "type": "object",
                    "required": ["text"],
                    "additionalProperties": False,
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Recent conversation text to analyze for persona detection"
                        }
                    }
                }
            },
            {
                "name": "calculateTrust",
                "description": "Calculate current trust score based on conversation events",
                "parameters": {
                    "type": "object",
                    "required": ["events"],
                    "additionalProperties": False,
                    "properties": {
                        "events": {
                            "type": "array",
                            "description": "Array of trust events from the conversation",
                            "items": {
                                "type": "object",
                                "required": ["type"],
                                "additionalProperties": False,
                                "properties": {
                                    "type": {
                                        "type": "string",
                                        "enum": ["positive", "negative", "neutral"],
                                        "description": "Type of trust event"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Description of the event"
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "name": "getStateRequirements",
                "description": "Get specific state contractor licensing requirements",
                "parameters": {
                    "type": "object",
                    "required": ["state"],
                    "additionalProperties": False,
                    "properties": {
                        "state": {
                            "type": "string",
                            "description": "Two-letter US state code",
                            "pattern": "^[A-Z]{2}$"
                        }
                    }
                }
            },
            {
                "name": "handleObjection",
                "description": "Get appropriate response for common objections",
                "parameters": {
                    "type": "object",
                    "required": ["type"],
                    "additionalProperties": False,
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Type of objection to handle",
                            "enum": ["too_expensive", "need_time", "not_sure", "already_tried", "too_complicated"]
                        }
                    }
                }
            }
        ],
        "server": {
            "url": "https://hyper8-fact-production.up.railway.app/vapi/webhook",
            "description": "FACT System VAPI Webhook Handler"
        }
    }


@router.options("/webhook")
async def webhook_options():
    """
    Handle OPTIONS requests for VAPI webhook.
    Returns available functions and their schemas.
    """
    schema = await webhook_schema()
    return schema
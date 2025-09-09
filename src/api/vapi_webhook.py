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
    Search the knowledge base for relevant information.
    
    This would connect to the actual database in production.
    """
    # Mock implementation - replace with actual database query
    mock_results = {
        "georgia": {
            "answer": "Georgia requires contractors to be licensed for work over $2,500. You'll need 4 years of experience or equivalent education. The application fee is $200, with total costs around $300-400. You'll take two exams: Business & Law and a Trade exam, each with 110 questions and requiring 70% to pass. A $10,000 surety bond is also required.",
            "category": "state_licensing_requirements",
            "confidence": 0.95,
            "source": "Georgia State Licensing Board"
        },
        "exam": {
            "answer": "The contractor licensing exam has two parts: Business & Law exam covering business practices, contracts, and regulations, and a Trade exam specific to your specialty. Both are 110 questions, you have 4 hours for each, and need 70% to pass. Most states use PSI or Prometric testing centers.",
            "category": "exam_preparation_testing",
            "confidence": 0.92,
            "source": "Exam Preparation Guide"
        },
        "cost": {
            "answer": "Total licensing costs typically range from $300 to $1,500 depending on your state. This includes application fees ($200-500), exam fees ($100-300), and the surety bond (1-15% of bond amount annually based on credit). Many contractors recover these costs within 1-2 months of being licensed.",
            "category": "financial_planning_roi",
            "confidence": 0.88,
            "source": "Cost Analysis Database"
        }
    }
    
    # Find best match based on query
    query_lower = query.lower()
    
    for key, data in mock_results.items():
        if key in query_lower:
            return {
                "answer": data["answer"],
                "category": data["category"],
                "confidence": data["confidence"],
                "source": data["source"],
                "state": state,
                "voice_optimized": True
            }
    
    # Default response
    return {
        "answer": "I can help you with contractor licensing requirements. Could you tell me which state you're interested in?",
        "category": "general",
        "confidence": 0.5,
        "source": "general_knowledge",
        "voice_optimized": True
    }


async def detect_persona(conversation_text: str, call_id: str) -> Dict[str, Any]:
    """
    Detect caller persona from conversation patterns.
    """
    text_lower = conversation_text.lower()
    
    # Check for persona indicators
    if any(phrase in text_lower for phrase in ["overwhelmed", "drowning", "too much", "can't keep up"]):
        persona = "overwhelmed_veteran"
        adjustments = {
            "speaking_pace": "slower",
            "empathy_level": "high",
            "detail_level": "step_by_step",
            "reassurance": True
        }
    elif any(phrase in text_lower for phrase in ["confused", "don't understand", "new to this", "where do i start"]):
        persona = "confused_newcomer"
        adjustments = {
            "speaking_pace": "patient",
            "explanation_style": "basic",
            "use_analogies": True,
            "check_understanding": True
        }
    elif any(phrase in text_lower for phrase in ["quickly", "right now", "urgent", "immediately"]):
        persona = "urgent_operator"
        adjustments = {
            "speaking_pace": "efficient",
            "get_to_point": True,
            "skip_pleasantries": True,
            "action_oriented": True
        }
    else:
        persona = "general_inquirer"
        adjustments = {
            "speaking_pace": "normal",
            "balanced_approach": True
        }
    
    # Cache persona for this call
    conversation_cache[call_id] = {
        "persona": persona,
        "adjustments": adjustments,
        "detected_at": datetime.utcnow().isoformat()
    }
    
    return {
        "persona": persona,
        "confidence": 0.8,
        "adjustments": adjustments,
        "cached": True
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
                # Detect caller persona
                result = await detect_persona(
                    conversation_text=parameters.get("text", ""),
                    call_id=request.call.id
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
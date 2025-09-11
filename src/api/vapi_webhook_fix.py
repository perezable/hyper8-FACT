"""
Fixed VAPI Webhook Handler for new tool-calls structure
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/vapi-fixed", tags=["vapi-fixed"])


class VAPIToolCallFunction(BaseModel):
    """VAPI tool call function structure."""
    name: str = Field(..., description="Function name")
    arguments: Dict[str, Any] = Field(..., description="Function arguments")


class VAPIToolCall(BaseModel):
    """VAPI tool call structure."""
    id: str = Field(..., description="Tool call ID")
    type: str = Field(..., description="Tool type (function)")
    function: VAPIToolCallFunction = Field(..., description="Function details")


class VAPIMessage(BaseModel):
    """VAPI message structure for tool-calls."""
    type: str = Field(..., description="Message type")
    toolCalls: Optional[List[VAPIToolCall]] = Field(None, description="Tool calls array")
    timestamp: Optional[int] = Field(None, description="Timestamp")


class VAPIWebhookRequest(BaseModel):
    """VAPI webhook request structure."""
    message: VAPIMessage = Field(..., description="Message details")


class VAPIWebhookResponse(BaseModel):
    """VAPI webhook response structure."""
    results: List[Dict[str, Any]] = Field(..., description="Tool call results")


@router.post("/webhook")
async def fixed_vapi_webhook(request: VAPIWebhookRequest):
    """
    Fixed VAPI webhook handler for tool-calls structure.
    """
    try:
        # Handle tool-calls message type
        if request.message.type == "tool-calls" and request.message.toolCalls:
            results = []
            
            for tool_call in request.message.toolCalls:
                logger.info(f"Processing tool call: {tool_call.function.name}")
                
                # Extract function details
                function_name = tool_call.function.name
                parameters = tool_call.function.arguments
                
                # Handle searchKnowledge
                if function_name == "searchKnowledge":
                    # Import the actual search function
                    from .vapi_webhook import search_knowledge_base
                    
                    # Extract parameters
                    query = parameters.get("query", "")
                    state = parameters.get("state", "")
                    category = parameters.get("category", "")
                    
                    # Search knowledge base
                    result = await search_knowledge_base(query, state, category)
                    
                    results.append({
                        "toolCallId": tool_call.id,
                        "result": result
                    })
                
                # Handle other functions
                elif function_name == "detectPersona":
                    from .vapi_enhanced_webhook import detect_persona_enhanced
                    
                    text = parameters.get("text", "")
                    # Use a default call_id since it's not provided
                    call_id = "default-call-id"
                    
                    result = await detect_persona_enhanced(text, call_id)
                    
                    results.append({
                        "toolCallId": tool_call.id,
                        "result": result
                    })
                
                elif function_name == "calculateTrust":
                    from .vapi_webhook import calculate_trust_score
                    
                    events = parameters.get("events", [])
                    call_id = "default-call-id"
                    
                    result = await calculate_trust_score(call_id, events)
                    
                    results.append({
                        "toolCallId": tool_call.id,
                        "result": result
                    })
                
                elif function_name == "handleObjection":
                    objection_type = parameters.get("type", "not_sure")
                    
                    objection_responses = {
                        "too_expensive": {
                            "response": "I understand cost is a concern. Consider this: DIY contractors have only a 35-45% approval rate, while our clients achieve 98%. The time you save—76 to 118 hours—is worth $6,000 to $18,750 at typical contractor rates. Plus, your first project typically returns 3 to 10 times your investment. Can you afford to lose projects while waiting months for approval?",
                            "confidence": 0.9
                        },
                        "need_time": {
                            "response": "I appreciate you want to think it through. While you're considering, remember that every day without a license costs contractors $500 to $2,500 in lost opportunities. Our next enrollment closes soon, and the following class isn't for another month. What specific concerns can I address to help you make the best decision today?",
                            "confidence": 0.85
                        },
                        "diy": {
                            "response": "Many contractors think that initially. But here's what they discover: DIY applications face a 55-65% rejection rate, often waiting 3-6 months only to start over. We guarantee 98% approval in weeks, not months. Plus, you'll join our qualifier network earning $3,000 to $6,000 monthly in passive income. Isn't your time worth more than struggling through complex paperwork?",
                            "confidence": 0.88
                        },
                        "not_sure": {
                            "response": "I understand you may have questions. Let me share this: contractors using our program report an average income increase of 150% within the first year. We handle all the complex paperwork, exam preparation, and even connect you with a network that generates passive income. What specific information would help you see if this is right for you?",
                            "confidence": 0.8
                        }
                    }
                    
                    result = objection_responses.get(objection_type, objection_responses["not_sure"])
                    
                    results.append({
                        "toolCallId": tool_call.id,
                        "result": result
                    })
                
                elif function_name == "bookAppointment":
                    # Mock booking response
                    result = {
                        "success": True,
                        "message": f"Appointment scheduled for {parameters.get('name', 'Customer')}",
                        "confirmation_number": f"CLP-{datetime.now().strftime('%Y%m%d%H%M')}",
                        "next_steps": "You'll receive a confirmation email with preparation materials."
                    }
                    
                    results.append({
                        "toolCallId": tool_call.id,
                        "result": result
                    })
                
                else:
                    # Unknown function
                    results.append({
                        "toolCallId": tool_call.id,
                        "result": {
                            "error": f"Unknown function: {function_name}"
                        }
                    })
            
            return {"results": results}
        
        else:
            return {
                "results": [{
                    "error": "No tool calls to process"
                }]
            }
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {
            "results": [{
                "error": str(e)
            }]
        }
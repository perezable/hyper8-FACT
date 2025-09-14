"""
Enhanced VAPI Webhook with Conversation Scoring and Journey Progression

Integrates the conversation scoring system to provide dynamic,
journey-based responses for the CLP Sales and Expert agents.
"""

from typing import Dict, Any, Optional, List, Union
from fastapi import APIRouter, Request, Header, Depends
from pydantic import BaseModel, Field
import structlog
from datetime import datetime

from .vapi_webhook import (
    VAPIFunctionCall, VAPIMessage, VAPICall, 
    VAPIWebhookRequest as OldVAPIWebhookRequest, VAPIWebhookResponse,
    verify_vapi_request, search_knowledge_base
)
from .vapi_conversation_scoring import (
    conversation_scorer, PersonaType, ConversationStage
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/vapi-enhanced", tags=["vapi-enhanced"])


# New VAPI structures for tool-calls
class VAPIToolCallFunction(BaseModel):
    """VAPI tool call function structure."""
    name: str = Field(..., description="Function name")
    arguments: Dict[str, Any] = Field(..., description="Function arguments")


class VAPIToolCall(BaseModel):
    """VAPI tool call structure."""
    id: str = Field(..., description="Tool call ID")
    type: str = Field(..., description="Tool type")
    function: VAPIToolCallFunction = Field(..., description="Function details")


class VAPIMessageNew(BaseModel):
    """VAPI message structure for tool-calls."""
    type: str = Field(..., description="Message type")
    toolCalls: Optional[List[VAPIToolCall]] = Field(None, description="Tool calls array")
    functionCall: Optional[VAPIFunctionCall] = Field(None, description="Function call (old format)")
    timestamp: Optional[int] = Field(None, description="Timestamp")


class VAPIWebhookRequest(BaseModel):
    """VAPI webhook request structure that handles both formats."""
    message: VAPIMessageNew = Field(..., description="Message details")
    call: Optional[VAPICall] = Field(None, description="Call information")


async def detect_persona_enhanced(text: str, call_id: str) -> Dict[str, Any]:
    """Enhanced persona detection with scoring integration."""
    
    # Detect persona and update metrics
    persona, confidence = conversation_scorer.detect_persona(call_id, text)
    metrics = conversation_scorer.get_or_create_conversation(call_id)
    
    # Process trust events based on content
    if any(word in text.lower() for word in ["interested", "tell me more", "sounds good"]):
        conversation_scorer.process_trust_event(call_id, "positive", "Shows interest")
    elif any(word in text.lower() for word in ["not sure", "expensive", "think about"]):
        conversation_scorer.process_trust_event(call_id, "negative", "Shows hesitation")
    
    # Get response tone recommendations
    tone = conversation_scorer.get_response_tone(call_id)
    
    # Check transfer recommendation
    should_transfer, transfer_reason = conversation_scorer.should_transfer(call_id)
    
    return {
        "detected_persona": persona.value,
        "confidence": confidence,
        "trust_score": metrics.trust_score,
        "stage": metrics.stage.value,
        "transfer_recommended": should_transfer,
        "transfer_reason": transfer_reason,
        "response_tone": tone,
        "urgency": metrics.urgency_level,
        "appointment_ready": metrics.appointment_ready
    }


async def calculate_trust_enhanced(call_id: str, events: list) -> Dict[str, Any]:
    """Enhanced trust calculation with journey progression."""
    
    # Process each event
    for event in events:
        conversation_scorer.process_trust_event(
            call_id,
            event.get("type", "neutral"),
            event.get("description", ""),
            event.get("impact")
        )
    
    # Get updated metrics
    metrics = conversation_scorer.get_or_create_conversation(call_id)
    summary = conversation_scorer.get_conversation_summary(call_id)
    
    # Determine response strategy based on stage
    stage_strategies = {
        ConversationStage.DISCOVERY: {
            "strategy": "build_rapport",
            "message": "Let me understand your specific situation better.",
            "focus": "Ask discovery questions"
        },
        ConversationStage.VALUE_BUILDING: {
            "strategy": "demonstrate_value",
            "message": "Here's how we can help you achieve your goals.",
            "focus": "Share success stories and benefits"
        },
        ConversationStage.OBJECTION_HANDLING: {
            "strategy": "address_concerns",
            "message": "I understand your concerns. Let me address them.",
            "focus": "Handle objections with specific examples"
        },
        ConversationStage.CLOSING: {
            "strategy": "move_to_commitment",
            "message": "You're ready to take the next step. Here's how we proceed.",
            "focus": "Create urgency and book appointment"
        },
        ConversationStage.COMMITMENT: {
            "strategy": "secure_next_steps",
            "message": "Excellent decision! Let's get you started.",
            "focus": "Gather information and schedule consultation"
        }
    }
    
    current_strategy = stage_strategies.get(metrics.stage, stage_strategies[ConversationStage.DISCOVERY])
    
    return {
        "trust_score": metrics.trust_score,
        "stage": metrics.stage.value,
        "strategy": current_strategy["strategy"],
        "message": current_strategy["message"],
        "focus": current_strategy["focus"],
        "appointment_ready": metrics.appointment_ready,
        "transfer_recommended": metrics.transfer_recommended,
        "recommendations": summary["recommendations"]
    }


async def handle_objection_enhanced(call_id: str, objection_type: str) -> Dict[str, Any]:
    """Enhanced objection handling with personalized responses."""
    
    # Get objection strategy
    strategy = conversation_scorer.handle_objection(call_id, objection_type)
    metrics = conversation_scorer.get_or_create_conversation(call_id)
    
    # Get persona-specific response
    objection_responses = {
        "too_expensive": {
            PersonaType.OVERWHELMED_VETERAN: "I understand it feels like a big investment when you're already stressed. Let me show you how this actually reduces your stress AND pays for itself. Most contractors like you see returns of 3-10x on their first project alone.",
            PersonaType.URGENT_OPERATOR: "Every day you wait costs you $500-$2,500 in projects you can't bid on. This investment pays for itself in 2-3 days of having your license. Can you afford to keep losing that money?",
            PersonaType.STRATEGIC_INVESTOR: "Let's talk ROI. Our data shows 2,735% first-year returns. Plus, the qualifier network generates $3,000-$6,000 monthly passive income. This isn't an expense, it's an investment with documented returns.",
            PersonaType.SKEPTICAL_SHOPPER: "I appreciate you being careful with your money. Here's the math: DIY costs $1,500-2,000 in fees plus 80-125 hours of your time worth $6,000-$18,750. Our success rate is 98% vs 35-45% DIY. The real question is: can you afford the risk of doing it wrong?",
            PersonaType.CONFUSED_NEWCOMER: "I know $3,000-$5,000 sounds like a lot when you're just starting. But consider this: one $30,000 project at 15% margin nets you $4,500. That's your entire investment back on project one.",
            PersonaType.UNKNOWN: strategy["key_points"][0] if strategy["key_points"] else "The investment pays for itself quickly through increased earning potential."
        },
        "need_time": {
            PersonaType.OVERWHELMED_VETERAN: "I completely understand needing time to process everything. While you're thinking, you're losing opportunities. What if I could simplify this decision for you right now?",
            PersonaType.URGENT_OPERATOR: "I respect that, but you mentioned urgency. Every day of thinking costs you money. What specific information would help you decide today?",
            PersonaType.STRATEGIC_INVESTOR: "Smart investors make informed decisions quickly. What specific data points do you need to evaluate this opportunity?",
            PersonaType.SKEPTICAL_SHOPPER: "Absolutely take the time you need. Can I send you our success stories and ROI documentation to review? Most people who see the data decide within 24 hours.",
            PersonaType.CONFUSED_NEWCOMER: "Of course! This is a big step. How about I send you our step-by-step guide so you can review everything clearly? We can reconnect tomorrow.",
            PersonaType.UNKNOWN: "I understand. What specific concerns can I address to help you make the best decision?"
        },
        "diy": {
            PersonaType.OVERWHELMED_VETERAN: "You could do it yourself, but you just told me you're overwhelmed. Why add 80-125 hours of complex paperwork to your stress? We handle everything with a 98% success rate.",
            PersonaType.URGENT_OPERATOR: "DIY takes 3-6 months. You need speed. We get you licensed in 35-42 days with a 98% success rate. How much will waiting cost you?",
            PersonaType.STRATEGIC_INVESTOR: "Smart business owners focus on their highest value activities. Is spending 80-125 hours on paperwork the best use of your time when you could be building your business?",
            PersonaType.SKEPTICAL_SHOPPER: "You absolutely can do it yourself. 35-45% succeed on their first try. If you're in that 55-65% who don't, you'll pay fees again and wait months more. Is that risk worth it?",
            PersonaType.CONFUSED_NEWCOMER: "DIY is possible, but it's like doing your own root canal - technically possible but not recommended. We navigate the complexities daily. You'd be learning as you go.",
            PersonaType.UNKNOWN: "DIY success rate is 35-45% with 80-125 hours of work. We achieve 98% success in 35-42 days. The math speaks for itself."
        }
    }
    
    # Get appropriate response
    response_map = objection_responses.get(objection_type, objection_responses["too_expensive"])
    response = response_map.get(metrics.persona_type, response_map[PersonaType.UNKNOWN])
    
    return {
        "response": response,
        "strategy": strategy,
        "trust_score": metrics.trust_score,
        "stage": metrics.stage.value,
        "follow_up": _get_follow_up_question(metrics),
        "transfer_recommended": strategy["transfer_recommended"]
    }


def _get_follow_up_question(metrics) -> str:
    """Get appropriate follow-up question based on stage and persona."""
    
    if metrics.stage == ConversationStage.DISCOVERY:
        return "What's your biggest challenge with getting licensed right now?"
    elif metrics.stage == ConversationStage.VALUE_BUILDING:
        return "What would having your license mean for your business?"
    elif metrics.stage == ConversationStage.OBJECTION_HANDLING:
        return "What would need to happen for you to feel confident moving forward?"
    elif metrics.stage == ConversationStage.CLOSING:
        return "Are you ready to get started with your application today?"
    else:
        return "When would you like to schedule your consultation?"


# Old calculate_roi_enhanced function removed - now using enhanced_roi_calculator module


async def process_function_call(function_name: str, parameters: Dict[str, Any], call_id: str) -> Dict[str, Any]:
    """
    Process a function call and return the result.
    Shared logic for both old and new VAPI formats.
    """
    if function_name == "searchKnowledge":
        # Standard knowledge search with context awareness
        result = await search_knowledge_base(
            query=parameters.get("query", ""),
            state=parameters.get("state"),
            category=parameters.get("category"),
            limit=parameters.get("limit", 3)
        )
        
        # Track value mention if discussing benefits
        if any(word in parameters.get("query", "").lower() 
              for word in ["benefit", "value", "roi", "income", "earn"]):
            metrics = conversation_scorer.get_or_create_conversation(call_id)
            metrics.value_mentions += 1
        
        return result
    
    elif function_name == "detectPersona":
        return await detect_persona_enhanced(
            text=parameters.get("text", ""),
            call_id=call_id
        )
    
    elif function_name == "calculateTrust":
        return await calculate_trust_enhanced(
            call_id=call_id,
            events=parameters.get("events", [])
        )
    
    elif function_name == "handleObjection":
        return await handle_objection_enhanced(
            call_id=call_id,
            objection_type=parameters.get("type", "not_sure")
        )
    
    elif function_name == "calculateROI":
        # Import the enhanced ROI calculator
        from .enhanced_roi_calculator import calculate_roi_enhanced_webhook
        
        return await calculate_roi_enhanced_webhook(
            call_id=call_id,
            current_income=parameters.get("currentIncome", 65000),
            industry_type=parameters.get("industryType", "residential"),
            geographic_market=parameters.get("geographicMarket", "suburban"),
            experience_years=parameters.get("experienceYears", 4),
            state=parameters.get("state", "GA"),
            project_size=parameters.get("projectSize", 15000),
            monthly_projects=parameters.get("monthlyProjects", 2),
            qualifier_network=parameters.get("qualifierNetwork", True)
        )
    
    elif function_name == "bookAppointment":
        # Book appointment with scoring context
        metrics = conversation_scorer.get_or_create_conversation(call_id)
        
        return {
            "success": True,
            "message": f"Perfect! I've scheduled your consultation, {parameters.get('name', 'there')}. You'll receive confirmation shortly.",
            "confirmation_number": f"CLP-{datetime.now().strftime('%Y%m%d%H%M')}",
            "trust_score": metrics.trust_score,
            "persona": metrics.persona_type.value if metrics.persona_type else "unknown",
            "urgency": parameters.get("urgency", "medium"),
            "next_steps": "Check your email for preparation materials and a calendar invite."
        }
    
    elif function_name == "qualifierNetworkAnalysis":
        # Analyze qualifier network opportunity
        metrics = conversation_scorer.get_or_create_conversation(call_id)
        metrics.qualifier_interest = True
        
        state = parameters.get("state", "GA")
        license_type = parameters.get("licenseType", "general")
        experience = parameters.get("experience", 4)
        
        monthly_income = 3000 if experience < 5 else 4500 if experience < 10 else 6000
        annual_income = monthly_income * 12
        
        return {
            "eligible": experience >= 2,
            "state": state,
            "license_type": license_type,
            "experience_years": experience,
            "estimated_monthly_income": monthly_income,
            "estimated_annual_income": annual_income,
            "demand_level": "high" if state in ["CA", "TX", "FL", "GA"] else "moderate",
            "message": f"With {experience} years experience in {state}, you could earn ${monthly_income:,}/month as a qualifier. That's ${annual_income:,} annually in passive income just for lending your license to help other contractors!",
            "trust_score": metrics.trust_score
        }
    
    elif function_name == "scheduleConsultation":
        # Schedule expert consultation
        metrics = conversation_scorer.get_or_create_conversation(call_id)
        
        return {
            "success": True,
            "consultation_type": parameters.get("consultationType", "licensing"),
            "message": f"Expert consultation scheduled for {parameters.get('name', 'you')}.",
            "confirmation": f"EXP-{datetime.now().strftime('%Y%m%d%H%M')}",
            "investment_range": parameters.get("investmentRange", "5k-10k"),
            "trust_score": metrics.trust_score,
            "stage": metrics.stage.value
        }
    
    else:
        return {
            "error": f"Unknown function: {function_name}"
        }


@router.post("/webhook", dependencies=[Depends(verify_vapi_request)])
async def enhanced_vapi_webhook(request: VAPIWebhookRequest):
    """
    Enhanced VAPI webhook with conversation scoring and journey progression.
    Handles both old (function-call) and new (tool-calls) formats.
    """
    try:
        # Get call_id (use default if not provided in new format)
        call_id = request.call.id if request.call else "default-call-id"
        
        # Handle new tool-calls format
        if request.message.type == "tool-calls" and request.message.toolCalls:
            logger.info(f"Processing tool-calls", count=len(request.message.toolCalls))
            
            # Process all tool calls and return results array
            results = []
            for tool_call in request.message.toolCalls:
                function_name = tool_call.function.name
                parameters = tool_call.function.arguments
                logger.info(f"Processing tool: {function_name}")
                
                # Process the function call (reuse existing logic)
                result = await process_function_call(function_name, parameters, call_id)
                
                results.append({
                    "toolCallId": tool_call.id,
                    "result": result
                })
            
            # Return results in the format VAPI expects for tool-calls
            return {"results": results}
        
        # Handle old function-call format
        elif request.message.type == "function-call" and request.message.functionCall:
            function_name = request.message.functionCall.name
            parameters = request.message.functionCall.parameters
            
            # Process the function call using shared logic
            result = await process_function_call(function_name, parameters, call_id)
            
            return VAPIWebhookResponse(
                result=result,
                metadata={"call_id": call_id, "function": function_name}
            )
            
            # Handle other functions...
            
        return VAPIWebhookResponse(
            result={"message": "Function processed"},
            metadata={"call_id": call_id}
        )
        
    except Exception as e:
        logger.error(f"Enhanced webhook error: {e}")
        return VAPIWebhookResponse(
            result={"message": "I'm having a moment. Let me reconnect."},
            error=str(e),
            metadata={"call_id": request.call.id if request.call else "unknown"}
        )


@router.get("/conversation/{call_id}/summary")
async def get_conversation_summary(call_id: str):
    """Get conversation summary with scoring metrics."""
    summary = conversation_scorer.get_conversation_summary(call_id)
    return summary


@router.post("/conversation/{call_id}/reset")
async def reset_conversation(call_id: str):
    """Reset conversation metrics for a call ID."""
    if call_id in conversation_scorer.conversations:
        del conversation_scorer.conversations[call_id]
    if call_id in conversation_scorer.event_history:
        del conversation_scorer.event_history[call_id]
    return {"status": "reset", "call_id": call_id}
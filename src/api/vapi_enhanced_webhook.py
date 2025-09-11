"""
Enhanced VAPI Webhook with Conversation Scoring and Journey Progression

Integrates the conversation scoring system to provide dynamic,
journey-based responses for the CLP Sales and Expert agents.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Header, Depends
from pydantic import BaseModel, Field
import structlog
from datetime import datetime

from .vapi_webhook import (
    VAPIFunctionCall, VAPIMessage, VAPICall, 
    VAPIWebhookRequest, VAPIWebhookResponse,
    verify_vapi_request, search_knowledge_base
)
from .vapi_conversation_scoring import (
    conversation_scorer, PersonaType, ConversationStage
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/vapi-enhanced", tags=["vapi-enhanced"])


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


async def calculate_roi_enhanced(call_id: str, current_income: float, 
                                project_size: float = 50000, 
                                monthly_projects: int = 2) -> Dict[str, Any]:
    """Calculate ROI with journey context."""
    
    metrics = conversation_scorer.get_or_create_conversation(call_id)
    
    # Mark that ROI has been calculated
    metrics.roi_calculated = True
    metrics.value_mentions += 1
    
    # Process positive trust event
    conversation_scorer.process_trust_event(
        call_id, "positive", "Engaged with ROI calculation", 5.0
    )
    
    # Calculate basic ROI
    licensed_income = current_income * 2.5  # Average 150% increase
    annual_increase = licensed_income - current_income
    project_revenue = project_size * monthly_projects * 12
    project_profit = project_revenue * 0.15  # 15% margin
    
    # Add qualifier income if interested
    qualifier_income = 0
    if metrics.qualifier_interest or metrics.persona_type == PersonaType.STRATEGIC_INVESTOR:
        qualifier_income = 4500 * 12  # $4,500/month average
    
    total_additional_income = annual_increase + project_profit + qualifier_income
    investment = 5000  # Average investment
    roi_percentage = (total_additional_income / investment) * 100
    payback_days = (investment / (total_additional_income / 365))
    
    return {
        "current_income": current_income,
        "projected_licensed_income": licensed_income,
        "annual_increase": annual_increase,
        "project_profit": project_profit,
        "qualifier_income": qualifier_income,
        "total_additional_income": total_additional_income,
        "investment": investment,
        "roi_percentage": roi_percentage,
        "payback_days": payback_days,
        "message": f"Based on your current income of ${current_income:,.0f}, you'll likely earn ${licensed_income:,.0f} once licensed - a ${annual_increase:,.0f} increase. Add ${project_profit:,.0f} from projects and ${qualifier_income:,.0f} from our qualifier network, totaling ${total_additional_income:,.0f} additional income. Your investment pays back in just {payback_days:.0f} days with a {roi_percentage:.0f}% ROI!",
        "trust_score": metrics.trust_score,
        "stage": metrics.stage.value
    }


@router.post("/webhook", response_model=VAPIWebhookResponse, dependencies=[Depends(verify_vapi_request)])
async def enhanced_vapi_webhook(request: VAPIWebhookRequest):
    """
    Enhanced VAPI webhook with conversation scoring and journey progression.
    """
    try:
        call_id = request.call.id
        logger.info(f"Enhanced VAPI webhook called", 
                   function=request.message.functionCall.name if request.message.functionCall else None,
                   call_id=call_id)
        
        # Handle function calls
        if request.message.type == "function-call" and request.message.functionCall:
            function_name = request.message.functionCall.name
            parameters = request.message.functionCall.parameters
            
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
                
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": call_id, "function": "searchKnowledge"}
                )
            
            elif function_name == "detectPersona":
                result = await detect_persona_enhanced(
                    text=parameters.get("text", ""),
                    call_id=call_id
                )
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": call_id, "function": "detectPersona"}
                )
            
            elif function_name == "calculateTrust":
                result = await calculate_trust_enhanced(
                    call_id=call_id,
                    events=parameters.get("events", [])
                )
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": call_id, "function": "calculateTrust"}
                )
            
            elif function_name == "handleObjection":
                result = await handle_objection_enhanced(
                    call_id=call_id,
                    objection_type=parameters.get("type", "not_sure")
                )
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": call_id, "function": "handleObjection"}
                )
            
            elif function_name == "calculateROI":
                result = await calculate_roi_enhanced(
                    call_id=call_id,
                    current_income=parameters.get("currentIncome", 65000),
                    project_size=parameters.get("projectSize", 50000),
                    monthly_projects=parameters.get("monthlyProjects", 2)
                )
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": call_id, "function": "calculateROI"}
                )
            
            elif function_name == "qualifierNetworkAnalysis":
                # Mark qualifier interest
                metrics = conversation_scorer.get_or_create_conversation(call_id)
                metrics.qualifier_interest = True
                conversation_scorer.process_trust_event(
                    call_id, "positive", "Shows qualifier network interest", 7.5
                )
                
                result = {
                    "state": parameters.get("state", "GA"),
                    "license_type": parameters.get("licenseType", "general"),
                    "monthly_income": "$3,000 - $6,000",
                    "annual_income": "$36,000 - $72,000",
                    "example": "One of our contractors in Georgia earns $72,000 annually just from being a qualifier",
                    "roi": "3,673% return on investment",
                    "effort": "Minimal - just lending your license to vetted contractors",
                    "benefit": "Help other contractors while earning passive income",
                    "trust_score": metrics.trust_score,
                    "transfer_recommended": metrics.transfer_recommended
                }
                
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": call_id, "function": "qualifierNetworkAnalysis"}
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
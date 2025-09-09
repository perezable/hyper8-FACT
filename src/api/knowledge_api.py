"""
FACT System Knowledge Base API Module

This module provides comprehensive API endpoints for the Bland AI
contractor licensing knowledge base with persona detection, pathways,
trust scoring, and advanced retrieval.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import json
import structlog

logger = structlog.get_logger(__name__)

# Create API router
router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


class PersonaDetectionRequest(BaseModel):
    """Request model for persona detection."""
    conversation_text: str = Field(..., description="Conversation transcript or caller statements")
    confidence_threshold: float = Field(0.7, description="Minimum confidence for detection")


class PersonaDetectionResponse(BaseModel):
    """Response model for persona detection."""
    detected_persona: str = Field(..., description="Detected persona type")
    confidence: float = Field(..., description="Detection confidence score")
    response_adjustments: Dict[str, Any] = Field(..., description="Recommended response adjustments")
    detection_signals: List[str] = Field(..., description="Signals that led to detection")


class TrustScoreRequest(BaseModel):
    """Request model for trust score calculation."""
    call_id: str = Field(..., description="Unique call identifier")
    events: List[Dict[str, Any]] = Field(..., description="List of trust events")
    current_score: float = Field(45.0, description="Current trust score")


class TrustScoreResponse(BaseModel):
    """Response model for trust score."""
    call_id: str = Field(..., description="Call identifier")
    initial_score: float = Field(..., description="Initial trust score")
    current_score: float = Field(..., description="Updated trust score")
    trust_level: str = Field(..., description="Trust level category")
    recommendations: List[str] = Field(..., description="Recommendations based on trust level")


class PathwayNavigationRequest(BaseModel):
    """Request model for pathway navigation."""
    current_node: str = Field(..., description="Current pathway node ID")
    user_response: str = Field(..., description="User's response or input")
    persona_type: Optional[str] = Field(None, description="Detected persona")
    trust_score: float = Field(45.0, description="Current trust score")
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")


class PathwayNavigationResponse(BaseModel):
    """Response model for pathway navigation."""
    next_node: str = Field(..., description="Next pathway node ID")
    response_text: str = Field(..., description="Response to provide")
    branch_taken: str = Field(..., description="Branch decision made")
    trust_adjustment: float = Field(..., description="Trust score adjustment")
    metadata: Dict[str, Any] = Field(..., description="Additional navigation data")


class StateRequirementsRequest(BaseModel):
    """Request model for state requirements lookup."""
    state_code: str = Field(..., description="Two-letter state code")
    license_class: Optional[str] = Field(None, description="License class (A, B, C)")
    license_type: Optional[str] = Field(None, description="Specific license type")


class StateRequirementsResponse(BaseModel):
    """Response model for state requirements."""
    state_code: str = Field(..., description="State code")
    state_name: str = Field(..., description="Full state name")
    requirements: List[Dict[str, Any]] = Field(..., description="List of requirements")
    summary: str = Field(..., description="Summarized requirements")
    metadata: Dict[str, Any] = Field(..., description="Additional state data")


@router.post("/persona/detect", response_model=PersonaDetectionResponse)
async def detect_persona(request: PersonaDetectionRequest):
    """
    Detect caller persona based on conversation patterns.
    
    Analyzes language patterns, keywords, and behavioral signals
    to identify the most likely persona type.
    """
    try:
        # This would connect to the actual database and persona detection logic
        # For now, returning a mock response
        
        # Analyze conversation for persona signals
        text_lower = request.conversation_text.lower()
        
        # Check for overwhelmed veteran signals
        if any(phrase in text_lower for phrase in ["drowning in", "can't keep up", "overwhelming"]):
            return PersonaDetectionResponse(
                detected_persona="overwhelmed_veteran",
                confidence=0.85,
                response_adjustments={
                    "empathy_level": "high",
                    "pace": "slower",
                    "detail_level": "comprehensive",
                    "reassurance_frequency": "high"
                },
                detection_signals=[
                    "Stress indicators present",
                    "Experience markers detected",
                    "Urgency language used"
                ]
            )
        
        # Check for confused newcomer signals
        elif any(phrase in text_lower for phrase in ["don't know", "confused", "where do I start"]):
            return PersonaDetectionResponse(
                detected_persona="confused_newcomer",
                confidence=0.78,
                response_adjustments={
                    "explanation_depth": "basic",
                    "pace": "patient",
                    "guidance_level": "step-by-step",
                    "terminology": "simplified"
                },
                detection_signals=[
                    "Confusion indicators",
                    "Lack of industry knowledge",
                    "Request for basic guidance"
                ]
            )
        
        # Default persona
        return PersonaDetectionResponse(
            detected_persona="general_inquirer",
            confidence=0.6,
            response_adjustments={
                "approach": "balanced",
                "pace": "moderate",
                "detail_level": "standard"
            },
            detection_signals=["No strong persona indicators detected"]
        )
        
    except Exception as e:
        logger.error(f"Persona detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trust/calculate", response_model=TrustScoreResponse)
async def calculate_trust_score(request: TrustScoreRequest):
    """
    Calculate and update trust score based on conversation events.
    
    Processes positive and negative indicators to maintain
    a real-time trust temperature throughout the conversation.
    """
    try:
        current_score = request.current_score
        
        # Process each event
        for event in request.events:
            event_type = event.get("type", "neutral")
            weight = event.get("weight", 1.0)
            
            if event_type == "positive":
                current_score = min(100, current_score + (weight * 5))
            elif event_type == "negative":
                current_score = max(0, current_score - (weight * 5))
        
        # Determine trust level
        if current_score >= 85:
            trust_level = "excellent"
            recommendations = [
                "Move to closing questions",
                "Offer premium options",
                "Ask for commitment"
            ]
        elif current_score >= 70:
            trust_level = "good"
            recommendations = [
                "Continue building value",
                "Address remaining concerns",
                "Introduce success stories"
            ]
        elif current_score >= 50:
            trust_level = "moderate"
            recommendations = [
                "Focus on building rapport",
                "Provide more evidence",
                "Slow down pace"
            ]
        else:
            trust_level = "low"
            recommendations = [
                "Rebuild trust urgently",
                "Address major concerns",
                "Consider alternative approach"
            ]
        
        return TrustScoreResponse(
            call_id=request.call_id,
            initial_score=45.0,
            current_score=current_score,
            trust_level=trust_level,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Trust calculation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pathway/navigate", response_model=PathwayNavigationResponse)
async def navigate_pathway(request: PathwayNavigationRequest):
    """
    Navigate conversation pathways based on user input and context.
    
    Determines the next conversation node based on branching logic,
    persona type, trust score, and user responses.
    """
    try:
        # This would connect to actual pathway logic
        # For now, returning a mock navigation response
        
        # Simple branching based on trust score
        if request.trust_score >= 70:
            next_node = "value_proposition"
            response_text = "Based on what you've told me, our program can save you significant time and money..."
            branch_taken = "high_trust_path"
            trust_adjustment = 5.0
        elif request.trust_score >= 50:
            next_node = "address_concerns"
            response_text = "I understand your concerns. Let me explain how we address those..."
            branch_taken = "moderate_trust_path"
            trust_adjustment = 3.0
        else:
            next_node = "rebuild_rapport"
            response_text = "I hear you. Let's take a step back and make sure I understand your situation..."
            branch_taken = "low_trust_path"
            trust_adjustment = 2.0
        
        return PathwayNavigationResponse(
            next_node=next_node,
            response_text=response_text,
            branch_taken=branch_taken,
            trust_adjustment=trust_adjustment,
            metadata={
                "persona_adjustments_applied": bool(request.persona_type),
                "context_considered": len(request.context) > 0
            }
        )
        
    except Exception as e:
        logger.error(f"Pathway navigation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/states/{state_code}/requirements", response_model=StateRequirementsResponse)
async def get_state_requirements(
    state_code: str,
    license_class: Optional[str] = Query(None, description="License class filter"),
    license_type: Optional[str] = Query(None, description="License type filter")
):
    """
    Get comprehensive state licensing requirements.
    
    Returns detailed requirements including experience, education,
    exams, bonds, insurance, fees, and processing timelines.
    """
    try:
        # This would query the actual database
        # For now, returning mock data for Georgia as an example
        
        if state_code.upper() == "GA":
            requirements = [
                {
                    "category": "experience",
                    "requirement": "4 years experience or equivalent education",
                    "details": "Journey level or as foreman, supervising employee, contractor, or owner-builder"
                },
                {
                    "category": "exams",
                    "requirement": "Two exams required",
                    "details": "Business & Law (110 questions, 4 hours) and Trade exam (110 questions, 4 hours). Both require 70% passing score."
                },
                {
                    "category": "bond",
                    "requirement": "$10,000 surety bond",
                    "details": "Required for general contractors"
                },
                {
                    "category": "fees",
                    "requirement": "Application fee $200",
                    "details": "Total costs range $300-400"
                }
            ]
            
            summary = ("Georgia requires contractors to be licensed for work over $2,500. "
                      "General contractor license requires 4 years experience or equivalent education. "
                      "Application fee is $200, with total costs ranging $300-400. "
                      "Two exams required with 70% passing score. "
                      "$10,000 surety bond required for general contractors.")
            
            return StateRequirementsResponse(
                state_code="GA",
                state_name="Georgia",
                requirements=requirements,
                summary=summary,
                metadata={
                    "regulatory_body": "Georgia State Licensing Board for Residential and General Contractors",
                    "processing_timeline": "4-6 weeks",
                    "renewal_cycle": "Every 2 years"
                }
            )
        else:
            raise HTTPException(status_code=404, detail=f"State {state_code} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"State requirements lookup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/success-stories")
async def get_success_stories(
    persona_type: Optional[str] = Query(None, description="Filter by persona type"),
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(5, description="Maximum number of stories")
):
    """
    Get relevant success stories for social proof.
    
    Returns success stories filtered by persona type and state
    to provide targeted social proof during conversations.
    """
    try:
        # This would query the actual database
        # For now, returning mock success stories
        
        stories = [
            {
                "id": "SS001",
                "title": "From Struggling to Six Figures",
                "customer_profile": {
                    "name": "John D.",
                    "state": "GA",
                    "background": "Small contractor struggling with licensing"
                },
                "summary": "Increased revenue by 250% in first year after getting licensed",
                "roi_metrics": {
                    "revenue_increase": "250%",
                    "time_to_roi": "3 months",
                    "contracts_gained": 15
                },
                "testimonial": "Getting my license through CLP was the best business decision I've made.",
                "persona_match": ["overwhelmed_veteran", "ambitious_grower"]
            }
        ]
        
        return {
            "stories": stories,
            "total": len(stories),
            "filters_applied": {
                "persona_type": persona_type,
                "state": state
            }
        }
        
    except Exception as e:
        logger.error(f"Success stories retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/objections/{objection_type}/response")
async def get_objection_response(
    objection_type: str,
    persona_type: Optional[str] = Query(None, description="Persona for customization"),
    trust_level: Optional[str] = Query("moderate", description="Current trust level")
):
    """
    Get scripted responses for common objections.
    
    Returns persona-specific objection handling scripts
    based on the type of objection and current trust level.
    """
    try:
        # Map of common objections to responses
        objection_responses = {
            "too_expensive": {
                "base_response": "I understand cost is a concern. Let me show you how this investment typically pays for itself within 3-4 months...",
                "follow_up": "Would you like to see the ROI calculator specific to your state?",
                "success_story_prompt": "John from Georgia had the same concern, but he made back his investment in just 2 months."
            },
            "need_to_think": {
                "base_response": "Of course, this is an important decision. What specific aspects would you like to think about?",
                "follow_up": "Would it help if I could address any specific concerns you have right now?",
                "urgency_builder": "Just so you know, licensing requirements are getting stricter next quarter in your state."
            }
        }
        
        response = objection_responses.get(objection_type, {
            "base_response": "I understand your concern. Let me address that for you...",
            "follow_up": "Does that help clarify things for you?"
        })
        
        return {
            "objection_type": objection_type,
            "response_script": response.get("base_response", ""),
            "follow_up_question": response.get("follow_up", ""),
            "persona_variation": f"Adjusted for {persona_type}" if persona_type else None,
            "trust_adjustment": f"Optimized for {trust_level} trust" if trust_level else None
        }
        
    except Exception as e:
        logger.error(f"Objection response retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/conversation/{call_id}")
async def get_conversation_analytics(call_id: str):
    """
    Get analytics for a specific conversation.
    
    Returns comprehensive metrics including persona detection,
    trust progression, pathways traversed, and outcome analysis.
    """
    try:
        # This would query the actual analytics database
        # For now, returning mock analytics
        
        return {
            "call_id": call_id,
            "duration_seconds": 720,
            "detected_persona": "confused_newcomer",
            "persona_confidence": 0.82,
            "trust_progression": {
                "initial": 45,
                "peak": 78,
                "final": 72,
                "events": [
                    {"time": 60, "score": 50, "event": "engagement_positive"},
                    {"time": 180, "score": 65, "event": "validation_received"},
                    {"time": 360, "score": 78, "event": "objection_resolved"},
                    {"time": 600, "score": 72, "event": "commitment_hesitation"}
                ]
            },
            "knowledge_queries": 8,
            "objections_handled": 3,
            "outcome": "callback_scheduled",
            "recommendations": [
                "Follow up within 24 hours",
                "Send Georgia-specific information",
                "Emphasize ROI in next conversation"
            ]
        }
        
    except Exception as e:
        logger.error(f"Analytics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
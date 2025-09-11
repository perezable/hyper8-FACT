"""
VAPI Conversation Scoring and Journey Progression System

Tracks trust scores, persona confidence, and conversation journey
to enable dynamic response adjustments based on caller engagement.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import structlog
import json

logger = structlog.get_logger(__name__)


class ConversationStage(Enum):
    """Stages of the customer journey."""
    DISCOVERY = "discovery"          # 0-30 trust score
    VALUE_BUILDING = "value_building" # 30-50 trust score
    OBJECTION_HANDLING = "objection_handling" # 50-70 trust score
    CLOSING = "closing"              # 70-85 trust score
    COMMITMENT = "commitment"        # 85+ trust score


class PersonaType(Enum):
    """Customer persona types."""
    OVERWHELMED_VETERAN = "overwhelmed_veteran"
    CONFUSED_NEWCOMER = "confused_newcomer"
    URGENT_OPERATOR = "urgent_operator"
    STRATEGIC_INVESTOR = "strategic_investor"
    SKEPTICAL_SHOPPER = "skeptical_shopper"
    UNKNOWN = "unknown"


@dataclass
class ConversationMetrics:
    """Metrics tracked throughout the conversation."""
    trust_score: float = 45.0
    persona_type: PersonaType = PersonaType.UNKNOWN
    persona_confidence: float = 0.0
    objection_count: int = 0
    value_mentions: int = 0
    urgency_level: str = "medium"
    questions_asked: int = 0
    positive_signals: int = 0
    negative_signals: int = 0
    transfer_recommended: bool = False
    stage: ConversationStage = ConversationStage.DISCOVERY
    roi_calculated: bool = False
    appointment_ready: bool = False
    qualifier_interest: bool = False


@dataclass
class TrustEvent:
    """Event that affects trust score."""
    event_type: str  # positive, negative, neutral
    description: str
    impact: float  # -10 to +10
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationScorer:
    """Manages conversation scoring and journey progression."""
    
    def __init__(self):
        """Initialize the conversation scorer."""
        self.conversations: Dict[str, ConversationMetrics] = {}
        self.event_history: Dict[str, List[TrustEvent]] = {}
        
    def get_or_create_conversation(self, call_id: str) -> ConversationMetrics:
        """Get existing or create new conversation metrics."""
        if call_id not in self.conversations:
            self.conversations[call_id] = ConversationMetrics()
            self.event_history[call_id] = []
        return self.conversations[call_id]
    
    def detect_persona(self, call_id: str, text: str) -> Tuple[PersonaType, float]:
        """
        Detect customer persona from conversation text.
        Returns persona type and confidence score.
        """
        text_lower = text.lower()
        persona_scores = {}
        
        # Overwhelmed Veteran patterns
        overwhelmed_keywords = ["complicated", "stressed", "too much", "overwhelming", 
                               "drowning", "confused by all", "bureaucracy", "red tape"]
        overwhelmed_score = sum(1 for kw in overwhelmed_keywords if kw in text_lower)
        persona_scores[PersonaType.OVERWHELMED_VETERAN] = overwhelmed_score
        
        # Confused Newcomer patterns
        newcomer_keywords = ["new to this", "first time", "beginner", "never done",
                            "where do i start", "don't understand", "explain", "help me understand"]
        newcomer_score = sum(1 for kw in newcomer_keywords if kw in text_lower)
        persona_scores[PersonaType.CONFUSED_NEWCOMER] = newcomer_score
        
        # Urgent Operator patterns
        urgent_keywords = ["quickly", "urgent", "deadline", "asap", "immediately",
                          "time sensitive", "rush", "need this now", "fast"]
        urgent_score = sum(1 for kw in urgent_keywords if kw in text_lower)
        persona_scores[PersonaType.URGENT_OPERATOR] = urgent_score
        
        # Strategic Investor patterns
        investor_keywords = ["income", "business", "profit", "passive income", "roi",
                           "make money", "earn", "qualifier", "network", "opportunity"]
        investor_score = sum(1 for kw in investor_keywords if kw in text_lower)
        persona_scores[PersonaType.STRATEGIC_INVESTOR] = investor_score
        
        # Skeptical Shopper patterns
        skeptical_keywords = ["price", "cost", "cheaper", "compare", "other options",
                            "guarantee", "proof", "references", "why should i"]
        skeptical_score = sum(1 for kw in skeptical_keywords if kw in text_lower)
        persona_scores[PersonaType.SKEPTICAL_SHOPPER] = skeptical_score
        
        # Determine persona with highest score
        if max(persona_scores.values()) == 0:
            return PersonaType.UNKNOWN, 0.0
        
        detected_persona = max(persona_scores, key=persona_scores.get)
        max_score = persona_scores[detected_persona]
        confidence = min(1.0, max_score / 3.0)  # Cap at 1.0, 3 keywords = high confidence
        
        # Update conversation metrics
        metrics = self.get_or_create_conversation(call_id)
        if confidence > metrics.persona_confidence:
            metrics.persona_type = detected_persona
            metrics.persona_confidence = confidence
            
            # Set urgency based on persona
            if detected_persona == PersonaType.URGENT_OPERATOR:
                metrics.urgency_level = "high"
            elif detected_persona == PersonaType.STRATEGIC_INVESTOR:
                metrics.urgency_level = "medium"
            else:
                metrics.urgency_level = "low"
        
        logger.info(f"Persona detected for {call_id}: {detected_persona.value} (confidence: {confidence:.2f})")
        return detected_persona, confidence
    
    def process_trust_event(self, call_id: str, event_type: str, 
                           description: str, custom_impact: Optional[float] = None) -> float:
        """
        Process an event that affects trust score.
        Returns updated trust score.
        """
        metrics = self.get_or_create_conversation(call_id)
        
        # Determine impact based on event type and description
        impact = custom_impact if custom_impact is not None else self._calculate_impact(event_type, description)
        
        # Create and store event
        event = TrustEvent(event_type=event_type, description=description, impact=impact)
        if call_id not in self.event_history:
            self.event_history[call_id] = []
        self.event_history[call_id].append(event)
        
        # Update trust score
        old_score = metrics.trust_score
        metrics.trust_score = max(0, min(100, metrics.trust_score + impact))
        
        # Update positive/negative signal counts
        if event_type == "positive":
            metrics.positive_signals += 1
        elif event_type == "negative":
            metrics.negative_signals += 1
        
        # Update conversation stage based on new score
        self._update_stage(metrics)
        
        # Check for transfer triggers
        self._check_transfer_triggers(metrics)
        
        logger.info(f"Trust event for {call_id}: {event_type} ({description}) | Score: {old_score:.1f} → {metrics.trust_score:.1f}")
        
        return metrics.trust_score
    
    def _calculate_impact(self, event_type: str, description: str) -> float:
        """Calculate trust impact based on event type and description."""
        description_lower = description.lower()
        
        if event_type == "positive":
            # High impact positive events
            if any(kw in description_lower for kw in ["ready to start", "want to move forward", "interested"]):
                return 10.0
            # Medium impact positive events
            elif any(kw in description_lower for kw in ["makes sense", "good point", "tell me more"]):
                return 5.0
            # Low impact positive events
            else:
                return 2.5
                
        elif event_type == "negative":
            # High impact negative events
            if any(kw in description_lower for kw in ["not interested", "too expensive", "goodbye"]):
                return -10.0
            # Medium impact negative events
            elif any(kw in description_lower for kw in ["not sure", "skeptical", "doubt"]):
                return -5.0
            # Low impact negative events
            else:
                return -2.5
                
        else:  # neutral
            return 0.0
    
    def _update_stage(self, metrics: ConversationMetrics):
        """Update conversation stage based on trust score."""
        if metrics.trust_score >= 85:
            metrics.stage = ConversationStage.COMMITMENT
            metrics.appointment_ready = True
        elif metrics.trust_score >= 70:
            metrics.stage = ConversationStage.CLOSING
            metrics.appointment_ready = True
        elif metrics.trust_score >= 50:
            metrics.stage = ConversationStage.OBJECTION_HANDLING
        elif metrics.trust_score >= 30:
            metrics.stage = ConversationStage.VALUE_BUILDING
        else:
            metrics.stage = ConversationStage.DISCOVERY
    
    def _check_transfer_triggers(self, metrics: ConversationMetrics):
        """Check if transfer to expert is recommended."""
        # Transfer if high trust and complex needs
        if metrics.trust_score >= 70 and metrics.qualifier_interest:
            metrics.transfer_recommended = True
        
        # Transfer if strategic investor with good engagement
        elif metrics.persona_type == PersonaType.STRATEGIC_INVESTOR and metrics.trust_score >= 50:
            metrics.transfer_recommended = True
        
        # Transfer if multiple objections but still engaged
        elif metrics.objection_count >= 3 and metrics.trust_score >= 50:
            metrics.transfer_recommended = True
    
    def handle_objection(self, call_id: str, objection_type: str) -> Dict[str, Any]:
        """
        Handle an objection and return appropriate response strategy.
        """
        metrics = self.get_or_create_conversation(call_id)
        metrics.objection_count += 1
        
        # Process as negative event but with reduced impact for engaged callers
        impact = -5.0 if metrics.trust_score < 50 else -2.5
        self.process_trust_event(call_id, "negative", f"Objection: {objection_type}", impact)
        
        # Determine response strategy based on stage and persona
        response_strategy = self._get_objection_strategy(metrics, objection_type)
        
        return response_strategy
    
    def _get_objection_strategy(self, metrics: ConversationMetrics, objection_type: str) -> Dict[str, Any]:
        """Get personalized objection handling strategy."""
        strategy = {
            "objection_type": objection_type,
            "persona": metrics.persona_type.value,
            "stage": metrics.stage.value,
            "trust_score": metrics.trust_score,
            "approach": "",
            "key_points": [],
            "transfer_recommended": metrics.transfer_recommended
        }
        
        # Customize approach based on persona
        if metrics.persona_type == PersonaType.OVERWHELMED_VETERAN:
            strategy["approach"] = "empathetic_simplification"
            strategy["key_points"] = [
                "We handle all the complexity for you",
                "Simple step-by-step process",
                "98% success rate takes the stress away"
            ]
        elif metrics.persona_type == PersonaType.URGENT_OPERATOR:
            strategy["approach"] = "speed_focused"
            strategy["key_points"] = [
                "35-42 day timeline",
                "Start working immediately with qualifier",
                "Every day costs $500-$2,500 in lost opportunities"
            ]
        elif metrics.persona_type == PersonaType.STRATEGIC_INVESTOR:
            strategy["approach"] = "roi_focused"
            strategy["key_points"] = [
                "2,735% first-year ROI documented",
                "Qualifier network: $3,000-$6,000 monthly",
                "Investment pays for itself on first project"
            ]
        else:
            strategy["approach"] = "value_focused"
            strategy["key_points"] = [
                "98% approval rate vs 35-45% DIY",
                "Save 76-118 hours of your time",
                "Professional guidance ensures success"
            ]
        
        return strategy
    
    def get_response_tone(self, call_id: str) -> Dict[str, Any]:
        """
        Get recommended response tone based on journey progression.
        """
        metrics = self.get_or_create_conversation(call_id)
        
        tone_guide = {
            "stage": metrics.stage.value,
            "trust_score": metrics.trust_score,
            "persona": metrics.persona_type.value,
            "urgency": metrics.urgency_level,
            "energy_level": "medium",
            "formality": "professional_casual",
            "pace": "moderate",
            "focus": ""
        }
        
        # Adjust tone based on stage
        if metrics.stage == ConversationStage.DISCOVERY:
            tone_guide["energy_level"] = "warm"
            tone_guide["focus"] = "building_rapport"
            tone_guide["pace"] = "relaxed"
            
        elif metrics.stage == ConversationStage.VALUE_BUILDING:
            tone_guide["energy_level"] = "enthusiastic"
            tone_guide["focus"] = "education"
            tone_guide["pace"] = "moderate"
            
        elif metrics.stage == ConversationStage.OBJECTION_HANDLING:
            tone_guide["energy_level"] = "confident"
            tone_guide["focus"] = "reassurance"
            tone_guide["pace"] = "deliberate"
            
        elif metrics.stage == ConversationStage.CLOSING:
            tone_guide["energy_level"] = "motivating"
            tone_guide["focus"] = "action"
            tone_guide["pace"] = "energetic"
            
        elif metrics.stage == ConversationStage.COMMITMENT:
            tone_guide["energy_level"] = "celebratory"
            tone_guide["focus"] = "next_steps"
            tone_guide["pace"] = "confident"
        
        # Persona-specific adjustments
        if metrics.persona_type == PersonaType.OVERWHELMED_VETERAN:
            tone_guide["pace"] = "slow"
            tone_guide["energy_level"] = "calm"
            
        elif metrics.persona_type == PersonaType.URGENT_OPERATOR:
            tone_guide["pace"] = "fast"
            tone_guide["energy_level"] = "high"
            
        elif metrics.persona_type == PersonaType.SKEPTICAL_SHOPPER:
            tone_guide["formality"] = "professional"
            tone_guide["energy_level"] = "measured"
        
        return tone_guide
    
    def should_transfer(self, call_id: str) -> Tuple[bool, str]:
        """
        Determine if call should be transferred to expert.
        Returns (should_transfer, reason).
        """
        metrics = self.get_or_create_conversation(call_id)
        
        # High-priority transfer triggers
        if metrics.qualifier_interest and metrics.trust_score >= 50:
            return True, "Qualifier network interest with good engagement"
        
        if metrics.persona_type == PersonaType.STRATEGIC_INVESTOR and metrics.trust_score >= 60:
            return True, "Strategic investor ready for advanced discussion"
        
        if metrics.trust_score >= 80 and metrics.stage == ConversationStage.CLOSING:
            return True, "High trust score ready for expert closing"
        
        if metrics.objection_count >= 3 and metrics.trust_score >= 50:
            return True, "Multiple objections need expert handling"
        
        return False, "Continue with current agent"
    
    def get_conversation_summary(self, call_id: str) -> Dict[str, Any]:
        """Get comprehensive conversation summary for handoff or analysis."""
        metrics = self.get_or_create_conversation(call_id)
        events = self.event_history.get(call_id, [])
        
        return {
            "call_id": call_id,
            "metrics": {
                "trust_score": metrics.trust_score,
                "stage": metrics.stage.value,
                "persona": metrics.persona_type.value,
                "persona_confidence": metrics.persona_confidence,
                "urgency": metrics.urgency_level,
                "objection_count": metrics.objection_count,
                "positive_signals": metrics.positive_signals,
                "negative_signals": metrics.negative_signals,
                "appointment_ready": metrics.appointment_ready,
                "transfer_recommended": metrics.transfer_recommended,
                "qualifier_interest": metrics.qualifier_interest
            },
            "events": [
                {
                    "type": e.event_type,
                    "description": e.description,
                    "impact": e.impact,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in events[-10:]  # Last 10 events
            ],
            "recommendations": self._get_recommendations(metrics)
        }
    
    def _get_recommendations(self, metrics: ConversationMetrics) -> List[str]:
        """Get recommended next actions based on metrics."""
        recommendations = []
        
        if metrics.appointment_ready:
            recommendations.append("Ready for appointment booking")
        
        if metrics.transfer_recommended:
            recommendations.append("Transfer to expert consultant recommended")
        
        if metrics.trust_score < 30:
            recommendations.append("Focus on rapport building and discovery")
        elif metrics.trust_score < 50:
            recommendations.append("Emphasize value proposition and benefits")
        elif metrics.trust_score < 70:
            recommendations.append("Address objections and build urgency")
        else:
            recommendations.append("Move toward commitment and next steps")
        
        if metrics.persona_type == PersonaType.URGENT_OPERATOR:
            recommendations.append("Emphasize speed and immediate action")
        elif metrics.persona_type == PersonaType.STRATEGIC_INVESTOR:
            recommendations.append("Focus on ROI and income opportunities")
        elif metrics.persona_type == PersonaType.OVERWHELMED_VETERAN:
            recommendations.append("Simplify and provide reassurance")
        
        return recommendations


# Global instance
conversation_scorer = ConversationScorer()
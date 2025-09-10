"""
VAPI Squad Routing Logic

Since VAPI doesn't support automatic routing based on persona detection,
we implement intelligent routing through our webhook functions.
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class PersonaScores:
    """Persona detection scores for routing decisions."""
    overwhelmed_veteran: float = 0.0
    confused_newcomer: float = 0.0
    urgent_operator: float = 0.0
    qualifier_network_specialist: float = 0.0

@dataclass
class RoutingRecommendation:
    """Routing recommendation with confidence score."""
    recommended_persona: str
    confidence: float
    reasoning: str
    transfer_message: Optional[str] = None

class VAPISquadRouter:
    """Intelligent routing for VAPI squad based on conversation analysis."""
    
    def __init__(self):
        self.assistant_mapping = {
            "overwhelmed_veteran": "8caf929b-ada3-476b-8523-f80ef6855b10",
            "confused_newcomer": "d87e82ce-bd5e-43b3-a992-c3790a214773", 
            "urgent_operator": "075cdd38-01e6-4adb-967c-8c6073a53af9",
            "qualifier_network_specialist": "6ee8dc58-6b82-4885-ad3c-dcfdc4b30e9b"
        }
        
        # Persona detection keywords and phrases
        self.persona_indicators = {
            "overwhelmed_veteran": [
                "overwhelming", "stressed", "complicated", "too much", 
                "confused", "help me understand", "break it down",
                "veteran", "military", "overwhelmed", "anxious",
                "don't know where to start", "this is complex"
            ],
            
            "confused_newcomer": [
                "new to this", "never done", "first time", "beginner",
                "what does that mean", "explain", "simple terms",
                "don't understand", "learning", "guide me",
                "step by step", "what is"
            ],
            
            "urgent_operator": [
                "quickly", "fast", "urgent", "ASAP", "deadline",
                "need this now", "time sensitive", "rush",
                "expedite", "immediate", "can't wait",
                "time frame", "how long", "fastest way"
            ],
            
            "qualifier_network_specialist": [
                "business opportunity", "make money", "income",
                "passive income", "network", "earn", "profit",
                "ROI", "investment", "business", "opportunity",
                "qualifying others", "help others get licensed"
            ]
        }
        
        # Context clues for deeper analysis
        self.context_clues = {
            "overwhelmed_veteran": {
                "emotional_indicators": ["stress", "worry", "anxiety", "fear"],
                "complexity_indicators": ["too many steps", "complicated process", "overwhelming"],
                "support_needs": ["help", "guidance", "support", "hand-holding"]
            },
            
            "confused_newcomer": {
                "knowledge_gaps": ["what", "how", "why", "when", "where"],
                "learning_indicators": ["teach", "explain", "show", "example"],
                "uncertainty": ["not sure", "don't know", "confused", "unclear"]
            },
            
            "urgent_operator": {
                "time_pressure": ["deadline", "soon", "quickly", "fast"],
                "urgency_words": ["need", "must", "have to", "required"],
                "action_oriented": ["do", "get", "start", "begin", "proceed"]
            },
            
            "qualifier_network_specialist": {
                "business_focus": ["business", "company", "income", "profit"],
                "network_interest": ["others", "people", "network", "referral"],
                "opportunity_seeking": ["opportunity", "potential", "possible", "chance"]
            }
        }
    
    def analyze_conversation_text(self, text: str, conversation_history: List[str] = None) -> PersonaScores:
        """
        Analyze conversation text to determine persona scores.
        
        Args:
            text: Recent conversation text
            conversation_history: Full conversation history for context
            
        Returns:
            PersonaScores with confidence levels for each persona
        """
        text_lower = text.lower()
        scores = PersonaScores()
        
        # Analyze recent text
        for persona, indicators in self.persona_indicators.items():
            score = 0.0
            matches = 0
            
            for indicator in indicators:
                if indicator.lower() in text_lower:
                    matches += 1
                    score += 1.0
            
            # Bonus for multiple matches
            if matches > 1:
                score += matches * 0.5
            
            # Context analysis
            if persona in self.context_clues:
                context_score = self._analyze_context(text_lower, self.context_clues[persona])
                score += context_score
            
            # Normalize score
            setattr(scores, persona, min(score / 10.0, 1.0))
        
        # Analyze conversation history if available
        if conversation_history:
            history_scores = self._analyze_conversation_history(conversation_history)
            scores = self._combine_scores(scores, history_scores)
        
        return scores
    
    def _analyze_context(self, text: str, context_clues: Dict[str, List[str]]) -> float:
        """Analyze contextual clues for deeper persona understanding."""
        total_score = 0.0
        
        for category, clues in context_clues.items():
            category_matches = sum(1 for clue in clues if clue in text)
            if category_matches > 0:
                total_score += category_matches * 0.3
        
        return total_score
    
    def _analyze_conversation_history(self, history: List[str]) -> PersonaScores:
        """Analyze full conversation history for patterns."""
        combined_text = " ".join(history).lower()
        
        # Look for patterns across the conversation
        scores = PersonaScores()
        
        for persona, indicators in self.persona_indicators.items():
            pattern_score = 0.0
            
            # Count indicator frequency
            for indicator in indicators:
                pattern_score += combined_text.count(indicator.lower()) * 0.2
            
            # Normalize
            setattr(scores, persona, min(pattern_score / 5.0, 1.0))
        
        return scores
    
    def _combine_scores(self, recent_scores: PersonaScores, history_scores: PersonaScores) -> PersonaScores:
        """Combine recent text scores with conversation history scores."""
        combined = PersonaScores()
        
        # Weight recent conversation more heavily
        for field in recent_scores.__dataclass_fields__:
            recent_val = getattr(recent_scores, field)
            history_val = getattr(history_scores, field)
            combined_val = (recent_val * 0.7) + (history_val * 0.3)
            setattr(combined, field, combined_val)
        
        return combined
    
    def get_routing_recommendation(self, text: str, conversation_history: List[str] = None, 
                                 current_assistant: str = None) -> RoutingRecommendation:
        """
        Get routing recommendation based on conversation analysis.
        
        Args:
            text: Recent conversation text
            conversation_history: Full conversation history
            current_assistant: Currently active assistant ID
            
        Returns:
            RoutingRecommendation with suggested persona and reasoning
        """
        scores = self.analyze_conversation_text(text, conversation_history)
        
        # Find highest scoring persona
        persona_scores = {
            "overwhelmed_veteran": scores.overwhelmed_veteran,
            "confused_newcomer": scores.confused_newcomer,
            "urgent_operator": scores.urgent_operator,
            "qualifier_network_specialist": scores.qualifier_network_specialist
        }
        
        best_persona = max(persona_scores, key=persona_scores.get)
        best_score = persona_scores[best_persona]
        
        # Check if transfer is recommended
        current_persona = self._get_current_persona(current_assistant)
        
        # Don't recommend transfer if confidence is too low
        if best_score < 0.3:
            return RoutingRecommendation(
                recommended_persona=current_persona or "confused_newcomer",
                confidence=best_score,
                reasoning="Low confidence in persona detection, maintaining current assistant"
            )
        
        # Don't recommend transfer if already on the right assistant
        if current_persona == best_persona and best_score < 0.8:
            return RoutingRecommendation(
                recommended_persona=best_persona,
                confidence=best_score,
                reasoning=f"Current assistant ({current_persona}) is appropriate for detected persona"
            )
        
        # Recommend transfer
        transfer_messages = {
            "overwhelmed_veteran": "I understand this feels overwhelming. Let me connect you with our specialist who's great at breaking things down step-by-step.",
            "confused_newcomer": "I can see you're new to this process. Let me transfer you to our guide who specializes in helping newcomers.",
            "urgent_operator": "I hear that you need this done quickly. Let me connect you with our fast-track specialist.",
            "qualifier_network_specialist": "It sounds like you're interested in the business opportunity side. Let me connect you with our network specialist."
        }
        
        return RoutingRecommendation(
            recommended_persona=best_persona,
            confidence=best_score,
            reasoning=f"Detected {best_persona} persona with {best_score:.2f} confidence",
            transfer_message=transfer_messages.get(best_persona)
        )
    
    def _get_current_persona(self, assistant_id: str) -> Optional[str]:
        """Get persona name from assistant ID."""
        for persona, aid in self.assistant_mapping.items():
            if aid == assistant_id:
                return persona
        return None
    
    def get_transfer_instructions(self, recommendation: RoutingRecommendation) -> Dict[str, Any]:
        """
        Generate transfer instructions for VAPI.
        
        Since VAPI doesn't support automatic transfers, this returns
        information that can be used by the assistant or dashboard.
        """
        return {
            "action": "transfer_recommended",
            "target_assistant_id": self.assistant_mapping.get(recommendation.recommended_persona),
            "target_persona": recommendation.recommended_persona,
            "confidence": recommendation.confidence,
            "reasoning": recommendation.reasoning,
            "transfer_message": recommendation.transfer_message,
            "manual_transfer_instruction": f"Transfer to {recommendation.recommended_persona.replace('_', ' ').title()}"
        }

# Global router instance
_router = None

def get_router() -> VAPISquadRouter:
    """Get the global router instance."""
    global _router
    if _router is None:
        _router = VAPISquadRouter()
    return _router

async def detect_persona_webhook(text: str, conversation_history: List[str] = None, 
                                current_assistant: str = None) -> Dict[str, Any]:
    """
    Webhook function for persona detection and routing.
    
    This function can be called by VAPI assistants to get routing recommendations.
    """
    try:
        router = get_router()
        recommendation = router.get_routing_recommendation(
            text=text,
            conversation_history=conversation_history,
            current_assistant=current_assistant
        )
        
        return {
            "detected_persona": recommendation.recommended_persona,
            "confidence": recommendation.confidence,
            "reasoning": recommendation.reasoning,
            "transfer_recommended": recommendation.transfer_message is not None,
            "transfer_message": recommendation.transfer_message,
            "transfer_instructions": router.get_transfer_instructions(recommendation)
        }
        
    except Exception as e:
        logger.error(f"Error in persona detection: {e}")
        return {
            "detected_persona": "confused_newcomer",  # Default fallback
            "confidence": 0.0,
            "reasoning": f"Error in detection: {str(e)}",
            "transfer_recommended": False,
            "error": str(e)
        }
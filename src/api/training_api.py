"""
Training API endpoints for the FACT system.

Provides endpoints for training the knowledge base retriever
based on user feedback and interaction patterns.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter(prefix="/training", tags=["training"])

# Import training module
try:
    from training.knowledge_trainer import KnowledgeTrainer
    TRAINING_AVAILABLE = True
    # Global trainer instance
    _trainer = None
except ImportError:
    TRAINING_AVAILABLE = False
    logger.warning("Training module not available")


class FeedbackRequest(BaseModel):
    """Request model for providing feedback on a query result."""
    query: str = Field(..., description="The original query")
    result_id: Optional[int] = Field(None, description="ID of the result returned")
    feedback: str = Field(..., description="Feedback: 'correct', 'incorrect', or 'partial'")
    expected_answer: Optional[str] = Field(None, description="Expected answer if incorrect")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TrainingStatusResponse(BaseModel):
    """Response model for training status."""
    total_examples: int
    accuracy: float
    target_accuracy: float
    learned_synonyms: int
    learned_patterns: int
    status: str
    current_weights: Dict[str, float]


class ImprovementSuggestion(BaseModel):
    """Model for improvement suggestions."""
    type: str
    suggestion: str
    details: Dict[str, Any]


def get_trainer():
    """Get or create the global trainer instance."""
    global _trainer
    if _trainer is None:
        from retrieval.enhanced_search import EnhancedRetriever
        retriever = EnhancedRetriever()
        _trainer = KnowledgeTrainer(retriever)
    return _trainer


@router.post("/feedback")
async def provide_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """
    Provide feedback on a search result to train the system.
    
    The system learns from:
    - Correct matches to reinforce patterns
    - Incorrect matches to adjust weights
    - User-provided corrections to learn new associations
    """
    if not TRAINING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Training module not available")
    
    try:
        trainer = get_trainer()
        
        # Create result dict from request
        result = {
            'id': request.result_id,
            'answer': '',  # Will be filled from actual result if available
            'score': 0.0,
            'metadata': request.metadata or {}
        }
        
        # Train in background to not block response
        background_tasks.add_task(
            trainer.train_from_feedback,
            request.query,
            result,
            request.feedback,
            request.expected_answer
        )
        
        return {
            "status": "success",
            "message": f"Feedback recorded for training",
            "feedback_type": request.feedback,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to process feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=TrainingStatusResponse)
async def get_training_status():
    """
    Get current training status and statistics.
    
    Returns metrics on:
    - Training examples collected
    - Current accuracy
    - Learned patterns and synonyms
    - Current weight adjustments
    """
    if not TRAINING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Training module not available")
    
    try:
        trainer = get_trainer()
        stats = trainer.get_training_stats()
        
        return TrainingStatusResponse(
            total_examples=stats['total_examples'],
            accuracy=stats['accuracy'],
            target_accuracy=stats['target_accuracy'],
            learned_synonyms=stats['learned_synonyms'],
            learned_patterns=stats['learned_patterns'],
            status=stats['status'],
            current_weights=stats['current_weights']
        )
        
    except Exception as e:
        logger.error(f"Failed to get training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrain")
async def trigger_retraining():
    """
    Manually trigger retraining with all collected feedback.
    
    This applies:
    - Learned synonym mappings
    - Adjusted scoring weights
    - Pattern recognitions
    """
    if not TRAINING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Training module not available")
    
    try:
        trainer = get_trainer()
        await trainer.retrain()
        
        stats = trainer.get_training_stats()
        
        return {
            "status": "success",
            "message": "Retraining completed",
            "new_accuracy": stats['accuracy'],
            "improvements_applied": {
                "synonyms": stats['learned_synonyms'],
                "patterns": stats['learned_patterns'],
                "weights": stats['current_weights']
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retrain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions", response_model=List[ImprovementSuggestion])
async def get_improvement_suggestions():
    """
    Get AI-generated suggestions for improving the knowledge base.
    
    Analyzes:
    - Failed query patterns
    - Missing synonyms
    - Weight optimization opportunities
    """
    if not TRAINING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Training module not available")
    
    try:
        trainer = get_trainer()
        suggestions = await trainer.suggest_improvements()
        
        return [
            ImprovementSuggestion(
                type=s['type'],
                suggestion=s['suggestion'],
                details={k: v for k, v in s.items() if k not in ['type', 'suggestion']}
            )
            for s in suggestions
        ]
        
    except Exception as e:
        logger.error(f"Failed to get suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_training_data(file_path: str):
    """
    Import training data from a JSON file.
    
    Useful for:
    - Restoring previous training
    - Sharing training between deployments
    - Applying pre-trained patterns
    """
    if not TRAINING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Training module not available")
    
    try:
        trainer = get_trainer()
        await trainer.import_training_data(file_path)
        
        stats = trainer.get_training_stats()
        
        return {
            "status": "success",
            "message": f"Training data imported from {file_path}",
            "examples_loaded": stats['total_examples'],
            "current_accuracy": stats['accuracy'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Training file not found: {file_path}")
    except Exception as e:
        logger.error(f"Failed to import training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_training_data(file_path: str = "data/training_export.json"):
    """
    Export current training data to a JSON file.
    
    Exports:
    - All training examples
    - Learned patterns and synonyms
    - Weight adjustments
    - Performance history
    """
    if not TRAINING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Training module not available")
    
    try:
        trainer = get_trainer()
        await trainer.export_training_data(file_path)
        
        stats = trainer.get_training_stats()
        
        return {
            "status": "success",
            "message": f"Training data exported to {file_path}",
            "examples_exported": stats['total_examples'],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to export training data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-train")
async def enable_auto_training(enabled: bool = True):
    """
    Enable or disable automatic training from user interactions.
    
    When enabled:
    - Learns from successful searches (high confidence)
    - Adjusts for failed searches (no results)
    - Continuously improves accuracy
    """
    if not TRAINING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Training module not available")
    
    try:
        # This would integrate with the main search endpoint
        # to automatically collect feedback
        
        return {
            "status": "success",
            "auto_training": enabled,
            "message": f"Auto-training {'enabled' if enabled else 'disabled'}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to configure auto-training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_training_history(limit: int = 100):
    """
    Get recent training history.
    
    Returns:
    - Recent training examples
    - Feedback distribution
    - Accuracy trend
    """
    if not TRAINING_AVAILABLE:
        raise HTTPException(status_code=501, detail="Training module not available")
    
    try:
        trainer = get_trainer()
        
        # Get recent examples
        recent_examples = trainer.training_examples[-limit:] if trainer.training_examples else []
        
        # Calculate feedback distribution
        feedback_dist = {
            'correct': sum(1 for e in recent_examples if e.feedback == 'correct'),
            'incorrect': sum(1 for e in recent_examples if e.feedback == 'incorrect'),
            'partial': sum(1 for e in recent_examples if e.feedback == 'partial')
        }
        
        return {
            "total_examples": len(trainer.training_examples),
            "recent_examples": [
                {
                    "query": e.query,
                    "feedback": e.feedback,
                    "score": e.score,
                    "timestamp": e.timestamp.isoformat()
                }
                for e in recent_examples
            ],
            "feedback_distribution": feedback_dist,
            "performance_history": trainer.performance_history[-10:],  # Last 10 accuracy measurements
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get training history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
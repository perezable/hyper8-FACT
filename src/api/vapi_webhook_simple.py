"""
Simple VAPI Webhook Handler that queries PostgreSQL directly.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Header
from pydantic import BaseModel, Field
import json
import asyncio
import asyncpg
import structlog
import os
from difflib import SequenceMatcher

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/vapi-simple", tags=["vapi-simple"])

# Import security if available
try:
    from .vapi_security import verify_vapi_request
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    async def verify_vapi_request(request: Request, 
                                 x_vapi_signature: Optional[str] = Header(None),
                                 x_api_key: Optional[str] = Header(None)):
        return True


class VAPIFunctionCall(BaseModel):
    name: str = Field(..., description="Function name")
    parameters: Dict[str, Any] = Field(..., description="Function parameters")


class VAPIMessage(BaseModel):
    type: str = Field(..., description="Message type")
    functionCall: Optional[VAPIFunctionCall] = Field(None, description="Function call details")


class VAPICall(BaseModel):
    id: str = Field(..., description="Call ID")


class VAPIWebhookRequest(BaseModel):
    message: VAPIMessage = Field(..., description="Message details")
    call: VAPICall = Field(..., description="Call information")


class VAPIWebhookResponse(BaseModel):
    result: Dict[str, Any] = Field(..., description="Function result")
    error: Optional[str] = Field(None, description="Error message if any")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Response metadata")


async def search_knowledge_simple(query: str, state: Optional[str] = None) -> Dict[str, Any]:
    """
    Simple direct PostgreSQL search.
    """
    try:
        if not os.getenv("DATABASE_URL"):
            logger.warning("No DATABASE_URL found")
            return {
                "answer": "Database not configured.",
                "confidence": 0.0,
                "source": "error"
            }
        
        conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
        
        try:
            # Simple search query
            if state:
                sql_query = """
                SELECT id, question, answer, category, state
                FROM knowledge_base
                WHERE state = $1 
                AND (LOWER(question) LIKE LOWER($2) OR LOWER(answer) LIKE LOWER($2))
                LIMIT 5
                """
                search_pattern = f"%{query}%"
                rows = await conn.fetch(sql_query, state.upper(), search_pattern)
            else:
                sql_query = """
                SELECT id, question, answer, category, state
                FROM knowledge_base
                WHERE LOWER(question) LIKE LOWER($1) OR LOWER(answer) LIKE LOWER($1)
                LIMIT 5
                """
                search_pattern = f"%{query}%"
                rows = await conn.fetch(sql_query, search_pattern)
            
            logger.info(f"Query: '{query}', State: {state}, Found: {len(rows)} results")
            
            if rows:
                # Score results by similarity
                best_score = 0
                best_result = None
                
                for row in rows:
                    # Calculate similarity score
                    q_score = SequenceMatcher(None, query.lower(), row['question'].lower()).ratio()
                    a_score = SequenceMatcher(None, query.lower(), row['answer'].lower()).ratio() * 0.5
                    score = max(q_score, a_score)
                    
                    if score > best_score:
                        best_score = score
                        best_result = row
                
                if best_result:
                    return {
                        "answer": best_result['answer'],
                        "category": best_result['category'],
                        "confidence": min(0.95, best_score + 0.3),  # Boost confidence
                        "source": "knowledge_base",
                        "state": best_result['state'],
                        "voice_optimized": True,
                        "metadata": {
                            "question_id": best_result['id'],
                            "score": best_score
                        }
                    }
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"Search error: {e}")
    
    # Default response
    return {
        "answer": "I can help you with contractor licensing information. Could you be more specific?",
        "category": "general",
        "confidence": 0.5,
        "source": "default",
        "state": state,
        "voice_optimized": True
    }


@router.post("/webhook", response_model=VAPIWebhookResponse)
async def vapi_webhook_simple(request: VAPIWebhookRequest):
    """
    Simple VAPI webhook handler.
    """
    try:
        if request.message.type == "function-call" and request.message.functionCall:
            function_name = request.message.functionCall.name
            parameters = request.message.functionCall.parameters
            
            if function_name == "searchKnowledge":
                result = await search_knowledge_simple(
                    query=parameters.get("query", ""),
                    state=parameters.get("state")
                )
                
                return VAPIWebhookResponse(
                    result=result,
                    metadata={"call_id": request.call.id, "function": "searchKnowledge"}
                )
        
        return VAPIWebhookResponse(
            result={"message": "Unknown function"},
            metadata={"call_id": request.call.id}
        )
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return VAPIWebhookResponse(
            result={"message": "Error processing request"},
            error=str(e),
            metadata={"call_id": request.call.id}
        )
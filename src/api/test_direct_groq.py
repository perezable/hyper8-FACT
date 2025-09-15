"""
Direct Groq API test endpoint bypassing all FACT error handling
"""

import os
from fastapi import APIRouter
from groq import Groq
import structlog
import traceback

router = APIRouter(prefix="/api", tags=["test"])
logger = structlog.get_logger(__name__)

@router.post("/test-direct-groq")
async def test_direct_groq(query: str):
    """Test Groq API directly without FACT driver"""
    
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key:
        return {
            "status": "error",
            "message": "GROQ_API_KEY not found"
        }
    
    try:
        # Direct Groq API call
        client = Groq(api_key=groq_key)
        
        # Simple system prompt
        system_prompt = "You are a helpful assistant for contractor licensing questions. Provide detailed, accurate information about contractor licensing, NASCLA certification, state requirements, and related topics."
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        
        response_text = response.choices[0].message.content
        
        return {
            "status": "success",
            "query": query,
            "response": response_text,
            "model": response.model,
            "tokens": response.usage.total_tokens
        }
        
    except Exception as e:
        tb = traceback.format_exc()
        return {
            "status": "error",
            "query": query,
            "error": str(e),
            "traceback": tb
        }
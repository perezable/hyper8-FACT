"""
Test endpoint to verify Groq API configuration
"""

import os
from fastapi import APIRouter
from groq import Groq
import structlog

router = APIRouter(prefix="/api", tags=["test"])
logger = structlog.get_logger(__name__)

@router.get("/test-groq")
async def test_groq():
    """Test if Groq API is configured and working"""
    
    groq_key = os.getenv("GROQ_API_KEY")
    
    if not groq_key:
        return {
            "status": "error",
            "message": "GROQ_API_KEY not found in environment",
            "available_env_vars": list(os.environ.keys())
        }
    
    try:
        # Test Groq API
        client = Groq(api_key=groq_key)
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "user", "content": "Say 'Groq is working' if you can hear me"}
            ],
            max_tokens=20
        )
        
        return {
            "status": "success",
            "message": "Groq API is working",
            "groq_response": response.choices[0].message.content,
            "model": response.model,
            "key_length": len(groq_key)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Groq API test failed: {str(e)}",
            "key_present": True,
            "key_length": len(groq_key)
        }
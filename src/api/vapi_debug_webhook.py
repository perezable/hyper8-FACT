"""
Debug webhook to log raw VAPI requests and understand the 422 error
"""

from fastapi import APIRouter, Request
import structlog
import json

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/vapi-debug", tags=["vapi-debug"])


@router.post("/webhook")
async def debug_webhook(request: Request):
    """
    Debug endpoint to log raw VAPI requests.
    """
    # Get raw body
    body = await request.body()
    
    # Try to parse as JSON
    try:
        json_body = json.loads(body)
        logger.info("VAPI Request Received", 
                   method=request.method,
                   url=str(request.url),
                   headers=dict(request.headers),
                   body=json_body)
        
        # Log structure details
        logger.info("Request Structure",
                   has_message=("message" in json_body),
                   has_call=("call" in json_body),
                   message_type=json_body.get("message", {}).get("type", "MISSING"),
                   call_id=json_body.get("call", {}).get("id", "MISSING"),
                   assistant_id=json_body.get("assistant", {}).get("id", "MISSING") if "assistant" in json_body else "NO ASSISTANT FIELD",
                   top_level_keys=list(json_body.keys()))
        
        # Check for function call
        if "message" in json_body:
            message = json_body["message"]
            if "functionCall" in message:
                func_call = message["functionCall"]
                logger.info("Function Call Details",
                           function_name=func_call.get("name", "MISSING"),
                           has_parameters=("parameters" in func_call),
                           parameters=func_call.get("parameters", {}))
        
        # Return success to prevent VAPI from retrying
        return {
            "result": {
                "answer": "Debug webhook received request successfully",
                "debug_info": {
                    "request_keys": list(json_body.keys()),
                    "message_type": json_body.get("message", {}).get("type", "MISSING")
                }
            }
        }
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON", 
                    error=str(e),
                    body=body.decode('utf-8') if body else "EMPTY")
        return {
            "error": "Invalid JSON",
            "raw_body": body.decode('utf-8') if body else "EMPTY"
        }
    except Exception as e:
        logger.error("Unexpected error", 
                    error=str(e),
                    type=type(e).__name__)
        return {
            "error": str(e)
        }
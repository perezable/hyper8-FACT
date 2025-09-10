#!/usr/bin/env python3
"""
Test simple VAPI webhook.
"""

import hmac
import hashlib
import json
import httpx
import asyncio

WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-simple/webhook"
WEBHOOK_SECRET = "a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb"

def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

async def test_query():
    """Test simple webhook."""
    
    queries = [
        ("Georgia", None),
        ("contractor license", None),
        ("Georgia contractor", None),
        ("requirements", "GA"),
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query, state in queries:
            print(f"\n{'='*60}")
            print(f"Query: '{query}' | State: {state}")
            print('-'*60)
            
            payload = {
                "message": {
                    "type": "function-call",
                    "functionCall": {
                        "name": "searchKnowledge",
                        "parameters": {
                            "query": query,
                            "state": state
                        }
                    }
                },
                "call": {
                    "id": f"test-{asyncio.get_event_loop().time()}"
                }
            }
            
            payload_str = json.dumps(payload, separators=(',', ':'))
            signature = generate_signature(payload_str, WEBHOOK_SECRET)
            
            headers = {
                "Content-Type": "application/json",
                "x-vapi-signature": signature
            }
            
            try:
                response = await client.post(
                    WEBHOOK_URL,
                    content=payload_str,
                    headers=headers
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get("result", {}).get("answer", "")
                    confidence = result.get("result", {}).get("confidence", 0)
                    source = result.get("result", {}).get("source", "")
                    
                    print(f"Source: {source}")
                    print(f"Confidence: {confidence:.2f}")
                    
                    if source == "knowledge_base":
                        print(f"✅ FOUND: {answer[:100]}...")
                    else:
                        print(f"❌ DEFAULT: {answer[:100]}...")
                else:
                    print(f"Error: {response.text}")
                    
            except Exception as e:
                print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_query())
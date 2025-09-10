#!/usr/bin/env python3
"""
Test VAPI webhook with direct query including state parameter.
"""

import hmac
import hashlib
import json
import httpx
import asyncio

WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"
WEBHOOK_SECRET = "a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb"

def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

async def test_query():
    """Test with Georgia state parameter."""
    
    query = "contractor license requirements"
    
    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": query,
                    "state": "GA",
                    "limit": 1
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
    
    print(f"Testing query: '{query}' with state: GA")
    print("-" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                content=payload_str,
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)}")
                
                # Check if we got real data
                answer = result.get("result", {}).get("answer", "")
                confidence = result.get("result", {}).get("confidence", 0)
                source = result.get("result", {}).get("source", "")
                
                print("\n" + "=" * 60)
                print("RESULTS ANALYSIS:")
                print(f"Source: {source}")
                print(f"Confidence: {confidence}")
                print(f"Got real answer: {source == 'knowledge_base'}")
                
                if confidence > 0.7:
                    print("✅ HIGH CONFIDENCE MATCH FOUND!")
                elif confidence > 0.5:
                    print("⚠️  Medium confidence - may need refinement")
                else:
                    print("❌ Low confidence - using default response")
                    
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_query())

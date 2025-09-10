#!/usr/bin/env python3
"""
Test VAPI webhook with simple Georgia query.
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
    """Test with exact match from knowledge API."""
    
    # Use the exact query that works in knowledge API
    query = "Georgia contractor license"
    
    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": query,
                    "limit": 3
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
    
    print(f"Testing VAPI webhook with query: '{query}'")
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
                
                # Extract key fields
                answer = result.get("result", {}).get("answer", "")
                confidence = result.get("result", {}).get("confidence", 0)
                source = result.get("result", {}).get("source", "")
                state = result.get("result", {}).get("state", "")
                
                print(f"\nResult:")
                print(f"  Source: {source}")
                print(f"  Confidence: {confidence:.2f}")
                print(f"  State: {state}")
                print(f"  Answer preview: {answer[:150]}...")
                
                if source == "knowledge_base" and confidence > 0.7:
                    print("\n✅ SUCCESS! VAPI webhook returned actual knowledge base data!")
                    print(f"   Achieved {confidence*100:.1f}% confidence")
                elif source == "knowledge_base":
                    print(f"\n⚠️  Found data but low confidence: {confidence:.2f}")
                else:
                    print(f"\n❌ FAILED: Using {source} response instead of knowledge_base")
                    
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_query())
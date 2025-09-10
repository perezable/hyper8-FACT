#!/usr/bin/env python3
"""
Test VAPI webhook with a real knowledge base query.
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

async def test_query(query: str):
    """Test a specific query."""
    
    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": query
                }
            }
        },
        "call": {
            "id": "test-call-123"
        }
    }
    
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = generate_signature(payload_str, WEBHOOK_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "x-vapi-signature": signature
    }
    
    print(f"Query: '{query}'")
    print("-" * 60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            WEBHOOK_URL,
            content=payload_str,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("result"):
                answer = result["result"].get("answer", "No answer")
                confidence = result["result"].get("confidence", 0)
                source = result["result"].get("source", "unknown")
                
                print(f"✅ Success!")
                print(f"Answer: {answer[:200]}...")
                print(f"Confidence: {confidence:.2f}")
                print(f"Source: {source}")
            else:
                print(f"❌ No result in response")
        else:
            print(f"❌ Request failed: {response.status_code}")

async def main():
    """Test multiple queries."""
    print("=" * 60)
    print("Testing VAPI Webhook with Real Queries")
    print("=" * 60)
    print()
    
    test_queries = [
        "What are the requirements for a contractor license in Georgia?",
        "How much does a contractor license cost?",
        "What's the ROI on getting licensed?",
        "How long does it take to get a license?",
        "What if I fail the contractor exam?"
    ]
    
    for query in test_queries:
        await test_query(query)
        print()

if __name__ == "__main__":
    asyncio.run(main())
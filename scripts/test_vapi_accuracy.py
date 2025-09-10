#!/usr/bin/env python3
"""
Test VAPI webhook accuracy with multiple queries.
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

async def test_query(query: str, state: str = None):
    """Test a single query."""
    
    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": query,
                    "state": state,
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
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            WEBHOOK_URL,
            content=payload_str,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "query": query,
                "state": state,
                "answer": result.get("result", {}).get("answer", "")[:100],
                "confidence": result.get("result", {}).get("confidence", 0),
                "source": result.get("result", {}).get("source", ""),
                "match_type": result.get("result", {}).get("match_type", "")
            }
        return None

async def main():
    """Test multiple queries."""
    
    test_cases = [
        ("Georgia contractor license", None),
        ("contractor license requirements", "GA"),
        ("how much does license cost", "GA"),
        ("exam requirements", "GA"),
        ("California contractor", None),
        ("Florida licensing", None),
        ("Texas requirements", None),
        ("bond requirements", "GA"),
        ("application process", "GA"),
        ("experience requirements", "GA"),
    ]
    
    print("VAPI Webhook Accuracy Test")
    print("=" * 80)
    
    successful = 0
    total = 0
    
    for query, state in test_cases:
        result = await test_query(query, state)
        if result:
            total += 1
            is_success = result["source"] == "knowledge_base" and result["confidence"] > 0.5
            if is_success:
                successful += 1
                status = "✅"
            else:
                status = "❌"
            
            print(f"\n{status} Query: '{query}' | State: {state or 'None'}")
            print(f"   Confidence: {result['confidence']:.2f} | Source: {result['source']} | Type: {result['match_type']}")
            print(f"   Answer: {result['answer']}...")
    
    accuracy = (successful / total * 100) if total > 0 else 0
    print("\n" + "=" * 80)
    print(f"RESULTS: {successful}/{total} successful ({accuracy:.1f}% accuracy)")
    
    if accuracy >= 96.7:
        print("✅ ACHIEVED TARGET 96.7% ACCURACY!")
    elif accuracy >= 90:
        print("⚠️  Good accuracy but below 96.7% target")
    else:
        print("❌ Below target accuracy")

if __name__ == "__main__":
    asyncio.run(main())
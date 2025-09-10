#!/usr/bin/env python3
"""
Test VAPI webhook and compare with knowledge API.
"""

import json
import httpx
import asyncio
import hmac
import hashlib

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"
WEBHOOK_SECRET = "a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb"

def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

async def test_both_endpoints():
    """Test both knowledge API and VAPI webhook."""
    
    query = "Georgia contractor license requirements"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test knowledge API first
        print("=" * 60)
        print("Testing Knowledge API")
        print("=" * 60)
        
        response = await client.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": query, "limit": 1}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data["results"]:
                result = data["results"][0]
                print(f"✅ Knowledge API Success!")
                print(f"   Question: {result['question']}")
                print(f"   Answer: {result['answer'][:150]}...")
                print(f"   State: {result['state']}")
                print(f"   Category: {result['category']}")
        else:
            print(f"❌ Knowledge API failed: {response.status_code}")
        
        print()
        
        # Test VAPI webhook
        print("=" * 60)
        print("Testing VAPI Webhook")
        print("=" * 60)
        
        payload = {
            "message": {
                "type": "function-call",
                "functionCall": {
                    "name": "searchKnowledge",
                    "parameters": {
                        "query": query,
                        "state": "GA"  # Try with explicit state
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
        
        response = await client.post(
            f"{RAILWAY_URL}/vapi/webhook",
            content=payload_str,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            print(f"✅ VAPI Webhook responded")
            print(f"   Answer: {result.get('answer', 'No answer')[:150]}...")
            print(f"   Confidence: {result.get('confidence', 0)}")
            print(f"   Source: {result.get('source', 'unknown')}")
            print(f"   State: {result.get('state', 'none')}")
            
            if result.get('source') == 'default':
                print("\n⚠️  VAPI is returning default fallback instead of actual data!")
                print("   This means the enhanced retriever is not finding matches.")
        else:
            print(f"❌ VAPI Webhook failed: {response.status_code}")
            print(f"   Error: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_both_endpoints())
#!/usr/bin/env python3
"""
Test VAPI webhook with proper HMAC authentication.
"""

import hmac
import hashlib
import json
import httpx
import asyncio

# Configuration
import sys
if len(sys.argv) > 1 and sys.argv[1] == "local":
    WEBHOOK_URL = "http://localhost:8000/vapi/webhook"
    print("Testing LOCAL server")
else:
    WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"
    print("Testing RAILWAY deployment")
    
WEBHOOK_SECRET = "a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb"  # From RAILWAY_ENV_CONFIG.md

def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

async def test_webhook():
    """Test the webhook with proper authentication."""
    
    # Create test payload
    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": "Georgia contractor license requirements"
                }
            }
        },
        "call": {
            "id": "test-call-123"
        }
    }
    
    # Convert to JSON string (no spaces after colons/commas for consistent hashing)
    payload_str = json.dumps(payload, separators=(',', ':'))
    
    # Generate signature
    signature = generate_signature(payload_str, WEBHOOK_SECRET)
    
    # Headers with signature
    headers = {
        "Content-Type": "application/json",
        "x-vapi-signature": signature
    }
    
    print(f"Testing webhook: {WEBHOOK_URL}")
    print(f"Signature: {signature}")
    print(f"Payload: {payload_str[:100]}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                content=payload_str,  # Use the exact string we signed
                headers=headers
            )
            
            print(f"\nStatus: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success! Authentication worked.")
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)[:500]}")
            elif response.status_code == 401:
                print("❌ Authentication failed. Check:")
                print("1. Is VAPI_WEBHOOK_SECRET set in Railway?")
                print("2. Does it match the secret in this script?")
                print(f"Response: {response.text}")
            else:
                print(f"Unexpected status: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_webhook())
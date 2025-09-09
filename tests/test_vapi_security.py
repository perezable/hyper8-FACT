#!/usr/bin/env python3
"""
Test VAPI webhook security
"""

import hmac
import hashlib
import json
import asyncio
import aiohttp
import sys
import os

# Test configuration
WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"
LOCAL_URL = "http://localhost:8000/vapi/webhook"

# Test secret (use the one you set in Railway)
TEST_SECRET = "a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb"


def generate_signature(payload: bytes, secret: str) -> str:
    """Generate HMAC-SHA256 signature for payload."""
    return hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()


async def test_webhook_security(base_url: str, use_local: bool = False):
    """Test webhook security configurations."""
    
    url = LOCAL_URL if use_local else base_url
    print(f"\n{'='*60}")
    print(f"Testing VAPI Webhook Security: {url}")
    print('='*60)
    
    # Test payload
    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": "test security"
                }
            }
        },
        "call": {
            "id": "security_test_123"
        }
    }
    
    payload_bytes = json.dumps(payload).encode()
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Without any authentication
        print("\n1. Testing WITHOUT authentication:")
        try:
            async with session.post(url, json=payload) as response:
                status = response.status
                if status == 200:
                    print(f"   ❌ INSECURE: Request accepted without auth (Status: {status})")
                elif status == 401:
                    print(f"   ✅ SECURE: Request rejected without auth (Status: {status})")
                else:
                    print(f"   ⚠️  Unexpected status: {status}")
                    print(f"   Response: {await response.text()}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: With invalid signature
        print("\n2. Testing with INVALID signature:")
        try:
            headers = {
                "X-Vapi-Signature": "invalid_signature_12345"
            }
            async with session.post(url, json=payload, headers=headers) as response:
                status = response.status
                if status == 200:
                    print(f"   ❌ INSECURE: Invalid signature accepted (Status: {status})")
                elif status == 401:
                    print(f"   ✅ SECURE: Invalid signature rejected (Status: {status})")
                else:
                    print(f"   ⚠️  Status: {status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 3: With valid signature
        print("\n3. Testing with VALID signature:")
        try:
            signature = generate_signature(payload_bytes, TEST_SECRET)
            headers = {
                "X-Vapi-Signature": signature
            }
            async with session.post(url, json=payload, headers=headers) as response:
                status = response.status
                if status == 200:
                    print(f"   ✅ Valid signature accepted (Status: {status})")
                    result = await response.json()
                    print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
                elif status == 401:
                    print(f"   ⚠️  Valid signature rejected - check secret configuration")
                else:
                    print(f"   ⚠️  Unexpected status: {status}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 4: Rate limiting
        print("\n4. Testing RATE LIMITING (10 rapid requests):")
        blocked = False
        for i in range(10):
            try:
                async with session.get(f"{url}/health") as response:
                    if response.status == 429:
                        print(f"   ✅ Rate limited after {i+1} requests")
                        blocked = True
                        break
            except:
                pass
        
        if not blocked:
            print(f"   ❌ No rate limiting detected after 10 requests")
        
        # Test 5: Check health endpoint
        print("\n5. Testing health endpoint (should be public):")
        try:
            health_url = url.replace("/webhook", "/webhook/health")
            async with session.get(health_url) as response:
                status = response.status
                if status == 200:
                    data = await response.json()
                    if "cache_size" in data:
                        print(f"   ⚠️  Health endpoint exposes internal data")
                    else:
                        print(f"   ✅ Health endpoint accessible (no sensitive data)")
                else:
                    print(f"   ❌ Health endpoint not accessible: {status}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "="*60)
    print("Security Assessment Complete")
    print("="*60)
    
    print("\nRECOMMENDATIONS:")
    print("1. Set VAPI_WEBHOOK_SECRET in Railway environment")
    print("2. Enable VAPI_RATE_LIMIT=true")
    print("3. Configure CORS_ORIGINS for your domains only")
    print("4. Consider adding API key authentication as backup")


async def main():
    """Run security tests."""
    # Test deployed version
    await test_webhook_security(WEBHOOK_URL)
    
    # Optionally test local version
    if "--local" in sys.argv:
        print("\n\nTesting LOCAL instance...")
        os.environ["VAPI_WEBHOOK_SECRET"] = TEST_SECRET
        os.environ["VAPI_RATE_LIMIT"] = "true"
        os.environ["VAPI_MAX_REQUESTS"] = "5"
        await test_webhook_security(LOCAL_URL, use_local=True)


if __name__ == "__main__":
    asyncio.run(main())
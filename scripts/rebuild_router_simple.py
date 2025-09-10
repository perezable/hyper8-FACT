#!/usr/bin/env python3
"""
Rebuild the Main Router with a simpler approach using VAPI's native transferCall.
Sometimes a fresh start with minimal configuration works better.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "c49631b4-2f8f-40b3-9ce1-22f731879fb9")
MAIN_ROUTER_ID = "686ead20-ceb5-45b3-a224-4ddb62f58bda"

# Get assistant IDs
with open("silent_transfer_squad_config.json", "r") as f:
    config = json.load(f)
    ASSISTANT_IDS = config["assistant_ids"]

# Simplified, direct system prompt
SYSTEM_PROMPT = """You help route contractor licensing calls.

When caller says "overwhelmed" or "stressed": 
Call transferCall function with assistantId "82efc90b-60f8-4fdd-b757-f089a8704123"

When caller says "new" or "confused":
Call transferCall function with assistantId "85ee06a0-b4fb-455a-8ef6-be1b169c57c7"

When caller says "quickly" or "urgent":
Call transferCall function with assistantId "2a340cc3-474e-4d2c-92d0-6590a7a22e80"

When caller says "business" or "money":
Call transferCall function with assistantId "d3ad7b67-93c4-4641-8c1f-130c4d1a284c"

Do not announce transfers. Just use the function."""

async def rebuild_router():
    """Rebuild the router with minimal configuration."""
    
    print("🔨 Rebuilding Main Router with Simple Configuration")
    print("=" * 60)
    
    # Minimal configuration focusing on core transfer functionality
    update_payload = {
        "name": "CLP-Main-Router",
        "model": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",  # Using 3.5 for faster, simpler responses
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ],
            "temperature": 0.1,  # Very low for deterministic behavior
            "maxTokens": 50  # Short responses only
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Rachel's actual ID
        },
        "functions": [
            {
                "name": "transferCall",
                "description": "Transfer to another assistant",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "assistantId": {
                            "type": "string",
                            "description": "Assistant ID to transfer to"
                        }
                    },
                    "required": ["assistantId"]
                }
            }
        ],
        "endCallFunctionEnabled": False,
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 0.5,
        "llmRequestDelaySeconds": 0.1,
        "firstMessage": "Hello, how can I help with your contractor licensing needs?",
        "firstMessageMode": "assistant-speaks-first"
    }
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Update the assistant with minimal config
        async with session.patch(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            json=update_payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Router rebuilt with simple configuration!")
                
                # Verify the configuration
                print("\n📋 New Configuration:")
                print("   - GPT-3.5-turbo for faster responses")
                print("   - Temperature 0.1 for consistency")
                print("   - Minimal prompt with direct instructions")
                print("   - Single transferCall function")
                print("   - No complex logic")
                
                # Test the function configuration
                if "functions" in data:
                    transfer_func = next(
                        (f for f in data["functions"] if f["name"] == "transferCall"),
                        None
                    )
                    if transfer_func:
                        print("   ✓ transferCall function configured")
                    else:
                        print("   ✗ transferCall function missing!")
                
                print("\n🧪 Simple Test Script:")
                print("1. Call the router")
                print("2. Say exactly: 'I am overwhelmed'")
                print("3. Router should transfer without announcing")
                
                return True
            else:
                error_text = await response.text()
                print(f"❌ Failed to update: {error_text}")
                
                # Try to parse error
                try:
                    error_data = json.loads(error_text)
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    pass
                
                return False

async def test_transfer_api():
    """Test if we can manually trigger a transfer via API."""
    print("\n🔍 Testing Manual Transfer via API...")
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try to get active calls (if any)
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.vapi.ai/call",
            headers=headers,
            params={"assistantId": MAIN_ROUTER_ID, "limit": 1}
        ) as response:
            if response.status == 200:
                calls = await response.json()
                if calls:
                    print(f"   Found {len(calls)} call(s)")
                    # Could potentially trigger transfer on active call
                else:
                    print("   No active calls to test with")
            else:
                print("   Could not retrieve calls")

async def main():
    """Main execution."""
    success = await rebuild_router()
    
    if success:
        await test_transfer_api()
        
        print("\n" + "=" * 60)
        print("🎯 Router Rebuilt with Simplest Configuration")
        print("\nIf transfers still don't work, the issue might be:")
        print("1. VAPI squad configuration preventing transfers")
        print("2. Need to use assistant names instead of IDs")
        print("3. May need to test with actual phone call (not dashboard)")
        print("\nAlternative: Try saying the specialist name directly:")
        print("'Transfer me to veteran support' might work better")
    else:
        print("\n⚠️ Rebuild failed. Check error above.")

if __name__ == "__main__":
    asyncio.run(main())
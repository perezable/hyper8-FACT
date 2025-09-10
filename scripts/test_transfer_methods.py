#!/usr/bin/env python3
"""
Test different transfer methods to see what VAPI actually accepts.
Try both assistant IDs and names to find what works.
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "c49631b4-2f8f-40b3-9ce1-22f731879fb9")
MAIN_ROUTER_ID = "686ead20-ceb5-45b3-a224-4ddb62f58bda"

# Get configuration
with open("silent_transfer_squad_config.json", "r") as f:
    config = json.load(f)
    ASSISTANT_IDS = config["assistant_ids"]

async def test_with_assistant_names():
    """Configure router to use assistant NAMES instead of IDs."""
    
    print("🔧 Testing with Assistant NAMES")
    print("=" * 60)
    
    # Try using assistant names for transfer
    system_prompt = """You help route contractor licensing calls.

When caller says "overwhelmed" or "stressed": 
Use transferCall function with assistantName "CLP-Veteran-Support"

When caller says "new" or "confused":
Use transferCall function with assistantName "CLP-Newcomer-Guide"

When caller says "quickly" or "urgent":
Use transferCall function with assistantName "CLP-Fast-Track"

When caller says "business" or "money":
Use transferCall function with assistantName "CLP-Network-Expert"

Just use the function, don't announce transfers."""
    
    update_payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ],
            "temperature": 0.1,
            "maxTokens": 50
        },
        "functions": [
            {
                "name": "transferCall",
                "description": "Transfer to another assistant by name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "assistantName": {
                            "type": "string",
                            "description": "Name of the assistant to transfer to",
                            "enum": [
                                "CLP-Veteran-Support",
                                "CLP-Newcomer-Guide",
                                "CLP-Fast-Track",
                                "CLP-Network-Expert"
                            ]
                        }
                    },
                    "required": ["assistantName"]
                }
            }
        ],
        "endCallFunctionEnabled": False
    }
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            json=update_payload,
            headers=headers
        ) as response:
            if response.status == 200:
                print("✅ Configured with assistant NAMES")
                return True
            else:
                print("❌ Failed with names")
                return False

async def test_with_destination_param():
    """Try using 'destination' as the parameter name."""
    
    print("\n🔧 Testing with 'destination' Parameter")
    print("=" * 60)
    
    system_prompt = """Route contractor licensing calls.

"overwhelmed" → transfer to CLP-Veteran-Support
"new" → transfer to CLP-Newcomer-Guide
"urgent" → transfer to CLP-Fast-Track
"business" → transfer to CLP-Network-Expert

Use transferCall function."""
    
    update_payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ],
            "temperature": 0.1
        },
        "functions": [
            {
                "name": "transferCall",
                "description": "Transfer the call",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination": {
                            "type": "string",
                            "description": "Assistant to transfer to"
                        }
                    },
                    "required": ["destination"]
                }
            }
        ],
        "endCallFunctionEnabled": False
    }
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            json=update_payload,
            headers=headers
        ) as response:
            if response.status == 200:
                print("✅ Configured with 'destination' parameter")
                return True
            else:
                print("❌ Failed with destination")
                return False

async def check_squad_transfer_config():
    """Check if the squad has special transfer configuration."""
    
    print("\n🔍 Checking Squad Transfer Configuration")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    squad_id = config.get("squad_id", "ca86111f-582f-4ba0-840f-e7a82dc0967d")
    
    async with aiohttp.ClientSession() as session:
        # Get squad details
        async with session.get(
            f"https://api.vapi.ai/squad/{squad_id}",
            headers=headers
        ) as response:
            if response.status == 200:
                squad_data = await response.json()
                
                print("Squad Configuration:")
                print(f"  - Squad ID: {squad_data.get('id')}")
                print(f"  - Members: {len(squad_data.get('members', []))}")
                
                # Check if members have transfer destinations defined
                members = squad_data.get("members", [])
                for member in members:
                    assistant_id = member.get("assistantId")
                    destinations = member.get("transferDestinations", [])
                    print(f"  - Assistant {assistant_id[:8]}...: {len(destinations)} destinations")
                
                return squad_data
            else:
                print("❌ Could not retrieve squad configuration")
                return None

async def main():
    """Test different transfer configurations."""
    
    print("🧪 Testing Different Transfer Methods")
    print("=" * 70)
    
    # Test 1: Assistant names
    names_work = await test_with_assistant_names()
    
    # Small delay
    await asyncio.sleep(1)
    
    # Test 2: Destination parameter
    destination_works = await test_with_destination_param()
    
    # Test 3: Check squad config
    squad_config = await check_squad_transfer_config()
    
    print("\n" + "=" * 70)
    print("📊 Test Results:")
    print(f"  - Assistant Names: {'✅ Works' if names_work else '❌ Failed'}")
    print(f"  - Destination Param: {'✅ Works' if destination_works else '❌ Failed'}")
    print(f"  - Squad Config: {'✅ Retrieved' if squad_config else '❌ Failed'}")
    
    print("\n🎯 Recommendation:")
    if names_work:
        print("Use assistant NAMES (not IDs) for transfers")
        print("Test by saying 'I am overwhelmed'")
    elif destination_works:
        print("Use 'destination' parameter for transfers")
    else:
        print("Transfers may need to be configured at squad level")
        print("Consider using VAPI Dashboard to configure transfers")

if __name__ == "__main__":
    asyncio.run(main())
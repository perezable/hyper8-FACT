#!/usr/bin/env python3
"""
Fix squad configuration for true silent transfers.
According to VAPI docs: Set message to empty string in assistantDestinations.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "c49631b4-2f8f-40b3-9ce1-22f731879fb9")

# Load configuration
with open("silent_transfer_squad_config.json", "r") as f:
    config = json.load(f)
    SQUAD_ID = config.get("squad_id", "ca86111f-582f-4ba0-840f-e7a82dc0967d")
    ASSISTANT_IDS = config["assistant_ids"]

async def fix_squad_silent_transfers():
    """Configure squad members for silent transfers."""
    
    print("🔧 Fixing Squad for Silent Transfers")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Build squad member configuration with silent transfer destinations
    members = []
    
    # Main Router - can transfer to all specialists
    members.append({
        "assistantId": ASSISTANT_IDS["CLP-Main-Router"],
        "assistantDestinations": [
            {
                "type": "assistant",
                "assistantName": "CLP-Veteran-Support",
                "message": "",  # Empty for silent transfer
                "description": "Transfer to veteran support specialist"
            },
            {
                "type": "assistant",
                "assistantName": "CLP-Newcomer-Guide",
                "message": "",  # Empty for silent transfer
                "description": "Transfer to newcomer guide"
            },
            {
                "type": "assistant",
                "assistantName": "CLP-Fast-Track",
                "message": "",  # Empty for silent transfer
                "description": "Transfer to fast track specialist"
            },
            {
                "type": "assistant",
                "assistantName": "CLP-Network-Expert",
                "message": "",  # Empty for silent transfer
                "description": "Transfer to network expert"
            }
        ]
    })
    
    # Add specialists (they can transfer back to router if needed)
    for name, assistant_id in ASSISTANT_IDS.items():
        if name != "CLP-Main-Router":
            members.append({
                "assistantId": assistant_id,
                "assistantDestinations": [
                    {
                        "type": "assistant",
                        "assistantName": "CLP-Main-Router",
                        "message": "",  # Empty for silent transfer back
                        "description": "Transfer back to main router"
                    }
                ]
            })
    
    # Update squad configuration
    squad_update = {
        "name": "CLP-Squad-Silent-Transfer",
        "members": members
    }
    
    async with aiohttp.ClientSession() as session:
        # Update the squad
        async with session.patch(
            f"https://api.vapi.ai/squad/{SQUAD_ID}",
            json=squad_update,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Squad updated with silent transfer configuration!")
                
                # Verify the configuration
                print("\n📋 Squad Configuration:")
                print(f"   - Squad ID: {data.get('id')}")
                print(f"   - Members: {len(data.get('members', []))}")
                
                # Check transfer destinations
                for member in data.get("members", []):
                    assistant_id = member.get("assistantId")
                    destinations = member.get("assistantDestinations", [])
                    print(f"\n   Assistant {assistant_id[:8]}...:")
                    for dest in destinations:
                        msg = dest.get("message", "NOT SET")
                        name = dest.get("assistantName", "Unknown")
                        silent = "✅ Silent" if msg == "" else "❌ Announces"
                        print(f"     → {name}: {silent}")
                
                return True
            else:
                error = await response.text()
                print(f"❌ Failed to update squad: {error}")
                
                # Try to parse error
                try:
                    error_data = json.loads(error)
                    if "message" in error_data:
                        print(f"\nError details: {error_data['message']}")
                except:
                    pass
                
                return False

async def update_router_for_squad_transfers():
    """Update router to use proper squad transfer syntax."""
    
    print("\n🔧 Updating Router for Squad Transfers")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Simple prompt that uses assistant names
    system_prompt = """You route contractor licensing calls.

When someone says "overwhelmed": Use transferCall with "CLP-Veteran-Support"
When someone says "new": Use transferCall with "CLP-Newcomer-Guide"
When someone says "urgent": Use transferCall with "CLP-Fast-Track"
When someone says "business": Use transferCall with "CLP-Network-Expert"

Just use the function. Don't announce anything."""
    
    router_update = {
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
        "endCallFunctionEnabled": False,
        "firstMessage": "Hello! How can I help with contractor licensing?",
        "firstMessageMode": "assistant-speaks-first"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            f"https://api.vapi.ai/assistant/{ASSISTANT_IDS['CLP-Main-Router']}",
            json=router_update,
            headers=headers
        ) as response:
            if response.status == 200:
                print("✅ Router updated for squad transfers")
                return True
            else:
                print("❌ Failed to update router")
                return False

async def main():
    """Main execution."""
    
    # Fix squad configuration
    squad_success = await fix_squad_silent_transfers()
    
    if squad_success:
        # Update router
        router_success = await update_router_for_squad_transfers()
        
        print("\n" + "=" * 60)
        print("🎯 Silent Transfer Configuration Complete!")
        print("\n📞 Test Instructions:")
        print("1. Call the Main Router")
        print("2. Say 'I am overwhelmed'")
        print("3. Should silently transfer to CLP-Veteran-Support")
        print("4. NO announcement should be made")
        print("\n✨ The key was setting message: '' in assistantDestinations!")
    else:
        print("\n⚠️ Squad update failed. Check error above.")

if __name__ == "__main__":
    asyncio.run(main())
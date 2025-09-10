#!/usr/bin/env python3
"""
Fix the transferCall function to use VAPI's correct format.
VAPI requires a specific structure for the built-in transferCall function.
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

# Corrected system prompt to use assistant IDs
SYSTEM_PROMPT = f"""You are the main contractor licensing assistant responsible for routing callers to the right specialist.

CRITICAL: Use the transferCall function to route callers. The function will handle the actual transfer.

ROUTING DECISIONS:
- If caller sounds overwhelmed, stressed, mentions "too much" → Transfer to Veteran Support
- If caller is new, confused, beginner → Transfer to Newcomer Guide  
- If caller needs something quickly, urgently, has deadline → Transfer to Fast Track
- If caller asks about business, money, income → Transfer to Network Expert

When you identify the need, immediately call the transferCall function with the appropriate assistantId.

IMPORTANT: Do not announce the transfer. Just execute the function and let it handle the transfer."""

async def fix_transfer_function():
    """Fix the transfer function configuration."""
    
    print("🔧 Fixing Transfer Function Configuration")
    print("=" * 60)
    
    # Remove the incorrect transferCall and let VAPI use its built-in
    # The key is to update the prompt to use assistant IDs directly
    update_payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ],
            "functions": [
                {
                    "name": "transferCall",
                    "description": "Transfer the call to another assistant",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "assistantId": {
                                "type": "string",
                                "description": "The assistant ID to transfer to",
                                "enum": [
                                    ASSISTANT_IDS["CLP-Veteran-Support"],
                                    ASSISTANT_IDS["CLP-Newcomer-Guide"],
                                    ASSISTANT_IDS["CLP-Fast-Track"],
                                    ASSISTANT_IDS["CLP-Network-Expert"]
                                ]
                            },
                            "message": {
                                "type": "string",
                                "description": "Optional message to pass to the next assistant"
                            }
                        },
                        "required": ["assistantId"]
                    }
                }
            ]
        },
        "endCallFunctionEnabled": False,
        "firstMessage": "",
        "firstMessageMode": "assistant-speaks-first-with-model-generated-message"
    }
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # First, get current configuration
        async with session.get(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            headers=headers
        ) as get_response:
            if get_response.status == 200:
                current_config = await get_response.json()
                
                # Keep existing functions except transferCall
                existing_functions = [
                    f for f in current_config.get("functions", [])
                    if f["name"] != "transferCall"
                ]
                
                # Add the correct transferCall function
                functions = existing_functions + [update_payload["model"]["functions"][0]]
                
                # Update with corrected configuration
                final_payload = {
                    "model": {
                        "provider": "openai",
                        "model": "gpt-4",
                        "messages": update_payload["model"]["messages"]
                    },
                    "functions": functions,
                    "endCallFunctionEnabled": False,
                    "firstMessage": "",
                    "firstMessageMode": "assistant-speaks-first-with-model-generated-message"
                }
                
                # Update the assistant
                async with session.patch(
                    f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
                    json=final_payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Transfer function updated successfully!")
                        
                        # Show the assistant ID mappings
                        print("\n📋 Assistant ID Mappings:")
                        print(f"   Veteran Support: {ASSISTANT_IDS['CLP-Veteran-Support']}")
                        print(f"   Newcomer Guide: {ASSISTANT_IDS['CLP-Newcomer-Guide']}")
                        print(f"   Fast Track: {ASSISTANT_IDS['CLP-Fast-Track']}")
                        print(f"   Network Expert: {ASSISTANT_IDS['CLP-Network-Expert']}")
                        
                        # Verify the function
                        transfer_func = next(
                            (f for f in data.get("functions", []) if f["name"] == "transferCall"),
                            None
                        )
                        
                        if transfer_func:
                            print("\n✅ Transfer Function Configured:")
                            print(f"   - Has assistantId parameter: {'assistantId' in transfer_func.get('parameters', {}).get('properties', {})}")
                            print(f"   - Assistant IDs in enum: {len(transfer_func.get('parameters', {}).get('properties', {}).get('assistantId', {}).get('enum', [])) == 4}")
                            
                        print("\n📞 Test Instructions:")
                        print("1. Start a new test call")
                        print("2. Say 'I'm feeling overwhelmed'")
                        print("3. Router should now SILENTLY transfer (no announcement)")
                        print("4. Veteran Support should take over the conversation")
                        
                        return True
                    else:
                        error = await response.text()
                        print(f"❌ Failed to update: {error}")
                        return False

async def main():
    """Main execution."""
    success = await fix_transfer_function()
    
    if not success:
        print("\n⚠️ Update failed. Please check the error above.")
    else:
        print("\n" + "=" * 60)
        print("🎯 The transfer function is now properly configured!")
        print("Test the call again - transfers should work silently.")

if __name__ == "__main__":
    asyncio.run(main())
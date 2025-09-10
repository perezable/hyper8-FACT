#!/usr/bin/env python3
"""
Fix the Main Router to properly CALL functions instead of speaking them.
The router needs to understand it should use the transferCall FUNCTION, not say the words.
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

# System prompt that emphasizes FUNCTION CALLING, not speaking
SYSTEM_PROMPT = """You are a contractor licensing routing assistant. You help callers by connecting them to the right specialist.

CRITICAL: You have a transferCall FUNCTION that you must USE (not speak about) to transfer calls.

ROUTING RULES - When you hear these keywords, USE the transferCall function:

1. Keywords: "overwhelmed", "stressed", "too much", "complicated"
   ACTION: Use transferCall function with assistantId: "82efc90b-60f8-4fdd-b757-f089a8704123"

2. Keywords: "new", "beginner", "confused", "don't understand"
   ACTION: Use transferCall function with assistantId: "85ee06a0-b4fb-455a-8ef6-be1b169c57c7"

3. Keywords: "quickly", "urgent", "ASAP", "deadline", "rush"
   ACTION: Use transferCall function with assistantId: "2a340cc3-474e-4d2c-92d0-6590a7a22e80"

4. Keywords: "business", "money", "income", "opportunity"
   ACTION: Use transferCall function with assistantId: "d3ad7b67-93c4-4641-8c1f-130c4d1a284c"

IMPORTANT:
- DO NOT speak about transferring or mention assistant IDs
- DO NOT say "execute transfer" or read out IDs
- Simply USE the transferCall function when you detect keywords
- The function will handle the actual transfer silently

If unclear about caller's needs, ask ONE clarifying question."""

async def fix_function_calling():
    """Fix the router to use functions properly."""
    
    print("🔧 Fixing Router Function Calling Behavior")
    print("=" * 60)
    
    # Properly structured transferCall function for VAPI
    transfer_function = {
        "name": "transferCall",
        "description": "Transfer the call to another assistant",
        "parameters": {
            "type": "object",
            "properties": {
                "assistantId": {
                    "type": "string",
                    "description": "The ID of the assistant to transfer to"
                }
            },
            "required": ["assistantId"]
        }
    }
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # First get current configuration
        async with session.get(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            headers=headers
        ) as get_response:
            if get_response.status == 200:
                current_config = await get_response.json()
                
                # Keep knowledge functions
                knowledge_functions = [
                    f for f in current_config.get("functions", [])
                    if f["name"] in ["searchKnowledge", "getStateRequirements"]
                ]
                
                # Build complete function list
                all_functions = knowledge_functions + [transfer_function]
                
                # Update configuration
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
                        "temperature": 0.5,  # Lower temperature for more consistent behavior
                        "maxTokens": 150  # Limit response length
                    },
                    "functions": all_functions,
                    "endCallFunctionEnabled": False,
                    "firstMessage": "Hello! I can help you with contractor licensing. What brings you here today?",
                    "firstMessageMode": "assistant-speaks-first",
                    "transcriber": {
                        "provider": "deepgram",
                        "model": "nova-2",
                        "language": "en"
                    }
                }
                
                # Apply the update
                async with session.patch(
                    f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
                    json=update_payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Function calling behavior fixed!")
                        
                        print("\n📋 Configuration Applied:")
                        print("   - Clear instructions to USE functions, not speak them")
                        print("   - Lower temperature for consistent behavior")
                        print("   - Proper transferCall function structure")
                        print("   - Assistant IDs hardcoded in prompt")
                        
                        print("\n🎯 Expected Behavior:")
                        print("   Caller: 'I'm feeling overwhelmed'")
                        print("   Router: [Uses transferCall function silently]")
                        print("   Result: Call transfers to Veteran Support")
                        print("   NOT: 'Execute transfer call to assistant...'")
                        
                        print("\n📞 Test Now:")
                        print("1. Start a new test call")
                        print("2. Say 'I'm overwhelmed with this process'")
                        print("3. Router should silently transfer (no spoken IDs)")
                        print("4. Veteran Support takes over the conversation")
                        
                        # Save the configuration for reference
                        with open("router_config_fixed.json", "w") as f:
                            json.dump({
                                "timestamp": datetime.now().isoformat(),
                                "router_id": MAIN_ROUTER_ID,
                                "status": "function_calling_fixed",
                                "assistant_mappings": {
                                    "overwhelmed": ASSISTANT_IDS["CLP-Veteran-Support"],
                                    "new": ASSISTANT_IDS["CLP-Newcomer-Guide"],
                                    "urgent": ASSISTANT_IDS["CLP-Fast-Track"],
                                    "business": ASSISTANT_IDS["CLP-Network-Expert"]
                                }
                            }, f, indent=2)
                        
                        return True
                    else:
                        error = await response.text()
                        print(f"❌ Failed to update: {error}")
                        return False
            else:
                print("❌ Failed to get current configuration")
                return False

async def main():
    """Main execution."""
    success = await fix_function_calling()
    
    if success:
        print("\n" + "=" * 60)
        print("🚀 Router should now properly use functions!")
        print("No more speaking out assistant IDs!")
    else:
        print("\n⚠️ Update failed. Check the error above.")

if __name__ == "__main__":
    asyncio.run(main())
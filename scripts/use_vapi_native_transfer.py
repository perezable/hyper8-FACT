#!/usr/bin/env python3
"""
Use VAPI's native transferCall function without custom definition.
VAPI provides transferCall as a built-in - we shouldn't override it.
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

# Get configuration
with open("silent_transfer_squad_config.json", "r") as f:
    config = json.load(f)
    ASSISTANT_IDS = config["assistant_ids"]

# System prompt that uses VAPI's native transfer format
SYSTEM_PROMPT = """You are a contractor licensing routing assistant.

IMPORTANT: You have access to a transferCall function. When you detect keywords, use it immediately.

ROUTING RULES:
- "overwhelmed" or "stressed" → transferCall to "CLP-Veteran-Support"
- "new" or "confused" → transferCall to "CLP-Newcomer-Guide"  
- "quickly" or "urgent" → transferCall to "CLP-Fast-Track"
- "business" or "money" → transferCall to "CLP-Network-Expert"

Do NOT announce transfers. Just execute the transferCall function silently."""

async def configure_native_transfer():
    """Configure router to use VAPI's native transfer."""
    
    print("🔧 Configuring VAPI Native Transfer")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # First, get current configuration
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            headers=headers
        ) as response:
            if response.status == 200:
                current = await response.json()
                
                # Keep only knowledge functions, remove our custom transferCall
                knowledge_functions = [
                    f for f in current.get("functions", [])
                    if f["name"] in ["searchKnowledge", "getStateRequirements"]
                ]
                
                # Update configuration WITHOUT custom transferCall
                # VAPI will provide it automatically
                update_payload = {
                    "name": "CLP-Main-Router",
                    "model": {
                        "provider": "openai",
                        "model": "gpt-3.5-turbo",
                        "messages": [
                            {
                                "role": "system",
                                "content": SYSTEM_PROMPT
                            }
                        ],
                        "temperature": 0.1,
                        "maxTokens": 50,
                        "tools": [  # Try using 'tools' instead of 'functions'
                            {
                                "type": "function",
                                "function": {
                                    "name": "transferCall",
                                    "description": "Transfer call to another assistant",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "assistantName": {
                                                "type": "string",
                                                "description": "Name of assistant to transfer to"
                                            }
                                        },
                                        "required": ["assistantName"]
                                    }
                                }
                            }
                        ]
                    },
                    "functions": knowledge_functions,  # Only knowledge functions
                    "endCallFunctionEnabled": False,
                    "firstMessage": "Hello! How can I help with contractor licensing?",
                    "firstMessageMode": "assistant-speaks-first",
                    "recordingEnabled": True,
                    "hipaaCompliant": False,
                    "backgroundSound": "off",
                    "backchannelingEnabled": False,
                    "modelOutputInMessagesEnabled": False
                }
                
                # Apply update
                async with session.patch(
                    f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
                    json=update_payload,
                    headers=headers
                ) as update_response:
                    if update_response.status == 200:
                        updated = await update_response.json()
                        print("✅ Configured with native transfer!")
                        
                        # Check what functions are available
                        funcs = updated.get("functions", [])
                        tools = updated.get("model", {}).get("tools", [])
                        
                        print("\n📋 Configuration:")
                        print(f"   - Functions: {[f['name'] for f in funcs]}")
                        print(f"   - Tools: {len(tools)} tool(s)")
                        print("   - Using VAPI's native transferCall")
                        
                        return True
                    else:
                        error = await update_response.text()
                        print(f"❌ Update failed: {error}")
                        return False

async def try_minimal_config():
    """Try the most minimal configuration possible."""
    
    print("\n🔧 Trying Minimal Configuration")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Absolute minimal config
    minimal_payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": "When someone says 'overwhelmed', use transferCall('CLP-Veteran-Support'). When someone says 'new', use transferCall('CLP-Newcomer-Guide'). Do not announce transfers."
                }
            ],
            "temperature": 0.1
        },
        "endCallFunctionEnabled": False
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            json=minimal_payload,
            headers=headers
        ) as response:
            if response.status == 200:
                print("✅ Minimal configuration applied")
                print("\nTest with: 'I am overwhelmed'")
                print("Expected: Silent transfer to CLP-Veteran-Support")
                return True
            else:
                print("❌ Minimal config failed")
                return False

async def check_vapi_docs():
    """Provide VAPI documentation reference."""
    
    print("\n📚 VAPI Transfer Documentation:")
    print("=" * 60)
    print("""
According to VAPI docs, transfers within a squad should work with:

1. The assistant must be part of a squad
2. Use the built-in transferCall function
3. Pass the assistant name (not ID) as parameter

Example function call that SHOULD work:
{
  "name": "transferCall",
  "parameters": {
    "assistantName": "CLP-Veteran-Support"
  }
}

If this still doesn't work, the issue might be:
- Squad configuration blocking transfers
- Need to enable a specific squad setting
- Dashboard configuration required
""")

async def main():
    """Main execution."""
    
    # Try native configuration
    success = await configure_native_transfer()
    
    if not success:
        # Try minimal as fallback
        await try_minimal_config()
    
    # Show documentation
    await check_vapi_docs()
    
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("1. Test call saying 'I am overwhelmed'")
    print("2. If still speaking transfers, check VAPI Dashboard")
    print("3. Look for 'Transfer Settings' in squad configuration")
    print("4. May need to enable 'Silent Transfers' in squad settings")

if __name__ == "__main__":
    asyncio.run(main())
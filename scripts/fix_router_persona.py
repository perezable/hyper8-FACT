#!/usr/bin/env python3
"""
Fix the Main Router to understand it's talking TO callers, not about them.
The router needs to recognize it's in a live conversation with the caller.
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

# Fixed system prompt - Router IS talking TO the caller
SYSTEM_PROMPT = f"""You are speaking directly with someone who needs help with contractor licensing. Listen to what they say and route them to the right specialist.

YOUR ROLE: You are the first point of contact. The person speaking to you IS the caller who needs help.

LISTEN FOR THESE KEYWORDS AND TRANSFER IMMEDIATELY:

1. If they say: "overwhelmed", "stressed", "too much", "complicated", "difficult"
   → IMMEDIATELY transferCall to assistantId: {ASSISTANT_IDS['CLP-Veteran-Support']}

2. If they say: "new", "beginner", "confused", "don't understand", "what is"
   → IMMEDIATELY transferCall to assistantId: {ASSISTANT_IDS['CLP-Newcomer-Guide']}

3. If they say: "quickly", "urgent", "ASAP", "deadline", "rush", "hurry"
   → IMMEDIATELY transferCall to assistantId: {ASSISTANT_IDS['CLP-Fast-Track']}

4. If they say: "business", "money", "income", "opportunity", "earn"
   → IMMEDIATELY transferCall to assistantId: {ASSISTANT_IDS['CLP-Network-Expert']}

IMPORTANT RULES:
- You are talking TO the caller, not about them
- When you hear trigger words, execute transferCall immediately
- Do NOT announce the transfer
- Do NOT ask for clarification if keywords are clear
- If no keywords match, ask ONE question to understand their main need

Example interactions:
Caller: "I'm feeling overwhelmed with all this"
You: [Execute transferCall to Veteran Support - no response needed]

Caller: "I need my license quickly"  
You: [Execute transferCall to Fast Track - no response needed]"""

async def fix_router_persona():
    """Fix the router to understand it's in conversation with callers."""
    
    print("🔧 Fixing Router Persona Understanding")
    print("=" * 60)
    
    update_payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                }
            ]
        },
        "endCallFunctionEnabled": False,
        "firstMessage": "Hello! I can help you with contractor licensing. What brings you here today?",
        "firstMessageMode": "assistant-speaks-first"
    }
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Update the assistant
        async with session.patch(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            json=update_payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Router persona updated successfully!")
                
                print("\n📋 Configuration Updated:")
                print("   - Router now understands it's talking TO callers")
                print("   - Clear keyword triggers with assistant IDs")
                print("   - Friendly opening message to start conversation")
                print("   - Immediate transfer on keyword detection")
                
                print("\n🔑 Keyword Triggers:")
                print("   'overwhelmed/stressed' → Veteran Support")
                print("   'new/confused' → Newcomer Guide")
                print("   'quickly/urgent' → Fast Track")
                print("   'business/money' → Network Expert")
                
                print("\n📞 Test Instructions:")
                print("1. Start a new test call")
                print("2. Router will greet you: 'Hello! I can help...'")
                print("3. Say 'I'm feeling overwhelmed'")
                print("4. Router should immediately transfer (no more confusion)")
                
                return True
            else:
                error = await response.text()
                print(f"❌ Failed to update: {error}")
                return False

async def verify_configuration():
    """Verify the router configuration is correct."""
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                print("\n✅ Verification Complete:")
                
                # Check prompt
                prompt = data.get("model", {}).get("messages", [{}])[0].get("content", "")
                if "You are speaking directly with someone" in prompt:
                    print("   ✓ Prompt correctly addresses caller")
                else:
                    print("   ✗ Prompt may still be confused")
                
                # Check transfer function
                transfer_func = next(
                    (f for f in data.get("functions", []) if f["name"] == "transferCall"),
                    None
                )
                if transfer_func:
                    has_ids = any(
                        ASSISTANT_IDS["CLP-Veteran-Support"] in str(transfer_func)
                    )
                    print(f"   ✓ Transfer function configured with IDs: {has_ids}")
                
                # Check first message
                first_msg = data.get("firstMessage", "")
                if first_msg:
                    print(f"   ✓ Has greeting: '{first_msg[:50]}...'")
                
                return True

async def main():
    """Main execution."""
    success = await fix_router_persona()
    
    if success:
        await verify_configuration()
        print("\n" + "=" * 60)
        print("🎯 Router is now properly configured!")
        print("It will recognize YOU as the caller and route based on your keywords.")
    else:
        print("\n⚠️ Update failed. Please check the error above.")

if __name__ == "__main__":
    asyncio.run(main())
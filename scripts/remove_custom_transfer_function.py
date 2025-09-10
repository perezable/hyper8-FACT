#!/usr/bin/env python3
"""
Remove the custom transferCall function entirely.
VAPI should provide transferCall as a built-in when in a squad.
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "c49631b4-2f8f-40b3-9ce1-22f731879fb9")
MAIN_ROUTER_ID = "686ead20-ceb5-45b3-a224-4ddb62f58bda"

async def remove_transfer_function():
    """Remove custom transferCall - let VAPI provide it."""
    
    print("🔧 REMOVING CUSTOM TRANSFER FUNCTION")
    print("=" * 70)
    print("Theory: VAPI provides transferCall automatically in squads.")
    print("Our custom definition might be overriding the built-in.")
    print("-" * 70)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # System prompt that references the built-in transferCall
    system_prompt = """You are a contractor licensing router in a squad.

IMPORTANT: You have a built-in transferCall function available.

When the caller says "overwhelmed" or "stressed":
Execute: transferCall("CLP-Veteran-Support")

When the caller says "new" or "confused":
Execute: transferCall("CLP-Newcomer-Guide")

When the caller says "urgent" or "quickly":
Execute: transferCall("CLP-Fast-Track")

When the caller says "business" or "money":
Execute: transferCall("CLP-Network-Expert")

Do NOT speak about transferring. Use the function."""
    
    update_payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",  # Simpler model
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ],
            "temperature": 0.1
        },
        "functions": [],  # EMPTY - no custom functions
        "endCallFunctionEnabled": False,
        "firstMessage": "Hello! How can I help with contractor licensing?",
        "firstMessageMode": "assistant-speaks-first"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.patch(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            json=update_payload,
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                print("✅ Custom transferCall function REMOVED")
                print("\nNew configuration:")
                print(f"  - Functions: {len(data.get('functions', []))} custom functions")
                print(f"  - Model: {data.get('model', {}).get('model')}")
                print(f"  - Prompt references built-in transferCall")
                
                print("\n📞 TEST NOW:")
                print("1. Call the Main Router")
                print("2. Say 'I am overwhelmed'")
                print("3. If VAPI provides transferCall in squads, it should work")
                print("4. If not, we know the issue is with VAPI's system")
                
                return True
            else:
                error = await response.text()
                print(f"❌ Failed: {error}")
                return False

async def check_vapi_documentation_link():
    """Provide link to check VAPI documentation."""
    
    print("\n" + "=" * 70)
    print("📚 VAPI DOCUMENTATION CHECK")
    print("-" * 70)
    print("""
Based on the actual configuration, here's what we know:

1. ✅ Squad is configured with assistantDestinations
2. ✅ Messages are empty (for silent transfers)
3. ✅ Router understands the intent (speaks "transfer call")
4. ❌ Transfer isn't executing

This indicates either:
A) VAPI's transferCall needs to be configured differently
B) There's an undocumented requirement for squad transfers
C) The feature might not work as documented

NEXT STEPS:
1. Test without custom transferCall function
2. If still not working, contact VAPI support at:
   - Discord: https://discord.gg/vapi
   - Email: support@vapi.ai
   
Show them:
- Squad ID: ca86111f-582f-4ba0-840f-e7a82dc0967d
- Router ID: 686ead20-ceb5-45b3-a224-4ddb62f58bda
- Issue: Assistant speaks transfer instead of executing
""")

async def main():
    """Main execution."""
    
    success = await remove_transfer_function()
    
    if success:
        await check_vapi_documentation_link()
    
    print("\n" + "=" * 70)
    print("🎯 FINAL ATTEMPT")
    print("Custom function removed. Test if VAPI's built-in works.")
    print("If not, this is a VAPI platform issue requiring support.")

if __name__ == "__main__":
    asyncio.run(main())
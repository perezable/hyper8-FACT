#!/usr/bin/env python3
"""
Fix Main Router configuration to prevent premature call endings.
Disables endCallFunction and updates prompt for better transfer handling.
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

# Updated system prompt with clearer instructions
UPDATED_SYSTEM_PROMPT = """You are the main contractor licensing assistant responsible for routing callers to the right specialist.

CRITICAL TRANSFER INSTRUCTIONS:
1. NEVER end the call - always transfer to a specialist
2. Listen for keywords to identify caller needs
3. Execute transferCall IMMEDIATELY when you detect a matching persona
4. Do NOT announce transfers - just execute them silently

ROUTING TRIGGERS:
- Keywords: "overwhelmed", "stressed", "too much", "complicated" → transferCall("CLP-Veteran-Support")
- Keywords: "new", "beginner", "don't understand", "confused" → transferCall("CLP-Newcomer-Guide")  
- Keywords: "quickly", "urgent", "ASAP", "deadline", "rush" → transferCall("CLP-Fast-Track")
- Keywords: "business", "money", "income", "opportunity" → transferCall("CLP-Network-Expert")

DEFAULT ACTION:
If unclear, ask ONE clarifying question to determine their primary need, then transfer immediately.

NEVER say goodbye or end the call yourself."""

async def fix_router():
    """Fix the Main Router configuration."""
    
    print("🔧 Fixing Main Router Configuration")
    print("=" * 60)
    
    # Update configuration
    update_payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": UPDATED_SYSTEM_PROMPT
                }
            ]
        },
        "endCallFunctionEnabled": False,  # CRITICAL: Disable end call
        "endCallMessage": "",  # Remove any end call message
        "recordingEnabled": True,
        "firstMessage": "",  # Keep empty for silent approach
        "firstMessageMode": "assistant-speaks-first-with-model-generated-message"
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
                print("✅ Main Router updated successfully!")
                print(f"   - End Call Disabled: {not data.get('endCallFunctionEnabled', True)}")
                print(f"   - Assistant ID: {data.get('id')}")
                
                # Verify the update
                print("\n📋 Verifying Configuration:")
                async with session.get(
                    f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
                    headers=headers
                ) as verify_response:
                    if verify_response.status == 200:
                        verify_data = await verify_response.json()
                        print(f"   - End Call Function: {'❌ DISABLED' if not verify_data.get('endCallFunctionEnabled') else '⚠️ STILL ENABLED'}")
                        print(f"   - Transfer Function: {'✅ Available' if any(f['name'] == 'transferCall' for f in verify_data.get('functions', [])) else '❌ Missing'}")
                        print(f"   - First Message: {'✅ Empty (Silent)' if not verify_data.get('firstMessage') else '⚠️ Has greeting'}")
                        
                        # Show routing keywords from prompt
                        prompt_content = verify_data.get('model', {}).get('messages', [{}])[0].get('content', '')
                        if 'overwhelmed' in prompt_content.lower():
                            print("   - Routing Logic: ✅ Updated with keywords")
                        else:
                            print("   - Routing Logic: ⚠️ May need verification")
                        
                        print("\n✅ Configuration Fixed!")
                        print("\n📞 Test Instructions:")
                        print("1. Start a new test call to the Main Router")
                        print("2. Say 'I'm feeling overwhelmed with all this'")
                        print("3. Should transfer to Veteran Support WITHOUT ending call")
                        print("4. Veteran Support should continue the conversation")
                        
                        return True
            else:
                error = await response.text()
                print(f"❌ Failed to update: {error}")
                return False

async def main():
    """Main execution."""
    success = await fix_router()
    
    if success:
        print("\n" + "=" * 60)
        print("🎯 Next Steps:")
        print("1. Test the call again with 'I'm overwhelmed'")
        print("2. Router should now transfer instead of ending")
        print("3. If still issues, check VAPI Dashboard logs")
    else:
        print("\n⚠️ Fix failed. Please check the error above.")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Update VAPI Assistants with Enhanced Routing Instructions

Since VAPI doesn't support automatic routing, we'll update each assistant's system prompt
to include instructions on when to recommend transfers to other specialists.
"""

import os
import json
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_BASE_URL = "https://api.vapi.ai"

# Assistant IDs from our squad
ASSISTANT_IDS = {
    "overwhelmed_veteran": "8caf929b-ada3-476b-8523-f80ef6855b10",
    "confused_newcomer": "d87e82ce-bd5e-43b3-a992-c3790a214773", 
    "urgent_operator": "075cdd38-01e6-4adb-967c-8c6073a53af9",
    "qualifier_network_specialist": "6ee8dc58-6b82-4885-ad3c-dcfdc4b30e9b"
}

# Enhanced routing instructions for each assistant
ROUTING_INSTRUCTIONS = {
    "overwhelmed_veteran": """

🔄 ROUTING INTELLIGENCE:
If the caller shows signs of these patterns, recommend a specialist transfer:

• URGENT/TIME-SENSITIVE: "quickly", "fast", "ASAP", "deadline" → "It sounds like you're working with a tight deadline. Let me connect you with our fast-track specialist who can help you get licensed as quickly as possible."

• BUSINESS OPPORTUNITY FOCUS: "make money", "business opportunity", "passive income", "network" → "I'm hearing that you're interested in the business side of licensing. Let me connect you with our specialist who focuses on the qualifier network and income opportunities."

• EXTREMELY CONFUSED/NEW: Multiple "what does X mean", "I don't understand basic terms" → "It sounds like you're new to this process. Let me connect you with our guide who specializes in helping newcomers understand everything from the ground up."

Use detectPersona function regularly to check for routing opportunities and calculateTrust to gauge when transfers would be helpful vs. disruptive.""",
    
    "confused_newcomer": """

🔄 ROUTING INTELLIGENCE:
If the caller shows signs of these patterns, recommend a specialist transfer:

• OVERWHELMING STRESS: "too much", "drowning", "can't handle", "overwhelmed" → "I can hear that this feels overwhelming. Let me connect you with our specialist who's excellent at breaking complex processes down into manageable steps."

• URGENT/TIME-SENSITIVE: "deadline", "quickly", "fast", "need this now" → "It sounds like you're working with a time constraint. Let me transfer you to our fast-track specialist who can help expedite your licensing process."

• BUSINESS/INCOME FOCUS: "make money", "opportunity", "business", "network", "qualifying others" → "I'm hearing interest in the business opportunities. Let me connect you with our network specialist who can show you the income potential."

Use detectPersona function to identify when the caller has moved beyond basic confusion and calculateTrust to ensure transfers happen at appropriate moments.""",
    
    "urgent_operator": """

🔄 ROUTING INTELLIGENCE:
If the caller shows signs of these patterns, recommend a specialist transfer:

• OVERWHELMING STRESS: "too much pressure", "can't handle the rush", "stressed about timeline" → "I understand the time pressure is creating stress. Let me connect you with our specialist who's excellent at managing overwhelming situations while still moving quickly."

• BASIC CONFUSION: Multiple basic questions, "what does X mean", "I don't understand" → "Since we're working quickly, let me connect you with our guide who can efficiently explain the basics without slowing down your timeline."

• BUSINESS OPPORTUNITY INTEREST: "make money while getting licensed", "business opportunity", "network" → "It sounds like you're interested in both the licensing and the business opportunity. Let me connect you with our network specialist."

Use detectPersona function to catch when speed isn't the primary need and calculateTrust to ensure quick transfers don't disrupt rapport.""",
    
    "qualifier_network_specialist": """

🔄 ROUTING INTELLIGENCE:
If the caller shows signs of these patterns, recommend a specialist transfer:

• OVERWHELMING STRESS: "too complicated", "don't understand the business side", "too much to learn" → "I can see this feels overwhelming. Let me connect you with our specialist who's excellent at breaking down complex information step-by-step."

• URGENT/TIME-SENSITIVE: "need to get licensed quickly first", "deadline for basic license" → "It sounds like you need to get your basic license quickly first. Let me connect you with our fast-track specialist to handle the immediate licensing, then we can discuss the network opportunity."

• BASIC CONFUSION: "I don't understand licensing at all", "completely new to this" → "Since you're new to contractor licensing, let me connect you with our newcomer guide who can explain the basics clearly."

Use detectPersona function to identify when business focus shifts to other needs and calculateTrust to determine if the caller is truly interested in the opportunity."""
}

async def update_assistant_prompt(session: aiohttp.ClientSession, 
                                 persona: str, assistant_id: str) -> bool:
    """Update an assistant's system prompt with routing instructions."""
    print(f"\n🔄 Updating {persona} routing instructions...")
    
    # First, get current assistant configuration
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get current configuration
        async with session.get(f"{VAPI_BASE_URL}/assistant/{assistant_id}",
                              headers=headers) as response:
            if response.status != 200:
                print(f"   ❌ Failed to get current config: {response.status}")
                return False
            
            current_config = await response.json()
            
        # Update system prompt with routing instructions
        current_prompt = current_config["model"]["systemPrompt"]
        updated_prompt = current_prompt + ROUTING_INSTRUCTIONS[persona]
        
        # Update configuration
        update_data = {
            "model": {
                **current_config["model"],
                "systemPrompt": updated_prompt
            }
        }
        
        async with session.patch(f"{VAPI_BASE_URL}/assistant/{assistant_id}",
                                json=update_data,
                                headers=headers) as response:
            if response.status == 200:
                print(f"   ✅ Updated successfully")
                return True
            else:
                error_text = await response.text()
                print(f"   ❌ Update failed: {response.status} - {error_text}")
                return False
                
    except Exception as e:
        print(f"   ❌ Error updating assistant: {e}")
        return False


async def main():
    """Update all assistants with routing intelligence."""
    if not VAPI_API_KEY:
        print("❌ VAPI_API_KEY not found in environment variables")
        return
    
    print("🔄 Adding Routing Intelligence to VAPI Squad")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        success_count = 0
        
        for persona, assistant_id in ASSISTANT_IDS.items():
            success = await update_assistant_prompt(session, persona, assistant_id)
            if success:
                success_count += 1
        
        print(f"\n📊 Routing Updates Complete")
        print(f"   Updated: {success_count}/{len(ASSISTANT_IDS)} assistants")
        
        if success_count == len(ASSISTANT_IDS):
            print("\n🎉 All assistants now have routing intelligence!")
            print("\n📋 How it works:")
            print("1. Each assistant can detect when caller needs a different specialist")
            print("2. They use detectPersona function to confirm routing recommendations")
            print("3. They provide appropriate transfer messages and instructions")
            print("4. Manual transfers can be executed through VAPI dashboard")
            
            print("\n🚀 Next Steps:")
            print("1. Test the routing intelligence with sample conversations")
            print("2. Monitor how often transfer recommendations occur")
            print("3. Train team on when to manually execute transfers")
        else:
            print("\n⚠️  Some updates failed. Check logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())
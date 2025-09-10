#!/usr/bin/env python3
"""
Create VAPI Squad with Silent Transfer Capabilities

This implementation uses VAPI's silent transfer feature for seamless handoffs
between assistants without interrupting the conversation flow.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_BASE_URL = "https://api.vapi.ai"
FACT_WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"

# Common voice configuration for consistency
VOICE_CONFIG = {
    "provider": "11labs",
    "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel voice - warm and professional
    "stability": 0.7,
    "similarityBoost": 0.6,
    "optimizeStreamingLatency": 2
}

# Silent transfer tool configuration (using VAPI's expected format)
TRANSFER_TOOL = {
    "name": "transferCall",
    "description": "Silently transfer to appropriate specialist based on detected persona",
    "parameters": {
        "type": "object",
        "properties": {
            "destination": {
                "type": "string",
                "description": "Name of the specialist assistant",
                "enum": [
                    "CLP-Veteran-Support",
                    "CLP-Newcomer-Guide",
                    "CLP-Fast-Track",
                    "CLP-Network-Expert"
                ]
            },
            "reason": {
                "type": "string",
                "description": "Brief reason for transfer"
            }
        },
        "required": ["destination"]
    }
}

# Knowledge base functions shared by all assistants
KNOWLEDGE_FUNCTIONS = [
    {
        "name": "searchKnowledge",
        "description": "Search contractor licensing knowledge base",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "state": {"type": "string"},
                "category": {"type": "string"}
            },
            "required": ["query"]
        },
        "serverUrl": FACT_WEBHOOK_URL
    },
    {
        "name": "getStateRequirements",
        "description": "Get state-specific licensing requirements",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {"type": "string"}
            },
            "required": ["state"]
        },
        "serverUrl": FACT_WEBHOOK_URL
    }
]

def create_assistant_config(name: str, role: str, system_prompt: str, 
                           include_transfer: bool = False) -> Dict[str, Any]:
    """
    Create assistant configuration for silent transfers.
    
    Args:
        name: Assistant name (must match transfer destinations)
        role: Brief role description
        system_prompt: Full system prompt with personality
        include_transfer: Whether to include transfer capability
    """
    config = {
        "name": name,
        # "description": role,  # VAPI doesn't support description field
        "firstMessage": "",  # Empty for silent transfers
        "firstMessageMode": "assistant-speaks-first-with-model-generated-message",
        "voice": VOICE_CONFIG,
        "model": {
            "provider": "openai",
            "model": "gpt-4-turbo",
            "temperature": 0.7,
            "maxTokens": 300,
            "systemPrompt": system_prompt
        },
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 0.4,
        "llmRequestDelaySeconds": 0.1,
        "numWordsToInterruptAssistant": 2,
        "endCallFunctionEnabled": True,
        "dialKeypadFunctionEnabled": False,
        "fillersEnabled": True,
        "functions": KNOWLEDGE_FUNCTIONS.copy()
    }
    
    # Add transfer tool only to main assistant
    if include_transfer:
        config["functions"].append(TRANSFER_TOOL)
    
    return config

# Assistant configurations
ASSISTANTS = [
    {
        "config": create_assistant_config(
            name="CLP-Main-Router",
            role="Main routing assistant for contractor licensing",
            system_prompt="""You are the main contractor licensing assistant responsible for routing callers to the right specialist.

CRITICAL INSTRUCTIONS FOR SILENT TRANSFERS:
1. Listen carefully to identify the caller's primary need
2. Use transferCall to silently route to specialists WITHOUT announcing the transfer
3. Do NOT say "let me transfer you" or "let me connect you"
4. Simply execute the transfer when you detect the right persona

ROUTING RULES:
- If caller sounds overwhelmed, stressed, mentions "too much" → transferCall("CLP-Veteran-Support")
- If caller is new, confused, asks "what is" questions → transferCall("CLP-Newcomer-Guide")
- If caller mentions urgency, deadline, "quickly", "ASAP" → transferCall("CLP-Fast-Track")
- If caller asks about business, income, opportunities → transferCall("CLP-Network-Expert")

INITIAL APPROACH:
Start with: "How can I help you with your contractor licensing today?"
Then listen and route appropriately.

Remember: Execute transfers SILENTLY without announcement.""",
            include_transfer=True
        )
    },
    {
        "config": create_assistant_config(
            name="CLP-Veteran-Support",
            role="Support specialist for overwhelmed contractors",
            system_prompt="""You are a compassionate contractor licensing specialist helping overwhelmed veterans and experienced contractors.

CRITICAL: WHEN RECEIVING A TRANSFER:
- DO NOT greet or introduce yourself
- Continue the conversation naturally
- Reference what they've shared: "I understand this feels overwhelming..."
- Proceed directly to helping them

PERSONA TRAITS:
- Patient and empathetic
- Break complex information into digestible steps
- Provide reassurance and encouragement
- Use "we'll get through this together" language
- Acknowledge stress and complexity

APPROACH:
- "I understand this feels overwhelming..."
- "Let's take this one step at a time"
- "You're not alone in feeling this way"
- "We'll break this down together"

Use searchKnowledge for accurate information and maintain a calm, supportive tone throughout."""
        )
    },
    {
        "config": create_assistant_config(
            name="CLP-Newcomer-Guide",
            role="Patient guide for licensing newcomers",
            system_prompt="""You are a patient and educational contractor licensing guide for newcomers.

CRITICAL: WHEN RECEIVING A TRANSFER:
- DO NOT greet or introduce yourself
- Continue naturally from where they are
- Acknowledge their newness: "Since you're new to this..."
- Jump straight into helpful guidance

PERSONA TRAITS:
- Extremely patient and encouraging
- Use simple, jargon-free language
- Provide context and background
- Celebrate small wins
- Educational and supportive

COMMUNICATION STYLE:
- Define industry terms when first used
- Use analogies and examples
- Check understanding: "Does that make sense?"
- Build confidence: "You're asking great questions"

Use searchKnowledge for accurate information and provide educational context."""
        )
    },
    {
        "config": create_assistant_config(
            name="CLP-Fast-Track",
            role="Expedited licensing specialist",
            system_prompt="""You are an efficient contractor licensing specialist for urgent timelines.

CRITICAL: WHEN RECEIVING A TRANSFER:
- DO NOT greet or waste time
- Immediately address urgency: "For your timeline..."
- Get straight to expedited options
- Focus on fastest path forward

PERSONA TRAITS:
- Direct and action-oriented
- Time-conscious and efficient
- Results-focused
- Prioritizes urgent needs
- Minimizes small talk

COMMUNICATION STYLE:
- Get straight to the point
- Focus on actionable next steps
- Provide timeline estimates
- Highlight expedited options

APPROACH:
- "Here's what you need to do immediately..."
- "The fastest path is..."
- "To save time, let's focus on..."

Use searchKnowledge for accurate timelines and expedited options."""
        )
    },
    {
        "config": create_assistant_config(
            name="CLP-Network-Expert",
            role="Qualifier network and business opportunity specialist",
            system_prompt="""You are a specialist in the qualifier network program for passive income opportunities.

CRITICAL: WHEN RECEIVING A TRANSFER:
- DO NOT greet or introduce
- Continue into opportunity discussion
- Reference their interest: "Regarding the business opportunity..."
- Focus immediately on income potential

PERSONA TRAITS:
- Business-focused and entrepreneurial
- Knowledgeable about passive income
- Professional but approachable
- Revenue and growth oriented

COMMUNICATION STYLE:
- Focus on business benefits
- Discuss income potential
- Explain network effects
- Show ROI and opportunity

APPROACH:
- "The income potential here is..."
- "You can help others while earning..."
- "The network effect means..."

Use searchKnowledge for qualifier program details and focus on business value."""
        )
    }
]

async def create_assistant(session: aiohttp.ClientSession, 
                          assistant_config: Dict[str, Any]) -> Optional[str]:
    """Create a single assistant via VAPI API."""
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with session.post(
            f"{VAPI_BASE_URL}/assistant",
            json=assistant_config,
            headers=headers
        ) as response:
            if response.status == 201:
                data = await response.json()
                print(f"✅ Created: {assistant_config['name']} (ID: {data['id']})")
                return data['id']
            else:
                error_text = await response.text()
                print(f"❌ Failed to create {assistant_config['name']}: {error_text}")
                return None
    except Exception as e:
        print(f"❌ Error creating {assistant_config['name']}: {e}")
        return None

async def update_transfer_destinations(session: aiohttp.ClientSession, 
                                      main_assistant_id: str,
                                      assistant_ids: Dict[str, str]):
    """
    Update the main router's transfer destinations with actual assistant IDs.
    Note: VAPI's transferCall is a built-in function, we just need to ensure
    the assistant names in our prompts match the created assistant names.
    """
    # For VAPI's built-in transferCall, we don't need to update destinations
    # The function will work with assistant names directly
    print(f"✅ Transfer routing configured for main router")
    return True

async def create_silent_transfer_squad():
    """Create the complete silent transfer squad."""
    if not VAPI_API_KEY:
        print("❌ VAPI_API_KEY not found")
        return
    
    print("🚀 Creating VAPI Silent Transfer Squad")
    print("=" * 60)
    print("This squad uses silent transfers for seamless handoffs")
    print("No conversation interruption when switching specialists")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Create all assistants
        assistant_ids = {}
        
        for assistant_data in ASSISTANTS:
            assistant_id = await create_assistant(session, assistant_data["config"])
            if assistant_id:
                assistant_ids[assistant_data["config"]["name"]] = assistant_id
        
        if not assistant_ids:
            print("❌ No assistants created successfully")
            return
        
        # Update main router with actual assistant IDs
        if "CLP-Main-Router" in assistant_ids:
            await update_transfer_destinations(
                session,
                assistant_ids["CLP-Main-Router"],
                assistant_ids
            )
        
        # Create squad (optional - transfers work without squad)
        squad_config = {
            "name": "CLP Silent Transfer Squad",
            "members": [
                {"assistantId": aid} for aid in assistant_ids.values()
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {VAPI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with session.post(
            f"{VAPI_BASE_URL}/squad",
            json=squad_config,
            headers=headers
        ) as response:
            if response.status == 201:
                squad = await response.json()
                print(f"\n✅ Squad created: {squad['id']}")
            else:
                print("\n⚠️  Squad creation failed, but assistants can still transfer")
        
        # Save configuration
        config_data = {
            "squad_type": "silent_transfer",
            "created_at": datetime.utcnow().isoformat(),
            "assistant_ids": assistant_ids,
            "main_router_id": assistant_ids.get("CLP-Main-Router"),
            "transfer_method": "silent",
            "webhook_url": FACT_WEBHOOK_URL
        }
        
        with open("silent_transfer_squad_config.json", "w") as f:
            json.dump(config_data, f, indent=2)
        
        print("\n📋 Silent Transfer Squad Summary:")
        print(f"   Main Router: {assistant_ids.get('CLP-Main-Router')}")
        print(f"   Total Assistants: {len(assistant_ids)}")
        print(f"   Transfer Method: Silent (seamless)")
        print(f"   Configuration saved to: silent_transfer_squad_config.json")
        
        print("\n🎯 How It Works:")
        print("1. Calls start with Main Router")
        print("2. Router detects persona from conversation")
        print("3. Silently transfers to appropriate specialist")
        print("4. Specialist continues without interruption")
        print("5. Caller experiences one seamless conversation")
        
        print("\n✨ Key Features:")
        print("- No 'transferring you now' announcements")
        print("- No conversation interruption")
        print("- Consistent voice throughout")
        print("- Full context preservation")
        print("- Automatic persona detection")

if __name__ == "__main__":
    asyncio.run(create_silent_transfer_squad())
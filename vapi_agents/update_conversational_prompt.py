#!/usr/bin/env python3
"""
Update VAPI Sales Agent to be more conversational and authentic
"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# VAPI API Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_KEY")
VAPI_BASE_URL = "https://api.vapi.ai"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

# More natural, conversational prompt
CONVERSATIONAL_SALES_PROMPT = """You are Sarah, a friendly licensing specialist at CLP. You help contractors get licensed quickly and easily.

SPEAKING STYLE:
- Talk like a real person on the phone
- Use SHORT sentences (5-10 words max)
- Pause naturally between thoughts
- Sound warm and approachable
- Be conversational, not robotic
- Use contractions (I'm, you'll, that's, etc.)
- Add filler words occasionally (um, well, so)
- Mirror the caller's energy level

NATURAL CONVERSATION EXAMPLES:
Instead of: "I understand cost is a concern. Consider this: DIY contractors have only a 35-45% approval rate."
Say: "Yeah, I get it. Cost is always a concern. But here's the thing - doing it yourself? Only about 4 out of 10 people pass."

Instead of: "Our program guarantees 98% approval in weeks, not months."
Say: "We get almost everyone approved. Like 98%. And fast too - weeks, not months."

Instead of: "The time you save—76 to 118 hours—is worth $6,000 to $18,750."
Say: "You'll save about 100 hours. That's like... $10,000 worth of your time."

CONVERSATION FLOW:
- Start casual: "Hey! Thanks for calling CLP. I'm Sarah. What's got you thinking about your license?"
- Listen and acknowledge: "Mm-hmm" "Got it" "I hear you" "Makes sense"
- Ask simple questions: "What state are you in?" "First time applying?"
- Share relatable info: "Yeah, Georgia's tricky" "A lot of folks feel that way"
- Build trust naturally: "Look, I'll be straight with you..."

KEY POINTS (say simply):
- "We get 98% of people approved" (not "98% approval rate")
- "Saves you about 100 hours" (not "76-118 hours")
- "First job usually pays for everything" (not "3-10x ROI")
- "Some folks make 3-6k extra per month" (not "qualifier network opportunity")

TOOL USAGE (Keep the same but respond naturally):

1. **searchKnowledge** - Use for any factual question
   But respond conversationally: "Let me check that for you real quick..."

2. **detectPersona** - Within first 2-3 exchanges
   Adjust your tone based on their vibe

3. **calculateTrust** - Every 3-4 exchanges
   No need to mention it

4. **handleObjection** - When they object
   But keep responses SHORT and natural

5. **bookAppointment** - When they're interested
   "Want me to get you started?"

HANDLING OBJECTIONS (Keep it real):
Price: "I get it. But think about this - one job pays for the whole thing."
Time: "The thing is, every day you wait costs you money. Real money."
DIY: "Sure, you could. But honestly? Most people fail and have to start over."

IMPORTANT RULES:
- NEVER give long explanations
- Break information into small chunks
- Pause between thoughts
- Sound like you're having a real conversation
- If they ask something complex, say: "That's a great question. Let me grab someone who knows more about that."

Remember: You're Sarah, a real person who happens to know a lot about licensing. Not a robot reading a script."""

CONVERSATIONAL_EXPERT_PROMPT = """You are Michael, senior licensing consultant at CLP. You're the expert people talk to for complex situations.

SPEAKING STYLE:
- Confident but approachable
- Use everyday language, not jargon
- Keep sentences SHORT
- Be direct and clear
- Sound like an experienced friend giving advice

NATURAL CONVERSATION EXAMPLES:
Instead of: "With your current income trajectory and market conditions..."
Say: "Based on what you're making now..."

Instead of: "The qualifier network presents a substantial passive income opportunity."
Say: "The qualifier thing? It's basically free money. 3 to 6 grand a month."

CONVERSATION APPROACH:
- Start strong: "Hey, I'm Michael. Sarah said you had some questions about [specific topic]. What's going on?"
- Get to the point quickly
- Use specific examples: "I had a guy last week who..."
- Be the expert but stay human

KEY PHRASES:
- "Here's what I'd do..."
- "In your situation..."
- "The smart move is..."
- "Between you and me..."
- "I've seen this work really well..."

Remember: You're the expert who makes complex things simple. Talk like you're explaining to a friend over coffee."""

def update_sales_agent_prompt():
    """Update Sales Agent with conversational prompt"""
    
    sales_agent_id = "edc2ad98-c1a0-4461-b963-64800fca1832"
    
    update_config = {
        "model": {
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.8,  # Slightly higher for more natural variation
            "maxTokens": 150,    # Shorter responses
            "systemPrompt": CONVERSATIONAL_SALES_PROMPT
        },
        "firstMessage": "Hey! Thanks for calling CLP. I'm Sarah. What's got you thinking about your license?",
        "responseDelaySeconds": 0.6  # Slightly longer for more natural pacing
    }
    
    response = requests.patch(
        f"{VAPI_BASE_URL}/assistant/{sales_agent_id}",
        headers=headers,
        json=update_config
    )
    
    if response.status_code == 200:
        print("✅ Updated Sales Agent to be more conversational")
        return True
    else:
        print(f"❌ Failed to update Sales Agent: {response.status_code}")
        print(response.text)
        return False

def update_expert_agent_prompt():
    """Update Expert Agent with conversational prompt"""
    
    expert_agent_id = "91b07fe0-4149-43fc-9cb3-fc4a24622e4f"
    
    update_config = {
        "model": {
            "provider": "anthropic",
            "model": "claude-3-opus-20240229",
            "temperature": 0.7,
            "maxTokens": 200,
            "systemPrompt": CONVERSATIONAL_EXPERT_PROMPT
        },
        "firstMessage": "Hey, I'm Michael. Sarah said you had some questions. What's going on?",
        "responseDelaySeconds": 0.5
    }
    
    response = requests.patch(
        f"{VAPI_BASE_URL}/assistant/{expert_agent_id}",
        headers=headers,
        json=update_config
    )
    
    if response.status_code == 200:
        print("✅ Updated Expert Agent to be more conversational")
        return True
    else:
        print(f"❌ Failed to update Expert Agent: {response.status_code}")
        print(response.text)
        return False

def create_response_examples():
    """Create a reference file with natural response examples"""
    
    examples = {
        "greetings": {
            "old": "Thanks for calling the Contractor Licensing Program! I'm Sarah, your licensing specialist. How's your day going?",
            "new": "Hey! Thanks for calling CLP. I'm Sarah. What's got you thinking about your license?"
        },
        "objection_price": {
            "old": "I understand cost is a concern. Consider this: DIY contractors have only a 35-45% approval rate, while our clients achieve 98%. The time you save—76 to 118 hours—is worth $6,000 to $18,750 at typical contractor rates.",
            "new": "Yeah, I get it. But look - one job pays for everything. Plus, doing it yourself? Most people fail and waste months."
        },
        "objection_time": {
            "old": "I appreciate you want to think it through. While you're considering, remember that every day without a license costs contractors $500 to $2,500 in lost opportunities.",
            "new": "I hear you. Thing is, every day you wait? You're losing money. Real money. Like $500 a day minimum."
        },
        "value_prop": {
            "old": "Our program guarantees 98% approval rate versus 35-45% for DIY applications, saving you 76-118 hours worth $6,000-$18,750.",
            "new": "So basically, we get almost everyone approved. Saves you about 100 hours too. That's worth like... 10 grand of your time."
        },
        "qualifier_network": {
            "old": "The qualifier network opportunity provides $3,000 to $6,000 monthly passive income by lending your license to vetted contractors.",
            "new": "Oh, and there's this qualifier thing. Some folks make an extra 3 to 6 grand a month. Just for having their license."
        },
        "closing": {
            "old": "Based on everything we've discussed, I can help you get started with the enrollment process today.",
            "new": "So... want me to get you started? I can set everything up right now."
        },
        "acknowledgments": [
            "Mm-hmm",
            "Got it",
            "I hear you",
            "Makes sense",
            "Right, right",
            "Okay, cool",
            "Yeah, totally",
            "I see what you mean",
            "Fair enough",
            "Absolutely"
        ],
        "transitions": [
            "So here's the thing...",
            "Let me ask you this...",
            "Okay, so...",
            "The way I see it...",
            "Here's what I'm thinking...",
            "You know what?",
            "Actually...",
            "Oh, and one more thing..."
        ]
    }
    
    with open("vapi_agents/conversational_examples.json", "w") as f:
        json.dump(examples, f, indent=2)
    
    print("📝 Created conversational examples reference")

def main():
    print("\n🎭 Making VAPI Agents More Conversational")
    print("=" * 60)
    
    # Update both agents
    print("\n1️⃣ Updating Sales Agent...")
    update_sales_agent_prompt()
    
    print("\n2️⃣ Updating Expert Agent...")
    update_expert_agent_prompt()
    
    # Create examples
    print("\n3️⃣ Creating response examples...")
    create_response_examples()
    
    print("\n" + "=" * 60)
    print("✅ Agents Updated!")
    print("=" * 60)
    print("""
Key Changes:
✓ Shorter sentences (5-10 words max)
✓ Natural pauses and fillers
✓ Conversational tone
✓ Real acknowledgments ("Got it", "I hear you")
✓ Simple language (no jargon)
✓ Warmer, more human responses

Test the improvements:
1. Call your VAPI number
2. Notice the more natural flow
3. Responses should feel like a real conversation
4. No more robotic, long-winded explanations

The agents will now:
- Sound like real people
- Use everyday language
- Keep responses short and punchy
- Build rapport naturally
    """)

if __name__ == "__main__":
    main()
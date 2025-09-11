#!/usr/bin/env python3
"""
VAPI Agent Setup Script
Automatically creates and configures both CLP agents in VAPI.
"""

import os
import json
import requests
from typing import Dict, Any

# VAPI API Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_BASE_URL = "https://api.vapi.ai"
WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook"

if not VAPI_API_KEY:
    print("❌ Error: VAPI_API_KEY environment variable not set")
    print("Get your API key from: https://dashboard.vapi.ai/api-keys")
    print("Then run: export VAPI_API_KEY='your-key-here'")
    exit(1)

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}


def create_sales_agent() -> Dict[str, Any]:
    """Create the CLP Sales Specialist agent."""
    
    agent_config = {
        "name": "CLP Sales Specialist",
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en-US"
        },
        "model": {
            "provider": "anthropic",
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.7,
            "maxTokens": 250,
            "systemPrompt": """You are Sarah, a CLP Sales Specialist. Your goal is to qualify callers, build trust, and either book appointments or transfer to an expert.

CONVERSATION SCORING:
- Track trust_score (0-100)
- Track persona_confidence (0-1)
- Track objection_count
- Track value_mentioned (boolean)
- Track urgency_level (low/medium/high)

PERSONA DETECTION:
Listen for keywords to identify:
1. Overwhelmed Veteran: 'complicated', 'stressed', 'too much'
2. Confused Newcomer: 'new', 'first time', 'beginner'
3. Urgent Operator: 'quickly', 'urgent', 'deadline'
4. Strategic Investor: 'income', 'business', 'profit'
5. Skeptical Shopper: price questions, comparisons

TRUST BUILDING:
- Score 0-30: Focus on rapport and understanding
- Score 30-50: Present value proposition
- Score 50-70: Handle objections, build urgency
- Score 70+: Close or transfer to expert

KEY POINTS:
- 98% approval rate vs 35-45% DIY
- Save 76-118 hours worth $6,000-$18,750
- First project returns 3-10x investment
- Qualifier network: $3,000-$6,000/month
- Daily cost of waiting: $500-$2,500

TRANSFER TRIGGERS:
- Trust score 70+ for complex cases
- Qualifier network interest
- Multi-state licensing
- Project values >$50,000
- Commercial licensing questions

Be conversational, empathetic, and solution-focused. Use specific numbers and examples."""
        },
        "voice": {
            "provider": "elevenlabs",
            "voiceId": "EXAVITQu4vr4xnSDxMaL",  # Sarah voice
            "model": "eleven_turbo_v2",
            "stability": 0.65,
            "similarityBoost": 0.75,
            "optimizeStreamingLatency": 3
        },
        "firstMessage": "Thanks for calling the Contractor Licensing Program! I'm Sarah, your licensing specialist. I help contractors save 76 to 118 hours getting licensed while achieving a 98% approval rate. Are you calling about getting your contractor license, or are you already licensed and interested in our qualifier network that pays $3,000 to $6,000 monthly?",
        "serverUrl": WEBHOOK_URL,
        "serverUrlSecret": os.getenv("VAPI_WEBHOOK_SECRET", ""),
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 0.4,
        "llmRequestDelaySeconds": 0.1,
        "numWordsToInterruptAssistant": 2,
        "endCallFunctionEnabled": True,
        "endCallMessage": "Thank you for calling the Contractor Licensing Program. We look forward to helping you achieve your licensing goals!",
        "endCallPhrases": ["goodbye", "bye", "talk to you later"],
        "functions": [
            {
                "name": "searchKnowledge",
                "description": "Search contractor licensing knowledge base",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "state": {"type": "string", "description": "Two-letter state code"},
                        "category": {"type": "string", "description": "Knowledge category"}
                    }
                }
            },
            {
                "name": "detectPersona",
                "description": "Detect caller persona for tailored responses",
                "parameters": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {"type": "string", "description": "Recent conversation text"}
                    }
                }
            },
            {
                "name": "calculateTrust",
                "description": "Calculate current trust score",
                "parameters": {
                    "type": "object",
                    "required": ["events"],
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                                    "description": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            },
            {
                "name": "handleObjection",
                "description": "Get objection handling response",
                "parameters": {
                    "type": "object",
                    "required": ["type"],
                    "properties": {
                        "type": {"type": "string", "enum": ["too_expensive", "need_time", "diy", "not_sure"]}
                    }
                }
            },
            {
                "name": "bookAppointment",
                "description": "Schedule consultation appointment",
                "parameters": {
                    "type": "object",
                    "required": ["name", "email", "phone"],
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "state": {"type": "string"},
                        "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
                        "notes": {"type": "string"}
                    }
                }
            }
        ]
    }
    
    response = requests.post(
        f"{VAPI_BASE_URL}/assistant",
        headers=headers,
        json=agent_config
    )
    
    if response.status_code == 201:
        agent = response.json()
        print(f"✅ Created Sales Agent: {agent['id']}")
        return agent
    else:
        print(f"❌ Failed to create Sales Agent: {response.status_code}")
        print(response.text)
        return None


def create_expert_agent(sales_agent_id: str) -> Dict[str, Any]:
    """Create the CLP Expert Consultant agent."""
    
    agent_config = {
        "name": "CLP Expert Consultant",
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-2",
            "language": "en-US"
        },
        "model": {
            "provider": "anthropic",
            "model": "claude-3-opus-20240229",
            "temperature": 0.6,
            "maxTokens": 300,
            "systemPrompt": """You are Michael, a Senior CLP Expert Consultant. You handle complex cases, close high-value deals, and explain qualifier network opportunities.

YOUR EXPERTISE:
- Multi-state licensing strategies
- Qualifier network income ($3,000-$6,000/month)
- Commercial vs residential licensing
- Business structure optimization
- Regulatory compliance
- ROI maximization strategies

CONVERSATION STATE:
You receive transfers with:
- trust_score (usually 50+)
- detected_persona
- specific_interest
- objection_history

AUTHORITY POSITIONING:
- Reference specific success cases
- Use precise numbers and data
- Demonstrate deep industry knowledge
- Share insider insights

QUALIFIER NETWORK FOCUS:
- $72,000 annual income example
- 3,673% ROI demonstrated
- Passive income like rental property
- No physical work required
- Help other contractors while earning

CLOSING STRATEGIES:
Trust 50-70: Build value, handle complex objections
Trust 70-85: Assumptive close, next steps
Trust 85+: Direct close, payment discussion

KEY SUCCESS METRICS:
- Ryan R.: $65K → $162K (150% increase)
- 35 days to license approval
- 2,735% first-year ROI
- 98% approval rate

Be authoritative, strategic, and consultative. You're the expert who makes complex things simple."""
        },
        "voice": {
            "provider": "elevenlabs",
            "voiceId": "pNInz6obpgDQGcFmaJgB",  # Adam voice
            "model": "eleven_turbo_v2",
            "stability": 0.75,
            "similarityBoost": 0.85,
            "optimizeStreamingLatency": 3
        },
        "firstMessage": "Hello, I'm Michael, Senior Licensing Consultant with the Contractor Licensing Program. I understand you're interested in our advanced licensing strategies or qualifier network opportunities. I specialize in complex licensing solutions and helping contractors generate $3,000 to $6,000 monthly passive income. What specific opportunity brought you to speak with me today?",
        "serverUrl": WEBHOOK_URL,
        "serverUrlSecret": os.getenv("VAPI_WEBHOOK_SECRET", ""),
        "silenceTimeoutSeconds": 30,
        "responseDelaySeconds": 0.3,
        "llmRequestDelaySeconds": 0.1,
        "numWordsToInterruptAssistant": 2,
        "endCallFunctionEnabled": True,
        "endCallMessage": "Thank you for your time today. I'm confident we can help you achieve extraordinary results with your contractor licensing goals. You'll receive our detailed proposal within 24 hours.",
        "endCallPhrases": ["goodbye", "bye", "talk to you later"],
        "transferList": [
            {
                "assistantId": sales_agent_id,
                "message": "Let me transfer you back to our sales team to finalize the details.",
                "description": "Transfer back to sales for basic questions"
            }
        ],
        "functions": [
            {
                "name": "searchKnowledge",
                "description": "Search advanced licensing knowledge",
                "parameters": {
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"},
                        "state": {"type": "string"},
                        "category": {"type": "string"}
                    }
                }
            },
            {
                "name": "calculateROI",
                "description": "Calculate specific ROI for customer",
                "parameters": {
                    "type": "object",
                    "required": ["currentIncome"],
                    "properties": {
                        "currentIncome": {"type": "number"},
                        "projectSize": {"type": "number"},
                        "monthlyProjects": {"type": "number"},
                        "qualifierNetwork": {"type": "boolean"}
                    }
                }
            },
            {
                "name": "qualifierNetworkAnalysis",
                "description": "Analyze qualifier network opportunity",
                "parameters": {
                    "type": "object",
                    "required": ["state", "licenseType"],
                    "properties": {
                        "state": {"type": "string"},
                        "licenseType": {"type": "string"},
                        "experience": {"type": "number"}
                    }
                }
            },
            {
                "name": "scheduleConsultation",
                "description": "Book expert consultation",
                "parameters": {
                    "type": "object",
                    "required": ["name", "email", "phone", "consultationType"],
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "phone": {"type": "string"},
                        "consultationType": {"type": "string", "enum": ["licensing", "qualifier", "multi-state", "commercial"]},
                        "preferredTime": {"type": "string"},
                        "investmentRange": {"type": "string", "enum": ["3k-5k", "5k-10k", "10k+"]},
                        "urgency": {"type": "string", "enum": ["immediate", "30days", "60days", "exploring"]}
                    }
                }
            }
        ]
    }
    
    response = requests.post(
        f"{VAPI_BASE_URL}/assistant",
        headers=headers,
        json=agent_config
    )
    
    if response.status_code == 201:
        agent = response.json()
        print(f"✅ Created Expert Agent: {agent['id']}")
        return agent
    else:
        print(f"❌ Failed to create Expert Agent: {response.status_code}")
        print(response.text)
        return None


def update_sales_agent_transfer(sales_agent_id: str, expert_agent_id: str):
    """Update the sales agent to include transfer to expert."""
    
    update_config = {
        "transferList": [
            {
                "assistantId": expert_agent_id,
                "message": "I'll connect you with our senior consultant Michael who specializes in your specific needs.",
                "description": "Transfer to expert for complex cases"
            }
        ]
    }
    
    response = requests.patch(
        f"{VAPI_BASE_URL}/assistant/{sales_agent_id}",
        headers=headers,
        json=update_config
    )
    
    if response.status_code == 200:
        print(f"✅ Updated Sales Agent with transfer to Expert")
        return True
    else:
        print(f"❌ Failed to update Sales Agent: {response.status_code}")
        print(response.text)
        return False


def main():
    """Main setup flow."""
    print("\n🚀 VAPI Agent Setup Script")
    print("=" * 50)
    
    # Step 1: Create Sales Agent
    print("\n1️⃣ Creating CLP Sales Specialist...")
    sales_agent = create_sales_agent()
    if not sales_agent:
        print("❌ Setup failed. Please check your API key and try again.")
        return
    
    # Step 2: Create Expert Agent
    print("\n2️⃣ Creating CLP Expert Consultant...")
    expert_agent = create_expert_agent(sales_agent['id'])
    if not expert_agent:
        print("❌ Setup failed. Please check the error and try again.")
        return
    
    # Step 3: Update Sales Agent with Transfer
    print("\n3️⃣ Linking agents for transfers...")
    if update_sales_agent_transfer(sales_agent['id'], expert_agent['id']):
        print("\n✅ Setup Complete!")
        print("=" * 50)
        print("\n📞 Your VAPI Agents are ready:")
        print(f"   Sales Agent ID: {sales_agent['id']}")
        print(f"   Expert Agent ID: {expert_agent['id']}")
        print(f"\n🔗 Webhook URL: {WEBHOOK_URL}")
        print("\n📱 Next Steps:")
        print("   1. Go to https://dashboard.vapi.ai/phone-numbers")
        print("   2. Assign a phone number to the Sales Agent")
        print("   3. Test by calling your VAPI number")
        print("\n💡 Test Phrases:")
        print('   - "I\'m overwhelmed by all this paperwork"')
        print('   - "Tell me about the qualifier network"')
        print('   - "How much does this cost?"')
        print('   - "I need my license urgently"')
        
        # Save agent IDs for reference
        with open('vapi_agents/agent_ids.json', 'w') as f:
            json.dump({
                "sales_agent_id": sales_agent['id'],
                "expert_agent_id": expert_agent['id'],
                "created_at": str(datetime.now()),
                "webhook_url": WEBHOOK_URL
            }, f, indent=2)
        print("\n📄 Agent IDs saved to: vapi_agents/agent_ids.json")
    else:
        print("\n⚠️  Agents created but transfer link failed. Please link manually in VAPI dashboard.")


if __name__ == "__main__":
    from datetime import datetime
    main()
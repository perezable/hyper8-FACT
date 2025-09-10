#!/usr/bin/env python3
"""
Create a VAPI Workflow for Contractor Licensing Program.
This uses VAPI's Workflow feature which properly handles transfers between conversation nodes.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "c49631b4-2f8f-40b3-9ce1-22f731879fb9")
FACT_WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"

# CLP Workflow Definition
CLP_WORKFLOW = {
    "name": "CLP Contractor Licensing Workflow",
    "nodes": [
        {
            "name": "main_router",
            "type": "conversation",
            "isStart": True,
            "metadata": {
                "position": {"x": 0, "y": 0}
            },
            "prompt": """You are the main contractor licensing assistant. Your role is to quickly identify what the caller needs and route them appropriately.

Listen for key indicators:
- If they sound overwhelmed, stressed, mention "too much" or "complicated" → Route to veteran_support
- If they're new, confused, asking "what is" or "how do I start" → Route to newcomer_guide
- If they need something quickly, urgently, have a deadline → Route to fast_track
- If they ask about business opportunities, making money, income → Route to network_expert

Start with a friendly greeting and ask how you can help.""",
            "messagePlan": {
                "firstMessage": "Hello! Welcome to the Contractor Licensing Program. I can help you with licensing requirements, applications, and more. What brings you here today?"
            }
        },
        {
            "name": "veteran_support",
            "type": "conversation",
            "metadata": {
                "position": {"x": -400, "y": 300}
            },
            "prompt": """You are a supportive specialist for overwhelmed contractors. Your tone is calm, reassuring, and methodical.

Your approach:
1. Acknowledge their feelings of being overwhelmed
2. Break down the process into simple, manageable steps
3. Focus on one thing at a time
4. Provide encouragement and realistic timelines
5. Use the searchKnowledge function to find specific information

Start by acknowledging their stress and offering to simplify things.""",
            "messagePlan": {
                "firstMessage": "I understand this feels overwhelming. Let's break this down into manageable steps. First, tell me where you are in the process so I can help simplify things for you."
            },
            "tools": [
                {
                    "type": "function",
                    "function": {
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
                    }
                }
            ]
        },
        {
            "name": "newcomer_guide",
            "type": "conversation",
            "metadata": {
                "position": {"x": -400, "y": 600}
            },
            "prompt": """You are a friendly guide for people new to contractor licensing. Your tone is educational, patient, and encouraging.

Your approach:
1. Start with the basics - no assumptions
2. Explain terminology in simple terms
3. Provide a clear roadmap from start to finish
4. Check understanding frequently
5. Use the searchKnowledge function for accurate information

Begin by welcoming them and explaining the basics.""",
            "messagePlan": {
                "firstMessage": "Welcome! Since you're new to contractor licensing, let me start with the basics. Getting licensed involves a few key steps, and I'll guide you through each one. What type of work are you planning to do?"
            },
            "tools": [
                {
                    "type": "function",
                    "function": {
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
                    }
                }
            ]
        },
        {
            "name": "fast_track",
            "type": "conversation",
            "metadata": {
                "position": {"x": 400, "y": 300}
            },
            "prompt": """You are an expedited licensing specialist. Your tone is efficient, direct, and action-oriented.

Your approach:
1. Get straight to the point - no fluff
2. Focus on fastest path to license
3. Provide specific timelines and deadlines
4. Highlight express options and shortcuts
5. Use searchKnowledge for quick, accurate answers

Start by acknowledging their urgency and getting key details.""",
            "messagePlan": {
                "firstMessage": "I understand you need your license quickly. Let me help you with the fastest path. What's your deadline, and what type of contractor license do you need?"
            },
            "tools": [
                {
                    "type": "function",
                    "function": {
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
                    }
                }
            ]
        },
        {
            "name": "network_expert",
            "type": "conversation",
            "metadata": {
                "position": {"x": 400, "y": 600}
            },
            "prompt": """You are a business opportunity specialist for the qualifier network. Your tone is entrepreneurial, motivating, and informative.

Your approach:
1. Focus on income potential and business opportunities
2. Explain the qualifier network and how it works
3. Discuss revenue models and earning potential
4. Provide success stories and examples
5. Use searchKnowledge for specific program details

Start by confirming their interest in business opportunities.""",
            "messagePlan": {
                "firstMessage": "Great question about income opportunities! The qualifier network allows you to help other contractors get licensed while earning substantial fees. Let me explain how this works and the potential earnings."
            },
            "tools": [
                {
                    "type": "function",
                    "function": {
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
                    }
                }
            ]
        },
        {
            "name": "collect_info",
            "type": "conversation",
            "metadata": {
                "position": {"x": 0, "y": 900}
            },
            "prompt": "Collect the caller's contact information and specific needs for follow-up. Get their name, email, phone number, state, and a brief description of what they need help with.",
            "variableExtractionPlan": {
                "output": [
                    {
                        "type": "string",
                        "title": "caller_name",
                        "description": "The caller's full name"
                    },
                    {
                        "type": "string",
                        "title": "email",
                        "description": "The caller's email address"
                    },
                    {
                        "type": "string",
                        "title": "phone",
                        "description": "The caller's phone number"
                    },
                    {
                        "type": "string",
                        "title": "state",
                        "description": "The state they need licensing in"
                    },
                    {
                        "type": "string",
                        "title": "needs",
                        "description": "What they need help with"
                    }
                ]
            }
        },
        {
            "name": "end_call",
            "type": "tool",
            "metadata": {
                "position": {"x": 0, "y": 1200}
            },
            "tool": {
                "type": "endCall",
                "function": {
                    "name": "end_call_tool",
                    "parameters": {
                        "type": "object",
                        "required": [],
                        "properties": {}
                    }
                },
                "messages": [
                    {
                        "type": "request-start",
                        "content": "Thank you for calling the Contractor Licensing Program. We'll follow up with you soon. Have a great day!",
                        "blocking": True
                    }
                ]
            }
        }
    ],
    "edges": [
        {
            "from": "main_router",
            "to": "veteran_support",
            "condition": {
                "type": "ai",
                "prompt": "User expressed feeling overwhelmed, stressed, or mentioned things are too complicated"
            }
        },
        {
            "from": "main_router",
            "to": "newcomer_guide",
            "condition": {
                "type": "ai",
                "prompt": "User is new to contractor licensing or confused about the basics"
            }
        },
        {
            "from": "main_router",
            "to": "fast_track",
            "condition": {
                "type": "ai",
                "prompt": "User needs license quickly, has urgent deadline, or expressed time pressure"
            }
        },
        {
            "from": "main_router",
            "to": "network_expert",
            "condition": {
                "type": "ai",
                "prompt": "User asked about business opportunities, making money, or the qualifier network"
            }
        },
        {
            "from": "veteran_support",
            "to": "collect_info",
            "condition": {
                "type": "ai",
                "prompt": "User received help and conversation is concluding, or user wants follow-up"
            }
        },
        {
            "from": "newcomer_guide",
            "to": "collect_info",
            "condition": {
                "type": "ai",
                "prompt": "User received guidance and conversation is concluding, or user wants follow-up"
            }
        },
        {
            "from": "fast_track",
            "to": "collect_info",
            "condition": {
                "type": "ai",
                "prompt": "User received expedited help and conversation is concluding, or user wants follow-up"
            }
        },
        {
            "from": "network_expert",
            "to": "collect_info",
            "condition": {
                "type": "ai",
                "prompt": "User learned about opportunities and conversation is concluding, or user wants follow-up"
            }
        },
        {
            "from": "collect_info",
            "to": "end_call",
            "condition": {
                "type": "ai",
                "prompt": "Contact information collected or user declined to provide it"
            }
        },
        {
            "from": "veteran_support",
            "to": "end_call",
            "condition": {
                "type": "ai",
                "prompt": "User wants to end the call without providing contact info"
            }
        },
        {
            "from": "newcomer_guide",
            "to": "end_call",
            "condition": {
                "type": "ai",
                "prompt": "User wants to end the call without providing contact info"
            }
        },
        {
            "from": "fast_track",
            "to": "end_call",
            "condition": {
                "type": "ai",
                "prompt": "User wants to end the call without providing contact info"
            }
        },
        {
            "from": "network_expert",
            "to": "end_call",
            "condition": {
                "type": "ai",
                "prompt": "User wants to end the call without providing contact info"
            }
        }
    ],
    "globalPrompt": "You are part of the Contractor Licensing Program (CLP) team. Always be helpful, professional, and focused on solving the caller's specific needs. Use the searchKnowledge function when you need specific information about licensing requirements, fees, or procedures."
}

async def create_workflow():
    """Create the CLP workflow in VAPI."""
    
    print("🚀 Creating CLP Workflow in VAPI")
    print("=" * 70)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Create the workflow
        async with session.post(
            "https://api.vapi.ai/workflow",
            json=CLP_WORKFLOW,
            headers=headers
        ) as response:
            if response.status in [200, 201]:
                data = await response.json()
                workflow_id = data.get("id")
                
                print("✅ Workflow created successfully!")
                print(f"\n📋 Workflow Details:")
                print(f"   - ID: {workflow_id}")
                print(f"   - Name: {data.get('name')}")
                print(f"   - Nodes: {len(data.get('nodes', []))}")
                print(f"   - Edges: {len(data.get('edges', []))}")
                
                # Save configuration
                with open("clp_workflow_config.json", "w") as f:
                    json.dump({
                        "workflow_id": workflow_id,
                        "created_at": datetime.now().isoformat(),
                        "name": "CLP Contractor Licensing Workflow",
                        "nodes": [
                            "main_router",
                            "veteran_support",
                            "newcomer_guide",
                            "fast_track",
                            "network_expert",
                            "collect_info",
                            "end_call"
                        ]
                    }, f, indent=2)
                
                print(f"\n   Configuration saved to: clp_workflow_config.json")
                
                print("\n🎯 Workflow Structure:")
                print("   main_router (entry)")
                print("   ├── veteran_support (overwhelmed)")
                print("   ├── newcomer_guide (new/confused)")
                print("   ├── fast_track (urgent/quickly)")
                print("   └── network_expert (business/money)")
                print("       └── collect_info → end_call")
                
                print("\n📞 To Test:")
                print("1. Go to VAPI Dashboard")
                print(f"2. Find workflow: {workflow_id}")
                print("3. Create an assistant with this workflow")
                print("4. Test different scenarios:")
                print("   - 'I'm overwhelmed' → Routes to veteran_support")
                print("   - 'I'm new to this' → Routes to newcomer_guide")
                print("   - 'I need this quickly' → Routes to fast_track")
                print("   - 'Can I make money?' → Routes to network_expert")
                
                return workflow_id
            else:
                error = await response.text()
                print(f"❌ Failed to create workflow: {error}")
                try:
                    error_data = json.loads(error)
                    print(f"\nError details: {json.dumps(error_data, indent=2)}")
                except:
                    pass
                return None

async def create_workflow_assistant(workflow_id):
    """Create an assistant that uses the workflow."""
    
    print("\n🤖 Creating Assistant for Workflow")
    print("=" * 70)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    assistant_config = {
        "name": "CLP-Workflow-Assistant",
        "workflow": {
            "id": workflow_id
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM"  # Rachel
        },
        "model": {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.7
        },
        "recordingEnabled": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.vapi.ai/assistant",
            json=assistant_config,
            headers=headers
        ) as response:
            if response.status in [200, 201]:
                data = await response.json()
                assistant_id = data.get("id")
                
                print("✅ Assistant created with workflow!")
                print(f"   - Assistant ID: {assistant_id}")
                print(f"   - Workflow ID: {workflow_id}")
                print("\n📱 Ready to test with this assistant!")
                
                return assistant_id
            else:
                error = await response.text()
                print(f"❌ Failed to create assistant: {error}")
                return None

async def main():
    """Main execution."""
    
    # Create workflow
    workflow_id = await create_workflow()
    
    if workflow_id:
        # Create assistant with workflow
        assistant_id = await create_workflow_assistant(workflow_id)
        
        if assistant_id:
            print("\n" + "=" * 70)
            print("🎉 SUCCESS! CLP Workflow System Ready")
            print("=" * 70)
            print("\nWorkflow handles routing automatically:")
            print("- No more manual transferCall issues")
            print("- Smooth transitions between specialists")
            print("- Proper conversation flow management")
            print("\nTest with the new assistant in VAPI Dashboard!")
        else:
            print("\nWorkflow created but assistant creation failed.")
            print("You can manually create an assistant with the workflow in the dashboard.")
    else:
        print("\n⚠️ Workflow creation failed. Check error above.")

if __name__ == "__main__":
    asyncio.run(main())
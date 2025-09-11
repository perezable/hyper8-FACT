#!/usr/bin/env python3
"""
Update VAPI agents to use proper custom functions via Tools API
"""

import os
import json
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# VAPI API Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY") or os.getenv("VAPI_KEY")
VAPI_BASE_URL = "https://api.vapi.ai"
WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

# Define all custom functions based on searchKnowledge template
CUSTOM_FUNCTIONS = [
    {
        "name": "searchKnowledge",
        "description": "Search contractor licensing knowledge base for accurate information",
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
                    "description": "Trust events from conversation",
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
                "type": {
                    "type": "string",
                    "enum": ["too_expensive", "need_time", "diy", "not_sure"],
                    "description": "Type of objection"
                }
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
                "name": {"type": "string", "description": "Customer name"},
                "email": {"type": "string", "description": "Customer email"},
                "phone": {"type": "string", "description": "Customer phone"},
                "state": {"type": "string", "description": "State code"},
                "urgency": {"type": "string", "enum": ["low", "medium", "high"], "description": "Urgency level"},
                "notes": {"type": "string", "description": "Additional notes"}
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
                "currentIncome": {"type": "number", "description": "Current annual income"},
                "projectSize": {"type": "number", "description": "Average project size"},
                "monthlyProjects": {"type": "number", "description": "Projects per month"},
                "qualifierNetwork": {"type": "boolean", "description": "Include qualifier network income"}
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
                "state": {"type": "string", "description": "State code"},
                "licenseType": {"type": "string", "description": "Type of license"},
                "experience": {"type": "number", "description": "Years of experience"}
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
                "name": {"type": "string", "description": "Customer name"},
                "email": {"type": "string", "description": "Customer email"},
                "phone": {"type": "string", "description": "Customer phone"},
                "consultationType": {
                    "type": "string",
                    "enum": ["licensing", "qualifier", "multi-state", "commercial"],
                    "description": "Type of consultation"
                },
                "preferredTime": {"type": "string", "description": "Preferred time"},
                "investmentRange": {
                    "type": "string",
                    "enum": ["3k-5k", "5k-10k", "10k+"],
                    "description": "Investment range"
                },
                "urgency": {
                    "type": "string",
                    "enum": ["immediate", "30days", "60days", "exploring"],
                    "description": "Urgency level"
                }
            }
        }
    }
]

def create_custom_tool(function_def):
    """Create a custom tool in VAPI"""
    
    tool_config = {
        "type": "function",
        "function": {
            "name": function_def["name"],
            "description": function_def["description"],
            "parameters": function_def["parameters"]
        },
        "server": {
            "url": WEBHOOK_URL,
            "secret": os.getenv("VAPI_WEBHOOK_SECRET", "")
        }
    }
    
    # First check if tool already exists
    check_response = requests.get(
        f"{VAPI_BASE_URL}/tool",
        headers=headers
    )
    
    if check_response.status_code == 200:
        existing_tools = check_response.json()
        for tool in existing_tools:
            if tool.get("function", {}).get("name") == function_def["name"]:
                print(f"   ✓ Tool '{function_def['name']}' already exists (ID: {tool['id']})")
                return tool["id"]
    
    # Create new tool
    response = requests.post(
        f"{VAPI_BASE_URL}/tool",
        headers=headers,
        json=tool_config
    )
    
    if response.status_code in [200, 201]:
        tool = response.json()
        print(f"   ✅ Created tool '{function_def['name']}' (ID: {tool['id']})")
        return tool["id"]
    else:
        print(f"   ❌ Failed to create tool '{function_def['name']}': {response.status_code}")
        print(f"      {response.text}")
        return None

def update_assistant_tools(assistant_id, assistant_name, tool_ids):
    """Update assistant to use the custom tools"""
    
    # Get current assistant configuration
    get_response = requests.get(
        f"{VAPI_BASE_URL}/assistant/{assistant_id}",
        headers=headers
    )
    
    if get_response.status_code != 200:
        print(f"❌ Failed to get assistant {assistant_name}")
        return False
    
    assistant = get_response.json()
    
    # Remove old functions and add tool IDs
    update_config = {
        "functions": [],  # Clear old functions
        "toolIds": tool_ids  # Add new tool IDs
    }
    
    response = requests.patch(
        f"{VAPI_BASE_URL}/assistant/{assistant_id}",
        headers=headers,
        json=update_config
    )
    
    if response.status_code == 200:
        print(f"✅ Updated {assistant_name} with {len(tool_ids)} custom tools")
        return True
    else:
        print(f"❌ Failed to update {assistant_name}: {response.status_code}")
        print(response.text)
        return False

def main():
    print("\n🚀 VAPI Function Update Script")
    print("=" * 70)
    
    # Step 1: Create all custom tools
    print("\n1️⃣ Creating Custom Tools...")
    print("-" * 70)
    
    tool_ids = []
    for func in CUSTOM_FUNCTIONS:
        tool_id = create_custom_tool(func)
        if tool_id:
            tool_ids.append(tool_id)
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n✅ Created/verified {len(tool_ids)} custom tools")
    
    # Step 2: Update Sales Agent
    print("\n2️⃣ Updating Sales Agent...")
    print("-" * 70)
    
    sales_agent_id = "edc2ad98-c1a0-4461-b963-64800fca1832"
    sales_tools = tool_ids[:5]  # First 5 tools for sales agent
    update_assistant_tools(sales_agent_id, "CLP Sales Specialist", sales_tools)
    
    # Step 3: Update Expert Agent
    print("\n3️⃣ Updating Expert Agent...")
    print("-" * 70)
    
    expert_agent_id = "91b07fe0-4149-43fc-9cb3-fc4a24622e4f"
    # Expert gets searchKnowledge, calculateROI, qualifierNetworkAnalysis, scheduleConsultation
    expert_tools = [tool_ids[0], tool_ids[5], tool_ids[6], tool_ids[7]]
    update_assistant_tools(expert_agent_id, "CLP Expert Consultant", expert_tools)
    
    print("\n" + "=" * 70)
    print("✅ Setup Complete!")
    print("=" * 70)
    print("""
Your agents are now configured with proper custom functions that:
1. Route to your webhook endpoint
2. Have correctly defined parameters
3. Will show up in VAPI dashboard as custom tools

Test by calling and saying:
- "What are the requirements in Georgia?" (tests searchKnowledge)
- "I'm overwhelmed by all this" (tests detectPersona)
- "That sounds expensive" (tests handleObjection)
    """)
    
    # Save configuration
    config = {
        "tool_ids": tool_ids,
        "sales_agent": {
            "id": sales_agent_id,
            "tools": sales_tools
        },
        "expert_agent": {
            "id": expert_agent_id,
            "tools": expert_tools
        },
        "webhook_url": WEBHOOK_URL,
        "updated_at": str(time.time())
    }
    
    with open("vapi_agents/tools_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print("\n📄 Configuration saved to: vapi_agents/tools_config.json")

if __name__ == "__main__":
    main()
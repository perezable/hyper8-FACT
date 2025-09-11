#!/usr/bin/env python3
"""
Link custom tools to VAPI assistants
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

def list_tools():
    """List all available tools"""
    response = requests.get(
        f"{VAPI_BASE_URL}/tool",
        headers=headers
    )
    
    if response.status_code == 200:
        tools = response.json()
        print(f"\n📋 Available Tools ({len(tools)} total):")
        print("=" * 70)
        
        tool_map = {}
        for tool in tools:
            func = tool.get("function", {})
            name = func.get("name", "Unnamed")
            tool_id = tool.get("id")
            tool_map[name] = tool_id
            
            print(f"\nTool: {name}")
            print(f"ID: {tool_id}")
            print(f"Type: {tool.get('type', 'Unknown')}")
            print(f"Description: {func.get('description', 'No description')}")
            
            # Show server configuration
            server = tool.get("server", {})
            if server:
                print(f"Webhook URL: {server.get('url', 'Not set')}")
        
        return tool_map
    else:
        print(f"❌ Failed to list tools: {response.status_code}")
        return {}

def update_assistant_with_tools(assistant_id, assistant_name, tool_names, tool_map):
    """Update assistant to reference the custom tools"""
    
    # Build functions array that references the tool IDs
    functions = []
    for tool_name in tool_names:
        if tool_name in tool_map:
            # Reference the existing tool by name
            functions.append({
                "name": tool_name,
                "description": f"Uses custom tool: {tool_name}",
                "toolId": tool_map[tool_name]
            })
    
    # Update assistant with function references
    update_config = {
        "functions": functions
    }
    
    response = requests.patch(
        f"{VAPI_BASE_URL}/assistant/{assistant_id}",
        headers=headers,
        json=update_config
    )
    
    if response.status_code == 200:
        print(f"✅ Updated {assistant_name} with {len(functions)} tool references")
        return True
    else:
        print(f"❌ Failed to update {assistant_name}: {response.status_code}")
        print(response.text)
        
        # Try alternative approach - set tools in the assistant's toolConfig
        alt_config = {
            "toolConfig": {
                "functionTools": tool_names
            }
        }
        
        alt_response = requests.patch(
            f"{VAPI_BASE_URL}/assistant/{assistant_id}",
            headers=headers,
            json=alt_config
        )
        
        if alt_response.status_code == 200:
            print(f"✅ Updated {assistant_name} using toolConfig")
            return True
        else:
            print(f"   Alternative approach also failed: {alt_response.status_code}")
            return False

def main():
    print("\n🔗 VAPI Tool Linking Script")
    print("=" * 70)
    
    # Get all available tools
    tool_map = list_tools()
    
    if not tool_map:
        print("❌ No tools found. Please run update_functions.py first.")
        return
    
    print("\n" + "=" * 70)
    print("🔄 Linking Tools to Assistants")
    print("=" * 70)
    
    # Sales Agent tools
    sales_agent_id = "edc2ad98-c1a0-4461-b963-64800fca1832"
    sales_tools = [
        "searchKnowledge",
        "detectPersona",
        "calculateTrust",
        "handleObjection",
        "bookAppointment"
    ]
    
    print(f"\n📱 Sales Agent Tools: {', '.join(sales_tools)}")
    update_assistant_with_tools(sales_agent_id, "CLP Sales Specialist", sales_tools, tool_map)
    
    # Expert Agent tools
    expert_agent_id = "91b07fe0-4149-43fc-9cb3-fc4a24622e4f"
    expert_tools = [
        "searchKnowledge",
        "calculateROI",
        "qualifierNetworkAnalysis",
        "scheduleConsultation"
    ]
    
    print(f"\n📱 Expert Agent Tools: {', '.join(expert_tools)}")
    update_assistant_with_tools(expert_agent_id, "CLP Expert Consultant", expert_tools, tool_map)
    
    print("\n" + "=" * 70)
    print("📌 Important Notes:")
    print("=" * 70)
    print("""
The custom tools are now created and available in VAPI.

To link them to your assistants:
1. Go to https://dashboard.vapi.ai/assistants
2. Edit each assistant
3. In the "Tools" or "Functions" section:
   - Remove the old inline functions
   - Add the custom tools by name:
     
     Sales Agent needs:
     • searchKnowledge
     • detectPersona
     • calculateTrust
     • handleObjection
     • bookAppointment
     
     Expert Agent needs:
     • searchKnowledge
     • calculateROI
     • qualifierNetworkAnalysis
     • scheduleConsultation

4. Save the changes

The tools are configured to route to your webhook at:
https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook
    """)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Check assistant configurations to see their webhook settings
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

def check_assistant_config(assistant_id: str, name: str):
    """Check detailed assistant configuration"""
    
    response = requests.get(
        f"{VAPI_BASE_URL}/assistant/{assistant_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        config = response.json()
        print(f"\n{'='*70}")
        print(f"📱 {name}")
        print(f"ID: {assistant_id}")
        print(f"{'='*70}")
        
        # Check main serverUrl
        print(f"\n🔗 Main Webhook Configuration:")
        print(f"   serverUrl: {config.get('serverUrl', 'NOT SET')}")
        print(f"   serverUrlSecret: {'SET' if config.get('serverUrlSecret') else 'NOT SET'}")
        
        # Check functions
        functions = config.get('functions', [])
        if functions:
            print(f"\n📋 Functions ({len(functions)}):")
            for func in functions:
                print(f"\n   {func.get('name', 'Unnamed')}:")
                print(f"      serverUrl: {func.get('serverUrl', 'INHERIT FROM MAIN')}")
                print(f"      description: {func.get('description', 'No description')[:50]}...")
        
        # Check tools/toolIds
        tool_ids = config.get('toolIds', [])
        if tool_ids:
            print(f"\n🔧 Tool IDs: {tool_ids}")
        
        # Check if using custom tools
        tools = config.get('tools', [])
        if tools:
            print(f"\n🔧 Tools: {tools}")
            
        return config
    else:
        print(f"❌ Failed to get {name}: {response.status_code}")
        return None

def check_tool_config(tool_name: str):
    """Check specific tool configuration"""
    
    # Get all tools
    response = requests.get(f"{VAPI_BASE_URL}/tool", headers=headers)
    
    if response.status_code == 200:
        tools = response.json()
        for tool in tools:
            func = tool.get("function", {})
            if func.get("name") == tool_name:
                print(f"\n🔧 Tool: {tool_name}")
                print(f"   ID: {tool.get('id')}")
                server = tool.get("server", {})
                print(f"   Server URL: {server.get('url', 'NOT SET')}")
                print(f"   Server Secret: {'SET' if server.get('secret') else 'NOT SET'}")
                return tool
        print(f"❌ Tool '{tool_name}' not found")
    else:
        print(f"❌ Failed to list tools: {response.status_code}")
    
    return None

def main():
    print("\n🚀 VAPI Configuration Check")
    print("=" * 70)
    
    # Check our two main assistants
    sales_id = "edc2ad98-c1a0-4461-b963-64800fca1832"
    expert_id = "91b07fe0-4149-43fc-9cb3-fc4a24622e4f"
    
    print("\n1️⃣ Checking Sales Assistant...")
    sales_config = check_assistant_config(sales_id, "CLP Sales Specialist")
    
    print("\n2️⃣ Checking Expert Assistant...")
    expert_config = check_assistant_config(expert_id, "CLP Expert Consultant")
    
    print("\n3️⃣ Checking searchKnowledge Tool...")
    search_tool = check_tool_config("searchKnowledge")
    
    print("\n" + "="*70)
    print("📌 Analysis:")
    print("="*70)
    
    # Check for configuration issues
    issues = []
    
    if sales_config:
        main_url = sales_config.get('serverUrl', '')
        if '/vapi/webhook' in main_url:
            issues.append("Sales assistant has main serverUrl pointing to /vapi/webhook")
        if '/vapi-enhanced/webhook' not in main_url and not main_url == '':
            issues.append(f"Sales assistant main serverUrl: {main_url}")
    
    if expert_config:
        main_url = expert_config.get('serverUrl', '')
        if '/vapi/webhook' in main_url:
            issues.append("Expert assistant has main serverUrl pointing to /vapi/webhook")
        if '/vapi-enhanced/webhook' not in main_url and not main_url == '':
            issues.append(f"Expert assistant main serverUrl: {main_url}")
    
    if search_tool:
        server = search_tool.get("server", {})
        tool_url = server.get("url", "")
        if "/vapi/webhook" in tool_url:
            issues.append("searchKnowledge tool is pointing to /vapi/webhook instead of /vapi-enhanced/webhook")
    
    if issues:
        print("\n⚠️ Issues Found:")
        for issue in issues:
            print(f"   - {issue}")
        
        print("\n🔧 Solution:")
        print("   1. Update assistant serverUrl to: https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook")
        print("   2. Or update searchKnowledge tool URL to: https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook")
    else:
        print("\n✅ Configuration looks correct!")
        print("   All webhooks should be pointing to /vapi-enhanced/webhook")
    
    print("\n💡 Note:")
    print("   - /vapi/webhook = Basic webhook (returns 422 for function calls)")
    print("   - /vapi-enhanced/webhook = Enhanced webhook with scoring (handles all functions)")

if __name__ == "__main__":
    main()
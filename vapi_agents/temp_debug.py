#!/usr/bin/env python3
"""
Temporarily point a tool to debug endpoint to see the request structure
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
DEBUG_WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-debug/webhook"
NORMAL_WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

def update_tool_url(tool_name: str, new_url: str):
    """Update a specific tool's webhook URL"""
    
    # Get all tools
    response = requests.get(f"{VAPI_BASE_URL}/tool", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to list tools: {response.status_code}")
        return False
    
    tools = response.json()
    
    for tool in tools:
        func = tool.get("function", {})
        if func.get("name") == tool_name:
            tool_id = tool.get("id")
            print(f"Found {tool_name} (ID: {tool_id})")
            
            # Update the tool
            update_response = requests.patch(
                f"{VAPI_BASE_URL}/tool/{tool_id}",
                headers=headers,
                json={"server": {"url": new_url}}
            )
            
            if update_response.status_code == 200:
                print(f"✅ Updated {tool_name} to use: {new_url}")
                return True
            else:
                print(f"❌ Failed to update: {update_response.status_code}")
                print(update_response.text)
                return False
    
    print(f"❌ Tool '{tool_name}' not found")
    return False

def main():
    print("\n🔍 VAPI Debug Setup")
    print("=" * 70)
    
    action = input("\nEnter 'debug' to enable debug mode or 'normal' to restore: ").strip().lower()
    
    if action == "debug":
        print("\n🐛 Enabling debug mode for searchKnowledge...")
        if update_tool_url("searchKnowledge", DEBUG_WEBHOOK_URL):
            print("\n✅ Debug mode enabled!")
            print("\nNow when you call VAPI and trigger searchKnowledge:")
            print("1. Check Railway logs for detailed request structure")
            print("2. Look for 'VAPI Request Received' and 'Request Structure' logs")
            print("3. This will show exactly what VAPI is sending")
            print("\nTest with: 'What are the requirements in Georgia?'")
    
    elif action == "normal":
        print("\n🔧 Restoring normal webhook...")
        if update_tool_url("searchKnowledge", NORMAL_WEBHOOK_URL):
            print("\n✅ Normal mode restored!")
    
    else:
        print("❌ Invalid action. Use 'debug' or 'normal'")

if __name__ == "__main__":
    main()
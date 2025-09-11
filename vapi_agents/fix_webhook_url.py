#!/usr/bin/env python3
"""
Fix webhook URLs for VAPI tools
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

# The correct webhook URL (using /vapi/webhook endpoint)
CORRECT_WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

def list_and_fix_tools():
    """List all tools and fix their webhook URLs"""
    
    # Get all tools
    response = requests.get(
        f"{VAPI_BASE_URL}/tool",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to list tools: {response.status_code}")
        return
    
    tools = response.json()
    print(f"\n📋 Found {len(tools)} tools to check...")
    print("=" * 70)
    
    tools_to_fix = []
    
    for tool in tools:
        tool_id = tool.get("id")
        func = tool.get("function", {})
        name = func.get("name", "Unnamed")
        server = tool.get("server", {})
        current_url = server.get("url", "")
        
        print(f"\nTool: {name}")
        print(f"ID: {tool_id}")
        print(f"Current URL: {current_url}")
        
        # Check if URL needs fixing
        if current_url and "vapi-enhanced" in current_url:
            tools_to_fix.append({
                "id": tool_id,
                "name": name,
                "old_url": current_url
            })
            print("⚠️  Needs fixing (using vapi-enhanced instead of vapi)")
        elif current_url == CORRECT_WEBHOOK_URL:
            print("✅ URL is correct")
        else:
            print("❓ Different URL configured")
    
    # Fix tools with wrong URL
    if tools_to_fix:
        print("\n" + "=" * 70)
        print(f"🔧 Fixing {len(tools_to_fix)} tools...")
        print("=" * 70)
        
        for tool_info in tools_to_fix:
            # Get the full tool config
            get_response = requests.get(
                f"{VAPI_BASE_URL}/tool/{tool_info['id']}",
                headers=headers
            )
            
            if get_response.status_code != 200:
                print(f"❌ Failed to get tool {tool_info['name']}")
                continue
            
            tool_config = get_response.json()
            
            # Update the server URL
            if "server" not in tool_config:
                tool_config["server"] = {}
            tool_config["server"]["url"] = CORRECT_WEBHOOK_URL
            
            # Update the tool
            update_response = requests.patch(
                f"{VAPI_BASE_URL}/tool/{tool_info['id']}",
                headers=headers,
                json={"server": {"url": CORRECT_WEBHOOK_URL}}
            )
            
            if update_response.status_code == 200:
                print(f"✅ Fixed {tool_info['name']}: {CORRECT_WEBHOOK_URL}")
            else:
                print(f"❌ Failed to fix {tool_info['name']}: {update_response.status_code}")
                print(f"   {update_response.text}")
    else:
        print("\n✅ All tools have correct webhook URLs!")
    
    print("\n" + "=" * 70)
    print("📌 Summary")
    print("=" * 70)
    print(f"Correct webhook URL: {CORRECT_WEBHOOK_URL}")
    print("\nThis URL routes to the /vapi/webhook endpoint which:")
    print("1. Handles all function calls")
    print("2. Searches the 469-entry knowledge base")
    print("3. Implements conversation scoring")
    print("4. Returns appropriate responses")

def test_webhook():
    """Test the webhook endpoint directly"""
    print("\n" + "=" * 70)
    print("🧪 Testing Webhook Endpoint")
    print("=" * 70)
    
    test_payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": "Georgia requirements",
                    "state": "GA"
                }
            }
        },
        "call": {
            "id": "test-call-123",
            "assistantId": "test-assistant"
        }
    }
    
    # Add webhook secret if available
    test_headers = {"Content-Type": "application/json"}
    webhook_secret = os.getenv("VAPI_WEBHOOK_SECRET")
    if webhook_secret:
        test_headers["x-vapi-secret"] = webhook_secret
    
    print(f"Testing: {CORRECT_WEBHOOK_URL}")
    print(f"Payload: searchKnowledge('Georgia requirements')")
    
    try:
        response = requests.post(
            CORRECT_WEBHOOK_URL,
            headers=test_headers,
            json=test_payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Webhook is working!")
            result = response.json()
            if "result" in result:
                print(f"Response: {result['result'].get('answer', 'No answer')[:200]}...")
        else:
            print(f"❌ Webhook returned error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Failed to test webhook: {e}")

if __name__ == "__main__":
    print("\n🚀 VAPI Webhook URL Fixer")
    print("=" * 70)
    
    list_and_fix_tools()
    test_webhook()
    
    print("\n✅ Done! Your tools should now work with VAPI calls.")
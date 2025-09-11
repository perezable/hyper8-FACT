#!/usr/bin/env python3
"""
List all VAPI assistants to verify creation
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

if not VAPI_API_KEY:
    print("❌ Error: VAPI_API_KEY not found in .env")
    exit(1)

headers = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json"
}

def list_assistants():
    """List all assistants in VAPI account"""
    
    response = requests.get(
        f"{VAPI_BASE_URL}/assistant",
        headers=headers
    )
    
    if response.status_code == 200:
        assistants = response.json()
        print(f"\n📋 Found {len(assistants)} assistants in your VAPI account:\n")
        print("=" * 60)
        
        for assistant in assistants:
            print(f"Name: {assistant.get('name', 'Unnamed')}")
            print(f"ID: {assistant.get('id')}")
            print(f"Created: {assistant.get('createdAt', 'Unknown')}")
            print(f"Model: {assistant.get('model', {}).get('model', 'Unknown')}")
            
            # Check if it's one of our agents
            if "CLP" in assistant.get('name', ''):
                print("✅ This is one of our CLP agents!")
            
            print("-" * 60)
        
        return assistants
    else:
        print(f"❌ Failed to list assistants: {response.status_code}")
        print(response.text)
        return []

def check_specific_ids():
    """Check if our specific agent IDs exist"""
    
    agent_ids = [
        "edc2ad98-c1a0-4461-b963-64800fca1832",  # Sales Agent
        "91b07fe0-4149-43fc-9cb3-fc4a24622e4f"   # Expert Agent
    ]
    
    print("\n🔍 Checking for our specific agent IDs...")
    print("=" * 60)
    
    for agent_id in agent_ids:
        response = requests.get(
            f"{VAPI_BASE_URL}/assistant/{agent_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            assistant = response.json()
            print(f"✅ Found: {assistant.get('name')} (ID: {agent_id})")
        else:
            print(f"❌ Not found: {agent_id}")
            print(f"   Status: {response.status_code}")

if __name__ == "__main__":
    print("\n🚀 VAPI Assistant Verification")
    print("=" * 60)
    
    # List all assistants
    assistants = list_assistants()
    
    # Check specific IDs
    check_specific_ids()
    
    print("\n💡 If the agents aren't showing:")
    print("   1. Check you're using the correct VAPI account")
    print("   2. Verify the API key matches your dashboard")
    print("   3. Try refreshing your VAPI dashboard")
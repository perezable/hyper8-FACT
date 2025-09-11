#!/usr/bin/env python3
"""
Show detailed function configurations for VAPI agents
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

def get_agent_functions(agent_id: str, agent_name: str):
    """Get detailed function configuration for an agent"""
    
    response = requests.get(
        f"{VAPI_BASE_URL}/assistant/{agent_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        assistant = response.json()
        print(f"\n{'='*70}")
        print(f"📱 {agent_name}")
        print(f"ID: {agent_id}")
        print(f"{'='*70}")
        
        # Check webhook configuration
        print(f"\n🔗 Webhook Configuration:")
        print(f"   URL: {assistant.get('serverUrl', 'Not configured')}")
        print(f"   Secret: {'✅ Configured' if assistant.get('serverUrlSecret') else '❌ Not set'}")
        
        # Show functions
        functions = assistant.get('functions', [])
        if functions:
            print(f"\n📋 Functions ({len(functions)} total):\n")
            for i, func in enumerate(functions, 1):
                print(f"{i}. {func.get('name', 'Unnamed')}")
                print(f"   Description: {func.get('description', 'No description')}")
                print(f"   Server URL: {func.get('serverUrl', 'Not set')}")
                
                # Show parameters
                params = func.get('parameters', {})
                if params:
                    props = params.get('properties', {})
                    required = params.get('required', [])
                    print(f"   Parameters:")
                    for param_name, param_info in props.items():
                        req_marker = "✓ Required" if param_name in required else "Optional"
                        print(f"      - {param_name} ({param_info.get('type', 'unknown')}) [{req_marker}]")
                        if param_info.get('description'):
                            print(f"        {param_info['description']}")
                        if param_info.get('enum'):
                            print(f"        Options: {', '.join(param_info['enum'])}")
                
                print()
        else:
            print("\n❌ No functions configured")
        
        # Show model configuration
        model_config = assistant.get('model', {})
        print(f"\n🤖 Model Configuration:")
        print(f"   Provider: {model_config.get('provider', 'Not set')}")
        print(f"   Model: {model_config.get('model', 'Not set')}")
        print(f"   Temperature: {model_config.get('temperature', 'Not set')}")
        
        return assistant
    else:
        print(f"❌ Failed to get agent details: {response.status_code}")
        return None

def main():
    print("\n🚀 VAPI Function Configuration Report")
    print("=" * 70)
    
    # Our agent IDs
    agents = [
        ("edc2ad98-c1a0-4461-b963-64800fca1832", "CLP Sales Specialist"),
        ("91b07fe0-4149-43fc-9cb3-fc4a24622e4f", "CLP Expert Consultant")
    ]
    
    for agent_id, agent_name in agents:
        get_agent_functions(agent_id, agent_name)
    
    print("\n" + "="*70)
    print("📌 Function Integration Notes:")
    print("="*70)
    print("""
1. searchKnowledge Function:
   - Routes to: Your webhook endpoint
   - Purpose: Searches the 469-entry knowledge base
   - Returns: Answer with confidence score and metadata
   
2. detectPersona Function:
   - Routes to: Your webhook endpoint
   - Purpose: Identifies caller type (Veteran, Newcomer, etc.)
   - Returns: Persona type and confidence score
   
3. calculateTrust Function:
   - Routes to: Your webhook endpoint
   - Purpose: Tracks conversation trust score (0-100)
   - Returns: Current trust level and journey stage
   
4. handleObjection Function:
   - Routes to: Your webhook endpoint
   - Purpose: Provides tailored objection responses
   - Returns: Specific rebuttal based on objection type
   
5. bookAppointment Function:
   - Routes to: Your webhook endpoint
   - Purpose: Schedules consultations
   - Returns: Confirmation and next steps
   
6. calculateROI Function:
   - Routes to: Your webhook endpoint
   - Purpose: Computes specific ROI for customer
   - Returns: Detailed ROI breakdown
   
7. qualifierNetworkAnalysis Function:
   - Routes to: Your webhook endpoint
   - Purpose: Analyzes $3k-$6k/month opportunity
   - Returns: Qualification status and potential earnings
   
8. scheduleConsultation Function:
   - Routes to: Your webhook endpoint
   - Purpose: Books expert consultation
   - Returns: Scheduled time and preparation materials
    """)
    
    print("\n💡 To test the functions:")
    print("   1. Assign a phone number to the Sales Specialist")
    print("   2. Call and say: 'What are the requirements in Georgia?'")
    print("   3. The agent will use searchKnowledge to query your database")
    print("   4. Monitor webhook logs to see function calls in action")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Stop guessing. Check what's actually configured in VAPI.
Get the real state of the assistant and see what functions it has.
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv()

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "c49631b4-2f8f-40b3-9ce1-22f731879fb9")
MAIN_ROUTER_ID = "686ead20-ceb5-45b3-a224-4ddb62f58bda"

async def get_actual_configuration():
    """Get the ACTUAL current configuration from VAPI."""
    
    print("🔍 CHECKING ACTUAL VAPI CONFIGURATION")
    print("=" * 70)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        # Get the assistant configuration
        async with session.get(
            f"https://api.vapi.ai/assistant/{MAIN_ROUTER_ID}",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                print("📋 MAIN ROUTER ACTUAL STATE:")
                print("-" * 70)
                
                # Check functions
                functions = data.get("functions", [])
                print(f"\n1. FUNCTIONS ({len(functions)} total):")
                for func in functions:
                    print(f"   - {func['name']}")
                    if func['name'] == 'transferCall':
                        print(f"     Parameters: {json.dumps(func.get('parameters', {}), indent=6)}")
                
                # Check if transferCall is in model tools
                model_tools = data.get("model", {}).get("tools", [])
                print(f"\n2. MODEL TOOLS ({len(model_tools)} total):")
                for tool in model_tools:
                    if tool.get("function", {}).get("name") == "transferCall":
                        print(f"   - Found transferCall in model tools")
                
                # Check system prompt (first 200 chars)
                messages = data.get("model", {}).get("messages", [])
                if messages:
                    prompt = messages[0].get("content", "")[:200]
                    print(f"\n3. SYSTEM PROMPT (first 200 chars):")
                    print(f"   {prompt}...")
                
                # Check other settings
                print(f"\n4. OTHER SETTINGS:")
                print(f"   - endCallFunctionEnabled: {data.get('endCallFunctionEnabled')}")
                print(f"   - firstMessage: {data.get('firstMessage', 'None')[:50]}")
                print(f"   - Model: {data.get('model', {}).get('model')}")
                print(f"   - Provider: {data.get('model', {}).get('provider')}")
                
                # Save full config for analysis
                with open("actual_router_config.json", "w") as f:
                    json.dump(data, f, indent=2)
                print(f"\n   Full config saved to: actual_router_config.json")
                
                return data

async def check_squad_configuration():
    """Check the squad configuration."""
    
    print("\n" + "=" * 70)
    print("🔍 CHECKING SQUAD CONFIGURATION")
    print("-" * 70)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.vapi.ai/squad/ca86111f-582f-4ba0-840f-e7a82dc0967d",
            headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                
                print(f"\n1. SQUAD MEMBERS ({len(data.get('members', []))} total):")
                for i, member in enumerate(data.get("members", [])):
                    assistant_id = member.get("assistantId", "")
                    destinations = member.get("assistantDestinations", [])
                    print(f"\n   Member {i+1}: {assistant_id[:8]}...")
                    print(f"   Destinations: {len(destinations)}")
                    for dest in destinations[:2]:  # Show first 2
                        print(f"     - Type: {dest.get('type')}")
                        print(f"       Name: {dest.get('assistantName')}")
                        print(f"       Message: '{dest.get('message', 'NOT SET')}'")
                
                # Save squad config
                with open("actual_squad_config.json", "w") as f:
                    json.dump(data, f, indent=2)
                print(f"\n   Full squad config saved to: actual_squad_config.json")
                
                return data

async def check_recent_calls():
    """Check recent call logs to see what's happening."""
    
    print("\n" + "=" * 70)
    print("🔍 CHECKING RECENT CALLS")
    print("-" * 70)
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.vapi.ai/call",
            headers=headers,
            params={"assistantId": MAIN_ROUTER_ID, "limit": 3}
        ) as response:
            if response.status == 200:
                calls = await response.json()
                
                if calls:
                    print(f"\nFound {len(calls)} recent call(s)")
                    for i, call in enumerate(calls[:1]):  # Just show latest
                        print(f"\n   Call {i+1}:")
                        print(f"   - ID: {call.get('id')}")
                        print(f"   - Status: {call.get('status')}")
                        print(f"   - Duration: {call.get('duration')} seconds")
                        
                        # Check for transfer attempts in messages
                        messages = call.get("messages", [])
                        for msg in messages[-5:]:  # Last 5 messages
                            if "transfer" in str(msg).lower():
                                print(f"\n   Transfer-related message found:")
                                print(f"   {msg.get('role')}: {msg.get('content', '')[:100]}")
                else:
                    print("\nNo recent calls found")

async def main():
    """Main execution."""
    
    print("STOP GUESSING - LET'S SEE WHAT'S ACTUALLY CONFIGURED")
    print("=" * 70)
    
    # Get actual configurations
    router_config = await get_actual_configuration()
    squad_config = await check_squad_configuration()
    await check_recent_calls()
    
    print("\n" + "=" * 70)
    print("📊 ANALYSIS:")
    print("-" * 70)
    
    # Check if transferCall is properly configured
    has_transfer_func = any(
        f["name"] == "transferCall" 
        for f in router_config.get("functions", [])
    )
    
    print(f"\n1. Router has transferCall function: {has_transfer_func}")
    
    if has_transfer_func:
        print("   BUT the assistant is speaking it instead of executing it.")
        print("\n   POSSIBLE ISSUES:")
        print("   - VAPI might need the function configured differently")
        print("   - The assistant might not have permission to transfer")
        print("   - Squad transfer might work differently than documented")
        print("   - May need to contact VAPI support for clarification")
    
    print("\n2. RECOMMENDATION:")
    print("   Since the assistant speaks 'Transfer call CLP veteran support'")
    print("   it seems to understand the intent but isn't executing the function.")
    print("\n   This suggests a VAPI platform issue or undocumented requirement.")
    print("   Consider contacting VAPI support with these findings.")

if __name__ == "__main__":
    asyncio.run(main())
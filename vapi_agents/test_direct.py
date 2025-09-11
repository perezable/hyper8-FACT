#!/usr/bin/env python3
"""
Direct test of webhook functions without signature verification
"""

import os
import json
import requests
from datetime import datetime

# Test the debug endpoint which doesn't require signature
WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-debug/webhook"

def test_searchKnowledge():
    """Test searchKnowledge function directly"""
    
    payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "test-123",
                    "type": "function",
                    "function": {
                        "name": "searchKnowledge",
                        "arguments": {
                            "query": "Georgia contractor license requirements",
                            "state": "GA"
                        }
                    }
                }
            ]
        }
    }
    
    print("\n🧪 Testing searchKnowledge function")
    print("-" * 50)
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful")
            print(f"Response: {json.dumps(result, indent=2)[:1000]}")
        else:
            print(f"❌ Request failed: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def check_railway_health():
    """Check if Railway deployment is healthy"""
    
    health_url = "https://hyper8-fact-fact-system.up.railway.app/health"
    
    print("\n🏥 Checking Railway deployment health")
    print("-" * 50)
    
    try:
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Deployment is healthy")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Version: {health_data.get('version', 'unknown')}")
            print(f"   Initialized: {health_data.get('initialized', False)}")
            
            if 'entries_count' in health_data:
                print(f"   Knowledge Base Entries: {health_data['entries_count']}")
        else:
            print(f"⚠️  Health check returned: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")


def list_available_endpoints():
    """List available API endpoints"""
    
    print("\n📋 Available Endpoints")
    print("-" * 50)
    
    endpoints = [
        "/health",
        "/vapi/webhook",
        "/vapi-enhanced/webhook",
        "/vapi-debug/webhook",
        "/vapi-simple/webhook",
        "/api/v1/knowledge/entries",
        "/debug/cache/status"
    ]
    
    base_url = "https://hyper8-fact-fact-system.up.railway.app"
    
    for endpoint in endpoints:
        url = base_url + endpoint
        try:
            response = requests.head(url, timeout=2)
            if response.status_code in [200, 401, 405, 422]:
                print(f"✅ {endpoint} - Available")
            else:
                print(f"❌ {endpoint} - Status: {response.status_code}")
        except:
            print(f"❌ {endpoint} - Not responding")


def main():
    print("\n🚀 Direct Webhook Test")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Check health first
    check_railway_health()
    
    # List endpoints
    list_available_endpoints()
    
    # Test searchKnowledge
    test_searchKnowledge()
    
    print("\n" + "=" * 60)
    print("💡 Notes:")
    print("- The debug endpoint doesn't require signature verification")
    print("- If searchKnowledge returns data, the webhook is working")
    print("- Check Railway logs for detailed error information")


if __name__ == "__main__":
    main()
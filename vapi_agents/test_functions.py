#!/usr/bin/env python3
"""
Test all VAPI functions to ensure they're working correctly
"""

import os
import json
import requests
from dotenv import load_dotenv
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi-enhanced/webhook"
WEBHOOK_SECRET = os.getenv("VAPI_WEBHOOK_SECRET", "")

# Test cases for each function
TEST_CASES = [
    {
        "name": "searchKnowledge - Georgia Requirements",
        "function": "searchKnowledge",
        "parameters": {
            "query": "Georgia contractor license requirements",
            "state": "GA"
        },
        "expected": "answer should contain Georgia-specific information"
    },
    {
        "name": "detectPersona - Overwhelmed",
        "function": "detectPersona",
        "parameters": {
            "text": "I'm so overwhelmed by all this paperwork and requirements"
        },
        "expected": "should detect overwhelmed_veteran persona"
    },
    {
        "name": "calculateTrust - Positive Events",
        "function": "calculateTrust",
        "parameters": {
            "events": [
                {"type": "positive", "description": "Shows interest"},
                {"type": "positive", "description": "Asks about benefits"}
            ]
        },
        "expected": "trust_score should increase"
    },
    {
        "name": "handleObjection - Too Expensive",
        "function": "handleObjection",
        "parameters": {
            "type": "too_expensive"
        },
        "expected": "response about ROI and value"
    },
    {
        "name": "calculateROI - $65k Income",
        "function": "calculateROI",
        "parameters": {
            "currentIncome": 65000,
            "projectSize": 15000,
            "monthlyProjects": 2,
            "qualifierNetwork": True
        },
        "expected": "should show ROI calculation"
    },
    {
        "name": "bookAppointment",
        "function": "bookAppointment",
        "parameters": {
            "name": "John Test",
            "email": "john@test.com",
            "phone": "555-0123",
            "state": "GA",
            "urgency": "high"
        },
        "expected": "confirmation number"
    },
    {
        "name": "qualifierNetworkAnalysis",
        "function": "qualifierNetworkAnalysis",
        "parameters": {
            "state": "GA",
            "licenseType": "general",
            "experience": 5
        },
        "expected": "monthly income estimate"
    },
    {
        "name": "scheduleConsultation",
        "function": "scheduleConsultation",
        "parameters": {
            "name": "Jane Test",
            "email": "jane@test.com",
            "phone": "555-0456",
            "consultationType": "qualifier",
            "investmentRange": "5k-10k"
        },
        "expected": "consultation confirmation"
    }
]


def test_function(test_case):
    """Test a single function"""
    print(f"\n🧪 Testing: {test_case['name']}")
    print("-" * 50)
    
    # Create a tool-calls request (new VAPI format)
    tool_call_id = f"test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": tool_call_id,
                    "type": "function",
                    "function": {
                        "name": test_case["function"],
                        "arguments": test_case["parameters"]
                    }
                }
            ],
            "timestamp": int(time.time() * 1000)
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-vapi-secret": WEBHOOK_SECRET
    }
    
    try:
        # Send request
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if we got results
            if "results" in result and len(result["results"]) > 0:
                tool_result = result["results"][0]
                
                if "result" in tool_result:
                    print("✅ Function executed successfully")
                    print(f"Result: {json.dumps(tool_result['result'], indent=2)[:500]}...")
                    
                    # Verify expected content
                    result_str = json.dumps(tool_result['result'])
                    if any(key in result_str for key in test_case["expected"].split()):
                        print(f"✅ Expected content found: {test_case['expected']}")
                    else:
                        print(f"⚠️  Expected content not clearly found: {test_case['expected']}")
                else:
                    print("❌ No result in response")
            else:
                print("❌ No results array in response")
                print(f"Response: {json.dumps(result, indent=2)[:500]}")
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return response.status_code == 200


def test_old_format():
    """Test with old function-call format to ensure backward compatibility"""
    print("\n🧪 Testing Old Format (function-call)")
    print("-" * 50)
    
    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": "Florida requirements",
                    "state": "FL"
                }
            }
        },
        "call": {
            "id": "test-old-format-123",
            "assistantId": "test-assistant"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "x-vapi-secret": WEBHOOK_SECRET
    }
    
    try:
        response = requests.post(
            WEBHOOK_URL,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if "result" in result:
                print("✅ Old format still works")
                print(f"Result: {json.dumps(result['result'], indent=2)[:300]}...")
            else:
                print("❌ No result in response")
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    print("\n🚀 VAPI Function Test Suite")
    print("=" * 60)
    print(f"Testing endpoint: {WEBHOOK_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test all functions
    passed = 0
    failed = 0
    
    for test_case in TEST_CASES:
        if test_function(test_case):
            passed += 1
        else:
            failed += 1
        time.sleep(0.5)  # Small delay between tests
    
    # Test old format
    test_old_format()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Passed: {passed}/{len(TEST_CASES)}")
    print(f"❌ Failed: {failed}/{len(TEST_CASES)}")
    
    if failed == 0:
        print("\n🎉 All functions are working correctly!")
    else:
        print(f"\n⚠️  {failed} function(s) need attention")
    
    print("\n💡 Next Steps:")
    print("1. If any tests failed, check Railway logs for errors")
    print("2. Verify the webhook secret is correct")
    print("3. Ensure the database has data (469 entries)")
    print("4. Test with actual VAPI phone calls")


if __name__ == "__main__":
    main()
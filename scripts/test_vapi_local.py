#!/usr/bin/env python3
"""
Local VAPI Integration Test
Tests VAPI webhook integration with local FACT server.
Run the server first: python src/web_server.py
"""

import asyncio
import json
import hmac
import hashlib
import time
from typing import Dict, Any
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, "src")

# Import test data
from data.sample_data import KNOWLEDGE_BASE_DATA

# Configuration
LOCAL_URL = "http://localhost:8000"
VAPI_SECRET = "test-vapi-secret-key"


def generate_hmac_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature for VAPI webhook authentication."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def create_vapi_webhook_payload(query: str, function_name: str = "searchKnowledge") -> Dict[str, Any]:
    """Create a VAPI webhook payload with searchKnowledge function call."""
    return {
        "message": {
            "type": "function-call",
            "call": {
                "id": f"call_{int(time.time() * 1000)}",
                "orgId": "org_test_123",
                "createdAt": datetime.now().isoformat() + "Z",
                "phoneNumber": {
                    "number": "+14155551234",
                    "country": "US"
                }
            },
            "functionCall": {
                "name": function_name,
                "parameters": {
                    "query": query,
                    "limit": 3
                }
            },
            "customer": {
                "number": "+14155555678"
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
    }


async def test_vapi_locally():
    """Test VAPI integration with local server."""
    print("=" * 70)
    print("VAPI Local Integration Test")
    print("=" * 70)
    print(f"Testing against: {LOCAL_URL}")
    print(f"Total knowledge entries: {len(KNOWLEDGE_BASE_DATA)}")
    
    # Import httpx for async HTTP
    try:
        import httpx
    except ImportError:
        print("\nERROR: httpx not installed. Run: pip install httpx")
        return
    
    # Test queries that voice agents might ask
    test_scenarios = [
        {
            "name": "Basic Requirements",
            "query": "What are the requirements for a contractor license in Georgia?",
            "expected_in_answer": ["Georgia", "requirements"]
        },
        {
            "name": "Cost Question",
            "query": "How much does a contractor license cost?",
            "expected_in_answer": ["cost", "$"]
        },
        {
            "name": "ROI Query",
            "query": "What's the ROI on getting licensed?",
            "expected_in_answer": ["return", "investment", "project"]
        },
        {
            "name": "Exam Failure",
            "query": "What if I fail the contractor exam?",
            "expected_in_answer": ["retake", "exam", "fail"]
        },
        {
            "name": "Timeline",
            "query": "How long does licensing take?",
            "expected_in_answer": ["time", "weeks", "days"]
        }
    ]
    
    print("\nChecking server health...")
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        # Check health
        try:
            health_response = await client.get(f"{LOCAL_URL}/health")
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"✓ Server is healthy")
                print(f"  Status: {health_data.get('status')}")
                print(f"  Enhanced Retriever: {health_data.get('metrics', {}).get('enhanced_retriever', False)}")
            else:
                print(f"✗ Server unhealthy or not running (status {health_response.status_code})")
                print("\nPlease start the server first:")
                print("  python src/web_server.py")
                return
        except Exception as e:
            print(f"✗ Cannot connect to server: {e}")
            print("\nPlease start the server first:")
            print("  python src/web_server.py")
            return
        
        print("\n" + "-" * 70)
        print("Testing VAPI Webhook Calls")
        print("-" * 70)
        
        results = []
        for scenario in test_scenarios:
            print(f"\nTest: {scenario['name']}")
            print(f"Query: '{scenario['query']}'")
            
            # Create VAPI payload
            payload = create_vapi_webhook_payload(scenario['query'])
            payload_str = json.dumps(payload, separators=(',', ':'))
            
            # Generate HMAC signature
            signature = generate_hmac_signature(payload_str, VAPI_SECRET)
            
            # Set headers as VAPI would
            headers = {
                "Content-Type": "application/json",
                "x-vapi-signature": signature,
                "x-vapi-timestamp": str(int(time.time())),
                "User-Agent": "VAPI-Webhook/1.0"
            }
            
            try:
                start_time = time.time()
                response = await client.post(
                    f"{LOCAL_URL}/vapi/webhook",
                    json=payload,
                    headers=headers
                )
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("results"):
                        result = data["results"][0]
                        print(f"✓ Success (Status: {response.status_code}, Time: {response_time:.0f}ms)")
                        print(f"  Found: {result['question'][:60]}...")
                        print(f"  Answer: {result['answer'][:100]}...")
                        
                        # Check metadata if available
                        if 'metadata' in result:
                            meta = result['metadata']
                            print(f"  Score: {meta.get('score', 0):.2f}")
                            print(f"  Confidence: {meta.get('confidence', 0):.1%}")
                            print(f"  Match Type: {meta.get('match_type', 'unknown')}")
                        
                        # Validate expected content
                        answer_lower = result['answer'].lower()
                        matched_keywords = [kw for kw in scenario['expected_in_answer'] 
                                          if kw.lower() in answer_lower]
                        
                        if matched_keywords:
                            print(f"  ✓ Contains expected keywords: {matched_keywords}")
                        else:
                            print(f"  ⚠ Missing expected keywords")
                        
                        results.append({
                            "scenario": scenario['name'],
                            "success": True,
                            "response_time": response_time,
                            "score": result.get('metadata', {}).get('score', 0)
                        })
                    else:
                        print(f"⚠ No results found")
                        results.append({
                            "scenario": scenario['name'],
                            "success": False,
                            "error": "No results"
                        })
                else:
                    print(f"✗ Failed (Status: {response.status_code})")
                    print(f"  Response: {response.text[:200]}")
                    results.append({
                        "scenario": scenario['name'],
                        "success": False,
                        "error": f"Status {response.status_code}"
                    })
                    
            except Exception as e:
                print(f"✗ Error: {e}")
                results.append({
                    "scenario": scenario['name'],
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        
        successful = sum(1 for r in results if r.get("success"))
        total = len(results)
        
        print(f"Total Tests: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success Rate: {(successful/total)*100:.1f}%")
        
        # Response time analysis
        response_times = [r.get("response_time", 0) for r in results if r.get("response_time")]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            print(f"\nAverage Response Time: {avg_time:.0f}ms")
            
            if avg_time < 100:
                print("  ✓ Excellent for real-time voice interactions")
            elif avg_time < 300:
                print("  ⚠ Acceptable for voice interactions")
            else:
                print("  ✗ May cause delays in voice conversations")
        
        # Show how to use with VAPI
        print("\n" + "=" * 70)
        print("How to Use with VAPI")
        print("=" * 70)
        print("\n1. In your VAPI assistant configuration, add a custom function:")
        print("""
{
  "name": "searchKnowledge",
  "description": "Search contractor licensing knowledge base",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The user's question about contractor licensing"
      },
      "limit": {
        "type": "integer",
        "description": "Maximum number of results to return",
        "default": 3
      }
    },
    "required": ["query"]
  }
}
""")
        
        print("\n2. Configure the webhook URL:")
        print(f"   Development: {LOCAL_URL}/vapi/webhook")
        print(f"   Production: https://your-railway-url.railway.app/vapi/webhook")
        
        print("\n3. Set the VAPI secret for HMAC authentication:")
        print(f"   Secret: {VAPI_SECRET}")
        
        print("\n4. In your VAPI assistant prompt, instruct it to use searchKnowledge:")
        print("""
"When users ask about contractor licensing, requirements, costs, or 
processes, use the searchKnowledge function to find accurate information 
from our knowledge base. Always search before providing an answer."
""")
        
        print("\n5. The system will learn from interactions:")
        print("   - Provide feedback via /training/feedback endpoint")
        print("   - System improves accuracy over time")
        print("   - Export/import training data between deployments")


async def main():
    """Run the local VAPI test."""
    await test_vapi_locally()
    
    print("\n" + "=" * 70)
    print("Next Steps")
    print("=" * 70)
    print("\n1. Deploy to Railway:")
    print("   railway up")
    print("\n2. Test Railway deployment:")
    print("   python scripts/test_vapi_integration.py")
    print("\n3. Configure VAPI with your Railway URL")
    print("\n4. Monitor and train the system:")
    print("   - Check /training/status for accuracy")
    print("   - Provide feedback to improve results")
    print("   - Export training data regularly")


if __name__ == "__main__":
    asyncio.run(main())
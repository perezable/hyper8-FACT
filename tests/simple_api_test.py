#!/usr/bin/env python3
"""
Simple API test with proper timeout handling
"""

import requests
import json
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

def test_single_query(question):
    """Test a single query with timeout"""
    try:
        response = requests.post(
            f"{RAILWAY_URL}/query",
            json={
                "query": question,
                "context": "Contractor licensing inquiry"
            },
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "question": question,
                "answer": data.get("response", data.get("answer", "")),
                "full_response": data
            }
        else:
            return {
                "success": False,
                "question": question,
                "error": f"HTTP {response.status_code}",
                "content": response.text
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "question": question,
            "error": "Request timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "question": question,
            "error": str(e)
        }

def main():
    print("\n" + "="*60)
    print("🔍 SIMPLE API TEST")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {RAILWAY_URL}")
    print()
    
    # Test a few key questions
    test_questions = [
        "What payment plans are available for the $4,995 fee?",
        "What's the cheapest state to get a contractor license?",
        "How much does a Florida contractor license cost?",
        "What states accept NASCLA?",
        "I don't know where to start - can you help?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Testing: {question}")
        print("-" * 40)
        
        result = test_single_query(question)
        
        if result["success"]:
            print(f"✅ Success!")
            print(f"Answer: {result['answer'][:200]}...")
            print(f"Full response: {json.dumps(result['full_response'], indent=2)}")
        else:
            print(f"❌ Failed: {result['error']}")
            if 'content' in result:
                print(f"Response content: {result['content'][:200]}")
    
    print("\n" + "="*60)
    print("Test completed")

if __name__ == "__main__":
    main()
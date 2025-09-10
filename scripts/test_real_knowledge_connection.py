#!/usr/bin/env python3
"""
Test that the VAPI webhook now uses real knowledge base data.
"""

import asyncio
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_knowledge_search():
    """Test the updated search_knowledge_base function."""
    
    print("🧪 Testing Real Knowledge Base Connection")
    print("=" * 70)
    
    # Import the updated function
    from src.api.vapi_webhook import search_knowledge_base
    
    # Test queries
    test_queries = [
        {
            "query": "California contractor license requirements",
            "state": "CA",
            "category": None
        },
        {
            "query": "How much does a contractor license cost",
            "state": None,
            "category": "financial_planning_roi"
        },
        {
            "query": "What exams do I need to take",
            "state": "TX",
            "category": "exam_preparation_testing"
        },
        {
            "query": "Georgia licensing",  # This used to return mock data
            "state": "GA",
            "category": None
        }
    ]
    
    print("\n📋 Testing Queries:")
    print("-" * 70)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {test['query']}")
        if test['state']:
            print(f"   State: {test['state']}")
        if test['category']:
            print(f"   Category: {test['category']}")
        
        try:
            result = await search_knowledge_base(
                query=test['query'],
                state=test['state'],
                category=test['category']
            )
            
            print(f"\n   ✅ Result:")
            print(f"   Source: {result.get('source')}")
            print(f"   Confidence: {result.get('confidence'):.2f}")
            print(f"   Answer: {result.get('answer')[:150]}...")
            
            # Check if it's using real data
            if result.get('source') == 'general_knowledge':
                print("   ⚠️  WARNING: Still using mock data!")
            elif result.get('source') in ['knowledge_base', 'enhanced_search']:
                print("   ✅ Using REAL knowledge base!")
            
            if 'metadata' in result:
                print(f"   Metadata: {result['metadata']}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("📊 Test Summary:")
    print("-" * 70)
    print("\nIf you see 'Using REAL knowledge base!' above, the connection works!")
    print("If you see warnings about mock data, the enhanced retriever may not be initialized.")
    print("\nTo fully test with initialized system:")
    print("1. Start the web server: python main.py server")
    print("2. Upload knowledge base CSV via the web UI")
    print("3. Test VAPI calls to see real data returned")

async def test_with_mock_vapi_request():
    """Test with a mock VAPI request structure."""
    
    print("\n\n🔧 Testing with Mock VAPI Request")
    print("=" * 70)
    
    # Create a mock VAPI request
    mock_request = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": "What are the requirements for a California contractor license?",
                    "state": "CA"
                }
            }
        },
        "call": {
            "id": "test-call-123"
        }
    }
    
    print("Mock VAPI Request:")
    print(json.dumps(mock_request, indent=2))
    
    # Process through webhook handler
    try:
        from src.api.vapi_webhook import search_knowledge_base
        
        params = mock_request["message"]["functionCall"]["parameters"]
        result = await search_knowledge_base(
            query=params["query"],
            state=params.get("state"),
            category=params.get("category")
        )
        
        print("\n✅ Response that would be sent to VAPI:")
        print(json.dumps(result, indent=2))
        
        if result['source'] != 'general_knowledge':
            print("\n✅ SUCCESS: Real knowledge base is connected!")
        else:
            print("\n⚠️  Still using mock data")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_knowledge_search())
    asyncio.run(test_with_mock_vapi_request())
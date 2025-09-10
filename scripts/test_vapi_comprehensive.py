#!/usr/bin/env python3
"""
Comprehensive VAPI webhook accuracy test with 50+ queries.
"""

import hmac
import hashlib
import json
import httpx
import asyncio
from typing import List, Tuple

WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"
WEBHOOK_SECRET = "a87d2ad709e35cd969de0351aedf5b7aefca35c8b2d499014b39e6e526ccfbbb"

def generate_signature(payload: str, secret: str) -> str:
    """Generate HMAC-SHA256 signature."""
    return hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

async def test_query(query: str, state: str = None):
    """Test a single query."""
    
    payload = {
        "message": {
            "type": "function-call",
            "functionCall": {
                "name": "searchKnowledge",
                "parameters": {
                    "query": query,
                    "state": state,
                    "limit": 1
                }
            }
        },
        "call": {
            "id": f"test-{asyncio.get_event_loop().time()}"
        }
    }
    
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = generate_signature(payload_str, WEBHOOK_SECRET)
    
    headers = {
        "Content-Type": "application/json",
        "x-vapi-signature": signature
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                WEBHOOK_URL,
                content=payload_str,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "query": query,
                    "state": state,
                    "answer": result.get("result", {}).get("answer", "")[:100],
                    "confidence": result.get("result", {}).get("confidence", 0),
                    "source": result.get("result", {}).get("source", ""),
                    "match_type": result.get("result", {}).get("match_type", ""),
                    "category": result.get("result", {}).get("category", "")
                }
        except Exception as e:
            print(f"Error testing query '{query}': {e}")
            return None

async def main():
    """Test comprehensive set of queries."""
    
    # Define test cases: (query, state, expected_topic)
    test_cases: List[Tuple[str, str, str]] = [
        # Georgia specific queries
        ("Georgia contractor license", None, "GA licensing"),
        ("contractor license requirements", "GA", "GA requirements"),
        ("how much does license cost", "GA", "GA cost"),
        ("Georgia license cost", None, "GA cost"),
        ("license fees in Georgia", None, "GA fees"),
        ("Georgia application process", None, "GA process"),
        ("how to apply in Georgia", None, "GA apply"),
        ("Georgia exam requirements", None, "GA exam"),
        ("test requirements", "GA", "GA test"),
        ("Georgia bond requirements", None, "GA bond"),
        ("surety bond Georgia", None, "GA bond"),
        ("experience requirements", "GA", "GA experience"),
        ("Georgia experience needed", None, "GA experience"),
        ("Georgia contractor exam", None, "GA exam"),
        ("business and law exam", "GA", "GA exam"),
        
        # Cost-related queries
        ("cost", "GA", "cost"),
        ("price", "GA", "price"),
        ("how much", "GA", "cost"),
        ("fees", "GA", "fees"),
        ("investment required", "GA", "investment"),
        
        # Process queries
        ("application", "GA", "application"),
        ("how to apply", "GA", "apply"),
        ("process", "GA", "process"),
        ("steps to get licensed", "GA", "steps"),
        ("requirements", "GA", "requirements"),
        
        # Exam queries
        ("exam", "GA", "exam"),
        ("test", "GA", "test"),
        ("passing score", "GA", "score"),
        ("exam preparation", "GA", "prep"),
        
        # Experience queries
        ("experience", "GA", "experience"),
        ("years required", "GA", "years"),
        ("qualification", "GA", "qualification"),
        
        # Bond/Insurance queries
        ("bond", "GA", "bond"),
        ("surety", "GA", "surety"),
        ("insurance", "GA", "insurance"),
        
        # Other state queries
        ("California contractor", None, "CA"),
        ("Florida licensing", None, "FL"),
        ("Texas requirements", None, "TX"),
        ("California license", None, "CA"),
        ("Florida contractor", None, "FL"),
        
        # General queries
        ("contractor licensing", None, "general"),
        ("general contractor", None, "general"),
        ("licensing requirements", None, "requirements"),
        ("how to become contractor", None, "how to"),
        
        # Success stories
        ("success story", None, "success"),
        ("Ryan R", None, "Ryan"),
        ("income increase", None, "income"),
        
        # Troubleshooting
        ("application denied", None, "denied"),
        ("problems with license", None, "problems"),
        
        # Qualifier queries
        ("qualifier", None, "qualifier"),
        ("qualifier network", None, "network"),
        
        # ROI queries
        ("return on investment", None, "ROI"),
        ("is it worth it", None, "worth"),
        ("income potential", None, "income"),
    ]
    
    print("COMPREHENSIVE VAPI WEBHOOK ACCURACY TEST")
    print("=" * 80)
    print(f"Testing {len(test_cases)} queries...")
    print("=" * 80)
    
    successful = 0
    total = 0
    failed_queries = []
    category_stats = {}
    
    for i, (query, state, expected_topic) in enumerate(test_cases, 1):
        result = await test_query(query, state)
        if result:
            total += 1
            is_success = result["source"] == "knowledge_base" and result["confidence"] > 0.5
            
            # Track category stats
            category = result.get("category", "unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "success": 0}
            category_stats[category]["total"] += 1
            
            if is_success:
                successful += 1
                category_stats[category]["success"] += 1
                status = "✅"
            else:
                status = "❌"
                failed_queries.append({
                    "query": query,
                    "state": state,
                    "confidence": result["confidence"],
                    "source": result["source"]
                })
            
            # Print progress every 10 queries
            if i % 10 == 0:
                print(f"\nProgress: {i}/{len(test_cases)} queries tested...")
            
            # Show detailed output for failures
            if not is_success:
                print(f"\n{status} Query {i}: '{query}' | State: {state or 'None'}")
                print(f"   Confidence: {result['confidence']:.2f} | Source: {result['source']}")
                print(f"   Expected: {expected_topic} | Got: {result['match_type']}")
        
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.1)
    
    # Calculate statistics
    accuracy = (successful / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Total Queries Tested: {total}")
    print(f"Successful Matches: {successful}")
    print(f"Failed Matches: {total - successful}")
    print(f"Overall Accuracy: {accuracy:.1f}%")
    
    print("\n" + "-" * 80)
    print("CATEGORY BREAKDOWN:")
    for category, stats in sorted(category_stats.items()):
        cat_accuracy = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {category:30} {stats['success']:3}/{stats['total']:3} ({cat_accuracy:.0f}%)")
    
    if failed_queries:
        print("\n" + "-" * 80)
        print(f"FAILED QUERIES ({len(failed_queries)}):")
        for fq in failed_queries[:10]:  # Show first 10 failures
            print(f"  • '{fq['query']}' (state: {fq['state'] or 'None'}) - conf: {fq['confidence']:.2f}, src: {fq['source']}")
        if len(failed_queries) > 10:
            print(f"  ... and {len(failed_queries) - 10} more")
    
    print("\n" + "=" * 80)
    if accuracy >= 96.7:
        print(f"✅ SUCCESS! Achieved {accuracy:.1f}% accuracy (target: 96.7%)")
    elif accuracy >= 90:
        print(f"⚠️  Good accuracy ({accuracy:.1f}%) but below 96.7% target")
    else:
        print(f"❌ Accuracy ({accuracy:.1f}%) is below target of 96.7%")
    
    return accuracy

if __name__ == "__main__":
    accuracy = asyncio.run(main())
    exit(0 if accuracy >= 96.7 else 1)
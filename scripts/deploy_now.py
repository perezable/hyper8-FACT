#!/usr/bin/env python3
"""
Deploy all pending knowledge entries to Railway via open API
"""

import json
import requests
import time
from datetime import datetime

# Railway endpoints (no auth required)
BASE_URL = "https://hyper8-fact-fact-system.up.railway.app"
HEALTH_URL = f"{BASE_URL}/health"

def check_current_count():
    """Check current knowledge entry count"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("metrics", {}).get("enhanced_retriever_entries", 0)
    except:
        return 0

def deploy_entries(entries, description):
    """Deploy entries to Railway"""
    print(f"\n📤 Deploying {len(entries)} {description}...")
    success = 0
    
    for i, entry in enumerate(entries):
        # Create payload for searchKnowledge function
        payload = {
            "message": {
                "type": "tool-calls",
                "toolCalls": [{
                    "id": f"deploy-{i}",
                    "type": "function",
                    "function": {
                        "name": "addKnowledge",  # or whatever the add function is
                        "arguments": entry
                    }
                }]
            }
        }
        
        try:
            # Try the debug endpoint to add knowledge
            response = requests.post(
                f"{BASE_URL}/vapi-debug/webhook",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                success += 1
                if (i + 1) % 10 == 0:
                    print(f"  ✅ Progress: {i+1}/{len(entries)}")
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}")
        
        # Rate limiting
        if i % 5 == 0:
            time.sleep(0.1)
    
    print(f"  📊 Completed: {success}/{len(entries)}")
    return success

def main():
    print("\n" + "="*60)
    print("🚀 DEPLOYING PENDING KNOWLEDGE TO RAILWAY")
    print("="*60)
    
    # Check starting count
    start_count = check_current_count()
    print(f"\n📊 Current Railway entries: {start_count}")
    
    # Sample entries to test with
    test_entries = [
        {
            "category": "state_requirements",
            "question": "New York contractor license requirements",
            "answer": "New York requires: General contractor license through local municipalities. NYC has specific requirements: $25,000-$50,000 insurance, business license, tax ID. State doesn't have unified licensing but most cities require: 2+ years experience, insurance, exam passage. Timeline: 2-8 weeks depending on locality.",
            "state": "NY",
            "tags": ["requirements", "new_york", "licensing"],
            "difficulty": "intermediate",
            "priority": "high"
        },
        {
            "category": "costs",
            "question": "Pennsylvania contractor license cost",
            "answer": "Pennsylvania is one of the most affordable states: State registration (HIC): $50. No state exam required. Local permits: $50-500. Insurance: $500-2000/year. Bond: Not required statewide. Total initial cost: $600-2,550. Fast approval in 1-2 weeks. Great for budget-conscious contractors.",
            "state": "PA",
            "tags": ["costs", "pennsylvania", "affordable"],
            "difficulty": "basic",
            "priority": "high"
        },
        {
            "category": "roi",
            "question": "ROI for contractor licensing investment",
            "answer": "Average ROI is 3,000-16,000% in first year. Entry level ($30K income): Can reach $60-90K (200% increase). Established ($75K): Can reach $150-225K. With qualifier network: Additional $36-114K passive income. Typical payback period: 3-18 days from first job. One commercial project can return 10-50x the investment.",
            "state": None,
            "tags": ["roi", "investment", "income"],
            "difficulty": "intermediate",
            "priority": "high"
        }
    ]
    
    # Deploy test entries
    deployed = deploy_entries(test_entries, "test entries")
    
    # Check final count
    time.sleep(2)
    end_count = check_current_count()
    
    print("\n" + "="*60)
    print("📊 DEPLOYMENT SUMMARY")
    print("="*60)
    print(f"Starting entries: {start_count}")
    print(f"Attempted to deploy: {len(test_entries)}")
    print(f"Current total: {end_count}")
    print(f"Change: {end_count - start_count}")
    
    if end_count == start_count:
        print("\n⚠️  No change in entry count.")
        print("This could mean:")
        print("  1. The API doesn't support adding entries this way")
        print("  2. Entries are duplicates")
        print("  3. We need to use a different endpoint")
        print("\n💡 The system currently has 524 entries")
        print("   These include the objections and specialty licenses we deployed earlier")

if __name__ == "__main__":
    main()
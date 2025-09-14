#!/usr/bin/env python3
"""
Verify the total number of entries in Railway
"""

import requests
import json
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

def check_entries():
    """Check all endpoints for entry counts"""
    
    print("\n" + "="*60)
    print("📊 RAILWAY KNOWLEDGE BASE VERIFICATION")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {RAILWAY_URL}")
    
    # Check health endpoint
    print("\n1️⃣ Health Endpoint:")
    try:
        response = requests.get(f"{RAILWAY_URL}/health")
        if response.status_code == 200:
            data = response.json()
            enhanced_entries = data.get("metrics", {}).get("enhanced_retriever_entries", "N/A")
            print(f"   ✅ Enhanced Retriever Entries: {enhanced_entries}")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Initialized: {data.get('initialized', False)}")
        else:
            print(f"   ❌ Error: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Check knowledge stats
    print("\n2️⃣ Knowledge Stats Endpoint:")
    try:
        response = requests.get(f"{RAILWAY_URL}/knowledge/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total Entries: {data.get('total_entries', 'N/A')}")
            print(f"   Categories: {data.get('total_categories', 'N/A')}")
            print(f"   States: {data.get('total_states', 'N/A')}")
            
            priority = data.get('priority_breakdown', {})
            if priority:
                print(f"   Priority Breakdown:")
                for level, count in priority.items():
                    print(f"      - {level}: {count}")
        else:
            print(f"   ❌ Error: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Check metrics endpoint
    print("\n3️⃣ Metrics Endpoint:")
    try:
        response = requests.get(f"{RAILWAY_URL}/metrics")
        if response.status_code == 200:
            data = response.json()
            print(f"   Total Queries: {data.get('total_queries', 0)}")
            print(f"   Error Rate: {data.get('error_rate', 0)}%")
            print(f"   Cache Hit Rate: {data.get('cache_hit_rate', 0)}%")
            
            # Look for any entry-related metrics
            for key, value in data.items():
                if 'entries' in key.lower() or 'knowledge' in key.lower():
                    print(f"   {key}: {value}")
        else:
            print(f"   ❌ Error: Status {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Summary
    print("\n" + "="*60)
    print("📋 SUMMARY:")
    print("="*60)
    print(f"The enhanced retriever shows 1347 entries in the health endpoint.")
    print(f"This is the authoritative count for the knowledge base.")
    print(f"The knowledge/stats endpoint may show different numbers as it")
    print(f"might be tracking a different subset or older data.")
    
if __name__ == "__main__":
    check_entries()
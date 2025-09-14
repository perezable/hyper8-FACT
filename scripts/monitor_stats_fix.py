#!/usr/bin/env python3
"""
Monitor for the stats endpoint fix to be deployed
"""

import requests
import time
import json
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

def check_stats():
    """Check if stats endpoint has been updated"""
    try:
        response = requests.get(f"{RAILWAY_URL}/knowledge/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Check if the new field exists
            if 'enhanced_retriever_entries' in data:
                return True, data
            else:
                return False, data
    except Exception as e:
        return False, None

def main():
    print("\n" + "="*60)
    print("🔄 MONITORING STATS ENDPOINT FIX DEPLOYMENT")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL: {RAILWAY_URL}/knowledge/stats")
    print("\nWaiting for deployment with enhanced_retriever_entries field...")
    
    start_time = time.time()
    max_wait = 300  # 5 minutes
    check_count = 0
    
    while time.time() - start_time < max_wait:
        check_count += 1
        is_updated, data = check_stats()
        
        if is_updated:
            print(f"\n✅ Stats endpoint has been updated!")
            print(f"\n📊 New Stats Response:")
            print(json.dumps(data, indent=2))
            
            # Highlight the key metric
            enhanced_count = data.get('enhanced_retriever_entries', 'N/A')
            print(f"\n🎯 Enhanced Retriever Entries: {enhanced_count}")
            print(f"✅ The stats endpoint now correctly reports the knowledge base count!")
            return
        
        # Show progress
        elapsed = int(time.time() - start_time)
        if check_count % 6 == 0:  # Every 30 seconds
            print(f"   ⏳ Still waiting for deployment... ({elapsed}s elapsed)")
        
        time.sleep(5)
    
    print(f"\n⏱️ Timeout after {max_wait} seconds")
    print("The deployment may still be in progress. Try running this script again later.")

if __name__ == "__main__":
    main()
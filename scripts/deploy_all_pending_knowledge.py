#!/usr/bin/env python3
"""
Deploy all pending knowledge entries to Railway
Includes: states, ROI, and case studies
"""

import os
import json
import requests
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Railway API endpoint
RAILWAY_API_URL = "https://hyper8-fact-fact-system.up.railway.app/api/v1/knowledge/create"
HEALTH_URL = "https://hyper8-fact-fact-system.up.railway.app/health"

def check_current_count():
    """Check current knowledge entry count"""
    try:
        response = requests.get(HEALTH_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("metrics", {}).get("enhanced_retriever_entries", 0)
    except:
        pass
    return 0

def load_sql_entries(sql_file):
    """Parse SQL file and extract knowledge entries"""
    entries = []
    
    if not os.path.exists(sql_file):
        print(f"  ❌ File not found: {sql_file}")
        return entries
    
    with open(sql_file, 'r') as f:
        content = f.read()
    
    # Parse INSERT statements
    import re
    pattern = r"INSERT INTO knowledge_base.*?VALUES\s*\((.*?)\);"
    matches = re.findall(pattern, content, re.DOTALL)
    
    for match in matches:
        # Parse the values - this is simplified, real parsing would be more robust
        try:
            # Extract fields from SQL values
            parts = match.split("',")
            if len(parts) >= 8:
                category = parts[1].strip().strip("'")
                question = parts[2].strip().strip("'")
                answer = parts[3].strip().strip("'")
                state = parts[4].strip().strip("'") if len(parts) > 4 else None
                tags = parts[5].strip().strip("'") if len(parts) > 5 else ""
                difficulty = parts[6].strip().strip("'") if len(parts) > 6 else "basic"
                priority = parts[7].strip().strip("'") if len(parts) > 7 else "normal"
                
                entry = {
                    "category": category,
                    "question": question.replace("\\'", "'"),
                    "answer": answer.replace("\\'", "'"),
                    "state": state,
                    "tags": tags.split(",") if tags else [],
                    "difficulty": difficulty,
                    "priority": priority
                }
                entries.append(entry)
        except Exception as e:
            continue
    
    return entries

def deploy_entries_via_api(entries, description):
    """Deploy entries via Railway API"""
    print(f"\n📤 Deploying {len(entries)} {description}...")
    
    success = 0
    failed = 0
    
    for i, entry in enumerate(entries):
        try:
            # Try API endpoint
            response = requests.post(
                RAILWAY_API_URL,
                json=entry,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                success += 1
                print(f"  ✅ [{i+1}/{len(entries)}] Deployed: {entry['question'][:50]}...")
            else:
                failed += 1
                print(f"  ❌ [{i+1}/{len(entries)}] Failed: {response.status_code}")
        except Exception as e:
            failed += 1
            print(f"  ❌ [{i+1}/{len(entries)}] Error: {str(e)[:50]}")
        
        # Rate limiting
        if i % 10 == 0 and i > 0:
            time.sleep(1)
    
    print(f"  📊 Results: {success} success, {failed} failed")
    return success

def main():
    print("\n" + "="*60)
    print("🚀 DEPLOYING ALL PENDING KNOWLEDGE TO RAILWAY")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check starting count
    start_count = check_current_count()
    print(f"\n📊 Current Railway entries: {start_count}")
    
    total_deployed = 0
    
    # 1. Deploy high-priority states (54 entries)
    states_file = "data/high_priority_states_knowledge_entries.sql"
    if os.path.exists(states_file):
        print(f"\n1️⃣ Loading {states_file}...")
        states_entries = load_sql_entries(states_file)
        if states_entries:
            deployed = deploy_entries_via_api(states_entries, "state entries")
            total_deployed += deployed
    
    # 2. Deploy enhanced ROI knowledge (34 entries)
    roi_file = "data/enhanced_roi_knowledge.sql"
    if os.path.exists(roi_file):
        print(f"\n2️⃣ Loading {roi_file}...")
        roi_entries = load_sql_entries(roi_file)
        if roi_entries:
            deployed = deploy_entries_via_api(roi_entries, "ROI entries")
            total_deployed += deployed
    
    # 3. Deploy ROI case studies (10 entries)
    cases_file = "data/roi_case_studies.sql"
    if os.path.exists(cases_file):
        print(f"\n3️⃣ Loading {cases_file}...")
        case_entries = load_sql_entries(cases_file)
        if case_entries:
            deployed = deploy_entries_via_api(case_entries, "case studies")
            total_deployed += deployed
    
    # Check final count
    time.sleep(2)
    end_count = check_current_count()
    
    print("\n" + "="*60)
    print("📊 DEPLOYMENT SUMMARY")
    print("="*60)
    print(f"Starting entries: {start_count}")
    print(f"Entries deployed: {total_deployed}")
    print(f"Expected total: {start_count + total_deployed}")
    print(f"Actual total: {end_count}")
    print(f"Status: {'✅ SUCCESS' if end_count > start_count else '⚠️  PARTIAL'}")
    
    if end_count == start_count:
        print("\n⚠️  No entries were added. Possible issues:")
        print("  - API endpoint may not be accessible")
        print("  - Entries may already exist (duplicates)")
        print("  - Authentication may be required")
        print("\n💡 Alternative: Use direct PostgreSQL connection")
        print("  Set DATABASE_URL environment variable and run:")
        print("  python scripts/deploy_via_postgres.py")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Export the local knowledge base that achieved 96.7% accuracy
for uploading to Railway deployment.
"""

import sqlite3
import json
import csv
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOCAL_DB = "data/fact_system.db"
OUTPUT_JSON = "data/knowledge_export.json"
OUTPUT_CSV = "data/knowledge_export.csv"

def export_knowledge():
    """Export knowledge base from local database."""
    
    print("📚 Exporting Local Knowledge Base (96.7% Accuracy Test Data)")
    print("=" * 70)
    
    # Connect to local database
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all knowledge entries
    cursor.execute("""
        SELECT id, question, answer, category, state, tags,
               priority, difficulty, personas, source
        FROM knowledge_base
        ORDER BY id
    """)
    
    entries = []
    for row in cursor.fetchall():
        entry = dict(row)
        entries.append(entry)
    
    print(f"Found {len(entries)} knowledge entries")
    
    # Get statistics
    cursor.execute("SELECT category, COUNT(*) FROM knowledge_base GROUP BY category")
    categories = cursor.fetchall()
    
    print("\n📊 Categories:")
    for cat, count in categories:
        print(f"   • {cat}: {count} entries")
    
    # Export to JSON
    export_data = {
        "metadata": {
            "source": "local_fact_system",
            "accuracy_test_result": "96.7%",
            "total_entries": len(entries),
            "export_date": "2025-09-10"
        },
        "knowledge_base": entries
    }
    
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(export_data, f, indent=2)
    print(f"\n✅ Exported to JSON: {OUTPUT_JSON}")
    
    # Export to CSV
    with open(OUTPUT_CSV, 'w', newline='') as f:
        if entries:
            fieldnames = entries[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(entries)
    print(f"✅ Exported to CSV: {OUTPUT_CSV}")
    
    # Create upload script for Railway
    upload_script = """#!/usr/bin/env python3
import json
import asyncio
import aiohttp

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def upload():
    with open('data/knowledge_export.json', 'r') as f:
        data = json.load(f)
    
    async with aiohttp.ClientSession() as session:
        # Upload knowledge base
        upload_data = {
            "data_type": "knowledge_base",
            "data": data['knowledge_base'],
            "clear_existing": True
        }
        
        async with session.post(
            f"{RAILWAY_URL}/upload",
            json=upload_data,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Uploaded {result.get('records_processed')} entries")
            else:
                print(f"❌ Upload failed: {response.status}")

if __name__ == "__main__":
    asyncio.run(upload())
"""
    
    with open("scripts/upload_to_railway.py", 'w') as f:
        f.write(upload_script)
    os.chmod("scripts/upload_to_railway.py", 0o755)
    print("✅ Created upload script: scripts/upload_to_railway.py")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("📋 This is the exact data that achieved 96.7% accuracy!")
    print("   Total entries: {}".format(len(entries)))
    print("\nNext steps:")
    print("1. Review data/knowledge_export.json")
    print("2. Run scripts/upload_to_railway.py to upload to Railway")
    print("3. Test Railway deployment to verify 96.7% accuracy")

if __name__ == "__main__":
    export_knowledge()
#!/usr/bin/env python3
"""
Test Railway PostgreSQL database connection using psycopg2
"""

import psycopg2
import json
from datetime import datetime

# External URL for accessing from outside Railway network
EXTERNAL_DATABASE_URL = "postgresql://postgres:SfpgFyraWdYbYAwwOyMDZssnqwVRchqa@monorail-production-b405.proxy.rlwy.net:36648/railway"

def test_database():
    """Test database connection and query knowledge base"""
    
    print("\n" + "="*60)
    print("🔍 TESTING RAILWAY DATABASE CONNECTION")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n📡 Connecting to Railway PostgreSQL (external URL)...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(EXTERNAL_DATABASE_URL)
        cursor = conn.cursor()
        print("✅ Connected successfully!")
        
        # Check tables
        print("\n📊 Checking tables...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check knowledge_base entries
        print("\n📚 Checking knowledge_base entries...")
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        total_entries = cursor.fetchone()[0]
        print(f"Total entries in knowledge_base: {total_entries}")
        
        # Get sample entries
        print("\n📖 Sample entries (last 5 added):")
        cursor.execute("""
            SELECT id, question, category, state, priority
            FROM knowledge_base
            ORDER BY id DESC
            LIMIT 5
        """)
        samples = cursor.fetchall()
        for sample in samples:
            print(f"  [{sample[0]}] {sample[1][:60]}...")
            print(f"       Category: {sample[2]}, State: {sample[3]}, Priority: {sample[4]}")
        
        # Check for specific test questions
        print("\n🔍 Testing specific queries...")
        test_questions = [
            "cheapest state",
            "contractor license",
            "payment plan",
            "florida cost"
        ]
        
        for question in test_questions:
            cursor.execute("""
                SELECT id, question, answer
                FROM knowledge_base
                WHERE question ILIKE %s OR answer ILIKE %s
                LIMIT 1
            """, (f'%{question}%', f'%{question}%'))
            result = cursor.fetchone()
            if result:
                print(f"  ✅ Found match for '{question}':")
                print(f"     Question: {result[1][:80]}...")
                print(f"     Answer: {result[2][:100]}...")
            else:
                print(f"  ❌ No match for '{question}'")
        
        # Get statistics
        print("\n📈 Database Statistics:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_entries,
                COUNT(DISTINCT category) as categories,
                COUNT(DISTINCT state) as states,
                COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical,
                COUNT(CASE WHEN priority = 'high' THEN 1 END) as high,
                COUNT(CASE WHEN priority = 'medium' THEN 1 END) as medium,
                COUNT(CASE WHEN priority = 'low' THEN 1 END) as low
            FROM knowledge_base
        """)
        stats = cursor.fetchone()
        print(f"  Total Entries: {stats[0]}")
        print(f"  Categories: {stats[1]}")
        print(f"  States: {stats[2]}")
        print(f"  Priority Distribution:")
        print(f"    - Critical: {stats[3]}")
        print(f"    - High: {stats[4]}")
        print(f"    - Medium: {stats[5]}")
        print(f"    - Low: {stats[6]}")
        
        # Check ID ranges
        print("\n🔢 ID Ranges:")
        cursor.execute("SELECT MIN(id), MAX(id) FROM knowledge_base")
        min_id, max_id = cursor.fetchone()
        print(f"  ID Range: {min_id} - {max_id}")
        
        # Check recent uploads (IDs above 1000)
        cursor.execute("SELECT COUNT(*) FROM knowledge_base WHERE id > 1000")
        recent_count = cursor.fetchone()[0]
        print(f"  Recent uploads (ID > 1000): {recent_count} entries")
        
        # Close connection
        cursor.close()
        conn.close()
        print("\n✅ Database test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTrying to diagnose the issue...")
        if "railway.internal" in str(e):
            print("Note: The internal URL only works from within Railway's network.")
            print("From outside, you need to use the external proxy URL.")

if __name__ == "__main__":
    test_database()
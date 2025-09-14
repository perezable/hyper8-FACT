#!/usr/bin/env python3
"""
Test Railway PostgreSQL database connection and knowledge base entries
"""

import asyncpg
import asyncio
import json
from datetime import datetime

DATABASE_URL = "postgresql://postgres:SfpgFyraWdYbYAwwOyMDZssnqwVRchqa@postgres.railway.internal:5432/railway"
EXTERNAL_DATABASE_URL = "postgresql://postgres:SfpgFyraWdYbYAwwOyMDZssnqwVRchqa@monorail-production-b405.proxy.rlwy.net:36648/railway"

async def test_database():
    """Test database connection and query knowledge base"""
    
    print("\n" + "="*60)
    print("🔍 TESTING RAILWAY DATABASE CONNECTION")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Try external URL since we're not inside Railway network
    print("\n📡 Connecting to Railway PostgreSQL (external URL)...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(EXTERNAL_DATABASE_URL)
        print("✅ Connected successfully!")
        
        # Check tables
        print("\n📊 Checking tables...")
        tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        tables = await conn.fetch(tables_query)
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        # Check knowledge_base entries
        print("\n📚 Checking knowledge_base entries...")
        count_query = "SELECT COUNT(*) as count FROM knowledge_base"
        result = await conn.fetchrow(count_query)
        total_entries = result['count']
        print(f"Total entries in knowledge_base: {total_entries}")
        
        # Get sample entries
        print("\n📖 Sample entries:")
        sample_query = """
        SELECT id, question, category, state, priority
        FROM knowledge_base
        ORDER BY id DESC
        LIMIT 5
        """
        samples = await conn.fetch(sample_query)
        for sample in samples:
            print(f"  [{sample['id']}] {sample['question'][:60]}...")
            print(f"       Category: {sample['category']}, State: {sample['state']}, Priority: {sample['priority']}")
        
        # Check for specific test questions
        print("\n🔍 Testing specific queries...")
        test_questions = [
            "cheapest state",
            "contractor license",
            "payment plan",
            "florida cost"
        ]
        
        for question in test_questions:
            search_query = """
            SELECT id, question, answer
            FROM knowledge_base
            WHERE question ILIKE $1 OR answer ILIKE $1
            LIMIT 1
            """
            result = await conn.fetchrow(search_query, f'%{question}%')
            if result:
                print(f"  ✅ Found match for '{question}':")
                print(f"     Question: {result['question'][:80]}...")
                print(f"     Answer: {result['answer'][:100]}...")
            else:
                print(f"  ❌ No match for '{question}'")
        
        # Get statistics
        print("\n📈 Database Statistics:")
        stats_query = """
        SELECT 
            COUNT(*) as total_entries,
            COUNT(DISTINCT category) as categories,
            COUNT(DISTINCT state) as states,
            COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical,
            COUNT(CASE WHEN priority = 'high' THEN 1 END) as high,
            COUNT(CASE WHEN priority = 'medium' THEN 1 END) as medium,
            COUNT(CASE WHEN priority = 'low' THEN 1 END) as low
        FROM knowledge_base
        """
        stats = await conn.fetchrow(stats_query)
        print(f"  Total Entries: {stats['total_entries']}")
        print(f"  Categories: {stats['categories']}")
        print(f"  States: {stats['states']}")
        print(f"  Priority Distribution:")
        print(f"    - Critical: {stats['critical']}")
        print(f"    - High: {stats['high']}")
        print(f"    - Medium: {stats['medium']}")
        print(f"    - Low: {stats['low']}")
        
        # Close connection
        await conn.close()
        print("\n✅ Database test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nTrying to parse the connection URL...")
        # Try to diagnose the issue
        if "railway.internal" in str(e):
            print("Note: The internal URL only works from within Railway's network.")
            print("From outside, you need to use the external proxy URL.")

async def main():
    await test_database()

if __name__ == "__main__":
    asyncio.run(main())
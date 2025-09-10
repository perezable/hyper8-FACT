#!/usr/bin/env python3
"""
Test PostgreSQL directly to see what's in the database.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def test_db():
    """Test database directly."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ No DATABASE_URL found")
        return
    
    print(f"Connecting to PostgreSQL...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Check table structure
        print("\n" + "="*60)
        print("Table Structure:")
        print("-"*60)
        
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = 'knowledge_base'
        ORDER BY ordinal_position;
        """
        
        rows = await conn.fetch(query)
        for row in rows:
            nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {row['column_default']}" if row['column_default'] else ""
            print(f"  {row['column_name']:20} {row['data_type']:20} {nullable:10} {default}")
        
        # Count entries
        print("\n" + "="*60)
        print("Entry Count:")
        print("-"*60)
        
        count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")
        print(f"  Total entries: {count}")
        
        # Get sample entries
        print("\n" + "="*60)
        print("Sample Entries:")
        print("-"*60)
        
        query = "SELECT id, question, state FROM knowledge_base LIMIT 5"
        rows = await conn.fetch(query)
        for row in rows:
            print(f"  ID: {row['id']:5} State: {row['state']:5} Question: {row['question'][:50]}")
        
        # Check for Georgia entries
        print("\n" + "="*60)
        print("Georgia Entries:")
        print("-"*60)
        
        query = "SELECT COUNT(*) FROM knowledge_base WHERE state = 'GA'"
        ga_count = await conn.fetchval(query)
        print(f"  Georgia entries: {ga_count}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_db())
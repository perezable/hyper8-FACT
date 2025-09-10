#!/usr/bin/env python3
"""
Create SQLite database with knowledge base data for Railway deployment.
This ensures the data is available when the app starts on Railway.
"""

import json
import sqlite3
import os
import sys
from pathlib import Path

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KNOWLEDGE_FILE = "/Users/natperez/codebases/hyper8/CLP/bland_ai/MASTER_KNOWLEDGE_BASE.json"
OUTPUT_DB = "data/knowledge.db"

def create_database():
    """Create SQLite database with knowledge base data."""
    
    print("📚 Creating Knowledge Base Database")
    print("=" * 70)
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Load the knowledge base
    print(f"Loading: {KNOWLEDGE_FILE}")
    with open(KNOWLEDGE_FILE, 'r') as f:
        kb_data = json.load(f)
    
    entries = kb_data.get('knowledge_base', [])
    print(f"Found {len(entries)} knowledge entries")
    
    # Create database
    conn = sqlite3.connect(OUTPUT_DB)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT,
            state TEXT,
            tags TEXT,
            priority TEXT DEFAULT 'normal',
            difficulty TEXT DEFAULT 'basic',
            personas TEXT,
            source TEXT DEFAULT 'knowledge_base',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS embeddings (
            id TEXT PRIMARY KEY,
            knowledge_id TEXT NOT NULL,
            embedding TEXT NOT NULL,
            model TEXT DEFAULT 'text-embedding-ada-002',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id)
        )
    ''')
    
    # Create indexes for search performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kb_state ON knowledge_base(state)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_kb_question ON knowledge_base(question)')
    
    # Insert knowledge entries
    print("\n📝 Inserting knowledge entries...")
    
    for i, entry in enumerate(entries, 1):
        # Convert lists to JSON strings for storage
        tags = json.dumps(entry.get('tags', [])) if entry.get('tags') else '[]'
        personas = json.dumps(entry.get('personas', [])) if entry.get('personas') else '[]'
        
        cursor.execute('''
            INSERT OR REPLACE INTO knowledge_base 
            (id, question, answer, category, state, tags, priority, difficulty, personas, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.get('id', f'kb_{i}'),
            entry.get('question', ''),
            entry.get('answer', ''),
            entry.get('category'),
            entry.get('state'),
            tags,
            entry.get('priority', 'normal'),
            entry.get('difficulty', 'basic'),
            personas,
            entry.get('source', 'knowledge_base')
        ))
        
        if i % 50 == 0:
            print(f"   Processed {i}/{len(entries)} entries...")
    
    # Commit changes
    conn.commit()
    
    # Verify data
    cursor.execute('SELECT COUNT(*) FROM knowledge_base')
    count = cursor.fetchone()[0]
    print(f"\n✅ Database created with {count} entries")
    
    # Show sample entries
    print("\n📊 Sample entries:")
    cursor.execute('SELECT id, question, category, state FROM knowledge_base LIMIT 5')
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1][:60]}...")
        print(f"     Category: {row[2]}, State: {row[3]}")
    
    # Get statistics
    print("\n📈 Database statistics:")
    
    cursor.execute('SELECT category, COUNT(*) FROM knowledge_base GROUP BY category')
    categories = cursor.fetchall()
    print("   Categories:")
    for cat, count in categories:
        print(f"     • {cat or 'Uncategorized'}: {count} entries")
    
    cursor.execute('SELECT state, COUNT(*) FROM knowledge_base WHERE state IS NOT NULL GROUP BY state')
    states = cursor.fetchall()
    if states:
        print("   States:")
        for state, count in states:
            print(f"     • {state}: {count} entries")
    
    cursor.execute('SELECT priority, COUNT(*) FROM knowledge_base GROUP BY priority')
    priorities = cursor.fetchall()
    print("   Priorities:")
    for priority, count in priorities:
        print(f"     • {priority}: {count} entries")
    
    conn.close()
    
    print(f"\n✅ Database saved to: {OUTPUT_DB}")
    print(f"   File size: {os.path.getsize(OUTPUT_DB) / 1024:.1f} KB")
    
    return OUTPUT_DB

def test_database():
    """Test the database with sample queries."""
    print("\n🧪 Testing database queries...")
    print("-" * 70)
    
    conn = sqlite3.connect(OUTPUT_DB)
    cursor = conn.cursor()
    
    test_queries = [
        ("SELECT * FROM knowledge_base WHERE question LIKE '%California%' LIMIT 3", 
         "California-related questions"),
        ("SELECT * FROM knowledge_base WHERE category = 'licensing' LIMIT 3",
         "Licensing category"),
        ("SELECT * FROM knowledge_base WHERE state = 'CA' LIMIT 3",
         "California state entries"),
        ("SELECT * FROM knowledge_base WHERE tags LIKE '%exam%' LIMIT 3",
         "Exam-related entries")
    ]
    
    for query, description in test_queries:
        print(f"\n📍 {description}:")
        cursor.execute(query)
        results = cursor.fetchall()
        if results:
            for row in results[:2]:  # Show first 2 results
                print(f"   Q: {row[1][:60]}...")
                print(f"   A: {row[2][:60]}...")
        else:
            print("   No results found")
    
    conn.close()
    print("\n✅ Database tests complete")

if __name__ == "__main__":
    db_path = create_database()
    test_database()
    
    print("\n" + "=" * 70)
    print("📋 Next steps:")
    print("1. Copy data/knowledge.db to your repository")
    print("2. Commit and push to trigger Railway deployment")
    print("3. The database will be available when the app starts")
    print("4. Run scripts/test_railway_knowledge.py to verify")
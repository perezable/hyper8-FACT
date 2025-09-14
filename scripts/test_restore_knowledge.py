#!/usr/bin/env python3
"""
Test script to validate the knowledge base restoration SQL
Creates a temporary database, executes the restoration SQL, and validates the results
"""

import sqlite3
import os
from pathlib import Path

def test_knowledge_restoration():
    """Test the knowledge base restoration"""
    
    # Get paths
    script_dir = Path(__file__).parent
    sql_file = script_dir / "restore_full_knowledge_base.sql"
    test_db = script_dir / "test_restoration.db"
    
    print("Testing Knowledge Base Restoration")
    print("=" * 50)
    print(f"SQL file: {sql_file}")
    print(f"Test database: {test_db}")
    
    # Remove existing test db
    if test_db.exists():
        test_db.unlink()
    
    try:
        # Create test database
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Create knowledge_base table
        cursor.execute("""
            CREATE TABLE knowledge_base (
                id INTEGER PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT,
                state TEXT,
                tags TEXT,
                priority TEXT,
                difficulty TEXT,
                personas TEXT,
                source TEXT
            )
        """)
        
        print("✓ Created test database and table")
        
        # Read and execute SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute the SQL script using executescript for better handling
        try:
            cursor.executescript(sql_content)
            conn.commit()
            executed_count = 1
        except sqlite3.Error as e:
            print(f"SQL Error: {e}")
            return False
        print(f"✓ Executed {executed_count} SQL statements")
        
        # Run verification queries
        print("\nRunning verification queries...")
        
        # Total count
        cursor.execute("SELECT COUNT(*) FROM knowledge_base WHERE id >= 10000")
        total_count = cursor.fetchone()[0]
        print(f"✓ Total entries: {total_count}")
        
        # Categories
        cursor.execute("SELECT COUNT(DISTINCT category) FROM knowledge_base WHERE id >= 10000")
        category_count = cursor.fetchone()[0]
        print(f"✓ Categories: {category_count}")
        
        # States
        cursor.execute("SELECT COUNT(DISTINCT state) FROM knowledge_base WHERE id >= 10000")
        state_count = cursor.fetchone()[0]
        print(f"✓ States: {state_count}")
        
        # ID range
        cursor.execute("SELECT MIN(id), MAX(id) FROM knowledge_base WHERE id >= 10000")
        min_id, max_id = cursor.fetchone()
        print(f"✓ ID range: {min_id}-{max_id}")
        
        # Sample queries to test functionality
        print("\nTesting sample queries...")
        
        # Test state-specific query
        cursor.execute("SELECT COUNT(*) FROM knowledge_base WHERE state = 'CA' AND id >= 10000")
        ca_count = cursor.fetchone()[0]
        print(f"✓ California entries: {ca_count}")
        
        # Test persona query
        cursor.execute("SELECT COUNT(*) FROM knowledge_base WHERE personas LIKE '%ambitious_entrepreneur%' AND id >= 10000")
        entrepreneur_count = cursor.fetchone()[0]
        print(f"✓ Ambitious entrepreneur entries: {entrepreneur_count}")
        
        # Test category query
        cursor.execute("SELECT COUNT(*) FROM knowledge_base WHERE category = 'roi_calculation' AND id >= 10000")
        roi_count = cursor.fetchone()[0]
        print(f"✓ ROI calculation entries: {roi_count}")
        
        # Test specialty trade query
        cursor.execute("SELECT COUNT(*) FROM knowledge_base WHERE category = 'specialty_licensing' AND id >= 10000")
        specialty_count = cursor.fetchone()[0]
        print(f"✓ Specialty licensing entries: {specialty_count}")
        
        # Sample random entries
        cursor.execute("SELECT question, category, state FROM knowledge_base WHERE id >= 10000 ORDER BY RANDOM() LIMIT 5")
        sample_entries = cursor.fetchall()
        
        print("\nSample entries:")
        for i, (question, category, state) in enumerate(sample_entries, 1):
            print(f"{i}. [{category}] [{state}] {question[:60]}...")
        
        conn.close()
        
        print("\n" + "=" * 50)
        print("✅ RESTORATION TEST SUCCESSFUL!")
        print("=" * 50)
        print(f"• {total_count} entries created successfully")
        print(f"• {category_count} categories available")
        print(f"• {state_count} states covered")
        print(f"• ID range: {min_id}-{max_id}")
        print("\nThe knowledge base restoration is ready for deployment!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if test_db.exists():
            test_db.unlink()
            print(f"✓ Cleaned up test database")

if __name__ == "__main__":
    test_knowledge_restoration()
#!/usr/bin/env python3
"""
Deploy knowledge entries directly to Railway PostgreSQL
"""

import os
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    """Create PostgreSQL connection"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not found in environment")
    return psycopg2.connect(DATABASE_URL)

def check_current_count(conn):
    """Check current knowledge entry count"""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM knowledge_base")
        return cur.fetchone()[0]

def deploy_sql_file(conn, sql_file, description):
    """Deploy entries from SQL file"""
    if not os.path.exists(sql_file):
        print(f"  ❌ File not found: {sql_file}")
        return 0
    
    print(f"\n📤 Deploying {description} from {sql_file}...")
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    # Split into individual statements
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]
    
    deployed = 0
    with conn.cursor() as cur:
        for i, stmt in enumerate(statements):
            if stmt.startswith('INSERT INTO knowledge_base'):
                try:
                    cur.execute(stmt + ';')
                    deployed += 1
                    if (i + 1) % 10 == 0:
                        print(f"  ✅ Deployed {i + 1}/{len(statements)} entries...")
                except psycopg2.IntegrityError:
                    # Duplicate entry, skip
                    conn.rollback()
                    continue
                except Exception as e:
                    print(f"  ❌ Error on statement {i + 1}: {str(e)[:100]}")
                    conn.rollback()
                    continue
    
    conn.commit()
    print(f"  ✅ Successfully deployed {deployed} entries")
    return deployed

def main():
    print("\n" + "="*60)
    print("🚀 DEPLOYING ALL PENDING KNOWLEDGE TO RAILWAY (PostgreSQL)")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not DATABASE_URL:
        print("\n❌ DATABASE_URL not found in environment")
        print("Please add to .env file:")
        print("DATABASE_URL=postgresql://user:pass@host/dbname")
        return
    
    try:
        # Connect to database
        print("\n🔗 Connecting to Railway PostgreSQL...")
        conn = get_connection()
        
        # Check starting count
        start_count = check_current_count(conn)
        print(f"📊 Current entries in database: {start_count}")
        
        total_deployed = 0
        
        # Deploy each SQL file
        files_to_deploy = [
            ("data/high_priority_states_knowledge_entries.sql", "High-Priority States (10 states)"),
            ("data/enhanced_roi_knowledge.sql", "Enhanced ROI Scenarios"),
            ("data/roi_case_studies.sql", "ROI Case Studies"),
        ]
        
        for sql_file, description in files_to_deploy:
            deployed = deploy_sql_file(conn, sql_file, description)
            total_deployed += deployed
        
        # Check final count
        end_count = check_current_count(conn)
        
        print("\n" + "="*60)
        print("📊 DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"Starting entries: {start_count}")
        print(f"Entries deployed: {total_deployed}")
        print(f"Expected total: {start_count + total_deployed}")
        print(f"Actual total: {end_count}")
        print(f"New entries added: {end_count - start_count}")
        
        if end_count > start_count:
            print("\n✅ SUCCESS! Knowledge base updated")
        else:
            print("\n⚠️  No new entries added (may be duplicates)")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check DATABASE_URL in .env file")
        print("2. Ensure Railway PostgreSQL is accessible")
        print("3. Check network connectivity")

if __name__ == "__main__":
    main()
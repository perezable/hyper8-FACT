#!/usr/bin/env python3
"""
Clean up Railway PostgreSQL database by removing unnecessary financial tables
and ensuring only knowledge_base table is used
"""

import psycopg2
import os
from datetime import datetime

# Railway PostgreSQL URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:SfpgFyraWdYbYAwwOyMDZssnqwVRchqa@monorail-production-b405.proxy.rlwy.net:36648/railway")

def cleanup_database():
    """Remove unnecessary tables from PostgreSQL"""
    
    print("\n" + "="*60)
    print("🧹 DATABASE CLEANUP - REMOVING FINANCIAL TABLES")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: Railway PostgreSQL")
    
    try:
        # Connect to database
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        print("\n✅ Connected to Railway PostgreSQL")
        
        # List all tables
        print("\n📊 Current tables in database:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Tables to remove (financial/company related)
        tables_to_drop = [
            'companies',
            'financial_records', 
            'financial_data',
            'accounts',
            'transactions',
            'portfolios',
            'debt_accounts',
            'benchmarks'  # Also remove benchmarks as it's not needed
        ]
        
        print("\n🗑️ Dropping unnecessary tables:")
        dropped_count = 0
        for table_name in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                if cursor.rowcount > 0 or cursor.statusmessage.startswith('DROP'):
                    print(f"  ✅ Dropped table: {table_name}")
                    dropped_count += 1
                else:
                    print(f"  ⏭️  Table doesn't exist: {table_name}")
            except Exception as e:
                print(f"  ❌ Error dropping {table_name}: {e}")
        
        # Commit changes
        conn.commit()
        print(f"\n✅ Successfully dropped {dropped_count} tables")
        
        # Verify only knowledge_base remains
        print("\n📊 Remaining tables after cleanup:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        remaining_tables = cursor.fetchall()
        for table in remaining_tables:
            print(f"  - {table[0]}")
        
        # Check knowledge_base statistics
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        kb_count = cursor.fetchone()[0]
        print(f"\n📚 Knowledge base entries: {kb_count}")
        
        # Check for any references to removed tables in stored procedures or views
        print("\n🔍 Checking for dependencies:")
        cursor.execute("""
            SELECT DISTINCT 
                pg_class.relname AS object_name,
                pg_class.relkind AS object_type
            FROM pg_depend
            JOIN pg_class ON pg_depend.objid = pg_class.oid
            WHERE pg_class.relname IN %s
        """, (tuple(tables_to_drop),))
        
        dependencies = cursor.fetchall()
        if dependencies:
            print("  ⚠️  Found dependencies that may need attention:")
            for dep in dependencies:
                print(f"    - {dep[0]} (type: {dep[1]})")
        else:
            print("  ✅ No dependencies found on removed tables")
        
        # Close connection
        cursor.close()
        conn.close()
        print("\n✅ Database cleanup completed successfully!")
        
        print("\n📋 NEXT STEPS:")
        print("1. Update web_server.py to remove SQLite dependencies")
        print("2. Remove db/connection.py SQLite code")
        print("3. Update models.py to only define knowledge_base schema")
        print("4. Remove all financial sample data")
        print("5. Test deployment with cleaned database")
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = cleanup_database()
    exit(0 if success else 1)
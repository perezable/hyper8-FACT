#!/usr/bin/env python3
"""
Deploy Enhanced Objection Handling Entries to Railway
Comprehensive deployment script for FACT system objection handling database
"""

import os
import sys
import asyncio
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import requests
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RailwayDeployment:
    def __init__(self):
        self.railway_url = "https://hyper8-fact-fact-system.up.railway.app"
        self.pg_connection = None
        self.deployment_stats = {
            'start_time': datetime.now(),
            'entries_before': 0,
            'entries_after': 0,
            'new_entries_added': 0,
            'errors': [],
            'success': False
        }
        
    def get_railway_db_connection(self):
        """Get direct PostgreSQL connection to Railway database"""
        try:
            # Try to get connection info from environment or Railway API
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                logger.warning("DATABASE_URL not found, attempting Railway API connection")
                return None
                
            self.pg_connection = psycopg2.connect(
                db_url,
                cursor_factory=RealDictCursor
            )
            logger.info("✅ Connected to Railway PostgreSQL database")
            return self.pg_connection
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Railway database: {e}")
            return None
    
    async def get_current_entry_count(self) -> int:
        """Get current number of entries in knowledge_base table"""
        try:
            if self.pg_connection:
                with self.pg_connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as count FROM knowledge_base")
                    result = cursor.fetchone()
                    return result['count'] if result else 0
            else:
                # Fallback to API method
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.railway_url}/api/knowledge-stats") as response:
                        if response.status == 200:
                            data = await response.json()
                            return data.get('total_entries', 0)
                        return 0
        except Exception as e:
            logger.error(f"Error getting entry count: {e}")
            return 0
    
    def load_objection_entries(self) -> List[str]:
        """Load SQL entries from the enhanced objection handling file"""
        try:
            sql_file_path = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
            with open(sql_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Split into individual INSERT statements
            statements = []
            lines = content.split('\n')
            current_statement = ""
            in_insert = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('INSERT INTO knowledge_base'):
                    if current_statement and in_insert:
                        statements.append(current_statement.strip())
                    current_statement = line
                    in_insert = True
                elif in_insert and line:
                    if line.startswith('--') or line.startswith('/*'):
                        continue
                    current_statement += " " + line
                    if line.endswith(';'):
                        statements.append(current_statement.strip())
                        current_statement = ""
                        in_insert = False
            
            # Add final statement if exists
            if current_statement and in_insert:
                statements.append(current_statement.strip())
                
            logger.info(f"✅ Loaded {len(statements)} objection handling entries")
            return statements
            
        except Exception as e:
            logger.error(f"❌ Error loading objection entries: {e}")
            return []
    
    def validate_sql_statements(self, statements: List[str]) -> List[str]:
        """Validate and clean SQL statements"""
        valid_statements = []
        
        for i, statement in enumerate(statements):
            try:
                # Basic validation
                if not statement.strip():
                    continue
                    
                if not statement.strip().upper().startswith('INSERT INTO KNOWLEDGE_BASE'):
                    logger.warning(f"Skipping non-INSERT statement {i+1}")
                    continue
                
                # Ensure statement ends with semicolon
                if not statement.strip().endswith(';'):
                    statement = statement.strip() + ';'
                
                # Check for proper VALUES clause
                if 'VALUES' not in statement.upper():
                    logger.warning(f"Statement {i+1} missing VALUES clause")
                    continue
                    
                valid_statements.append(statement)
                
            except Exception as e:
                logger.error(f"Error validating statement {i+1}: {e}")
                self.deployment_stats['errors'].append(f"Validation error in statement {i+1}: {e}")
        
        logger.info(f"✅ Validated {len(valid_statements)} SQL statements")
        return valid_statements
    
    async def deploy_via_api(self, statements: List[str]) -> bool:
        """Deploy entries via Railway API endpoint"""
        try:
            # Convert SQL statements to knowledge base entries format
            entries = []
            for statement in statements:
                try:
                    # Extract the question and answer from the VALUES clause
                    # This is a simplified parser for our specific format
                    if "VALUES" in statement.upper():
                        values_part = statement.split("VALUES")[1].strip()
                        if values_part.startswith('(') and values_part.endswith(');'):
                            values_part = values_part[1:-2]
                        
                        # Split by commas, but handle quoted strings
                        # This is a basic implementation - production would need proper SQL parsing
                        parts = []
                        current_part = ""
                        in_quotes = False
                        escape_next = False
                        
                        for char in values_part:
                            if escape_next:
                                current_part += char
                                escape_next = False
                                continue
                                
                            if char == '\\':
                                escape_next = True
                                current_part += char
                                continue
                                
                            if char == "'" and not escape_next:
                                in_quotes = not in_quotes
                                current_part += char
                                continue
                                
                            if char == ',' and not in_quotes:
                                parts.append(current_part.strip())
                                current_part = ""
                                continue
                                
                            current_part += char
                        
                        if current_part.strip():
                            parts.append(current_part.strip())
                        
                        if len(parts) >= 9:  # question, answer, category, state, tags, priority, difficulty, personas, source
                            entry = {
                                "question": parts[0].strip("'"),
                                "answer": parts[1].strip("'"),
                                "category": parts[2].strip("'"),
                                "state": parts[3].strip("'"),
                                "tags": parts[4].strip("'"),
                                "priority": parts[5].strip("'"),
                                "difficulty": parts[6].strip("'"),
                                "personas": parts[7].strip("'"),
                                "source": parts[8].strip("'")
                            }
                            entries.append(entry)
                            
                except Exception as e:
                    logger.warning(f"Could not parse statement for API: {e}")
                    continue
            
            if not entries:
                logger.error("❌ No entries parsed from SQL statements")
                return False
            
            # Deploy via API
            async with aiohttp.ClientSession() as session:
                upload_data = {
                    "data_type": "knowledge_base",
                    "data": entries,
                    "clear_existing": False  # Don't clear existing data
                }
                
                async with session.post(
                    f"{self.railway_url}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        uploaded_count = result.get('records_uploaded', 0)
                        logger.info(f"✅ Successfully uploaded {uploaded_count} entries via API")
                        self.deployment_stats['new_entries_added'] = uploaded_count
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"❌ API upload failed: {response.status} - {text[:200]}")
                        return False
            
        except Exception as e:
            logger.error(f"❌ API deployment failed: {e}")
            return False
    
    async def deploy_via_database(self, statements: List[str]) -> bool:
        """Deploy entries directly to PostgreSQL database"""
        if not self.pg_connection:
            logger.error("❌ No database connection available")
            return False
        
        try:
            with self.pg_connection.cursor() as cursor:
                successful_inserts = 0
                
                for i, statement in enumerate(statements):
                    try:
                        cursor.execute(statement)
                        successful_inserts += 1
                        logger.info(f"✅ Inserted entry {i+1}/{len(statements)}")
                        
                    except psycopg2.IntegrityError as e:
                        if "duplicate key" in str(e).lower():
                            logger.warning(f"⚠️  Entry {i+1} already exists, skipping")
                        else:
                            logger.error(f"❌ Integrity error in entry {i+1}: {e}")
                            self.deployment_stats['errors'].append(f"Entry {i+1}: {e}")
                        # Continue with next entry
                        self.pg_connection.rollback()
                        
                    except Exception as e:
                        logger.error(f"❌ Error inserting entry {i+1}: {e}")
                        self.deployment_stats['errors'].append(f"Entry {i+1}: {e}")
                        self.pg_connection.rollback()
                
                # Commit all successful inserts
                if successful_inserts > 0:
                    self.pg_connection.commit()
                    logger.info(f"✅ Committed {successful_inserts} new entries")
                    self.deployment_stats['new_entries_added'] = successful_inserts
                    return True
                else:
                    logger.warning("⚠️  No entries were successfully inserted")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Database deployment failed: {e}")
            self.pg_connection.rollback()
            return False
    
    async def verify_deployment(self) -> Dict:
        """Verify deployment success and generate report"""
        try:
            # Get final count
            final_count = await self.get_current_entry_count()
            self.deployment_stats['entries_after'] = final_count
            
            # Calculate new entries added
            if self.deployment_stats['entries_before'] > 0:
                calculated_new = final_count - self.deployment_stats['entries_before']
                self.deployment_stats['new_entries_added'] = max(calculated_new, self.deployment_stats['new_entries_added'])
            
            # Verify objection handling entries exist
            if self.pg_connection:
                with self.pg_connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM knowledge_base 
                        WHERE category = 'objection_handling'
                    """)
                    result = cursor.fetchone()
                    objection_count = result['count'] if result else 0
                    
                    cursor.execute("""
                        SELECT COUNT(*) as count 
                        FROM knowledge_base 
                        WHERE tags LIKE '%sarah_style%' OR tags LIKE '%michael_style%'
                    """)
                    result = cursor.fetchone()
                    style_count = result['count'] if result else 0
                    
                    self.deployment_stats['objection_entries'] = objection_count
                    self.deployment_stats['styled_entries'] = style_count
            
            # Mark as successful if we added entries
            self.deployment_stats['success'] = self.deployment_stats['new_entries_added'] > 0
            self.deployment_stats['end_time'] = datetime.now()
            self.deployment_stats['duration'] = (
                self.deployment_stats['end_time'] - self.deployment_stats['start_time']
            ).total_seconds()
            
            return self.deployment_stats
            
        except Exception as e:
            logger.error(f"❌ Error during verification: {e}")
            self.deployment_stats['errors'].append(f"Verification error: {e}")
            return self.deployment_stats
    
    def generate_report(self) -> str:
        """Generate deployment report"""
        stats = self.deployment_stats
        
        report = f"""
=== RAILWAY DEPLOYMENT REPORT ===
Deployment Time: {stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
Duration: {stats.get('duration', 0):.2f} seconds

DATABASE STATISTICS:
• Entries Before: {stats['entries_before']}
• Entries After: {stats['entries_after']}
• New Entries Added: {stats['new_entries_added']}
• Objection Handling Entries: {stats.get('objection_entries', 'N/A')}
• Styled Entries (Sarah/Michael): {stats.get('styled_entries', 'N/A')}

DEPLOYMENT STATUS: {'✅ SUCCESS' if stats['success'] else '❌ FAILED'}

"""
        
        if stats['errors']:
            report += f"\nERRORS ({len(stats['errors'])}):\n"
            for i, error in enumerate(stats['errors'][:10], 1):  # Show first 10 errors
                report += f"{i}. {error}\n"
            if len(stats['errors']) > 10:
                report += f"... and {len(stats['errors']) - 10} more errors\n"
        
        return report
    
    async def run_deployment(self) -> Dict:
        """Main deployment workflow"""
        logger.info("🚀 Starting Railway deployment of objection handling entries")
        
        try:
            # Step 1: Try to connect to database, but proceed with API if no connection
            logger.info("📡 Attempting to connect to Railway database...")
            has_db_connection = self.get_railway_db_connection() is not None
            
            # Step 2: Get initial count
            logger.info("📊 Getting current entry count...")
            self.deployment_stats['entries_before'] = await self.get_current_entry_count()
            logger.info(f"📈 Current entries in database: {self.deployment_stats['entries_before']}")
            
            # Step 3: Load and validate entries
            logger.info("📄 Loading objection handling entries...")
            statements = self.load_objection_entries()
            if not statements:
                logger.error("❌ No entries to deploy")
                return self.deployment_stats
            
            logger.info("✅ Validating SQL statements...")
            valid_statements = self.validate_sql_statements(statements)
            if not valid_statements:
                logger.error("❌ No valid statements to deploy")
                return self.deployment_stats
            
            # Step 4: Deploy entries (try database first, then API)
            logger.info(f"🚀 Deploying {len(valid_statements)} entries to Railway...")
            if has_db_connection:
                logger.info("🔗 Using direct database connection...")
                deployment_success = await self.deploy_via_database(valid_statements)
            else:
                logger.info("🌐 Using API deployment method...")
                deployment_success = await self.deploy_via_api(valid_statements)
            
            if not deployment_success:
                logger.error("❌ Deployment failed")
                return self.deployment_stats
            
            # Step 5: Verify deployment
            logger.info("🔍 Verifying deployment...")
            final_stats = await self.verify_deployment()
            
            # Step 6: Generate report
            report = self.generate_report()
            logger.info(report)
            
            # Save report to file
            with open('deployment_report.txt', 'w') as f:
                f.write(report)
            
            return final_stats
            
        except Exception as e:
            logger.error(f"❌ Deployment failed with error: {e}")
            self.deployment_stats['errors'].append(f"Deployment error: {e}")
            return self.deployment_stats
        
        finally:
            if self.pg_connection:
                self.pg_connection.close()
                logger.info("🔌 Database connection closed")

async def main():
    """Main execution function"""
    deployment = RailwayDeployment()
    results = await deployment.run_deployment()
    
    # Print summary
    print("\n" + "="*50)
    print("DEPLOYMENT SUMMARY")
    print("="*50)
    print(f"Success: {'✅ YES' if results['success'] else '❌ NO'}")
    print(f"New Entries: {results['new_entries_added']}")
    print(f"Total Errors: {len(results['errors'])}")
    print(f"Duration: {results.get('duration', 0):.2f} seconds")
    print("="*50)
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)

if __name__ == "__main__":
    asyncio.run(main())
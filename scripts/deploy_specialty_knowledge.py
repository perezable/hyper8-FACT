#!/usr/bin/env python3
"""
Deploy Specialty Contractor License Knowledge to Railway
Comprehensive deployment script for HVAC, Electrical, Plumbing, Roofing, and Flooring contractor knowledge entries.
"""

import os
import sys
import json
import logging
import traceback
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_config
from src.db.postgres_adapter import PostgresAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/natperez/codebases/hyper8/hyper8-FACT/logs/specialty_deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SpecialtyKnowledgeDeployer:
    """Deploy specialty contractor license knowledge to Railway PostgreSQL."""
    
    def __init__(self):
        """Initialize the deployer with configuration."""
        self.config = get_config()
        self.local_db_path = '/Users/natperez/codebases/hyper8/hyper8-FACT/data/knowledge.db'
        self.specialty_sql_path = '/Users/natperez/codebases/hyper8/hyper8-FACT/data/specialty_licenses_knowledge.sql'
        self.postgres_adapter = None
        self.deployment_stats = {
            'start_time': datetime.now(),
            'entries_before': 0,
            'entries_after': 0,
            'specialty_entries_added': 0,
            'errors': [],
            'validation_results': {}
        }
    
    def setup_postgres_connection(self) -> bool:
        """Setup PostgreSQL connection to Railway."""
        try:
            logger.info("Setting up PostgreSQL connection to Railway...")
            
            # Try multiple connection methods
            postgres_configs = [
                {
                    'host': os.getenv('PGHOST', 'junction.proxy.rlwy.net'),
                    'port': int(os.getenv('PGPORT', 28334)),
                    'database': os.getenv('PGDATABASE', 'railway'),
                    'user': os.getenv('PGUSER', 'postgres'),
                    'password': os.getenv('PGPASSWORD', '')
                },
                {
                    'host': os.getenv('DATABASE_HOST', 'junction.proxy.rlwy.net'),
                    'port': int(os.getenv('DATABASE_PORT', 28334)),
                    'database': os.getenv('DATABASE_NAME', 'railway'),
                    'user': os.getenv('DATABASE_USER', 'postgres'),
                    'password': os.getenv('DATABASE_PASSWORD', '')
                }
            ]
            
            for config in postgres_configs:
                if config['password']:  # Only try if password is available
                    try:
                        logger.info(f"Attempting connection to {config['host']}:{config['port']}")
                        self.postgres_adapter = PostgresAdapter(config)
                        
                        # Test connection
                        with self.postgres_adapter.get_connection() as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("SELECT version();")
                                version = cursor.fetchone()[0]
                                logger.info(f"Connected to PostgreSQL: {version}")
                                return True
                                
                    except Exception as e:
                        logger.warning(f"Connection attempt failed: {str(e)}")
                        continue
            
            raise Exception("All PostgreSQL connection attempts failed")
            
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL connection: {str(e)}")
            self.deployment_stats['errors'].append(f"PostgreSQL connection failed: {str(e)}")
            return False
    
    def count_existing_entries(self) -> int:
        """Count existing knowledge base entries."""
        try:
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM knowledge_base;")
                    count = cursor.fetchone()[0]
                    logger.info(f"Found {count} existing knowledge base entries")
                    return count
        except Exception as e:
            logger.error(f"Failed to count existing entries: {str(e)}")
            return 0
    
    def validate_sql_file(self) -> bool:
        """Validate the specialty SQL file before deployment."""
        try:
            logger.info("Validating specialty SQL file...")
            
            if not os.path.exists(self.specialty_sql_path):
                raise FileNotFoundError(f"SQL file not found: {self.specialty_sql_path}")
            
            with open(self.specialty_sql_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic validation checks
            if not content.strip():
                raise ValueError("SQL file is empty")
            
            insert_count = content.count('INSERT INTO knowledge_base')
            if insert_count == 0:
                raise ValueError("No INSERT statements found in SQL file")
            
            logger.info(f"SQL file validation passed - found {insert_count} INSERT statements")
            return True
            
        except Exception as e:
            logger.error(f"SQL file validation failed: {str(e)}")
            self.deployment_stats['errors'].append(f"SQL validation failed: {str(e)}")
            return False
    
    def deploy_specialty_entries(self) -> bool:
        """Deploy specialty contractor license entries to PostgreSQL."""
        try:
            logger.info("Deploying specialty contractor license entries...")
            
            with open(self.specialty_sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split into individual INSERT statements
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip() and 'INSERT INTO' in stmt]
            
            successful_inserts = 0
            failed_inserts = 0
            
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor() as cursor:
                    for i, statement in enumerate(statements, 1):
                        try:
                            cursor.execute(statement + ';')
                            successful_inserts += 1
                            logger.debug(f"Inserted statement {i}/{len(statements)}")
                        except Exception as e:
                            failed_inserts += 1
                            logger.warning(f"Failed to insert statement {i}: {str(e)}")
                            # Continue with other statements
                    
                    # Commit all successful inserts
                    conn.commit()
                    logger.info(f"Successfully inserted {successful_inserts} entries, {failed_inserts} failed")
            
            self.deployment_stats['specialty_entries_added'] = successful_inserts
            
            if failed_inserts > 0:
                self.deployment_stats['errors'].append(f"{failed_inserts} entries failed to insert")
            
            return successful_inserts > 0
            
        except Exception as e:
            logger.error(f"Failed to deploy specialty entries: {str(e)}")
            self.deployment_stats['errors'].append(f"Deployment failed: {str(e)}")
            return False
    
    def validate_deployment(self) -> Dict[str, Any]:
        """Validate the deployment by testing search functionality."""
        validation_results = {
            'total_entries': 0,
            'specialty_entries': 0,
            'search_tests': {},
            'category_distribution': {},
            'state_coverage': {},
            'errors': []
        }
        
        try:
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Count total entries
                    cursor.execute("SELECT COUNT(*) as count FROM knowledge_base;")
                    validation_results['total_entries'] = cursor.fetchone()['count']
                    
                    # Count specialty entries (added today)
                    cursor.execute("""
                        SELECT COUNT(*) as count FROM knowledge_base 
                        WHERE created_at >= CURRENT_DATE 
                        AND category LIKE '%specialty%';
                    """)
                    validation_results['specialty_entries'] = cursor.fetchone()['count']
                    
                    # Category distribution
                    cursor.execute("""
                        SELECT category, COUNT(*) as count 
                        FROM knowledge_base 
                        GROUP BY category 
                        ORDER BY count DESC;
                    """)
                    validation_results['category_distribution'] = {
                        row['category']: row['count'] for row in cursor.fetchall()
                    }
                    
                    # State coverage
                    cursor.execute("""
                        SELECT state, COUNT(*) as count 
                        FROM knowledge_base 
                        WHERE state IS NOT NULL AND state != '' 
                        GROUP BY state 
                        ORDER BY count DESC;
                    """)
                    validation_results['state_coverage'] = {
                        row['state']: row['count'] for row in cursor.fetchall()
                    }
                    
                    # Test searches for each specialty
                    search_tests = {
                        'hvac': "SELECT COUNT(*) as count FROM knowledge_base WHERE question ILIKE '%hvac%' OR answer ILIKE '%hvac%';",
                        'electrical': "SELECT COUNT(*) as count FROM knowledge_base WHERE question ILIKE '%electrical%' OR answer ILIKE '%electrical%';",
                        'plumbing': "SELECT COUNT(*) as count FROM knowledge_base WHERE question ILIKE '%plumbing%' OR answer ILIKE '%plumbing%';",
                        'roofing': "SELECT COUNT(*) as count FROM knowledge_base WHERE question ILIKE '%roofing%' OR answer ILIKE '%roofing%';",
                        'flooring': "SELECT COUNT(*) as count FROM knowledge_base WHERE question ILIKE '%flooring%' OR answer ILIKE '%flooring%';",
                        'epa_608': "SELECT COUNT(*) as count FROM knowledge_base WHERE question ILIKE '%epa 608%' OR answer ILIKE '%epa 608%';",
                        'nate': "SELECT COUNT(*) as count FROM knowledge_base WHERE question ILIKE '%nate%' OR answer ILIKE '%nate%';",
                        'osha': "SELECT COUNT(*) as count FROM knowledge_base WHERE question ILIKE '%osha%' OR answer ILIKE '%osha%';"
                    }
                    
                    for test_name, query in search_tests.items():
                        cursor.execute(query)
                        validation_results['search_tests'][test_name] = cursor.fetchone()['count']
                    
                    logger.info("Deployment validation completed successfully")
                    
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            validation_results['errors'].append(str(e))
        
        return validation_results
    
    def test_vapi_webhook_integration(self) -> bool:
        """Test integration with VAPI webhook."""
        try:
            logger.info("Testing VAPI webhook integration...")
            
            # Test queries that would come from VAPI
            test_queries = [
                "hvac license requirements california",
                "electrical contractor license texas",
                "plumbing license florida",
                "roofing contractor insurance",
                "flooring license new york"
            ]
            
            successful_tests = 0
            
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    for query in test_queries:
                        try:
                            # Simulate VAPI-style search
                            search_sql = """
                                SELECT question, answer, category, state, tags 
                                FROM knowledge_base 
                                WHERE question ILIKE %s OR answer ILIKE %s 
                                ORDER BY 
                                    CASE 
                                        WHEN question ILIKE %s THEN 1 
                                        WHEN answer ILIKE %s THEN 2 
                                        ELSE 3 
                                    END 
                                LIMIT 3;
                            """
                            search_term = f"%{query}%"
                            cursor.execute(search_sql, (search_term, search_term, search_term, search_term))
                            results = cursor.fetchall()
                            
                            if results:
                                successful_tests += 1
                                logger.debug(f"Query '{query}' returned {len(results)} results")
                            else:
                                logger.warning(f"Query '{query}' returned no results")
                                
                        except Exception as e:
                            logger.error(f"Test query '{query}' failed: {str(e)}")
            
            success_rate = successful_tests / len(test_queries)
            logger.info(f"VAPI integration test: {successful_tests}/{len(test_queries)} queries successful ({success_rate:.1%})")
            
            return success_rate >= 0.8  # 80% success rate required
            
        except Exception as e:
            logger.error(f"VAPI webhook integration test failed: {str(e)}")
            return False
    
    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment report."""
        self.deployment_stats['end_time'] = datetime.now()
        self.deployment_stats['duration'] = (
            self.deployment_stats['end_time'] - self.deployment_stats['start_time']
        ).total_seconds()
        
        report = {
            'deployment_summary': {
                'timestamp': self.deployment_stats['end_time'].isoformat(),
                'duration_seconds': self.deployment_stats['duration'],
                'status': 'SUCCESS' if len(self.deployment_stats['errors']) == 0 else 'PARTIAL' if self.deployment_stats['specialty_entries_added'] > 0 else 'FAILED',
                'entries_before': self.deployment_stats['entries_before'],
                'entries_after': self.deployment_stats['entries_after'],
                'specialty_entries_added': self.deployment_stats['specialty_entries_added'],
                'errors': self.deployment_stats['errors']
            },
            'validation_results': self.deployment_stats['validation_results'],
            'specialty_coverage': {
                'hvac_entries': self.deployment_stats['validation_results'].get('search_tests', {}).get('hvac', 0),
                'electrical_entries': self.deployment_stats['validation_results'].get('search_tests', {}).get('electrical', 0),
                'plumbing_entries': self.deployment_stats['validation_results'].get('search_tests', {}).get('plumbing', 0),
                'roofing_entries': self.deployment_stats['validation_results'].get('search_tests', {}).get('roofing', 0),
                'flooring_entries': self.deployment_stats['validation_results'].get('search_tests', {}).get('flooring', 0)
            },
            'certification_coverage': {
                'epa_608_entries': self.deployment_stats['validation_results'].get('search_tests', {}).get('epa_608', 0),
                'nate_entries': self.deployment_stats['validation_results'].get('search_tests', {}).get('nate', 0),
                'osha_entries': self.deployment_stats['validation_results'].get('search_tests', {}).get('osha', 0)
            },
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on deployment results."""
        recommendations = []
        
        if self.deployment_stats['specialty_entries_added'] > 40:
            recommendations.append("✅ Excellent specialty coverage achieved - all 5 major trades covered comprehensively")
        elif self.deployment_stats['specialty_entries_added'] > 25:
            recommendations.append("⚠️ Good specialty coverage - consider adding more state-specific entries")
        else:
            recommendations.append("❌ Limited specialty coverage - need more comprehensive entries")
        
        validation = self.deployment_stats.get('validation_results', {})
        search_tests = validation.get('search_tests', {})
        
        if search_tests.get('hvac', 0) < 5:
            recommendations.append("📋 Add more HVAC-specific entries for EPA 608, NATE certification")
        
        if search_tests.get('electrical', 0) < 5:
            recommendations.append("📋 Add more electrical entries for IBEW, OSHA, arc flash safety")
        
        if search_tests.get('plumbing', 0) < 5:
            recommendations.append("📋 Add more plumbing entries for backflow prevention, medical gas")
        
        state_coverage = validation.get('state_coverage', {})
        if len(state_coverage) < 8:
            recommendations.append("📍 Expand state coverage - target top 10 construction states")
        
        if len(self.deployment_stats['errors']) > 0:
            recommendations.append("🔧 Address deployment errors for 100% success rate")
        
        return recommendations
    
    def run_deployment(self) -> Dict[str, Any]:
        """Run the complete specialty knowledge deployment process."""
        logger.info("=" * 60)
        logger.info("STARTING SPECIALTY CONTRACTOR LICENSE KNOWLEDGE DEPLOYMENT")
        logger.info("=" * 60)
        
        try:
            # Step 1: Setup PostgreSQL connection
            if not self.setup_postgres_connection():
                raise Exception("Failed to setup PostgreSQL connection")
            
            # Step 2: Count existing entries
            self.deployment_stats['entries_before'] = self.count_existing_entries()
            
            # Step 3: Validate SQL file
            if not self.validate_sql_file():
                raise Exception("SQL file validation failed")
            
            # Step 4: Deploy specialty entries
            if not self.deploy_specialty_entries():
                raise Exception("Failed to deploy specialty entries")
            
            # Step 5: Count entries after deployment
            self.deployment_stats['entries_after'] = self.count_existing_entries()
            
            # Step 6: Validate deployment
            self.deployment_stats['validation_results'] = self.validate_deployment()
            
            # Step 7: Test VAPI integration
            vapi_success = self.test_vapi_webhook_integration()
            self.deployment_stats['validation_results']['vapi_integration'] = vapi_success
            
            # Step 8: Generate report
            report = self.generate_deployment_report()
            
            logger.info("=" * 60)
            logger.info("DEPLOYMENT COMPLETED SUCCESSFULLY")
            logger.info("=" * 60)
            
            return report
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            logger.error(traceback.format_exc())
            
            self.deployment_stats['errors'].append(f"Critical failure: {str(e)}")
            report = self.generate_deployment_report()
            
            return report


def main():
    """Main deployment function."""
    deployer = SpecialtyKnowledgeDeployer()
    report = deployer.run_deployment()
    
    # Save report to file
    report_path = '/Users/natperez/codebases/hyper8/hyper8-FACT/logs/specialty_deployment_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SPECIALTY CONTRACTOR LICENSE DEPLOYMENT SUMMARY")
    print("=" * 80)
    print(f"Status: {report['deployment_summary']['status']}")
    print(f"Duration: {report['deployment_summary']['duration_seconds']:.2f} seconds")
    print(f"Entries Before: {report['deployment_summary']['entries_before']}")
    print(f"Entries After: {report['deployment_summary']['entries_after']}")
    print(f"Specialty Entries Added: {report['deployment_summary']['specialty_entries_added']}")
    
    print(f"\nSpecialty Coverage:")
    specialty_coverage = report['specialty_coverage']
    for specialty, count in specialty_coverage.items():
        print(f"  {specialty}: {count} entries")
    
    print(f"\nCertification Coverage:")
    cert_coverage = report['certification_coverage']
    for cert, count in cert_coverage.items():
        print(f"  {cert}: {count} entries")
    
    if report['deployment_summary']['errors']:
        print(f"\nErrors ({len(report['deployment_summary']['errors'])}):")
        for error in report['deployment_summary']['errors']:
            print(f"  ❌ {error}")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    print(f"\nFull report saved to: {report_path}")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    main()
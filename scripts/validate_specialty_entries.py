#!/usr/bin/env python3
"""
Validate Specialty Contractor License Knowledge Entries
Comprehensive testing and validation script for specialty trade knowledge base entries.
"""

import os
import sys
import json
import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import re

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.config import get_config
from src.db.postgres_adapter import PostgresAdapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SpecialtyKnowledgeValidator:
    """Validate specialty contractor license knowledge entries."""
    
    def __init__(self):
        """Initialize the validator."""
        self.config = get_config()
        self.postgres_adapter = None
        self.validation_results = {
            'timestamp': datetime.now(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_results': {},
            'content_analysis': {},
            'search_performance': {},
            'data_quality': {},
            'recommendations': []
        }
        
        # Define test categories and expected content
        self.specialty_categories = {
            'hvac': ['EPA 608', 'NATE', 'refrigerant', 'mechanical', 'heating', 'air conditioning'],
            'electrical': ['IBEW', 'OSHA', 'arc flash', 'electrician', 'master electrician', 'journeyman'],
            'plumbing': ['backflow', 'medical gas', 'ASSE', 'master plumber', 'water', 'pipe'],
            'roofing': ['GAF', 'Owens Corning', 'OSHA', 'fall protection', 'shingle', 'hurricane'],
            'flooring': ['TCNA', 'NWFA', 'tile', 'hardwood', 'carpet', 'ceramic']
        }
        
        self.target_states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
        
    def setup_postgres_connection(self) -> bool:
        """Setup PostgreSQL connection."""
        try:
            postgres_configs = [
                {
                    'host': os.getenv('PGHOST', 'junction.proxy.rlwy.net'),
                    'port': int(os.getenv('PGPORT', 28334)),
                    'database': os.getenv('PGDATABASE', 'railway'),
                    'user': os.getenv('PGUSER', 'postgres'),
                    'password': os.getenv('PGPASSWORD', '')
                }
            ]
            
            for config in postgres_configs:
                if config['password']:
                    try:
                        self.postgres_adapter = PostgresAdapter(config)
                        with self.postgres_adapter.get_connection() as conn:
                            with conn.cursor() as cursor:
                                cursor.execute("SELECT version();")
                                return True
                    except Exception:
                        continue
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL: {str(e)}")
            return False
    
    def test_database_connectivity(self) -> Dict[str, Any]:
        """Test database connectivity and basic operations."""
        test_result = {
            'name': 'Database Connectivity',
            'status': 'FAILED',
            'details': {},
            'errors': []
        }
        
        try:
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Test basic query
                    cursor.execute("SELECT COUNT(*) as count FROM knowledge_base;")
                    total_count = cursor.fetchone()['count']
                    test_result['details']['total_entries'] = total_count
                    
                    # Test table structure
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'knowledge_base'
                        ORDER BY ordinal_position;
                    """)
                    columns = cursor.fetchall()
                    test_result['details']['table_structure'] = {
                        row['column_name']: row['data_type'] for row in columns
                    }
                    
                    # Required columns check
                    required_columns = ['id', 'question', 'answer', 'category', 'state', 'tags', 'priority', 'difficulty', 'personas', 'source']
                    existing_columns = set(test_result['details']['table_structure'].keys())
                    missing_columns = set(required_columns) - existing_columns
                    
                    if missing_columns:
                        test_result['errors'].append(f"Missing required columns: {missing_columns}")
                    else:
                        test_result['status'] = 'PASSED'
                        
        except Exception as e:
            test_result['errors'].append(str(e))
            
        return test_result
    
    def test_specialty_content_coverage(self) -> Dict[str, Any]:
        """Test coverage of specialty contractor content."""
        test_result = {
            'name': 'Specialty Content Coverage',
            'status': 'FAILED',
            'details': {},
            'errors': []
        }
        
        try:
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    coverage_results = {}
                    
                    for specialty, keywords in self.specialty_categories.items():
                        # Count entries containing specialty keywords
                        keyword_conditions = [
                            f"(question ILIKE '%{keyword}%' OR answer ILIKE '%{keyword}%')"
                            for keyword in keywords
                        ]
                        query = f"""
                            SELECT COUNT(*) as count 
                            FROM knowledge_base 
                            WHERE {' OR '.join(keyword_conditions)};
                        """
                        
                        cursor.execute(query)
                        count = cursor.fetchone()['count']
                        coverage_results[specialty] = {
                            'entry_count': count,
                            'keywords_found': []
                        }
                        
                        # Check which specific keywords are covered
                        for keyword in keywords:
                            cursor.execute("""
                                SELECT COUNT(*) as count 
                                FROM knowledge_base 
                                WHERE question ILIKE %s OR answer ILIKE %s;
                            """, (f'%{keyword}%', f'%{keyword}%'))
                            
                            keyword_count = cursor.fetchone()['count']
                            if keyword_count > 0:
                                coverage_results[specialty]['keywords_found'].append(keyword)
                    
                    test_result['details']['specialty_coverage'] = coverage_results
                    
                    # Determine overall test status
                    total_specialties_covered = sum(1 for spec_data in coverage_results.values() if spec_data['entry_count'] > 0)
                    coverage_percentage = total_specialties_covered / len(self.specialty_categories)
                    
                    test_result['details']['coverage_percentage'] = coverage_percentage * 100
                    
                    if coverage_percentage >= 0.8:  # 80% coverage required
                        test_result['status'] = 'PASSED'
                    else:
                        test_result['errors'].append(f"Only {coverage_percentage:.1%} specialty coverage (need 80%)")
                        
        except Exception as e:
            test_result['errors'].append(str(e))
            
        return test_result
    
    def test_state_coverage(self) -> Dict[str, Any]:
        """Test coverage of target states."""
        test_result = {
            'name': 'State Coverage',
            'status': 'FAILED',
            'details': {},
            'errors': []
        }
        
        try:
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Count entries per state
                    cursor.execute("""
                        SELECT state, COUNT(*) as count 
                        FROM knowledge_base 
                        WHERE state IS NOT NULL AND state != '' 
                        GROUP BY state 
                        ORDER BY count DESC;
                    """)
                    
                    state_counts = {row['state']: row['count'] for row in cursor.fetchall()}
                    test_result['details']['state_distribution'] = state_counts
                    
                    # Check coverage of target states
                    covered_target_states = [state for state in self.target_states if state in state_counts]
                    test_result['details']['target_states_covered'] = covered_target_states
                    test_result['details']['target_states_missing'] = [
                        state for state in self.target_states if state not in state_counts
                    ]
                    
                    coverage_percentage = len(covered_target_states) / len(self.target_states)
                    test_result['details']['target_coverage_percentage'] = coverage_percentage * 100
                    
                    if coverage_percentage >= 0.7:  # 70% of target states
                        test_result['status'] = 'PASSED'
                    else:
                        test_result['errors'].append(f"Only {coverage_percentage:.1%} target state coverage")
                        
        except Exception as e:
            test_result['errors'].append(str(e))
            
        return test_result
    
    def test_search_functionality(self) -> Dict[str, Any]:
        """Test search functionality with common queries."""
        test_result = {
            'name': 'Search Functionality',
            'status': 'FAILED',
            'details': {},
            'errors': []
        }
        
        test_queries = [
            # HVAC queries
            "EPA 608 certification requirements",
            "HVAC license California",
            "NATE certification benefits",
            
            # Electrical queries
            "electrical contractor license Texas",
            "IBEW apprenticeship program",
            "OSHA electrical safety training",
            
            # Plumbing queries
            "plumbing license Florida",
            "backflow prevention certification",
            "medical gas plumbing ASSE 6010",
            
            # Roofing queries
            "roofing contractor license requirements",
            "GAF Master Elite certification",
            "roofing safety OSHA fall protection",
            
            # Flooring queries
            "flooring contractor license",
            "TCNA ceramic tile certification",
            "hardwood flooring NWFA certification"
        ]
        
        try:
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    search_results = {}
                    successful_searches = 0
                    
                    for query in test_queries:
                        try:
                            # Test relevance-based search
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
                                LIMIT 5;
                            """
                            search_term = f"%{query}%"
                            cursor.execute(search_sql, (search_term, search_term, search_term, search_term))
                            results = cursor.fetchall()
                            
                            search_results[query] = {
                                'result_count': len(results),
                                'results': [dict(row) for row in results[:2]]  # Top 2 for review
                            }
                            
                            if len(results) > 0:
                                successful_searches += 1
                                
                        except Exception as e:
                            search_results[query] = {'error': str(e)}
                    
                    test_result['details']['search_results'] = search_results
                    test_result['details']['successful_searches'] = successful_searches
                    test_result['details']['total_test_queries'] = len(test_queries)
                    test_result['details']['success_rate'] = successful_searches / len(test_queries)
                    
                    if test_result['details']['success_rate'] >= 0.8:  # 80% success rate
                        test_result['status'] = 'PASSED'
                    else:
                        test_result['errors'].append(f"Search success rate only {test_result['details']['success_rate']:.1%}")
                        
        except Exception as e:
            test_result['errors'].append(str(e))
            
        return test_result
    
    def test_data_quality(self) -> Dict[str, Any]:
        """Test data quality and completeness."""
        test_result = {
            'name': 'Data Quality',
            'status': 'FAILED',
            'details': {},
            'errors': []
        }
        
        try:
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    quality_metrics = {}
                    
                    # Check for required field completeness
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_entries,
                            COUNT(CASE WHEN question IS NULL OR question = '' THEN 1 END) as missing_questions,
                            COUNT(CASE WHEN answer IS NULL OR answer = '' THEN 1 END) as missing_answers,
                            COUNT(CASE WHEN category IS NULL OR category = '' THEN 1 END) as missing_categories,
                            COUNT(CASE WHEN tags IS NULL OR tags = '' THEN 1 END) as missing_tags,
                            COUNT(CASE WHEN priority IS NULL OR priority = '' THEN 1 END) as missing_priority,
                            COUNT(CASE WHEN difficulty IS NULL OR difficulty = '' THEN 1 END) as missing_difficulty,
                            COUNT(CASE WHEN personas IS NULL OR personas = '' THEN 1 END) as missing_personas,
                            COUNT(CASE WHEN source IS NULL OR source = '' THEN 1 END) as missing_source
                        FROM knowledge_base;
                    """)
                    
                    completeness = cursor.fetchone()
                    quality_metrics['field_completeness'] = dict(completeness)
                    
                    # Check answer lengths (quality indicator)
                    cursor.execute("""
                        SELECT 
                            AVG(LENGTH(answer)) as avg_answer_length,
                            MIN(LENGTH(answer)) as min_answer_length,
                            MAX(LENGTH(answer)) as max_answer_length,
                            COUNT(CASE WHEN LENGTH(answer) < 100 THEN 1 END) as short_answers,
                            COUNT(CASE WHEN LENGTH(answer) > 1000 THEN 1 END) as long_answers
                        FROM knowledge_base 
                        WHERE answer IS NOT NULL;
                    """)
                    
                    length_stats = cursor.fetchone()
                    quality_metrics['answer_length_stats'] = dict(length_stats)
                    
                    # Check for duplicate questions
                    cursor.execute("""
                        SELECT question, COUNT(*) as count 
                        FROM knowledge_base 
                        GROUP BY question 
                        HAVING COUNT(*) > 1
                        ORDER BY count DESC;
                    """)
                    
                    duplicates = cursor.fetchall()
                    quality_metrics['duplicate_questions'] = len(duplicates)
                    quality_metrics['duplicate_examples'] = [dict(row) for row in duplicates[:5]]
                    
                    # Check category distribution
                    cursor.execute("""
                        SELECT category, COUNT(*) as count 
                        FROM knowledge_base 
                        GROUP BY category 
                        ORDER BY count DESC;
                    """)
                    
                    categories = cursor.fetchall()
                    quality_metrics['category_distribution'] = {row['category']: row['count'] for row in categories}
                    
                    test_result['details']['quality_metrics'] = quality_metrics
                    
                    # Determine test status based on quality thresholds
                    issues = []
                    
                    if completeness['missing_questions'] > 0:
                        issues.append(f"{completeness['missing_questions']} missing questions")
                    
                    if completeness['missing_answers'] > 0:
                        issues.append(f"{completeness['missing_answers']} missing answers")
                    
                    if length_stats['avg_answer_length'] < 200:
                        issues.append(f"Average answer length too short: {length_stats['avg_answer_length']:.0f} chars")
                    
                    if quality_metrics['duplicate_questions'] > 0:
                        issues.append(f"{quality_metrics['duplicate_questions']} duplicate questions")
                    
                    if issues:
                        test_result['errors'] = issues
                    else:
                        test_result['status'] = 'PASSED'
                        
        except Exception as e:
            test_result['errors'].append(str(e))
            
        return test_result
    
    def test_vapi_integration_simulation(self) -> Dict[str, Any]:
        """Simulate VAPI webhook integration scenarios."""
        test_result = {
            'name': 'VAPI Integration Simulation',
            'status': 'FAILED',
            'details': {},
            'errors': []
        }
        
        # Simulate typical VAPI voice queries
        vapi_scenarios = [
            {
                'query': "I need to get an HVAC license in California",
                'expected_content': ['California', 'HVAC', 'C-20', 'EPA 608']
            },
            {
                'query': "What is EPA 608 certification",
                'expected_content': ['EPA 608', 'refrigerant', 'certification']
            },
            {
                'query': "How much does electrical license cost in Texas",
                'expected_content': ['Texas', 'electrical', 'cost', 'fee']
            },
            {
                'query': "Plumbing license requirements Florida",
                'expected_content': ['Florida', 'plumbing', 'requirement']
            },
            {
                'query': "Roofing safety OSHA training",
                'expected_content': ['roofing', 'safety', 'OSHA', 'fall protection']
            }
        ]
        
        try:
            with self.postgres_adapter.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    scenario_results = {}
                    successful_scenarios = 0
                    
                    for scenario in vapi_scenarios:
                        query = scenario['query']
                        expected_content = scenario['expected_content']
                        
                        # Search for relevant entries
                        search_sql = """
                            SELECT question, answer, category, state, tags,
                                   ts_rank_cd(to_tsvector('english', question || ' ' || answer), 
                                             plainto_tsquery('english', %s)) as rank
                            FROM knowledge_base 
                            WHERE to_tsvector('english', question || ' ' || answer) @@ plainto_tsquery('english', %s)
                            ORDER BY rank DESC
                            LIMIT 3;
                        """
                        
                        try:
                            cursor.execute(search_sql, (query, query))
                            results = cursor.fetchall()
                        except:
                            # Fallback to ILIKE search if full-text search fails
                            fallback_sql = """
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
                            cursor.execute(fallback_sql, (search_term, search_term, search_term, search_term))
                            results = cursor.fetchall()
                        
                        # Analyze results for expected content
                        content_matches = 0
                        if results:
                            combined_text = ' '.join([
                                f"{row['question']} {row['answer']} {row['tags'] or ''}"
                                for row in results
                            ]).lower()
                            
                            content_matches = sum(1 for content in expected_content 
                                                if content.lower() in combined_text)
                        
                        scenario_results[query] = {
                            'result_count': len(results),
                            'expected_content_matches': content_matches,
                            'expected_content_total': len(expected_content),
                            'match_percentage': content_matches / len(expected_content) if expected_content else 0,
                            'top_result': dict(results[0]) if results else None
                        }
                        
                        if len(results) > 0 and content_matches >= len(expected_content) * 0.5:  # 50% content match
                            successful_scenarios += 1
                    
                    test_result['details']['scenario_results'] = scenario_results
                    test_result['details']['successful_scenarios'] = successful_scenarios
                    test_result['details']['total_scenarios'] = len(vapi_scenarios)
                    test_result['details']['success_rate'] = successful_scenarios / len(vapi_scenarios)
                    
                    if test_result['details']['success_rate'] >= 0.8:  # 80% success rate
                        test_result['status'] = 'PASSED'
                    else:
                        test_result['errors'].append(f"VAPI scenario success rate only {test_result['details']['success_rate']:.1%}")
                        
        except Exception as e:
            test_result['errors'].append(str(e))
            
        return test_result
    
    def generate_recommendations(self, all_test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Analyze each test result
        for test in all_test_results:
            if test['status'] == 'FAILED':
                test_name = test['name']
                
                if 'Database Connectivity' in test_name:
                    recommendations.append("🔧 Fix database connectivity issues before proceeding")
                
                elif 'Specialty Content Coverage' in test_name:
                    coverage = test['details'].get('coverage_percentage', 0)
                    if coverage < 80:
                        recommendations.append(f"📋 Increase specialty coverage from {coverage:.1f}% to 80%+")
                        
                        # Specific specialty recommendations
                        specialty_coverage = test['details'].get('specialty_coverage', {})
                        for specialty, data in specialty_coverage.items():
                            if data['entry_count'] < 5:
                                recommendations.append(f"  ➕ Add more {specialty.upper()} entries (current: {data['entry_count']})")
                
                elif 'State Coverage' in test_name:
                    missing_states = test['details'].get('target_states_missing', [])
                    if missing_states:
                        recommendations.append(f"🗺️ Add entries for missing states: {', '.join(missing_states)}")
                
                elif 'Search Functionality' in test_name:
                    success_rate = test['details'].get('success_rate', 0)
                    if success_rate < 0.8:
                        recommendations.append(f"🔍 Improve search relevance (current: {success_rate:.1%})")
                
                elif 'Data Quality' in test_name:
                    if test['errors']:
                        recommendations.append("📊 Address data quality issues:")
                        for error in test['errors']:
                            recommendations.append(f"  🔸 {error}")
                
                elif 'VAPI Integration' in test_name:
                    success_rate = test['details'].get('success_rate', 0)
                    if success_rate < 0.8:
                        recommendations.append(f"🎙️ Improve VAPI integration compatibility (current: {success_rate:.1%})")
        
        # Overall recommendations
        passed_tests = sum(1 for test in all_test_results if test['status'] == 'PASSED')
        total_tests = len(all_test_results)
        
        if passed_tests == total_tests:
            recommendations.append("✅ All tests passed! Knowledge base is ready for production")
        elif passed_tests >= total_tests * 0.8:
            recommendations.append("⚠️ Most tests passed. Address remaining issues for production readiness")
        else:
            recommendations.append("❌ Multiple critical issues found. Significant improvements needed")
        
        return recommendations
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        logger.info("=" * 60)
        logger.info("STARTING SPECIALTY KNOWLEDGE VALIDATION")
        logger.info("=" * 60)
        
        # Setup database connection
        if not self.setup_postgres_connection():
            return {
                'status': 'FAILED',
                'error': 'Could not connect to database',
                'validation_results': self.validation_results
            }
        
        # Define tests to run
        tests = [
            self.test_database_connectivity,
            self.test_specialty_content_coverage,
            self.test_state_coverage,
            self.test_search_functionality,
            self.test_data_quality,
            self.test_vapi_integration_simulation
        ]
        
        all_test_results = []
        
        # Run each test
        for test_func in tests:
            try:
                logger.info(f"Running {test_func.__name__}...")
                result = test_func()
                all_test_results.append(result)
                
                self.validation_results['total_tests'] += 1
                if result['status'] == 'PASSED':
                    self.validation_results['passed_tests'] += 1
                    logger.info(f"✅ {result['name']}: PASSED")
                else:
                    self.validation_results['failed_tests'] += 1
                    logger.warning(f"❌ {result['name']}: FAILED")
                    for error in result.get('errors', []):
                        logger.warning(f"   Error: {error}")
                
            except Exception as e:
                logger.error(f"Test {test_func.__name__} crashed: {str(e)}")
                all_test_results.append({
                    'name': test_func.__name__,
                    'status': 'CRASHED',
                    'errors': [str(e)]
                })
                self.validation_results['total_tests'] += 1
                self.validation_results['failed_tests'] += 1
        
        # Store test results
        self.validation_results['test_results'] = all_test_results
        
        # Generate recommendations
        self.validation_results['recommendations'] = self.generate_recommendations(all_test_results)
        
        # Calculate overall status
        success_rate = self.validation_results['passed_tests'] / self.validation_results['total_tests']
        if success_rate >= 0.8:
            overall_status = 'PASSED'
        elif success_rate >= 0.6:
            overall_status = 'PARTIAL'
        else:
            overall_status = 'FAILED'
        
        self.validation_results['overall_status'] = overall_status
        self.validation_results['success_rate'] = success_rate
        
        logger.info("=" * 60)
        logger.info(f"VALIDATION COMPLETED: {overall_status}")
        logger.info(f"Success Rate: {success_rate:.1%} ({self.validation_results['passed_tests']}/{self.validation_results['total_tests']})")
        logger.info("=" * 60)
        
        return {
            'status': overall_status,
            'validation_results': self.validation_results
        }


def main():
    """Main validation function."""
    validator = SpecialtyKnowledgeValidator()
    result = validator.run_validation()
    
    # Save validation report
    report_path = '/Users/natperez/codebases/hyper8/hyper8-FACT/logs/specialty_validation_report.json'
    with open(report_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    # Print summary
    validation_results = result['validation_results']
    
    print("\n" + "=" * 80)
    print("SPECIALTY KNOWLEDGE VALIDATION SUMMARY")
    print("=" * 80)
    print(f"Overall Status: {result['status']}")
    print(f"Success Rate: {validation_results['success_rate']:.1%}")
    print(f"Tests Passed: {validation_results['passed_tests']}/{validation_results['total_tests']}")
    
    print(f"\nTest Results:")
    for test in validation_results['test_results']:
        status_emoji = "✅" if test['status'] == 'PASSED' else "❌"
        print(f"  {status_emoji} {test['name']}: {test['status']}")
        if test['status'] != 'PASSED' and test.get('errors'):
            for error in test['errors'][:2]:  # Show first 2 errors
                print(f"     ⚠️ {error}")
    
    print(f"\nRecommendations:")
    for recommendation in validation_results['recommendations']:
        print(f"  {recommendation}")
    
    print(f"\nDetailed report saved to: {report_path}")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    main()
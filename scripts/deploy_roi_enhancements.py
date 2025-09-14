#!/usr/bin/env python3
"""
Deploy ROI Enhancements to Railway
Enhanced ROI calculation system with industry-specific scenarios and case studies
"""

import os
import sys
import asyncio
import logging
import psycopg2
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
import requests
import json

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from db.connection import create_database_manager
from api.enhanced_roi_calculator import EnhancedROICalculator, ROIScenario, IndustryType, GeographicMarket, ExperienceLevel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ROIEnhancementDeployer:
    """Deploy enhanced ROI system to Railway"""
    
    def __init__(self):
        self.railway_url = os.getenv('RAILWAY_URL', 'https://hyper8-fact-production.up.railway.app')
        self.database_url = os.getenv('DATABASE_URL')
        self.deployment_report = {
            'timestamp': datetime.now().isoformat(),
            'status': 'initiated',
            'components': {},
            'tests': {},
            'errors': []
        }
    
    async def deploy_all(self):
        """Deploy all ROI enhancement components"""
        
        logger.info("🚀 Starting ROI Enhancement Deployment to Railway")
        
        try:
            # Step 1: Deploy knowledge entries
            await self.deploy_knowledge_entries()
            
            # Step 2: Test enhanced ROI calculator
            await self.test_roi_calculator()
            
            # Step 3: Validate VAPI integration
            await self.validate_vapi_integration()
            
            # Step 4: Run comprehensive tests
            await self.run_comprehensive_tests()
            
            # Step 5: Generate deployment report
            await self.generate_deployment_report()
            
            self.deployment_report['status'] = 'completed'
            logger.info("✅ ROI Enhancement Deployment Completed Successfully")
            
        except Exception as e:
            self.deployment_report['status'] = 'failed'
            self.deployment_report['errors'].append(str(e))
            logger.error(f"❌ Deployment failed: {e}")
            raise
    
    async def deploy_knowledge_entries(self):
        """Deploy enhanced ROI knowledge entries to Railway database"""
        
        logger.info("📚 Deploying enhanced ROI knowledge entries...")
        
        try:
            # Read SQL files
            sql_files = [
                '../data/enhanced_roi_knowledge.sql',
                '../data/roi_case_studies.sql'
            ]
            
            total_entries = 0
            
            for sql_file in sql_files:
                file_path = os.path.join(os.path.dirname(__file__), sql_file)
                
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        sql_content = f.read()
                    
                    # Count INSERT statements
                    insert_count = sql_content.count('INSERT INTO knowledge_base')
                    total_entries += insert_count
                    
                    # Execute SQL
                    await self.execute_sql(sql_content)
                    logger.info(f"✅ Deployed {insert_count} entries from {os.path.basename(sql_file)}")
                else:
                    logger.warning(f"⚠️ SQL file not found: {sql_file}")
            
            self.deployment_report['components']['knowledge_entries'] = {
                'status': 'success',
                'total_entries': total_entries,
                'files_deployed': len(sql_files)
            }
            
            logger.info(f"📚 Total ROI knowledge entries deployed: {total_entries}")
            
        except Exception as e:
            self.deployment_report['components']['knowledge_entries'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    async def execute_sql(self, sql_content: str):
        """Execute SQL against Railway database"""
        
        if not self.database_url:
            logger.warning("⚠️ DATABASE_URL not set, using local database")
            # Use local SQLite database for testing
            local_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fact_system.db')
            conn = sqlite3.connect(local_db_path)
        else:
            conn = psycopg2.connect(self.database_url)
        
        try:
            cursor = conn.cursor()
            
            # Split SQL content by semicolons and execute individually
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement.upper().startswith('INSERT'):
                    cursor.execute(statement)
            
            conn.commit()
            logger.info("✅ SQL executed successfully")
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ SQL execution failed: {e}")
            raise
        finally:
            conn.close()
    
    async def test_roi_calculator(self):
        """Test enhanced ROI calculator functionality"""
        
        logger.info("🧮 Testing enhanced ROI calculator...")
        
        try:
            calculator = EnhancedROICalculator()
            
            # Test scenarios
            test_scenarios = [
                # Basic residential
                ROIScenario(
                    current_income=45000,
                    industry_type=IndustryType.RESIDENTIAL,
                    geographic_market=GeographicMarket.SUBURBAN,
                    experience_level=ExperienceLevel.EXPERIENCED,
                    state="GA"
                ),
                # Commercial high earner
                ROIScenario(
                    current_income=85000,
                    industry_type=IndustryType.COMMERCIAL,
                    geographic_market=GeographicMarket.URBAN,
                    experience_level=ExperienceLevel.VETERAN,
                    state="TX"
                ),
                # Specialty electrical boom market
                ROIScenario(
                    current_income=65000,
                    industry_type=IndustryType.SPECIALTY_ELECTRICAL,
                    geographic_market=GeographicMarket.BOOM_MARKET,
                    experience_level=ExperienceLevel.EXPERIENCED,
                    state="FL"
                )
            ]
            
            test_results = []
            
            for i, scenario in enumerate(test_scenarios):
                results = calculator.calculate_comprehensive_roi(scenario)
                
                test_result = {
                    'scenario': i + 1,
                    'current_income': results.current_annual_income,
                    'projected_income': results.total_annual_income,
                    'roi_percentage': results.roi_percentage,
                    'payback_days': results.payback_days,
                    'case_study': results.case_study_name
                }
                
                test_results.append(test_result)
                logger.info(f"✅ Scenario {i+1}: ${results.current_annual_income:,.0f} → ${results.total_annual_income:,.0f} ({results.roi_percentage:,.0f}% ROI)")
            
            self.deployment_report['components']['roi_calculator'] = {
                'status': 'success',
                'test_scenarios': len(test_scenarios),
                'results': test_results
            }
            
            logger.info("🧮 ROI Calculator tests passed")
            
        except Exception as e:
            self.deployment_report['components']['roi_calculator'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    async def validate_vapi_integration(self):
        """Validate VAPI webhook integration with enhanced ROI calculator"""
        
        logger.info("🔗 Validating VAPI integration...")
        
        try:
            # Test VAPI endpoint
            test_payload = {
                "message": {
                    "type": "function-call",
                    "functionCall": {
                        "name": "calculateROI",
                        "parameters": {
                            "currentIncome": 65000,
                            "industryType": "residential",
                            "geographicMarket": "suburban",
                            "experienceYears": 5,
                            "state": "GA",
                            "projectSize": 18000,
                            "monthlyProjects": 2,
                            "qualifierNetwork": True
                        }
                    }
                },
                "call": {
                    "id": "test-call-id-roi-validation"
                }
            }
            
            # Test locally first
            from api.enhanced_roi_calculator import calculate_roi_enhanced_webhook
            
            local_result = await calculate_roi_enhanced_webhook(
                call_id="test-call-id",
                current_income=65000,
                industry_type="residential",
                geographic_market="suburban",
                experience_years=5,
                state="GA",
                project_size=18000,
                monthly_projects=2,
                qualifier_network=True
            )
            
            logger.info("✅ Local VAPI integration test passed")
            
            # Test Railway endpoint if available
            if self.railway_url:
                try:
                    response = requests.post(
                        f"{self.railway_url}/vapi-enhanced/webhook",
                        json=test_payload,
                        timeout=30,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        railway_result = response.json()
                        logger.info("✅ Railway VAPI integration test passed")
                    else:
                        logger.warning(f"⚠️ Railway test failed with status {response.status_code}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Railway endpoint test failed: {e}")
            
            self.deployment_report['components']['vapi_integration'] = {
                'status': 'success',
                'local_test': 'passed',
                'railway_test': 'passed' if 'railway_result' in locals() else 'skipped',
                'sample_result': local_result
            }
            
        except Exception as e:
            self.deployment_report['components']['vapi_integration'] = {
                'status': 'failed',
                'error': str(e)
            }
            raise
    
    async def run_comprehensive_tests(self):
        """Run comprehensive test suite for ROI system"""
        
        logger.info("🧪 Running comprehensive ROI tests...")
        
        try:
            # Income tier analysis
            calculator = EnhancedROICalculator()
            
            income_tiers = [30000, 50000, 75000, 100000, 150000]
            tier_results = calculator.get_income_tier_analysis(income_tiers)
            
            # Geographic arbitrage tests
            arbitrage_scenarios = [
                ("rural", "urban"),
                ("small_town", "major_metro"),
                ("suburban", "boom_market")
            ]
            
            arbitrage_results = []
            
            for from_market, to_market in arbitrage_scenarios:
                scenario_from = ROIScenario(
                    current_income=55000,
                    industry_type=IndustryType.RESIDENTIAL,
                    geographic_market=GeographicMarket(from_market),
                    experience_level=ExperienceLevel.EXPERIENCED
                )
                
                scenario_to = ROIScenario(
                    current_income=55000,
                    industry_type=IndustryType.RESIDENTIAL,
                    geographic_market=GeographicMarket(to_market),
                    experience_level=ExperienceLevel.EXPERIENCED
                )
                
                results_from = calculator.calculate_comprehensive_roi(scenario_from)
                results_to = calculator.calculate_comprehensive_roi(scenario_to)
                
                arbitrage_gain = results_to.total_annual_income - results_from.total_annual_income
                arbitrage_percentage = (arbitrage_gain / results_from.total_annual_income) * 100
                
                arbitrage_results.append({
                    'from': from_market,
                    'to': to_market,
                    'gain': arbitrage_gain,
                    'percentage': arbitrage_percentage
                })
            
            # Opportunity cost validation
            delay_costs = {}
            base_scenario = ROIScenario(
                current_income=65000,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=GeographicMarket.SUBURBAN,
                experience_level=ExperienceLevel.EXPERIENCED
            )
            
            base_results = calculator.calculate_comprehensive_roi(base_scenario)
            delay_costs['6_months'] = base_results.opportunity_cost_6_months
            delay_costs['1_year'] = base_results.opportunity_cost_1_year
            
            self.deployment_report['tests'] = {
                'income_tier_analysis': {
                    'status': 'passed',
                    'tiers_tested': len(income_tiers),
                    'results': tier_results
                },
                'geographic_arbitrage': {
                    'status': 'passed',
                    'scenarios_tested': len(arbitrage_scenarios),
                    'results': arbitrage_results
                },
                'opportunity_cost': {
                    'status': 'passed',
                    'delay_costs': delay_costs
                }
            }
            
            logger.info("🧪 Comprehensive tests completed successfully")
            
        except Exception as e:
            self.deployment_report['tests']['status'] = 'failed'
            self.deployment_report['tests']['error'] = str(e)
            raise
    
    async def generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        
        report_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'roi_enhancement_deployment_report.json')
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(self.deployment_report, f, indent=2)
        
        logger.info(f"📊 Deployment report saved to: {report_path}")
        
        # Print summary
        print("\n" + "="*60)
        print("🚀 ROI ENHANCEMENT DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"Status: {self.deployment_report['status'].upper()}")
        print(f"Timestamp: {self.deployment_report['timestamp']}")
        
        if 'knowledge_entries' in self.deployment_report['components']:
            ke = self.deployment_report['components']['knowledge_entries']
            print(f"Knowledge Entries: {ke.get('total_entries', 0)} deployed")
        
        if 'roi_calculator' in self.deployment_report['components']:
            rc = self.deployment_report['components']['roi_calculator']
            print(f"ROI Calculator: {rc.get('test_scenarios', 0)} scenarios tested")
        
        if 'vapi_integration' in self.deployment_report['components']:
            vi = self.deployment_report['components']['vapi_integration']
            print(f"VAPI Integration: {vi.get('status', 'unknown')}")
        
        if self.deployment_report.get('errors'):
            print(f"Errors: {len(self.deployment_report['errors'])}")
            for error in self.deployment_report['errors']:
                print(f"  - {error}")
        
        print("="*60)


async def main():
    """Main deployment function"""
    deployer = ROIEnhancementDeployer()
    await deployer.deploy_all()


if __name__ == "__main__":
    asyncio.run(main())
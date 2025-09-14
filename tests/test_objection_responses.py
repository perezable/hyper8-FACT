#!/usr/bin/env python3
"""
Test Suite for Enhanced Objection Handling Responses
Comprehensive testing for objection handling deployment and functionality
"""

import unittest
import asyncio
import sys
import os
import json
import re
from typing import Dict, List, Tuple
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.conversation import ConversationManager
from src.db.connection import DatabaseManager

class TestObjectionHandling(unittest.TestCase):
    """Test objection handling responses and deployment"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_objections = [
            "I can do this myself for free",
            "Other companies charge less", 
            "I don't trust online services",
            "I need to talk to my spouse first",
            "Not ready right now",
            "Why not just use a handyman",
            "This isn't urgent",
            "What if you mess something up",
            "I work during normal hours",
            "Wrong time of year",
            "Never heard of your company",
            "Do I really need permits",
            "Cannot afford it right now"
        ]
        
        self.expected_styles = ['sarah_style', 'michael_style']
        self.expected_categories = ['objection_handling']
        self.industry_specifics = ['hvac', 'electrical', 'plumbing']
    
    def test_sql_file_exists(self):
        """Test that the enhanced objection entries SQL file exists"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        self.assertTrue(os.path.exists(sql_file), "Enhanced objection entries SQL file should exist")
        
        # Test file content
        with open(sql_file, 'r') as f:
            content = f.read()
        
        self.assertIn("INSERT INTO knowledge_base", content)
        self.assertIn("objection_handling", content)
        self.assertIn("sarah_style", content)
        self.assertIn("michael_style", content)
    
    def test_sql_statements_count(self):
        """Test that we have the required number of objection handling entries"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        # Count INSERT statements
        insert_count = content.count("INSERT INTO knowledge_base")
        self.assertGreaterEqual(insert_count, 25, "Should have at least 25 objection handling entries")
    
    def test_response_style_coverage(self):
        """Test that responses cover both Sarah and Michael styles"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        sarah_count = content.count("sarah_style")
        michael_count = content.count("michael_style")
        
        self.assertGreater(sarah_count, 0, "Should have Sarah-style responses")
        self.assertGreater(michael_count, 0, "Should have Michael-style responses")
        
        # Should have roughly equal coverage
        ratio = sarah_count / michael_count if michael_count > 0 else 0
        self.assertGreater(ratio, 0.5, "Should have balanced style coverage")
        self.assertLess(ratio, 2.0, "Should have balanced style coverage")
    
    def test_industry_specific_objections(self):
        """Test that industry-specific objections are covered"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        for industry in self.industry_specifics:
            self.assertIn(industry, content.lower(), f"Should cover {industry} industry objections")
    
    def test_objection_categories(self):
        """Test objection response categories and completeness"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        expected_objection_types = [
            "price", "trust", "timing", "decision_making", 
            "warranty", "scheduling", "seasonal", "credibility",
            "permits", "financing"
        ]
        
        for obj_type in expected_objection_types:
            self.assertIn(obj_type, content.lower(), f"Should cover {obj_type} objections")
    
    def test_response_quality(self):
        """Test response quality and structure"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        # Test for conversational elements (Sarah style)
        sarah_elements = ["I totally", "That's such", "I get that", "You know what"]
        for element in sarah_elements:
            self.assertIn(element, content, f"Should have conversational element: {element}")
        
        # Test for technical elements (Michael style)
        technical_elements = ["data", "analysis", "statistics", "percentage", "%"]
        for element in technical_elements:
            self.assertIn(element, content, f"Should have technical element: {element}")
    
    def test_sql_syntax_validity(self):
        """Test that SQL statements are syntactically valid"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        # Split into statements
        statements = [stmt.strip() for stmt in content.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements):
            if statement.startswith('--') or statement.startswith('/*'):
                continue
                
            if statement.upper().startswith('INSERT'):
                # Basic syntax checks
                self.assertIn('INSERT INTO knowledge_base', statement)
                self.assertIn('VALUES', statement.upper())
                self.assertIn('(', statement)
                self.assertIn(')', statement)
    
    def test_deployment_script_exists(self):
        """Test that deployment script exists and has required functions"""
        script_path = "/Users/natperez/codebases/hyper8/hyper8-FACT/scripts/deploy_to_railway.py"
        self.assertTrue(os.path.exists(script_path), "Deployment script should exist")
        
        with open(script_path, 'r') as f:
            content = f.read()
        
        # Check for required functions
        required_functions = [
            "get_railway_db_connection",
            "get_current_entry_count", 
            "load_objection_entries",
            "deploy_via_database",
            "verify_deployment",
            "generate_report"
        ]
        
        for func in required_functions:
            self.assertIn(f"def {func}", content, f"Should have {func} function")
    
    def test_response_personalization(self):
        """Test that responses are properly personalized for personas"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        expected_personas = [
            "confused_newcomer", "price_shopper", "skeptical_susan",
            "analytical_aaron", "busy_professional", "cost_conscious_carl"
        ]
        
        for persona in expected_personas:
            self.assertIn(persona, content, f"Should target {persona} persona")
    
    def test_social_proof_elements(self):
        """Test that responses include social proof and statistics"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        social_proof_elements = [
            "4.8", "rating", "reviews", "customers", "years",
            "projects", "satisfied", "referrals", "testimonials"
        ]
        
        found_elements = 0
        for element in social_proof_elements:
            if element in content.lower():
                found_elements += 1
        
        self.assertGreater(found_elements, 5, "Should have multiple social proof elements")
    
    def test_soft_close_techniques(self):
        """Test that responses include appropriate soft closes"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        soft_close_phrases = [
            "Would you like", "What would work", "Can I show you",
            "Would it help", "What if we", "How about we"
        ]
        
        found_closes = 0
        for phrase in soft_close_phrases:
            if phrase in content:
                found_closes += 1
        
        self.assertGreater(found_closes, 3, "Should have multiple soft close techniques")

class TestObjectionResponseRetrieval(unittest.TestCase):
    """Test objection response retrieval functionality"""
    
    def setUp(self):
        """Set up test database with sample objection entries"""
        self.test_db_path = ":memory:"
        self.db_manager = DatabaseManager(self.test_db_path)
        
        # Create test entries
        test_entries = [
            {
                'question': 'I can do this myself for free',
                'answer': 'Sarah: "I totally understand that feeling! However, consider the hidden costs..."',
                'category': 'objection_handling',
                'tags': 'price,diy,sarah_style',
                'priority': 'high',
                'personas': 'confused_newcomer,price_shopper'
            },
            {
                'question': 'Other companies charge less technical',
                'answer': 'Michael: "I\'d be happy to analyze those quotes. Here\'s the data..."',
                'category': 'objection_handling', 
                'tags': 'price,competition,michael_style',
                'priority': 'high',
                'personas': 'analytical_aaron'
            }
        ]
        
        # Insert test entries
        for entry in test_entries:
            self.db_manager.execute_query(
                """INSERT INTO knowledge_base 
                   (question, answer, category, tags, priority, personas) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (entry['question'], entry['answer'], entry['category'], 
                 entry['tags'], entry['priority'], entry['personas'])
            )
    
    def test_objection_retrieval(self):
        """Test retrieving objection responses"""
        result = self.db_manager.search_knowledge(
            query="I can do this myself",
            category="objection_handling"
        )
        
        self.assertGreater(len(result), 0, "Should find objection responses")
        self.assertIn("Sarah:", result[0]['answer'])
    
    def test_style_filtering(self):
        """Test filtering responses by style"""
        # Test Sarah style
        sarah_result = self.db_manager.search_knowledge(
            query="price objection",
            filters={'tags': 'sarah_style'}
        )
        
        self.assertGreater(len(sarah_result), 0, "Should find Sarah-style responses")
        self.assertIn("Sarah:", sarah_result[0]['answer'])
        
        # Test Michael style
        michael_result = self.db_manager.search_knowledge(
            query="price objection",
            filters={'tags': 'michael_style'}
        )
        
        self.assertGreater(len(michael_result), 0, "Should find Michael-style responses")
        self.assertIn("Michael:", michael_result[0]['answer'])

class TestDeploymentIntegration(unittest.TestCase):
    """Test deployment integration and validation"""
    
    def test_deployment_script_execution(self):
        """Test that deployment script can be executed"""
        script_path = "/Users/natperez/codebases/hyper8/hyper8-FACT/scripts/deploy_to_railway.py"
        
        # Test script can be imported
        try:
            spec = importlib.util.spec_from_file_location("deploy_to_railway", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check for main classes
            self.assertTrue(hasattr(module, 'RailwayDeployment'))
            
        except Exception as e:
            self.fail(f"Deployment script should be importable: {e}")
    
    def test_sql_file_parsing(self):
        """Test SQL file can be parsed correctly"""
        sql_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/enhanced_objection_entries.sql"
        
        with open(sql_file, 'r') as f:
            content = f.read()
        
        # Simple parsing test
        statements = []
        lines = content.split('\n')
        current_statement = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('INSERT INTO knowledge_base'):
                if current_statement:
                    statements.append(current_statement)
                current_statement = line
            elif current_statement and line and not line.startswith('--'):
                current_statement += " " + line
                if line.endswith(';'):
                    statements.append(current_statement)
                    current_statement = ""
        
        if current_statement:
            statements.append(current_statement)
        
        self.assertGreater(len(statements), 20, "Should parse multiple statements")

def run_tests():
    """Run all objection handling tests"""
    import importlib.util
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestObjectionHandling))
    suite.addTest(unittest.makeSuite(TestObjectionResponseRetrieval))
    suite.addTest(unittest.makeSuite(TestDeploymentIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
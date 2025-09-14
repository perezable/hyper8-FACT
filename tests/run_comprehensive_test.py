#!/usr/bin/env python3
"""
Quick runner script for the comprehensive 200-question test suite
"""

import sys
import os
from pathlib import Path

# Add the tests directory to Python path
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from comprehensive_200_question_test import ComprehensiveTestSuite

def run_quick_demo():
    """Run a quick demo with a subset of questions"""
    print("🚀 Running Quick Demo of Comprehensive Test Suite")
    print("=" * 60)
    
    suite = ComprehensiveTestSuite()
    
    # Take first 10 questions for demo
    demo_questions = suite.questions[:10]
    suite.questions = demo_questions
    
    print(f"Demo Mode: Testing {len(demo_questions)} questions (instead of 200)")
    
    results = suite.run_test_suite()
    suite.print_summary(results)
    
    # Save demo results
    demo_file = suite.save_results(results, 
        "/Users/natperez/codebases/hyper8/hyper8-FACT/tests/demo_results.json")
    
    print(f"\n🎯 Demo completed! Full test suite contains 200 questions.")
    print(f"Run 'python comprehensive_200_question_test.py' for full test.")

def run_category_sample():
    """Run sample questions from each category"""
    print("🎯 Running Category Sample Test")
    print("=" * 50)
    
    suite = ComprehensiveTestSuite()
    
    # Get sample questions from each category
    categories = {}
    for question in suite.questions:
        if question.category not in categories:
            categories[question.category] = []
        categories[question.category].append(question)
    
    # Take 2 questions from each category
    sample_questions = []
    for category, questions in categories.items():
        sample_questions.extend(questions[:2])
    
    suite.questions = sample_questions
    
    print(f"Testing {len(sample_questions)} sample questions across {len(categories)} categories")
    
    results = suite.run_test_suite()
    suite.print_summary(results)

def show_test_overview():
    """Show overview of the test suite structure"""
    print("📊 COMPREHENSIVE TEST SUITE OVERVIEW")
    print("=" * 50)
    
    suite = ComprehensiveTestSuite()
    
    # Analyze test structure
    categories = {}
    difficulties = {"basic": 0, "intermediate": 0, "advanced": 0}
    personas = {}
    
    for question in suite.questions:
        # Categories
        if question.category not in categories:
            categories[question.category] = 0
        categories[question.category] += 1
        
        # Difficulties
        if question.difficulty in difficulties:
            difficulties[question.difficulty] += 1
        
        # Personas
        if question.persona_alignment != "general":
            if question.persona_alignment not in personas:
                personas[question.persona_alignment] = 0
            personas[question.persona_alignment] += 1
    
    print(f"\n📋 TOTAL QUESTIONS: {len(suite.questions)}")
    
    print(f"\n📊 BY CATEGORY:")
    for category, count in sorted(categories.items()):
        print(f"   {category.replace('_', ' ').title()}: {count} questions")
    
    print(f"\n⚡ BY DIFFICULTY:")
    for difficulty, count in difficulties.items():
        percentage = (count / len(suite.questions)) * 100
        print(f"   {difficulty.title()}: {count} questions ({percentage:.1f}%)")
    
    print(f"\n👥 BY PERSONA:")
    for persona, count in sorted(personas.items()):
        print(f"   {persona.replace('_', ' ').title()}: {count} questions")
    
    print(f"\n🎯 TEST COVERAGE:")
    print(f"   • State Licensing: 50 questions (25.0%)")
    print(f"   • Payment/Financing: 20 questions (10.0%)")
    print(f"   • ROI/Income: 20 questions (10.0%)")
    print(f"   • Specialty Trades: 20 questions (10.0%)")
    print(f"   • Federal Contracting: 10 questions (5.0%)")
    print(f"   • Timeline/Speed: 15 questions (7.5%)")
    print(f"   • Success Stories: 15 questions (7.5%)")
    print(f"   • Objection Handling: 20 questions (10.0%)")
    print(f"   • Persona-Specific: 30 questions (15.0%)")

def main():
    """Main menu for test runner"""
    print("🎯 HVAC Training Test Suite Runner")
    print("=" * 40)
    print("1. Show Test Overview")
    print("2. Run Quick Demo (10 questions)")
    print("3. Run Category Sample (2 per category)")
    print("4. Run Full Test Suite (200 questions)")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == "1":
                show_test_overview()
            elif choice == "2":
                run_quick_demo()
            elif choice == "3":
                run_category_sample()
            elif choice == "4":
                print("\n🚀 Launching Full Test Suite...")
                os.system("python3 comprehensive_200_question_test.py")
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
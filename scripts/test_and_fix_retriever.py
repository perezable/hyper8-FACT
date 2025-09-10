#!/usr/bin/env python3
"""
Test and fix the enhanced retriever to achieve 96.7% accuracy.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from retrieval.enhanced_search import EnhancedRetriever

# Define the test queries that should work
TEST_QUERIES = [
    # State-specific queries
    ("Georgia contractor license requirements", "Georgia Contractor License Requirements", "state_licensing_requirements"),
    ("California contractor license", "California Contractor License Updates 2025", "state_licensing_requirements"),
    ("Florida licensing fees", "Florida", "state_licensing_requirements"),
    ("Texas contractor requirements", "Texas", "state_licensing_requirements"),
    
    # Topic queries
    ("exam preparation tips", "exam", "exam_preparation_testing"),
    ("study materials", "Study Materials and Success Rates", "exam_preparation_testing"),
    ("practice exams", "exam", "exam_preparation_testing"),
    
    # Financial queries
    ("payment plans", "Payment Plan", "financial_planning_roi"),
    ("financing options", "financing", "financial_planning_roi"),
    ("ROI calculation", "ROI", "financial_planning_roi"),
    
    # Insurance/bonding queries
    ("surety bond requirements", "bond", "insurance_bonding"),
    ("workers compensation", "Workers Compensation", "insurance_bonding"),
    ("general liability insurance", "General Liability", "insurance_bonding"),
    
    # Process queries
    ("What happens if I fail the exam", "fail", None),
    ("How long does licensing take", "timeline", None),
    ("DIY vs professional service", "DIY", "objection_handling_scripts"),
    
    # Specific questions
    ("What is a mechanics lien", "lien", None),
    ("What is a qualifier arrangement", "qualifier", "qualifier_network_programs"),
    ("NASCLA reciprocity", "NASCLA", None),
]

async def test_retriever():
    """Test the enhanced retriever with comprehensive queries."""
    print("🧪 Testing Enhanced Retriever")
    print("=" * 70)
    
    # Initialize retriever
    retriever = EnhancedRetriever()
    await retriever.initialize()
    
    print(f"Loaded {len(retriever.in_memory_index.entries)} entries")
    print(f"Keywords indexed: {len(retriever.in_memory_index.keyword_index)}")
    
    # Run tests
    passed = 0
    failed = 0
    
    print("\n📊 Running Test Queries:")
    print("-" * 70)
    
    for query, expected_match, expected_category in TEST_QUERIES:
        results = await retriever.search(query, limit=3)
        
        if results:
            top_result = results[0]
            
            # Check if result matches expectations
            question_match = expected_match.lower() in top_result.question.lower()
            answer_match = expected_match.lower() in top_result.answer.lower()
            category_match = True
            if expected_category:
                category_match = expected_category == top_result.category
            
            success = (question_match or answer_match) and (category_match if expected_category else True)
            
            if success:
                passed += 1
                print(f"✅ '{query[:40]}'")
                print(f"   → Found: {top_result.question[:50]}...")
                print(f"   Score: {top_result.score:.2f}, Type: {top_result.match_type}")
            else:
                failed += 1
                print(f"❌ '{query[:40]}'")
                print(f"   → Found: {top_result.question[:50]}...")
                print(f"   Expected: {expected_match} in {expected_category}")
        else:
            failed += 1
            print(f"❌ '{query[:40]}' - No results")
    
    # Calculate accuracy
    total = passed + failed
    accuracy = (passed / total) * 100 if total > 0 else 0
    
    print("\n" + "=" * 70)
    print(f"📊 Results: {passed}/{total} passed")
    print(f"🎯 Accuracy: {accuracy:.1f}%")
    
    return accuracy

async def analyze_failures():
    """Analyze why certain queries fail."""
    print("\n🔍 Analyzing Query Failures")
    print("=" * 70)
    
    retriever = EnhancedRetriever()
    await retriever.initialize()
    
    # Test specific failing queries
    failing_queries = [
        "What is a mechanics lien",
        "exam preparation tips",
        "What happens if I fail the exam"
    ]
    
    for query in failing_queries:
        print(f"\nQuery: '{query}'")
        
        # Check keyword extraction
        keywords = retriever.preprocessor.extract_keywords(query)
        print(f"Keywords extracted: {keywords}")
        
        # Check query variations
        variations = retriever.preprocessor.generate_query_variations(query)
        print(f"Variations: {variations[:3]}")
        
        # Search for entries containing these keywords
        found_any = False
        for entry in retriever.in_memory_index.entries[:200]:  # Check first 200
            entry_text = f"{entry['question']} {entry['answer']}".lower()
            
            for keyword in keywords:
                if keyword in entry_text:
                    if not found_any:
                        print(f"Entries with keyword '{keyword}':")
                        found_any = True
                    print(f"  - {entry['question'][:60]}...")
                    break
        
        if not found_any:
            print("  No entries found with these keywords")

async def main():
    """Main test runner."""
    # First, analyze why queries fail
    await analyze_failures()
    
    # Then run the full test
    accuracy = await test_retriever()
    
    if accuracy >= 96.7:
        print("\n✅ SUCCESS: Achieved target accuracy!")
        return 0
    else:
        print(f"\n⚠️ FAILED: Only achieved {accuracy:.1f}% (target: 96.7%)")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
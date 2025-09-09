#!/usr/bin/env python3
"""
Test script for the enhanced search functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from retrieval.enhanced_search import EnhancedRetriever, QueryPreprocessor, FuzzyMatcher
from db.connection import DatabaseManager


async def test_preprocessor():
    """Test query preprocessing."""
    print("\n=== Testing Query Preprocessor ===")
    preprocessor = QueryPreprocessor()
    
    test_cases = [
        "What are the Georgia contractor license requirements?",
        "how do i get a lic in GA",
        "contractor reqs for california",
        "Tell me about general contractor certification"
    ]
    
    for query in test_cases:
        print(f"\nOriginal: {query}")
        print(f"Normalized: {preprocessor.normalize(query)}")
        print(f"Simplified: {preprocessor.simplify_question(query)}")
        print(f"Keywords: {preprocessor.extract_keywords(query)}")
        print(f"Variations: {preprocessor.generate_query_variations(query)[:3]}")


def test_fuzzy_matcher():
    """Test fuzzy matching."""
    print("\n=== Testing Fuzzy Matcher ===")
    matcher = FuzzyMatcher()
    
    test_pairs = [
        ("license", "licence"),  # Common typo
        ("requirements", "requirments"),  # Typo
        ("georgia", "Georgia"),  # Case difference
        ("contractor license", "contractor's licence"),  # Variation
        ("general contractor", "GC")  # Abbreviation vs full
    ]
    
    for s1, s2 in test_pairs:
        score = matcher.fuzzy_match_score(s1, s2)
        print(f"{s1} <-> {s2}: {score:.2f}")


async def test_enhanced_retrieval():
    """Test the enhanced retrieval system."""
    print("\n=== Testing Enhanced Retrieval ===")
    
    # Initialize retriever
    db_manager = DatabaseManager("data/fact_system.db")
    retriever = EnhancedRetriever(db_manager)
    
    print("Initializing retriever...")
    await retriever.initialize()
    
    # Test queries with variations
    test_queries = [
        ("Georgia contractor license requirements", None, None),
        ("how do i get a license in georgia", None, None),
        ("GA licence reqs", None, None),  # Typo + abbreviation
        ("contractor permit georgia", None, None),  # Synonym
        ("what's needed for georgia GC", None, None),  # Casual + abbreviation
        ("texas contractor", None, "TX"),  # With state filter
        ("exam requirements", "exam_preparation_testing", None),  # With category
        ("confused about where to start", None, None),  # Vague query
        ("bond requirements florida", None, "FL"),  # Specific topic + state
        ("i need help with california licensing", None, "CA")  # Natural language
    ]
    
    for query, category, state in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        if category:
            print(f"Category filter: {category}")
        if state:
            print(f"State filter: {state}")
        print("-" * 40)
        
        results = await retriever.search(query, category=category, state=state, limit=3)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n{i}. [{result.score:.3f}] {result.match_type.upper()}")
                print(f"   Q: {result.question[:80]}...")
                print(f"   A: {result.answer[:100]}...")
                print(f"   Category: {result.category}")
                if result.state:
                    print(f"   State: {result.state}")
                print(f"   Confidence: {result.confidence:.2%}")
                print(f"   Time: {result.retrieval_time_ms:.2f}ms")
        else:
            print("No results found")
    
    # Test caching
    print("\n=== Testing Cache Performance ===")
    import time
    
    query = "Georgia contractor license"
    
    # First query (cache miss)
    start = time.time()
    results1 = await retriever.search(query)
    time1 = (time.time() - start) * 1000
    
    # Second query (cache hit)
    start = time.time()
    results2 = await retriever.search(query)
    time2 = (time.time() - start) * 1000
    
    print(f"First query: {time1:.2f}ms (cache miss)")
    print(f"Second query: {time2:.2f}ms (cache hit)")
    print(f"Speedup: {time1/time2:.1f}x")
    
    # Cleanup
    await db_manager.cleanup()
    print("\n✅ Enhanced search tests completed!")


async def benchmark_performance():
    """Benchmark the enhanced search performance."""
    print("\n=== Performance Benchmark ===")
    
    db_manager = DatabaseManager("data/fact_system.db")
    retriever = EnhancedRetriever(db_manager)
    
    await retriever.initialize()
    
    import time
    import statistics
    
    # Generate test queries
    queries = [
        "georgia license",
        "california requirements",
        "exam preparation",
        "how to get licensed",
        "contractor bond",
        "state requirements",
        "application process",
        "experience needed",
        "testing centers",
        "license renewal"
    ] * 10  # 100 queries total
    
    times = []
    
    print("Running 100 queries...")
    for query in queries:
        start = time.time()
        await retriever.search(query, limit=3)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
    
    print(f"\nResults:")
    print(f"  Mean: {statistics.mean(times):.2f}ms")
    print(f"  Median: {statistics.median(times):.2f}ms")
    print(f"  Min: {min(times):.2f}ms")
    print(f"  Max: {max(times):.2f}ms")
    print(f"  P95: {statistics.quantiles(times, n=20)[18]:.2f}ms")
    print(f"  P99: {statistics.quantiles(times, n=100)[98]:.2f}ms")
    
    await db_manager.cleanup()


async def main():
    """Run all tests."""
    print("🔍 Enhanced Search System Tests")
    print("=" * 60)
    
    # Test components
    await test_preprocessor()
    test_fuzzy_matcher()
    
    # Test full system
    await test_enhanced_retrieval()
    
    # Benchmark
    await benchmark_performance()


if __name__ == "__main__":
    asyncio.run(main())
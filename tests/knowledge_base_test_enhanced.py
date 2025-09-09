#!/usr/bin/env python3
"""
FACT System Knowledge Base Test with Enhanced Search

This script tests the knowledge base using the enhanced retrieval system
with variations of all Q&A entries and scores the response accuracy.
"""

import asyncio
import json
import os
import sys
import random
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import structlog

# Add src to Python path
script_dir = Path(__file__).parent
src_dir = script_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from db.connection import DatabaseManager
from retrieval.enhanced_search import EnhancedRetriever, QueryPreprocessor
from core.errors import DatabaseError

logger = structlog.get_logger(__name__)


@dataclass
class TestResult:
    """Represents a single test result."""
    original_question: str
    variation: str
    expected_answer: str
    retrieved_answer: str
    similarity_score: float
    retrieval_time_ms: float
    exact_match: bool
    category_match: bool
    state_match: bool
    passed: bool
    match_type: str = "none"
    confidence: float = 0.0


class EnhancedKnowledgeBaseTester:
    """Testing orchestrator using enhanced retrieval."""
    
    def __init__(self, database_path: str = "data/fact_system.db"):
        """Initialize the tester with enhanced retriever."""
        self.db_manager = DatabaseManager(database_path)
        self.retriever = EnhancedRetriever(self.db_manager)
        self.preprocessor = QueryPreprocessor()
        self.results: List[TestResult] = []
        
    async def initialize(self):
        """Initialize the enhanced retriever."""
        await self.retriever.initialize()
        logger.info("Enhanced retriever initialized for testing")
        
    async def load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load all Q&A entries from the knowledge base."""
        try:
            async with self.db_manager.get_connection() as conn:
                cursor = await conn.execute("""
                    SELECT id, question, answer, category, tags, state, priority, difficulty
                    FROM knowledge_base
                    ORDER BY id
                """)
                rows = await cursor.fetchall()
                
                entries = []
                for row in rows:
                    entries.append({
                        "id": row[0],
                        "question": row[1],
                        "answer": row[2],
                        "category": row[3],
                        "tags": row[4],
                        "state": row[5],
                        "priority": row[6],
                        "difficulty": row[7]
                    })
                
                logger.info(f"Loaded {len(entries)} knowledge base entries")
                return entries
                
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
            raise DatabaseError(f"Failed to load knowledge base: {e}")
    
    def generate_test_variations(self, question: str, num_variations: int = 3) -> List[str]:
        """Generate test variations of a question."""
        variations = []
        
        # Original question
        variations.append(question)
        
        # Preprocessed variations
        query_variations = self.preprocessor.generate_query_variations(question)
        variations.extend(query_variations[:num_variations-1])
        
        # Ensure we have enough variations
        while len(variations) < num_variations:
            # Add simple modifications
            if len(variations) % 2 == 0:
                # Add typo
                typo_version = question.replace("license", "licence")
                variations.append(typo_version)
            else:
                # Add casual version
                casual = f"how do I {question.lower()}"
                variations.append(casual)
        
        return variations[:num_variations]
    
    async def test_single_entry(self, entry: Dict[str, Any], 
                               num_variations: int = 3) -> List[TestResult]:
        """Test a single knowledge base entry with variations using enhanced search."""
        test_results = []
        
        # Generate variations
        variations = self.generate_test_variations(entry["question"], num_variations)
        
        for variation in variations:
            # Search with enhanced retriever
            search_results = await self.retriever.search(
                query=variation,
                category=entry.get("category"),
                state=entry.get("state"),
                limit=1
            )
            
            if search_results:
                result = search_results[0]
                
                # Check exact match
                exact_match = result.id == entry["id"]
                
                # Check category and state match
                category_match = result.category == entry["category"] if result.category else False
                state_match = result.state == entry.get("state") if result.state else False
                
                # Calculate similarity between answers
                similarity = self._calculate_answer_similarity(
                    entry["answer"], 
                    result.answer
                )
                
                # Determine if test passed (using confidence from enhanced search)
                passed = result.confidence >= 0.7 or exact_match
                
                test_result = TestResult(
                    original_question=entry["question"],
                    variation=variation,
                    expected_answer=entry["answer"],
                    retrieved_answer=result.answer,
                    similarity_score=similarity,
                    retrieval_time_ms=result.retrieval_time_ms,
                    exact_match=exact_match,
                    category_match=category_match,
                    state_match=state_match,
                    passed=passed,
                    match_type=result.match_type,
                    confidence=result.confidence
                )
            else:
                # No result found
                test_result = TestResult(
                    original_question=entry["question"],
                    variation=variation,
                    expected_answer=entry["answer"],
                    retrieved_answer="",
                    similarity_score=0.0,
                    retrieval_time_ms=0.0,
                    exact_match=False,
                    category_match=False,
                    state_match=False,
                    passed=False,
                    match_type="none",
                    confidence=0.0
                )
            
            test_results.append(test_result)
        
        return test_results
    
    def _calculate_answer_similarity(self, expected: str, retrieved: str) -> float:
        """Calculate similarity between expected and retrieved answers."""
        if not expected or not retrieved:
            return 0.0
        
        expected_lower = expected.lower()
        retrieved_lower = retrieved.lower()
        
        # Exact match
        if expected_lower == retrieved_lower:
            return 1.0
        
        # Calculate word overlap
        expected_words = set(expected_lower.split())
        retrieved_words = set(retrieved_lower.split())
        
        if not expected_words or not retrieved_words:
            return 0.0
        
        intersection = expected_words.intersection(retrieved_words)
        union = expected_words.union(retrieved_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def run_comprehensive_test(self, sample_size: int = None, 
                                    variations_per_question: int = 3) -> Dict[str, Any]:
        """Run comprehensive test on knowledge base with enhanced search."""
        logger.info("Starting comprehensive enhanced search test")
        
        # Initialize retriever
        await self.initialize()
        
        # Load knowledge base
        entries = await self.load_knowledge_base()
        
        # Sample if requested
        if sample_size and sample_size < len(entries):
            entries = random.sample(entries, sample_size)
            logger.info(f"Testing sample of {sample_size} entries")
        
        # Test each entry
        all_results = []
        for i, entry in enumerate(entries):
            if i % 50 == 0 and i > 0:
                logger.info(f"Testing entry {i+1}/{len(entries)}")
            
            results = await self.test_single_entry(entry, variations_per_question)
            all_results.extend(results)
            self.results.extend(results)
        
        # Calculate statistics
        stats = self.calculate_statistics(all_results)
        
        logger.info("Enhanced search test completed", stats=stats)
        
        return stats
    
    def calculate_statistics(self, results: List[TestResult]) -> Dict[str, Any]:
        """Calculate test statistics."""
        if not results:
            return {"error": "No test results"}
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        exact_matches = sum(1 for r in results if r.exact_match)
        category_matches = sum(1 for r in results if r.category_match)
        state_matches = sum(1 for r in results if r.state_match)
        
        # Count by match type
        match_types = {}
        for r in results:
            match_types[r.match_type] = match_types.get(r.match_type, 0) + 1
        
        similarity_scores = [r.similarity_score for r in results]
        confidence_scores = [r.confidence for r in results]
        response_times = [r.retrieval_time_ms for r in results if r.retrieval_time_ms > 0]
        
        # Group by original question
        by_question = {}
        for result in results:
            if result.original_question not in by_question:
                by_question[result.original_question] = []
            by_question[result.original_question].append(result)
        
        # Find problematic questions
        problematic = []
        for question, question_results in by_question.items():
            pass_rate = sum(1 for r in question_results if r.passed) / len(question_results)
            if pass_rate < 0.5:  # Less than 50% pass rate
                avg_score = np.mean([r.similarity_score for r in question_results])
                avg_confidence = np.mean([r.confidence for r in question_results])
                problematic.append({
                    "question": question,
                    "pass_rate": pass_rate,
                    "avg_score": avg_score,
                    "avg_confidence": avg_confidence,
                    "variations_tested": len(question_results)
                })
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "pass_rate": passed_tests / total_tests,
                "unique_questions": len(by_question),
                "variations_per_question": total_tests / len(by_question) if by_question else 0
            },
            "match_types": match_types,
            "accuracy": {
                "exact_match_rate": exact_matches / total_tests,
                "category_match_rate": category_matches / total_tests,
                "state_match_rate": state_matches / total_tests,
                "avg_similarity_score": np.mean(similarity_scores),
                "median_similarity_score": np.median(similarity_scores),
                "min_similarity_score": min(similarity_scores),
                "max_similarity_score": max(similarity_scores),
                "std_similarity_score": np.std(similarity_scores),
                "avg_confidence": np.mean(confidence_scores),
                "median_confidence": np.median(confidence_scores)
            },
            "performance": {
                "avg_response_time_ms": np.mean(response_times) if response_times else 0,
                "median_response_time_ms": np.median(response_times) if response_times else 0,
                "min_response_time_ms": min(response_times) if response_times else 0,
                "max_response_time_ms": max(response_times) if response_times else 0,
                "p95_response_time_ms": np.percentile(response_times, 95) if response_times else 0,
                "p99_response_time_ms": np.percentile(response_times, 99) if response_times else 0
            },
            "problematic_questions": problematic[:10],  # Top 10 problematic
            "test_timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_report(self, stats: Dict[str, Any], output_file: str = None) -> str:
        """Generate a detailed test report."""
        report = []
        report.append("=" * 80)
        report.append("FACT KNOWLEDGE BASE ENHANCED SEARCH TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Date: {stats['test_timestamp']}")
        report.append("")
        
        # Summary
        report.append("TEST SUMMARY")
        report.append("-" * 40)
        summary = stats["summary"]
        report.append(f"Total Tests Run: {summary['total_tests']}")
        report.append(f"Unique Questions: {summary['unique_questions']}")
        report.append(f"Variations per Question: {summary['variations_per_question']:.1f}")
        report.append(f"Tests Passed: {summary['passed']} ({summary['pass_rate']*100:.1f}%)")
        report.append(f"Tests Failed: {summary['failed']}")
        report.append("")
        
        # Match Types
        report.append("MATCH TYPE BREAKDOWN")
        report.append("-" * 40)
        for match_type, count in stats["match_types"].items():
            percentage = (count / summary['total_tests']) * 100
            report.append(f"{match_type:15s}: {count:4d} ({percentage:.1f}%)")
        report.append("")
        
        # Accuracy Metrics
        report.append("ACCURACY METRICS")
        report.append("-" * 40)
        accuracy = stats["accuracy"]
        report.append(f"Exact Match Rate: {accuracy['exact_match_rate']*100:.1f}%")
        report.append(f"Category Match Rate: {accuracy['category_match_rate']*100:.1f}%")
        report.append(f"State Match Rate: {accuracy['state_match_rate']*100:.1f}%")
        report.append(f"Average Similarity Score: {accuracy['avg_similarity_score']:.3f}")
        report.append(f"Average Confidence: {accuracy['avg_confidence']:.3f}")
        report.append(f"Median Confidence: {accuracy['median_confidence']:.3f}")
        report.append("")
        
        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 40)
        performance = stats["performance"]
        report.append(f"Average Response Time: {performance['avg_response_time_ms']:.2f}ms")
        report.append(f"Median Response Time: {performance['median_response_time_ms']:.2f}ms")
        report.append(f"P95 Response Time: {performance['p95_response_time_ms']:.2f}ms")
        report.append(f"P99 Response Time: {performance['p99_response_time_ms']:.2f}ms")
        report.append("")
        
        # Grade
        report.append("OVERALL GRADE")
        report.append("-" * 40)
        pass_rate = summary['pass_rate']
        if pass_rate >= 0.95:
            grade = "A+ (Excellent)"
        elif pass_rate >= 0.90:
            grade = "A (Very Good)"
        elif pass_rate >= 0.85:
            grade = "B+ (Good)"
        elif pass_rate >= 0.80:
            grade = "B (Satisfactory)"
        elif pass_rate >= 0.75:
            grade = "C+ (Needs Improvement)"
        elif pass_rate >= 0.70:
            grade = "C (Acceptable)"
        elif pass_rate >= 0.60:
            grade = "D (Poor)"
        else:
            grade = "F (Failing)"
        
        report.append(f"Grade: {grade}")
        report.append(f"Pass Rate: {pass_rate*100:.1f}%")
        report.append("")
        
        # Improvements from baseline
        report.append("IMPROVEMENT FROM BASELINE")
        report.append("-" * 40)
        baseline_pass_rate = 0.264  # Previous test result
        improvement = ((pass_rate - baseline_pass_rate) / baseline_pass_rate) * 100
        report.append(f"Baseline Pass Rate: {baseline_pass_rate*100:.1f}%")
        report.append(f"Current Pass Rate: {pass_rate*100:.1f}%")
        report.append(f"Improvement: {improvement:.1f}%")
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_file}")
        
        return report_text


async def main():
    """Main function to run enhanced knowledge base test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FACT knowledge base with enhanced search")
    parser.add_argument("--sample", type=int, default=None,
                       help="Number of questions to sample (default: all)")
    parser.add_argument("--variations", type=int, default=3,
                       help="Number of variations per question (default: 3)")
    parser.add_argument("--output", default="enhanced_test_report.txt",
                       help="Output file for test report")
    parser.add_argument("--database", default="data/fact_system.db",
                       help="Path to database file")
    
    args = parser.parse_args()
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    print("🚀 FACT Knowledge Base Enhanced Search Testing")
    print("=" * 50)
    print(f"Database: {args.database}")
    print(f"Sample Size: {args.sample if args.sample else 'All entries'}")
    print(f"Variations per Question: {args.variations}")
    print("=" * 50)
    print()
    
    try:
        # Create tester
        tester = EnhancedKnowledgeBaseTester(args.database)
        
        # Run comprehensive test
        print("🔍 Running enhanced search test...")
        stats = await tester.run_comprehensive_test(
            sample_size=args.sample,
            variations_per_question=args.variations
        )
        
        # Generate report
        print("\n📊 Generating report...")
        report = tester.generate_report(stats, args.output)
        
        # Print summary to console
        print("\n" + "=" * 50)
        print("ENHANCED SEARCH TEST RESULTS")
        print("=" * 50)
        print(f"✅ Pass Rate: {stats['summary']['pass_rate']*100:.1f}%")
        print(f"📈 Avg Confidence: {stats['accuracy']['avg_confidence']:.3f}")
        print(f"⚡ Avg Response Time: {stats['performance']['avg_response_time_ms']:.2f}ms")
        
        # Show improvement
        baseline = 0.264
        improvement = ((stats['summary']['pass_rate'] - baseline) / baseline) * 100
        print(f"📊 Improvement from baseline: {improvement:.1f}%")
        
        print(f"📝 Report saved to: {args.output}")
        print()
        
        # Cleanup
        await tester.db_manager.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error("Test script failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
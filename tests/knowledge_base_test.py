#!/usr/bin/env python3
"""
FACT System Knowledge Base Comprehensive Testing

This script tests the knowledge base with variations of all Q&A entries
and scores the response accuracy, relevance, and retrieval performance.
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


class QuestionVariationGenerator:
    """Generate variations of questions for testing."""
    
    def __init__(self):
        """Initialize the variation generator."""
        self.variation_patterns = {
            "synonyms": {
                "requirements": ["requirements", "needs", "prerequisites", "qualifications"],
                "license": ["license", "permit", "certification", "credential"],
                "contractor": ["contractor", "builder", "construction professional"],
                "cost": ["cost", "price", "fee", "expense", "charge"],
                "exam": ["exam", "test", "examination", "assessment"],
                "state": ["state", "location", "jurisdiction", "region"],
                "how": ["how", "what's the process", "what are the steps"],
                "get": ["get", "obtain", "acquire", "secure"],
                "need": ["need", "require", "must have", "necessary"]
            },
            "question_formats": [
                "What are {topic}?",
                "Tell me about {topic}",
                "I need information on {topic}",
                "Can you explain {topic}?",
                "How do I {action}?",
                "What's required for {topic}?",
                "Help me understand {topic}",
                "{topic}",  # Direct statement
                "I'm looking for {topic}",
                "Do you know about {topic}?"
            ],
            "casual_variations": [
                "umm, {question}",
                "so {question}",
                "hey, {question}",
                "{question}, you know?",
                "I was wondering, {question}",
                "quick question - {question}"
            ],
            "typos": {
                "license": ["licence", "lisence", "liscense"],
                "contractor": ["contracter", "contractr"],
                "requirements": ["requirments", "requiremnts"],
                "Georgia": ["Gerogia", "Gorgia"],
                "California": ["Califonia", "Cali"]
            }
        }
    
    def generate_variations(self, original_question: str, num_variations: int = 5) -> List[str]:
        """
        Generate variations of a question.
        
        Args:
            original_question: The original question text
            num_variations: Number of variations to generate
            
        Returns:
            List of question variations
        """
        variations = []
        
        # 1. Synonym replacement
        synonym_variation = self._replace_synonyms(original_question)
        if synonym_variation != original_question:
            variations.append(synonym_variation)
        
        # 2. Format change
        format_variation = self._change_format(original_question)
        if format_variation:
            variations.append(format_variation)
        
        # 3. Casual variation
        casual_variation = self._make_casual(original_question)
        variations.append(casual_variation)
        
        # 4. Add typos (occasionally)
        if random.random() < 0.3:  # 30% chance
            typo_variation = self._add_typos(original_question)
            variations.append(typo_variation)
        
        # 5. Rephrase with different structure
        rephrase = self._rephrase_question(original_question)
        if rephrase:
            variations.append(rephrase)
        
        # 6. Abbreviation/expansion
        abbrev_variation = self._abbreviate_expand(original_question)
        if abbrev_variation != original_question:
            variations.append(abbrev_variation)
        
        # Remove duplicates and limit to requested number
        variations = list(set(variations))[:num_variations]
        
        # Ensure we have enough variations
        while len(variations) < num_variations:
            # Add minor modifications
            base = original_question.lower()
            modifiers = ["please tell me ", "I need to know ", "what about ", "explain "]
            variations.append(random.choice(modifiers) + base)
        
        return variations[:num_variations]
    
    def _replace_synonyms(self, text: str) -> str:
        """Replace words with synonyms."""
        result = text
        for word, synonyms in self.variation_patterns["synonyms"].items():
            if word in result.lower():
                replacement = random.choice([s for s in synonyms if s != word])
                result = re.sub(r'\b' + word + r'\b', replacement, result, flags=re.IGNORECASE)
        return result
    
    def _change_format(self, text: str) -> str:
        """Change question format."""
        # Extract key topic from question
        topic_patterns = [
            r"(.*?) requirements",
            r"requirements for (.*)",
            r"about (.*)",
            r"(.*?) license"
        ]
        
        for pattern in topic_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                template = random.choice(self.variation_patterns["question_formats"])
                return template.format(topic=topic, action=f"get {topic}")
        
        return text
    
    def _make_casual(self, text: str) -> str:
        """Make question more casual."""
        template = random.choice(self.variation_patterns["casual_variations"])
        return template.format(question=text.lower())
    
    def _add_typos(self, text: str) -> str:
        """Add realistic typos."""
        result = text
        for correct, typos in self.variation_patterns["typos"].items():
            if correct.lower() in result.lower():
                typo = random.choice(typos)
                result = re.sub(r'\b' + correct + r'\b', typo, result, flags=re.IGNORECASE)
                break  # Only add one typo
        return result
    
    def _rephrase_question(self, text: str) -> str:
        """Rephrase question with different structure."""
        rephrases = {
            "What are": "Can you list",
            "How do I": "What's the process to",
            "requirements": "what I need",
            "Tell me about": "I'd like to know about"
        }
        
        result = text
        for original, replacement in rephrases.items():
            if original in result:
                result = result.replace(original, replacement)
                break
        
        return result
    
    def _abbreviate_expand(self, text: str) -> str:
        """Abbreviate or expand terms."""
        abbreviations = {
            "Georgia": "GA",
            "California": "CA",
            "Florida": "FL",
            "Texas": "TX",
            "requirements": "reqs",
            "license": "lic",
            "contractor": "GC"  # General Contractor
        }
        
        result = text
        # Randomly choose to abbreviate or expand
        if random.random() < 0.5:
            # Abbreviate
            for full, abbrev in abbreviations.items():
                if full in result:
                    result = result.replace(full, abbrev)
                    break
        else:
            # Expand (reverse)
            for full, abbrev in abbreviations.items():
                if abbrev in result and abbrev != "I":  # Avoid false positives
                    result = result.replace(abbrev, full)
                    break
        
        return result


class ResponseScorer:
    """Score the accuracy of retrieved responses."""
    
    def __init__(self):
        """Initialize the scorer."""
        self.key_terms_weights = {
            "critical": ["required", "must", "mandatory", "necessary"],
            "important": ["should", "recommended", "typically", "usually"],
            "specific": ["$", "years", "days", "hours", "%", "exam", "test"]
        }
    
    def calculate_similarity(self, expected: str, retrieved: str) -> float:
        """
        Calculate similarity score between expected and retrieved answers.
        
        Args:
            expected: Expected answer
            retrieved: Retrieved answer
            
        Returns:
            Similarity score between 0 and 1
        """
        if not expected or not retrieved:
            return 0.0
        
        # Convert to lowercase for comparison
        expected_lower = expected.lower()
        retrieved_lower = retrieved.lower()
        
        # 1. Exact match
        if expected_lower == retrieved_lower:
            return 1.0
        
        # 2. Calculate word overlap (Jaccard similarity)
        expected_words = set(expected_lower.split())
        retrieved_words = set(retrieved_lower.split())
        
        intersection = expected_words.intersection(retrieved_words)
        union = expected_words.union(retrieved_words)
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        # 3. Check for key terms preservation
        key_term_score = self._score_key_terms(expected_lower, retrieved_lower)
        
        # 4. Check for numerical accuracy
        number_score = self._score_numbers(expected, retrieved)
        
        # 5. Length similarity (penalize very different lengths)
        length_ratio = min(len(retrieved), len(expected)) / max(len(retrieved), len(expected))
        length_score = length_ratio if length_ratio > 0.5 else 0.5
        
        # Weighted combination
        final_score = (
            jaccard * 0.4 +           # Word overlap
            key_term_score * 0.3 +     # Key terms
            number_score * 0.2 +       # Numbers
            length_score * 0.1         # Length
        )
        
        return min(1.0, final_score)
    
    def _score_key_terms(self, expected: str, retrieved: str) -> float:
        """Score preservation of key terms."""
        score = 0.0
        total_weight = 0.0
        
        for category, terms in self.key_terms_weights.items():
            weight = 1.0 if category == "critical" else 0.7 if category == "important" else 0.5
            
            for term in terms:
                if term in expected:
                    total_weight += weight
                    if term in retrieved:
                        score += weight
        
        if total_weight == 0:
            return 1.0  # No key terms to check
        
        return score / total_weight
    
    def _score_numbers(self, expected: str, retrieved: str) -> float:
        """Score accuracy of numerical information."""
        import re
        
        # Extract numbers from both strings
        expected_numbers = set(re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', expected))
        retrieved_numbers = set(re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', retrieved))
        
        if not expected_numbers:
            return 1.0  # No numbers to check
        
        if not retrieved_numbers:
            return 0.0  # Expected numbers but none found
        
        # Calculate overlap
        correct = len(expected_numbers.intersection(retrieved_numbers))
        total = len(expected_numbers)
        
        return correct / total
    
    def determine_pass_threshold(self, category: str) -> float:
        """
        Determine pass threshold based on category.
        
        Args:
            category: Question category
            
        Returns:
            Minimum similarity score to pass
        """
        critical_categories = [
            "state_licensing_requirements",
            "exam_preparation_testing",
            "financial_planning_roi"
        ]
        
        if category in critical_categories:
            return 0.8  # Higher threshold for critical information
        else:
            return 0.7  # Standard threshold


class KnowledgeBaseTester:
    """Main testing orchestrator for knowledge base."""
    
    def __init__(self, database_path: str = "data/fact_system.db"):
        """Initialize the tester."""
        self.db_manager = DatabaseManager(database_path)
        self.generator = QuestionVariationGenerator()
        self.scorer = ResponseScorer()
        self.results: List[TestResult] = []
        
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
    
    async def search_knowledge(self, query: str, category: str = None, 
                              state: str = None) -> Tuple[Dict[str, Any], float]:
        """
        Search knowledge base and measure response time.
        
        Args:
            query: Search query
            category: Optional category filter
            state: Optional state filter
            
        Returns:
            Tuple of (best match result, response time in ms)
        """
        import time
        
        start_time = time.time()
        
        try:
            # Build search query
            sql_parts = ["SELECT * FROM knowledge_base WHERE 1=1"]
            
            # Add text search
            if query:
                # Escape single quotes for SQL
                safe_query = query.replace("'", "''")
                sql_parts.append(f"""
                    AND (
                        question LIKE '%{safe_query}%' 
                        OR answer LIKE '%{safe_query}%'
                        OR tags LIKE '%{safe_query}%'
                    )
                """)
            
            if category:
                sql_parts.append(f"AND category = '{category}'")
            
            if state:
                sql_parts.append(f"AND state = '{state}'")
            
            sql_parts.append("LIMIT 1")
            
            sql_query = " ".join(sql_parts)
            
            async with self.db_manager.get_connection() as conn:
                cursor = await conn.execute(sql_query)
                row = await cursor.fetchone()
                
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                
                if row:
                    result = {
                        "id": row[0],
                        "question": row[1],
                        "answer": row[2],
                        "category": row[3],
                        "tags": row[4],
                        "state": row[5],
                        "priority": row[6],
                        "difficulty": row[7]
                    }
                    return result, response_time_ms
                else:
                    return None, response_time_ms
                    
        except Exception as e:
            logger.error(f"Search failed: {e}")
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            return None, response_time_ms
    
    async def test_single_entry(self, entry: Dict[str, Any], 
                               num_variations: int = 3) -> List[TestResult]:
        """
        Test a single knowledge base entry with variations.
        
        Args:
            entry: Knowledge base entry to test
            num_variations: Number of variations to test
            
        Returns:
            List of test results
        """
        test_results = []
        
        # Generate variations
        variations = self.generator.generate_variations(
            entry["question"], 
            num_variations
        )
        
        for variation in variations:
            # Search with variation
            result, response_time = await self.search_knowledge(
                variation,
                category=entry["category"],
                state=entry["state"]
            )
            
            if result:
                # Calculate similarity score
                similarity = self.scorer.calculate_similarity(
                    entry["answer"],
                    result["answer"]
                )
                
                # Determine if test passed
                threshold = self.scorer.determine_pass_threshold(entry["category"])
                passed = similarity >= threshold
                
                # Check exact match
                exact_match = result["id"] == entry["id"]
                
                # Check category and state match
                category_match = result["category"] == entry["category"]
                state_match = result.get("state") == entry.get("state")
                
                test_result = TestResult(
                    original_question=entry["question"],
                    variation=variation,
                    expected_answer=entry["answer"],
                    retrieved_answer=result["answer"],
                    similarity_score=similarity,
                    retrieval_time_ms=response_time,
                    exact_match=exact_match,
                    category_match=category_match,
                    state_match=state_match,
                    passed=passed
                )
            else:
                # No result found
                test_result = TestResult(
                    original_question=entry["question"],
                    variation=variation,
                    expected_answer=entry["answer"],
                    retrieved_answer="",
                    similarity_score=0.0,
                    retrieval_time_ms=response_time,
                    exact_match=False,
                    category_match=False,
                    state_match=False,
                    passed=False
                )
            
            test_results.append(test_result)
        
        return test_results
    
    async def run_comprehensive_test(self, sample_size: int = None, 
                                    variations_per_question: int = 3) -> Dict[str, Any]:
        """
        Run comprehensive test on knowledge base.
        
        Args:
            sample_size: Number of entries to test (None for all)
            variations_per_question: Number of variations per question
            
        Returns:
            Test summary and statistics
        """
        logger.info("Starting comprehensive knowledge base test")
        
        # Load knowledge base
        entries = await self.load_knowledge_base()
        
        # Sample if requested
        if sample_size and sample_size < len(entries):
            entries = random.sample(entries, sample_size)
            logger.info(f"Testing sample of {sample_size} entries")
        
        # Test each entry
        all_results = []
        for i, entry in enumerate(entries):
            if i % 50 == 0:
                logger.info(f"Testing entry {i+1}/{len(entries)}")
            
            results = await self.test_single_entry(entry, variations_per_question)
            all_results.extend(results)
            self.results.extend(results)
        
        # Calculate statistics
        stats = self.calculate_statistics(all_results)
        
        logger.info("Comprehensive test completed", stats=stats)
        
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
        
        similarity_scores = [r.similarity_score for r in results]
        response_times = [r.retrieval_time_ms for r in results]
        
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
                problematic.append({
                    "question": question,
                    "pass_rate": pass_rate,
                    "avg_score": avg_score,
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
            "accuracy": {
                "exact_match_rate": exact_matches / total_tests,
                "category_match_rate": category_matches / total_tests,
                "state_match_rate": state_matches / total_tests,
                "avg_similarity_score": np.mean(similarity_scores),
                "median_similarity_score": np.median(similarity_scores),
                "min_similarity_score": min(similarity_scores),
                "max_similarity_score": max(similarity_scores),
                "std_similarity_score": np.std(similarity_scores)
            },
            "performance": {
                "avg_response_time_ms": np.mean(response_times),
                "median_response_time_ms": np.median(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "p95_response_time_ms": np.percentile(response_times, 95),
                "p99_response_time_ms": np.percentile(response_times, 99)
            },
            "problematic_questions": problematic[:10],  # Top 10 problematic
            "test_timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_report(self, stats: Dict[str, Any], output_file: str = None) -> str:
        """Generate a detailed test report."""
        report = []
        report.append("=" * 80)
        report.append("FACT KNOWLEDGE BASE COMPREHENSIVE TEST REPORT")
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
        
        # Accuracy Metrics
        report.append("ACCURACY METRICS")
        report.append("-" * 40)
        accuracy = stats["accuracy"]
        report.append(f"Exact Match Rate: {accuracy['exact_match_rate']*100:.1f}%")
        report.append(f"Category Match Rate: {accuracy['category_match_rate']*100:.1f}%")
        report.append(f"State Match Rate: {accuracy['state_match_rate']*100:.1f}%")
        report.append(f"Average Similarity Score: {accuracy['avg_similarity_score']:.3f}")
        report.append(f"Median Similarity Score: {accuracy['median_similarity_score']:.3f}")
        report.append(f"Score Range: {accuracy['min_similarity_score']:.3f} - {accuracy['max_similarity_score']:.3f}")
        report.append(f"Score Std Dev: {accuracy['std_similarity_score']:.3f}")
        report.append("")
        
        # Performance Metrics
        report.append("PERFORMANCE METRICS")
        report.append("-" * 40)
        performance = stats["performance"]
        report.append(f"Average Response Time: {performance['avg_response_time_ms']:.2f}ms")
        report.append(f"Median Response Time: {performance['median_response_time_ms']:.2f}ms")
        report.append(f"P95 Response Time: {performance['p95_response_time_ms']:.2f}ms")
        report.append(f"P99 Response Time: {performance['p99_response_time_ms']:.2f}ms")
        report.append(f"Response Time Range: {performance['min_response_time_ms']:.2f}ms - {performance['max_response_time_ms']:.2f}ms")
        report.append("")
        
        # Problematic Questions
        if stats["problematic_questions"]:
            report.append("PROBLEMATIC QUESTIONS (Lowest Pass Rates)")
            report.append("-" * 40)
            for i, pq in enumerate(stats["problematic_questions"], 1):
                report.append(f"{i}. Question: {pq['question'][:80]}...")
                report.append(f"   Pass Rate: {pq['pass_rate']*100:.1f}%")
                report.append(f"   Avg Score: {pq['avg_score']:.3f}")
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
            grade = "C (Poor)"
        else:
            grade = "F (Failing)"
        
        report.append(f"Grade: {grade}")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        
        if pass_rate < 0.90:
            report.append("• Review and improve search algorithm for better variation handling")
        
        if accuracy['exact_match_rate'] < 0.70:
            report.append("• Consider implementing fuzzy matching or semantic search")
        
        if performance['p95_response_time_ms'] > 100:
            report.append("• Optimize database queries and consider adding indexes")
        
        if stats["problematic_questions"]:
            report.append("• Review problematic questions for indexing or tagging improvements")
        
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
    """Main function to run comprehensive knowledge base test."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FACT knowledge base with Q&A variations")
    parser.add_argument("--sample", type=int, default=None,
                       help="Number of questions to sample (default: all)")
    parser.add_argument("--variations", type=int, default=3,
                       help="Number of variations per question (default: 3)")
    parser.add_argument("--output", default="test_report.txt",
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
    
    print("🧪 FACT Knowledge Base Comprehensive Testing")
    print("=" * 50)
    print(f"Database: {args.database}")
    print(f"Sample Size: {args.sample if args.sample else 'All entries'}")
    print(f"Variations per Question: {args.variations}")
    print("=" * 50)
    print()
    
    try:
        # Create tester
        tester = KnowledgeBaseTester(args.database)
        
        # Run comprehensive test
        print("🔍 Running comprehensive test...")
        stats = await tester.run_comprehensive_test(
            sample_size=args.sample,
            variations_per_question=args.variations
        )
        
        # Generate report
        print("\n📊 Generating report...")
        report = tester.generate_report(stats, args.output)
        
        # Print summary to console
        print("\n" + "=" * 50)
        print("TEST RESULTS SUMMARY")
        print("=" * 50)
        print(f"✅ Pass Rate: {stats['summary']['pass_rate']*100:.1f}%")
        print(f"📈 Avg Similarity: {stats['accuracy']['avg_similarity_score']:.3f}")
        print(f"⚡ Avg Response Time: {stats['performance']['avg_response_time_ms']:.2f}ms")
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
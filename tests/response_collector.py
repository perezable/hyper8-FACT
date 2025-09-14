"""
Response Collector for FACT System Testing

Collects, analyzes, and stores test results with comprehensive evaluation
metrics including accuracy scoring, performance analysis, and reporting.
"""

import json
import sqlite3
import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from collections import defaultdict, Counter
import re

# Set up logging  
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Individual test result with comprehensive metrics"""
    query_id: str
    question_id: str
    query_text: str
    method: str
    success: bool
    response: Optional[Dict[str, Any]]
    response_time_ms: float
    accuracy_score: Optional[float] = None
    relevance_score: Optional[float] = None
    completeness_score: Optional[float] = None
    error_message: Optional[str] = None
    attempt_count: int = 1
    timestamp: datetime = field(default_factory=datetime.now)
    evaluation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class TestSummary:
    """Comprehensive test summary with aggregated metrics"""
    session_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    config: Dict[str, Any]
    method_summaries: Dict[str, Any]
    overall_metrics: Dict[str, Any]
    all_results: List[TestResult] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat()
        result['all_results'] = [r.to_dict() for r in self.all_results]
        return result


class ResponseEvaluator:
    """Evaluates response quality using multiple metrics"""
    
    def __init__(self):
        self.contractor_keywords = {
            'license', 'licensing', 'permit', 'certification', 'requirements',
            'exam', 'test', 'experience', 'bond', 'insurance', 'application',
            'fee', 'cost', 'state', 'contractor', 'general', 'specialty',
            'qualification', 'renewal', 'registration'
        }
        
        self.state_abbreviations = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        }
        
        # Category-specific keywords for relevance scoring
        self.category_keywords = {
            'state_licensing_requirements': {
                'requirements', 'license', 'permit', 'application', 'qualification',
                'experience', 'education', 'exam', 'bond', 'insurance'
            },
            'exam_preparation_testing': {
                'exam', 'test', 'preparation', 'study', 'questions', 'score',
                'passing', 'practice', 'materials', 'review'
            },
            'qualifier_network_programs': {
                'qualifier', 'network', 'program', 'partnership', 'referral',
                'connections', 'business', 'opportunities', 'leads'
            },
            'business_formation_operations': {
                'business', 'formation', 'LLC', 'corporation', 'operations',
                'setup', 'structure', 'legal', 'entity', 'registration'
            },
            'insurance_bonding': {
                'insurance', 'bond', 'bonding', 'surety', 'liability',
                'coverage', 'premium', 'policy', 'protection'
            },
            'financial_planning_roi': {
                'ROI', 'return', 'investment', 'profit', 'income', 'revenue',
                'financial', 'planning', 'cost', 'benefit', 'payback'
            },
            'success_stories_case_studies': {
                'success', 'story', 'case', 'study', 'example', 'testimonial',
                'experience', 'results', 'outcome', 'achievement'
            },
            'troubleshooting_problem_resolution': {
                'problem', 'issue', 'troubleshooting', 'solution', 'help',
                'fix', 'resolve', 'error', 'difficulty', 'support'
            }
        }
    
    def evaluate_response(self, query_text: str, response: Dict[str, Any], 
                         expected_category: Optional[str] = None,
                         expected_state: Optional[str] = None) -> Dict[str, float]:
        """
        Comprehensive response evaluation returning multiple scores.
        
        Returns:
            Dict with accuracy_score, relevance_score, completeness_score
        """
        if not response or not response.get('answer'):
            return {
                'accuracy_score': 0.0,
                'relevance_score': 0.0,
                'completeness_score': 0.0
            }
        
        answer = response.get('answer', '').lower()
        query_lower = query_text.lower()
        
        # 1. Accuracy Score - How well does the response match the query intent
        accuracy_score = self._calculate_accuracy_score(query_lower, answer, response)
        
        # 2. Relevance Score - How relevant is the response to the category/domain
        relevance_score = self._calculate_relevance_score(
            answer, expected_category, expected_state, response
        )
        
        # 3. Completeness Score - How complete/comprehensive is the response
        completeness_score = self._calculate_completeness_score(answer, query_lower)
        
        return {
            'accuracy_score': accuracy_score,
            'relevance_score': relevance_score,
            'completeness_score': completeness_score
        }
    
    def _calculate_accuracy_score(self, query: str, answer: str, response: Dict[str, Any]) -> float:
        """Calculate accuracy score based on query-answer matching"""
        score = 0.0
        
        # Extract key terms from query
        query_words = set(re.findall(r'\b\w+\b', query))
        query_words = {w for w in query_words if len(w) > 2}  # Filter short words
        
        answer_words = set(re.findall(r'\b\w+\b', answer))
        
        # 1. Keyword overlap (30% weight)
        if query_words:
            overlap = query_words.intersection(answer_words)
            keyword_score = len(overlap) / len(query_words)
            score += keyword_score * 0.3
        
        # 2. Contractor domain relevance (25% weight)
        contractor_matches = self.contractor_keywords.intersection(answer_words)
        domain_score = min(len(contractor_matches) / 5.0, 1.0)  # Cap at 5 matches
        score += domain_score * 0.25
        
        # 3. Specific answer patterns (25% weight)
        pattern_score = 0.0
        
        # Check for specific information patterns
        if re.search(r'\$\d+', answer):  # Dollar amounts
            pattern_score += 0.3
        if re.search(r'\d+\s*(years?|months?|days?)', answer):  # Time periods
            pattern_score += 0.3
        if re.search(r'\d+%', answer):  # Percentages
            pattern_score += 0.2
        if any(state in answer.upper() for state in self.state_abbreviations):  # State mention
            pattern_score += 0.2
        
        score += min(pattern_score, 1.0) * 0.25
        
        # 4. Response confidence/metadata (20% weight)
        confidence = response.get('confidence', 0.5)
        if isinstance(confidence, (int, float)):
            score += confidence * 0.2
        
        return min(score, 1.0)
    
    def _calculate_relevance_score(self, answer: str, expected_category: Optional[str],
                                 expected_state: Optional[str], response: Dict[str, Any]) -> float:
        """Calculate relevance score based on category and context"""
        score = 0.5  # Base score
        
        # 1. Category relevance (40% weight)
        if expected_category and expected_category in self.category_keywords:
            category_words = self.category_keywords[expected_category]
            answer_words = set(re.findall(r'\b\w+\b', answer.lower()))
            
            matches = category_words.intersection(answer_words)
            category_score = min(len(matches) / 3.0, 1.0)  # Cap at 3 matches
            score += category_score * 0.4 - 0.2  # Adjust from base
        
        # 2. State relevance (30% weight)
        if expected_state:
            state_mentioned = False
            state_variations = [
                expected_state.upper(),
                expected_state.lower(),
                self._get_state_name(expected_state)
            ]
            
            for variation in state_variations:
                if variation and variation.lower() in answer.lower():
                    state_mentioned = True
                    break
            
            if state_mentioned:
                score += 0.3
            else:
                score -= 0.1  # Penalty for missing expected state
        
        # 3. Response metadata relevance (30% weight)
        response_category = response.get('category', '').lower()
        response_state = response.get('state', '').upper()
        
        if expected_category and response_category:
            if expected_category.lower() in response_category:
                score += 0.15
        
        if expected_state and response_state:
            if expected_state.upper() == response_state:
                score += 0.15
        
        return max(0.0, min(score, 1.0))
    
    def _calculate_completeness_score(self, answer: str, query: str) -> float:
        """Calculate completeness score based on answer length and detail"""
        score = 0.0
        
        # 1. Length appropriateness (30% weight)
        answer_length = len(answer.split())
        if answer_length < 10:
            length_score = 0.2  # Too short
        elif answer_length < 30:
            length_score = 0.6  # Adequate
        elif answer_length < 100:
            length_score = 1.0  # Good length
        elif answer_length < 200:
            length_score = 0.8  # Long but acceptable
        else:
            length_score = 0.4  # Too long
        
        score += length_score * 0.3
        
        # 2. Information density (40% weight)
        # Count specific details: numbers, dollar amounts, percentages, etc.
        detail_patterns = [
            r'\$\d+(?:,\d+)*(?:\.\d+)?',  # Dollar amounts
            r'\d+\s*(?:years?|months?|days?|hours?)',  # Time periods
            r'\d+(?:\.\d+)?%',  # Percentages
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # Dates
            r'\b\d+\s*(?:questions?|points?|credits?)\b',  # Quantities
        ]
        
        detail_count = 0
        for pattern in detail_patterns:
            detail_count += len(re.findall(pattern, answer, re.IGNORECASE))
        
        detail_score = min(detail_count / 3.0, 1.0)  # Cap at 3 details
        score += detail_score * 0.4
        
        # 3. Structure and organization (30% weight)
        structure_score = 0.0
        
        # Check for structured information
        if any(word in answer.lower() for word in ['first', 'second', 'third', 'finally']):
            structure_score += 0.3
        if any(char in answer for char in ['•', '-', '1.', '2.']):
            structure_score += 0.3
        if len(re.findall(r'[.!?]', answer)) > 2:  # Multiple sentences
            structure_score += 0.4
        
        score += min(structure_score, 1.0) * 0.3
        
        return min(score, 1.0)
    
    def _get_state_name(self, state_code: str) -> Optional[str]:
        """Get full state name from abbreviation"""
        state_names = {
            'AL': 'alabama', 'AK': 'alaska', 'AZ': 'arizona', 'AR': 'arkansas',
            'CA': 'california', 'CO': 'colorado', 'CT': 'connecticut', 'DE': 'delaware',
            'FL': 'florida', 'GA': 'georgia', 'HI': 'hawaii', 'ID': 'idaho',
            'IL': 'illinois', 'IN': 'indiana', 'IA': 'iowa', 'KS': 'kansas',
            'KY': 'kentucky', 'LA': 'louisiana', 'ME': 'maine', 'MD': 'maryland',
            'MA': 'massachusetts', 'MI': 'michigan', 'MN': 'minnesota', 'MS': 'mississippi',
            'MO': 'missouri', 'MT': 'montana', 'NE': 'nebraska', 'NV': 'nevada',
            'NH': 'new hampshire', 'NJ': 'new jersey', 'NM': 'new mexico', 'NY': 'new york',
            'NC': 'north carolina', 'ND': 'north dakota', 'OH': 'ohio', 'OK': 'oklahoma',
            'OR': 'oregon', 'PA': 'pennsylvania', 'RI': 'rhode island', 'SC': 'south carolina',
            'SD': 'south dakota', 'TN': 'tennessee', 'TX': 'texas', 'UT': 'utah',
            'VT': 'vermont', 'VA': 'virginia', 'WA': 'washington', 'WV': 'west virginia',
            'WI': 'wisconsin', 'WY': 'wyoming'
        }
        return state_names.get(state_code.upper())


class ResponseCollector:
    """
    Collects and analyzes test results with persistent storage
    and comprehensive performance metrics.
    """
    
    def __init__(self, config):
        self.config = config
        self.evaluator = ResponseEvaluator()
        self.results = []
        self.db_path = None
        
        # Performance tracking
        self.method_performance = defaultdict(list)
        self.category_performance = defaultdict(list)
        self.error_patterns = Counter()
        
        # Create storage directory
        self.storage_dir = Path(config.output_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    async def initialize(self):
        """Initialize response collector with persistent storage"""
        # Set up SQLite database for results
        self.db_path = self.storage_dir / "test_results.db"
        
        # Create database schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                query_id TEXT,
                question_id TEXT,
                query_text TEXT,
                method TEXT,
                success BOOLEAN,
                response_json TEXT,
                response_time_ms REAL,
                accuracy_score REAL,
                relevance_score REAL,
                completeness_score REAL,
                error_message TEXT,
                attempt_count INTEGER,
                timestamp DATETIME,
                evaluation_metadata_json TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_sessions (
                session_id TEXT PRIMARY KEY,
                start_time DATETIME,
                end_time DATETIME,
                duration_seconds REAL,
                config_json TEXT,
                summary_json TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Response collector initialized with database: {self.db_path}")
    
    async def collect_result(self, result_data: Dict[str, Any], 
                           expected_category: Optional[str] = None,
                           expected_state: Optional[str] = None) -> TestResult:
        """
        Collect and evaluate a single test result.
        
        Args:
            result_data: Raw result data from query executor
            expected_category: Expected response category for evaluation
            expected_state: Expected state for evaluation
            
        Returns:
            TestResult with evaluation scores
        """
        # Create base test result
        test_result = TestResult(
            query_id=result_data.get('query_id', ''),
            question_id=result_data.get('question_id', ''),
            query_text=result_data.get('query_text', ''),
            method=result_data.get('method', ''),
            success=result_data.get('success', False),
            response=result_data.get('response'),
            response_time_ms=result_data.get('response_time_ms', 0.0),
            error_message=result_data.get('error_message'),
            attempt_count=result_data.get('attempt_count', 1),
            timestamp=datetime.fromisoformat(result_data.get('timestamp', datetime.now().isoformat()))
        )
        
        # Evaluate response quality if successful
        if test_result.success and test_result.response:
            evaluation = self.evaluator.evaluate_response(
                test_result.query_text,
                test_result.response,
                expected_category,
                expected_state
            )
            
            test_result.accuracy_score = evaluation['accuracy_score']
            test_result.relevance_score = evaluation['relevance_score']
            test_result.completeness_score = evaluation['completeness_score']
            
            # Store evaluation metadata
            test_result.evaluation_metadata = {
                'expected_category': expected_category,
                'expected_state': expected_state,
                'response_category': test_result.response.get('category'),
                'response_state': test_result.response.get('state'),
                'confidence': test_result.response.get('confidence'),
                'source': test_result.response.get('source')
            }
        
        # Track performance metrics
        self._update_performance_tracking(test_result)
        
        # Store in database
        await self._store_result(test_result)
        
        # Add to in-memory collection
        self.results.append(test_result)
        
        return test_result
    
    def _update_performance_tracking(self, result: TestResult):
        """Update performance tracking metrics"""
        # Method performance
        self.method_performance[result.method].append({
            'success': result.success,
            'response_time_ms': result.response_time_ms,
            'accuracy_score': result.accuracy_score,
            'timestamp': result.timestamp
        })
        
        # Category performance (if available)
        if result.response and result.response.get('category'):
            category = result.response['category']
            self.category_performance[category].append({
                'success': result.success,
                'response_time_ms': result.response_time_ms,
                'accuracy_score': result.accuracy_score,
                'method': result.method
            })
        
        # Error pattern tracking
        if not result.success and result.error_message:
            # Classify error types
            error_type = self._classify_error(result.error_message)
            self.error_patterns[error_type] += 1
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error message into categories"""
        error_lower = error_message.lower()
        
        if 'timeout' in error_lower or 'timed out' in error_lower:
            return 'timeout'
        elif 'connection' in error_lower or 'network' in error_lower:
            return 'network'
        elif 'database' in error_lower or 'sql' in error_lower:
            return 'database'
        elif '404' in error_lower or 'not found' in error_lower:
            return 'not_found'
        elif '500' in error_lower or 'internal server' in error_lower:
            return 'server_error'
        elif 'authentication' in error_lower or 'unauthorized' in error_lower:
            return 'auth_error'
        elif 'rate limit' in error_lower or 'too many' in error_lower:
            return 'rate_limit'
        else:
            return 'other'
    
    async def _store_result(self, result: TestResult):
        """Store test result in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO test_results (
                session_id, query_id, question_id, query_text, method,
                success, response_json, response_time_ms, accuracy_score,
                relevance_score, completeness_score, error_message,
                attempt_count, timestamp, evaluation_metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            getattr(self, 'session_id', 'unknown'),
            result.query_id,
            result.question_id,
            result.query_text,
            result.method,
            result.success,
            json.dumps(result.response) if result.response else None,
            result.response_time_ms,
            result.accuracy_score,
            result.relevance_score,
            result.completeness_score,
            result.error_message,
            result.attempt_count,
            result.timestamp.isoformat(),
            json.dumps(result.evaluation_metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        if not self.results:
            return {"error": "No results to analyze"}
        
        # Overall statistics
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Response time statistics
        response_times = [r.response_time_ms for r in self.results if r.success]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = 0
        
        # Accuracy statistics
        accuracy_scores = [r.accuracy_score for r in self.results if r.accuracy_score is not None]
        if accuracy_scores:
            avg_accuracy = statistics.mean(accuracy_scores)
            median_accuracy = statistics.median(accuracy_scores)
        else:
            avg_accuracy = median_accuracy = 0
        
        # Method performance comparison
        method_stats = {}
        for method, performances in self.method_performance.items():
            if performances:
                method_stats[method] = {
                    'total_tests': len(performances),
                    'success_rate': sum(1 for p in performances if p['success']) / len(performances),
                    'avg_response_time': statistics.mean([p['response_time_ms'] for p in performances if p['success']]) if any(p['success'] for p in performances) else 0,
                    'avg_accuracy': statistics.mean([p['accuracy_score'] for p in performances if p['accuracy_score'] is not None]) if any(p.get('accuracy_score') for p in performances) else 0
                }
        
        # Error analysis
        error_analysis = {
            'total_errors': total_tests - successful_tests,
            'error_rate': 1 - success_rate,
            'error_patterns': dict(self.error_patterns),
            'most_common_error': self.error_patterns.most_common(1)[0] if self.error_patterns else None
        }
        
        # Performance thresholds analysis
        threshold_analysis = {
            'response_time_threshold_met': avg_response_time <= self.config.max_response_time_ms,
            'accuracy_threshold_met': avg_accuracy >= self.config.min_accuracy_threshold,
            'error_rate_threshold_met': (1 - success_rate) <= self.config.max_error_rate
        }
        
        return {
            'overall_statistics': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': success_rate,
                'avg_response_time_ms': avg_response_time,
                'median_response_time_ms': median_response_time,
                'p95_response_time_ms': p95_response_time,
                'avg_accuracy_score': avg_accuracy,
                'median_accuracy_score': median_accuracy
            },
            'method_performance': method_stats,
            'error_analysis': error_analysis,
            'threshold_analysis': threshold_analysis,
            'category_breakdown': self._generate_category_breakdown(),
            'temporal_analysis': self._generate_temporal_analysis()
        }
    
    def _generate_category_breakdown(self) -> Dict[str, Any]:
        """Generate performance breakdown by category"""
        category_stats = {}
        
        for category, performances in self.category_performance.items():
            if performances:
                category_stats[category] = {
                    'total_tests': len(performances),
                    'success_rate': sum(1 for p in performances if p['success']) / len(performances),
                    'avg_response_time': statistics.mean([p['response_time_ms'] for p in performances if p['success']]) if any(p['success'] for p in performances) else 0,
                    'avg_accuracy': statistics.mean([p['accuracy_score'] for p in performances if p['accuracy_score'] is not None]) if any(p.get('accuracy_score') for p in performances) else 0,
                    'methods_used': list(set(p['method'] for p in performances))
                }
        
        return category_stats
    
    def _generate_temporal_analysis(self) -> Dict[str, Any]:
        """Generate temporal performance analysis"""
        if not self.results:
            return {}
        
        # Sort results by timestamp
        sorted_results = sorted(self.results, key=lambda r: r.timestamp)
        
        # Calculate performance over time (in 5-minute buckets)
        time_buckets = defaultdict(list)
        start_time = sorted_results[0].timestamp
        
        for result in sorted_results:
            bucket_index = int((result.timestamp - start_time).total_seconds() / 300)  # 5-minute buckets
            time_buckets[bucket_index].append(result)
        
        temporal_stats = {}
        for bucket_index, bucket_results in time_buckets.items():
            bucket_time = start_time + timedelta(seconds=bucket_index * 300)
            successful_in_bucket = [r for r in bucket_results if r.success]
            
            temporal_stats[bucket_time.isoformat()] = {
                'total_tests': len(bucket_results),
                'success_rate': len(successful_in_bucket) / len(bucket_results) if bucket_results else 0,
                'avg_response_time': statistics.mean([r.response_time_ms for r in successful_in_bucket]) if successful_in_bucket else 0
            }
        
        return temporal_stats
    
    async def export_results(self, format: str = 'json') -> Path:
        """Export results in specified format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == 'json':
            export_file = self.storage_dir / f"results_export_{timestamp}.json"
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_results': len(self.results),
                'performance_report': self.generate_performance_report(),
                'results': [r.to_dict() for r in self.results]
            }
            
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
        
        elif format == 'csv':
            import csv
            export_file = self.storage_dir / f"results_export_{timestamp}.csv"
            
            with open(export_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'query_id', 'question_id', 'query_text', 'method', 'success',
                    'response_time_ms', 'accuracy_score', 'relevance_score',
                    'completeness_score', 'error_message', 'timestamp'
                ])
                
                # Write data
                for result in self.results:
                    writer.writerow([
                        result.query_id,
                        result.question_id, 
                        result.query_text,
                        result.method,
                        result.success,
                        result.response_time_ms,
                        result.accuracy_score,
                        result.relevance_score,
                        result.completeness_score,
                        result.error_message,
                        result.timestamp.isoformat()
                    ])
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Results exported to: {export_file}")
        return export_file
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info(f"Response collector cleanup completed. {len(self.results)} results collected.")


# Testing and utility functions
async def test_response_evaluation():
    """Test response evaluation functionality"""
    evaluator = ResponseEvaluator()
    
    # Test cases
    test_cases = [
        {
            'query': 'What are the requirements for a contractor license in Georgia?',
            'response': {
                'answer': 'Georgia requires contractors to be licensed for work over $2,500. General contractor license requires 4 years experience or equivalent education. Application fee is $200, with total costs ranging $300-400.',
                'category': 'state_licensing_requirements',
                'state': 'GA',
                'confidence': 0.9
            },
            'expected_category': 'state_licensing_requirements',
            'expected_state': 'GA'
        },
        {
            'query': 'How much does bonding cost?',
            'response': {
                'answer': 'Bonding costs typically range from $100-$500 annually depending on the bond amount required.',
                'category': 'insurance_bonding',
                'confidence': 0.8
            },
            'expected_category': 'insurance_bonding'
        }
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest Case {i + 1}:")
        print(f"Query: {test_case['query']}")
        
        scores = evaluator.evaluate_response(
            test_case['query'],
            test_case['response'],
            test_case.get('expected_category'),
            test_case.get('expected_state')
        )
        
        print(f"Accuracy Score: {scores['accuracy_score']:.3f}")
        print(f"Relevance Score: {scores['relevance_score']:.3f}")
        print(f"Completeness Score: {scores['completeness_score']:.3f}")


if __name__ == "__main__":
    # Test response evaluation
    asyncio.run(test_response_evaluation())
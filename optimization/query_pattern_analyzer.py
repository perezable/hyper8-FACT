"""
FACT System Query Pattern Analyzer

Analyzes search patterns, success/failure rates, and generates optimization
recommendations for improving query performance and accuracy.
"""

import json
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import structlog
import re
from pathlib import Path

logger = structlog.get_logger(__name__)


@dataclass
class QueryMetrics:
    """Metrics for a specific query pattern."""
    query_pattern: str
    total_searches: int = 0
    successful_searches: int = 0
    failed_searches: int = 0
    avg_response_time_ms: float = 0.0
    avg_confidence_score: float = 0.0
    cache_hit_rate: float = 0.0
    common_variations: List[str] = field(default_factory=list)
    suggested_synonyms: List[str] = field(default_factory=list)
    improvement_potential: float = 0.0
    last_updated: float = field(default_factory=time.time)


@dataclass
class QueryAnalysisResult:
    """Result of query pattern analysis."""
    total_queries_analyzed: int
    unique_patterns_found: int
    top_failing_patterns: List[QueryMetrics]
    optimization_recommendations: List[Dict[str, Any]]
    synonym_suggestions: Dict[str, List[str]]
    search_term_improvements: Dict[str, str]
    performance_insights: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


class QueryPatternAnalyzer:
    """
    Analyzes query patterns to identify optimization opportunities.
    
    Focuses on:
    - Failed vs successful search patterns
    - Query variations and synonyms
    - Performance bottlenecks
    - Search term optimization
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the query pattern analyzer."""
        self.config = config or {}
        self.query_history: List[Dict[str, Any]] = []
        self.pattern_metrics: Dict[str, QueryMetrics] = {}
        self.synonyms_database = self._load_contractor_synonyms()
        self.state_mappings = self._load_state_mappings()
        
        # Analysis parameters
        self.min_pattern_frequency = 3
        self.failure_threshold = 0.3  # 30% failure rate triggers optimization
        self.low_confidence_threshold = 0.6
        self.slow_response_threshold = 150.0  # ms
        
        logger.info("Query pattern analyzer initialized")
    
    def record_query(self, query: str, success: bool, response_time_ms: float,
                    confidence_score: float = 0.0, cache_hit: bool = False,
                    metadata: Optional[Dict[str, Any]] = None):
        """Record a query for pattern analysis."""
        try:
            # Normalize query for pattern matching
            normalized_query = self._normalize_query(query)
            pattern = self._extract_query_pattern(normalized_query)
            
            # Record in history
            query_record = {
                'original_query': query,
                'normalized_query': normalized_query,
                'pattern': pattern,
                'success': success,
                'response_time_ms': response_time_ms,
                'confidence_score': confidence_score,
                'cache_hit': cache_hit,
                'timestamp': time.time(),
                'metadata': metadata or {}
            }
            self.query_history.append(query_record)
            
            # Update pattern metrics
            self._update_pattern_metrics(pattern, query_record)
            
            # Keep history manageable (last 10,000 queries)
            if len(self.query_history) > 10000:
                self.query_history = self.query_history[-10000:]
            
            logger.debug("Query recorded for analysis",
                        pattern=pattern,
                        success=success,
                        response_time_ms=response_time_ms)
        
        except Exception as e:
            logger.error("Failed to record query", query=query[:50], error=str(e))
    
    def analyze_patterns(self, time_window_hours: int = 24) -> QueryAnalysisResult:
        """
        Analyze query patterns and generate optimization recommendations.
        
        Args:
            time_window_hours: Time window for analysis
            
        Returns:
            Analysis results with recommendations
        """
        try:
            logger.info("Starting query pattern analysis", time_window_hours=time_window_hours)
            
            # Filter queries within time window
            cutoff_time = time.time() - (time_window_hours * 3600)
            recent_queries = [q for q in self.query_history if q['timestamp'] >= cutoff_time]
            
            if not recent_queries:
                logger.warning("No recent queries found for analysis")
                return QueryAnalysisResult(
                    total_queries_analyzed=0,
                    unique_patterns_found=0,
                    top_failing_patterns=[],
                    optimization_recommendations=[],
                    synonym_suggestions={},
                    search_term_improvements={},
                    performance_insights={}
                )
            
            # Analyze patterns
            pattern_analysis = self._analyze_pattern_performance(recent_queries)
            failing_patterns = self._identify_failing_patterns(pattern_analysis)
            
            # Generate recommendations
            recommendations = self._generate_optimization_recommendations(
                failing_patterns, recent_queries
            )
            
            # Create synonym suggestions
            synonym_suggestions = self._generate_synonym_suggestions(failing_patterns)
            
            # Search term improvements
            search_improvements = self._suggest_search_term_improvements(failing_patterns)
            
            # Performance insights
            performance_insights = self._analyze_performance_patterns(recent_queries)
            
            result = QueryAnalysisResult(
                total_queries_analyzed=len(recent_queries),
                unique_patterns_found=len(pattern_analysis),
                top_failing_patterns=failing_patterns[:10],
                optimization_recommendations=recommendations,
                synonym_suggestions=synonym_suggestions,
                search_term_improvements=search_improvements,
                performance_insights=performance_insights
            )
            
            logger.info("Query pattern analysis completed",
                       total_queries=len(recent_queries),
                       unique_patterns=len(pattern_analysis),
                       failing_patterns=len(failing_patterns))
            
            return result
        
        except Exception as e:
            logger.error("Query pattern analysis failed", error=str(e))
            raise
    
    def get_query_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get query suggestions based on successful patterns."""
        try:
            normalized_partial = self._normalize_query(partial_query)
            suggestions = []
            
            # Find patterns that match the partial query
            for pattern, metrics in self.pattern_metrics.items():
                if (normalized_partial.lower() in pattern.lower() and
                    metrics.successful_searches > 0 and
                    metrics.total_searches >= self.min_pattern_frequency):
                    
                    # Score based on success rate and frequency
                    success_rate = metrics.successful_searches / metrics.total_searches
                    frequency_score = min(metrics.total_searches / 100, 1.0)
                    score = success_rate * 0.7 + frequency_score * 0.3
                    
                    suggestions.append((score, pattern, metrics.common_variations))
            
            # Sort by score and return top suggestions
            suggestions.sort(reverse=True)
            result = []
            
            for score, pattern, variations in suggestions[:limit]:
                result.append(pattern)
                # Add variations if available
                for variation in variations[:2]:  # Top 2 variations
                    if len(result) < limit:
                        result.append(variation)
            
            return result[:limit]
        
        except Exception as e:
            logger.error("Failed to generate query suggestions", error=str(e))
            return []
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent analysis."""
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove punctuation except important ones
        normalized = re.sub(r'[^\w\s\-\'"]', ' ', normalized)
        
        # Expand common abbreviations
        abbreviations = {
            'lic': 'license',
            'req': 'requirements',
            'reqs': 'requirements',
            'gc': 'general contractor',
            'ga': 'georgia',
            'ca': 'california',
            'fl': 'florida',
            'tx': 'texas',
            'ny': 'new york',
            'cert': 'certification',
            'app': 'application',
            'exp': 'experience'
        }
        
        for abbrev, expansion in abbreviations.items():
            normalized = re.sub(r'\b' + abbrev + r'\b', expansion, normalized)
        
        return normalized.strip()
    
    def _extract_query_pattern(self, normalized_query: str) -> str:
        """Extract a pattern from the normalized query."""
        # Split into words
        words = normalized_query.split()
        
        # Remove stop words but keep important domain terms
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'i', 'me', 'my', 'you', 'your'
        }
        
        # Keep domain-specific words even if they're normally stop words
        domain_words = {
            'what', 'how', 'when', 'where', 'why', 'who', 'can', 'do', 'need'
        }
        
        pattern_words = []
        for word in words:
            if word not in stop_words or word in domain_words or len(word) > 3:
                pattern_words.append(word)
        
        # Create pattern (first 5 significant words)
        pattern = ' '.join(pattern_words[:5])
        
        # If pattern is too short, use more words
        if len(pattern.split()) < 2 and len(words) > 1:
            pattern = ' '.join(words[:3])
        
        return pattern or normalized_query
    
    def _update_pattern_metrics(self, pattern: str, query_record: Dict[str, Any]):
        """Update metrics for a query pattern."""
        if pattern not in self.pattern_metrics:
            self.pattern_metrics[pattern] = QueryMetrics(query_pattern=pattern)
        
        metrics = self.pattern_metrics[pattern]
        metrics.total_searches += 1
        metrics.last_updated = time.time()
        
        if query_record['success']:
            metrics.successful_searches += 1
        else:
            metrics.failed_searches += 1
        
        # Update averages
        total = metrics.total_searches
        metrics.avg_response_time_ms = (
            (metrics.avg_response_time_ms * (total - 1) + query_record['response_time_ms']) / total
        )
        
        if query_record['confidence_score'] > 0:
            metrics.avg_confidence_score = (
                (metrics.avg_confidence_score * (total - 1) + query_record['confidence_score']) / total
            )
        
        # Update cache hit rate
        cache_hits = sum(1 for q in self.query_history 
                        if q['pattern'] == pattern and q['cache_hit'])
        pattern_queries = sum(1 for q in self.query_history if q['pattern'] == pattern)
        metrics.cache_hit_rate = cache_hits / pattern_queries if pattern_queries > 0 else 0.0
        
        # Update common variations
        variations = set(metrics.common_variations)
        variations.add(query_record['normalized_query'])
        metrics.common_variations = list(variations)[:10]  # Keep top 10
    
    def _analyze_pattern_performance(self, queries: List[Dict[str, Any]]) -> Dict[str, QueryMetrics]:
        """Analyze performance of query patterns."""
        pattern_stats = defaultdict(lambda: {
            'total': 0, 'successful': 0, 'response_times': [],
            'confidence_scores': [], 'variations': set()
        })
        
        for query in queries:
            pattern = query['pattern']
            stats = pattern_stats[pattern]
            
            stats['total'] += 1
            if query['success']:
                stats['successful'] += 1
            
            stats['response_times'].append(query['response_time_ms'])
            if query['confidence_score'] > 0:
                stats['confidence_scores'].append(query['confidence_score'])
            stats['variations'].add(query['normalized_query'])
        
        # Convert to QueryMetrics
        result = {}
        for pattern, stats in pattern_stats.items():
            if stats['total'] >= self.min_pattern_frequency:
                metrics = QueryMetrics(
                    query_pattern=pattern,
                    total_searches=stats['total'],
                    successful_searches=stats['successful'],
                    failed_searches=stats['total'] - stats['successful'],
                    avg_response_time_ms=sum(stats['response_times']) / len(stats['response_times']),
                    avg_confidence_score=sum(stats['confidence_scores']) / len(stats['confidence_scores']) if stats['confidence_scores'] else 0.0,
                    common_variations=list(stats['variations'])[:10]
                )
                
                # Calculate improvement potential
                success_rate = stats['successful'] / stats['total']
                metrics.improvement_potential = max(0, 1 - success_rate)
                
                result[pattern] = metrics
        
        return result
    
    def _identify_failing_patterns(self, pattern_analysis: Dict[str, QueryMetrics]) -> List[QueryMetrics]:
        """Identify patterns that are failing frequently."""
        failing_patterns = []
        
        for metrics in pattern_analysis.values():
            failure_rate = metrics.failed_searches / metrics.total_searches
            
            # Identify as failing if:
            # 1. High failure rate
            # 2. Low confidence scores
            # 3. Slow response times
            
            is_failing = (
                failure_rate > self.failure_threshold or
                metrics.avg_confidence_score < self.low_confidence_threshold or
                metrics.avg_response_time_ms > self.slow_response_threshold
            )
            
            if is_failing:
                failing_patterns.append(metrics)
        
        # Sort by improvement potential
        failing_patterns.sort(key=lambda x: x.improvement_potential, reverse=True)
        return failing_patterns
    
    def _generate_optimization_recommendations(self, failing_patterns: List[QueryMetrics],
                                             recent_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations."""
        recommendations = []
        
        for pattern_metrics in failing_patterns[:5]:  # Top 5 failing patterns
            pattern = pattern_metrics.query_pattern
            failure_rate = pattern_metrics.failed_searches / pattern_metrics.total_searches
            
            recommendation = {
                'pattern': pattern,
                'priority': 'high' if failure_rate > 0.5 else 'medium',
                'failure_rate': failure_rate,
                'total_searches': pattern_metrics.total_searches,
                'issues': [],
                'solutions': []
            }
            
            # Identify specific issues and solutions
            if failure_rate > self.failure_threshold:
                recommendation['issues'].append('High failure rate')
                recommendation['solutions'].extend([
                    'Add more comprehensive knowledge entries for this topic',
                    'Improve search keyword matching',
                    'Add synonyms and variations to search index'
                ])
            
            if pattern_metrics.avg_confidence_score < self.low_confidence_threshold:
                recommendation['issues'].append('Low confidence scores')
                recommendation['solutions'].extend([
                    'Improve answer quality and specificity',
                    'Add more detailed information to knowledge base',
                    'Enhance semantic matching algorithms'
                ])
            
            if pattern_metrics.avg_response_time_ms > self.slow_response_threshold:
                recommendation['issues'].append('Slow response times')
                recommendation['solutions'].extend([
                    'Optimize database queries for this pattern',
                    'Add caching for common variations',
                    'Improve indexing strategy'
                ])
            
            # Check for missing synonyms
            missing_synonyms = self._identify_missing_synonyms(pattern)
            if missing_synonyms:
                recommendation['solutions'].append(
                    f'Add synonyms: {", ".join(missing_synonyms)}'
                )
            
            recommendations.append(recommendation)
        
        # Add general performance recommendations
        if recent_queries:
            avg_response_time = sum(q['response_time_ms'] for q in recent_queries) / len(recent_queries)
            cache_hit_rate = sum(1 for q in recent_queries if q['cache_hit']) / len(recent_queries)
            
            if avg_response_time > 100:
                recommendations.append({
                    'pattern': 'SYSTEM_PERFORMANCE',
                    'priority': 'high',
                    'issues': ['Overall slow response times'],
                    'solutions': [
                        'Implement more aggressive caching',
                        'Optimize database indexes',
                        'Consider response preprocessing'
                    ]
                })
            
            if cache_hit_rate < 0.3:
                recommendations.append({
                    'pattern': 'CACHE_PERFORMANCE',
                    'priority': 'medium',
                    'issues': ['Low cache hit rate'],
                    'solutions': [
                        'Improve query normalization',
                        'Expand cache warming strategies',
                        'Increase cache size limits'
                    ]
                })
        
        return recommendations
    
    def _generate_synonym_suggestions(self, failing_patterns: List[QueryMetrics]) -> Dict[str, List[str]]:
        """Generate synonym suggestions for failing patterns."""
        suggestions = {}
        
        for metrics in failing_patterns:
            pattern_words = metrics.query_pattern.split()
            pattern_synonyms = []
            
            for word in pattern_words:
                if word in self.synonyms_database:
                    pattern_synonyms.extend(self.synonyms_database[word][:3])  # Top 3 synonyms
            
            if pattern_synonyms:
                suggestions[metrics.query_pattern] = list(set(pattern_synonyms))
        
        return suggestions
    
    def _suggest_search_term_improvements(self, failing_patterns: List[QueryMetrics]) -> Dict[str, str]:
        """Suggest improved search terms for failing patterns."""
        improvements = {}
        
        for metrics in failing_patterns:
            pattern = metrics.query_pattern
            
            # Suggest improvements based on common successful variations
            variations = metrics.common_variations
            if variations and len(variations) > 1:
                # Find the most successful variation
                # This would require tracking success per variation
                # For now, suggest the most complete variation
                longest_variation = max(variations, key=len)
                if len(longest_variation) > len(pattern):
                    improvements[pattern] = longest_variation
            
            # Suggest adding state information if missing
            if not any(state in pattern.lower() for state in ['georgia', 'california', 'texas', 'florida']):
                if 'license' in pattern or 'contractor' in pattern:
                    improvements[pattern] = f"{pattern} in [your state]"
        
        return improvements
    
    def _analyze_performance_patterns(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze performance patterns across all queries."""
        if not queries:
            return {}
        
        # Time-based analysis
        query_times = sorted([(q['timestamp'], q['response_time_ms'], q['success']) for q in queries])
        
        # Success rate over time
        hourly_success = defaultdict(list)
        for timestamp, response_time, success in query_times:
            hour = int(timestamp // 3600)
            hourly_success[hour].append(success)
        
        # Performance trends
        performance_trends = []
        for hour in sorted(hourly_success.keys()):
            successes = hourly_success[hour]
            success_rate = sum(successes) / len(successes)
            performance_trends.append({'hour': hour, 'success_rate': success_rate})
        
        # Response time analysis
        response_times = [q['response_time_ms'] for q in queries if q['success']]
        cache_hits = [q for q in queries if q['cache_hit']]
        cache_misses = [q for q in queries if not q['cache_hit']]
        
        insights = {
            'total_queries': len(queries),
            'overall_success_rate': sum(1 for q in queries if q['success']) / len(queries),
            'avg_response_time_ms': sum(response_times) / len(response_times) if response_times else 0,
            'cache_hit_rate': len(cache_hits) / len(queries),
            'avg_cache_hit_time_ms': sum(q['response_time_ms'] for q in cache_hits) / len(cache_hits) if cache_hits else 0,
            'avg_cache_miss_time_ms': sum(q['response_time_ms'] for q in cache_misses) / len(cache_misses) if cache_misses else 0,
            'performance_trends': performance_trends,
            'peak_hours': self._identify_peak_hours(queries),
            'slowest_patterns': self._identify_slowest_patterns(queries)
        }
        
        return insights
    
    def _identify_peak_hours(self, queries: List[Dict[str, Any]]) -> List[int]:
        """Identify peak usage hours."""
        hourly_counts = defaultdict(int)
        for query in queries:
            hour = datetime.fromtimestamp(query['timestamp']).hour
            hourly_counts[hour] += 1
        
        if not hourly_counts:
            return []
        
        avg_hourly = sum(hourly_counts.values()) / len(hourly_counts)
        peak_threshold = avg_hourly * 1.5
        
        return [hour for hour, count in hourly_counts.items() if count > peak_threshold]
    
    def _identify_slowest_patterns(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify the slowest query patterns."""
        pattern_times = defaultdict(list)
        for query in queries:
            if query['success']:
                pattern_times[query['pattern']].append(query['response_time_ms'])
        
        slowest = []
        for pattern, times in pattern_times.items():
            if len(times) >= 3:  # Only patterns with enough data
                avg_time = sum(times) / len(times)
                slowest.append({
                    'pattern': pattern,
                    'avg_response_time_ms': avg_time,
                    'query_count': len(times)
                })
        
        slowest.sort(key=lambda x: x['avg_response_time_ms'], reverse=True)
        return slowest[:5]
    
    def _identify_missing_synonyms(self, pattern: str) -> List[str]:
        """Identify missing synonyms for a pattern."""
        pattern_words = pattern.lower().split()
        missing_synonyms = []
        
        for word in pattern_words:
            if word in self.synonyms_database:
                # Check if synonyms are already in use
                synonyms = self.synonyms_database[word]
                for synonym in synonyms[:3]:  # Check top 3 synonyms
                    if synonym not in pattern and synonym not in missing_synonyms:
                        missing_synonyms.append(synonym)
        
        return missing_synonyms[:5]  # Return top 5 missing synonyms
    
    def _load_contractor_synonyms(self) -> Dict[str, List[str]]:
        """Load contractor-specific synonyms database."""
        return {
            'license': ['permit', 'certification', 'credential', 'authorization'],
            'contractor': ['builder', 'construction professional', 'tradesperson', 'tradesman'],
            'requirements': ['prerequisites', 'qualifications', 'criteria', 'conditions'],
            'cost': ['fee', 'price', 'expense', 'charge', 'payment'],
            'test': ['exam', 'examination', 'assessment', 'evaluation'],
            'get': ['obtain', 'acquire', 'secure', 'receive', 'apply for'],
            'need': ['require', 'must have', 'necessary', 'essential'],
            'help': ['assistance', 'guidance', 'support', 'aid'],
            'state': ['location', 'jurisdiction', 'region'],
            'experience': ['background', 'work history', 'years'],
            'application': ['form', 'paperwork', 'submission'],
            'bond': ['surety', 'insurance', 'guarantee'],
            'insurance': ['coverage', 'protection', 'policy'],
            'business': ['company', 'operation', 'enterprise'],
            'work': ['job', 'project', 'construction'],
            'general': ['main', 'primary', 'principal'],
            'specialty': ['specialized', 'specific', 'trade-specific'],
            'residential': ['home', 'house', 'domestic'],
            'commercial': ['business', 'industrial', 'corporate']
        }
    
    def _load_state_mappings(self) -> Dict[str, str]:
        """Load state name to abbreviation mappings."""
        return {
            'georgia': 'GA', 'california': 'CA', 'florida': 'FL',
            'texas': 'TX', 'new york': 'NY', 'nevada': 'NV',
            'arizona': 'AZ', 'utah': 'UT', 'oregon': 'OR',
            'washington': 'WA', 'colorado': 'CO', 'illinois': 'IL',
            'north carolina': 'NC', 'south carolina': 'SC',
            'virginia': 'VA', 'maryland': 'MD', 'pennsylvania': 'PA'
        }
    
    def export_analysis(self, result: QueryAnalysisResult, 
                       filepath: Optional[str] = None) -> str:
        """Export analysis results to JSON file."""
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"optimization/query_analysis_{timestamp}.json"
        
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to serializable format
            export_data = {
                'analysis_timestamp': result.timestamp,
                'total_queries_analyzed': result.total_queries_analyzed,
                'unique_patterns_found': result.unique_patterns_found,
                'top_failing_patterns': [asdict(pattern) for pattern in result.top_failing_patterns],
                'optimization_recommendations': result.optimization_recommendations,
                'synonym_suggestions': result.synonym_suggestions,
                'search_term_improvements': result.search_term_improvements,
                'performance_insights': result.performance_insights
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info("Query analysis exported", filepath=filepath)
            return filepath
        
        except Exception as e:
            logger.error("Failed to export analysis", filepath=filepath, error=str(e))
            raise


def create_sample_query_history():
    """Create sample query history for testing."""
    analyzer = QueryPatternAnalyzer()
    
    # Sample queries with varying success rates
    sample_queries = [
        ("georgia contractor license requirements", True, 45.2, 0.9),
        ("ga license reqs", False, 120.5, 0.3),
        ("how to get contractor license in georgia", True, 67.8, 0.8),
        ("contractor permit georgia", True, 52.1, 0.85),
        ("general contractor license ga", True, 41.3, 0.92),
        ("georgia gc license", False, 134.7, 0.4),
        ("surety bond requirements", True, 76.4, 0.75),
        ("how do i get a bond", False, 145.2, 0.25),
        ("bonding company georgia", True, 58.9, 0.8),
        ("psi exam information", True, 63.2, 0.88),
        ("contractor exam schedule", False, 167.3, 0.35),
        ("what is psi test", True, 44.7, 0.9),
        ("failed contractor exam", True, 72.1, 0.82),
        ("retake exam policy", False, 198.4, 0.2),
        ("exam prep courses", True, 55.6, 0.86)
    ]
    
    # Record queries
    for query, success, response_time, confidence in sample_queries:
        analyzer.record_query(query, success, response_time, confidence)
    
    return analyzer


if __name__ == "__main__":
    # Test the analyzer
    analyzer = create_sample_query_history()
    result = analyzer.analyze_patterns(time_window_hours=24)
    
    print(f"Analyzed {result.total_queries_analyzed} queries")
    print(f"Found {result.unique_patterns_found} unique patterns")
    print(f"Top failing patterns: {len(result.top_failing_patterns)}")
    
    for i, pattern in enumerate(result.top_failing_patterns[:3]):
        print(f"{i+1}. {pattern.query_pattern} (failure rate: {pattern.failed_searches/pattern.total_searches:.1%})")
    
    # Export results
    analyzer.export_analysis(result)
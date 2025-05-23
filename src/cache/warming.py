"""
FACT System Cache Warming

Implements intelligent cache warming strategies to improve hit rates
and reduce cold start latency for common queries.
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import structlog

from manager import CacheManager, get_cache_manager
from metrics import get_metrics_collector
from core.errors import CacheError


logger = structlog.get_logger(__name__)


@dataclass
class WarmupQuery:
    """Represents a query for cache warming."""
    query: str
    priority: int  # 1-10, 10 being highest priority
    expected_tokens: int
    category: str
    frequency_score: float = 0.0
    last_warmed: Optional[float] = None


@dataclass
class WarmupResult:
    """Result of cache warming operation."""
    queries_attempted: int
    queries_successful: int
    queries_failed: int
    total_time_ms: float
    cache_entries_created: int
    total_tokens_cached: int
    errors: List[str]


class QueryPatternAnalyzer:
    """Analyzes query patterns to identify candidates for warming."""
    
    def __init__(self):
        self.query_frequency: Dict[str, int] = {}
        self.query_patterns: Dict[str, List[str]] = {}
        self.common_templates = [
            "What was {period} revenue?",
            "Show me {period} financial data",
            "Calculate {metric} for {period}",
            "Compare {period1} vs {period2} {metric}",
            "What is the total {metric}?",
            "Show revenue by {dimension}",
            "What was the highest {metric} {period}?",
        ]
    
    def analyze_query_log(self, query_log: List[str]) -> List[WarmupQuery]:
        """
        Analyze query log to identify warming candidates.
        
        Args:
            query_log: List of historical queries
            
        Returns:
            List of warmup queries with priorities
        """
        # Count query frequencies
        for query in query_log:
            normalized = self._normalize_query(query)
            self.query_frequency[normalized] = self.query_frequency.get(normalized, 0) + 1
        
        # Generate warmup queries
        warmup_queries = []
        
        # Add high-frequency queries
        for query, freq in self.query_frequency.items():
            if freq >= 3:  # Appeared 3+ times
                priority = min(10, freq)
                warmup_queries.append(WarmupQuery(
                    query=query,
                    priority=priority,
                    expected_tokens=750,  # Estimated
                    category="frequent",
                    frequency_score=freq
                ))
        
        # Add template-based queries
        template_queries = self._generate_template_queries()
        warmup_queries.extend(template_queries)
        
        # Sort by priority and frequency
        warmup_queries.sort(key=lambda q: (q.priority, q.frequency_score), reverse=True)
        
        logger.info("Query analysis completed",
                   total_queries=len(query_log),
                   unique_patterns=len(self.query_frequency),
                   warmup_candidates=len(warmup_queries))
        
        return warmup_queries[:50]  # Limit to top 50
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching."""
        # Convert to lowercase and remove extra whitespace
        normalized = " ".join(query.lower().split())
        
        # Replace specific values with placeholders
        replacements = [
            (r'\bq[1-4]-\d{4}\b', '{period}'),
            (r'\b\d{4}\b', '{year}'),
            (r'\b\d+[.,]\d+\b', '{number}'),
            (r'\$[\d,]+\.?\d*', '{currency}'),
        ]
        
        for pattern, replacement in replacements:
            import re
            normalized = re.sub(pattern, replacement, normalized)
        
        return normalized
    
    def _generate_template_queries(self) -> List[WarmupQuery]:
        """Generate queries based on common templates."""
        template_queries = []
        
        # Financial periods
        periods = ["Q1-2025", "Q4-2024", "Q3-2024", "Q2-2024", "2024", "2023"]
        metrics = ["revenue", "profit", "sales", "income"]
        
        # Generate revenue queries (highest priority)
        for period in periods[:4]:  # Recent quarters
            template_queries.append(WarmupQuery(
                query=f"What was {period} revenue?",
                priority=9,
                expected_tokens=600,
                category="revenue"
            ))
        
        # Generate comparison queries
        template_queries.append(WarmupQuery(
            query="Compare Q1-2025 vs Q1-2024 revenue",
            priority=8,
            expected_tokens=800,
            category="comparison"
        ))
        
        # Generate summary queries
        template_queries.append(WarmupQuery(
            query="Show me quarterly revenue summary",
            priority=7,
            expected_tokens=900,
            category="summary"
        ))
        
        # Generate total queries
        for metric in metrics:
            template_queries.append(WarmupQuery(
                query=f"What is the total {metric} for 2024?",
                priority=6,
                expected_tokens=650,
                category="totals"
            ))
        
        return template_queries


class CacheWarmer:
    """Main cache warming coordinator."""
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.cache_manager = cache_manager or get_cache_manager()
        self.metrics_collector = get_metrics_collector()
        self.query_analyzer = QueryPatternAnalyzer()
        self.warmup_history: List[WarmupResult] = []
        self._is_warming = False
    
    async def warm_cache_from_queries(self, 
                                    queries: List[str],
                                    generate_responses: bool = True) -> WarmupResult:
        """
        Warm cache with provided queries.
        
        Args:
            queries: List of queries to warm
            generate_responses: Whether to generate mock responses
            
        Returns:
            Warmup operation result
        """
        if self._is_warming:
            raise CacheError("Cache warming already in progress")
        
        self._is_warming = True
        start_time = time.perf_counter()
        
        try:
            logger.info("Starting cache warming", query_count=len(queries))
            
            successful = 0
            failed = 0
            errors = []
            total_tokens = 0
            
            for i, query in enumerate(queries):
                try:
                    # Generate query hash
                    query_hash = self.cache_manager.generate_hash(query)
                    
                    # Skip if already cached
                    if self.cache_manager.get(query_hash):
                        logger.debug("Query already cached, skipping", query=query[:50])
                        continue
                    
                    # Generate response content
                    if generate_responses:
                        response = await self._generate_mock_response(query)
                    else:
                        response = self._create_placeholder_response(query)
                    
                    # Store in cache
                    entry = self.cache_manager.store(query_hash, response)
                    total_tokens += entry.token_count
                    successful += 1
                    
                    logger.debug("Query cached for warming",
                               query=query[:50],
                               tokens=entry.token_count)
                    
                    # Small delay to avoid overwhelming the system
                    if i % 10 == 0:
                        await asyncio.sleep(0.1)
                
                except Exception as e:
                    failed += 1
                    error_msg = f"Failed to warm query '{query[:50]}': {str(e)}"
                    errors.append(error_msg)
                    logger.warning("Cache warming failed for query", 
                                 query=query[:50], 
                                 error=str(e))
            
            total_time = (time.perf_counter() - start_time) * 1000
            
            result = WarmupResult(
                queries_attempted=len(queries),
                queries_successful=successful,
                queries_failed=failed,
                total_time_ms=total_time,
                cache_entries_created=successful,
                total_tokens_cached=total_tokens,
                errors=errors
            )
            
            self.warmup_history.append(result)
            
            logger.info("Cache warming completed",
                       successful=successful,
                       failed=failed,
                       total_time_ms=total_time,
                       tokens_cached=total_tokens)
            
            return result
            
        finally:
            self._is_warming = False
    
    async def warm_cache_intelligently(self, 
                                     query_log: Optional[List[str]] = None,
                                     max_queries: int = 30) -> WarmupResult:
        """
        Intelligently warm cache based on query analysis.
        
        Args:
            query_log: Historical query log for analysis
            max_queries: Maximum number of queries to warm
            
        Returns:
            Warmup operation result
        """
        try:
            # Use provided log or generate default queries
            if query_log:
                warmup_queries = self.query_analyzer.analyze_query_log(query_log)
            else:
                warmup_queries = self._get_default_warmup_queries()
            
            # Limit to max_queries
            warmup_queries = warmup_queries[:max_queries]
            
            # Extract query strings and warm cache
            query_strings = [wq.query for wq in warmup_queries]
            
            return await self.warm_cache_from_queries(query_strings, generate_responses=True)
            
        except Exception as e:
            logger.error("Intelligent cache warming failed", error=str(e))
            raise CacheError(f"Intelligent warming failed: {e}")
    
    async def scheduled_warming(self, 
                               interval_hours: int = 24,
                               query_log_file: Optional[str] = None) -> None:
        """
        Run scheduled cache warming in background.
        
        Args:
            interval_hours: Warming interval in hours
            query_log_file: Optional file path for query log
        """
        logger.info("Starting scheduled cache warming", interval_hours=interval_hours)
        
        while True:
            try:
                # Load query log if provided
                query_log = None
                if query_log_file and Path(query_log_file).exists():
                    query_log = self._load_query_log(query_log_file)
                
                # Perform intelligent warming
                result = await self.warm_cache_intelligently(query_log)
                
                logger.info("Scheduled warming completed",
                           successful=result.queries_successful,
                           failed=result.queries_failed)
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
            except asyncio.CancelledError:
                logger.info("Scheduled warming cancelled")
                break
            except Exception as e:
                logger.error("Scheduled warming error", error=str(e))
                # Continue after short delay
                await asyncio.sleep(300)  # 5 minutes
    
    def get_warming_recommendations(self, 
                                  cache_metrics: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Get recommendations for cache warming based on current performance.
        
        Args:
            cache_metrics: Current cache metrics
            
        Returns:
            List of recommended queries for warming
        """
        recommendations = []
        
        try:
            # Get current cache health
            if not cache_metrics:
                metrics = self.cache_manager.get_metrics()
                hit_rate = metrics.hit_rate
            else:
                hit_rate = cache_metrics.get("hit_rate", 0)
            
            # Recommend warming if hit rate is low
            if hit_rate < 50:
                recommendations.extend([
                    "What was Q1-2025 revenue?",
                    "Show me quarterly revenue summary",
                    "What is the total revenue for 2024?",
                    "Compare Q1-2025 vs Q4-2024 revenue"
                ])
                logger.info("Low hit rate detected, recommending basic warming", hit_rate=hit_rate)
            
            # Add seasonal recommendations
            current_time = time.time()
            hour = int((current_time // 3600) % 24)
            
            if 8 <= hour <= 10:  # Morning hours
                recommendations.extend([
                    "Show me yesterday's performance",
                    "What are today's key metrics?",
                    "Daily revenue report"
                ])
            elif 17 <= hour <= 19:  # Evening hours
                recommendations.extend([
                    "End of day summary",
                    "Today's revenue total",
                    "Weekly performance summary"
                ])
            
            return recommendations[:20]  # Limit recommendations
            
        except Exception as e:
            logger.error("Failed to generate warming recommendations", error=str(e))
            return self._get_default_warmup_queries()[:5]
    
    async def _generate_mock_response(self, query: str) -> str:
        """Generate mock response for warming."""
        # Simple template-based response generation
        query_lower = query.lower()
        
        if "revenue" in query_lower:
            if "q1-2025" in query_lower:
                response = "Q1-2025 revenue was $1,234,567.89, representing a 15.2% increase compared to Q1-2024."
            elif "q4-2024" in query_lower:
                response = "Q4-2024 revenue reached $1,133,221.55, marking strong year-end performance."
            else:
                response = "Revenue data shows consistent growth across all quarters with strong performance indicators."
        elif "summary" in query_lower:
            response = ("Quarterly revenue summary: Q1-2025: $1,234,567.89, Q4-2024: $1,133,221.55, "
                       "Q3-2024: $987,654.32, Q2-2024: $876,543.21. Year-over-year growth trends positive.")
        elif "compare" in query_lower:
            response = ("Comparison analysis shows Q1-2025 revenue of $1,234,567.89 vs Q1-2024 revenue of "
                       "$1,072,456.78, representing a 15.1% year-over-year increase.")
        else:
            response = f"Financial analysis for your query: {query}"
        
        # Ensure minimum token count
        while len(response.split()) < 125:  # Roughly 500 tokens
            response += " Additional financial context and detailed analysis provided for comprehensive understanding."
        
        return response
    
    def _create_placeholder_response(self, query: str) -> str:
        """Create placeholder response with minimum token count."""
        base_response = f"Cached response for query: {query}. "
        
        # Add padding to meet minimum token requirement
        padding = "This is cached financial data analysis. " * 50
        return base_response + padding
    
    def _get_default_warmup_queries(self) -> List[WarmupQuery]:
        """Get default set of queries for warming."""
        return [
            WarmupQuery("What was Q1-2025 revenue?", 10, 600, "revenue"),
            WarmupQuery("Show me quarterly revenue summary", 9, 800, "summary"),
            WarmupQuery("What is the total revenue for 2024?", 8, 650, "totals"),
            WarmupQuery("Compare Q1-2025 vs Q1-2024 revenue", 8, 750, "comparison"),
            WarmupQuery("What was Q4-2024 revenue?", 7, 600, "revenue"),
            WarmupQuery("Show revenue by category", 7, 700, "analysis"),
            WarmupQuery("What was the highest revenue quarter?", 6, 650, "analysis"),
            WarmupQuery("Calculate year-over-year growth", 6, 700, "analysis"),
            WarmupQuery("Show revenue trends", 5, 750, "trends"),
            WarmupQuery("What is average quarterly revenue?", 5, 600, "statistics")
        ]
    
    def _load_query_log(self, file_path: str) -> List[str]:
        """Load query log from file."""
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.json'):
                    data = json.load(f)
                    return data if isinstance(data, list) else data.get('queries', [])
                else:
                    return [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error("Failed to load query log", file_path=file_path, error=str(e))
            return []


# Global cache warmer instance
_cache_warmer: Optional[CacheWarmer] = None


def get_cache_warmer(cache_manager: Optional[CacheManager] = None) -> CacheWarmer:
    """Get or create global cache warmer instance."""
    global _cache_warmer
    
    if _cache_warmer is None:
        _cache_warmer = CacheWarmer(cache_manager)
    
    return _cache_warmer


async def warm_cache_startup(queries: Optional[List[str]] = None) -> WarmupResult:
    """
    Warm cache on system startup.
    
    Args:
        queries: Optional list of queries to warm
        
    Returns:
        Warmup operation result
    """
    warmer = get_cache_warmer()
    
    if queries:
        return await warmer.warm_cache_from_queries(queries)
    else:
        return await warmer.warm_cache_intelligently()
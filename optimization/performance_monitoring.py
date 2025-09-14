"""
Advanced Performance Monitoring System for FACT

Real-time monitoring, alerting, and optimization recommendations
for query performance, cache efficiency, and system health.
"""

import time
import asyncio
import json
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from datetime import datetime, timedelta
import structlog
from pathlib import Path
import statistics

logger = structlog.get_logger(__name__)


@dataclass
class PerformanceAlert:
    """Performance alert with severity and action recommendations."""
    alert_id: str
    severity: str  # 'info', 'warning', 'critical'
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    recommendations: List[str]
    timestamp: float = field(default_factory=time.time)
    resolved: bool = False


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics snapshot."""
    timestamp: float
    
    # Query Performance
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    avg_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    
    # Cache Performance
    cache_hit_rate: float = 0.0
    cache_miss_rate: float = 0.0
    avg_cache_hit_time_ms: float = 0.0
    avg_cache_miss_time_ms: float = 0.0
    cache_size_mb: float = 0.0
    cache_utilization_percent: float = 0.0
    
    # Search Performance
    search_accuracy_rate: float = 0.0
    avg_confidence_score: float = 0.0
    low_confidence_queries: int = 0
    zero_result_queries: int = 0
    
    # System Health
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    error_rate: float = 0.0
    uptime_hours: float = 0.0
    
    # Quality Metrics
    user_satisfaction_score: float = 0.0
    query_resolution_rate: float = 0.0
    escalation_rate: float = 0.0


@dataclass
class OptimizationRecommendation:
    """System optimization recommendation."""
    recommendation_id: str
    category: str  # 'cache', 'search', 'database', 'system'
    priority: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    expected_improvement: str
    implementation_effort: str  # 'low', 'medium', 'high'
    estimated_impact: Dict[str, float]  # metric -> improvement percentage
    action_items: List[str]
    timestamp: float = field(default_factory=time.time)


class PerformanceMonitor:
    """
    Real-time performance monitoring system with alerting and optimization.
    
    Tracks query performance, cache efficiency, search accuracy, and system health
    with automatic alerting and optimization recommendations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize performance monitoring system."""
        self.config = config or self._get_default_config()
        
        # Metrics storage
        self.current_metrics = PerformanceMetrics(timestamp=time.time())
        self.metrics_history: deque = deque(maxlen=1440)  # 24 hours at 1-minute intervals
        self.query_buffer: deque = deque(maxlen=1000)  # Recent queries for analysis
        
        # Alerting system
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_callbacks: List[Callable] = []
        self.alert_thresholds = self.config.get('alert_thresholds', {})
        
        # Optimization tracking
        self.optimization_history: List[OptimizationRecommendation] = []
        self.last_optimization_check = time.time()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Monitoring state
        self.monitoring_active = False
        self.start_time = time.time()
        
        logger.info("Performance monitor initialized", 
                   config_keys=list(self.config.keys()))
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous performance monitoring."""
        self.monitoring_active = True
        logger.info("Starting performance monitoring", interval_seconds=interval_seconds)
        
        # Start monitoring loop in background thread
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    self.collect_metrics()
                    self.check_alerts()
                    
                    # Check for optimization opportunities every 5 minutes
                    if time.time() - self.last_optimization_check > 300:
                        self.analyze_optimization_opportunities()
                        self.last_optimization_check = time.time()
                    
                    time.sleep(interval_seconds)
                    
                except Exception as e:
                    logger.error("Error in monitoring loop", error=str(e))
                    time.sleep(interval_seconds)
        
        monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring_active = False
        logger.info("Performance monitoring stopped")
    
    def record_query(self, query: str, response_time_ms: float, success: bool,
                    cache_hit: bool = False, confidence_score: float = 0.0,
                    result_count: int = 0, metadata: Optional[Dict[str, Any]] = None):
        """Record a query for performance analysis."""
        try:
            with self._lock:
                query_record = {
                    'timestamp': time.time(),
                    'query': query[:100],  # Truncate for privacy
                    'response_time_ms': response_time_ms,
                    'success': success,
                    'cache_hit': cache_hit,
                    'confidence_score': confidence_score,
                    'result_count': result_count,
                    'metadata': metadata or {}
                }
                
                self.query_buffer.append(query_record)
                
                # Update real-time counters
                self.current_metrics.total_queries += 1
                if success:
                    self.current_metrics.successful_queries += 1
                else:
                    self.current_metrics.failed_queries += 1
                
                if confidence_score < 0.6:
                    self.current_metrics.low_confidence_queries += 1
                
                if result_count == 0:
                    self.current_metrics.zero_result_queries += 1
                
                logger.debug("Query recorded for monitoring",
                           response_time_ms=response_time_ms,
                           success=success,
                           cache_hit=cache_hit)
        
        except Exception as e:
            logger.error("Failed to record query", error=str(e))
    
    def collect_metrics(self):
        """Collect comprehensive performance metrics."""
        try:
            with self._lock:
                current_time = time.time()
                
                # Calculate metrics from query buffer
                if self.query_buffer:
                    queries = list(self.query_buffer)
                    
                    # Response time metrics
                    response_times = [q['response_time_ms'] for q in queries if q['success']]
                    if response_times:
                        self.current_metrics.avg_response_time_ms = statistics.mean(response_times)
                        self.current_metrics.p95_response_time_ms = statistics.quantiles(
                            response_times, n=20)[18] if len(response_times) >= 20 else max(response_times)
                        self.current_metrics.p99_response_time_ms = statistics.quantiles(
                            response_times, n=100)[98] if len(response_times) >= 100 else max(response_times)
                    
                    # Cache metrics
                    total_queries = len(queries)
                    cache_hits = sum(1 for q in queries if q['cache_hit'])
                    cache_misses = total_queries - cache_hits
                    
                    self.current_metrics.cache_hit_rate = (cache_hits / total_queries) if total_queries > 0 else 0.0
                    self.current_metrics.cache_miss_rate = 1.0 - self.current_metrics.cache_hit_rate
                    
                    # Cache timing
                    hit_times = [q['response_time_ms'] for q in queries if q['cache_hit'] and q['success']]
                    miss_times = [q['response_time_ms'] for q in queries if not q['cache_hit'] and q['success']]
                    
                    self.current_metrics.avg_cache_hit_time_ms = statistics.mean(hit_times) if hit_times else 0.0
                    self.current_metrics.avg_cache_miss_time_ms = statistics.mean(miss_times) if miss_times else 0.0
                    
                    # Search accuracy
                    successful_queries = sum(1 for q in queries if q['success'])
                    self.current_metrics.search_accuracy_rate = (successful_queries / total_queries) if total_queries > 0 else 0.0
                    
                    # Confidence scores
                    confidence_scores = [q['confidence_score'] for q in queries if q['confidence_score'] > 0]
                    self.current_metrics.avg_confidence_score = statistics.mean(confidence_scores) if confidence_scores else 0.0
                    
                    # Error rate
                    failed_queries = sum(1 for q in queries if not q['success'])
                    self.current_metrics.error_rate = (failed_queries / total_queries) if total_queries > 0 else 0.0
                
                # System metrics
                self.current_metrics.uptime_hours = (current_time - self.start_time) / 3600
                self.current_metrics.timestamp = current_time
                
                # Store metrics history
                metrics_snapshot = PerformanceMetrics(**asdict(self.current_metrics))
                self.metrics_history.append(metrics_snapshot)
                
                logger.debug("Metrics collected",
                           avg_response_time=self.current_metrics.avg_response_time_ms,
                           cache_hit_rate=self.current_metrics.cache_hit_rate,
                           error_rate=self.current_metrics.error_rate)
        
        except Exception as e:
            logger.error("Failed to collect metrics", error=str(e))
    
    def check_alerts(self):
        """Check for performance alerts and trigger notifications."""
        try:
            metrics = self.current_metrics
            new_alerts = []
            
            # Response time alerts
            if metrics.avg_response_time_ms > self.alert_thresholds.get('avg_response_time_ms', 200):
                alert = PerformanceAlert(
                    alert_id="response_time_high",
                    severity="warning" if metrics.avg_response_time_ms < 300 else "critical",
                    metric_name="avg_response_time_ms",
                    current_value=metrics.avg_response_time_ms,
                    threshold_value=self.alert_thresholds.get('avg_response_time_ms', 200),
                    message=f"Average response time is {metrics.avg_response_time_ms:.1f}ms (threshold: {self.alert_thresholds.get('avg_response_time_ms', 200)}ms)",
                    recommendations=[
                        "Check cache hit rate and optimize caching strategy",
                        "Review database query performance",
                        "Consider scaling system resources",
                        "Analyze slow query patterns"
                    ]
                )
                new_alerts.append(alert)
            
            # Cache performance alerts
            if metrics.cache_hit_rate < self.alert_thresholds.get('cache_hit_rate', 0.5):
                alert = PerformanceAlert(
                    alert_id="cache_hit_rate_low",
                    severity="warning",
                    metric_name="cache_hit_rate",
                    current_value=metrics.cache_hit_rate,
                    threshold_value=self.alert_thresholds.get('cache_hit_rate', 0.5),
                    message=f"Cache hit rate is {metrics.cache_hit_rate:.1%} (threshold: {self.alert_thresholds.get('cache_hit_rate', 0.5):.1%})",
                    recommendations=[
                        "Improve query normalization for better cache matching",
                        "Expand cache warming with common queries",
                        "Increase cache size or adjust TTL settings",
                        "Analyze query patterns for optimization"
                    ]
                )
                new_alerts.append(alert)
            
            # Error rate alerts
            if metrics.error_rate > self.alert_thresholds.get('error_rate', 0.1):
                alert = PerformanceAlert(
                    alert_id="error_rate_high",
                    severity="critical",
                    metric_name="error_rate",
                    current_value=metrics.error_rate,
                    threshold_value=self.alert_thresholds.get('error_rate', 0.1),
                    message=f"Error rate is {metrics.error_rate:.1%} (threshold: {self.alert_thresholds.get('error_rate', 0.1):.1%})",
                    recommendations=[
                        "Review error logs for common failure patterns",
                        "Check database connectivity and health",
                        "Validate knowledge base data integrity",
                        "Consider fallback mechanisms"
                    ]
                )
                new_alerts.append(alert)
            
            # Search accuracy alerts
            if metrics.search_accuracy_rate < self.alert_thresholds.get('search_accuracy_rate', 0.8):
                alert = PerformanceAlert(
                    alert_id="search_accuracy_low",
                    severity="warning",
                    metric_name="search_accuracy_rate",
                    current_value=metrics.search_accuracy_rate,
                    threshold_value=self.alert_thresholds.get('search_accuracy_rate', 0.8),
                    message=f"Search accuracy is {metrics.search_accuracy_rate:.1%} (threshold: {self.alert_thresholds.get('search_accuracy_rate', 0.8):.1%})",
                    recommendations=[
                        "Review and expand knowledge base content",
                        "Improve search algorithm parameters",
                        "Add synonyms and alternative phrasings",
                        "Analyze failed query patterns"
                    ]
                )
                new_alerts.append(alert)
            
            # Update active alerts
            for alert in new_alerts:
                if alert.alert_id not in self.active_alerts:
                    self.active_alerts[alert.alert_id] = alert
                    self._trigger_alert_callbacks(alert)
                    logger.warning("Performance alert triggered",
                                 alert_id=alert.alert_id,
                                 severity=alert.severity,
                                 message=alert.message)
            
            # Check for resolved alerts
            resolved_alerts = []
            for alert_id, alert in self.active_alerts.items():
                if self._is_alert_resolved(alert, metrics):
                    alert.resolved = True
                    resolved_alerts.append(alert_id)
                    logger.info("Performance alert resolved", alert_id=alert_id)
            
            for alert_id in resolved_alerts:
                del self.active_alerts[alert_id]
        
        except Exception as e:
            logger.error("Failed to check alerts", error=str(e))
    
    def analyze_optimization_opportunities(self):
        """Analyze system performance and generate optimization recommendations."""
        try:
            if len(self.metrics_history) < 10:  # Need sufficient data
                return
            
            recommendations = []
            recent_metrics = list(self.metrics_history)[-10:]  # Last 10 metrics snapshots
            
            # Cache optimization analysis
            avg_cache_hit_rate = statistics.mean(m.cache_hit_rate for m in recent_metrics)
            if avg_cache_hit_rate < 0.6:
                rec = OptimizationRecommendation(
                    recommendation_id="cache_optimization_001",
                    category="cache",
                    priority="high",
                    title="Improve Cache Hit Rate",
                    description=f"Current cache hit rate is {avg_cache_hit_rate:.1%}, below optimal 60% threshold",
                    expected_improvement="15-25% reduction in response times",
                    implementation_effort="medium",
                    estimated_impact={
                        "avg_response_time_ms": -20.0,  # 20% reduction
                        "cache_hit_rate": 25.0,  # 25% improvement
                        "cost_savings": 30.0  # 30% cost reduction
                    },
                    action_items=[
                        "Implement query normalization improvements",
                        "Expand cache warming strategy",
                        "Optimize cache key generation",
                        "Increase cache size allocation"
                    ]
                )
                recommendations.append(rec)
            
            # Response time optimization
            avg_response_time = statistics.mean(m.avg_response_time_ms for m in recent_metrics)
            if avg_response_time > 150:
                rec = OptimizationRecommendation(
                    recommendation_id="response_time_001",
                    category="search",
                    priority="high" if avg_response_time > 200 else "medium",
                    title="Optimize Query Response Times",
                    description=f"Average response time is {avg_response_time:.1f}ms, above target of 150ms",
                    expected_improvement="30-40% faster query responses",
                    implementation_effort="medium",
                    estimated_impact={
                        "avg_response_time_ms": -35.0,
                        "p95_response_time_ms": -30.0,
                        "user_satisfaction": 15.0
                    },
                    action_items=[
                        "Add database indexes for common query patterns",
                        "Implement result caching for frequent searches",
                        "Optimize search algorithm parameters",
                        "Consider query result precomputation"
                    ]
                )
                recommendations.append(rec)
            
            # Search accuracy optimization
            avg_accuracy = statistics.mean(m.search_accuracy_rate for m in recent_metrics)
            if avg_accuracy < 0.85:
                rec = OptimizationRecommendation(
                    recommendation_id="accuracy_001",
                    category="search",
                    priority="medium",
                    title="Improve Search Accuracy",
                    description=f"Search accuracy is {avg_accuracy:.1%}, below target of 85%",
                    expected_improvement="10-15% improvement in successful queries",
                    implementation_effort="high",
                    estimated_impact={
                        "search_accuracy_rate": 12.0,
                        "avg_confidence_score": 8.0,
                        "user_satisfaction": 10.0
                    },
                    action_items=[
                        "Expand knowledge base with missing topics",
                        "Improve synonym matching algorithms",
                        "Add fuzzy search capabilities",
                        "Implement query suggestion system"
                    ]
                )
                recommendations.append(rec)
            
            # Store new recommendations
            for rec in recommendations:
                # Check if similar recommendation already exists
                existing = any(
                    r.category == rec.category and r.title == rec.title
                    for r in self.optimization_history[-5:]  # Check last 5 recommendations
                )
                if not existing:
                    self.optimization_history.append(rec)
                    logger.info("New optimization recommendation generated",
                               category=rec.category,
                               priority=rec.priority,
                               title=rec.title)
        
        except Exception as e:
            logger.error("Failed to analyze optimization opportunities", error=str(e))
    
    def get_performance_report(self, hours_back: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        try:
            cutoff_time = time.time() - (hours_back * 3600)
            recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {"error": "Insufficient data for report"}
            
            # Calculate trends
            first_half = recent_metrics[:len(recent_metrics)//2]
            second_half = recent_metrics[len(recent_metrics)//2:]
            
            def calculate_trend(metric_name):
                if not first_half or not second_half:
                    return 0.0
                
                first_avg = statistics.mean(getattr(m, metric_name) for m in first_half)
                second_avg = statistics.mean(getattr(m, metric_name) for m in second_half)
                
                if first_avg == 0:
                    return 0.0
                
                return ((second_avg - first_avg) / first_avg) * 100
            
            report = {
                "report_timestamp": time.time(),
                "time_period_hours": hours_back,
                "data_points": len(recent_metrics),
                
                "current_metrics": asdict(self.current_metrics),
                
                "performance_trends": {
                    "response_time_trend_percent": calculate_trend("avg_response_time_ms"),
                    "cache_hit_rate_trend_percent": calculate_trend("cache_hit_rate"),
                    "error_rate_trend_percent": calculate_trend("error_rate"),
                    "accuracy_trend_percent": calculate_trend("search_accuracy_rate")
                },
                
                "period_statistics": {
                    "avg_response_time_ms": statistics.mean(m.avg_response_time_ms for m in recent_metrics),
                    "min_response_time_ms": min(m.avg_response_time_ms for m in recent_metrics),
                    "max_response_time_ms": max(m.avg_response_time_ms for m in recent_metrics),
                    "avg_cache_hit_rate": statistics.mean(m.cache_hit_rate for m in recent_metrics),
                    "avg_error_rate": statistics.mean(m.error_rate for m in recent_metrics),
                    "total_queries": sum(m.total_queries for m in recent_metrics),
                    "total_successful_queries": sum(m.successful_queries for m in recent_metrics),
                    "total_failed_queries": sum(m.failed_queries for m in recent_metrics)
                },
                
                "active_alerts": [asdict(alert) for alert in self.active_alerts.values()],
                
                "recent_optimizations": [
                    asdict(rec) for rec in self.optimization_history[-5:]
                ],
                
                "performance_score": self._calculate_performance_score(recent_metrics),
                
                "recommendations": self._generate_immediate_recommendations()
            }
            
            return report
        
        except Exception as e:
            logger.error("Failed to generate performance report", error=str(e))
            return {"error": str(e)}
    
    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """Export metrics history to JSON file."""
        if not filepath:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"optimization/performance_metrics_{timestamp}.json"
        
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            
            export_data = {
                "export_timestamp": time.time(),
                "monitoring_start_time": self.start_time,
                "current_metrics": asdict(self.current_metrics),
                "metrics_history": [asdict(m) for m in self.metrics_history],
                "optimization_history": [asdict(r) for r in self.optimization_history],
                "active_alerts": [asdict(a) for a in self.active_alerts.values()],
                "configuration": self.config
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info("Performance metrics exported", filepath=filepath)
            return filepath
        
        except Exception as e:
            logger.error("Failed to export metrics", filepath=filepath, error=str(e))
            raise
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default monitoring configuration."""
        return {
            "alert_thresholds": {
                "avg_response_time_ms": 200,
                "p95_response_time_ms": 500,
                "cache_hit_rate": 0.5,
                "error_rate": 0.1,
                "search_accuracy_rate": 0.8,
                "avg_confidence_score": 0.7
            },
            "optimization_check_interval": 300,  # 5 minutes
            "metrics_retention_hours": 24,
            "alert_cooldown_minutes": 15
        }
    
    def _is_alert_resolved(self, alert: PerformanceAlert, metrics: PerformanceMetrics) -> bool:
        """Check if an alert condition has been resolved."""
        current_value = getattr(metrics, alert.metric_name, 0)
        
        # Add hysteresis to prevent alert flapping
        if alert.metric_name in ["avg_response_time_ms", "error_rate"]:
            # For metrics where lower is better
            return current_value < (alert.threshold_value * 0.9)
        else:
            # For metrics where higher is better
            return current_value > (alert.threshold_value * 1.1)
    
    def _trigger_alert_callbacks(self, alert: PerformanceAlert):
        """Trigger registered alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error("Alert callback failed", error=str(e))
    
    def _calculate_performance_score(self, metrics: List[PerformanceMetrics]) -> float:
        """Calculate overall performance score (0-100)."""
        if not metrics:
            return 0.0
        
        latest = metrics[-1]
        
        # Component scores (0-1)
        response_time_score = max(0, min(1, (300 - latest.avg_response_time_ms) / 200))
        cache_score = latest.cache_hit_rate
        accuracy_score = latest.search_accuracy_rate
        error_score = max(0, 1 - (latest.error_rate / 0.2))  # 20% error rate = 0 score
        
        # Weighted overall score
        overall_score = (
            response_time_score * 0.3 +
            cache_score * 0.25 +
            accuracy_score * 0.25 +
            error_score * 0.2
        ) * 100
        
        return round(overall_score, 1)
    
    def _generate_immediate_recommendations(self) -> List[str]:
        """Generate immediate actionable recommendations."""
        recommendations = []
        metrics = self.current_metrics
        
        if metrics.avg_response_time_ms > 150:
            recommendations.append("Consider implementing response caching for frequent queries")
        
        if metrics.cache_hit_rate < 0.6:
            recommendations.append("Optimize query normalization to improve cache hit rate")
        
        if metrics.error_rate > 0.05:
            recommendations.append("Investigate and resolve query processing errors")
        
        if metrics.search_accuracy_rate < 0.85:
            recommendations.append("Expand knowledge base content for better coverage")
        
        if metrics.avg_confidence_score < 0.7:
            recommendations.append("Review and improve answer quality in knowledge base")
        
        return recommendations
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add callback function for alert notifications."""
        self.alert_callbacks.append(callback)


# Example alert callback functions
def slack_alert_callback(alert: PerformanceAlert):
    """Example Slack alert notification."""
    logger.info("Slack alert would be sent",
               alert_id=alert.alert_id,
               severity=alert.severity,
               message=alert.message)


def email_alert_callback(alert: PerformanceAlert):
    """Example email alert notification."""
    logger.info("Email alert would be sent",
               alert_id=alert.alert_id,
               severity=alert.severity,
               message=alert.message)


def create_monitoring_dashboard():
    """Create a simple monitoring dashboard."""
    monitor = PerformanceMonitor()
    
    # Add alert callbacks
    monitor.add_alert_callback(slack_alert_callback)
    monitor.add_alert_callback(email_alert_callback)
    
    # Start monitoring
    monitor.start_monitoring(interval_seconds=30)
    
    return monitor


if __name__ == "__main__":
    # Test the monitoring system
    monitor = create_monitoring_dashboard()
    
    # Simulate some queries
    import random
    for i in range(100):
        response_time = random.uniform(50, 300)
        success = random.random() > 0.1
        cache_hit = random.random() > 0.4
        confidence = random.uniform(0.6, 0.95) if success else random.uniform(0.1, 0.5)
        
        monitor.record_query(
            query=f"test query {i}",
            response_time_ms=response_time,
            success=success,
            cache_hit=cache_hit,
            confidence_score=confidence,
            result_count=random.randint(0, 5) if success else 0
        )
    
    # Collect metrics and generate report
    monitor.collect_metrics()
    report = monitor.get_performance_report(hours_back=1)
    
    print("Performance Report:")
    print(f"Performance Score: {report['performance_score']}/100")
    print(f"Average Response Time: {report['current_metrics']['avg_response_time_ms']:.1f}ms")
    print(f"Cache Hit Rate: {report['current_metrics']['cache_hit_rate']:.1%}")
    print(f"Search Accuracy: {report['current_metrics']['search_accuracy_rate']:.1%}")
    
    # Export metrics
    filepath = monitor.export_metrics()
    print(f"Metrics exported to: {filepath}")
    
    # Stop monitoring
    monitor.stop_monitoring()
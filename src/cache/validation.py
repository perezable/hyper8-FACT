"""
FACT System Cache Validation

Implements cache validation mechanisms to ensure data integrity,
consistency, and performance compliance.
"""

import time
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import structlog

from .manager import CacheManager, CacheEntry
from ..core.errors import CacheError


logger = structlog.get_logger(__name__)


class ValidationLevel(Enum):
    """Cache validation levels."""
    BASIC = "basic"          # Basic integrity checks
    STANDARD = "standard"    # Standard validation
    COMPREHENSIVE = "comprehensive"  # Full validation suite


@dataclass
class ValidationResult:
    """Result of cache validation operation."""
    validation_level: str
    total_entries_checked: int
    valid_entries: int
    invalid_entries: int
    corrupted_entries: int
    expired_entries: int
    validation_time_ms: float
    issues_found: List[Dict[str, Any]]
    recommendations: List[str]
    overall_health: str  # "healthy", "warning", "critical"


@dataclass
class IntegrityIssue:
    """Represents a cache integrity issue."""
    entry_key: str
    issue_type: str
    severity: str  # "low", "medium", "high", "critical"
    description: str
    suggested_action: str


class CacheValidator:
    """Main cache validation engine."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.validation_history: List[ValidationResult] = []
        
        # Validation thresholds
        self.thresholds = {
            "max_corruption_rate": 0.05,  # 5% max corruption
            "max_expiry_rate": 0.20,      # 20% max expired entries
            "min_token_efficiency": 50.0,  # tokens per KB
            "max_entry_age_hours": 24.0,   # 24 hours max age
            "min_access_frequency": 0.1    # minimum access rate
        }
    
    async def validate_cache(self, level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
        """
        Perform cache validation based on specified level.
        
        Args:
            level: Validation level to perform
            
        Returns:
            Comprehensive validation result
        """
        start_time = time.perf_counter()
        
        try:
            logger.info("Starting cache validation", level=level.value)
            
            issues = []
            recommendations = []
            
            # Get all cache entries for validation
            with self.cache_manager._lock:
                entries = dict(self.cache_manager.cache)
            
            total_entries = len(entries)
            valid_count = 0
            invalid_count = 0
            corrupted_count = 0
            expired_count = 0
            
            # Perform validation based on level
            for entry_key, entry in entries.items():
                entry_issues = []
                
                # Basic validation (always performed)
                basic_issues = await self._validate_basic_integrity(entry_key, entry)
                entry_issues.extend(basic_issues)
                
                if level in [ValidationLevel.STANDARD, ValidationLevel.COMPREHENSIVE]:
                    # Standard validation
                    standard_issues = await self._validate_standard_compliance(entry_key, entry)
                    entry_issues.extend(standard_issues)
                
                if level == ValidationLevel.COMPREHENSIVE:
                    # Comprehensive validation
                    comprehensive_issues = await self._validate_comprehensive_analysis(entry_key, entry)
                    entry_issues.extend(comprehensive_issues)
                
                # Categorize entry status
                if not entry_issues:
                    valid_count += 1
                else:
                    has_corruption = any(issue.issue_type == "corruption" for issue in entry_issues)
                    has_expiry = any(issue.issue_type == "expired" for issue in entry_issues)
                    
                    if has_corruption:
                        corrupted_count += 1
                    elif has_expiry:
                        expired_count += 1
                    else:
                        invalid_count += 1
                
                issues.extend(entry_issues)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(issues, total_entries)
            
            # Determine overall health
            overall_health = self._determine_health_status(
                total_entries, valid_count, invalid_count, corrupted_count, expired_count
            )
            
            validation_time = (time.perf_counter() - start_time) * 1000
            
            result = ValidationResult(
                validation_level=level.value,
                total_entries_checked=total_entries,
                valid_entries=valid_count,
                invalid_entries=invalid_count,
                corrupted_entries=corrupted_count,
                expired_entries=expired_count,
                validation_time_ms=validation_time,
                issues_found=[issue.__dict__ for issue in issues],
                recommendations=recommendations,
                overall_health=overall_health
            )
            
            self.validation_history.append(result)
            
            logger.info("Cache validation completed",
                       level=level.value,
                       total_entries=total_entries,
                       valid_entries=valid_count,
                       issues_found=len(issues),
                       overall_health=overall_health)
            
            return result
            
        except Exception as e:
            logger.error("Cache validation failed", error=str(e))
            raise CacheError(f"Validation failed: {e}")
    
    async def _validate_basic_integrity(self, entry_key: str, entry: CacheEntry) -> List[IntegrityIssue]:
        """Perform basic integrity validation."""
        issues = []
        
        try:
            # Check for null/empty content
            if not entry.content:
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="corruption",
                    severity="critical",
                    description="Entry has null or empty content",
                    suggested_action="Remove corrupted entry"
                ))
            
            # Check prefix validity
            if not entry.prefix or entry.prefix != self.cache_manager.prefix:
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="invalid_prefix",
                    severity="high",
                    description=f"Invalid cache prefix: {entry.prefix}",
                    suggested_action="Update or remove entry with invalid prefix"
                ))
            
            # Check token count validity
            if entry.token_count < 500:
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="insufficient_tokens",
                    severity="medium",
                    description=f"Entry has {entry.token_count} tokens, minimum is 500",
                    suggested_action="Remove entry below minimum token threshold"
                ))
            
            # Check for corruption in token count
            actual_tokens = CacheEntry._count_tokens(entry.content)
            if abs(actual_tokens - entry.token_count) > entry.token_count * 0.1:  # 10% tolerance
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="corruption",
                    severity="medium",
                    description=f"Token count mismatch: stored={entry.token_count}, actual={actual_tokens}",
                    suggested_action="Recalculate and update token count"
                ))
            
            # Check timestamp validity
            current_time = time.time()
            if entry.created_at > current_time or entry.created_at < (current_time - 86400 * 365):  # 1 year
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="invalid_timestamp",
                    severity="low",
                    description="Invalid creation timestamp",
                    suggested_action="Update creation timestamp"
                ))
            
        except Exception as e:
            issues.append(IntegrityIssue(
                entry_key=entry_key,
                issue_type="validation_error",
                severity="high",
                description=f"Validation error: {str(e)}",
                suggested_action="Investigate validation failure"
            ))
        
        return issues
    
    async def _validate_standard_compliance(self, entry_key: str, entry: CacheEntry) -> List[IntegrityIssue]:
        """Perform standard compliance validation."""
        issues = []
        
        try:
            # Check expiration
            if entry.is_expired(self.cache_manager.ttl_seconds):
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="expired",
                    severity="medium",
                    description="Entry has expired based on TTL",
                    suggested_action="Remove expired entry"
                ))
            
            # Check token efficiency
            content_size_kb = len(entry.content.encode('utf-8')) / 1024
            efficiency = entry.token_count / content_size_kb if content_size_kb > 0 else 0
            
            if efficiency < self.thresholds["min_token_efficiency"]:
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="low_efficiency",
                    severity="low",
                    description=f"Low token efficiency: {efficiency:.1f} tokens/KB",
                    suggested_action="Consider removing low-efficiency entries"
                ))
            
            # Check entry age
            age_hours = (time.time() - entry.created_at) / 3600
            if age_hours > self.thresholds["max_entry_age_hours"]:
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="stale",
                    severity="low",
                    description=f"Entry is {age_hours:.1f} hours old",
                    suggested_action="Consider refreshing old entries"
                ))
            
            # Check access patterns
            if entry.access_count == 0 and age_hours > 1:  # No access after 1 hour
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="unused",
                    severity="low",
                    description="Entry has never been accessed",
                    suggested_action="Consider removing unused entries"
                ))
            
        except Exception as e:
            issues.append(IntegrityIssue(
                entry_key=entry_key,
                issue_type="compliance_error",
                severity="medium",
                description=f"Compliance check error: {str(e)}",
                suggested_action="Investigate compliance check failure"
            ))
        
        return issues
    
    async def _validate_comprehensive_analysis(self, entry_key: str, entry: CacheEntry) -> List[IntegrityIssue]:
        """Perform comprehensive analysis validation."""
        issues = []
        
        try:
            # Content quality analysis
            content_quality_issues = self._analyze_content_quality(entry_key, entry)
            issues.extend(content_quality_issues)
            
            # Performance impact analysis
            performance_issues = self._analyze_performance_impact(entry_key, entry)
            issues.extend(performance_issues)
            
            # Security validation
            security_issues = self._analyze_security_concerns(entry_key, entry)
            issues.extend(security_issues)
            
        except Exception as e:
            issues.append(IntegrityIssue(
                entry_key=entry_key,
                issue_type="analysis_error",
                severity="medium",
                description=f"Comprehensive analysis error: {str(e)}",
                suggested_action="Investigate analysis failure"
            ))
        
        return issues
    
    def _analyze_content_quality(self, entry_key: str, entry: CacheEntry) -> List[IntegrityIssue]:
        """Analyze content quality and structure."""
        issues = []
        
        # Check for suspicious content patterns
        content = entry.content.lower()
        
        # Check for error messages in cached content
        error_indicators = ["error", "failed", "exception", "traceback", "internal server error"]
        if any(indicator in content for indicator in error_indicators):
            issues.append(IntegrityIssue(
                entry_key=entry_key,
                issue_type="error_content",
                severity="high",
                description="Cached content contains error messages",
                suggested_action="Remove cache entry with error content"
            ))
        
        # Check for placeholder content
        placeholder_indicators = ["lorem ipsum", "placeholder", "test data", "sample content"]
        if any(indicator in content for indicator in placeholder_indicators):
            issues.append(IntegrityIssue(
                entry_key=entry_key,
                issue_type="placeholder_content",
                severity="medium",
                description="Cached content appears to be placeholder data",
                suggested_action="Replace with actual content"
            ))
        
        # Check content length vs token count ratio
        char_to_token_ratio = len(entry.content) / entry.token_count if entry.token_count > 0 else 0
        if char_to_token_ratio > 10:  # Unusually high character to token ratio
            issues.append(IntegrityIssue(
                entry_key=entry_key,
                issue_type="unusual_ratio",
                severity="low",
                description=f"Unusual character to token ratio: {char_to_token_ratio:.1f}",
                suggested_action="Verify content tokenization"
            ))
        
        return issues
    
    def _analyze_performance_impact(self, entry_key: str, entry: CacheEntry) -> List[IntegrityIssue]:
        """Analyze performance impact of cache entry."""
        issues = []
        
        # Check entry size impact
        entry_size_mb = len(entry.content.encode('utf-8')) / (1024 * 1024)
        if entry_size_mb > 1.0:  # Large entry
            issues.append(IntegrityIssue(
                entry_key=entry_key,
                issue_type="large_entry",
                severity="medium",
                description=f"Large cache entry: {entry_size_mb:.2f} MB",
                suggested_action="Consider compressing or splitting large entries"
            ))
        
        # Check access frequency vs size
        if entry.access_count > 0:
            access_frequency = entry.access_count / max(1, (time.time() - entry.created_at) / 3600)
            size_penalty = entry_size_mb * 10  # Penalty for large entries
            
            if access_frequency < size_penalty:
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="inefficient_caching",
                    severity="low",
                    description=f"Low access frequency ({access_frequency:.2f}/hour) for large entry",
                    suggested_action="Consider removing infrequently accessed large entries"
                ))
        
        return issues
    
    def _analyze_security_concerns(self, entry_key: str, entry: CacheEntry) -> List[IntegrityIssue]:
        """Analyze security concerns in cached content."""
        issues = []
        
        content = entry.content.lower()
        
        # Check for sensitive data patterns
        sensitive_patterns = [
            "password", "api_key", "secret", "token", "credential",
            "social security", "credit card", "ssn", "private key"
        ]
        
        for pattern in sensitive_patterns:
            if pattern in content:
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="sensitive_data",
                    severity="critical",
                    description=f"Potential sensitive data detected: {pattern}",
                    suggested_action="Immediately remove entry with sensitive data"
                ))
                break  # Only report first match to avoid spam
        
        # Check for SQL injection patterns in cached queries
        injection_patterns = ["drop table", "delete from", "insert into", "update set", "exec("]
        for pattern in injection_patterns:
            if pattern in content:
                issues.append(IntegrityIssue(
                    entry_key=entry_key,
                    issue_type="sql_injection",
                    severity="high",
                    description=f"Potential SQL injection pattern: {pattern}",
                    suggested_action="Review and sanitize cached content"
                ))
        
        return issues
    
    def _generate_recommendations(self, issues: List[IntegrityIssue], total_entries: int) -> List[str]:
        """Generate recommendations based on validation issues."""
        recommendations = []
        
        # Count issues by type
        issue_counts = {}
        for issue in issues:
            issue_counts[issue.issue_type] = issue_counts.get(issue.issue_type, 0) + 1
        
        # Generate recommendations based on common issues
        if issue_counts.get("expired", 0) > total_entries * 0.1:  # >10% expired
            recommendations.append("Consider reducing TTL or implementing more aggressive cleanup")
        
        if issue_counts.get("corruption", 0) > 0:
            recommendations.append("Investigate source of cache corruption and implement integrity checks")
        
        if issue_counts.get("low_efficiency", 0) > total_entries * 0.2:  # >20% inefficient
            recommendations.append("Review caching strategy to improve token efficiency")
        
        if issue_counts.get("unused", 0) > total_entries * 0.3:  # >30% unused
            recommendations.append("Implement more selective caching based on access patterns")
        
        if issue_counts.get("sensitive_data", 0) > 0:
            recommendations.append("URGENT: Review security policies and implement content filtering")
        
        if issue_counts.get("large_entry", 0) > total_entries * 0.1:  # >10% large entries
            recommendations.append("Consider implementing content compression or entry size limits")
        
        # Add general recommendations if no specific issues
        if not recommendations:
            recommendations.append("Cache appears healthy - continue current practices")
        
        return recommendations
    
    def _determine_health_status(self, total: int, valid: int, invalid: int, 
                                corrupted: int, expired: int) -> str:
        """Determine overall cache health status."""
        if total == 0:
            return "healthy"
        
        corruption_rate = corrupted / total
        invalid_rate = (invalid + expired) / total
        
        if corruption_rate > self.thresholds["max_corruption_rate"]:
            return "critical"
        elif invalid_rate > self.thresholds["max_expiry_rate"] * 1.5:
            return "critical"
        elif invalid_rate > self.thresholds["max_expiry_rate"]:
            return "warning"
        elif valid / total < 0.7:  # Less than 70% valid
            return "warning"
        else:
            return "healthy"
    
    async def auto_repair_cache(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """
        Automatically repair cache based on validation results.
        
        Args:
            validation_result: Result from cache validation
            
        Returns:
            Repair operation summary
        """
        repair_summary = {
            "entries_removed": 0,
            "entries_updated": 0,
            "critical_issues_fixed": 0,
            "warnings_addressed": 0
        }
        
        try:
            with self.cache_manager._lock:
                for issue_dict in validation_result.issues_found:
                    issue = IntegrityIssue(**issue_dict)
                    
                    if issue.severity == "critical":
                        # Remove entries with critical issues
                        if issue.entry_key in self.cache_manager.cache:
                            del self.cache_manager.cache[issue.entry_key]
                            repair_summary["entries_removed"] += 1
                            repair_summary["critical_issues_fixed"] += 1
                    
                    elif issue.issue_type == "expired":
                        # Remove expired entries
                        if issue.entry_key in self.cache_manager.cache:
                            del self.cache_manager.cache[issue.entry_key]
                            repair_summary["entries_removed"] += 1
                            repair_summary["warnings_addressed"] += 1
            
            logger.info("Auto-repair completed", **repair_summary)
            return repair_summary
            
        except Exception as e:
            logger.error("Auto-repair failed", error=str(e))
            raise CacheError(f"Auto-repair failed: {e}")


# Global validator instance
_cache_validator: Optional[CacheValidator] = None


def get_cache_validator(cache_manager: CacheManager) -> CacheValidator:
    """Get or create cache validator instance."""
    global _cache_validator
    
    if _cache_validator is None or _cache_validator.cache_manager != cache_manager:
        _cache_validator = CacheValidator(cache_manager)
    
    return _cache_validator


async def validate_cache_integrity(cache_manager: CacheManager,
                                 level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
    """
    Convenience function to validate cache integrity.
    
    Args:
        cache_manager: Cache manager to validate
        level: Validation level
        
    Returns:
        Validation result
    """
    validator = get_cache_validator(cache_manager)
    return await validator.validate_cache(level)
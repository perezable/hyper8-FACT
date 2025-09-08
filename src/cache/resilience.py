"""
Cache Resilience Module

Provides resilience patterns for cache operations including:
- Circuit breaker pattern for cache failures
- Resilient wrapper for cache operations
- Fallback mechanisms and graceful degradation
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failures detected, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CacheCircuitBreaker:
    """
    Circuit breaker pattern for cache operations.
    
    Prevents cascading failures by temporarily disabling cache operations
    when error threshold is exceeded.
    """
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 success_threshold: int = 2):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            success_threshold: Successful operations needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
        
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None if circuit is open
            
        Raises:
            Exception: If function fails and circuit allows
        """
        # Check circuit state
        self._check_state()
        
        if self.state == CircuitState.OPEN:
            logger.warning("Circuit breaker is open, rejecting cache operation")
            return None
            
        try:
            # Execute function
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            if self.state != CircuitState.OPEN:
                raise
            return None
    
    async def async_call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute async function through circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None if circuit is open
            
        Raises:
            Exception: If function fails and circuit allows
        """
        # Check circuit state
        self._check_state()
        
        if self.state == CircuitState.OPEN:
            logger.warning("Circuit breaker is open, rejecting cache operation")
            return None
            
        try:
            # Execute async function
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            if self.state != CircuitState.OPEN:
                raise
            return None
    
    def _check_state(self) -> None:
        """Check and update circuit state."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               time.time() - self.last_failure_time >= self.recovery_timeout:
                logger.info("Circuit breaker entering half-open state")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
    
    def _on_success(self) -> None:
        """Handle successful operation."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker closing, service recovered")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_state_change = time.time()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            # Immediately open on failure in half-open state
            logger.warning("Circuit breaker opening, recovery failed")
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
        elif self.state == CircuitState.CLOSED and \
             self.failure_count >= self.failure_threshold:
            # Open circuit after threshold exceeded
            logger.warning(f"Circuit breaker opening, failure threshold {self.failure_threshold} exceeded")
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state information."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "is_available": self.state != CircuitState.OPEN
        }
    
    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        logger.info("Circuit breaker reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()


class ResilientCacheWrapper:
    """
    Resilient wrapper for cache operations.
    
    Provides fallback mechanisms and graceful degradation for cache failures.
    """
    
    def __init__(self, 
                 cache_system: Any,
                 circuit_breaker: Optional[CacheCircuitBreaker] = None,
                 enable_fallback: bool = True,
                 enable_retry: bool = True,
                 max_retries: int = 3,
                 retry_delay: float = 0.1):
        """
        Initialize resilient cache wrapper.
        
        Args:
            cache_system: Underlying cache system
            circuit_breaker: Optional circuit breaker instance
            enable_fallback: Enable fallback mechanisms
            enable_retry: Enable retry logic
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
        """
        self.cache_system = cache_system
        self.circuit_breaker = circuit_breaker or CacheCircuitBreaker()
        self.enable_fallback = enable_fallback
        self.enable_retry = enable_retry
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.fallback_cache: Dict[str, Any] = {}
        self.operation_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_hits": 0,
            "circuit_opens": 0,
            "retries": 0,
            "failures": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with resilience.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Try through circuit breaker
        result = await self._execute_with_retry(
            self._cache_get,
            key
        )
        
        if result is not None:
            self.operation_stats["cache_hits"] += 1
            return result
        
        # Try fallback cache if enabled
        if self.enable_fallback and key in self.fallback_cache:
            logger.debug(f"Using fallback cache for key: {key[:16]}")
            self.operation_stats["fallback_hits"] += 1
            return self.fallback_cache[key]
        
        self.operation_stats["cache_misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with resilience.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        # Store in fallback cache first if enabled
        if self.enable_fallback:
            self.fallback_cache[key] = value
            # Limit fallback cache size
            if len(self.fallback_cache) > 1000:
                # Remove oldest entries
                keys_to_remove = list(self.fallback_cache.keys())[:100]
                for k in keys_to_remove:
                    del self.fallback_cache[k]
        
        # Try through circuit breaker
        success = await self._execute_with_retry(
            self._cache_set,
            key, value, ttl
        )
        
        return success or False
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache with resilience.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        # Remove from fallback cache
        if key in self.fallback_cache:
            del self.fallback_cache[key]
        
        # Try through circuit breaker
        success = await self._execute_with_retry(
            self._cache_delete,
            key
        )
        
        return success or False
    
    async def _execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or None
        """
        last_exception = None
        
        for attempt in range(self.max_retries if self.enable_retry else 1):
            try:
                # Execute through circuit breaker
                result = await self.circuit_breaker.async_call(func, *args, **kwargs)
                return result
                
            except Exception as e:
                last_exception = e
                self.operation_stats["retries"] += 1
                
                if attempt < self.max_retries - 1 and self.enable_retry:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    logger.debug(f"Retrying cache operation, attempt {attempt + 2}/{self.max_retries}")
                else:
                    self.operation_stats["failures"] += 1
                    logger.error(f"Cache operation failed after {attempt + 1} attempts: {e}")
                    break
        
        return None
    
    async def _cache_get(self, key: str) -> Optional[Any]:
        """Internal cache get operation."""
        if hasattr(self.cache_system, 'get_cached_response'):
            return await self.cache_system.get_cached_response(key)
        elif hasattr(self.cache_system, 'get'):
            return self.cache_system.get(key)
        return None
    
    async def _cache_set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Internal cache set operation."""
        if hasattr(self.cache_system, 'store_response'):
            return await self.cache_system.store_response(key, value)
        elif hasattr(self.cache_system, 'set'):
            return self.cache_system.set(key, value, ttl)
        return False
    
    async def _cache_delete(self, key: str) -> bool:
        """Internal cache delete operation."""
        if hasattr(self.cache_system, 'invalidate'):
            return self.cache_system.invalidate(key)
        elif hasattr(self.cache_system, 'delete'):
            return self.cache_system.delete(key)
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get operation statistics."""
        return {
            **self.operation_stats,
            "circuit_breaker": self.circuit_breaker.get_state(),
            "fallback_cache_size": len(self.fallback_cache)
        }
    
    def reset_stats(self) -> None:
        """Reset operation statistics."""
        self.operation_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "fallback_hits": 0,
            "circuit_opens": 0,
            "retries": 0,
            "failures": 0
        }
    
    def clear_fallback_cache(self) -> None:
        """Clear the fallback cache."""
        self.fallback_cache.clear()
        logger.info("Fallback cache cleared")


# Export classes
__all__ = [
    'CacheCircuitBreaker',
    'ResilientCacheWrapper',
    'CircuitState'
]
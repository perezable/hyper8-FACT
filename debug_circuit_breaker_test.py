#!/usr/bin/env python3

import asyncio
import sys
import time
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cache.manager import CacheManager
from cache.resilience import ResilientCacheWrapper, CacheCircuitBreaker, CircuitBreakerConfig

async def debug_circuit_breaker():
    # Initialize cache manager with same config as test
    cache_config = {
        "prefix": "fact_resilience_test",
        "min_tokens": 100,
        "max_size": "5MB",
        "ttl_seconds": 30,
        "hit_target_ms": 50,
        "miss_target_ms": 140
    }
    cache_manager = CacheManager(cache_config)
    
    # Initialize circuit breaker with test-friendly settings (same as test)
    circuit_config = CircuitBreakerConfig(
        failure_threshold=3,
        timeout_seconds=5.0,
        success_threshold=3
    )
    
    circuit_breaker = CacheCircuitBreaker(circuit_config)
    resilient_cache = ResilientCacheWrapper(
        cache_manager=cache_manager,
        circuit_breaker=circuit_breaker
    )
    
    print("=== Circuit Breaker Recovery Test Debug ===")
    
    # Step 1: Force circuit breaker to open
    print("\n--- Step 1: Force circuit breaker to open ---")
    
    def failing_get(key):
        raise Exception("Cache failure")
    
    # Trigger failures
    with patch.object(cache_manager, 'get', side_effect=failing_get):
        for i in range(5):
            try:
                await resilient_cache.get(f"test_key_{i}")
            except Exception:
                pass
    
    print(f"Circuit breaker state after failures: {circuit_breaker.get_state()}")
    print(f"Is circuit breaker open? {circuit_breaker.is_open()}")
    
    # Step 2: Wait for timeout and transition to half-open
    print("\n--- Step 2: Wait for timeout ---")
    circuit_breaker.config.timeout_seconds = 0.5
    time.sleep(0.8)
    
    # Try an operation to trigger transition to half-open
    with patch.object(cache_manager, 'get', return_value=None):
        try:
            result = await resilient_cache.get("transition_test")
            print(f"Transition test result: {result}")
        except Exception as e:
            print(f"Transition test exception: {e}")
    
    print(f"Circuit breaker state after timeout: {circuit_breaker.get_state()}")
    
    # Step 3: Store items to close circuit breaker
    print("\n--- Step 3: Store items to close circuit breaker ---")
    test_content = "Recovery test content with sufficient tokens to meet the minimum requirement for cache storage. " * 12
    
    success_count = 0
    stored_queries = []
    for i in range(5):
        try:
            query = f"recovery_test_{i}"
            query_hash = resilient_cache.generate_hash(query)
            print(f"Attempting to store: Query={query}, Hash={query_hash[:16]}...")
            
            store_result = await resilient_cache.store(query_hash, test_content)
            print(f"Store result: {store_result}")
            
            if store_result:
                success_count += 1
                stored_queries.append((query, query_hash))
                print(f"Successful store operation {success_count}/3")
            
            # Check cache contents
            direct_check = cache_manager.get(query_hash)
            print(f"Direct cache check: {direct_check is not None}")
            
            # Check circuit breaker state
            print(f"Circuit breaker state: {circuit_breaker.get_state()}")
            
            time.sleep(0.01)
            
            if success_count >= 3 and circuit_breaker.is_closed():
                print("Circuit breaker closed after 3 successes")
                break
                
        except Exception as e:
            print(f"Store operation failed: {e}")
            continue
    
    print(f"Total successful operations: {success_count}")
    print(f"Final circuit breaker state: {circuit_breaker.get_state()}")
    print(f"Circuit breaker is closed: {circuit_breaker.is_closed()}")
    
    # Step 4: Try retrieval
    print("\n--- Step 4: Try retrieval ---")
    print(f"Total stored queries: {len(stored_queries)}")
    print(f"Cache contents: {list(cache_manager.cache.keys())}")
    
    if stored_queries:
        query, query_hash = stored_queries[0]
        print(f"Attempting to retrieve: Query={query}, Hash={query_hash[:16]}...")
        
        # First try direct cache manager
        direct_retrieved = cache_manager.get(query_hash)
        print(f"Direct retrieval: {direct_retrieved is not None}")
        
        # Then try through resilient cache
        retrieved = await resilient_cache.get(query_hash)
        print(f"Resilient cache retrieval: {retrieved is not None}")
        
        if retrieved:
            print(f"Content length: {len(retrieved.content) if hasattr(retrieved, 'content') else len(str(retrieved))}")
        else:
            print("Retrieved item is None - investigating...")
            
            # Check if item exists in cache
            print(f"Item exists in cache: {query_hash in cache_manager.cache}")
            
            # Check if circuit breaker is affecting this
            print(f"Circuit breaker state during retrieval: {circuit_breaker.get_state()}")
            
            # Try with a fresh circuit breaker state
            print("Testing with circuit breaker in different states...")

if __name__ == "__main__":
    asyncio.run(debug_circuit_breaker())
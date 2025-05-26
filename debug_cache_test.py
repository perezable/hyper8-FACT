#!/usr/bin/env python3

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from cache.manager import CacheManager
from cache.resilience import ResilientCacheWrapper

async def debug_cache():
    # Initialize cache manager
    config = {
        "prefix": "debug_test",
        "min_tokens": 100,
        "max_size": "5MB",
        "ttl_seconds": 30
    }
    cache_manager = CacheManager(config)
    
    # Initialize resilient cache
    resilient_cache = ResilientCacheWrapper(cache_manager)
    
    # Test content
    test_content = "Debug test content with sufficient tokens to meet the minimum requirement for cache storage. " * 12
    
    # Test 1: Direct hash usage
    print("=== Test 1: Direct hash usage ===")
    query = "debug_test_query"
    query_hash = resilient_cache.generate_hash(query)
    print(f"Query: {query}")
    print(f"Generated hash: {query_hash}")
    
    # Store
    store_result = await resilient_cache.store(query_hash, test_content)
    print(f"Store result: {store_result}")
    
    # Retrieve
    retrieved = await resilient_cache.get(query_hash)
    print(f"Retrieved: {retrieved is not None}")
    if retrieved:
        print(f"Content length: {len(retrieved.content) if hasattr(retrieved, 'content') else len(str(retrieved))}")
    
    # Test 2: Check what's in the cache manager directly
    print("\n=== Test 2: Direct cache manager access ===")
    direct_retrieved = cache_manager.get(query_hash)
    print(f"Direct retrieval: {direct_retrieved is not None}")
    if direct_retrieved:
        print(f"Direct content length: {len(direct_retrieved.content)}")
    
    # Test 3: Check cache contents
    print("\n=== Test 3: Cache contents ===")
    print(f"Cache keys: {list(cache_manager.cache.keys())}")
    print(f"Number of items in cache: {len(cache_manager.cache)}")
    
    # Test 4: Alternative approach - store with original query
    print("\n=== Test 4: Store with original query approach ===")
    query2 = "debug_test_query_2"
    query2_hash = cache_manager.generate_hash(query2)
    print(f"Query2: {query2}")
    print(f"Cache manager hash: {query2_hash}")
    
    # Try storing directly with cache manager
    direct_store = cache_manager.store(query2_hash, test_content)
    print(f"Direct store result: {direct_store is not None}")
    
    # Try retrieving
    direct_get = cache_manager.get(query2_hash)
    print(f"Direct get result: {direct_get is not None}")
    
    # Test 5: Check if there's a difference in hash generation
    print("\n=== Test 5: Hash comparison ===")
    resilient_hash = resilient_cache.generate_hash(query2)
    manager_hash = cache_manager.generate_hash(query2)
    print(f"Resilient cache hash: {resilient_hash}")
    print(f"Manager hash: {manager_hash}")
    print(f"Hashes match: {resilient_hash == manager_hash}")

if __name__ == "__main__":
    asyncio.run(debug_cache())
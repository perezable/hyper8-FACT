#!/usr/bin/env python3
"""
Cached Arcade.dev Client Integration Example

This example demonstrates how to integrate Arcade.dev with FACT's caching system
to optimize performance and reduce API calls.
"""

import os
import sys
import asyncio
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import json
import time

# Setup FACT imports using the import helper
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.import_helper import setup_fact_imports

# Setup FACT module path
setup_fact_imports()

from src.cache.manager import CacheManager
from src.core.driver import FACTDriver


@dataclass
class CacheConfig:
    """Configuration for caching behavior."""
    default_ttl: int = 3600  # 1 hour
    max_size: int = 1000
    enabled: bool = True
    key_prefix: str = "arcade"
    
    # Cache TTL by operation type
    ttl_by_operation: Dict[str, int] = None
    
    def __post_init__(self):
        if self.ttl_by_operation is None:
            self.ttl_by_operation = {
                'health': 300,        # 5 minutes
                'user_info': 1800,    # 30 minutes
                'code_analysis': 7200,  # 2 hours
                'test_generation': 3600,  # 1 hour
                'documentation': 7200,   # 2 hours
                'refactoring': 3600,     # 1 hour
            }


class CachedArcadeClient:
    """Arcade.dev client with intelligent caching."""
    
    def __init__(self, api_key: str, cache_manager: CacheManager, cache_config: CacheConfig = None):
        self.api_key = api_key
        self.cache_manager = cache_manager
        self.cache_config = cache_config or CacheConfig()
        self.logger = logging.getLogger(__name__)
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'api_calls': 0,
            'cache_sets': 0,
            'cache_errors': 0
        }
        
    def _generate_cache_key(self, operation: str, **kwargs) -> str:
        """Generate a consistent cache key for the operation."""
        # Create a stable hash of the parameters
        param_str = json.dumps(kwargs, sort_keys=True, default=str)
        param_hash = hashlib.sha256(param_str.encode()).hexdigest()[:16]
        
        return f"{self.cache_config.key_prefix}:{operation}:{param_hash}"
        
    def _get_cache_ttl(self, operation: str) -> int:
        """Get appropriate TTL for the operation."""
        return self.cache_config.ttl_by_operation.get(
            operation, 
            self.cache_config.default_ttl
        )
        
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache with error handling."""
        if not self.cache_config.enabled:
            return None
            
        try:
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                self.stats['cache_hits'] += 1
                self.logger.debug(f"Cache hit for key: {cache_key}")
                return cached_data
            else:
                self.stats['cache_misses'] += 1
                self.logger.debug(f"Cache miss for key: {cache_key}")
                return None
                
        except Exception as e:
            self.stats['cache_errors'] += 1
            self.logger.warning(f"Cache retrieval error for {cache_key}: {e}")
            return None
            
    async def _set_cache(self, cache_key: str, data: Dict[str, Any], ttl: int) -> bool:
        """Store data in cache with error handling."""
        if not self.cache_config.enabled:
            return False
            
        try:
            # Add metadata to cached data
            cache_data = {
                'data': data,
                'cached_at': time.time(),
                'ttl': ttl,
                'operation': cache_key.split(':')[1] if ':' in cache_key else 'unknown'
            }
            
            await self.cache_manager.set(cache_key, cache_data, ttl=ttl)
            self.stats['cache_sets'] += 1
            self.logger.debug(f"Cached data for key: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.stats['cache_errors'] += 1
            self.logger.warning(f"Cache storage error for {cache_key}: {e}")
            return False
            
    async def _simulate_api_call(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Simulate an API call to Arcade.dev (replace with actual implementation)."""
        self.stats['api_calls'] += 1
        
        # Simulate different response times
        delay_map = {
            'health': 0.1,
            'user_info': 0.3,
            'code_analysis': 2.0,
            'test_generation': 3.0,
            'documentation': 2.5,
            'refactoring': 1.8,
        }
        
        await asyncio.sleep(delay_map.get(operation, 1.0))
        
        # Generate mock responses based on operation
        if operation == 'health':
            return {'status': 'healthy', 'timestamp': time.time()}
            
        elif operation == 'user_info':
            return {
                'user_id': '12345',
                'username': 'demo_user',
                'tier': 'premium',
                'api_calls_remaining': 1000
            }
            
        elif operation == 'code_analysis':
            code = kwargs.get('code', '')
            return {
                'analysis_id': f"analysis_{hash(code) % 10000}",
                'language': kwargs.get('language', 'python'),
                'lines_analyzed': len(code.split('\n')),
                'suggestions': [
                    {'type': 'performance', 'message': 'Consider using list comprehension'},
                    {'type': 'style', 'message': 'Function name should be snake_case'},
                    {'type': 'security', 'message': 'Validate input parameters'}
                ],
                'score': 8.5,
                'timestamp': time.time()
            }
            
        elif operation == 'test_generation':
            return {
                'test_id': f"test_{time.time()}",
                'test_cases': [
                    {'name': 'test_happy_path', 'type': 'unit'},
                    {'name': 'test_edge_cases', 'type': 'unit'},
                    {'name': 'test_error_handling', 'type': 'unit'}
                ],
                'coverage_estimate': 95.0,
                'timestamp': time.time()
            }
            
        elif operation == 'documentation':
            return {
                'doc_id': f"doc_{time.time()}",
                'sections': ['Overview', 'Parameters', 'Returns', 'Examples'],
                'estimated_length': 500,
                'timestamp': time.time()
            }
            
        elif operation == 'refactoring':
            return {
                'refactor_id': f"refactor_{time.time()}",
                'suggestions': [
                    {'type': 'extract_method', 'confidence': 0.9},
                    {'type': 'rename_variable', 'confidence': 0.8},
                    {'type': 'optimize_loop', 'confidence': 0.7}
                ],
                'estimated_improvement': '15% performance boost',
                'timestamp': time.time()
            }
            
        else:
            return {'operation': operation, 'timestamp': time.time(), 'status': 'completed'}
            
    async def cached_request(self, operation: str, force_refresh: bool = False, **kwargs) -> Dict[str, Any]:
        """Make a cached request to Arcade.dev API."""
        cache_key = self._generate_cache_key(operation, **kwargs)
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_result = await self._get_from_cache(cache_key)
            if cached_result:
                # Return the data part, not the metadata
                return cached_result.get('data', cached_result)
                
        # Make API call
        start_time = time.time()
        result = await self._simulate_api_call(operation, **kwargs)
        api_duration = time.time() - start_time
        
        # Add API call metadata
        result['_api_duration'] = api_duration
        result['_cached'] = False
        
        # Cache the result
        ttl = self._get_cache_ttl(operation)
        await self._set_cache(cache_key, result, ttl)
        
        self.logger.info(f"API call completed: {operation} ({api_duration:.2f}s)")
        return result
        
    async def health_check(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get API health status with caching."""
        return await self.cached_request('health', force_refresh=force_refresh)
        
    async def get_user_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get user information with caching."""
        return await self.cached_request('user_info', force_refresh=force_refresh)
        
    async def analyze_code(self, code: str, language: str = 'python', force_refresh: bool = False) -> Dict[str, Any]:
        """Analyze code with caching."""
        return await self.cached_request(
            'code_analysis',
            force_refresh=force_refresh,
            code=code,
            language=language
        )
        
    async def generate_tests(self, code: str, test_type: str = 'unit', force_refresh: bool = False) -> Dict[str, Any]:
        """Generate tests with caching."""
        return await self.cached_request(
            'test_generation',
            force_refresh=force_refresh,
            code=code,
            test_type=test_type
        )
        
    async def generate_documentation(self, code: str, doc_type: str = 'api', force_refresh: bool = False) -> Dict[str, Any]:
        """Generate documentation with caching."""
        return await self.cached_request(
            'documentation',
            force_refresh=force_refresh,
            code=code,
            doc_type=doc_type
        )
        
    async def suggest_refactoring(self, code: str, focus: str = 'performance', force_refresh: bool = False) -> Dict[str, Any]:
        """Get refactoring suggestions with caching."""
        return await self.cached_request(
            'refactoring',
            force_refresh=force_refresh,
            code=code,
            focus=focus
        )
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.stats['cache_hits'],
            'cache_misses': self.stats['cache_misses'],
            'api_calls': self.stats['api_calls'],
            'cache_sets': self.stats['cache_sets'],
            'cache_errors': self.stats['cache_errors'],
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests
        }
        
    async def clear_cache(self, operation: str = None):
        """Clear cache for specific operation or all cache."""
        if operation:
            # Clear cache for specific operation (simplified - would need pattern matching)
            self.logger.info(f"Cache clear requested for operation: {operation}")
        else:
            # Clear all cache (if cache manager supports it)
            self.logger.info("Full cache clear requested")


async def demonstrate_caching():
    """Demonstrate the caching capabilities."""
    print("🔧 Initializing cached Arcade.dev client...")
    
    # Initialize cache manager
    cache_manager = CacheManager()
    
    # Configure caching
    cache_config = CacheConfig(
        default_ttl=3600,
        enabled=True,
        ttl_by_operation={
            'health': 300,
            'code_analysis': 7200,  # Cache code analysis for 2 hours
        }
    )
    
    # Create cached client
    api_key = os.getenv('ARCADE_API_KEY', 'demo_key')
    client = CachedArcadeClient(api_key, cache_manager, cache_config)
    
    sample_code = '''
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def main():
    for i in range(10):
        print(f"F({i}) = {calculate_fibonacci(i)}")
'''
    
    print("\n📊 Performance Comparison: First vs Cached Requests")
    print("=" * 60)
    
    # First request (will hit API)
    print("🔍 First code analysis request (API call)...")
    start_time = time.time()
    result1 = await client.analyze_code(sample_code)
    first_duration = time.time() - start_time
    print(f"   Duration: {first_duration:.2f}s")
    print(f"   Suggestions: {len(result1.get('suggestions', []))}")
    
    # Second request (should hit cache)
    print("\n🔍 Second code analysis request (cached)...")
    start_time = time.time()
    result2 = await client.analyze_code(sample_code)
    second_duration = time.time() - start_time
    print(f"   Duration: {second_duration:.2f}s")
    print(f"   Suggestions: {len(result2.get('suggestions', []))}")
    
    # Performance improvement
    if first_duration > 0:
        improvement = ((first_duration - second_duration) / first_duration) * 100
        print(f"\n⚡ Performance improvement: {improvement:.1f}% faster")
    
    # Demonstrate force refresh
    print("\n🔄 Force refresh (bypassing cache)...")
    start_time = time.time()
    result3 = await client.analyze_code(sample_code, force_refresh=True)
    third_duration = time.time() - start_time
    print(f"   Duration: {third_duration:.2f}s")
    
    # Show cache statistics
    print("\n📈 Cache Statistics:")
    stats = client.get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
        
    # Demonstrate different operations
    print("\n🎯 Testing different operations...")
    
    operations = [
        ('Health Check', client.health_check),
        ('User Info', client.get_user_info),
        ('Test Generation', lambda: client.generate_tests(sample_code)),
        ('Documentation', lambda: client.generate_documentation(sample_code)),
        ('Refactoring', lambda: client.suggest_refactoring(sample_code))
    ]
    
    for name, operation in operations:
        print(f"   {name}...")
        result = await operation()
        print(f"   ✅ Completed (cached for {client._get_cache_ttl(name.lower().replace(' ', '_'))}s)")
        
    # Final statistics
    print("\n📊 Final Cache Statistics:")
    final_stats = client.get_cache_stats()
    for key, value in final_stats.items():
        print(f"   {key}: {value}")


async def main():
    """Main demonstration function."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🎮 Arcade.dev Cache Integration Example")
    print("=" * 50)
    
    try:
        await demonstrate_caching()
        print("\n🎉 Cache integration example completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
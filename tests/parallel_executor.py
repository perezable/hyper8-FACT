"""
Parallel Executor for FACT System Testing

Manages concurrent execution of test queries with intelligent load balancing,
rate limiting, and resource management to maximize throughput while maintaining
system stability.
"""

import asyncio
import logging
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from collections import deque, defaultdict
import threading

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ExecutionStats:
    """Statistics for parallel execution monitoring"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time_ms: float = 0.0
    tasks_per_second: float = 0.0
    active_workers: int = 0
    queue_depth: int = 0
    start_time: Optional[datetime] = None
    last_update: Optional[datetime] = None


class RateLimiter:
    """Token bucket rate limiter for controlling request rate"""
    
    def __init__(self, requests_per_second: float, burst_size: int = None):
        self.rate = requests_per_second
        self.burst_size = burst_size or max(1, int(requests_per_second))
        self.tokens = self.burst_size
        self.last_update = time.time()
        self._lock = threading.Lock()
    
    async def acquire(self) -> bool:
        """Acquire a token from the rate limiter"""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            tokens_to_add = elapsed * self.rate
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            else:
                # Calculate wait time for next token
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
                return True


class WorkerPool:
    """Pool of worker coroutines for parallel execution"""
    
    def __init__(self, executor_func: Callable, max_workers: int = 10, 
                 rate_limiter: Optional[RateLimiter] = None):
        self.executor_func = executor_func
        self.max_workers = max_workers
        self.rate_limiter = rate_limiter
        
        self.task_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.workers = []
        self.active_tasks = set()
        self.stats = ExecutionStats()
        self._shutdown = False
        
    async def start(self):
        """Start the worker pool"""
        self.stats.start_time = datetime.now()
        logger.info(f"Starting worker pool with {self.max_workers} workers")
        
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info(f"Worker pool started with {len(self.workers)} workers")
    
    async def _worker(self, worker_id: str):
        """Individual worker coroutine"""
        logger.debug(f"Worker {worker_id} started")
        
        while not self._shutdown:
            try:
                # Get task from queue with timeout
                try:
                    task_data = await asyncio.wait_for(
                        self.task_queue.get(), 
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Apply rate limiting
                if self.rate_limiter:
                    await self.rate_limiter.acquire()
                
                # Execute task
                task_id = task_data.get('id', 'unknown')
                self.active_tasks.add(task_id)
                self.stats.active_workers += 1
                
                start_time = time.time()
                
                try:
                    result = await self.executor_func(**task_data)
                    execution_time = (time.time() - start_time) * 1000
                    
                    # Update stats
                    self.stats.completed_tasks += 1
                    self._update_avg_response_time(execution_time)
                    
                    await self.result_queue.put({
                        'task_id': task_id,
                        'success': True,
                        'result': result,
                        'execution_time_ms': execution_time,
                        'worker_id': worker_id
                    })
                    
                except Exception as e:
                    execution_time = (time.time() - start_time) * 1000
                    self.stats.failed_tasks += 1
                    
                    logger.error(f"Worker {worker_id} task {task_id} failed: {e}")
                    
                    await self.result_queue.put({
                        'task_id': task_id,
                        'success': False,
                        'error': str(e),
                        'execution_time_ms': execution_time,
                        'worker_id': worker_id
                    })
                
                finally:
                    self.active_tasks.discard(task_id)
                    self.stats.active_workers -= 1
                    self.task_queue.task_done()
                    
            except asyncio.CancelledError:
                logger.debug(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(0.1)  # Brief pause before retrying
        
        logger.debug(f"Worker {worker_id} stopped")
    
    def _update_avg_response_time(self, new_time: float):
        """Update average response time with exponential moving average"""
        alpha = 0.1  # Smoothing factor
        if self.stats.avg_response_time_ms == 0:
            self.stats.avg_response_time_ms = new_time
        else:
            self.stats.avg_response_time_ms = (
                alpha * new_time + 
                (1 - alpha) * self.stats.avg_response_time_ms
            )
    
    async def submit_task(self, task_data: Dict[str, Any]):
        """Submit a task for execution"""
        self.stats.total_tasks += 1
        self.stats.queue_depth = self.task_queue.qsize() + 1
        await self.task_queue.put(task_data)
    
    async def submit_batch(self, batch_data: List[Dict[str, Any]]):
        """Submit a batch of tasks"""
        for task_data in batch_data:
            await self.submit_task(task_data)
    
    async def get_result(self) -> Dict[str, Any]:
        """Get next available result"""
        return await self.result_queue.get()
    
    async def get_results(self, count: int, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get specified number of results"""
        results = []
        
        try:
            for _ in range(count):
                if timeout:
                    result = await asyncio.wait_for(self.get_result(), timeout=timeout)
                else:
                    result = await self.get_result()
                results.append(result)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for results. Got {len(results)}/{count}")
        
        return results
    
    def get_stats(self) -> ExecutionStats:
        """Get current execution statistics"""
        now = datetime.now()
        self.stats.last_update = now
        self.stats.queue_depth = self.task_queue.qsize()
        
        # Calculate tasks per second
        if self.stats.start_time:
            elapsed_seconds = (now - self.stats.start_time).total_seconds()
            if elapsed_seconds > 0:
                self.stats.tasks_per_second = self.stats.completed_tasks / elapsed_seconds
        
        return self.stats
    
    async def shutdown(self):
        """Shutdown the worker pool gracefully"""
        logger.info("Shutting down worker pool...")
        self._shutdown = True
        
        # Wait for active tasks to complete
        if self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")
            while self.active_tasks:
                await asyncio.sleep(0.1)
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        logger.info("Worker pool shutdown complete")


class LoadBalancer:
    """Load balancer for distributing tasks across different query methods"""
    
    def __init__(self, method_weights: Dict[str, float] = None):
        self.method_weights = method_weights or {}
        self.method_stats = defaultdict(lambda: {'success_count': 0, 'total_count': 0, 'avg_response_time': 0.0})
        self.method_queues = defaultdict(deque)
        
    def assign_method(self, available_methods: List[str]) -> str:
        """Assign optimal method based on current performance"""
        if not available_methods:
            raise ValueError("No available methods")
        
        if len(available_methods) == 1:
            return available_methods[0]
        
        # Calculate method scores based on success rate and response time
        method_scores = {}
        
        for method in available_methods:
            stats = self.method_stats[method]
            
            # Base score from configured weights
            base_score = self.method_weights.get(method, 1.0)
            
            # Adjust based on performance
            if stats['total_count'] > 0:
                success_rate = stats['success_count'] / stats['total_count']
                response_time_penalty = min(stats['avg_response_time'] / 1000.0, 1.0)  # Normalize to 0-1
                performance_score = success_rate * (1.0 - response_time_penalty * 0.3)
            else:
                performance_score = 0.5  # Neutral for untested methods
            
            method_scores[method] = base_score * (0.3 + 0.7 * performance_score)
        
        # Select method with highest score
        best_method = max(method_scores.items(), key=lambda x: x[1])[0]
        return best_method
    
    def update_method_stats(self, method: str, success: bool, response_time_ms: float):
        """Update method performance statistics"""
        stats = self.method_stats[method]
        stats['total_count'] += 1
        
        if success:
            stats['success_count'] += 1
        
        # Update average response time with exponential moving average
        alpha = 0.2
        if stats['avg_response_time'] == 0:
            stats['avg_response_time'] = response_time_ms
        else:
            stats['avg_response_time'] = (
                alpha * response_time_ms + 
                (1 - alpha) * stats['avg_response_time']
            )
    
    def get_method_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get performance statistics for all methods"""
        return dict(self.method_stats)


class ParallelExecutor:
    """
    Main parallel executor for FACT system testing.
    
    Manages concurrent execution of test queries with intelligent
    load balancing, rate limiting, and performance monitoring.
    """
    
    def __init__(self, config):
        self.config = config
        self.load_balancer = LoadBalancer()
        
        # Create rate limiter if configured
        requests_per_second = getattr(config, 'requests_per_second', 10.0)
        self.rate_limiter = RateLimiter(
            requests_per_second=requests_per_second,
            burst_size=config.max_concurrent_tests
        )
        
        # Execution tracking
        self.active_batches = {}
        self.execution_history = []
        
    async def execute_batch(self, method, questions, batch_id: str) -> List[Any]:
        """
        Execute a batch of questions using specified method.
        
        Args:
            method: QueryMethod enum value
            questions: List of TestQuestion objects
            batch_id: Unique identifier for this batch
            
        Returns:
            List of TestResult objects
        """
        start_time = datetime.now()
        logger.info(f"Starting batch {batch_id} with {len(questions)} questions using method {method.value}")
        
        # Import here to avoid circular imports
        from query_executor import QueryExecutor
        from response_collector import TestResult
        
        # Create query executor for this batch
        query_executor = QueryExecutor(self.config)
        await query_executor.initialize()
        
        try:
            # Create worker pool
            async def execute_single_query(question, question_idx):
                """Execute a single query and return result"""
                try:
                    query_result = await query_executor.execute_query(method, question)
                    
                    # Convert to TestResult format
                    result = TestResult(
                        query_id=query_result.query_id,
                        question_id=question.id,
                        query_text=question.text,
                        method=query_result.method,
                        success=query_result.success,
                        response=query_result.response,
                        response_time_ms=query_result.response_time_ms,
                        error_message=query_result.error_message,
                        attempt_count=query_result.attempt_count,
                        timestamp=query_result.timestamp
                    )
                    
                    # Update load balancer stats
                    self.load_balancer.update_method_stats(
                        method.value, 
                        query_result.success, 
                        query_result.response_time_ms
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.error(f"Error executing query {question.id}: {e}")
                    return TestResult(
                        query_id=f"error_{question.id}",
                        question_id=question.id,
                        query_text=question.text,
                        method=method.value,
                        success=False,
                        response=None,
                        response_time_ms=0.0,
                        error_message=str(e)
                    )
            
            # Create worker pool
            worker_pool = WorkerPool(
                executor_func=execute_single_query,
                max_workers=min(self.config.max_concurrent_tests, len(questions)),
                rate_limiter=self.rate_limiter
            )
            
            await worker_pool.start()
            
            # Track this batch
            self.active_batches[batch_id] = {
                'method': method.value,
                'question_count': len(questions),
                'start_time': start_time,
                'worker_pool': worker_pool
            }
            
            try:
                # Submit all questions as tasks
                for idx, question in enumerate(questions):
                    task_data = {
                        'id': f"{batch_id}_{question.id}",
                        'question': question,
                        'question_idx': idx
                    }
                    await worker_pool.submit_task(task_data)
                
                # Collect results
                results = []
                total_questions = len(questions)
                
                # Progress monitoring
                last_progress_log = 0
                
                for i in range(total_questions):
                    result_data = await worker_pool.get_result()
                    results.append(result_data['result'])
                    
                    # Log progress periodically
                    progress = (i + 1) / total_questions * 100
                    if progress - last_progress_log >= 20:  # Log every 20%
                        stats = worker_pool.get_stats()
                        logger.info(f"Batch {batch_id} progress: {progress:.0f}% "
                                  f"({i + 1}/{total_questions}), "
                                  f"avg response time: {stats.avg_response_time_ms:.1f}ms, "
                                  f"throughput: {stats.tasks_per_second:.1f} req/s")
                        last_progress_log = progress
                
                # Final statistics
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                final_stats = worker_pool.get_stats()
                
                batch_summary = {
                    'batch_id': batch_id,
                    'method': method.value,
                    'duration_seconds': duration,
                    'total_questions': total_questions,
                    'successful_results': sum(1 for r in results if r.success),
                    'failed_results': sum(1 for r in results if not r.success),
                    'avg_response_time_ms': final_stats.avg_response_time_ms,
                    'throughput_req_per_sec': final_stats.tasks_per_second
                }
                
                self.execution_history.append(batch_summary)
                
                logger.info(f"Batch {batch_id} completed in {duration:.1f}s: "
                          f"{batch_summary['successful_results']}/{total_questions} successful, "
                          f"avg response time: {final_stats.avg_response_time_ms:.1f}ms, "
                          f"throughput: {final_stats.tasks_per_second:.1f} req/s")
                
                return results
                
            finally:
                await worker_pool.shutdown()
                
        finally:
            # Clean up
            await query_executor.cleanup()
            if batch_id in self.active_batches:
                del self.active_batches[batch_id]
    
    async def execute_multi_method_batch(self, questions, batch_id: str) -> Dict[str, List[Any]]:
        """
        Execute a batch of questions using multiple methods for comparison.
        
        Args:
            questions: List of TestQuestion objects  
            batch_id: Unique identifier for this batch
            
        Returns:
            Dict mapping method names to lists of TestResult objects
        """
        available_methods = self.config.query_methods
        results = {}
        
        logger.info(f"Starting multi-method batch {batch_id} with {len(questions)} questions "
                   f"across {len(available_methods)} methods")
        
        # Execute each method in parallel
        method_tasks = []
        
        for method_name in available_methods:
            from query_executor import QueryMethod
            method = QueryMethod[method_name.upper()]
            
            task = asyncio.create_task(
                self.execute_batch(method, questions, f"{batch_id}_{method_name}")
            )
            method_tasks.append((method_name, task))
        
        # Wait for all methods to complete
        for method_name, task in method_tasks:
            try:
                method_results = await task
                results[method_name] = method_results
                logger.info(f"Method {method_name} completed for batch {batch_id}")
            except Exception as e:
                logger.error(f"Method {method_name} failed for batch {batch_id}: {e}")
                results[method_name] = []
        
        return results
    
    async def execute_adaptive_batch(self, questions, batch_id: str) -> List[Any]:
        """
        Execute batch with adaptive method selection based on performance.
        
        Dynamically assigns the best-performing method to each question.
        """
        logger.info(f"Starting adaptive batch {batch_id} with {len(questions)} questions")
        
        from query_executor import QueryMethod, QueryExecutor
        from response_collector import TestResult
        
        # Initialize query executor
        query_executor = QueryExecutor(self.config)
        await query_executor.initialize()
        
        results = []
        available_methods = [QueryMethod[m.upper()] for m in self.config.query_methods]
        
        try:
            # Process questions with adaptive method selection
            for question in questions:
                # Select best method based on current performance
                best_method_name = self.load_balancer.assign_method(
                    [m.value for m in available_methods]
                )
                best_method = QueryMethod[best_method_name.upper()]
                
                # Execute query
                query_result = await query_executor.execute_query(best_method, question)
                
                # Convert to TestResult
                result = TestResult(
                    query_id=query_result.query_id,
                    question_id=question.id,
                    query_text=question.text,
                    method=query_result.method,
                    success=query_result.success,
                    response=query_result.response,
                    response_time_ms=query_result.response_time_ms,
                    error_message=query_result.error_message,
                    attempt_count=query_result.attempt_count,
                    timestamp=query_result.timestamp
                )
                
                results.append(result)
                
                # Update load balancer with performance
                self.load_balancer.update_method_stats(
                    best_method.value,
                    query_result.success,
                    query_result.response_time_ms
                )
                
                # Log progress
                if len(results) % 10 == 0:
                    logger.info(f"Adaptive batch {batch_id} progress: {len(results)}/{len(questions)}")
            
            logger.info(f"Adaptive batch {batch_id} completed: {len(results)} results")
            return results
            
        finally:
            await query_executor.cleanup()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary across all executions"""
        if not self.execution_history:
            return {"message": "No execution history available"}
        
        total_duration = sum(batch['duration_seconds'] for batch in self.execution_history)
        total_questions = sum(batch['total_questions'] for batch in self.execution_history)
        total_successful = sum(batch['successful_results'] for batch in self.execution_history)
        
        avg_response_times = [batch['avg_response_time_ms'] for batch in self.execution_history 
                             if batch['avg_response_time_ms'] > 0]
        avg_throughputs = [batch['throughput_req_per_sec'] for batch in self.execution_history 
                          if batch['throughput_req_per_sec'] > 0]
        
        return {
            'total_batches': len(self.execution_history),
            'total_duration_seconds': total_duration,
            'total_questions_processed': total_questions,
            'overall_success_rate': total_successful / total_questions if total_questions > 0 else 0,
            'avg_response_time_ms': sum(avg_response_times) / len(avg_response_times) if avg_response_times else 0,
            'avg_throughput_req_per_sec': sum(avg_throughputs) / len(avg_throughputs) if avg_throughputs else 0,
            'method_performance': self.load_balancer.get_method_stats(),
            'batch_history': self.execution_history[-10:]  # Last 10 batches
        }
    
    async def monitor_active_batches(self) -> Dict[str, Any]:
        """Monitor currently active batch executions"""
        active_status = {}
        
        for batch_id, batch_info in self.active_batches.items():
            if 'worker_pool' in batch_info:
                stats = batch_info['worker_pool'].get_stats()
                elapsed = (datetime.now() - batch_info['start_time']).total_seconds()
                
                active_status[batch_id] = {
                    'method': batch_info['method'],
                    'total_questions': batch_info['question_count'],
                    'completed_tasks': stats.completed_tasks,
                    'failed_tasks': stats.failed_tasks,
                    'active_workers': stats.active_workers,
                    'queue_depth': stats.queue_depth,
                    'elapsed_seconds': elapsed,
                    'avg_response_time_ms': stats.avg_response_time_ms,
                    'tasks_per_second': stats.tasks_per_second
                }
        
        return active_status
    
    async def cleanup(self):
        """Cleanup parallel executor resources"""
        # Wait for any active batches to complete
        if self.active_batches:
            logger.info(f"Waiting for {len(self.active_batches)} active batches to complete...")
            
            while self.active_batches:
                await asyncio.sleep(0.5)
        
        logger.info("Parallel executor cleanup completed")


# Testing function
async def test_parallel_execution():
    """Test parallel execution functionality"""
    from fact_test_runner import create_default_config, TestConfig
    from query_executor import TestQuestion
    
    # Create test configuration
    config = create_default_config("local")
    config.max_concurrent_tests = 5
    config.query_methods = ["database"]  # Test with database only
    
    # Create parallel executor
    executor = ParallelExecutor(config)
    
    # Create test questions
    questions = [
        TestQuestion(
            id=f"test_{i}",
            text=f"What are the contractor license requirements for question {i}?",
            category="state_licensing_requirements",
            state="GA"
        )
        for i in range(10)
    ]
    
    # Execute batch
    from query_executor import QueryMethod
    results = await executor.execute_batch(
        QueryMethod.DATABASE, 
        questions, 
        "test_batch_1"
    )
    
    print(f"Parallel execution test completed: {len(results)} results")
    for result in results[:3]:  # Show first 3 results
        print(f"  Result {result.question_id}: Success={result.success}, "
              f"Time={result.response_time_ms:.1f}ms")
    
    # Get performance summary
    summary = executor.get_performance_summary()
    print(f"Performance summary: {summary}")
    
    await executor.cleanup()


if __name__ == "__main__":
    # Test parallel execution
    import asyncio
    asyncio.run(test_parallel_execution())
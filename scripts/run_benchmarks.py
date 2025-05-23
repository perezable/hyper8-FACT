#!/usr/bin/env python3
"""
FACT Comprehensive Benchmarking Script

Executes complete performance validation including benchmarks, comparisons,
profiling, and report generation.
"""

import asyncio
import argparse
import json
import sys
import time
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from benchmarking import (
    BenchmarkFramework,
    BenchmarkRunner,
    BenchmarkConfig,
    RAGComparison,
    SystemProfiler,
    ContinuousMonitor,
    BenchmarkVisualizer,
    ReportGenerator
)
from cache.manager import CacheManager


async def run_comprehensive_benchmark(args):
    """Run comprehensive benchmark suite."""
    print("🚀 Starting FACT Comprehensive Benchmark Suite")
    print("=" * 60)
    
    # Initialize components
    config = BenchmarkConfig(
        iterations=args.iterations,
        warmup_iterations=args.warmup,
        concurrent_users=args.concurrent_users,
        timeout_seconds=args.timeout,
        target_hit_latency_ms=args.hit_target,
        target_miss_latency_ms=args.miss_target,
        target_cost_reduction_hit=args.cost_reduction / 100.0,
        target_cache_hit_rate=args.cache_hit_rate / 100.0
    )
    
    framework = BenchmarkFramework(config)
    runner = BenchmarkRunner(framework)
    profiler = SystemProfiler()
    visualizer = BenchmarkVisualizer()
    report_generator = ReportGenerator(visualizer)
    
    # Initialize cache manager if available
    cache_manager = None
    try:
        cache_manager = CacheManager()
        print("✅ Cache manager initialized")
    except Exception as e:
        print(f"⚠️  Cache manager not available: {e}")
    
    # Phase 1: Performance Validation
    print("\n📊 Phase 1: Performance Validation")
    print("-" * 40)
    
    validation_results = await runner.run_performance_validation(cache_manager)
    
    # Display validation results
    print(f"Overall Validation: {'✅ PASS' if validation_results['overall_pass'] else '❌ FAIL'}")
    
    target_validation = validation_results['target_validation']
    for target_name, target_data in target_validation.items():
        status = "✅ PASS" if target_data['met'] else "❌ FAIL"
        print(f"  {target_name}: {status} ({target_data['actual_ms' if 'latency' in target_name else 'actual_percent']:.1f})")
    
    # Phase 2: RAG Comparison (if enabled)
    comparison_result = None
    if args.include_rag_comparison:
        print("\n⚔️  Phase 2: RAG Comparison Analysis")
        print("-" * 40)
        
        rag_comparison = RAGComparison(framework)
        comparison_result = await rag_comparison.run_comparison_benchmark(
            runner.test_queries, cache_manager, config.iterations
        )
        
        print(f"Latency Improvement: {comparison_result.improvement_factors.get('latency', 1.0):.1f}x")
        print(f"Cost Savings: {comparison_result.cost_savings.get('percentage', 0.0):.1f}%")
        print(f"Recommendation: {comparison_result.recommendation}")
    
    # Phase 3: Profiling Analysis (if enabled)
    profile_result = None
    if args.include_profiling:
        print("\n🔍 Phase 3: Performance Profiling")
        print("-" * 40)
        
        # Profile a representative operation
        async def sample_operation():
            return await runner.run_performance_validation(cache_manager)
        
        _, profile_result = await profiler.profile_complete_operation(
            sample_operation, "performance_validation"
        )
        
        print(f"Execution Time: {profile_result.execution_time_ms:.1f}ms")
        print(f"Bottlenecks Found: {len(profile_result.bottlenecks)}")
        
        critical_bottlenecks = [b for b in profile_result.bottlenecks if b.severity == "critical"]
        if critical_bottlenecks:
            print("❌ Critical Bottlenecks:")
            for bottleneck in critical_bottlenecks[:3]:
                print(f"  - {bottleneck.component}: {bottleneck.description}")
    
    # Phase 4: Load Testing (if enabled)
    load_test_results = None
    if args.include_load_test:
        print("\n🚦 Phase 4: Load Testing")
        print("-" * 40)
        
        load_test_results = await runner.run_load_test(
            concurrent_users=args.load_test_users,
            duration_seconds=args.load_test_duration
        )
        
        print(f"Concurrent Users: {load_test_results['concurrent_users']}")
        print(f"Throughput: {load_test_results['throughput_qps']:.1f} QPS")
        print(f"Avg Response Time: {load_test_results['avg_response_time_ms']:.1f}ms")
        print(f"Error Rate: {load_test_results['error_rate']:.1f}%")
    
    # Phase 5: Report Generation
    print("\n📝 Phase 5: Report Generation")
    print("-" * 40)
    
    benchmark_summary = validation_results['benchmark_summary']
    
    # Generate comprehensive report
    report = report_generator.generate_comprehensive_report(
        benchmark_summary=benchmark_summary,
        comparison_result=comparison_result,
        profile_result=profile_result,
        alerts=None  # No alerts in batch mode
    )
    
    # Save reports
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # JSON report
    json_report_path = output_dir / f"benchmark_report_{int(time.time())}.json"
    with open(json_report_path, 'w') as f:
        f.write(report_generator.export_report_json(report))
    
    # Text summary
    text_report_path = output_dir / f"benchmark_summary_{int(time.time())}.txt"
    with open(text_report_path, 'w') as f:
        f.write(report_generator.export_report_summary_text(report))
    
    # Chart data (for external visualization)
    charts_dir = output_dir / "charts"
    charts_dir.mkdir(exist_ok=True)
    
    for i, chart in enumerate(report.charts):
        chart_path = charts_dir / f"chart_{i}_{chart.chart_type}.json"
        with open(chart_path, 'w') as f:
            f.write(visualizer.export_chart_data_json(chart))
    
    print(f"📄 Reports saved to: {output_dir}")
    print(f"📄 JSON Report: {json_report_path}")
    print(f"📄 Summary: {text_report_path}")
    print(f"📈 Charts: {charts_dir}")
    
    # Final Summary
    print("\n🎯 Final Summary")
    print("-" * 40)
    
    grade = report.summary.get('performance_grade', 'N/A')
    print(f"Performance Grade: {grade}")
    
    if validation_results['overall_pass']:
        print("🎉 All performance targets achieved!")
    else:
        print("⚠️  Some performance targets not met. Review optimization strategies.")
    
    # Print key recommendations
    if report.recommendations:
        print("\n🔧 Key Recommendations:")
        for i, rec in enumerate(report.recommendations[:5], 1):
            print(f"  {i}. {rec}")
    
    return validation_results['overall_pass']


async def run_continuous_monitoring(args):
    """Run continuous monitoring mode."""
    print("🔄 Starting FACT Continuous Monitoring")
    print("=" * 60)
    
    # Initialize monitoring
    monitor = ContinuousMonitor()
    
    # Add console alert callback
    def alert_callback(alert):
        severity_emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}
        emoji = severity_emoji.get(alert.severity, "📢")
        print(f"{emoji} {alert.severity.upper()}: {alert.message}")
    
    monitor.add_alert_callback(alert_callback)
    
    # Initialize cache manager
    cache_manager = None
    try:
        cache_manager = CacheManager()
        print("✅ Cache manager initialized")
    except Exception as e:
        print(f"⚠️  Cache manager not available: {e}")
    
    try:
        # Start monitoring
        await monitor.start_monitoring(cache_manager)
        print("📡 Monitoring started. Press Ctrl+C to stop.")
        
        # Monitor for specified duration or indefinitely
        if args.monitor_duration > 0:
            await asyncio.sleep(args.monitor_duration)
        else:
            # Monitor indefinitely
            try:
                while True:
                    await asyncio.sleep(60)
                    
                    # Print status every minute
                    status = monitor.get_monitoring_status()
                    print(f"📊 Active alerts: {status['active_alerts']}")
            except KeyboardInterrupt:
                pass
    
    finally:
        # Stop monitoring and generate report
        await monitor.stop_monitoring()
        
        monitoring_report = monitor.export_monitoring_report()
        
        # Save monitoring report
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        report_path = output_dir / f"monitoring_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(monitoring_report, f, indent=2, default=str)
        
        print(f"\n📄 Monitoring report saved: {report_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FACT Comprehensive Benchmarking System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic benchmark
  python scripts/run_benchmarks.py

  # Comprehensive benchmark with all features
  python scripts/run_benchmarks.py --include-rag-comparison --include-profiling --include-load-test
  
  # Continuous monitoring
  python scripts/run_benchmarks.py --mode monitoring --monitor-duration 3600
  
  # Custom performance targets
  python scripts/run_benchmarks.py --hit-target 40 --miss-target 120 --cost-reduction 85
        """
    )
    
    # Mode selection
    parser.add_argument(
        '--mode', 
        choices=['benchmark', 'monitoring'],
        default='benchmark',
        help='Execution mode (default: benchmark)'
    )
    
    # Benchmark configuration
    parser.add_argument('--iterations', type=int, default=10, help='Number of benchmark iterations')
    parser.add_argument('--warmup', type=int, default=3, help='Number of warmup iterations')
    parser.add_argument('--concurrent-users', type=int, default=1, help='Number of concurrent users')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')
    
    # Performance targets
    parser.add_argument('--hit-target', type=float, default=48.0, help='Cache hit latency target (ms)')
    parser.add_argument('--miss-target', type=float, default=140.0, help='Cache miss latency target (ms)')
    parser.add_argument('--cost-reduction', type=float, default=90.0, help='Cost reduction target (%)')
    parser.add_argument('--cache-hit-rate', type=float, default=60.0, help='Cache hit rate target (%)')
    
    # Optional components
    parser.add_argument('--include-rag-comparison', action='store_true', help='Include RAG comparison')
    parser.add_argument('--include-profiling', action='store_true', help='Include performance profiling')
    parser.add_argument('--include-load-test', action='store_true', help='Include load testing')
    
    # Load testing configuration
    parser.add_argument('--load-test-users', type=int, default=10, help='Load test concurrent users')
    parser.add_argument('--load-test-duration', type=int, default=60, help='Load test duration (seconds)')
    
    # Monitoring configuration
    parser.add_argument('--monitor-duration', type=int, default=0, help='Monitoring duration (0=indefinite)')
    
    # Output configuration
    parser.add_argument('--output-dir', default='./benchmark_results', help='Output directory for reports')
    
    args = parser.parse_args()
    
    # Run appropriate mode
    if args.mode == 'benchmark':
        success = asyncio.run(run_comprehensive_benchmark(args))
        sys.exit(0 if success else 1)
    elif args.mode == 'monitoring':
        asyncio.run(run_continuous_monitoring(args))
        sys.exit(0)


if __name__ == "__main__":
    main()
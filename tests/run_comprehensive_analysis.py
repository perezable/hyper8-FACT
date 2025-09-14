#!/usr/bin/env python3
"""
FACT System - Comprehensive Performance Analysis Pipeline

This script orchestrates the complete performance analysis pipeline:
1. Response Analysis Engine - Multi-dimensional scoring
2. Statistical Reporter - Comprehensive statistics and comparisons
3. Weakness Detector - Pattern identification and gap analysis
4. Report Generator - Comprehensive markdown reports and dashboards

Usage:
    python run_comprehensive_analysis.py --input-file path/to/test_data.json --output-dir reports/
    python run_comprehensive_analysis.py --sample-mode --test-size 200
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import structlog

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from performance_analyzer import ResponseAnalysisEngine, AnalyzedResponse
from statistical_reporter import StatisticalReporter
from weakness_detector import WeaknessDetector
from report_generator import ReportGenerator

logger = structlog.get_logger(__name__)


class ComprehensiveAnalysisPipeline:
    """Orchestrates the complete FACT performance analysis pipeline."""
    
    def __init__(self, output_dir: str = "reports"):
        """Initialize the analysis pipeline."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize analysis components
        self.performance_analyzer = ResponseAnalysisEngine()
        self.statistical_reporter = StatisticalReporter()
        self.weakness_detector = WeaknessDetector()
        self.report_generator = ReportGenerator()
        
        # Track analysis results
        self.analyzed_responses: List[AnalyzedResponse] = []
        self.results_files = {}
        
        # Setup logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.dev.ConsoleRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    
    def generate_sample_test_data(self, num_responses: int = 200) -> List[Dict[str, Any]]:
        """Generate sample test data for demonstration."""
        import random
        import numpy as np
        
        personas = ['insurance_agent', 'insurance_broker', 'claims_adjuster', 'underwriter', 'producer']
        categories = ['licensing', 'continuing_education', 'renewals', 'exams', 'regulations', 'compliance']
        states = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
        difficulties = ['easy', 'medium', 'hard']
        match_types = ['exact', 'fuzzy', 'keyword', 'partial', 'none']
        
        sample_questions = [
            "What are the licensing requirements for insurance agents?",
            "How many CE hours are required for license renewal?",
            "What is the fee for an insurance producer license?",
            "When does my insurance license expire?",
            "What are the continuing education requirements?",
            "How do I renew my insurance license?",
            "What exams do I need to take for licensing?",
            "Are there any ethics requirements for CE?",
            "What is the process for license reinstatement?",
            "How do I transfer my license to another state?"
        ]
        
        sample_data = []
        
        for i in range(num_responses):
            persona = random.choice(personas)
            category = random.choice(categories)
            state = random.choice(states)
            difficulty = random.choice(difficulties)
            base_question = random.choice(sample_questions)
            
            # Generate performance characteristics based on category and difficulty
            if category == 'licensing' and difficulty == 'easy':
                base_confidence = 0.85
                base_score = 0.8
            elif category == 'regulations' and difficulty == 'hard':
                base_confidence = 0.6
                base_score = 0.5
            else:
                base_confidence = 0.75
                base_score = 0.7
            
            # Add noise
            confidence = max(0.0, min(1.0, base_confidence + random.gauss(0, 0.15)))
            overall_score = max(0.0, min(1.0, base_score + random.gauss(0, 0.2)))
            
            # Generate related metrics
            exact_match = 1.0 if random.random() < 0.3 else 0.0
            semantic_similarity = max(0.0, min(1.0, overall_score + random.gauss(0, 0.1)))
            category_accuracy = 1.0 if random.random() < 0.8 else 0.0
            state_relevance = 1.0 if random.random() < 0.7 else 0.0
            
            # Response time - varies by complexity
            base_time = 150 if difficulty == 'easy' else 300 if difficulty == 'medium' else 500
            response_time = max(50, base_time + random.gauss(0, 100))
            
            match_type = random.choice(match_types)
            if match_type == 'none':
                confidence = 0.0
                overall_score = 0.0
                semantic_similarity = 0.0
            
            sample_data.append({
                'test_id': f'test_{i+1:04d}',
                'persona': persona,
                'category': category,
                'state': state,
                'difficulty': difficulty,
                'original_question': f"{state} {base_question}",
                'query_variation': f"How about {base_question.lower()}",
                'expected_answer': f"Sample expected answer for {category} in {state}",
                'retrieved_answer': "" if match_type == 'none' else f"Retrieved answer for {category}",
                'response_time_ms': response_time,
                'match_type': match_type,
                'confidence': confidence,
                'exact_match': exact_match == 1.0,
                'category_match': category_accuracy == 1.0,
                'state_match': state_relevance == 1.0
            })
        
        logger.info(f"Generated {len(sample_data)} sample test records")
        return sample_data
    
    def load_test_data(self, input_file: str) -> List[Dict[str, Any]]:
        """Load test data from file."""
        with open(input_file, 'r') as f:
            if input_file.endswith('.json'):
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif 'test_results' in data:
                    return data['test_results']
                elif 'analyzed_responses' in data:
                    return data['analyzed_responses']
                else:
                    logger.error(f"Unexpected JSON structure in {input_file}")
                    return []
            else:
                logger.error(f"Unsupported file format: {input_file}")
                return []
    
    async def run_performance_analysis(self, test_data: List[Dict[str, Any]]) -> str:
        """Run the performance analysis engine."""
        logger.info("🔍 Starting Performance Analysis Engine...")
        
        # Initialize the analyzer
        await self.performance_analyzer.initialize()
        
        # Analyze all responses
        self.analyzed_responses = await self.performance_analyzer.analyze_batch(test_data)
        
        # Save results
        analysis_file = self.output_dir / f"performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.performance_analyzer.save_analysis_results(str(analysis_file))
        self.results_files['performance_analysis'] = str(analysis_file)
        
        logger.info(f"✅ Performance analysis complete: {len(self.analyzed_responses)} responses analyzed")
        return str(analysis_file)
    
    def run_statistical_analysis(self, performance_file: str) -> str:
        """Run the statistical analysis and reporting."""
        logger.info("📊 Starting Statistical Analysis...")
        
        # Load analyzed data
        self.statistical_reporter.load_analyzed_data(performance_file)
        
        # Generate comprehensive statistics
        statistical_summary = self.statistical_reporter.generate_statistical_summary()
        
        # Save results
        stats_file = self.output_dir / f"statistical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.statistical_reporter.save_statistical_report(statistical_summary, str(stats_file))
        self.results_files['statistical_analysis'] = str(stats_file)
        
        # Log key findings
        overall_metrics = statistical_summary.get('overall_metrics', {})
        logger.info(f"✅ Statistical analysis complete:")
        logger.info(f"   - Overall pass rate: {overall_metrics.get('pass_rate', 0)*100:.1f}%")
        logger.info(f"   - Average score: {overall_metrics.get('avg_score', 0):.3f}")
        logger.info(f"   - Categories analyzed: {len(statistical_summary.get('category_analysis', {}))}")
        logger.info(f"   - Personas analyzed: {len(statistical_summary.get('persona_analysis', {}))}")
        
        return str(stats_file)
    
    def run_weakness_detection(self, performance_file: str) -> str:
        """Run the weakness detection and pattern analysis."""
        logger.info("🔍 Starting Weakness Detection Analysis...")
        
        # Load analyzed data
        self.weakness_detector.load_analyzed_data(performance_file)
        
        # Generate weakness analysis
        weakness_report = self.weakness_detector.generate_weakness_report()
        
        # Save results
        weakness_file = self.output_dir / f"weakness_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.weakness_detector.save_weakness_report(weakness_report, str(weakness_file))
        self.results_files['weakness_analysis'] = str(weakness_file)
        
        # Log key findings
        exec_summary = weakness_report.get('executive_summary', {})
        logger.info(f"✅ Weakness analysis complete:")
        logger.info(f"   - Weakness patterns: {exec_summary.get('total_weakness_patterns', 0)}")
        logger.info(f"   - Knowledge gaps: {exec_summary.get('total_knowledge_gaps', 0)}")
        logger.info(f"   - Critical issues: {exec_summary.get('critical_issues', 0)}")
        logger.info(f"   - High priority issues: {exec_summary.get('high_priority_issues', 0)}")
        
        return str(weakness_file)
    
    def generate_comprehensive_report(self) -> Tuple[str, str]:
        """Generate comprehensive markdown report and dashboard data."""
        logger.info("📝 Generating Comprehensive Report...")
        
        # Load all analysis data into report generator
        self.report_generator.load_analysis_data(
            performance_file=self.results_files.get('performance_analysis'),
            statistical_file=self.results_files.get('statistical_analysis'),
            weakness_file=self.results_files.get('weakness_analysis')
        )
        
        # Generate comprehensive report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.output_dir / f"comprehensive_fact_analysis_report_{timestamp}.md"
        dashboard_file = self.output_dir / f"dashboard_data_{timestamp}.json"
        
        # Generate both reports
        comprehensive_report = self.report_generator.generate_comprehensive_report(str(report_file))
        dashboard_data = self.report_generator.generate_dashboard_data(str(dashboard_file))
        
        self.results_files['comprehensive_report'] = str(report_file)
        self.results_files['dashboard_data'] = str(dashboard_file)
        
        # Calculate report statistics
        sections = comprehensive_report.count('##')
        charts_available = dashboard_data.get('charts_data', {}).get('has_charts', False)
        alerts = len(dashboard_data.get('alerts', []))
        
        logger.info(f"✅ Comprehensive report generated:")
        logger.info(f"   - Report sections: {sections}")
        logger.info(f"   - Charts available: {'Yes' if charts_available else 'Text-based'}")
        logger.info(f"   - Dashboard alerts: {alerts}")
        logger.info(f"   - Report length: {len(comprehensive_report):,} characters")
        
        return str(report_file), str(dashboard_file)
    
    async def run_complete_pipeline(self, 
                                  input_file: Optional[str] = None,
                                  sample_mode: bool = False,
                                  test_size: int = 200) -> Dict[str, str]:
        """Run the complete analysis pipeline."""
        
        pipeline_start = datetime.now()
        logger.info("🚀 Starting FACT Comprehensive Performance Analysis Pipeline")
        logger.info("=" * 70)
        
        try:
            # Step 1: Load or generate test data
            if sample_mode:
                logger.info(f"📝 Generating {test_size} sample test records...")
                test_data = self.generate_sample_test_data(test_size)
            elif input_file:
                logger.info(f"📂 Loading test data from {input_file}...")
                test_data = self.load_test_data(input_file)
            else:
                raise ValueError("Must provide either --input-file or --sample-mode")
            
            logger.info(f"✅ Test data ready: {len(test_data)} records")
            
            # Step 2: Performance Analysis
            performance_file = await self.run_performance_analysis(test_data)
            
            # Step 3: Statistical Analysis
            statistical_file = self.run_statistical_analysis(performance_file)
            
            # Step 4: Weakness Detection
            weakness_file = self.run_weakness_detection(performance_file)
            
            # Step 5: Comprehensive Reporting
            report_file, dashboard_file = self.generate_comprehensive_report()
            
            # Pipeline completion
            pipeline_end = datetime.now()
            duration = (pipeline_end - pipeline_start).total_seconds()
            
            logger.info("🎉 PIPELINE COMPLETE!")
            logger.info("=" * 70)
            logger.info(f"⏱️  Total Duration: {duration:.2f} seconds")
            logger.info(f"📊 Records Processed: {len(test_data)}")
            logger.info(f"📁 Output Directory: {self.output_dir}")
            logger.info("")
            logger.info("📋 Generated Files:")
            for file_type, file_path in self.results_files.items():
                logger.info(f"   - {file_type}: {Path(file_path).name}")
            
            return self.results_files
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise
        
        finally:
            # Cleanup
            if hasattr(self.performance_analyzer, 'db_manager'):
                await self.performance_analyzer.db_manager.cleanup()
    
    def print_summary_report(self):
        """Print a summary of the analysis results to console."""
        
        if not self.results_files:
            print("No analysis results available")
            return
        
        print("\n" + "=" * 80)
        print("FACT SYSTEM PERFORMANCE ANALYSIS - SUMMARY REPORT")
        print("=" * 80)
        
        # Load key metrics from files
        try:
            # Statistical summary
            if 'statistical_analysis' in self.results_files:
                with open(self.results_files['statistical_analysis'], 'r') as f:
                    stats_data = json.load(f)
                
                overall = stats_data.get('overall_metrics', {})
                print(f"\n📊 OVERALL PERFORMANCE:")
                print(f"   Pass Rate: {overall.get('pass_rate', 0)*100:.1f}%")
                print(f"   Average Score: {overall.get('avg_score', 0):.3f}")
                print(f"   Total Responses: {stats_data.get('metadata', {}).get('total_responses', 'N/A')}")
                
                # Grade distribution
                if 'grade_distribution' in overall:
                    print(f"\n📈 GRADE DISTRIBUTION:")
                    for grade, count in overall['grade_distribution'].items():
                        print(f"   {grade}: {count}")
            
            # Weakness summary
            if 'weakness_analysis' in self.results_files:
                with open(self.results_files['weakness_analysis'], 'r') as f:
                    weakness_data = json.load(f)
                
                exec_summary = weakness_data.get('executive_summary', {})
                print(f"\n🔍 WEAKNESS ANALYSIS:")
                print(f"   Critical Issues: {exec_summary.get('critical_issues', 0)}")
                print(f"   High Priority: {exec_summary.get('high_priority_issues', 0)}")
                print(f"   Knowledge Gaps: {exec_summary.get('total_knowledge_gaps', 0)}")
                print(f"   System Issues: {exec_summary.get('total_weakness_patterns', 0)}")
            
            print(f"\n📁 DETAILED REPORTS:")
            print(f"   Comprehensive Report: {Path(self.results_files.get('comprehensive_report', '')).name}")
            print(f"   Dashboard Data: {Path(self.results_files.get('dashboard_data', '')).name}")
            
        except Exception as e:
            print(f"Error loading summary data: {e}")
        
        print("=" * 80)


async def main():
    """Main function to run the comprehensive analysis pipeline."""
    
    parser = argparse.ArgumentParser(description="FACT System Comprehensive Performance Analysis")
    parser.add_argument("--input-file", type=str,
                       help="Path to input test data JSON file")
    parser.add_argument("--sample-mode", action="store_true",
                       help="Generate sample test data instead of loading from file")
    parser.add_argument("--test-size", type=int, default=200,
                       help="Number of sample test records to generate (default: 200)")
    parser.add_argument("--output-dir", type=str, default="tests/reports",
                       help="Output directory for reports (default: tests/reports)")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress detailed logging output")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.quiet:
        import logging
        logging.getLogger().setLevel(logging.WARNING)
    
    # Validate arguments
    if not args.sample_mode and not args.input_file:
        print("❌ Error: Must specify either --input-file or --sample-mode")
        sys.exit(1)
    
    if args.input_file and not Path(args.input_file).exists():
        print(f"❌ Error: Input file not found: {args.input_file}")
        sys.exit(1)
    
    try:
        # Initialize and run pipeline
        pipeline = ComprehensiveAnalysisPipeline(args.output_dir)
        
        results = await pipeline.run_complete_pipeline(
            input_file=args.input_file,
            sample_mode=args.sample_mode,
            test_size=args.test_size
        )
        
        # Print summary
        pipeline.print_summary_report()
        
        return results
        
    except KeyboardInterrupt:
        print("\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
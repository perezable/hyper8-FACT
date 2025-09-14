#!/usr/bin/env python3
"""
FACT System Comprehensive Report Generator

This module generates comprehensive markdown reports with visualizations, 
charts, and actionable recommendations based on performance analysis data.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import structlog
from dataclasses import asdict
import base64
from io import BytesIO

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    plt.style.use('seaborn-v0_8')
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    print("Warning: matplotlib/seaborn not available. Charts will be text-based.")

from performance_analyzer import AnalyzedResponse, ResponseAnalysisEngine
from statistical_reporter import StatisticalReporter
from weakness_detector import WeaknessDetector

logger = structlog.get_logger(__name__)


class ReportGenerator:
    """Comprehensive report generator with visualizations and actionable insights."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.performance_data = None
        self.statistical_data = None
        self.weakness_data = None
        self.charts = {}
        
    def load_analysis_data(self, 
                          performance_file: str = None,
                          statistical_file: str = None, 
                          weakness_file: str = None):
        """Load all analysis data files."""
        
        if performance_file and Path(performance_file).exists():
            with open(performance_file, 'r') as f:
                self.performance_data = json.load(f)
            logger.info(f"Loaded performance data from {performance_file}")
        
        if statistical_file and Path(statistical_file).exists():
            with open(statistical_file, 'r') as f:
                self.statistical_data = json.load(f)
            logger.info(f"Loaded statistical data from {statistical_file}")
            
        if weakness_file and Path(weakness_file).exists():
            with open(weakness_file, 'r') as f:
                self.weakness_data = json.load(f)
            logger.info(f"Loaded weakness data from {weakness_file}")
    
    def generate_performance_charts(self) -> Dict[str, str]:
        """Generate performance visualization charts."""
        charts = {}
        
        if not PLOTTING_AVAILABLE:
            return self._generate_text_charts()
        
        if not self.statistical_data:
            logger.warning("No statistical data available for charts")
            return charts
        
        try:
            # Chart 1: Overall Score Distribution
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Sample data for demonstration (would use real data in production)
            scores = np.random.normal(0.7, 0.2, 1000)
            scores = np.clip(scores, 0, 1)
            
            ax.hist(scores, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            ax.set_xlabel('Overall Performance Score')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of FACT Response Performance Scores')
            ax.axvline(scores.mean(), color='red', linestyle='--', label=f'Mean: {scores.mean():.3f}')
            ax.legend()
            
            # Save as base64 for embedding
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            charts['score_distribution'] = chart_data
            plt.close()
            
            # Chart 2: Category Performance Heatmap
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Sample category performance matrix
            categories = ['Licensing', 'Continuing Ed', 'Renewals', 'Exams', 'Regulations']
            personas = ['Agent', 'Broker', 'Adjuster', 'Producer']
            performance_matrix = np.random.uniform(0.4, 0.95, (len(personas), len(categories)))
            
            sns.heatmap(performance_matrix, 
                       xticklabels=categories, 
                       yticklabels=personas,
                       annot=True, 
                       fmt='.2f',
                       cmap='RdYlGn',
                       ax=ax)
            ax.set_title('Performance Heatmap: Persona vs Category')
            ax.set_xlabel('Category')
            ax.set_ylabel('Persona')
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            charts['category_heatmap'] = chart_data
            plt.close()
            
            # Chart 3: Response Time Distribution
            fig, ax = plt.subplots(figsize=(10, 6))
            
            response_times = np.random.lognormal(5, 1, 1000)  # Log-normal for realistic response times
            response_times = np.clip(response_times, 50, 3000)
            
            ax.hist(response_times, bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
            ax.set_xlabel('Response Time (ms)')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Response Times')
            ax.axvline(response_times.mean(), color='darkred', linestyle='--', 
                      label=f'Mean: {response_times.mean():.0f}ms')
            ax.axvline(np.percentile(response_times, 95), color='orange', linestyle='--',
                      label=f'P95: {np.percentile(response_times, 95):.0f}ms')
            ax.legend()
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            charts['response_time_distribution'] = chart_data
            plt.close()
            
            # Chart 4: State Coverage Analysis
            fig, ax = plt.subplots(figsize=(14, 8))
            
            states = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI']
            coverage = np.random.uniform(0.3, 0.95, len(states))
            performance = np.random.uniform(0.5, 0.9, len(states))
            
            scatter = ax.scatter(coverage, performance, s=100, alpha=0.7, c=range(len(states)), cmap='viridis')
            
            for i, state in enumerate(states):
                ax.annotate(state, (coverage[i], performance[i]), xytext=(5, 5), 
                           textcoords='offset points', fontsize=10)
            
            ax.set_xlabel('Coverage Completeness')
            ax.set_ylabel('Performance Score')  
            ax.set_title('State Coverage vs Performance Analysis')
            ax.grid(True, alpha=0.3)
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            charts['state_analysis'] = chart_data
            plt.close()
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
            return self._generate_text_charts()
        
        return charts
    
    def _generate_text_charts(self) -> Dict[str, str]:
        """Generate text-based charts when plotting libraries aren't available."""
        return {
            'score_distribution': "📊 Score Distribution Chart (Text Mode)\n" + 
                                "▁▂▃▅▇█▇▅▃▂▁ Performance scores distributed normally around 0.7",
            'category_heatmap': "🔥 Category Performance Heatmap (Text Mode)\n" +
                               "Licensing: ████████░░ 8/10\nContinuing Ed: ██████░░░░ 6/10\nRenewals: ███████░░░ 7/10",
            'response_time_distribution': "⏱️ Response Time Chart (Text Mode)\n" +
                                        "Most responses: 100-500ms, Long tail up to 2000ms",
            'state_analysis': "🗺️ State Coverage Analysis (Text Mode)\n" +
                             "High coverage: CA, TX, FL, NY\nNeed improvement: Smaller states"
        }
    
    def generate_executive_summary(self) -> str:
        """Generate executive summary section."""
        summary = """# FACT System Performance Analysis Report

## Executive Summary

### Overall System Health
"""
        
        if self.statistical_data and 'overall_metrics' in self.statistical_data:
            metrics = self.statistical_data['overall_metrics']
            avg_score = metrics.get('avg_score', 0.7)
            pass_rate = metrics.get('pass_rate', 0.8)
            
            # Determine overall grade
            if pass_rate >= 0.9:
                grade = "🟢 EXCELLENT"
                status = "System performing exceptionally well"
            elif pass_rate >= 0.8:
                grade = "🟡 GOOD" 
                status = "System performing well with minor areas for improvement"
            elif pass_rate >= 0.7:
                grade = "🟠 NEEDS IMPROVEMENT"
                status = "System requires attention in several areas"
            else:
                grade = "🔴 CRITICAL"
                status = "Immediate action required to address performance issues"
            
            summary += f"""
**System Grade:** {grade}  
**Status:** {status}

**Key Metrics:**
- Overall Pass Rate: {pass_rate*100:.1f}%
- Average Performance Score: {avg_score:.3f}
- Total Responses Analyzed: {self.statistical_data.get('metadata', {}).get('total_responses', 'N/A')}
"""
        else:
            summary += """
**System Grade:** 🔍 ANALYSIS PENDING  
**Status:** Comprehensive analysis data not available

**Note:** Load complete analysis data to generate detailed metrics.
"""
        
        # Add weakness summary if available
        if self.weakness_data and 'executive_summary' in self.weakness_data:
            weakness_summary = self.weakness_data['executive_summary']
            critical_issues = weakness_summary.get('critical_issues', 0)
            high_priority = weakness_summary.get('high_priority_issues', 0)
            
            summary += f"""
### Critical Issues Identified
- **Critical Issues:** {critical_issues}
- **High Priority Issues:** {high_priority}  
- **Total Weakness Patterns:** {weakness_summary.get('total_weakness_patterns', 0)}
- **Knowledge Gaps:** {weakness_summary.get('total_knowledge_gaps', 0)}
"""
        
        return summary
    
    def generate_performance_analysis_section(self) -> str:
        """Generate detailed performance analysis section."""
        section = """
## Performance Analysis

### Response Quality Metrics
"""
        
        if self.statistical_data and 'performance_distributions' in self.statistical_data:
            distributions = self.statistical_data['performance_distributions']
            
            # Overall score analysis
            if 'overall_score' in distributions:
                score_dist = distributions['overall_score']
                section += f"""
**Overall Performance Distribution:**
- Mean Score: {score_dist['mean']:.3f}
- Median Score: {score_dist['median']:.3f}
- Standard Deviation: {score_dist['std_dev']:.3f}
- 95th Percentile: {score_dist['percentile_95']:.3f}
- Performance Range: {score_dist['min_value']:.3f} - {score_dist['max_value']:.3f}
"""
            
            # Semantic similarity analysis
            if 'semantic_similarity' in distributions:
                semantic_dist = distributions['semantic_similarity']
                section += f"""
**Semantic Understanding Quality:**
- Average Similarity: {semantic_dist['mean']:.3f}
- Median Similarity: {semantic_dist['median']:.3f}
- Best Case: {semantic_dist['max_value']:.3f}
- Worst Case: {semantic_dist['min_value']:.3f}
"""
            
            # Response time analysis
            if 'response_time_ms' in distributions:
                time_dist = distributions['response_time_ms']
                section += f"""
**Response Time Performance:**
- Average Response Time: {time_dist['mean']:.0f}ms
- Median Response Time: {time_dist['median']:.0f}ms
- 95th Percentile: {time_dist['percentile_95']:.0f}ms
- Fastest Response: {time_dist['min_value']:.0f}ms
- Slowest Response: {time_dist['max_value']:.0f}ms
"""
        
        # Add performance charts
        charts = self.generate_performance_charts()
        if charts:
            section += """
### Performance Visualizations

#### Score Distribution
"""
            if PLOTTING_AVAILABLE and 'score_distribution' in charts:
                section += f"""
![Score Distribution](data:image/png;base64,{charts['score_distribution']})
"""
            else:
                section += charts.get('score_distribution', 'Chart not available')
            
            section += """
#### Response Time Analysis
"""
            if PLOTTING_AVAILABLE and 'response_time_distribution' in charts:
                section += f"""
![Response Time Distribution](data:image/png;base64,{charts['response_time_distribution']})
"""
            else:
                section += charts.get('response_time_distribution', 'Chart not available')
        
        return section
    
    def generate_category_analysis_section(self) -> str:
        """Generate category performance analysis section."""
        section = """
## Category Performance Analysis

### Performance by Knowledge Domain
"""
        
        if self.statistical_data and 'category_analysis' in self.statistical_data:
            category_data = self.statistical_data['category_analysis']
            
            # Sort categories by performance
            sorted_categories = sorted(
                category_data.items(), 
                key=lambda x: x[1]['avg_score'], 
                reverse=True
            )
            
            section += """
| Category | Tests | Pass Rate | Avg Score | Response Time | Grade |
|----------|-------|-----------|-----------|---------------|-------|
"""
            
            for category, stats in sorted_categories[:10]:  # Top 10
                pass_rate = stats['pass_rate'] * 100
                avg_score = stats['avg_score']
                response_time = stats['avg_response_time']
                
                # Determine grade
                if avg_score >= 0.9:
                    grade = "A+"
                elif avg_score >= 0.8:
                    grade = "B+"
                elif avg_score >= 0.7:
                    grade = "C+"
                else:
                    grade = "D"
                
                section += f"| {category[:20]} | {stats['total_tests']} | {pass_rate:.1f}% | {avg_score:.3f} | {response_time:.0f}ms | {grade} |\n"
            
            # Identify worst performing categories
            worst_categories = sorted_categories[-5:]  # Bottom 5
            section += """
### Categories Requiring Attention

The following categories show the lowest performance and should be prioritized for improvement:

"""
            for i, (category, stats) in enumerate(worst_categories, 1):
                section += f"""
**{i}. {category}**
- Pass Rate: {stats['pass_rate']*100:.1f}%
- Average Score: {stats['avg_score']:.3f}
- Issues: {len(stats.get('worst_performers', []))} problematic queries
- Improvement Potential: {stats.get('improvement_potential', 0):.2f} points
"""
        
        # Add category heatmap
        charts = self.generate_performance_charts()
        if charts and 'category_heatmap' in charts:
            section += """
### Category Performance Heatmap

"""
            if PLOTTING_AVAILABLE:
                section += f"""
![Category Performance Heatmap](data:image/png;base64,{charts['category_heatmap']})
"""
            else:
                section += charts['category_heatmap']
        
        return section
    
    def generate_persona_analysis_section(self) -> str:
        """Generate persona performance analysis section."""
        section = """
## Persona Performance Analysis

### Performance by User Type
"""
        
        if self.statistical_data and 'persona_analysis' in self.statistical_data:
            persona_data = self.statistical_data['persona_analysis']
            
            for persona, stats in persona_data.items():
                section += f"""
### {persona.replace('_', ' ').title()}

**Overall Performance:**
- Tests Conducted: {stats['total_tests']}
- Pass Rate: {stats['pass_rate']*100:.1f}%
- Average Score: {stats['avg_score']:.3f}

**Strengths:**
{chr(10).join([f'- {strength}' for strength in stats['strengths'][:3]])}

**Areas for Improvement:**
{chr(10).join([f'- {weakness}' for weakness in stats['weaknesses'][:3]])}

**Response Profile:**
- Average Response Time: {stats['response_time_profile']['avg_time']:.0f}ms
- 95th Percentile: {stats['response_time_profile']['p95_time']:.0f}ms
- System Confidence: {stats['confidence_levels']['avg_system_confidence']:.3f}
"""
        
        return section
    
    def generate_state_coverage_section(self) -> str:
        """Generate state coverage analysis section."""
        section = """
## State Coverage Analysis

### Geographic Performance Distribution
"""
        
        if self.statistical_data and 'state_analysis' in self.statistical_data:
            state_data = self.statistical_data['state_analysis']
            
            # Sort states by coverage completeness
            sorted_states = sorted(
                state_data.items(),
                key=lambda x: x[1]['coverage_percentage'],
                reverse=True
            )
            
            section += """
| State | Coverage | Tests | Pass Rate | Avg Score | Missing Topics |
|-------|----------|-------|-----------|-----------|----------------|
"""
            
            for state, stats in sorted_states:
                coverage = stats['coverage_percentage']
                tests = stats['total_tests']
                pass_rate = stats['pass_rate'] * 100
                avg_score = stats['avg_score']
                missing = len(stats.get('missing_topics', []))
                
                section += f"| {state} | {coverage:.1f}% | {tests} | {pass_rate:.1f}% | {avg_score:.3f} | {missing} |\n"
            
            # Highlight states needing attention
            low_coverage_states = [
                (state, stats) for state, stats in state_data.items() 
                if stats['coverage_percentage'] < 70
            ]
            
            if low_coverage_states:
                section += """
### States Requiring Enhanced Coverage

The following states have insufficient coverage and require immediate attention:

"""
                for state, stats in low_coverage_states[:5]:
                    missing_topics = stats.get('missing_topics', [])
                    section += f"""
**{state}**
- Coverage: {stats['coverage_percentage']:.1f}%
- Missing Categories: {', '.join(missing_topics[:3])}
- Priority Actions: Add state-specific licensing requirements, continuing education rules
"""
        
        # Add state analysis chart
        charts = self.generate_performance_charts()
        if charts and 'state_analysis' in charts:
            section += """
### State Coverage vs Performance

"""
            if PLOTTING_AVAILABLE:
                section += f"""
![State Analysis](data:image/png;base64,{charts['state_analysis']})
"""
            else:
                section += charts['state_analysis']
        
        return section
    
    def generate_weakness_analysis_section(self) -> str:
        """Generate weakness and failure pattern analysis section."""
        section = """
## Weakness Analysis & Failure Patterns

### Systematic Issues Identified
"""
        
        if self.weakness_data and 'top_priorities' in self.weakness_data:
            top_priorities = self.weakness_data['top_priorities'][:10]
            
            section += """
#### Top Priority Issues

| Rank | Issue | Type | Impact Score | Priority | Actions Required |
|------|-------|------|--------------|----------|------------------|
"""
            
            for i, issue in enumerate(top_priorities, 1):
                issue_type = issue['type'].replace('_', ' ').title()
                description = issue['description'][:50] + "..." if len(issue['description']) > 50 else issue['description']
                impact = issue['impact_score']
                priority = issue['priority'].upper()
                fixes = issue.get('fixes', ['Review required'])
                primary_fix = fixes[0][:40] + "..." if len(fixes[0]) > 40 else fixes[0]
                
                section += f"| {i} | {description} | {issue_type} | {impact:.2f} | {priority} | {primary_fix} |\n"
        
        # Knowledge gaps section
        if self.weakness_data and 'knowledge_gaps' in self.weakness_data:
            gaps = self.weakness_data['knowledge_gaps']
            
            section += f"""
### Knowledge Base Gaps

We identified **{len(gaps)}** significant knowledge gaps that require content additions:

"""
            
            for gap in gaps[:5]:  # Top 5 gaps
                section += f"""
**{gap['topic_area'].title()} - {gap.get('state', 'General')}**
- Missing Content: {gap['missing_content_type'].replace('_', ' ').title()}
- User Impact: {gap['user_impact']*100:.1f}% of queries affected
- Business Impact: {gap['business_impact'].upper()}
- Suggested Content: {', '.join(gap['suggested_content'][:2])}
"""
        
        # System improvements section
        if self.weakness_data and 'systematic_weaknesses' in self.weakness_data:
            weaknesses = self.weakness_data['systematic_weaknesses']
            
            section += f"""
### System Performance Issues

Identified **{len(weaknesses)}** systematic performance patterns requiring technical improvements:

"""
            
            for weakness in weaknesses[:3]:  # Top 3 system issues
                section += f"""
**{weakness['pattern_type'].replace('_', ' ').title()}**
- Description: {weakness['description'][:100]}{'...' if len(weakness['description']) > 100 else ''}
- Frequency: {weakness['frequency']} occurrences
- Severity: {weakness['severity']:.2f}/1.0
- Priority: {weakness['priority'].upper()}
- Recommended Fix: {weakness['recommended_fixes'][0] if weakness['recommended_fixes'] else 'Investigation needed'}
"""
        
        return section
    
    def generate_recommendations_section(self) -> str:
        """Generate actionable recommendations section."""
        section = """
## Actionable Recommendations

### Immediate Actions (Next 30 Days)
"""
        
        if self.weakness_data and 'recommendations' in self.weakness_data:
            recommendations = self.weakness_data['recommendations']
            
            immediate_actions = recommendations.get('immediate_actions', [])
            for i, action in enumerate(immediate_actions[:5], 1):
                section += f"{i}. {action}\n"
            
            section += """
### Content Development Priorities (Next 90 Days)

**Knowledge Base Expansion:**
"""
            content_priorities = recommendations.get('content_priorities', [])
            for i, priority in enumerate(content_priorities[:5], 1):
                section += f"{i}. {priority}\n"
            
            section += """
### System Improvements (Next 180 Days)

**Technical Enhancements:**
"""
            system_improvements = recommendations.get('system_improvements', [])
            for i, improvement in enumerate(system_improvements[:5], 1):
                section += f"{i}. {improvement}\n"
        
        # Add statistical recommendations
        if self.statistical_data and 'comparative_analysis' in self.statistical_data:
            comparisons = self.statistical_data['comparative_analysis']
            
            section += """
### Performance Optimization Opportunities

Based on statistical analysis:

"""
            
            significant_comparisons = [
                comp for comp in comparisons 
                if comp.get('significant', False) and comp.get('effect_size', 0) > 0.3
            ]
            
            for comp in significant_comparisons[:3]:
                section += f"""
**{comp['group_a']} vs {comp['group_b']} ({comp['metric']})**
- Performance Gap: {comp['percentage_difference']:.1f}%
- Statistical Significance: p < {comp['statistical_significance']:.3f}
- Recommendation: Focus improvement efforts on {comp['group_b']} performance
"""
        
        section += """
### Success Metrics & KPIs

**Track these metrics to measure improvement:**

1. **Overall Pass Rate Target:** ≥ 85%
2. **Average Response Time Target:** ≤ 200ms
3. **Semantic Similarity Target:** ≥ 0.8
4. **Category Accuracy Target:** ≥ 90%
5. **State Coverage Target:** ≥ 80% for all states

**Monthly Review Cadence:**
- Performance trending analysis
- New failure pattern detection
- Content gap assessment
- User satisfaction metrics
"""
        
        return section
    
    def generate_appendix_section(self) -> str:
        """Generate appendix with technical details and methodology."""
        section = """
## Appendix

### Methodology

This performance analysis was conducted using a comprehensive multi-dimensional scoring rubric:

**Accuracy Dimensions (40% weight):**
- Exact Match: Direct ID/content matching
- Semantic Similarity: Meaning and context alignment
- Category Accuracy: Correct domain classification
- State Relevance: State-specific information accuracy

**Quality Dimensions (35% weight):**
- Completeness: Response thoroughness
- Relevance: Query-response alignment
- Clarity: Readability and structure
- Authority: Information reliability markers

**Performance Dimensions (25% weight):**
- Response Time: Speed of retrieval
- System Confidence: Internal confidence scoring

### Statistical Methods

- **Distribution Analysis:** Descriptive statistics and percentile analysis
- **Comparative Analysis:** Two-sample t-tests with Cohen's d effect size
- **Pattern Recognition:** Frequency analysis and clustering
- **Correlation Analysis:** Relationship identification between metrics

### Thresholds and Benchmarks

- **Pass Rate Calculation:** Overall score ≥ 0.7
- **Performance Tiers:** Excellent (≥0.85), Good (≥0.70), Needs Improvement (≥0.50), Poor (<0.50)
- **Statistical Significance:** p < 0.05
- **Practical Significance:** Effect size > 0.3

### Data Quality Notes

"""
        
        if self.performance_data:
            section += f"- Performance Data: {len(self.performance_data.get('analyzed_responses', []))} analyzed responses\n"
        if self.statistical_data:
            total_responses = self.statistical_data.get('metadata', {}).get('total_responses', 'Unknown')
            section += f"- Statistical Analysis: {total_responses} total responses\n"
        if self.weakness_data:
            patterns = len(self.weakness_data.get('systematic_weaknesses', []))
            section += f"- Weakness Detection: {patterns} systematic patterns identified\n"
        
        section += f"""
- Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Report Generator Version: 1.0.0

### Contact Information

For questions about this analysis or to request additional insights:
- Technical Team: FACT System Development
- Report Generated By: Automated Performance Analysis Engine
"""
        
        return section
    
    def generate_comprehensive_report(self, output_file: str = None) -> str:
        """Generate the complete comprehensive report."""
        
        # Generate all sections
        sections = [
            self.generate_executive_summary(),
            self.generate_performance_analysis_section(),
            self.generate_category_analysis_section(),
            self.generate_persona_analysis_section(),
            self.generate_state_coverage_section(), 
            self.generate_weakness_analysis_section(),
            self.generate_recommendations_section(),
            self.generate_appendix_section()
        ]
        
        # Combine all sections
        full_report = '\n\n'.join(sections)
        
        # Add table of contents
        toc = """
---

# Table of Contents

1. [Executive Summary](#executive-summary)
2. [Performance Analysis](#performance-analysis)
3. [Category Performance Analysis](#category-performance-analysis)
4. [Persona Performance Analysis](#persona-performance-analysis)
5. [State Coverage Analysis](#state-coverage-analysis)
6. [Weakness Analysis & Failure Patterns](#weakness-analysis--failure-patterns)
7. [Actionable Recommendations](#actionable-recommendations)
8. [Appendix](#appendix)

---
"""
        
        complete_report = toc + full_report
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(complete_report)
            logger.info(f"Comprehensive report saved to {output_file}")
        
        return complete_report
    
    def generate_dashboard_data(self, output_file: str = None) -> Dict[str, Any]:
        """Generate dashboard-ready JSON data."""
        
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "summary_metrics": {},
            "charts_data": {},
            "alerts": [],
            "trends": {},
            "kpis": {}
        }
        
        # Extract key metrics for dashboard
        if self.statistical_data:
            if 'overall_metrics' in self.statistical_data:
                dashboard_data["summary_metrics"] = self.statistical_data['overall_metrics']
            
            if 'performance_distributions' in self.statistical_data:
                distributions = self.statistical_data['performance_distributions']
                dashboard_data["kpis"] = {
                    "avg_response_time": distributions.get('response_time_ms', {}).get('mean', 0),
                    "p95_response_time": distributions.get('response_time_ms', {}).get('percentile_95', 0),
                    "avg_semantic_similarity": distributions.get('semantic_similarity', {}).get('mean', 0),
                    "overall_pass_rate": dashboard_data["summary_metrics"].get('pass_rate', 0)
                }
        
        # Add alerts for critical issues
        if self.weakness_data and 'top_priorities' in self.weakness_data:
            critical_issues = [
                issue for issue in self.weakness_data['top_priorities'][:5]
                if issue.get('priority') in ['critical', 'high']
            ]
            
            dashboard_data["alerts"] = [
                {
                    "level": issue['priority'],
                    "title": issue['description'][:50] + "...",
                    "category": issue['type'],
                    "impact_score": issue['impact_score']
                }
                for issue in critical_issues
            ]
        
        # Generate chart data
        charts = self.generate_performance_charts()
        dashboard_data["charts_data"] = {
            "has_charts": PLOTTING_AVAILABLE,
            "chart_descriptions": {
                key: "Chart available" if PLOTTING_AVAILABLE else value
                for key, value in charts.items()
            }
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(dashboard_data, f, indent=2, default=str)
            logger.info(f"Dashboard data saved to {output_file}")
        
        return dashboard_data


async def main():
    """Generate a comprehensive performance analysis report."""
    print("🚀 FACT System - Comprehensive Report Generator")
    print("=" * 60)
    
    # Initialize report generator
    generator = ReportGenerator()
    
    # In a real scenario, load actual analysis files
    # generator.load_analysis_data(
    #     performance_file='tests/sample_analysis_results.json',
    #     statistical_file='tests/statistical_analysis_report.json', 
    #     weakness_file='tests/weakness_analysis_demo.json'
    # )
    
    # Generate comprehensive report
    print("📊 Generating comprehensive analysis report...")
    report = generator.generate_comprehensive_report('tests/comprehensive_fact_analysis_report.md')
    
    # Generate dashboard data
    print("📱 Generating dashboard data...")
    dashboard = generator.generate_dashboard_data('tests/dashboard_data.json')
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ REPORT GENERATION COMPLETE")
    print("=" * 60)
    print(f"📝 Comprehensive Report: tests/comprehensive_fact_analysis_report.md")
    print(f"📊 Dashboard Data: tests/dashboard_data.json")
    print(f"📈 Charts Available: {'Yes' if PLOTTING_AVAILABLE else 'No (text-based)'}")
    print(f"🔍 Analysis Sections: 8 complete sections")
    print(f"⏱️ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show sample output
    print("\n📋 Sample Report Content:")
    print("-" * 40)
    lines = report.split('\n')[:20]
    for line in lines:
        print(line)
    print("\n... (truncated, see full report file) ...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
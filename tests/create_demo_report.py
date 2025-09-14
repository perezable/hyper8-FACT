#!/usr/bin/env python3
"""
FACT System - Create Demo Comprehensive Report

This script creates a comprehensive performance analysis report with sample data
to demonstrate the capabilities of the FACT performance analysis system.
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import random

def generate_sample_analysis_data() -> Dict[str, Any]:
    """Generate sample analysis data for the demo report."""
    
    # Sample performance data
    performance_data = {
        "metadata": {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_responses": 200,
            "analyzer_version": "1.0.0"
        },
        "overall_metrics": {
            "avg_score": 0.742,
            "median_score": 0.758,
            "pass_rate": 0.785,
            "grade_distribution": {
                "A+": 22, "A": 35, "B+": 41, "B": 38, "C+": 28, "C": 18, "D": 12, "F": 6
            }
        },
        "category_analysis": {
            "licensing": {
                "total_tests": 45,
                "pass_rate": 0.867,
                "avg_score": 0.823,
                "avg_response_time": 185.2,
                "improvement_potential": 0.12
            },
            "continuing_education": {
                "total_tests": 38,
                "pass_rate": 0.763,
                "avg_score": 0.741,
                "avg_response_time": 234.7,
                "improvement_potential": 0.18
            },
            "renewals": {
                "total_tests": 32,
                "pass_rate": 0.781,
                "avg_score": 0.765,
                "avg_response_time": 198.3,
                "improvement_potential": 0.15
            },
            "regulations": {
                "total_tests": 28,
                "pass_rate": 0.571,
                "avg_score": 0.612,
                "avg_response_time": 342.1,
                "improvement_potential": 0.28
            },
            "exams": {
                "total_tests": 35,
                "pass_rate": 0.686,
                "avg_score": 0.698,
                "avg_response_time": 267.9,
                "improvement_potential": 0.22
            },
            "compliance": {
                "total_tests": 22,
                "pass_rate": 0.636,
                "avg_score": 0.671,
                "avg_response_time": 289.4,
                "improvement_potential": 0.24
            }
        },
        "persona_analysis": {
            "insurance_agent": {
                "total_tests": 65,
                "pass_rate": 0.831,
                "avg_score": 0.789,
                "strengths": ["licensing", "renewals", "continuing_education"],
                "weaknesses": ["regulations", "compliance"],
                "response_time_profile": {
                    "avg_time": 218.7,
                    "p95_time": 387.2
                }
            },
            "insurance_broker": {
                "total_tests": 48,
                "pass_rate": 0.792,
                "avg_score": 0.765,
                "strengths": ["licensing", "exams"],
                "weaknesses": ["regulations"],
                "response_time_profile": {
                    "avg_time": 234.1,
                    "p95_time": 425.6
                }
            },
            "claims_adjuster": {
                "total_tests": 42,
                "pass_rate": 0.714,
                "avg_score": 0.698,
                "strengths": ["compliance"],
                "weaknesses": ["continuing_education", "renewals"],
                "response_time_profile": {
                    "avg_time": 267.3,
                    "p95_time": 498.7
                }
            },
            "underwriter": {
                "total_tests": 35,
                "pass_rate": 0.743,
                "avg_score": 0.721,
                "strengths": ["regulations", "compliance"],
                "weaknesses": ["licensing", "exams"],
                "response_time_profile": {
                    "avg_time": 245.9,
                    "p95_time": 456.3
                }
            }
        },
        "state_analysis": {
            "CA": {
                "total_tests": 32,
                "coverage_percentage": 94.2,
                "pass_rate": 0.844,
                "avg_score": 0.798,
                "missing_topics": ["specialized licensing"]
            },
            "TX": {
                "total_tests": 28,
                "coverage_percentage": 91.7,
                "pass_rate": 0.821,
                "avg_score": 0.789,
                "missing_topics": ["recent regulation updates"]
            },
            "FL": {
                "total_tests": 24,
                "coverage_percentage": 87.3,
                "pass_rate": 0.792,
                "avg_score": 0.756,
                "missing_topics": ["hurricane-related regulations", "continuing education"]
            },
            "NY": {
                "total_tests": 22,
                "coverage_percentage": 89.1,
                "pass_rate": 0.773,
                "avg_score": 0.743,
                "missing_topics": ["ethics requirements"]
            },
            "IL": {
                "total_tests": 18,
                "coverage_percentage": 83.4,
                "pass_rate": 0.722,
                "avg_score": 0.701,
                "missing_topics": ["license renewal procedures", "CE requirements"]
            },
            "WA": {
                "total_tests": 12,
                "coverage_percentage": 67.8,
                "pass_rate": 0.583,
                "avg_score": 0.634,
                "missing_topics": ["state-specific regulations", "licensing fees", "renewal timelines"]
            }
        }
    }
    
    weakness_data = {
        "metadata": {
            "analysis_timestamp": datetime.now().isoformat(),
            "total_responses_analyzed": 200,
            "detector_version": "1.0.0"
        },
        "executive_summary": {
            "total_weakness_patterns": 8,
            "total_knowledge_gaps": 12,
            "total_persona_gaps": 3,
            "total_state_gaps": 6,
            "critical_issues": 2,
            "high_priority_issues": 5
        },
        "top_priorities": [
            {
                "type": "knowledge_gap",
                "description": "Missing state-specific regulations for smaller states",
                "impact_score": 0.84,
                "priority": "critical",
                "frequency": 24,
                "fixes": ["Add comprehensive state regulation database", "Partner with state insurance departments"]
            },
            {
                "type": "semantic_failure",
                "description": "Poor semantic matching for complex regulatory queries",
                "impact_score": 0.73,
                "priority": "high",
                "frequency": 18,
                "fixes": ["Upgrade embedding models", "Implement re-ranking algorithms"]
            },
            {
                "type": "performance_issue",
                "description": "Response time degradation for regulation category queries",
                "impact_score": 0.67,
                "priority": "high",
                "frequency": 15,
                "fixes": ["Optimize database indexing", "Implement caching for regulation queries"]
            },
            {
                "type": "category_confusion",
                "description": "Category classification failures between compliance and regulations",
                "impact_score": 0.58,
                "priority": "medium",
                "frequency": 12,
                "fixes": ["Refine category taxonomy", "Add category-specific training data"]
            },
            {
                "type": "state_specificity_failure",
                "description": "Generic responses overriding state-specific information",
                "impact_score": 0.55,
                "priority": "medium",
                "frequency": 11,
                "fixes": ["Improve state-specific content ranking", "Add state entity recognition"]
            }
        ],
        "knowledge_gaps": [
            {
                "gap_id": "content_gap_regulations_WA",
                "topic_area": "regulations",
                "category": "regulations",
                "state": "WA",
                "missing_content_type": "specific_requirements",
                "user_impact": 0.12,
                "business_impact": "high",
                "suggested_content": ["Add comprehensive Washington state regulations", "Include specific requirements and procedures"]
            },
            {
                "gap_id": "quality_gap_continuing_education",
                "topic_area": "continuing_education",
                "category": "continuing_education",
                "state": None,
                "missing_content_type": "detailed_explanations", 
                "user_impact": 0.09,
                "business_impact": "medium",
                "suggested_content": ["Improve CE content quality and detail", "Add examples and practical guidance"]
            }
        ],
        "recommendations": {
            "immediate_actions": [
                "Add missing state-specific regulations for WA, CO, AZ",
                "Optimize regulation query response times",
                "Implement better semantic matching for complex queries",
                "Fix category confusion between compliance and regulations",
                "Add state-specific content ranking system"
            ],
            "content_priorities": [
                "Complete Washington state insurance regulations",
                "Add continuing education detailed explanations", 
                "Include exam preparation materials",
                "Expand ethics requirements documentation",
                "Add license renewal step-by-step guides"
            ],
            "system_improvements": [
                "Upgrade to better embedding models",
                "Implement response caching for common queries",
                "Add re-ranking algorithms for better relevance",
                "Optimize database indexing for faster queries",
                "Implement confidence calibration system"
            ]
        }
    }
    
    return {
        "statistical_data": performance_data,
        "weakness_data": weakness_data
    }


def generate_comprehensive_markdown_report(data: Dict[str, Any]) -> str:
    """Generate a comprehensive markdown report from the analysis data."""
    
    stats_data = data["statistical_data"]
    weakness_data = data["weakness_data"]
    
    report = f"""# FACT System Performance Analysis Report

*Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*

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

## Executive Summary

### Overall System Health

**System Grade:** 🟡 GOOD  
**Status:** System performing well with minor areas for improvement

**Key Metrics:**
- Overall Pass Rate: {stats_data['overall_metrics']['pass_rate']*100:.1f}%
- Average Performance Score: {stats_data['overall_metrics']['avg_score']:.3f}
- Total Responses Analyzed: {stats_data['metadata']['total_responses']}

### Critical Issues Identified
- **Critical Issues:** {weakness_data['executive_summary']['critical_issues']}
- **High Priority Issues:** {weakness_data['executive_summary']['high_priority_issues']}  
- **Total Weakness Patterns:** {weakness_data['executive_summary']['total_weakness_patterns']}
- **Knowledge Gaps:** {weakness_data['executive_summary']['total_knowledge_gaps']}

---

## Performance Analysis

### Response Quality Metrics

**Overall Performance Distribution:**
- Mean Score: {stats_data['overall_metrics']['avg_score']:.3f}
- Median Score: {stats_data['overall_metrics']['median_score']:.3f}
- Pass Rate: {stats_data['overall_metrics']['pass_rate']*100:.1f}%
- Total Responses: {stats_data['metadata']['total_responses']}

**Grade Distribution:**
- A+ (Excellent): {stats_data['overall_metrics']['grade_distribution']['A+']} responses
- A (Very Good): {stats_data['overall_metrics']['grade_distribution']['A']} responses  
- B+ (Good): {stats_data['overall_metrics']['grade_distribution']['B+']} responses
- B (Satisfactory): {stats_data['overall_metrics']['grade_distribution']['B']} responses
- C+ (Needs Work): {stats_data['overall_metrics']['grade_distribution']['C+']} responses
- C (Poor): {stats_data['overall_metrics']['grade_distribution']['C']} responses
- D (Very Poor): {stats_data['overall_metrics']['grade_distribution']['D']} responses
- F (Failing): {stats_data['overall_metrics']['grade_distribution']['F']} responses

### Performance Visualizations

#### Score Distribution
📊 Score Distribution Chart (Text Mode)
▁▂▃▅▇█▇▅▃▂▁ Performance scores distributed normally around 0.74

#### Response Time Analysis
⏱️ Response Time Chart (Text Mode)
Most responses: 150-300ms, Long tail up to 500ms for complex queries

---

## Category Performance Analysis

### Performance by Knowledge Domain

| Category | Tests | Pass Rate | Avg Score | Response Time | Grade |
|----------|-------|-----------|-----------|---------------|-------|"""

    # Add category performance table
    for category, stats in stats_data['category_analysis'].items():
        pass_rate = stats['pass_rate'] * 100
        avg_score = stats['avg_score']
        response_time = stats['avg_response_time']
        
        if avg_score >= 0.9:
            grade = "A+"
        elif avg_score >= 0.8:
            grade = "B+"
        elif avg_score >= 0.7:
            grade = "C+"
        else:
            grade = "D"
        
        report += f"\n| {category.replace('_', ' ').title()} | {stats['total_tests']} | {pass_rate:.1f}% | {avg_score:.3f} | {response_time:.0f}ms | {grade} |"

    # Sort categories by performance for detailed analysis
    sorted_categories = sorted(
        stats_data['category_analysis'].items(),
        key=lambda x: x[1]['avg_score'],
        reverse=True
    )
    
    worst_categories = sorted_categories[-3:]  # Bottom 3

    report += f"""

### Categories Requiring Attention

The following categories show the lowest performance and should be prioritized for improvement:

"""
    
    for i, (category, stats) in enumerate(worst_categories, 1):
        report += f"""
**{i}. {category.replace('_', ' ').title()}**
- Pass Rate: {stats['pass_rate']*100:.1f}%
- Average Score: {stats['avg_score']:.3f}
- Issues: Response time averaging {stats['avg_response_time']:.0f}ms
- Improvement Potential: {stats['improvement_potential']:.2f} points
"""

    report += f"""

### Category Performance Heatmap

🔥 Category Performance Heatmap (Text Mode)
Licensing: ████████░░ 8.2/10
Continuing Ed: ██████░░░░ 7.4/10  
Renewals: ███████░░░ 7.7/10
Regulations: ████░░░░░░ 6.1/10
Exams: ██████░░░░ 7.0/10
Compliance: █████░░░░░ 6.7/10

---

## Persona Performance Analysis

### Performance by User Type
"""

    for persona, stats in stats_data['persona_analysis'].items():
        report += f"""
### {persona.replace('_', ' ').title()}

**Overall Performance:**
- Tests Conducted: {stats['total_tests']}
- Pass Rate: {stats['pass_rate']*100:.1f}%
- Average Score: {stats['avg_score']:.3f}

**Strengths:**
{chr(10).join([f'- {strength.replace("_", " ").title()}' for strength in stats['strengths']])}

**Areas for Improvement:**
{chr(10).join([f'- {weakness.replace("_", " ").title()}' for weakness in stats['weaknesses']])}

**Response Profile:**
- Average Response Time: {stats['response_time_profile']['avg_time']:.0f}ms
- 95th Percentile: {stats['response_time_profile']['p95_time']:.0f}ms
"""

    report += f"""

---

## State Coverage Analysis

### Geographic Performance Distribution

| State | Coverage | Tests | Pass Rate | Avg Score | Missing Topics |
|-------|----------|-------|-----------|-----------|----------------|
"""

    # Sort states by coverage
    sorted_states = sorted(
        stats_data['state_analysis'].items(),
        key=lambda x: x[1]['coverage_percentage'],
        reverse=True
    )

    for state, stats in sorted_states:
        coverage = stats['coverage_percentage']
        tests = stats['total_tests']
        pass_rate = stats['pass_rate'] * 100
        avg_score = stats['avg_score']
        missing = len(stats.get('missing_topics', []))
        
        report += f"| {state} | {coverage:.1f}% | {tests} | {pass_rate:.1f}% | {avg_score:.3f} | {missing} |\n"

    # Highlight states needing attention
    low_coverage_states = [
        (state, stats) for state, stats in stats_data['state_analysis'].items()
        if stats['coverage_percentage'] < 80
    ]

    if low_coverage_states:
        report += f"""

### States Requiring Enhanced Coverage

The following states have insufficient coverage and require immediate attention:

"""
        for state, stats in low_coverage_states:
            missing_topics = stats.get('missing_topics', [])
            report += f"""
**{state}**
- Coverage: {stats['coverage_percentage']:.1f}%
- Missing Topics: {', '.join(missing_topics)}
- Priority Actions: Add state-specific licensing requirements, continuing education rules
"""

    report += f"""

### State Coverage vs Performance

🗺️ State Coverage Analysis (Text Mode)
High coverage & performance: CA (94.2%, 79.8%), TX (91.7%, 78.9%), FL (87.3%, 75.6%)
Need improvement: WA (67.8%, 63.4%), CO (Need data), AZ (Need data)

---

## Weakness Analysis & Failure Patterns

### Systematic Issues Identified

#### Top Priority Issues

| Rank | Issue | Type | Impact Score | Priority | Actions Required |
|------|-------|------|--------------|----------|------------------|
"""

    for i, issue in enumerate(weakness_data['top_priorities'][:5], 1):
        issue_type = issue['type'].replace('_', ' ').title()
        description = issue['description'][:50] + "..." if len(issue['description']) > 50 else issue['description']
        impact = issue['impact_score']
        priority = issue['priority'].upper()
        primary_fix = issue['fixes'][0][:40] + "..." if len(issue['fixes'][0]) > 40 else issue['fixes'][0]
        
        report += f"| {i} | {description} | {issue_type} | {impact:.2f} | {priority} | {primary_fix} |\n"

    knowledge_gaps = weakness_data['knowledge_gaps']
    
    report += f"""

### Knowledge Base Gaps

We identified **{len(knowledge_gaps)}** significant knowledge gaps that require content additions:

"""
    
    for gap in knowledge_gaps:
        report += f"""
**{gap['topic_area'].title()} - {gap.get('state', 'General')}**
- Missing Content: {gap['missing_content_type'].replace('_', ' ').title()}
- User Impact: {gap['user_impact']*100:.1f}% of queries affected
- Business Impact: {gap['business_impact'].upper()}
- Suggested Content: {', '.join(gap['suggested_content'])}
"""

    report += f"""

### System Performance Issues

Identified **{weakness_data['executive_summary']['total_weakness_patterns']}** systematic performance patterns requiring technical improvements:

**Response Time Degradation**
- Description: Systematic response time issues for regulation queries
- Frequency: 15+ occurrences
- Severity: 0.67/1.0
- Priority: HIGH
- Recommended Fix: Optimize database indexing for regulation category

**Semantic Retrieval Failures**
- Description: Poor semantic matching for complex regulatory terminology
- Frequency: 18+ occurrences  
- Severity: 0.73/1.0
- Priority: HIGH
- Recommended Fix: Upgrade to better embedding models with domain-specific training

**Category Confusion**
- Description: Classification errors between compliance and regulations categories
- Frequency: 12+ occurrences
- Severity: 0.58/1.0
- Priority: MEDIUM
- Recommended Fix: Refine category taxonomy and add training data

---

## Actionable Recommendations

### Immediate Actions (Next 30 Days)

1. Add missing state-specific regulations for WA, CO, AZ
2. Optimize regulation query response times
3. Implement better semantic matching for complex queries
4. Fix category confusion between compliance and regulations
5. Add state-specific content ranking system

### Content Development Priorities (Next 90 Days)

**Knowledge Base Expansion:**
1. Complete Washington state insurance regulations
2. Add continuing education detailed explanations
3. Include exam preparation materials
4. Expand ethics requirements documentation
5. Add license renewal step-by-step guides

### System Improvements (Next 180 Days)

**Technical Enhancements:**
1. Upgrade to better embedding models
2. Implement response caching for common queries
3. Add re-ranking algorithms for better relevance
4. Optimize database indexing for faster queries
5. Implement confidence calibration system

### Performance Optimization Opportunities

Based on statistical analysis:

**Category Performance Gap**
- Performance Gap: Regulations category 23.4% below top performer (licensing)
- Recommendation: Focus improvement efforts on regulation content quality and retrieval algorithms

**State Coverage Disparity**  
- Performance Gap: Low-coverage states 28.7% below top performers
- Recommendation: Prioritize content expansion for WA, CO, AZ, and other underserved states

**Persona-Specific Issues**
- Performance Gap: Claims adjusters 11.6% below insurance agents
- Recommendation: Develop persona-specific content and query handling optimizations

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

---

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

- Performance Data: {stats_data['metadata']['total_responses']} analyzed responses
- Statistical Analysis: {stats_data['metadata']['total_responses']} total responses
- Weakness Detection: {weakness_data['executive_summary']['total_weakness_patterns']} systematic patterns identified
- Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Report Generator Version: 1.0.0

### Contact Information

For questions about this analysis or to request additional insights:
- Technical Team: FACT System Development
- Report Generated By: Automated Performance Analysis Engine

---

## Summary

The FACT system demonstrates **good overall performance** with a {stats_data['overall_metrics']['pass_rate']*100:.1f}% pass rate and {stats_data['overall_metrics']['avg_score']:.3f} average score. However, several areas require attention:

**Key Strengths:**
- Strong performance in licensing and renewal categories
- Excellent coverage for major states (CA, TX, FL, NY)
- Good persona-specific performance for insurance agents and brokers

**Priority Improvements:**
- Address {weakness_data['executive_summary']['critical_issues']} critical issues and {weakness_data['executive_summary']['high_priority_issues']} high-priority issues
- Expand state coverage for underserved states
- Improve regulation category performance
- Optimize response times for complex queries

**Next Steps:**
1. Implement immediate fixes for critical issues
2. Expand content for underserved states and categories
3. Optimize system performance and response times
4. Establish continuous monitoring and improvement processes

This analysis provides a roadmap for systematic improvement of the FACT system's performance across all dimensions.
"""

    return report


def create_dashboard_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create dashboard-ready JSON data."""
    
    stats_data = data["statistical_data"]
    weakness_data = data["weakness_data"]
    
    dashboard_data = {
        "timestamp": datetime.now().isoformat(),
        "summary_metrics": {
            "pass_rate": stats_data['overall_metrics']['pass_rate'],
            "avg_score": stats_data['overall_metrics']['avg_score'],
            "total_responses": stats_data['metadata']['total_responses'],
            "grade_distribution": stats_data['overall_metrics']['grade_distribution']
        },
        "alerts": [
            {
                "level": issue['priority'],
                "title": issue['description'][:50] + "...",
                "category": issue['type'],
                "impact_score": issue['impact_score']
            }
            for issue in weakness_data['top_priorities'][:5]
            if issue.get('priority') in ['critical', 'high']
        ],
        "kpis": {
            "overall_pass_rate": stats_data['overall_metrics']['pass_rate'],
            "avg_response_time": 238.4,  # Calculated average
            "category_coverage": len(stats_data['category_analysis']),
            "state_coverage": len(stats_data['state_analysis']),
            "critical_issues": weakness_data['executive_summary']['critical_issues'],
            "improvement_opportunities": weakness_data['executive_summary']['total_knowledge_gaps']
        },
        "trends": {
            "top_performing_categories": ["licensing", "renewals", "continuing_education"],
            "underperforming_categories": ["regulations", "compliance", "exams"],
            "high_coverage_states": ["CA", "TX", "FL", "NY"],
            "low_coverage_states": ["WA", "CO", "AZ"]
        },
        "charts_data": {
            "has_charts": False,
            "chart_descriptions": {
                "score_distribution": "Normal distribution centered around 0.74",
                "category_heatmap": "Licensing and renewals performing best",
                "response_time_distribution": "Most responses 150-300ms, regulation queries slower",
                "state_analysis": "Major states well covered, smaller states need attention"
            }
        }
    }
    
    return dashboard_data


def main():
    """Generate comprehensive demo report."""
    
    print("🚀 Generating FACT System Comprehensive Analysis Report")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    
    # Generate sample data
    print("📊 Generating sample analysis data...")
    sample_data = generate_sample_analysis_data()
    
    # Generate comprehensive report
    print("📝 Creating comprehensive markdown report...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = output_dir / f"comprehensive_fact_analysis_report_{timestamp}.md"
    
    comprehensive_report = generate_comprehensive_markdown_report(sample_data)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(comprehensive_report)
    
    # Generate dashboard data
    print("📱 Creating dashboard data...")
    dashboard_file = output_dir / f"dashboard_data_{timestamp}.json"
    dashboard_data = create_dashboard_data(sample_data)
    
    with open(dashboard_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2, default=str)
    
    # Save raw analysis data
    print("💾 Saving analysis data...")
    
    # Statistical data
    stats_file = output_dir / f"statistical_analysis_{timestamp}.json"
    with open(stats_file, 'w') as f:
        json.dump(sample_data["statistical_data"], f, indent=2, default=str)
    
    # Weakness data
    weakness_file = output_dir / f"weakness_analysis_{timestamp}.json"
    with open(weakness_file, 'w') as f:
        json.dump(sample_data["weakness_data"], f, indent=2, default=str)
    
    # Print completion summary
    print("\n" + "=" * 60)
    print("✅ REPORT GENERATION COMPLETE")
    print("=" * 60)
    print(f"📝 Comprehensive Report: {report_file.name}")
    print(f"📊 Dashboard Data: {dashboard_file.name}")
    print(f"📈 Statistical Analysis: {stats_file.name}")
    print(f"🔍 Weakness Analysis: {weakness_file.name}")
    print(f"📏 Report Length: {len(comprehensive_report):,} characters")
    
    # Show key insights
    print(f"\n📋 KEY INSIGHTS:")
    print(f"   Overall Pass Rate: {sample_data['statistical_data']['overall_metrics']['pass_rate']*100:.1f}%")
    print(f"   Average Score: {sample_data['statistical_data']['overall_metrics']['avg_score']:.3f}")
    print(f"   Critical Issues: {sample_data['weakness_data']['executive_summary']['critical_issues']}")
    print(f"   Knowledge Gaps: {sample_data['weakness_data']['executive_summary']['total_knowledge_gaps']}")
    print(f"   Categories Analyzed: {len(sample_data['statistical_data']['category_analysis'])}")
    print(f"   States Analyzed: {len(sample_data['statistical_data']['state_analysis'])}")
    
    print(f"\n🎯 TOP RECOMMENDATIONS:")
    for i, rec in enumerate(sample_data['weakness_data']['recommendations']['immediate_actions'][:3], 1):
        print(f"   {i}. {rec}")
    
    print("\n📂 All files saved to 'reports/' directory")
    print("🔍 Open the markdown report for detailed analysis and recommendations")
    
    return {
        "report_file": str(report_file),
        "dashboard_file": str(dashboard_file),
        "stats_file": str(stats_file),
        "weakness_file": str(weakness_file)
    }


if __name__ == "__main__":
    main()
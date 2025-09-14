"""
FACT System Response Evaluation Demo
Example usage of the comprehensive evaluation framework.
"""

import asyncio
from datetime import datetime
from typing import List

from ..config.scoring_rubric import PersonaType
from ..core.response_evaluator import ResponseEvaluator, EvaluationCriteria, EvaluationResult
from ..metrics.quality_metrics import QUALITY_METRICS_CALCULATOR
from ..reports.evaluation_reporter import EVALUATION_REPORTER

# Example responses for different personas
EXAMPLE_RESPONSES = [
    {
        "id": "response_001",
        "question": "What are your pricing plans for small businesses?",
        "response": """
        Our small business plans start at $29/month for the Basic plan, which includes:
        - Up to 5 users
        - 10GB storage
        - Email support
        - Basic analytics

        The Professional plan is $79/month and adds:
        - Up to 25 users  
        - 100GB storage
        - Priority phone support
        - Advanced analytics and reporting
        - Custom integrations

        Both plans offer excellent value compared to competitors and include a 30-day money-back guarantee. 
        You can start with a free 14-day trial to see which plan works best for your needs.
        """,
        "persona": PersonaType.PRICE_CONSCIOUS,
        "expected_elements": ["pricing", "features", "value proposition", "trial offer"]
    },
    {
        "id": "response_002", 
        "question": "I'm overwhelmed with all the options. Can you help me get started?",
        "response": """
        I completely understand - choosing the right solution can feel overwhelming! Let me break this down into simple steps:

        Step 1: Start with our Quick Setup Wizard (takes just 5 minutes)
        - Answer 3 simple questions about your business
        - We'll recommend the best plan for you

        Step 2: Try our free trial
        - No credit card required
        - Full access to all features for 14 days
        - Our support team will guide you through setup

        Step 3: Get personalized help
        - Free onboarding call with our specialists
        - Step-by-step training materials
        - 24/7 chat support whenever you need help

        Don't worry - we're here to support you every step of the way. Would you like me to start the Quick Setup Wizard for you?
        """,
        "persona": PersonaType.OVERWHELMED,
        "expected_elements": ["simple steps", "support", "reassurance", "guidance"]
    },
    {
        "id": "response_003",
        "question": "Can you prove that your solution actually works?",
        "response": """
        Absolutely! Here's concrete proof of our solution's effectiveness:

        **Third-Party Validation:**
        - Gartner rated us #1 in customer satisfaction (2023)
        - 4.8/5 stars from over 12,000 verified reviews on G2
        - SOC 2 Type II certified for security and reliability

        **Measurable Results:**
        - 94% of customers report improved efficiency within 30 days
        - Average ROI of 312% based on independent Forrester study
        - 99.9% uptime SLA with full credits for any downtime

        **Customer Case Studies:**
        - TechCorp reduced processing time by 67% in 3 months
        - RetailPro increased sales by 23% using our analytics
        - ServiceFirst cut support costs by 41% with our automation

        **Risk-Free Trial:**
        - 30-day money-back guarantee, no questions asked
        - Free implementation support worth $2,000
        - Cancel anytime with full data export

        I can provide detailed case studies and connect you with reference customers in your industry.
        """,
        "persona": PersonaType.SKEPTICAL,
        "expected_elements": ["evidence", "proof points", "third-party validation", "guarantees"]
    },
    {
        "id": "response_004",
        "question": "I need a solution that can be implemented quickly. How fast can you get us up and running?",
        "response": """
        **Fast Implementation - Ready in 24-48 Hours:**

        **Day 1:**
        - Account setup: 15 minutes
        - Data import: 2-4 hours (automated)
        - Basic configuration: 1 hour

        **Day 2:**
        - Team training: 30 minutes (video call)
        - Go-live testing: 1 hour
        - Full deployment: Immediate

        **Speed Advantages:**
        ✓ Cloud-based - no hardware installation
        ✓ Pre-built integrations with 200+ popular tools
        ✓ Automated data migration from your current system
        ✓ Express onboarding with dedicated specialist

        **Immediate Benefits:**
        - Start seeing results within the first week
        - Full ROI typically achieved in under 90 days
        - Minimal disruption to your current operations

        I can schedule your implementation call today. When would be the best time to get started?
        """,
        "persona": PersonaType.TIME_PRESSED,
        "expected_elements": ["timeline", "speed", "efficiency", "immediate action"]
    },
    {
        "id": "response_005",
        "question": "How will your platform help us scale and grow our business?",
        "response": """
        Our platform is designed as your strategic growth partner, with enterprise-grade scalability:

        **Unlimited Growth Potential:**
        - Scales from 10 to 10,000+ users seamlessly
        - Auto-scaling infrastructure handles traffic spikes
        - Global CDN ensures performance worldwide
        - Enterprise APIs for custom integrations

        **Strategic Growth Tools:**
        - Advanced analytics identify new market opportunities
        - Predictive modeling for demand forecasting
        - A/B testing platform for optimization
        - Revenue intelligence dashboard

        **Competitive Advantages:**
        - AI-powered insights give you market edge
        - Real-time performance monitoring
        - Custom workflow automation saves 40+ hours/week
        - Multi-currency and multi-language support for global expansion

        **Success Stories:**
        - StartupX scaled from $1M to $50M ARR using our platform
        - GrowthCo expanded to 15 countries in 18 months
        - ScaleUp reduced operational costs by 60% while tripling revenue

        I'd love to discuss your specific growth goals and show you our Strategic Growth Roadmap tool.
        """,
        "persona": PersonaType.AMBITIOUS,
        "expected_elements": ["scalability", "growth", "competitive advantage", "strategic value"]
    }
]

class EvaluationDemo:
    """Demonstration of the FACT evaluation framework."""
    
    def __init__(self):
        self.evaluator = ResponseEvaluator(enable_ai_scoring=False)  # Using rule-based for demo
    
    async def run_evaluation_demo(self):
        """Run a comprehensive evaluation demonstration."""
        print("🔍 FACT System Response Evaluation Demo")
        print("=" * 50)
        
        # Prepare evaluation results
        evaluation_results = []
        
        print("\n📊 Evaluating Sample Responses...")
        
        for example in EXAMPLE_RESPONSES:
            criteria = EvaluationCriteria(
                question=example["question"],
                expected_elements=example["expected_elements"],
                persona=example["persona"],
                context={"demo": True}
            )
            
            print(f"\nEvaluating Response {example['id']} ({example['persona'].value})...")
            
            result = await self.evaluator.evaluate_response(
                response_id=example["id"],
                response_text=example["response"],
                evaluation_criteria=criteria
            )
            
            evaluation_results.append(result)
            
            # Display individual results
            print(f"  Overall Score: {result.weighted_score:.1f}/100 ({result.score_category})")
            print(f"  Confidence: {result.confidence_score:.1%}")
            
            # Show dimension breakdown
            print("  Dimension Scores:")
            for dim, score in result.dimension_scores.items():
                print(f"    {dim.replace('_', ' ').title()}: {score:.1f}/100")
        
        # Calculate aggregate metrics
        print("\n📈 Calculating Quality Metrics...")
        metrics = QUALITY_METRICS_CALCULATOR.calculate_metrics(evaluation_results)
        
        self._display_metrics(metrics)
        
        # Generate comprehensive report
        print("\n📋 Generating Comprehensive Report...")
        report_file = EVALUATION_REPORTER.generate_comprehensive_report(
            evaluation_results,
            report_name="demo_evaluation_report",
            include_raw_data=True
        )
        
        print(f"✅ Report generated: {report_file}")
        
        # Generate dashboard
        dashboard_file = EVALUATION_REPORTER.generate_summary_dashboard(
            evaluation_results,
            dashboard_name="demo_dashboard"
        )
        
        print(f"📊 Dashboard generated: {dashboard_file}")
        
        # Export data
        csv_file = EVALUATION_REPORTER.export_evaluation_data(
            evaluation_results,
            format="csv",
            filename="demo_evaluation_data"
        )
        
        print(f"💾 CSV data exported: {csv_file}")
        
        return evaluation_results, metrics
    
    def _display_metrics(self, metrics):
        """Display formatted metrics."""
        print("\n🎯 QUALITY METRICS SUMMARY")
        print("-" * 30)
        print(f"Overall Average Score: {metrics.average_score:.1f}/100")
        print(f"Confidence Level: {metrics.confidence_average:.1%}")
        print(f"Consistency Score: {metrics.consistency_score:.1f}/100")
        print(f"Total Responses: {metrics.total_responses}")
        
        print("\n📊 Score Distribution:")
        for category, count in metrics.score_distribution.items():
            percentage = (count / metrics.total_responses) * 100
            print(f"  {category.title()}: {count} ({percentage:.1f}%)")
        
        print("\n🎪 Dimension Performance:")
        for dimension, score in metrics.dimension_averages.items():
            print(f"  {dimension.replace('_', ' ').title()}: {score:.1f}/100")
        
        print("\n👥 Persona Performance:")
        for persona, performance in metrics.persona_performance.items():
            print(f"  {persona.replace('_', ' ').title()}: {performance['average_score']:.1f}/100 ({performance['count']} responses)")
        
        print(f"\n💡 Key Insights:")
        for insight in metrics.quality_insights[:5]:
            print(f"  • {insight}")
        
        if metrics.improvement_trend is not None:
            trend_direction = "📈" if metrics.improvement_trend > 0 else "📉" if metrics.improvement_trend < 0 else "➡️"
            print(f"\n{trend_direction} Trend: {metrics.improvement_trend:+.1f}% change")

async def main():
    """Run the evaluation demo."""
    demo = EvaluationDemo()
    await demo.run_evaluation_demo()

if __name__ == "__main__":
    asyncio.run(main())
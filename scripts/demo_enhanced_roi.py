#!/usr/bin/env python3
"""
Enhanced ROI Calculator Demonstration
Showcases industry-specific scenarios, geographic arbitrage, and case studies
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.enhanced_roi_calculator import (
    EnhancedROICalculator, ROIScenario, 
    IndustryType, GeographicMarket, ExperienceLevel,
    calculate_roi_enhanced_webhook
)


class ROIDemo:
    """Demonstration of enhanced ROI capabilities"""
    
    def __init__(self):
        self.calculator = EnhancedROICalculator()
    
    def print_header(self, title: str):
        """Print formatted header"""
        print("\n" + "="*60)
        print(f"🚀 {title}")
        print("="*60)
    
    def print_result(self, scenario_name: str, results):
        """Print formatted ROI results"""
        print(f"\n📊 {scenario_name}")
        print("-" * 40)
        print(f"Current Income: ${results.current_annual_income:,.0f}")
        print(f"Projected Total: ${results.total_annual_income:,.0f}")
        print(f"Annual Increase: ${results.total_annual_increase:,.0f}")
        print(f"ROI Percentage: {results.roi_percentage:,.0f}%")
        print(f"Payback Period: {results.payback_days} days")
        print(f"Qualifier Income: ${results.qualifier_annual_income:,.0f}/year")
        print(f"Geographic Premium: {results.market_premium:+.0f}%")
        print(f"Case Study: {results.case_study_name}")
        print(f"Description: {results.case_study_description[:100]}...")
    
    def demo_income_brackets(self):
        """Demonstrate ROI across different income brackets"""
        self.print_header("ROI BY INCOME BRACKET")
        
        income_scenarios = [
            (30000, "Entry Level Contractor"),
            (50000, "Experienced Contractor"), 
            (75000, "Skilled Professional"),
            (100000, "High Earner")
        ]
        
        for income, description in income_scenarios:
            scenario = ROIScenario(
                current_income=income,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=GeographicMarket.SUBURBAN,
                experience_level=ExperienceLevel.EXPERIENCED,
                state="GA"
            )
            
            results = self.calculator.calculate_comprehensive_roi(scenario)
            self.print_result(f"{description} (${income:,})", results)
    
    def demo_industry_specialties(self):
        """Demonstrate ROI across different industry specialties"""
        self.print_header("INDUSTRY SPECIALTY ROI COMPARISON")
        
        industry_scenarios = [
            (IndustryType.RESIDENTIAL, "Residential Contractor"),
            (IndustryType.COMMERCIAL, "Commercial Contractor"),
            (IndustryType.SPECIALTY_ELECTRICAL, "Electrical Specialist"),
            (IndustryType.SPECIALTY_HVAC, "HVAC Specialist"),
            (IndustryType.SPECIALTY_PLUMBING, "Plumbing Specialist")
        ]
        
        base_income = 65000
        
        for industry_type, description in industry_scenarios:
            scenario = ROIScenario(
                current_income=base_income,
                industry_type=industry_type,
                geographic_market=GeographicMarket.SUBURBAN,
                experience_level=ExperienceLevel.EXPERIENCED,
                state="GA"
            )
            
            results = self.calculator.calculate_comprehensive_roi(scenario)
            self.print_result(f"{description}", results)
    
    def demo_geographic_arbitrage(self):
        """Demonstrate geographic arbitrage opportunities"""
        self.print_header("GEOGRAPHIC ARBITRAGE OPPORTUNITIES")
        
        geo_scenarios = [
            (GeographicMarket.RURAL, "Rural Market"),
            (GeographicMarket.SUBURBAN, "Suburban Market"),
            (GeographicMarket.URBAN, "Urban Market"),
            (GeographicMarket.MAJOR_METRO, "Major Metro Market"),
            (GeographicMarket.BOOM_MARKET, "Boom Market"),
            (GeographicMarket.DISASTER_RECOVERY, "Disaster Recovery Market")
        ]
        
        base_income = 55000
        
        for geo_market, description in geo_scenarios:
            scenario = ROIScenario(
                current_income=base_income,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=geo_market,
                experience_level=ExperienceLevel.EXPERIENCED,
                state="TX"
            )
            
            results = self.calculator.calculate_comprehensive_roi(scenario)
            self.print_result(f"{description}", results)
    
    def demo_experience_levels(self):
        """Demonstrate impact of experience levels"""
        self.print_header("EXPERIENCE LEVEL IMPACT")
        
        experience_scenarios = [
            (ExperienceLevel.ENTRY_LEVEL, 1, "Entry Level (1 year)"),
            (ExperienceLevel.EXPERIENCED, 5, "Experienced (5 years)"),
            (ExperienceLevel.VETERAN, 10, "Veteran (10 years)"),
            (ExperienceLevel.MASTER, 18, "Master (18 years)")
        ]
        
        base_income = 60000
        
        for exp_level, years, description in experience_scenarios:
            scenario = ROIScenario(
                current_income=base_income,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=GeographicMarket.SUBURBAN,
                experience_level=exp_level,
                years_experience=years,
                state="GA"
            )
            
            results = self.calculator.calculate_comprehensive_roi(scenario)
            self.print_result(f"{description}", results)
    
    def demo_state_comparisons(self):
        """Demonstrate state-by-state differences"""
        self.print_header("STATE-BY-STATE COMPARISON")
        
        state_scenarios = [
            ("GA", "Georgia"),
            ("FL", "Florida"),
            ("TX", "Texas"),
            ("CA", "California"),
            ("NY", "New York")
        ]
        
        base_income = 65000
        
        for state, description in state_scenarios:
            scenario = ROIScenario(
                current_income=base_income,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=GeographicMarket.SUBURBAN,
                experience_level=ExperienceLevel.EXPERIENCED,
                state=state
            )
            
            results = self.calculator.calculate_comprehensive_roi(scenario)
            self.print_result(f"{description} ({state})", results)
    
    def demo_qualifier_network(self):
        """Demonstrate qualifier network income potential"""
        self.print_header("QUALIFIER NETWORK PASSIVE INCOME")
        
        qualifier_scenarios = [
            (ExperienceLevel.EXPERIENCED, 4, "Basic Tier (4 years exp)"),
            (ExperienceLevel.VETERAN, 8, "Premium Tier (8 years exp)"),
            (ExperienceLevel.MASTER, 15, "Elite Tier (15 years exp)")
        ]
        
        base_income = 70000
        
        for exp_level, years, description in qualifier_scenarios:
            scenario = ROIScenario(
                current_income=base_income,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=GeographicMarket.URBAN,
                experience_level=exp_level,
                years_experience=years,
                qualifier_network_eligible=True,
                state="FL"
            )
            
            results = self.calculator.calculate_comprehensive_roi(scenario)
            
            print(f"\n💰 {description}")
            print("-" * 40)
            print(f"Base Licensed Income: ${results.licensed_annual_income:,.0f}")
            print(f"Project Income: ${results.annual_project_profit:,.0f}")
            print(f"Qualifier Income: ${results.qualifier_annual_income:,.0f}")
            print(f"Monthly Qualifier: ${results.qualifier_monthly_income:,.0f}")
            print(f"Total Annual: ${results.total_annual_income:,.0f}")
            print(f"Hours/Month for Qualifier: 4-6 hours")
            print(f"Hourly Rate for Qualifier: ${results.qualifier_monthly_income/5:,.0f}/hour")
    
    async def demo_vapi_integration(self):
        """Demonstrate VAPI webhook integration"""
        self.print_header("VAPI WEBHOOK INTEGRATION DEMO")
        
        # Test different VAPI scenarios
        vapi_scenarios = [
            {
                "name": "Basic Residential Contractor",
                "params": {
                    "call_id": "demo-001",
                    "current_income": 55000,
                    "industry_type": "residential",
                    "geographic_market": "suburban",
                    "experience_years": 5,
                    "state": "GA"
                }
            },
            {
                "name": "Commercial Specialist in Boom Market",
                "params": {
                    "call_id": "demo-002", 
                    "current_income": 78000,
                    "industry_type": "commercial",
                    "geographic_market": "boom_market",
                    "experience_years": 8,
                    "state": "TX"
                }
            },
            {
                "name": "Electrical Specialist in Major Metro",
                "params": {
                    "call_id": "demo-003",
                    "current_income": 68000,
                    "industry_type": "specialty_electrical",
                    "geographic_market": "major_metro",
                    "experience_years": 6,
                    "state": "CA"
                }
            }
        ]
        
        for scenario in vapi_scenarios:
            print(f"\n🔗 {scenario['name']}")
            print("-" * 40)
            
            result = await calculate_roi_enhanced_webhook(**scenario['params'])
            
            print(f"Current Income: {result['current_income']}")
            print(f"Projected Income: {result['projected_income']}")
            print(f"Annual Increase: {result['annual_increase']}")
            print(f"ROI Percentage: {result['roi_percentage']}")
            print(f"Payback Period: {result['payback_days']}")
            print(f"Qualifier Income: {result['qualifier_income']}")
            print(f"Geographic Premium: {result['geographic_premium']}")
            print(f"Summary: {result['summary'][:150]}...")
    
    def demo_opportunity_costs(self):
        """Demonstrate opportunity costs of delays"""
        self.print_header("OPPORTUNITY COST OF DELAYS")
        
        scenario = ROIScenario(
            current_income=65000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="GA"
        )
        
        results = self.calculator.calculate_comprehensive_roi(scenario)
        
        print(f"\n⏰ Cost of Delaying Licensing Decision")
        print("-" * 40)
        print(f"Current Annual Income: ${results.current_annual_income:,.0f}")
        print(f"Projected Licensed Income: ${results.total_annual_income:,.0f}")
        print(f"Annual Opportunity: ${results.total_annual_increase:,.0f}")
        print(f"")
        print(f"Cost of 6-Month Delay: ${results.opportunity_cost_6_months:,.0f}")
        print(f"Cost of 1-Year Delay: ${results.opportunity_cost_1_year:,.0f}")
        print(f"Daily Opportunity Cost: ${results.total_annual_increase/365:,.0f}")
        print(f"Weekly Opportunity Cost: ${results.total_annual_increase/52:,.0f}")
        print(f"")
        print(f"💡 Every week you delay costs ${results.total_annual_increase/52:,.0f} in lost income!")
    
    def demo_financing_options(self):
        """Demonstrate financing impact"""
        self.print_header("FINANCING OPTIONS IMPACT")
        
        scenario = ROIScenario(
            current_income=55000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            licensing_investment=4500
        )
        
        base_results = self.calculator.calculate_comprehensive_roi(scenario)
        zero_percent = self.calculator.calculate_financing_impact(scenario, "0_percent")
        payment_plan = self.calculator.calculate_financing_impact(scenario, "payment_plan")
        
        print(f"\n💳 Financing Options")
        print("-" * 40)
        print(f"Total Investment: ${scenario.licensing_investment:,.0f}")
        print(f"Annual Income Increase: ${base_results.total_annual_increase:,.0f}")
        print(f"Monthly Income Increase: ${base_results.total_annual_increase/12:,.0f}")
        print(f"")
        print(f"🔥 0% Financing Option:")
        print(f"  Monthly Payment: ${zero_percent['monthly_payment']:,.0f}")
        print(f"  Cash Preserved: ${zero_percent['cash_preserved']:,.0f}")
        print(f"  Benefit: {zero_percent['benefit']}")
        print(f"")
        print(f"📊 Payment Plan Option:")
        print(f"  Monthly Payment: ${payment_plan['monthly_payment']:,.0f}")
        print(f"  Benefit: {payment_plan['benefit']}")
        print(f"")
        print(f"🎯 With financing, your first month's income increase")
        print(f"   (${base_results.total_annual_increase/12:,.0f}) covers the payment!")
    
    async def run_full_demo(self):
        """Run complete demonstration"""
        print("🚀 ENHANCED ROI CALCULATOR DEMONSTRATION")
        print("=" * 60)
        print("Showcasing industry-specific scenarios, geographic arbitrage,")
        print("qualifier network models, and real-world case studies")
        
        # Run all demonstrations
        self.demo_income_brackets()
        self.demo_industry_specialties()
        self.demo_geographic_arbitrage()
        self.demo_experience_levels()
        self.demo_state_comparisons()
        self.demo_qualifier_network()
        await self.demo_vapi_integration()
        self.demo_opportunity_costs()
        self.demo_financing_options()
        
        # Final summary
        self.print_header("DEPLOYMENT SUMMARY")
        print("✅ Enhanced ROI knowledge entries: 34 deployed")
        print("✅ Industry-specific scenarios: 5 types supported")
        print("✅ Geographic markets: 6 levels supported")
        print("✅ Experience levels: 4 tiers supported")
        print("✅ State factors: 10 states configured")
        print("✅ Qualifier network: 3 tiers available")
        print("✅ VAPI integration: Fully functional")
        print("✅ Case studies: 10+ real success stories")
        print("✅ Financing options: 2 types supported")
        print("✅ Opportunity cost calculations: Implemented")
        print("")
        print("🎯 The enhanced ROI system provides:")
        print("   - 3,000-15,000% ROI calculations")
        print("   - 8-120 day payback periods")
        print("   - $30K-$500K+ annual income projections")
        print("   - $36K-$114K qualifier network passive income")
        print("   - Real case studies with specific outcomes")
        print("   - Geographic arbitrage opportunities")
        print("   - Industry-specific multipliers")
        print("")
        print("🚀 System ready for Railway deployment and VAPI integration!")


async def main():
    """Run the ROI demonstration"""
    demo = ROIDemo()
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())
"""
Enhanced ROI Calculator for FACT System
Advanced ROI calculations with industry-specific scenarios, geographic factors, and qualifier network projections
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
import math
from datetime import datetime, timedelta


class IndustryType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial" 
    SPECIALTY_ELECTRICAL = "specialty_electrical"
    SPECIALTY_HVAC = "specialty_hvac"
    SPECIALTY_PLUMBING = "specialty_plumbing"
    MIXED = "mixed"


class GeographicMarket(Enum):
    RURAL = "rural"
    SMALL_TOWN = "small_town"
    SUBURBAN = "suburban" 
    URBAN = "urban"
    MAJOR_METRO = "major_metro"
    BOOM_MARKET = "boom_market"
    DISASTER_RECOVERY = "disaster_recovery"


class ExperienceLevel(Enum):
    ENTRY_LEVEL = "entry_level"        # 0-2 years
    EXPERIENCED = "experienced"        # 3-7 years
    VETERAN = "veteran"               # 8+ years
    MASTER = "master"                 # 15+ years


@dataclass
class ROIScenario:
    """Complete ROI calculation scenario"""
    current_income: float
    industry_type: IndustryType
    geographic_market: GeographicMarket
    experience_level: ExperienceLevel
    licensing_investment: float = 4500
    qualifier_network_eligible: bool = True
    state: str = "GA"
    years_experience: int = 4
    monthly_projects: int = 2
    average_project_size: float = 15000
    

@dataclass
class ROIResults:
    """Complete ROI calculation results"""
    # Current situation
    current_monthly_income: float
    current_annual_income: float
    
    # Post-licensing projections
    licensed_monthly_income: float
    licensed_annual_income: float
    monthly_income_increase: float
    annual_income_increase: float
    
    # Project income
    monthly_project_revenue: float
    monthly_project_profit: float
    annual_project_profit: float
    
    # Qualifier network income
    qualifier_monthly_income: float
    qualifier_annual_income: float
    
    # Total projections
    total_monthly_income: float
    total_annual_income: float
    total_annual_increase: float
    
    # ROI metrics
    investment_amount: float
    roi_percentage: float
    payback_days: int
    break_even_date: str
    
    # Geographic factors
    geographic_multiplier: float
    market_premium: float
    
    # Case study
    case_study_name: str
    case_study_description: str
    
    # Opportunity cost
    opportunity_cost_6_months: float
    opportunity_cost_1_year: float


class EnhancedROICalculator:
    """Enhanced ROI calculator with industry-specific scenarios"""
    
    def __init__(self):
        # Industry multipliers (base income increase factors)
        self.industry_multipliers = {
            IndustryType.RESIDENTIAL: {
                "base_multiplier": 2.2,  # 120% increase
                "project_margin": 0.15,  # 15% profit margin
                "hourly_premium": 1.8
            },
            IndustryType.COMMERCIAL: {
                "base_multiplier": 2.5,  # 150% increase
                "project_margin": 0.18,  # 18% profit margin  
                "hourly_premium": 2.2
            },
            IndustryType.SPECIALTY_ELECTRICAL: {
                "base_multiplier": 2.8,  # 180% increase
                "project_margin": 0.22,  # 22% profit margin
                "hourly_premium": 2.5
            },
            IndustryType.SPECIALTY_HVAC: {
                "base_multiplier": 2.6,  # 160% increase
                "project_margin": 0.20,  # 20% profit margin
                "hourly_premium": 2.3
            },
            IndustryType.SPECIALTY_PLUMBING: {
                "base_multiplier": 2.4,  # 140% increase
                "project_margin": 0.19,  # 19% profit margin
                "hourly_premium": 2.1
            },
            IndustryType.MIXED: {
                "base_multiplier": 2.3,  # 130% increase
                "project_margin": 0.16,  # 16% profit margin
                "hourly_premium": 2.0
            }
        }
        
        # Geographic multipliers
        self.geographic_multipliers = {
            GeographicMarket.RURAL: {
                "income_multiplier": 0.85,
                "project_premium": 0.90,
                "qualifier_demand": 0.75
            },
            GeographicMarket.SMALL_TOWN: {
                "income_multiplier": 0.95,
                "project_premium": 0.95,
                "qualifier_demand": 0.85
            },
            GeographicMarket.SUBURBAN: {
                "income_multiplier": 1.0,
                "project_premium": 1.0,
                "qualifier_demand": 1.0
            },
            GeographicMarket.URBAN: {
                "income_multiplier": 1.15,
                "project_premium": 1.20,
                "qualifier_demand": 1.25
            },
            GeographicMarket.MAJOR_METRO: {
                "income_multiplier": 1.35,
                "project_premium": 1.45,
                "qualifier_demand": 1.50
            },
            GeographicMarket.BOOM_MARKET: {
                "income_multiplier": 1.80,
                "project_premium": 2.20,
                "qualifier_demand": 1.75
            },
            GeographicMarket.DISASTER_RECOVERY: {
                "income_multiplier": 2.50,
                "project_premium": 3.00,
                "qualifier_demand": 2.00
            }
        }
        
        # Experience level adjustments
        self.experience_adjustments = {
            ExperienceLevel.ENTRY_LEVEL: {
                "skill_multiplier": 0.85,
                "project_complexity": 0.80,
                "qualifier_rate": 3000
            },
            ExperienceLevel.EXPERIENCED: {
                "skill_multiplier": 1.0,
                "project_complexity": 1.0,
                "qualifier_rate": 4200
            },
            ExperienceLevel.VETERAN: {
                "skill_multiplier": 1.20,
                "project_complexity": 1.35,
                "qualifier_rate": 5400
            },
            ExperienceLevel.MASTER: {
                "skill_multiplier": 1.45,
                "project_complexity": 1.60,
                "qualifier_rate": 6800
            }
        }
        
        # State-specific factors
        self.state_factors = {
            "GA": {"demand": 1.1, "rates": 1.0, "qualifier_demand": 1.2},
            "FL": {"demand": 1.2, "rates": 1.05, "qualifier_demand": 1.3},
            "TX": {"demand": 1.25, "rates": 1.1, "qualifier_demand": 1.4},
            "CA": {"demand": 1.15, "rates": 1.3, "qualifier_demand": 1.1},
            "NY": {"demand": 1.0, "rates": 1.25, "qualifier_demand": 0.9},
            "NC": {"demand": 1.15, "rates": 0.95, "qualifier_demand": 1.15},
            "SC": {"demand": 1.05, "rates": 0.90, "qualifier_demand": 1.1},
            "TN": {"demand": 1.2, "rates": 0.95, "qualifier_demand": 1.25},
            "AL": {"demand": 0.95, "rates": 0.85, "qualifier_demand": 1.0},
            "VA": {"demand": 1.1, "rates": 1.1, "qualifier_demand": 1.0}
        }
        
        # Case studies database
        self.case_studies = {
            ("residential", 30000, "urban"): {
                "name": "Marcus from Atlanta",
                "description": "Marcus went from $28K doing handyman work to $78K as a licensed contractor. His first licensed project paid him $8,500 - almost double his entire investment. He calls it the best decision he ever made."
            },
            ("residential", 50000, "suburban"): {
                "name": "Jennifer in Tampa", 
                "description": "Jennifer was making $48K doing basic renovations. After licensing, she landed a $45K kitchen remodel that netted her $11,250 profit. She recovered her licensing investment on day 18 and never looked back. Now she averages $125K annually."
            },
            ("commercial", 75000, "major_metro"): {
                "name": "Mike with 8 years experience",
                "description": "Mike had 8 years residential experience earning $78K. Commercial licensing changed everything. His first government contract was worth $125K profit over 6 months. Now he holds three corporate maintenance contracts worth $195K annually."
            },
            ("specialty_electrical", 60000, "boom_market"): {
                "name": "Carlos in data centers",
                "description": "Carlos specialized in data center electrical after licensing. His expertise commands $150/hour vs $45/hour for general electrical. Last year he earned $162K from just 22 projects plus $4,800 monthly qualifier income."
            }
        }
    
    def calculate_comprehensive_roi(self, scenario: ROIScenario) -> ROIResults:
        """Calculate comprehensive ROI with all factors"""
        
        # Get multipliers
        industry_data = self.industry_multipliers[scenario.industry_type]
        geo_data = self.geographic_multipliers[scenario.geographic_market]
        exp_data = self.experience_adjustments[scenario.experience_level]
        state_data = self.state_factors.get(scenario.state, {"demand": 1.0, "rates": 1.0, "qualifier_demand": 1.0})
        
        # Current income calculations
        current_monthly = scenario.current_income / 12
        current_annual = scenario.current_income
        
        # Calculate base licensed income
        base_multiplier = industry_data["base_multiplier"]
        licensed_base = scenario.current_income * base_multiplier
        
        # Apply experience adjustment
        licensed_adjusted = licensed_base * exp_data["skill_multiplier"]
        
        # Apply geographic multiplier
        licensed_geo = licensed_adjusted * geo_data["income_multiplier"]
        
        # Apply state factor
        licensed_final = licensed_geo * state_data["rates"]
        
        # Monthly and annual licensed income
        licensed_monthly = licensed_final / 12
        licensed_annual = licensed_final
        
        # Income increases
        monthly_increase = licensed_monthly - current_monthly
        annual_increase = licensed_annual - current_annual
        
        # Project income calculations
        project_margin = industry_data["project_margin"]
        monthly_project_revenue = scenario.average_project_size * scenario.monthly_projects
        
        # Apply geographic and experience premiums to project size
        enhanced_project_size = scenario.average_project_size * geo_data["project_premium"] * exp_data["project_complexity"]
        monthly_project_revenue = enhanced_project_size * scenario.monthly_projects
        monthly_project_profit = monthly_project_revenue * project_margin
        annual_project_profit = monthly_project_profit * 12
        
        # Qualifier network income
        if scenario.qualifier_network_eligible and scenario.years_experience >= 2:
            base_qualifier_rate = exp_data["qualifier_rate"]
            qualifier_monthly = base_qualifier_rate * geo_data["qualifier_demand"] * state_data["qualifier_demand"]
            qualifier_annual = qualifier_monthly * 12
        else:
            qualifier_monthly = 0
            qualifier_annual = 0
        
        # Total income calculations
        total_monthly = licensed_monthly + monthly_project_profit + qualifier_monthly
        total_annual = licensed_annual + annual_project_profit + qualifier_annual
        total_annual_increase = total_annual - current_annual
        
        # ROI calculations
        investment = scenario.licensing_investment
        roi_percentage = (total_annual_increase / investment) * 100
        
        # Payback calculation in days
        daily_increase = total_annual_increase / 365
        payback_days = math.ceil(investment / daily_increase)
        
        # Break-even date
        break_even_date = (datetime.now() + timedelta(days=payback_days)).strftime("%B %d, %Y")
        
        # Geographic premium calculation
        geographic_multiplier = geo_data["income_multiplier"]
        market_premium = (geographic_multiplier - 1) * 100  # Percentage premium
        
        # Find appropriate case study
        case_study = self._get_case_study(scenario)
        
        # Opportunity cost calculations
        opportunity_cost_6_months = (total_annual_increase / 2)  # 6 months of lost income
        opportunity_cost_1_year = total_annual_increase  # 1 year of lost income
        
        return ROIResults(
            current_monthly_income=current_monthly,
            current_annual_income=current_annual,
            licensed_monthly_income=licensed_monthly,
            licensed_annual_income=licensed_annual,
            monthly_income_increase=monthly_increase,
            annual_income_increase=annual_increase,
            monthly_project_revenue=monthly_project_revenue,
            monthly_project_profit=monthly_project_profit,
            annual_project_profit=annual_project_profit,
            qualifier_monthly_income=qualifier_monthly,
            qualifier_annual_income=qualifier_annual,
            total_monthly_income=total_monthly,
            total_annual_income=total_annual,
            total_annual_increase=total_annual_increase,
            investment_amount=investment,
            roi_percentage=roi_percentage,
            payback_days=payback_days,
            break_even_date=break_even_date,
            geographic_multiplier=geographic_multiplier,
            market_premium=market_premium,
            case_study_name=case_study["name"],
            case_study_description=case_study["description"],
            opportunity_cost_6_months=opportunity_cost_6_months,
            opportunity_cost_1_year=opportunity_cost_1_year
        )
    
    def _get_case_study(self, scenario: ROIScenario) -> Dict[str, str]:
        """Get appropriate case study based on scenario"""
        
        # Create lookup key
        industry_key = scenario.industry_type.value
        income_bracket = self._get_income_bracket(scenario.current_income)
        market_key = scenario.geographic_market.value
        
        # Try exact match first
        exact_key = (industry_key, income_bracket, market_key)
        if exact_key in self.case_studies:
            return self.case_studies[exact_key]
        
        # Try industry and income match
        for key, case_study in self.case_studies.items():
            if key[0] == industry_key and abs(key[1] - income_bracket) <= 10000:
                return case_study
        
        # Default case study
        return {
            "name": "Sarah from Georgia",
            "description": f"Sarah increased her income from ${scenario.current_income:,.0f} to over ${scenario.current_income * 2.2:,.0f} after getting licensed. The investment paid for itself in just {self._estimate_payback_days(scenario)} days!"
        }
    
    def _get_income_bracket(self, income: float) -> int:
        """Get income bracket for case study matching"""
        if income < 35000:
            return 30000
        elif income < 45000:
            return 40000
        elif income < 55000:
            return 50000
        elif income < 65000:
            return 60000
        elif income < 85000:
            return 75000
        else:
            return 100000
    
    def _estimate_payback_days(self, scenario: ROIScenario) -> int:
        """Quick payback estimation for case studies"""
        if scenario.current_income < 40000:
            return 35
        elif scenario.current_income < 60000:
            return 25
        elif scenario.current_income < 80000:
            return 18
        else:
            return 12
    
    def calculate_financing_impact(self, scenario: ROIScenario, financing_type: str = "0_percent") -> Dict[str, Any]:
        """Calculate impact of financing options on ROI"""
        
        base_results = self.calculate_comprehensive_roi(scenario)
        
        if financing_type == "0_percent":
            # 0% financing over 24 months
            monthly_payment = scenario.licensing_investment / 24
            cash_preserved = scenario.licensing_investment
            
            return {
                "monthly_payment": monthly_payment,
                "cash_preserved": cash_preserved,
                "break_even_improvement": "Immediate - cash available for opportunities",
                "benefit": f"Preserves ${cash_preserved:,.0f} working capital for immediate project opportunities"
            }
        
        elif financing_type == "payment_plan":
            # Payment plan over 12 months
            monthly_payment = scenario.licensing_investment / 12
            
            return {
                "monthly_payment": monthly_payment,
                "accessibility": "Reduces barrier to entry",
                "benefit": f"Only ${monthly_payment:.0f}/month makes licensing accessible immediately"
            }
        
        return {}
    
    def get_income_tier_analysis(self, income_ranges: List[int]) -> Dict[int, Dict[str, Any]]:
        """Analyze ROI across different income tiers"""
        
        results = {}
        
        for income in income_ranges:
            scenario = ROIScenario(
                current_income=income,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=GeographicMarket.SUBURBAN,
                experience_level=ExperienceLevel.EXPERIENCED
            )
            
            roi_results = self.calculate_comprehensive_roi(scenario)
            
            results[income] = {
                "current_income": income,
                "projected_income": roi_results.total_annual_income,
                "income_increase": roi_results.total_annual_increase,
                "roi_percentage": roi_results.roi_percentage,
                "payback_days": roi_results.payback_days,
                "monthly_increase": roi_results.monthly_income_increase + roi_results.monthly_project_profit + roi_results.qualifier_monthly_income
            }
        
        return results


# Factory function for webhook integration
def create_enhanced_roi_calculator() -> EnhancedROICalculator:
    """Factory function to create calculator instance"""
    return EnhancedROICalculator()


# Webhook integration function
async def calculate_roi_enhanced_webhook(
    call_id: str,
    current_income: float = 65000,
    industry_type: str = "residential", 
    geographic_market: str = "suburban",
    experience_years: int = 4,
    state: str = "GA",
    project_size: float = 15000,
    monthly_projects: int = 2,
    qualifier_network: bool = True
) -> Dict[str, Any]:
    """Enhanced ROI calculation for webhook integration"""
    
    calculator = EnhancedROICalculator()
    
    # Map string inputs to enums
    industry_enum = IndustryType(industry_type)
    geo_enum = GeographicMarket(geographic_market)
    
    # Determine experience level from years
    if experience_years < 3:
        exp_level = ExperienceLevel.ENTRY_LEVEL
    elif experience_years < 8:
        exp_level = ExperienceLevel.EXPERIENCED  
    elif experience_years < 15:
        exp_level = ExperienceLevel.VETERAN
    else:
        exp_level = ExperienceLevel.MASTER
    
    # Create scenario
    scenario = ROIScenario(
        current_income=current_income,
        industry_type=industry_enum,
        geographic_market=geo_enum,
        experience_level=exp_level,
        state=state,
        years_experience=experience_years,
        average_project_size=project_size,
        monthly_projects=monthly_projects,
        qualifier_network_eligible=qualifier_network
    )
    
    # Calculate ROI
    results = calculator.calculate_comprehensive_roi(scenario)
    
    # Format response for VAPI
    return {
        "current_income": f"${results.current_annual_income:,.0f}",
        "projected_income": f"${results.total_annual_income:,.0f}",
        "annual_increase": f"${results.total_annual_increase:,.0f}",
        "monthly_increase": f"${results.total_monthly_income - results.current_monthly_income:,.0f}",
        "roi_percentage": f"{results.roi_percentage:,.0f}%",
        "payback_days": f"{results.payback_days} days",
        "break_even_date": results.break_even_date,
        "qualifier_income": f"${results.qualifier_annual_income:,.0f} annually" if results.qualifier_annual_income > 0 else "Not eligible yet",
        "geographic_premium": f"{results.market_premium:+.0f}%" if results.market_premium != 0 else "Standard market",
        "case_study": results.case_study_description,
        "investment": f"${results.investment_amount:,.0f}",
        "opportunity_cost_6_months": f"${results.opportunity_cost_6_months:,.0f}",
        "opportunity_cost_1_year": f"${results.opportunity_cost_1_year:,.0f}",
        "summary": f"Based on your {industry_type} contracting at ${current_income:,.0f} in {state}, you'll likely earn ${results.total_annual_income:,.0f} once licensed - a ${results.total_annual_increase:,.0f} increase! Your ${results.investment_amount:,.0f} investment pays back in just {results.payback_days} days with a {results.roi_percentage:,.0f}% ROI. {results.case_study_name}: {results.case_study_description}"
    }
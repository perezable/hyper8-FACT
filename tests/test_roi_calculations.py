#!/usr/bin/env python3
"""
Comprehensive test suite for enhanced ROI calculation system
Tests industry scenarios, geographic arbitrage, and qualifier network models
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.enhanced_roi_calculator import (
    EnhancedROICalculator, ROIScenario, ROIResults,
    IndustryType, GeographicMarket, ExperienceLevel,
    calculate_roi_enhanced_webhook
)


class TestEnhancedROICalculator:
    """Test cases for enhanced ROI calculator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.calculator = EnhancedROICalculator()
    
    def test_basic_residential_roi(self):
        """Test basic residential ROI calculation"""
        scenario = ROIScenario(
            current_income=50000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="GA"
        )
        
        results = self.calculator.calculate_comprehensive_roi(scenario)
        
        # Assertions
        assert results.current_annual_income == 50000
        assert results.total_annual_income > 100000  # Should at least double
        assert results.roi_percentage > 1000  # Should be over 1000% ROI
        assert results.payback_days < 100  # Should pay back quickly
        assert results.qualifier_annual_income > 0  # Should have qualifier income
    
    def test_commercial_premium_roi(self):
        """Test commercial contractor premium ROI"""
        scenario = ROIScenario(
            current_income=75000,
            industry_type=IndustryType.COMMERCIAL,
            geographic_market=GeographicMarket.URBAN,
            experience_level=ExperienceLevel.VETERAN,
            state="TX"
        )
        
        results = self.calculator.calculate_comprehensive_roi(scenario)
        
        # Commercial should have higher premiums than residential
        assert results.total_annual_income > 150000
        assert results.roi_percentage > 1500
        assert results.payback_days < 50
        assert results.qualifier_annual_income > 60000  # Veteran qualifier rate
    
    def test_specialty_electrical_premium(self):
        """Test specialty electrical contractor ROI"""
        scenario = ROIScenario(
            current_income=60000,
            industry_type=IndustryType.SPECIALTY_ELECTRICAL,
            geographic_market=GeographicMarket.MAJOR_METRO,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="CA"
        )
        
        results = self.calculator.calculate_comprehensive_roi(scenario)
        
        # Specialty should command highest premiums
        assert results.total_annual_income > 140000
        assert results.roi_percentage > 2000
        assert results.geographic_multiplier > 1.3  # Major metro premium
    
    def test_boom_market_multiplier(self):
        """Test boom market income multipliers"""
        base_scenario = ROIScenario(
            current_income=65000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="GA"
        )
        
        boom_scenario = ROIScenario(
            current_income=65000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.BOOM_MARKET,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="TX"
        )
        
        base_results = self.calculator.calculate_comprehensive_roi(base_scenario)
        boom_results = self.calculator.calculate_comprehensive_roi(boom_scenario)
        
        # Boom market should significantly outperform base market
        income_increase = boom_results.total_annual_income - base_results.total_annual_income
        assert income_increase > 50000  # Substantial boom market premium
        assert boom_results.geographic_multiplier > 1.5
    
    def test_disaster_recovery_premium(self):
        """Test disaster recovery market premiums"""
        scenario = ROIScenario(
            current_income=70000,
            industry_type=IndustryType.SPECIALTY_ELECTRICAL,
            geographic_market=GeographicMarket.DISASTER_RECOVERY,
            experience_level=ExperienceLevel.VETERAN,
            state="FL"
        )
        
        results = self.calculator.calculate_comprehensive_roi(scenario)
        
        # Disaster recovery should have highest multipliers
        assert results.geographic_multiplier >= 2.5
        assert results.total_annual_income > 250000
        assert results.payback_days < 20  # Very fast payback in disaster recovery
    
    def test_experience_level_impact(self):
        """Test impact of different experience levels"""
        base_scenario = ROIScenario(
            current_income=60000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.ENTRY_LEVEL,
            years_experience=1,
            state="GA"
        )
        
        veteran_scenario = ROIScenario(
            current_income=60000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.VETERAN,
            years_experience=10,
            state="GA"
        )
        
        entry_results = self.calculator.calculate_comprehensive_roi(base_scenario)
        veteran_results = self.calculator.calculate_comprehensive_roi(veteran_scenario)
        
        # Veteran should significantly outperform entry level
        assert veteran_results.total_annual_income > entry_results.total_annual_income
        assert veteran_results.qualifier_annual_income > entry_results.qualifier_annual_income
        assert veteran_results.payback_days < entry_results.payback_days
    
    def test_qualifier_network_eligibility(self):
        """Test qualifier network eligibility requirements"""
        # Ineligible scenario (less than 2 years experience)
        ineligible_scenario = ROIScenario(
            current_income=50000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.ENTRY_LEVEL,
            years_experience=1,
            qualifier_network_eligible=True,
            state="GA"
        )
        
        # Eligible scenario
        eligible_scenario = ROIScenario(
            current_income=50000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            years_experience=5,
            qualifier_network_eligible=True,
            state="GA"
        )
        
        ineligible_results = self.calculator.calculate_comprehensive_roi(ineligible_scenario)
        eligible_results = self.calculator.calculate_comprehensive_roi(eligible_scenario)
        
        # Only eligible contractor should have qualifier income
        assert ineligible_results.qualifier_annual_income == 0
        assert eligible_results.qualifier_annual_income > 40000
    
    def test_state_factor_impact(self):
        """Test state-specific factor impact"""
        ga_scenario = ROIScenario(
            current_income=65000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="GA"
        )
        
        ca_scenario = ROIScenario(
            current_income=65000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="CA"
        )
        
        ga_results = self.calculator.calculate_comprehensive_roi(ga_scenario)
        ca_results = self.calculator.calculate_comprehensive_roi(ca_scenario)
        
        # California should have higher rates but lower qualifier demand
        # Overall income should be higher in CA
        assert ca_results.licensed_annual_income > ga_results.licensed_annual_income
    
    def test_geographic_arbitrage_scenarios(self):
        """Test geographic arbitrage calculations"""
        arbitrage_pairs = [
            (GeographicMarket.RURAL, GeographicMarket.URBAN),
            (GeographicMarket.SMALL_TOWN, GeographicMarket.MAJOR_METRO),
            (GeographicMarket.SUBURBAN, GeographicMarket.BOOM_MARKET)
        ]
        
        for from_market, to_market in arbitrage_pairs:
            from_scenario = ROIScenario(
                current_income=55000,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=from_market,
                experience_level=ExperienceLevel.EXPERIENCED,
                state="GA"
            )
            
            to_scenario = ROIScenario(
                current_income=55000,
                industry_type=IndustryType.RESIDENTIAL,
                geographic_market=to_market,
                experience_level=ExperienceLevel.EXPERIENCED,
                state="TX"
            )
            
            from_results = self.calculator.calculate_comprehensive_roi(from_scenario)
            to_results = self.calculator.calculate_comprehensive_roi(to_scenario)
            
            # Target market should always be better
            assert to_results.total_annual_income > from_results.total_annual_income
            assert to_results.geographic_multiplier > from_results.geographic_multiplier
    
    def test_opportunity_cost_calculations(self):
        """Test opportunity cost calculations for delays"""
        scenario = ROIScenario(
            current_income=65000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="GA"
        )
        
        results = self.calculator.calculate_comprehensive_roi(scenario)
        
        # Opportunity costs should be significant
        assert results.opportunity_cost_6_months > 20000
        assert results.opportunity_cost_1_year > 40000
        assert results.opportunity_cost_1_year > results.opportunity_cost_6_months
        
        # Should be roughly half of annual increase for 6 months
        expected_6_month = results.total_annual_increase / 2
        assert abs(results.opportunity_cost_6_months - expected_6_month) < 1000
    
    def test_financing_impact_calculations(self):
        """Test financing option impact calculations"""
        scenario = ROIScenario(
            current_income=55000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.SUBURBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            licensing_investment=4500
        )
        
        # Test 0% financing
        zero_percent = self.calculator.calculate_financing_impact(scenario, "0_percent")
        assert zero_percent['monthly_payment'] == 187.5  # 4500/24
        assert zero_percent['cash_preserved'] == 4500
        
        # Test payment plan
        payment_plan = self.calculator.calculate_financing_impact(scenario, "payment_plan")
        assert payment_plan['monthly_payment'] == 375  # 4500/12
    
    def test_income_tier_analysis(self):
        """Test income tier analysis across different brackets"""
        income_tiers = [30000, 50000, 75000, 100000]
        results = self.calculator.get_income_tier_analysis(income_tiers)
        
        assert len(results) == len(income_tiers)
        
        # Higher income tiers should generally have better absolute gains
        prev_income = 0
        for income in sorted(income_tiers):
            assert income in results
            assert results[income]['projected_income'] > results[income]['current_income']
            assert results[income]['roi_percentage'] > 500  # Should be substantial ROI
            
            if prev_income > 0:
                # Higher income should generally mean higher absolute gains
                prev_gain = results[prev_income]['income_increase']
                current_gain = results[income]['income_increase']
                assert current_gain > prev_gain
            
            prev_income = income
    
    def test_case_study_selection(self):
        """Test appropriate case study selection"""
        scenario = ROIScenario(
            current_income=45000,
            industry_type=IndustryType.RESIDENTIAL,
            geographic_market=GeographicMarket.URBAN,
            experience_level=ExperienceLevel.EXPERIENCED,
            state="GA"
        )
        
        results = self.calculator.calculate_comprehensive_roi(scenario)
        
        # Should have a case study
        assert results.case_study_name != ""
        assert results.case_study_description != ""
        assert len(results.case_study_description) > 50  # Should be detailed


class TestVAPIWebhookIntegration:
    """Test VAPI webhook integration"""
    
    @pytest.mark.asyncio
    async def test_webhook_basic_call(self):
        """Test basic webhook ROI calculation"""
        result = await calculate_roi_enhanced_webhook(
            call_id="test-call-001",
            current_income=65000,
            industry_type="residential",
            geographic_market="suburban",
            experience_years=5,
            state="GA"
        )
        
        # Should return formatted strings for VAPI
        assert isinstance(result['current_income'], str)
        assert '$' in result['current_income']
        assert isinstance(result['projected_income'], str)
        assert '$' in result['projected_income']
        assert isinstance(result['roi_percentage'], str)
        assert '%' in result['roi_percentage']
        assert 'days' in result['payback_days']
        assert result['summary'] != ""
    
    @pytest.mark.asyncio
    async def test_webhook_specialty_parameters(self):
        """Test webhook with specialty contractor parameters"""
        result = await calculate_roi_enhanced_webhook(
            call_id="test-call-002",
            current_income=75000,
            industry_type="specialty_electrical",
            geographic_market="boom_market",
            experience_years=8,
            state="TX",
            project_size=25000,
            monthly_projects=3,
            qualifier_network=True
        )
        
        # Specialty in boom market should show high returns
        projected_income = int(result['projected_income'].replace('$', '').replace(',', ''))
        assert projected_income > 200000
        
        roi_percentage = int(result['roi_percentage'].replace('%', '').replace(',', ''))
        assert roi_percentage > 2000
    
    @pytest.mark.asyncio
    async def test_webhook_entry_level_contractor(self):
        """Test webhook for entry level contractor"""
        result = await calculate_roi_enhanced_webhook(
            call_id="test-call-003",
            current_income=35000,
            industry_type="residential",
            geographic_market="rural",
            experience_years=1,
            state="AL",
            qualifier_network=False  # Not eligible yet
        )
        
        # Entry level should still show good returns
        projected_income = int(result['projected_income'].replace('$', '').replace(',', ''))
        current_income = int(result['current_income'].replace('$', '').replace(',', ''))
        
        assert projected_income > current_income * 1.5  # At least 50% increase
        assert 'Not eligible yet' in result['qualifier_income']  # Should note ineligibility
    
    @pytest.mark.asyncio  
    async def test_webhook_default_parameters(self):
        """Test webhook with default parameters"""
        result = await calculate_roi_enhanced_webhook(
            call_id="test-call-004"
        )
        
        # Should work with all defaults
        assert result['current_income'] == '$65,000'
        assert '$' in result['projected_income']
        assert '%' in result['roi_percentage']
        assert 'days' in result['payback_days']
        assert result['summary'] != ""


class TestROIDataValidation:
    """Test ROI calculation data validation"""
    
    def setup_method(self):
        self.calculator = EnhancedROICalculator()
    
    def test_multiplier_consistency(self):
        """Test that multipliers are consistent and realistic"""
        # Industry multipliers should be reasonable
        for industry, data in self.calculator.industry_multipliers.items():
            assert 1.5 <= data['base_multiplier'] <= 3.0
            assert 0.10 <= data['project_margin'] <= 0.30
            assert 1.5 <= data['hourly_premium'] <= 3.0
    
    def test_geographic_multiplier_progression(self):
        """Test that geographic multipliers progress logically"""
        markets = [
            GeographicMarket.RURAL,
            GeographicMarket.SMALL_TOWN,
            GeographicMarket.SUBURBAN,
            GeographicMarket.URBAN,
            GeographicMarket.MAJOR_METRO
        ]
        
        prev_multiplier = 0
        for market in markets:
            multiplier = self.calculator.geographic_multipliers[market]['income_multiplier']
            if prev_multiplier > 0:
                assert multiplier >= prev_multiplier  # Should increase or stay same
            prev_multiplier = multiplier
    
    def test_experience_level_progression(self):
        """Test that experience levels provide logical progression"""
        levels = [
            ExperienceLevel.ENTRY_LEVEL,
            ExperienceLevel.EXPERIENCED,
            ExperienceLevel.VETERAN,
            ExperienceLevel.MASTER
        ]
        
        prev_rate = 0
        for level in levels:
            rate = self.calculator.experience_adjustments[level]['qualifier_rate']
            if prev_rate > 0:
                assert rate >= prev_rate  # Should increase
            prev_rate = rate
    
    def test_state_factors_reasonable(self):
        """Test that state factors are within reasonable ranges"""
        for state, factors in self.calculator.state_factors.items():
            assert 0.8 <= factors['demand'] <= 1.5
            assert 0.8 <= factors['rates'] <= 1.4
            assert 0.8 <= factors['qualifier_demand'] <= 1.5


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
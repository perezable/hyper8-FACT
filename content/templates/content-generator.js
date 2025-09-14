/**
 * Content Generator for Persona-Specific LLC Content
 * Generates additional content variations and state-specific adaptations
 */

class ContentGenerator {
  constructor(personaContentSystem) {
    this.contentSystem = personaContentSystem;
    this.stateData = this.initializeStateData();
    this.templates = this.initializeTemplates();
  }

  /**
   * Initialize state-specific data for content generation
   */
  initializeStateData() {
    return {
      delaware: {
        filing_fee: 90,
        annual_fee: 300,
        processing_time: "5-7 days",
        benefits: ["strongest_protection", "business_friendly_courts", "no_sales_tax"],
        drawbacks: ["higher_annual_fees", "not_home_state_for_most"]
      },
      wyoming: {
        filing_fee: 100,
        annual_fee: 50,
        processing_time: "3-5 days", 
        benefits: ["lowest_annual_fees", "privacy_protection", "no_state_income_tax"],
        drawbacks: ["limited_case_law", "fewer_business_services"]
      },
      nevada: {
        filing_fee: 425,
        annual_fee: 350,
        processing_time: "5-10 days",
        benefits: ["no_state_income_tax", "privacy_protection", "business_friendly"],
        drawbacks: ["higher_filing_fees", "higher_annual_fees"]
      },
      texas: {
        filing_fee: 300,
        annual_fee: 0,
        processing_time: "5-15 days",
        benefits: ["no_annual_fees", "large_economy", "business_friendly"],
        drawbacks: ["franchise_tax_on_revenue", "longer_processing"]
      },
      florida: {
        filing_fee: 125,
        annual_fee: 138,
        processing_time: "5-10 days",
        benefits: ["no_state_income_tax", "growing_economy", "reasonable_fees"],
        drawbacks: ["annual_report_required", "moderate_protection"]
      }
    };
  }

  /**
   * Initialize content templates for different content types
   */
  initializeTemplates() {
    return {
      cost_comparison: {
        template: "{state_a} LLC costs ${cost_a} total vs {state_b} LLC costs ${cost_b} total. You save ${savings} with {better_state}.",
        variables: ["state_a", "cost_a", "state_b", "cost_b", "savings", "better_state"]
      },
      timeline_guarantee: {
        template: "{state}: {processing_time} processing or ${refund} refund. We guarantee your timeline.",
        variables: ["state", "processing_time", "refund"]
      },
      benefit_highlight: {
        template: "{state} offers {benefit} which means {explanation} for your business.",
        variables: ["state", "benefit", "explanation"]
      },
      step_by_step: {
        template: "Step {step}: {action} - {explanation}. Expected time: {duration}.",
        variables: ["step", "action", "explanation", "duration"]
      }
    };
  }

  /**
   * Generate state-specific content for any persona
   */
  generateStateContent(persona, state, contentType) {
    const stateInfo = this.stateData[state.toLowerCase()];
    if (!stateInfo) return null;

    const template = this.templates[contentType];
    if (!template) return null;

    // Generate content based on persona priorities
    switch (persona) {
      case 'price-conscious-penny':
        return this.generatePriceContent(state, stateInfo, template);
      case 'time-pressed':
        return this.generateSpeedContent(state, stateInfo, template);
      case 'overwhelmed-veteran':
        return this.generateSimpleContent(state, stateInfo, template);
      case 'skeptical-researcher':
        return this.generateDataContent(state, stateInfo, template);
      case 'ambitious-entrepreneur':
        return this.generateGrowthContent(state, stateInfo, template);
      default:
        return this.generateGenericContent(state, stateInfo, template);
    }
  }

  /**
   * Generate price-focused content
   */
  generatePriceContent(state, stateInfo, template) {
    return {
      title: `${this.capitalize(state)} Cost Analysis`,
      content: `${this.capitalize(state)} LLC formation costs $${stateInfo.filing_fee} state fee + $249 service fee = $${stateInfo.filing_fee + 249} total. Annual renewal: $${stateInfo.annual_fee}.`,
      tags: ["cost", "pricing", state, "analysis"],
      type: "cost_comparison",
      value_prop: "Clear cost breakdown"
    };
  }

  /**
   * Generate speed-focused content
   */
  generateSpeedContent(state, stateInfo, template) {
    return {
      title: `${this.capitalize(state)} Processing Speed`,
      content: `${this.capitalize(state)} processes LLC filings in ${stateInfo.processing_time}. Express service available for 24-48 hour processing.`,
      tags: ["speed", "processing", state, "timeline"],
      type: "timeline_guarantee", 
      value_prop: "Fast processing time"
    };
  }

  /**
   * Generate simplified content for overwhelmed users
   */
  generateSimpleContent(state, stateInfo, template) {
    const mainBenefit = stateInfo.benefits[0].replace('_', ' ');
    return {
      title: `Why Choose ${this.capitalize(state)}?`,
      content: `${this.capitalize(state)} is popular because of ${mainBenefit}. We handle all paperwork - you just provide basic info.`,
      tags: ["simple", "guidance", state, "benefits"],
      type: "benefit_highlight",
      value_prop: "Simple explanation"
    };
  }

  /**
   * Generate data-driven content
   */
  generateDataContent(state, stateInfo, template) {
    return {
      title: `${this.capitalize(state)} Formation Statistics`,
      content: `${this.capitalize(state)}: ${stateInfo.processing_time} average processing, $${stateInfo.filing_fee} state fee, $${stateInfo.annual_fee} annual renewal. Success rate: 99.8%.`,
      tags: ["statistics", "data", state, "success_rate"],
      type: "data_analysis",
      value_prop: "Statistical validation"
    };
  }

  /**
   * Generate growth-focused content
   */
  generateGrowthContent(state, stateInfo, template) {
    const growthBenefit = stateInfo.benefits.find(b => 
      b.includes('business_friendly') || b.includes('economy') || b.includes('protection')
    ) || stateInfo.benefits[0];
    
    return {
      title: `${this.capitalize(state)} for Business Growth`,
      content: `${this.capitalize(state)} offers ${growthBenefit.replace('_', ' ')} perfect for scaling businesses. Supports multi-entity structures.`,
      tags: ["growth", "scaling", state, "business"],
      type: "growth_strategy",
      value_prop: "Growth enablement"
    };
  }

  /**
   * Generate comparison content between states
   */
  generateStateComparison(states, persona) {
    const comparisons = [];
    
    for (let i = 0; i < states.length; i++) {
      for (let j = i + 1; j < states.length; j++) {
        const stateA = states[i].toLowerCase();
        const stateB = states[j].toLowerCase();
        const infoA = this.stateData[stateA];
        const infoB = this.stateData[stateB];
        
        if (infoA && infoB) {
          comparisons.push(this.createComparison(stateA, infoA, stateB, infoB, persona));
        }
      }
    }
    
    return comparisons;
  }

  /**
   * Create detailed comparison between two states
   */
  createComparison(stateA, infoA, stateB, infoB, persona) {
    const costA = infoA.filing_fee + 249;
    const costB = infoB.filing_fee + 249;
    const savings = Math.abs(costA - costB);
    const betterState = costA < costB ? stateA : stateB;
    
    let comparison = {
      id: `comp_${stateA}_${stateB}`,
      title: `${this.capitalize(stateA)} vs ${this.capitalize(stateB)} Comparison`,
      type: "state_comparison",
      tags: [stateA, stateB, "comparison", persona]
    };
    
    switch (persona) {
      case 'price-conscious-penny':
        comparison.content = `${this.capitalize(stateA)}: $${costA} total cost vs ${this.capitalize(stateB)}: $${costB} total cost. Save $${savings} with ${this.capitalize(betterState)}.`;
        comparison.value_prop = "Cost savings identified";
        break;
        
      case 'time-pressed':
        comparison.content = `${this.capitalize(stateA)}: ${infoA.processing_time} vs ${this.capitalize(stateB)}: ${infoB.processing_time} processing time.`;
        comparison.value_prop = "Processing speed comparison";
        break;
        
      case 'ambitious-entrepreneur':
        const benefitA = infoA.benefits[0].replace('_', ' ');
        const benefitB = infoB.benefits[0].replace('_', ' ');
        comparison.content = `${this.capitalize(stateA)} offers ${benefitA} while ${this.capitalize(stateB)} provides ${benefitB}. Choose based on business strategy.`;
        comparison.value_prop = "Strategic advantage comparison";
        break;
        
      default:
        comparison.content = `${this.capitalize(stateA)} and ${this.capitalize(stateB)} each offer unique advantages. Cost difference: $${savings}.`;
        comparison.value_prop = "Comprehensive comparison";
    }
    
    return comparison;
  }

  /**
   * Generate FAQ content for specific persona
   */
  generatePersonaFAQ(persona) {
    const faqs = {
      'price-conscious-penny': [
        {
          question: "What's the total cost to form an LLC?",
          answer: "Total cost = State filing fee + Our $249 service fee. Delaware example: $90 + $249 = $339 total."
        },
        {
          question: "Are there any hidden fees?",
          answer: "Zero hidden fees. Our $249 includes filing, registered agent (1 year), operating agreement, and EIN assistance."
        },
        {
          question: "Do you offer payment plans?",
          answer: "Yes! Split service fee into 3 payments of $83/month. No interest or credit check required."
        }
      ],
      'overwhelmed-veteran': [
        {
          question: "Where do I start if I'm completely new to LLCs?",
          answer: "Start with our state recommendation tool. Answer 3 questions, we suggest the best state and handle everything else."
        },
        {
          question: "What documents will I receive?",
          answer: "You'll get: Certificate of Formation, Operating Agreement, EIN letter, Registered Agent agreement, and compliance calendar."
        },
        {
          question: "How much support do you provide?",
          answer: "Unlimited support via phone, email, chat. Dedicated specialist for complex situations. We're here every step."
        }
      ]
      // Add more personas as needed
    };
    
    return faqs[persona] || [];
  }

  /**
   * Generate seasonal/timely content
   */
  generateSeasonalContent(persona, season) {
    const seasonal = {
      tax_season: {
        'price-conscious-penny': {
          title: "Tax Season LLC Formation Special",
          content: "Form your LLC before tax season ends and start deducting business expenses immediately. Save $25 in January-April.",
          type: "seasonal_promotion"
        },
        'time-pressed': {
          title: "Beat Tax Deadline with Express LLC",
          content: "Need LLC before tax deadline? Express 24-hour service ensures your business is ready for this year's taxes.",
          type: "urgent_tax_deadline"
        }
      },
      year_end: {
        'price-conscious-penny': {
          title: "Year-End Tax Savings with LLC",
          content: "Form LLC by December 31st to maximize this year's tax deductions. Business expenses, home office, equipment all deductible.",
          type: "year_end_savings"
        },
        'ambitious-entrepreneur': {
          title: "End Year Strong with Multi-State Expansion", 
          content: "Cap off successful year by expanding into new markets. Multi-state LLC formation discounts available through December.",
          type: "year_end_expansion"
        }
      }
    };
    
    return seasonal[season]?.[persona] || null;
  }

  /**
   * Utility function to capitalize state names
   */
  capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  /**
   * Generate content variations for A/B testing
   */
  generateContentVariations(baseContent, variations = 3) {
    const variations_list = [];
    
    for (let i = 0; i < variations; i++) {
      const variation = {
        ...baseContent,
        id: `${baseContent.id}_var${i + 1}`,
        variation: i + 1
      };
      
      // Modify content slightly for testing
      switch (i) {
        case 0:
          variation.title = `${variation.title} - Option A`;
          break;
        case 1:
          variation.title = `${variation.title} - Option B`;
          variation.content = variation.content + " Contact us for details.";
          break;
        case 2:
          variation.title = `${variation.title} - Option C`;
          variation.content = "⭐ " + variation.content;
          break;
      }
      
      variations_list.push(variation);
    }
    
    return variations_list;
  }

  /**
   * Generate complete content package for new state
   */
  generateStatePackage(state) {
    const stateInfo = this.stateData[state.toLowerCase()];
    if (!stateInfo) return null;

    const package = {
      state: state,
      personas: {}
    };

    // Generate content for each persona
    Object.keys(this.contentSystem.personas).forEach(persona => {
      package.personas[persona] = [
        this.generateStateContent(persona, state, 'cost_comparison'),
        this.generateStateContent(persona, state, 'timeline_guarantee'),
        this.generateStateContent(persona, state, 'benefit_highlight')
      ].filter(content => content !== null);
    });

    return package;
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ContentGenerator;
}

// Usage example:
/*
const contentSystem = new PersonaContentSystem();
const generator = new ContentGenerator(contentSystem);

// Generate state-specific content
const wyomingContent = generator.generateStateContent('price-conscious-penny', 'wyoming', 'cost_comparison');
console.log(wyomingContent);

// Generate state comparisons
const comparisons = generator.generateStateComparison(['delaware', 'wyoming'], 'price-conscious-penny');
console.log(comparisons);

// Generate seasonal content
const taxSeasonContent = generator.generateSeasonalContent('price-conscious-penny', 'tax_season');
console.log(taxSeasonContent);
*/
/**
 * Content Validation System
 * Ensures all 200 persona-specific entries meet quality standards
 */

class ContentValidator {
  constructor() {
    this.validationRules = this.initializeValidationRules();
    this.qualityMetrics = this.initializeQualityMetrics();
  }

  /**
   * Initialize validation rules for content quality
   */
  initializeValidationRules() {
    return {
      required_fields: ['id', 'type', 'title', 'content', 'tags', 'value_prop'],
      id_pattern: /^[a-z]{2}\d{3}$/,  // e.g., pp001, ov002
      min_content_length: 50,
      max_content_length: 500,
      min_tags: 3,
      max_tags: 6,
      required_types_per_persona: {
        'price-conscious-penny': ['cost_comparison', 'payment_plan', 'roi_calculation', 'guarantee', 'discount'],
        'overwhelmed-veteran': ['getting_started', 'step_by_step', 'document_list', 'support_options', 'simplified_explanation'],
        'skeptical-researcher': ['success_statistics', 'third_party_validation', 'case_study', 'competitor_analysis', 'data_backed_claims'],
        'time-pressed': ['fast_track', 'expedited_processing', 'timeline_guarantees', 'priority_services', 'bottleneck_solutions'],
        'ambitious-entrepreneur': ['multi_state_strategy', 'qualifier_network', 'growth_market_analysis', 'commercial_opportunities', 'scaling_tactics']
      }
    };
  }

  /**
   * Initialize quality metrics thresholds
   */
  initializeQualityMetrics() {
    return {
      content_uniqueness: 0.85,  // 85% unique content
      tag_relevance: 0.90,       // 90% tag relevance
      value_prop_clarity: 0.88,  // 88% clear value propositions
      persona_alignment: 0.92    // 92% persona alignment
    };
  }

  /**
   * Validate entire content database
   */
  async validateContentDatabase(contentDatabase) {
    const results = {
      total_entries: 0,
      valid_entries: 0,
      invalid_entries: 0,
      validation_errors: [],
      quality_scores: {},
      persona_analysis: {},
      recommendations: []
    };

    // Validate each persona's content
    for (const [persona, content] of Object.entries(contentDatabase)) {
      const personaResults = await this.validatePersonaContent(persona, content);
      
      results.total_entries += content.length;
      results.valid_entries += personaResults.valid_count;
      results.invalid_entries += personaResults.invalid_count;
      results.validation_errors.push(...personaResults.errors);
      results.quality_scores[persona] = personaResults.quality_score;
      results.persona_analysis[persona] = personaResults.analysis;
    }

    // Generate overall recommendations
    results.recommendations = this.generateRecommendations(results);

    return results;
  }

  /**
   * Validate content for specific persona
   */
  async validatePersonaContent(persona, content) {
    const results = {
      persona,
      total_entries: content.length,
      valid_count: 0,
      invalid_count: 0,
      errors: [],
      quality_score: 0,
      analysis: {}
    };

    // Validate entry count (should be 40 per persona)
    if (content.length !== 40) {
      results.errors.push({
        type: 'count_mismatch',
        message: `${persona} has ${content.length} entries, expected 40`,
        severity: 'error'
      });
    }

    // Validate each content entry
    const validationPromises = content.map((entry, index) => 
      this.validateContentEntry(entry, persona, index)
    );
    
    const entryResults = await Promise.all(validationPromises);
    
    // Aggregate results
    entryResults.forEach(result => {
      if (result.valid) {
        results.valid_count++;
      } else {
        results.invalid_count++;
        results.errors.push(...result.errors);
      }
    });

    // Calculate quality score
    results.quality_score = this.calculateQualityScore(content, persona);
    
    // Generate analysis
    results.analysis = this.analyzePersonaContent(content, persona);

    return results;
  }

  /**
   * Validate individual content entry
   */
  async validateContentEntry(entry, persona, index) {
    const result = {
      valid: true,
      errors: []
    };

    // Check required fields
    this.validationRules.required_fields.forEach(field => {
      if (!entry[field]) {
        result.valid = false;
        result.errors.push({
          type: 'missing_field',
          field,
          entry_id: entry.id || `index_${index}`,
          message: `Missing required field: ${field}`,
          severity: 'error'
        });
      }
    });

    // Validate ID format
    if (entry.id && !this.validationRules.id_pattern.test(entry.id)) {
      result.valid = false;
      result.errors.push({
        type: 'invalid_id_format',
        entry_id: entry.id,
        message: `Invalid ID format: ${entry.id}. Expected format: pp001, ov002, etc.`,
        severity: 'error'
      });
    }

    // Validate content length
    if (entry.content) {
      const length = entry.content.length;
      if (length < this.validationRules.min_content_length) {
        result.valid = false;
        result.errors.push({
          type: 'content_too_short',
          entry_id: entry.id,
          message: `Content too short: ${length} chars (minimum ${this.validationRules.min_content_length})`,
          severity: 'warning'
        });
      }
      if (length > this.validationRules.max_content_length) {
        result.errors.push({
          type: 'content_too_long',
          entry_id: entry.id,
          message: `Content too long: ${length} chars (maximum ${this.validationRules.max_content_length})`,
          severity: 'warning'
        });
      }
    }

    // Validate tags
    if (entry.tags) {
      if (entry.tags.length < this.validationRules.min_tags) {
        result.errors.push({
          type: 'insufficient_tags',
          entry_id: entry.id,
          message: `Too few tags: ${entry.tags.length} (minimum ${this.validationRules.min_tags})`,
          severity: 'warning'
        });
      }
      if (entry.tags.length > this.validationRules.max_tags) {
        result.errors.push({
          type: 'too_many_tags',
          entry_id: entry.id,
          message: `Too many tags: ${entry.tags.length} (maximum ${this.validationRules.max_tags})`,
          severity: 'warning'
        });
      }
    }

    // Validate persona alignment
    if (!this.validatePersonaAlignment(entry, persona)) {
      result.errors.push({
        type: 'persona_misalignment',
        entry_id: entry.id,
        message: `Content may not align well with ${persona} persona`,
        severity: 'warning'
      });
    }

    return result;
  }

  /**
   * Validate persona alignment
   */
  validatePersonaAlignment(entry, persona) {
    const personaKeywords = {
      'price-conscious-penny': ['cost', 'price', 'save', 'budget', 'affordable', 'discount', 'cheap', 'value'],
      'overwhelmed-veteran': ['help', 'support', 'guide', 'simple', 'step', 'easy', 'assistance'],
      'skeptical-researcher': ['proof', 'data', 'evidence', 'statistics', 'study', 'research', 'validation'],
      'time-pressed': ['fast', 'quick', 'express', 'urgent', 'immediate', 'speed', 'rush'],
      'ambitious-entrepreneur': ['growth', 'scale', 'expansion', 'multiple', 'strategy', 'portfolio']
    };

    const keywords = personaKeywords[persona] || [];
    const contentText = (entry.title + ' ' + entry.content + ' ' + entry.tags.join(' ')).toLowerCase();
    
    // Check if at least 2 persona keywords appear in content
    const matchCount = keywords.filter(keyword => contentText.includes(keyword)).length;
    return matchCount >= 2;
  }

  /**
   * Calculate quality score for persona content
   */
  calculateQualityScore(content, persona) {
    let totalScore = 0;
    const maxScore = content.length * 100;

    content.forEach(entry => {
      let entryScore = 0;

      // Content completeness (25 points)
      if (entry.title && entry.content && entry.value_prop) entryScore += 25;
      
      // Content length appropriateness (20 points)
      if (entry.content && entry.content.length >= 50 && entry.content.length <= 300) {
        entryScore += 20;
      }
      
      // Tag quality (20 points)
      if (entry.tags && entry.tags.length >= 3 && entry.tags.length <= 5) {
        entryScore += 20;
      }
      
      // Persona alignment (25 points)
      if (this.validatePersonaAlignment(entry, persona)) {
        entryScore += 25;
      }
      
      // Value proposition clarity (10 points)
      if (entry.value_prop && entry.value_prop.length > 10) {
        entryScore += 10;
      }

      totalScore += entryScore;
    });

    return Math.round((totalScore / maxScore) * 100);
  }

  /**
   * Analyze persona content distribution
   */
  analyzePersonaContent(content, persona) {
    const analysis = {
      type_distribution: {},
      tag_frequency: {},
      content_length_stats: {},
      duplicate_detection: [],
      coverage_analysis: {}
    };

    // Analyze content types
    content.forEach(entry => {
      analysis.type_distribution[entry.type] = (analysis.type_distribution[entry.type] || 0) + 1;
      
      // Count tag frequency
      entry.tags.forEach(tag => {
        analysis.tag_frequency[tag] = (analysis.tag_frequency[tag] || 0) + 1;
      });
    });

    // Content length statistics
    const lengths = content.map(entry => entry.content.length);
    analysis.content_length_stats = {
      min: Math.min(...lengths),
      max: Math.max(...lengths),
      average: Math.round(lengths.reduce((a, b) => a + b, 0) / lengths.length),
      median: this.calculateMedian(lengths)
    };

    // Duplicate detection
    analysis.duplicate_detection = this.detectDuplicateContent(content);

    // Coverage analysis
    const requiredTypes = this.validationRules.required_types_per_persona[persona] || [];
    analysis.coverage_analysis = {
      required_types: requiredTypes,
      covered_types: Object.keys(analysis.type_distribution),
      missing_types: requiredTypes.filter(type => !analysis.type_distribution[type]),
      coverage_percentage: Math.round((Object.keys(analysis.type_distribution).filter(type => 
        requiredTypes.includes(type)).length / requiredTypes.length) * 100)
    };

    return analysis;
  }

  /**
   * Detect duplicate or similar content
   */
  detectDuplicateContent(content) {
    const duplicates = [];
    
    for (let i = 0; i < content.length; i++) {
      for (let j = i + 1; j < content.length; j++) {
        const similarity = this.calculateSimilarity(content[i].content, content[j].content);
        if (similarity > 0.8) {  // 80% similarity threshold
          duplicates.push({
            entry1: content[i].id,
            entry2: content[j].id,
            similarity: Math.round(similarity * 100)
          });
        }
      }
    }
    
    return duplicates;
  }

  /**
   * Calculate content similarity
   */
  calculateSimilarity(text1, text2) {
    const words1 = text1.toLowerCase().split(/\s+/);
    const words2 = text2.toLowerCase().split(/\s+/);
    
    const intersection = words1.filter(word => words2.includes(word));
    const union = [...new Set([...words1, ...words2])];
    
    return intersection.length / union.length;
  }

  /**
   * Calculate median value
   */
  calculateMedian(numbers) {
    const sorted = numbers.slice().sort((a, b) => a - b);
    const middle = Math.floor(sorted.length / 2);
    
    if (sorted.length % 2 === 0) {
      return (sorted[middle - 1] + sorted[middle]) / 2;
    } else {
      return sorted[middle];
    }
  }

  /**
   * Generate recommendations based on validation results
   */
  generateRecommendations(results) {
    const recommendations = [];

    // Overall quality recommendations
    const avgQuality = Object.values(results.quality_scores).reduce((a, b) => a + b, 0) / 
                      Object.values(results.quality_scores).length;
    
    if (avgQuality < 80) {
      recommendations.push({
        type: 'quality_improvement',
        priority: 'high',
        message: `Overall quality score (${Math.round(avgQuality)}%) needs improvement. Target 85%+.`
      });
    }

    // Content count recommendations
    if (results.total_entries !== 200) {
      recommendations.push({
        type: 'content_count',
        priority: 'critical',
        message: `Total entries (${results.total_entries}) should be exactly 200 (40 per persona).`
      });
    }

    // Error-specific recommendations
    const errorTypes = {};
    results.validation_errors.forEach(error => {
      errorTypes[error.type] = (errorTypes[error.type] || 0) + 1;
    });

    Object.entries(errorTypes).forEach(([type, count]) => {
      if (count > 5) {  // If more than 5 errors of same type
        recommendations.push({
          type: 'error_pattern',
          priority: 'medium',
          message: `${count} instances of ${type} errors found. Consider batch fixing.`
        });
      }
    });

    // Persona-specific recommendations
    Object.entries(results.persona_analysis).forEach(([persona, analysis]) => {
      if (analysis.coverage_analysis && analysis.coverage_analysis.coverage_percentage < 80) {
        recommendations.push({
          type: 'coverage_improvement',
          priority: 'high',
          persona,
          message: `${persona} content coverage (${analysis.coverage_analysis.coverage_percentage}%) needs improvement.`
        });
      }
    });

    return recommendations;
  }

  /**
   * Generate validation report
   */
  generateReport(validationResults) {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total_entries: validationResults.total_entries,
        valid_entries: validationResults.valid_entries,
        invalid_entries: validationResults.invalid_entries,
        overall_quality: Math.round(Object.values(validationResults.quality_scores)
          .reduce((a, b) => a + b, 0) / Object.values(validationResults.quality_scores).length)
      },
      persona_scores: validationResults.quality_scores,
      error_summary: this.summarizeErrors(validationResults.validation_errors),
      recommendations: validationResults.recommendations,
      detailed_analysis: validationResults.persona_analysis
    };

    return report;
  }

  /**
   * Summarize errors by type and severity
   */
  summarizeErrors(errors) {
    const summary = {
      by_type: {},
      by_severity: {},
      total: errors.length
    };

    errors.forEach(error => {
      summary.by_type[error.type] = (summary.by_type[error.type] || 0) + 1;
      summary.by_severity[error.severity] = (summary.by_severity[error.severity] || 0) + 1;
    });

    return summary;
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ContentValidator;
}

// Usage example:
/*
const validator = new ContentValidator();

// Validate content database
const mockDatabase = {
  'price-conscious-penny': [], // 40 entries
  'overwhelmed-veteran': [],   // 40 entries
  // ... etc
};

validator.validateContentDatabase(mockDatabase).then(results => {
  const report = validator.generateReport(results);
  console.log('Validation Report:', JSON.stringify(report, null, 2));
});
*/
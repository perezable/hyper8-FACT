/**
 * Persona-Specific Content Management System
 * Matches customer queries to exact persona content for LLC formation
 */

class PersonaContentSystem {
  constructor() {
    this.personas = {
      'price-conscious-penny': {
        keywords: ['cost', 'price', 'cheap', 'affordable', 'budget', 'save', 'money', 'discount', 'fee', 'payment'],
        concerns: ['total_cost', 'hidden_fees', 'payment_plans', 'roi', 'value'],
        priority: 'financial'
      },
      'overwhelmed-veteran': {
        keywords: ['help', 'confused', 'complicated', 'overwhelmed', 'guide', 'step', 'support', 'assistance'],
        concerns: ['complexity', 'guidance', 'process', 'support', 'education'],
        priority: 'simplicity'
      },
      'skeptical-researcher': {
        keywords: ['proof', 'data', 'statistics', 'research', 'evidence', 'validation', 'study', 'comparison'],
        concerns: ['credibility', 'validation', 'track_record', 'success_rate', 'evidence'],
        priority: 'credibility'
      },
      'time-pressed': {
        keywords: ['fast', 'quick', 'urgent', 'rush', 'immediate', 'asap', 'deadline', 'express', 'speed'],
        concerns: ['timeline', 'speed', 'efficiency', 'express_service', 'guarantees'],
        priority: 'speed'
      },
      'ambitious-entrepreneur': {
        keywords: ['scale', 'growth', 'multiple', 'expansion', 'portfolio', 'strategy', 'investment', 'enterprise'],
        concerns: ['scalability', 'multi_state', 'growth', 'investment', 'strategy'],
        priority: 'growth'
      }
    };

    this.contentDatabase = {};
    this.loadPersonaContent();
  }

  /**
   * Load all persona content from JSON files
   */
  async loadPersonaContent() {
    const personaFiles = [
      'price-conscious-penny',
      'overwhelmed-veteran', 
      'skeptical-researcher',
      'time-pressed',
      'ambitious-entrepreneur'
    ];

    for (const persona of personaFiles) {
      try {
        const content = await this.loadJSON(`./personas/${persona}.json`);
        this.contentDatabase[persona] = content.content;
      } catch (error) {
        console.error(`Failed to load ${persona} content:`, error);
      }
    }
  }

  /**
   * Identify customer persona based on query analysis
   */
  identifyPersona(query, userContext = {}) {
    const queryLower = query.toLowerCase();
    const scores = {};

    // Score each persona based on keyword matches
    for (const [persona, config] of Object.entries(this.personas)) {
      scores[persona] = 0;
      
      // Keyword matching
      config.keywords.forEach(keyword => {
        if (queryLower.includes(keyword)) {
          scores[persona] += 2;
        }
      });

      // Concern matching
      config.concerns.forEach(concern => {
        if (queryLower.includes(concern.replace('_', ' '))) {
          scores[persona] += 3;
        }
      });

      // Context clues
      if (userContext.previousQueries) {
        const contextScore = this.analyzeContext(userContext.previousQueries, config);
        scores[persona] += contextScore;
      }
    }

    // Return highest scoring persona
    const topPersona = Object.keys(scores).reduce((a, b) => 
      scores[a] > scores[b] ? a : b
    );

    return {
      persona: topPersona,
      confidence: scores[topPersona],
      allScores: scores
    };
  }

  /**
   * Get targeted content for specific persona and query
   */
  getPersonaContent(persona, query, options = {}) {
    const content = this.contentDatabase[persona];
    if (!content) return null;

    // Filter content based on query relevance
    const relevantContent = this.filterRelevantContent(content, query);
    
    // Sort by relevance and return top matches
    const sortedContent = this.sortByRelevance(relevantContent, query);
    
    return {
      persona,
      totalContent: content.length,
      relevantContent: sortedContent.slice(0, options.limit || 5),
      personaConfig: this.personas[persona]
    };
  }

  /**
   * Filter content based on query relevance
   */
  filterRelevantContent(content, query) {
    const queryLower = query.toLowerCase();
    const queryWords = queryLower.split(' ').filter(word => word.length > 2);
    
    return content.filter(item => {
      const searchText = (item.title + ' ' + item.content + ' ' + item.tags.join(' ')).toLowerCase();
      
      // Check for direct keyword matches
      const hasKeywordMatch = queryWords.some(word => searchText.includes(word));
      
      // Check for tag matches
      const hasTagMatch = item.tags.some(tag => queryLower.includes(tag));
      
      // Check for type match
      const hasTypeMatch = queryLower.includes(item.type);
      
      return hasKeywordMatch || hasTagMatch || hasTypeMatch;
    });
  }

  /**
   * Sort content by relevance to query
   */
  sortByRelevance(content, query) {
    const queryLower = query.toLowerCase();
    const queryWords = queryLower.split(' ').filter(word => word.length > 2);
    
    return content.map(item => {
      let relevanceScore = 0;
      const searchText = (item.title + ' ' + item.content + ' ' + item.tags.join(' ')).toLowerCase();
      
      // Title matches are most important
      queryWords.forEach(word => {
        if (item.title.toLowerCase().includes(word)) relevanceScore += 5;
        if (item.content.toLowerCase().includes(word)) relevanceScore += 2;
        if (item.tags.some(tag => tag.includes(word))) relevanceScore += 3;
      });
      
      // Exact phrase matches
      if (searchText.includes(queryLower)) relevanceScore += 10;
      
      return { ...item, relevanceScore };
    }).sort((a, b) => b.relevanceScore - a.relevanceScore);
  }

  /**
   * Analyze user context for persona identification
   */
  analyzeContext(previousQueries, personaConfig) {
    let score = 0;
    const allQueries = previousQueries.join(' ').toLowerCase();
    
    personaConfig.keywords.forEach(keyword => {
      const count = (allQueries.match(new RegExp(keyword, 'g')) || []).length;
      score += count;
    });
    
    return score;
  }

  /**
   * Get comprehensive answer for specific query
   */
  getAnswerForQuery(query, userContext = {}) {
    // Identify persona
    const personaResult = this.identifyPersona(query, userContext);
    
    // Get relevant content
    const content = this.getPersonaContent(personaResult.persona, query, { limit: 3 });
    
    // Construct comprehensive answer
    return {
      persona: personaResult.persona,
      confidence: personaResult.confidence,
      answer: this.constructAnswer(content, query),
      supportingContent: content.relevantContent,
      alternatives: this.getAlternativeContent(query, personaResult.persona)
    };
  }

  /**
   * Construct comprehensive answer from content
   */
  constructAnswer(content, query) {
    if (!content || !content.relevantContent.length) {
      return "I'd be happy to help with your LLC formation question. Could you provide more specific details?";
    }

    const topContent = content.relevantContent[0];
    let answer = topContent.content;
    
    // Add supporting information from other relevant content
    if (content.relevantContent.length > 1) {
      answer += "\n\nAdditionally:";
      content.relevantContent.slice(1, 3).forEach(item => {
        answer += `\n• ${item.title}: ${item.content.substring(0, 100)}...`;
      });
    }
    
    return answer;
  }

  /**
   * Get alternative content for broader context
   */
  getAlternativeContent(query, primaryPersona) {
    const alternatives = {};
    
    Object.keys(this.personas).forEach(persona => {
      if (persona !== primaryPersona) {
        const content = this.getPersonaContent(persona, query, { limit: 1 });
        if (content && content.relevantContent.length > 0) {
          alternatives[persona] = content.relevantContent[0];
        }
      }
    });
    
    return alternatives;
  }

  /**
   * Get all content for a specific state
   */
  getStateSpecificContent(state) {
    const stateContent = {};
    
    Object.keys(this.contentDatabase).forEach(persona => {
      const content = this.contentDatabase[persona];
      stateContent[persona] = content.filter(item => 
        item.tags.includes(state.toLowerCase()) || 
        item.content.toLowerCase().includes(state.toLowerCase())
      );
    });
    
    return stateContent;
  }

  /**
   * Get content analytics
   */
  getContentAnalytics() {
    const analytics = {
      totalEntries: 0,
      contentByPersona: {},
      contentByType: {},
      mostCommonTags: {}
    };

    Object.keys(this.contentDatabase).forEach(persona => {
      const content = this.contentDatabase[persona];
      analytics.totalEntries += content.length;
      analytics.contentByPersona[persona] = content.length;
      
      // Analyze content types and tags
      content.forEach(item => {
        analytics.contentByType[item.type] = (analytics.contentByType[item.type] || 0) + 1;
        
        item.tags.forEach(tag => {
          analytics.mostCommonTags[tag] = (analytics.mostCommonTags[tag] || 0) + 1;
        });
      });
    });

    return analytics;
  }

  /**
   * Helper method to load JSON (would be replaced with actual file loading)
   */
  async loadJSON(filepath) {
    // In a real implementation, this would load from the file system
    // For now, returning a placeholder structure
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ content: [] });
      }, 100);
    });
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PersonaContentSystem;
}

// Usage example:
/*
const contentSystem = new PersonaContentSystem();

// Example queries and expected persona matches:
const testQueries = [
  "What's the cheapest state to form an LLC?", // price-conscious-penny
  "I'm confused about LLC formation, can you help?", // overwhelmed-veteran  
  "Show me success rate statistics for LLC formation", // skeptical-researcher
  "I need to form an LLC today, what's the fastest option?", // time-pressed
  "I want to form LLCs in multiple states for expansion" // ambitious-entrepreneur
];

testQueries.forEach(query => {
  const result = contentSystem.getAnswerForQuery(query);
  console.log(`Query: ${query}`);
  console.log(`Persona: ${result.persona} (${result.confidence}% confidence)`);
  console.log(`Answer: ${result.answer.substring(0, 150)}...`);
  console.log('---');
});
*/
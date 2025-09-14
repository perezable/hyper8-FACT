# Comprehensive 200-Question Test Suite

This directory contains a comprehensive test suite for evaluating the HVAC Training Knowledge System across all knowledge categories and difficulty levels.

## 🎯 Test Suite Overview

### Total Coverage: 200 Questions

**By Category:**
- **State Licensing**: 50 questions (25%) - All US states, requirements, reciprocity
- **Payment/Financing**: 20 questions (10%) - Costs, payment plans, financial aid
- **ROI/Income Potential**: 20 questions (10%) - Salaries, career growth, specialization pay
- **Specialty Trades**: 20 questions (10%) - Refrigeration, boilers, industrial systems
- **Federal Contracting**: 10 questions (5%) - Government contracts, certifications
- **Timeline/Speed**: 15 questions (7.5%) - Training duration, certification speed
- **Success Stories**: 15 questions (7.5%) - Career change examples, income growth
- **Objection Handling**: 20 questions (10%) - Common concerns and responses
- **Persona-Specific**: 30 questions (15%) - Targeted for 5 personas (6 each)

**By Difficulty:**
- **Basic**: 60 questions (30%) - Fundamental concepts
- **Intermediate**: 100 questions (50%) - Detailed knowledge
- **Advanced**: 40 questions (20%) - Expert-level understanding

**By Persona:**
- Career Changer (6 questions)
- Young Adult (6 questions)  
- Military Veteran (6 questions)
- Unemployed (6 questions)
- Skilled Tradesperson (6 questions)

## 📁 Files

- `comprehensive_200_question_test.py` - Main test suite (executable)
- `run_comprehensive_test.py` - Interactive runner with demo modes
- `TEST_SUITE_README.md` - This documentation

## 🚀 Running the Tests

### Option 1: Full Test Suite (Recommended)
```bash
cd /Users/natperez/codebases/hyper8/hyper8-FACT/tests
python3 comprehensive_200_question_test.py
```

### Option 2: Interactive Runner
```bash
python3 run_comprehensive_test.py
```

**Interactive options:**
1. Show Test Overview - See test structure and coverage
2. Run Quick Demo - Test 10 sample questions
3. Run Category Sample - Test 2 questions per category
4. Run Full Test Suite - All 200 questions
5. Exit

### Option 3: Direct Execution
```bash
./comprehensive_200_question_test.py
```

## 📊 Test Results

### Scoring System

**Question Scoring (0-100%):**
- Keyword matching (70% weight)
- Response quality/length (30% weight)
- Pass threshold: 70%

**Overall Grades:**
- A+ (95-100%) - Exceptional
- A (90-94%) - Excellent  
- B+ (80-89%) - Good
- B (70-79%) - Satisfactory
- C (60-69%) - Needs Improvement
- D/F (<60%) - Poor Performance

### Metrics Tracked

**Performance Metrics:**
- Overall accuracy score (0-100%)
- Pass/fail rate by category
- Response latency (seconds)
- Keyword match accuracy
- Persona alignment scores

**Category Analysis:**
- Questions per category
- Pass rates by category
- Average accuracy scores
- Failed question identification

**Difficulty Breakdown:**
- Performance by difficulty level
- Pass rates for each level
- Time analysis by complexity

## 📈 Output Files

Results are automatically saved as JSON files:

**Filename Format:**
```
test_results_YYYYMMDD_HHMMSS.json
```

**Contains:**
- Complete test results
- Question-by-question analysis
- Category breakdowns
- Performance metrics
- Failed questions list
- Execution metadata

## 🎯 Test Categories Explained

### 1. State Licensing (50 questions)
Tests knowledge of licensing requirements across all US states, including reciprocity agreements and renewal processes.

### 2. Payment/Financing (20 questions)
Evaluates understanding of training costs, payment options, financial aid, and ROI calculations.

### 3. ROI/Income Potential (20 questions)
Assesses knowledge of HVAC salary ranges, career growth potential, and specialization premiums.

### 4. Specialty Trades (20 questions)
Tests understanding of specialized HVAC areas like commercial refrigeration, boiler systems, and industrial applications.

### 5. Federal Contracting (10 questions)
Evaluates knowledge of government contracting requirements, security clearances, and federal certifications.

### 6. Timeline/Speed (15 questions)
Tests understanding of training durations, certification timelines, and accelerated programs.

### 7. Success Stories (15 questions)
Assesses ability to share relevant career transition examples and income growth stories.

### 8. Objection Handling (20 questions)
Evaluates responses to common concerns like age, cost, job security, and career viability.

### 9. Persona-Specific (30 questions)
Tests tailored responses for different audience segments with specific needs and concerns.

## 🔍 Understanding Results

### Interpreting Scores

**90%+ Overall Score:**
- System demonstrates excellent knowledge across all categories
- Ready for production deployment
- Minor refinements may be beneficial

**70-89% Overall Score:**
- Good foundational knowledge with room for improvement
- Focus on categories with lowest scores
- Additional training data recommended

**Below 70% Overall Score:**
- Significant knowledge gaps identified
- Comprehensive review and retraining needed
- Not recommended for production use

### Common Improvement Areas

**Low State Licensing Scores:**
- Add more state-specific licensing data
- Include recent regulation changes
- Expand reciprocity information

**Poor Objection Handling:**
- Practice addressing specific concerns
- Develop empathetic responses
- Include more success stories

**Weak Persona Alignment:**
- Tailor responses to audience needs
- Use appropriate language and examples
- Address persona-specific concerns

## 🛠️ Customization

### Adding Questions

To add more questions, modify the `_create_question_bank()` method in `comprehensive_200_question_test.py`:

```python
# Add to existing category
category_questions.append(
    TestQuestion(
        id=question_id,
        category="your_category",
        subcategory="specific_area", 
        difficulty="basic|intermediate|advanced",
        question="Your question text?",
        expected_keywords=["key1", "key2", "key3"],
        persona_alignment="general|specific_persona"
    )
)
```

### Modifying Scoring

Adjust scoring weights in the `_evaluate_response()` method:

```python
# Current weights
accuracy_score = (keyword_score * 0.7 + response_length_score * 0.3)

# Modify as needed
accuracy_score = (keyword_score * 0.8 + response_length_score * 0.2)
```

### Custom Categories

Add new categories by:
1. Creating questions with new category names
2. Updating the analysis methods
3. Adding category-specific evaluation criteria

## 📋 Best Practices

### Running Tests

1. **Run Regularly** - Execute after major training updates
2. **Compare Results** - Track improvement over time  
3. **Focus Improvements** - Address lowest-scoring categories first
4. **Validate Changes** - Test after each knowledge update

### Interpreting Results

1. **Look at Trends** - Compare multiple test runs
2. **Category Focus** - Identify consistent weak areas
3. **Question Analysis** - Review specific failed questions
4. **Response Quality** - Check for appropriate detail level

### Improving Performance

1. **Add Training Data** - Focus on failed question topics
2. **Enhance Keywords** - Update expected response terms
3. **Persona Training** - Improve audience-specific responses
4. **Response Templates** - Develop consistent answer formats

## 🚨 Troubleshooting

### Common Issues

**ImportError for HVACTrainingBot:**
- Test runs with mock responses if bot unavailable
- Implement actual bot integration for real testing

**Slow Performance:**
- Large test suite takes time to complete
- Use demo modes for quick validation
- Consider parallel execution for production

**Low Scores:**
- Review failed questions in detail
- Check keyword relevance and coverage
- Validate response quality expectations

### Getting Help

1. Check the failed questions list in results
2. Review response examples for patterns
3. Analyze category-specific performance
4. Compare with baseline expectations

## 📞 Support

For questions about the test suite:
1. Review this documentation
2. Check the code comments in test files
3. Analyze sample outputs and results
4. Consider customization for specific needs
# FACT System Response Evaluation Framework

A comprehensive evaluation framework for assessing the quality of FACT system responses across multiple dimensions and customer personas.

## Overview

This framework provides:
- **Multi-dimensional scoring** (Accuracy, Completeness, Relevance, Clarity, Persona-fit)
- **Persona-specific evaluation** (Price-conscious, Overwhelmed, Skeptical, Time-pressed, Ambitious)
- **AI-powered assessment** with rule-based fallbacks
- **Comprehensive reporting** and analytics
- **Automated quality metrics** and trend analysis

## Architecture

```
evaluation/
├── config/
│   └── scoring_rubric.py      # Scoring dimensions and criteria
├── core/
│   └── response_evaluator.py  # Main evaluation engine
├── metrics/
│   └── quality_metrics.py     # Quality metrics calculator
├── reports/
│   └── evaluation_reporter.py # Report generation
├── utils/
│   └── evaluation_utils.py    # Utility functions
├── examples/
│   └── evaluation_demo.py     # Usage demonstration
└── tests/
    ├── test_scoring_rubric.py
    └── test_response_evaluator.py
```

## Scoring Framework

### Dimensions (0-100 scale)

1. **Accuracy (40% weight)**: Factual correctness and reliability
2. **Completeness (20% weight)**: Covers all relevant aspects
3. **Relevance (20% weight)**: Directly addresses the question
4. **Clarity (10% weight)**: Easy to understand and well-structured
5. **Persona-fit (10% weight)**: Appropriate for customer type

### Score Categories

- **90-100 Excellent**: Perfect answer with extras
- **70-89 Good**: Solid answer, minor gaps
- **50-69 Adequate**: Basic answer, some issues
- **30-49 Poor**: Significant problems
- **0-29 Failed**: Wrong or missing answer

### Persona-Specific Criteria

#### Price-Conscious
- **Focus**: Cost, value, budget considerations
- **Keywords**: "cost", "price", "budget", "affordable", "value", "ROI"
- **Requirements**: Clear pricing, value proposition, cost comparisons

#### Overwhelmed
- **Focus**: Simplicity, guidance, support
- **Keywords**: "simple", "easy", "step-by-step", "help", "support"
- **Requirements**: Jargon-free language, clear steps, reassuring tone

#### Skeptical
- **Focus**: Proof, evidence, credibility
- **Keywords**: "proof", "evidence", "data", "verified", "guarantee"
- **Requirements**: Concrete evidence, credible sources, addresses concerns

#### Time-Pressed
- **Focus**: Speed, efficiency, immediate value
- **Keywords**: "quick", "fast", "immediate", "efficient", "now"
- **Requirements**: Concise responses, prioritized information, clear actions

#### Ambitious
- **Focus**: Growth, scalability, competitive advantage
- **Keywords**: "growth", "scale", "competitive", "opportunity", "strategic"
- **Requirements**: Growth focus, strategic perspective, scalability

## Quick Start

### Basic Usage

```python
from evaluation import ResponseEvaluator, EvaluationCriteria, PersonaType

# Create evaluator
evaluator = ResponseEvaluator(enable_ai_scoring=False)

# Define evaluation criteria
criteria = EvaluationCriteria(
    question="What are your pricing plans?",
    expected_elements=["pricing", "features", "value"],
    persona=PersonaType.PRICE_CONSCIOUS,
    context={}
)

# Evaluate response
result = await evaluator.evaluate_response(
    response_id="response_001",
    response_text="Our plans start at $29/month...",
    evaluation_criteria=criteria
)

print(f"Score: {result.weighted_score}/100 ({result.score_category})")
```

### Batch Evaluation

```python
# Evaluate multiple responses
responses = [
    {
        "id": "resp_001",
        "response": "Response text...",
        "criteria": {
            "question": "Question text",
            "expected_elements": ["element1", "element2"],
            "persona": PersonaType.PRICE_CONSCIOUS,
            "context": {}
        }
    }
    # ... more responses
]

results = await evaluator.batch_evaluate(responses)
```

### Generate Reports

```python
from evaluation.reports import EVALUATION_REPORTER
from evaluation.metrics import QUALITY_METRICS_CALCULATOR

# Calculate metrics
metrics = QUALITY_METRICS_CALCULATOR.calculate_metrics(results)

# Generate comprehensive report
report_file = EVALUATION_REPORTER.generate_comprehensive_report(
    results,
    report_name="monthly_evaluation",
    include_raw_data=True
)

# Generate dashboard
dashboard_file = EVALUATION_REPORTER.generate_summary_dashboard(
    results,
    dashboard_name="quality_dashboard"
)
```

## AI Integration

### Enable AI-Powered Scoring

```python
# With Claude
import anthropic
client = anthropic.Anthropic(api_key="your-key")
evaluator = ResponseEvaluator(ai_client=client, enable_ai_scoring=True)

# With OpenAI
import openai
client = openai.OpenAI(api_key="your-key")
evaluator = ResponseEvaluator(ai_client=client, enable_ai_scoring=True)
```

### Custom AI Integration

```python
class CustomAIEvaluator(ResponseEvaluator):
    async def _call_ai_evaluator(self, prompt: str) -> str:
        # Implement your AI client call
        response = await your_ai_client.complete(prompt)
        return response
```

## Quality Metrics

### Comprehensive Analytics

```python
metrics = QUALITY_METRICS_CALCULATOR.calculate_metrics(results)

print(f"Overall Score: {metrics.average_score}/100")
print(f"Consistency: {metrics.consistency_score}/100") 
print(f"Confidence: {metrics.confidence_average:.1%}")

# Dimension performance
for dim, score in metrics.dimension_averages.items():
    print(f"{dim}: {score}/100")

# Persona performance  
for persona, perf in metrics.persona_performance.items():
    print(f"{persona}: {perf['average_score']}/100")
```

### Trend Analysis

```python
trends = QUALITY_METRICS_CALCULATOR.calculate_trend_analysis(results)

for period, trend in trends.items():
    print(f"{period}: {trend.trend_direction} ({trend.trend_strength:.2f})")
```

## Export and Reporting

### Export Formats

```python
# CSV export
csv_file = EVALUATION_REPORTER.export_evaluation_data(
    results, format="csv", filename="evaluations"
)

# JSON export
json_file = EVALUATION_REPORTER.export_evaluation_data(
    results, format="json", filename="evaluations"
)

# Excel export (requires openpyxl)
xlsx_file = EVALUATION_REPORTER.export_evaluation_data(
    results, format="xlsx", filename="evaluations"
)
```

### Report Types

- **Comprehensive Report**: Full analysis with recommendations
- **Summary Dashboard**: Key metrics and alerts
- **Quality Report**: Detailed quality analysis
- **Trend Report**: Time-based performance analysis

## Testing

Run the test suite:

```bash
python -m pytest evaluation/tests/ -v
```

Run specific tests:

```bash
python -m pytest evaluation/tests/test_scoring_rubric.py -v
python -m pytest evaluation/tests/test_response_evaluator.py -v
```

## Demo

Run the evaluation demo:

```bash
python -m evaluation.examples.evaluation_demo
```

## Installation

Install required dependencies:

```bash
pip install -r requirements_evaluation.txt
```

Optional dependencies:
- `scipy`: For statistical analysis
- `openai`: For OpenAI integration
- `anthropic`: For Claude integration
- `openpyxl`: For Excel export

## Configuration

### Custom Scoring Weights

```python
from evaluation.config.scoring_rubric import ScoringRubric, ScoreDimension

# Modify weights (must sum to 1.0)
rubric = ScoringRubric()
rubric.dimensions[ScoreDimension.ACCURACY].weight = 0.5  # Increase accuracy weight
rubric.dimensions[ScoreDimension.COMPLETENESS].weight = 0.3
# ... adjust other dimensions
```

### Custom Persona Criteria

```python
from evaluation.config.scoring_rubric import PersonaScoring, PersonaType

# Add custom persona criteria
custom_criteria = PersonaScoring(
    persona=PersonaType.PRICE_CONSCIOUS,
    emphasis_keywords=["budget", "cost", "affordable"],
    required_elements=["Clear pricing information"],
    bonus_criteria=["Mentions discounts"],
    penalty_criteria=["Hidden costs"]
)
```

## Best Practices

1. **Use AI scoring when possible** for more nuanced evaluation
2. **Regularly calibrate** scoring criteria based on results
3. **Monitor confidence scores** to ensure evaluation quality
4. **Analyze trends** to identify improvement opportunities
5. **Export data regularly** for analysis and record-keeping

## Limitations

- Rule-based scoring may miss nuanced quality aspects
- AI scoring requires API keys and may have costs
- Large batch evaluations may be slow without optimization
- Statistical analysis requires sufficient data points

## Contributing

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure backward compatibility when possible

## License

This evaluation framework is part of the FACT system project.
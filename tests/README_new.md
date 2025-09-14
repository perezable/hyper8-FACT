# FACT System Automated Testing Framework

A comprehensive testing framework for evaluating the FACT (contractor licensing) system performance across multiple query methods with detailed accuracy analysis and performance metrics.

## 🎯 Features

- **Multi-Method Testing**: Tests database queries, VAPI webhooks, and REST API endpoints
- **Parallel Execution**: Concurrent testing with intelligent load balancing and rate limiting
- **Synthetic Question Generation**: Creates 200+ realistic test questions across all categories
- **Comprehensive Evaluation**: Accuracy, relevance, and completeness scoring for all responses
- **Performance Monitoring**: Response time, throughput, and error rate analysis
- **Flexible Configuration**: Separate configs for local, Railway production, and performance testing
- **Detailed Reporting**: JSON exports, human-readable reports, and performance charts

## 🚀 Quick Start

### 1. Installation

```bash
# Install testing framework dependencies
pip install -r tests/requirements.txt

# Install main FACT system dependencies
pip install -r requirements.txt
```

### 2. Run Tests

```bash
# Quick validation test (20 questions)
python tests/run_tests.py quick

# Full local test suite (200 questions)
python tests/run_tests.py local

# Test specific method only
python tests/run_tests.py database

# Generate test questions
python tests/run_tests.py questions
```

### 3. Railway Production Testing

```bash
# Set Railway database URL
export DATABASE_URL="postgresql://user:pass@host:port/db"

# Run production tests
python tests/run_tests.py railway
```

## 📁 Framework Structure

```
tests/
├── fact_test_runner.py      # Main test execution engine
├── query_executor.py        # Handles DB/VAPI/API queries with retry logic
├── response_collector.py    # Stores results and evaluates response quality
├── parallel_executor.py     # Manages concurrent execution
├── synthetic_questions.py   # Generates realistic test questions
├── run_tests.py            # Convenient CLI entry point
├── configs/
│   ├── local_test_config.yaml       # Local development settings
│   ├── railway_test_config.yaml     # Production testing settings
│   └── performance_test_config.yaml # Performance benchmarking
└── test_results/           # Output directory for all results
```

## 🔧 Configuration

### Test Environments

#### Local Development (`local_test_config.yaml`)
- **Questions**: 200 comprehensive test cases
- **Concurrency**: 10 parallel requests
- **Timeout**: 30 seconds
- **Methods**: Database, VAPI webhook, REST API
- **Rate Limit**: 10 requests/second

#### Railway Production (`railway_test_config.yaml`)
- **Questions**: 100 focused test cases
- **Concurrency**: 5 parallel requests (conservative)
- **Timeout**: 45 seconds
- **Rate Limit**: 3 requests/second
- **Thresholds**: Higher tolerance for network latency

#### Performance Testing (`performance_test_config.yaml`)
- **Questions**: 500 high-load test cases
- **Concurrency**: 25 parallel requests
- **Timeout**: 15 seconds
- **Rate Limit**: 25 requests/second
- **Thresholds**: Strict performance requirements

### Key Configuration Options

```yaml
# Query methods to test
query_methods:
  - database    # Direct database queries
  - vapi       # VAPI webhook calls
  - api        # REST API endpoints

# Performance thresholds
max_response_time_ms: 3000.0
min_accuracy_threshold: 0.7
max_error_rate: 0.15

# Parallel execution
max_concurrent_tests: 10
request_timeout: 30
max_retries: 3
```

## 🧪 Test Question Categories

The framework generates comprehensive test questions across 8 categories:

1. **State Licensing Requirements** (40% of tests)
   - License requirements by state
   - Experience and education requirements
   - Application processes and fees

2. **Exam Preparation & Testing** (20% of tests)
   - Exam formats and passing scores
   - Study materials and preparation
   - Retake policies and procedures

3. **Qualifier Network Programs** (10% of tests)
   - Network program benefits
   - Qualifier sponsorship
   - Business lead generation

4. **Business Formation & Operations** (10% of tests)
   - Legal entity formation
   - Business licenses and permits
   - Accounting and insurance setup

5. **Insurance & Bonding** (8% of tests)
   - Liability insurance requirements
   - Surety bond costs and processes
   - Workers compensation policies

6. **Financial Planning & ROI** (7% of tests)
   - Return on investment calculations
   - Income increase projections
   - Cost-benefit analysis

7. **Success Stories & Case Studies** (3% of tests)
   - Contractor success examples
   - Income transformation stories
   - Business growth testimonials

8. **Troubleshooting & Problem Resolution** (2% of tests)
   - License application issues
   - Exam failure recovery
   - Legal and compliance problems

## 📊 Evaluation Metrics

### Response Quality Scoring

Each response is evaluated across three dimensions:

#### 1. Accuracy Score (0-1)
- **Keyword Overlap**: Query terms present in response
- **Domain Relevance**: Contractor-specific terminology
- **Information Patterns**: Specific data (costs, timeframes, percentages)
- **System Confidence**: Response confidence metadata

#### 2. Relevance Score (0-1)
- **Category Matching**: Response aligns with expected category
- **State Specificity**: Correct state information when applicable
- **Context Appropriateness**: Response fits query context

#### 3. Completeness Score (0-1)
- **Response Length**: Appropriate detail level
- **Information Density**: Specific facts and figures
- **Structure Quality**: Well-organized, multi-sentence responses

### Performance Metrics

- **Response Time**: P50, P95, P99 latencies
- **Throughput**: Requests per second
- **Success Rate**: Percentage of successful queries
- **Error Analysis**: Categorized error types and frequencies
- **Resource Usage**: Memory and CPU consumption

## 🎮 Usage Examples

### Basic Testing

```bash
# Quick system health check
python tests/run_tests.py quick

# Full local test suite
python tests/run_tests.py local

# Test single method
python tests/run_tests.py database --env local
python tests/run_tests.py vapi --env railway
```

### Advanced Testing

```bash
# High-performance benchmarking
python tests/run_tests.py performance

# Custom configuration
python tests/fact_test_runner.py --config custom_config.yaml

# Generate specific question sets
python tests/synthetic_questions.py
```

### Programmatic Usage

```python
from fact_test_runner import FACTTestRunner, TestConfig
from query_executor import QueryMethod

# Create custom configuration
config = TestConfig(
    environment="local",
    test_question_count=50,
    query_methods=["database", "vapi"]
)

# Run tests
test_runner = FACTTestRunner(config)
await test_runner.initialize()
summary = await test_runner.run_comprehensive_test()

print(f"Success rate: {summary.overall_metrics['success_rate']:.1%}")
```

## 📈 Output Reports

### Test Results Structure

```
test_results/
├── local/
│   ├── raw_results_20240101_120000.json      # All individual results
│   ├── test_summary_20240101_120000.json     # Aggregated metrics
│   ├── test_report_20240101_120000.txt       # Human-readable report
│   └── test_questions_20240101_120000.json   # Generated questions
├── railway/
└── performance/
```

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Verify database file exists
ls -la data/fact_system.db

# Test direct database access
python -c "import sqlite3; print(sqlite3.connect('data/fact_system.db').execute('SELECT COUNT(*) FROM knowledge_base').fetchone())"
```

#### VAPI Webhook Failures
```bash
# Check webhook endpoint
curl -X POST http://localhost:8000/vapi/webhook/health

# Verify webhook schema
curl http://localhost:8000/vapi/webhook/schema
```

#### Railway Connection Issues
```bash
# Verify environment variable
echo $DATABASE_URL

# Test Railway API endpoint
curl https://hyper8-fact-production.up.railway.app/health
```

## 📋 Performance Benchmarks

### Expected Performance (Local)
- **Database Queries**: <500ms average
- **VAPI Webhooks**: <2000ms average  
- **API Endpoints**: <1500ms average
- **Success Rate**: >95%
- **Throughput**: >5 req/s

### Production Thresholds (Railway)
- **Response Time**: <5000ms
- **Success Rate**: >90%
- **Error Rate**: <10%
- **Accuracy Score**: >0.75

## 🛠 Legacy Tests

The following legacy tests are also available for specific validation:

### Validation and Fix Tests
- **`test_all_fixes.py`** - Comprehensive validation test for all FACT system fixes
- **`test_fixes_summary.py`** - Focused validation test for key FACT system fixes
- **`test_sql_fixes.py`** - Comprehensive test for SQL connector NoneType fixes

### Debug and Development Tests
- **`debug_sql_validation.py`** - Debug script for SQL validation issues
- **`test_basic_functionality.py`** - Basic system functionality tests

### Test Organization
- **`unit/`** - Unit tests for individual components
- **`integration/`** - Integration tests for component interactions
- **`performance/`** - Performance and load tests

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Run test suite (`python tests/run_tests.py local`)
5. Update documentation
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Create Pull Request

## 📝 License

This testing framework is part of the FACT System project. See the main project LICENSE file for details.
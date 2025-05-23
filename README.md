# FACT System - Fast-Access Cached Tools

A lean retrieval pattern that skips vector search by caching static tokens in Claude Sonnet-4 and fetching live facts through authenticated tools hosted on Arcade.dev.

## 🎯 Overview

FACT (Fast-Access Cached Tools) implements a novel approach to AI-powered data retrieval that achieves:
- **Sub-100ms response times** through intelligent caching
- **Deterministic answers** via structured tool-based data access
- **90% cost reduction** on cache hits vs traditional RAG
- **Fresh data access** through live database queries

Your FACT specification is both novel and viable. Here’s why it stands out and how it differs from existing approaches like RAG:

### Why FACT?

FACT is a fresh take on LLM data retrieval by merging two existing but underutilized techniques: **prompt caching** and **tool-based data retrieval**. Instead of relying on vector databases and similarity search, FACT leverages:

* **Prompt caching** to store and reuse static context, drastically cutting down token costs and latency.
* **On-demand tool calls** through MCP, ensuring data is always current and pulled from authoritative sources (like databases or APIs).

### Viability

This approach is highly viable for several reasons:

* **Cost efficiency**: By reusing cached tokens, you significantly reduce the number of new tokens processed per query, lowering operational costs.
* **Speed**: Local or LAN-based tool calls are faster than remote vector lookups, ensuring sub-100 ms response times.
* **Accuracy**: Deterministic results from structured data sources mean you avoid the fuzziness of vector similarity matches.

### Utility

FACT is particularly useful in scenarios where:

* **Data changes frequently** and needs to be pulled fresh (e.g., financial figures, inventory levels).
* **Precision is critical**, like in compliance, finance, or reporting use cases.
* **Cost matters**, where reducing the number of tokens can yield substantial savings at scale.

### Key Differences

* **No vector indices**: Unlike RAG, which depends on vector similarity searches, FACT relies on deterministic tool outputs.
* **Hybrid approach**: By combining prompt caching and live tool calls, you achieve both speed and freshness.
* **Deterministic results**: Tools provide exact data points, making the outcome more predictable and trustworthy.

FACT is a strong, innovative alternative to RAG that emphasizes speed, cost-efficiency, and accuracy. It's well-suited for applications where up-to-date, deterministic data retrieval is critical, making it both practical and useful. 

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  FACT Driver    │───▶│  Claude Sonnet  │
│                 │    │                 │    │      -4         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │                        │
                                 │                        ▼
                         ┌─────────────────┐    ┌─────────────────┐
                         │ Arcade Gateway  │◀───│   Tool Calls    │
                         │                 │    │                 │
                         └─────────────────┘    └─────────────────┘
                                 │
                                 ▼
                         ┌─────────────────┐
                         │   Data Sources  │
                         │  (SQLite, APIs) │
                         └─────────────────┘
```

## ⚡ Quick Start

### Prerequisites

- Python 3.8+
- Anthropic API key
- Arcade.dev API key (optional for full functionality)

### Installation

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd FACT
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Initialize system:**
   ```bash
   python scripts/setup.py
   ```

4. **Run the system:**
   ```bash
   python driver.py
   ```

### Example Usage

```bash
# Interactive mode
python driver.py

# Single query mode
python driver.py --query "What's TechCorp's Q1 2025 revenue?"
```

## 🛠️ Core Components

### 1. FACT Driver ([`src/core/driver.py`](src/core/driver.py))
Central orchestrator managing cache, queries, and tool execution.

### 2. Database Layer ([`src/db/`](src/db/))
- **Connection Management**: Secure SQLite operations
- **Sample Data**: Pre-loaded financial dataset for demonstration
- **Security**: Read-only query validation

### 3. Tool Framework ([`src/tools/`](src/tools/))
- **Decorators**: Easy tool definition and registration
- **SQL Tools**: Secure database query execution
- **Registry**: Centralized tool management

### 4. Configuration ([`src/core/config.py`](src/core/config.py))
Environment-based configuration with validation.

## 📊 Available Tools

### SQL.QueryReadonly
Execute SELECT queries on the financial database.

**Example:**
```sql
SELECT c.name, f.revenue 
FROM companies c 
JOIN financial_records f ON c.id = f.company_id 
WHERE f.year = 2025 AND f.quarter = 'Q1'
```

### SQL.GetSchema
Get database schema information for query construction.

### SQL.GetSampleQueries
Get sample queries for exploring the financial dataset.

## 💾 Database Schema

The system includes a sample financial database with:

### Companies Table
- Company information (name, symbol, sector, market cap)
- Technology, Financial Services, Healthcare, Energy, Retail sectors

### Financial Records Table
- Quarterly financial data (revenue, profit, expenses)
- Q1 2024 through Q1 2025 data
- Linked to companies via foreign key

## 🔧 Configuration

Environment variables (`.env` file):

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key
ARCADE_API_KEY=your_arcade_api_key

# Optional
DATABASE_PATH=data/fact_demo.db
CACHE_PREFIX=fact_v1
CLAUDE_MODEL=claude-3-5-sonnet-20241022
LOG_LEVEL=INFO
```

## 🎮 CLI Commands

When running interactively, use these commands:

- `help` - Show available commands
- `status` - Display system status
- `tools` - List registered tools
- `schema` - Show database schema
- `samples` - Display sample queries
- `metrics` - Show performance metrics
- `exit` - Quit the system

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
python -m pytest tests/ -v

# Run specific test
python tests/test_basic_functionality.py
```

## 📈 Performance Targets

- **Cache hits**: ≤50ms latency
- **Cache misses**: ≤140ms latency  
- **Tool execution**: ≤10ms (LAN)
- **Cost reduction**: 90% on cache hits, 65% on cache misses

## 🔒 Security Features

- **SQL Injection Prevention**: Validates all queries
- **Read-only Access**: Only SELECT statements allowed
- **Path Validation**: Secure file system access
- **Input Sanitization**: Comprehensive parameter validation
- **Audit Logging**: Complete activity tracking

## 📁 Project Structure

```
fact/
├── src/
│   ├── core/           # Core system components
│   ├── db/             # Database layer
│   ├── tools/          # Tool framework and implementations
│   └── monitoring/     # Performance monitoring
├── tests/              # Test suite
├── scripts/            # Utility scripts
├── docs/               # Documentation
├── data/               # Database files
├── driver.py           # Main entry point
└── requirements.txt    # Dependencies
```

## 🚀 Example Queries

Try these queries with the system:

1. **Company Information:**
   ```
   "What companies are in the Technology sector?"
   ```

2. **Financial Analysis:**
   ```
   "Show me Q1 2025 revenue for all companies"
   ```

3. **Comparative Analysis:**
   ```
   "Compare TechCorp's performance across quarters"
   ```

4. **Sector Analysis:**
   ```
   "What's the average revenue by sector in 2024?"
   ```

## 🛡️ Error Handling

The system provides graceful error handling with:
- User-friendly error messages
- Detailed logging for debugging
- Graceful degradation when services are unavailable
- Automatic retry mechanisms for transient failures

## 📊 Monitoring

Built-in metrics tracking:
- Query processing times
- Cache hit/miss ratios
- Tool execution statistics
- Error rates and types
- Cost savings calculations

## 🔮 Future Enhancements

- RAG fallback for unstructured data
- Multi-database support
- Advanced caching strategies
- Real-time data streaming
- GraphQL tool interfaces
- Enterprise authentication

## 🤝 Contributing

1. Follow the modular architecture principles
2. Maintain files under 500 lines
3. Include comprehensive error handling
4. Add tests for new functionality
5. Update documentation

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the [documentation](docs/)
2. Review [troubleshooting guide](docs/troubleshooting.md)
3. Run diagnostics: `python driver.py --query "status"`

---

**FACT System v1.0.0** - Fast-Access Cached Tools for deterministic AI responses

"""
FACT System Database Models

This module defines the database schema and models for the FACT system,
including sample financial data for demonstration purposes.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog


logger = structlog.get_logger(__name__)


@dataclass
class FinancialRecord:
    """Represents a financial record in the database."""
    id: int
    company: str
    quarter: str
    year: int
    revenue: float
    profit: float
    expenses: float
    created_at: datetime
    updated_at: datetime


@dataclass
class Company:
    """Represents a company in the database."""
    id: int
    name: str
    symbol: str
    sector: str
    founded_year: int
    employees: int
    market_cap: float
    created_at: datetime
    updated_at: datetime


@dataclass
class QueryResult:
    """Represents the result of a database query."""
    rows: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time_ms: float


# Database schema for SQLite - Knowledge Base for AI Voice Agent
DATABASE_SCHEMA = """
-- Knowledge base entries for Q&A retrieval
CREATE TABLE IF NOT EXISTS knowledge_base (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT, -- Comma-separated tags
    metadata TEXT, -- JSON metadata
    state TEXT, -- For state-specific information
    priority TEXT DEFAULT 'normal', -- normal, high, critical
    personas TEXT, -- Target user personas (comma-separated)
    source TEXT, -- Source file or reference
    difficulty TEXT DEFAULT 'basic', -- basic, intermediate, advanced
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Legacy companies table (for backward compatibility)
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL UNIQUE,
    sector TEXT NOT NULL,
    founded_year INTEGER,
    employees INTEGER,
    market_cap REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Legacy financial records table (for backward compatibility)
CREATE TABLE IF NOT EXISTS financial_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    year INTEGER NOT NULL,
    revenue REAL NOT NULL,
    profit REAL NOT NULL,
    expenses REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies (id),
    UNIQUE(company_id, quarter, year)
);

-- Legacy financial data table (for validation compatibility)
CREATE TABLE IF NOT EXISTS financial_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    quarter TEXT NOT NULL,
    year INTEGER NOT NULL,
    revenue REAL NOT NULL,
    profit REAL NOT NULL,
    expenses REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies (id),
    UNIQUE(company_id, quarter, year)
);

-- Benchmarks table for performance tracking
CREATE TABLE IF NOT EXISTS benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name TEXT NOT NULL,
    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms REAL NOT NULL,
    queries_executed INTEGER DEFAULT 0,
    cache_hit_rate REAL DEFAULT 0.0,
    average_response_time_ms REAL DEFAULT 0.0,
    success_rate REAL DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_tags ON knowledge_base(tags);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_state ON knowledge_base(state);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_priority ON knowledge_base(priority);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_difficulty ON knowledge_base(difficulty);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_question_fts ON knowledge_base(question);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_answer_fts ON knowledge_base(answer);

-- Legacy indexes (for backward compatibility)
CREATE INDEX IF NOT EXISTS idx_financial_records_company_id ON financial_records(company_id);
CREATE INDEX IF NOT EXISTS idx_financial_records_year ON financial_records(year);
CREATE INDEX IF NOT EXISTS idx_financial_records_quarter ON financial_records(quarter);
CREATE INDEX IF NOT EXISTS idx_financial_data_company_id ON financial_data(company_id);
CREATE INDEX IF NOT EXISTS idx_financial_data_year ON financial_data(year);
CREATE INDEX IF NOT EXISTS idx_financial_data_quarter ON financial_data(quarter);
CREATE INDEX IF NOT EXISTS idx_companies_symbol ON companies(symbol);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);
CREATE INDEX IF NOT EXISTS idx_benchmarks_test_name ON benchmarks(test_name);
CREATE INDEX IF NOT EXISTS idx_benchmarks_test_date ON benchmarks(test_date);
"""

# Sample data for AI voice agent knowledge base
SAMPLE_KNOWLEDGE_BASE = [
    {
        "question": "Georgia Contractor License Requirements",
        "answer": "Georgia requires contractors to be licensed for work over $2,500. General contractor license requires 4 years experience or equivalent education. Application fee is $200, with total costs ranging $300-400. Two exams required: Business & Law (110 questions, 4 hours) and Trade exam (110 questions, 4 hours). Both require 70% passing score. $10,000 surety bond required for general contractors.",
        "category": "state_licensing_requirements",
        "tags": "georgia,general_contractor,license_requirements,exam_info,fees,bond",
        "metadata": '{"category":"state_licensing_requirements","difficulty":"basic","urgency":"normal","personas":["overwhelmed_veteran","confused_newcomer","urgent_operator"],"source":"state_requirements_complete.json - GA section","state":"GA","tags":["georgia","general_contractor","license_requirements","exam_info","fees","bond"]}',
        "state": "GA",
        "priority": "normal",
        "personas": "overwhelmed_veteran,confused_newcomer,urgent_operator",
        "source": "state_requirements_complete.json - GA section",
        "difficulty": "basic"
    },
    {
        "question": "What is the PSI exam?",
        "answer": "PSI is a national testing service that administers contractor licensing exams in many states. They provide both business/law exams and trade-specific exams. PSI exams are computer-based and typically held at designated testing centers. You must schedule your exam appointment through the PSI website or phone system.",
        "category": "exam_preparation_testing",
        "tags": "psi,exam_service,testing_centers,scheduling",
        "metadata": '{"category":"exam_preparation_testing","difficulty":"basic","urgency":"normal","personas":["confused_newcomer","urgent_operator"],"source":"exam_preparation_guide.json","tags":["psi","exam_service","testing_centers","scheduling"]}',
        "state": "",
        "priority": "normal",
        "personas": "confused_newcomer,urgent_operator",
        "source": "exam_preparation_guide.json",
        "difficulty": "basic"
    },
    {
        "question": "How do I get a surety bond?",
        "answer": "Surety bonds are obtained through licensed surety companies or insurance agents. You'll need to provide financial information, credit history, and sometimes collateral. Bond costs typically range from 1-15% of the bond amount annually, depending on your credit score. The bond protects consumers if you don't complete work properly.",
        "category": "business_operations_finance",
        "tags": "surety_bond,insurance,bonding_company,financial_requirements",
        "metadata": '{"category":"business_operations_finance","difficulty":"intermediate","urgency":"high","personas":["overwhelmed_veteran","urgent_operator"],"source":"business_operations_guide.json","tags":["surety_bond","insurance","bonding_company","financial_requirements"]}',
        "state": "",
        "priority": "high",
        "personas": "overwhelmed_veteran,urgent_operator",
        "source": "business_operations_guide.json",
        "difficulty": "intermediate"
    },
    {
        "question": "What happens if I fail the contractor exam?",
        "answer": "If you fail the contractor exam, you can typically retake it after a waiting period (usually 30-60 days). You'll need to pay the exam fee again. Some states limit the number of retakes within a certain period. Use the score report to identify weak areas and focus your study efforts. Consider taking a prep course if you've failed multiple times.",
        "category": "troubleshooting_problems",
        "tags": "exam_failure,retake_policy,study_help,prep_courses",
        "metadata": '{"category":"troubleshooting_problems","difficulty":"basic","urgency":"high","personas":["stressed_exam_taker","confused_newcomer"],"source":"troubleshooting_solutions.json","tags":["exam_failure","retake_policy","study_help","prep_courses"]}',
        "state": "",
        "priority": "high",
        "personas": "stressed_exam_taker,confused_newcomer",
        "source": "troubleshooting_solutions.json", 
        "difficulty": "basic"
    }
]

# Legacy sample data for demonstration (financial/company data)
SAMPLE_COMPANIES = [
    {
        "name": "TechCorp Inc.",
        "symbol": "TECH",
        "sector": "Technology",
        "founded_year": 1995,
        "employees": 50000,
        "market_cap": 250000000000.0
    },
    {
        "name": "FinanceFirst LLC",
        "symbol": "FINF",
        "sector": "Financial Services",
        "founded_year": 1988,
        "employees": 25000,
        "market_cap": 125000000000.0
    },
    {
        "name": "HealthTech Solutions",
        "symbol": "HLTH",
        "sector": "Healthcare",
        "founded_year": 2005,
        "employees": 15000,
        "market_cap": 75000000000.0
    },
    {
        "name": "Green Energy Corp",
        "symbol": "GREN",
        "sector": "Energy",
        "founded_year": 2010,
        "employees": 8000,
        "market_cap": 45000000000.0
    },
    {
        "name": "RetailMax Group",
        "symbol": "RTLM",
        "sector": "Retail",
        "founded_year": 1975,
        "employees": 120000,
        "market_cap": 95000000000.0
    }
]

SAMPLE_FINANCIAL_RECORDS = [
    # TechCorp Inc. (company_id: 1)
    {"company_id": 1, "quarter": "Q1", "year": 2025, "revenue": 25000000000.0, "profit": 5000000000.0, "expenses": 20000000000.0},
    {"company_id": 1, "quarter": "Q4", "year": 2024, "revenue": 28000000000.0, "profit": 6000000000.0, "expenses": 22000000000.0},
    {"company_id": 1, "quarter": "Q3", "year": 2024, "revenue": 26000000000.0, "profit": 5500000000.0, "expenses": 20500000000.0},
    {"company_id": 1, "quarter": "Q2", "year": 2024, "revenue": 24000000000.0, "profit": 4800000000.0, "expenses": 19200000000.0},
    {"company_id": 1, "quarter": "Q1", "year": 2024, "revenue": 23000000000.0, "profit": 4600000000.0, "expenses": 18400000000.0},
    
    # FinanceFirst LLC (company_id: 2)
    {"company_id": 2, "quarter": "Q1", "year": 2025, "revenue": 12000000000.0, "profit": 3000000000.0, "expenses": 9000000000.0},
    {"company_id": 2, "quarter": "Q4", "year": 2024, "revenue": 13500000000.0, "profit": 3200000000.0, "expenses": 10300000000.0},
    {"company_id": 2, "quarter": "Q3", "year": 2024, "revenue": 13000000000.0, "profit": 3100000000.0, "expenses": 9900000000.0},
    {"company_id": 2, "quarter": "Q2", "year": 2024, "revenue": 12500000000.0, "profit": 2900000000.0, "expenses": 9600000000.0},
    {"company_id": 2, "quarter": "Q1", "year": 2024, "revenue": 11800000000.0, "profit": 2800000000.0, "expenses": 9000000000.0},
    
    # HealthTech Solutions (company_id: 3)
    {"company_id": 3, "quarter": "Q1", "year": 2025, "revenue": 8000000000.0, "profit": 1200000000.0, "expenses": 6800000000.0},
    {"company_id": 3, "quarter": "Q4", "year": 2024, "revenue": 8500000000.0, "profit": 1300000000.0, "expenses": 7200000000.0},
    {"company_id": 3, "quarter": "Q3", "year": 2024, "revenue": 8200000000.0, "profit": 1250000000.0, "expenses": 6950000000.0},
    {"company_id": 3, "quarter": "Q2", "year": 2024, "revenue": 7800000000.0, "profit": 1150000000.0, "expenses": 6650000000.0},
    {"company_id": 3, "quarter": "Q1", "year": 2024, "revenue": 7500000000.0, "profit": 1100000000.0, "expenses": 6400000000.0},
    
    # Green Energy Corp (company_id: 4)
    {"company_id": 4, "quarter": "Q1", "year": 2025, "revenue": 5500000000.0, "profit": 800000000.0, "expenses": 4700000000.0},
    {"company_id": 4, "quarter": "Q4", "year": 2024, "revenue": 6000000000.0, "profit": 900000000.0, "expenses": 5100000000.0},
    {"company_id": 4, "quarter": "Q3", "year": 2024, "revenue": 5800000000.0, "profit": 850000000.0, "expenses": 4950000000.0},
    {"company_id": 4, "quarter": "Q2", "year": 2024, "revenue": 5200000000.0, "profit": 750000000.0, "expenses": 4450000000.0},
    {"company_id": 4, "quarter": "Q1", "year": 2024, "revenue": 4800000000.0, "profit": 680000000.0, "expenses": 4120000000.0},
    
    # RetailMax Group (company_id: 5)
    {"company_id": 5, "quarter": "Q1", "year": 2025, "revenue": 18000000000.0, "profit": 1800000000.0, "expenses": 16200000000.0},
    {"company_id": 5, "quarter": "Q4", "year": 2024, "revenue": 22000000000.0, "profit": 2400000000.0, "expenses": 19600000000.0},  # Holiday season
    {"company_id": 5, "quarter": "Q3", "year": 2024, "revenue": 19000000000.0, "profit": 2000000000.0, "expenses": 17000000000.0},
    {"company_id": 5, "quarter": "Q2", "year": 2024, "revenue": 17500000000.0, "profit": 1750000000.0, "expenses": 15750000000.0},
    {"company_id": 5, "quarter": "Q1", "year": 2024, "revenue": 16800000000.0, "profit": 1650000000.0, "expenses": 15150000000.0},
]


def get_sample_queries() -> List[str]:
    """
    Get list of sample queries for testing and demonstration.
    
    Returns:
        List of sample SQL queries
    """
    return [
        "SELECT * FROM companies WHERE sector = 'Technology'",
        "SELECT company_id, SUM(revenue) as total_revenue FROM financial_records WHERE year = 2024 GROUP BY company_id",
        "SELECT c.name, f.revenue, f.profit FROM companies c JOIN financial_records f ON c.id = f.company_id WHERE f.quarter = 'Q1' AND f.year = 2025",
        "SELECT sector, COUNT(*) as company_count FROM companies GROUP BY sector",
        "SELECT c.name, f.quarter, f.year, f.revenue FROM companies c JOIN financial_records f ON c.id = f.company_id WHERE c.symbol = 'TECH' ORDER BY f.year DESC, f.quarter DESC",
        "SELECT AVG(revenue) as avg_revenue, AVG(profit) as avg_profit FROM financial_records WHERE year = 2024",
        "SELECT c.name, c.market_cap, f.revenue FROM companies c JOIN financial_records f ON c.id = f.company_id WHERE f.year = 2025 AND f.quarter = 'Q1' ORDER BY c.market_cap DESC"
    ]


def validate_schema_integrity(tables_info: List[Dict[str, Any]]) -> bool:
    """
    Validate that the database schema matches expected structure.
    
    Args:
        tables_info: Information about database tables
        
    Returns:
        True if schema is valid, False otherwise
    """
    # Primary tables for knowledge base system
    expected_tables = {"knowledge_base", "benchmarks"}
    
    # Legacy tables for backward compatibility
    legacy_tables = {"companies", "financial_records", "financial_data"}
    
    actual_tables = {table["name"] for table in tables_info}
    
    # Check for primary knowledge base tables
    if not expected_tables.issubset(actual_tables):
        missing_tables = expected_tables - actual_tables
        logger.error("Missing primary database tables", missing=list(missing_tables))
        return False
    
    # Warn about missing legacy tables but don't fail
    missing_legacy = legacy_tables - actual_tables
    if missing_legacy:
        logger.warning("Missing legacy tables (non-critical)", missing=list(missing_legacy))
    
    logger.info("Database schema validation passed")
    return True
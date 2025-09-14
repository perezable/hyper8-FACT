"""
FACT System Database Models - Knowledge Base Only
This module defines the database schema for the FACT knowledge base system.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

@dataclass
class KnowledgeEntry:
    """Represents a knowledge base entry."""
    id: int
    question: str
    answer: str
    category: str
    state: Optional[str]
    tags: Optional[str]
    priority: str = 'normal'
    difficulty: str = 'basic'
    personas: Optional[str] = None
    source: Optional[str] = None
    metadata: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class QueryResult:
    """Represents the result of a database query."""
    rows: List[Dict[str, Any]]
    row_count: int
    columns: List[str]
    execution_time_ms: float

# PostgreSQL schema for knowledge base
POSTGRESQL_SCHEMA = """
-- Knowledge base entries for Q&A retrieval
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category TEXT NOT NULL,
    tags TEXT, -- Comma-separated tags or JSON array
    metadata TEXT, -- JSON metadata
    state TEXT, -- For state-specific information
    priority TEXT DEFAULT 'normal', -- normal, high, critical
    personas TEXT, -- Target user personas (comma-separated)
    source TEXT, -- Source file or reference
    difficulty TEXT DEFAULT 'basic', -- basic, intermediate, advanced
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_state ON knowledge_base(state);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_priority ON knowledge_base(priority);
CREATE INDEX IF NOT EXISTS idx_knowledge_base_difficulty ON knowledge_base(difficulty);

-- Full text search indexes (PostgreSQL specific)
CREATE INDEX IF NOT EXISTS idx_knowledge_base_question_gin ON knowledge_base USING gin(to_tsvector('english', question));
CREATE INDEX IF NOT EXISTS idx_knowledge_base_answer_gin ON knowledge_base USING gin(to_tsvector('english', answer));
"""

def validate_schema_integrity(tables_info: List[Dict[str, Any]]) -> bool:
    """
    Validate that the database schema matches expected structure.
    
    Args:
        tables_info: Information about database tables
        
    Returns:
        True if schema is valid, False otherwise
    """
    # Only expect knowledge_base table
    expected_tables = {"knowledge_base"}
    
    actual_tables = {table["name"] for table in tables_info}
    
    # Check for required table
    if not expected_tables.issubset(actual_tables):
        missing_tables = expected_tables - actual_tables
        logger.error("Missing required database table", missing=list(missing_tables))
        return False
    
    # Warn about extra tables that shouldn't be there
    extra_tables = actual_tables - expected_tables
    if extra_tables:
        # Filter out system tables
        non_system_extras = {t for t in extra_tables if not t.startswith('pg_') and not t.startswith('sql_')}
        if non_system_extras:
            logger.warning("Unexpected tables found in database", extra=list(non_system_extras))
    
    logger.info("Database schema validation passed")
    return True

def get_knowledge_categories() -> List[str]:
    """
    Get list of standard knowledge categories.
    
    Returns:
        List of category names
    """
    return [
        "payment_options",
        "state_requirements", 
        "licensing_process",
        "exam_preparation",
        "reciprocity",
        "business_setup",
        "timeline_expectations",
        "troubleshooting",
        "contractor_benefits",
        "legal_compliance",
        "insurance_bonding",
        "specialty_licenses"
    ]

def get_user_personas() -> List[str]:
    """
    Get list of user personas.
    
    Returns:
        List of persona identifiers
    """
    return [
        "price_conscious",
        "overwhelmed_veteran",
        "skeptical_researcher",
        "time_pressed",
        "ambitious_entrepreneur"
    ]
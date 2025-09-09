"""
FACT System Extended Database Models for Bland AI Integration

This module defines extended database schemas for comprehensive contractor
licensing knowledge base with personas, pathways, and trust scoring.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


# Extended database schema for comprehensive knowledge base
EXTENDED_DATABASE_SCHEMA = """
-- Personas table for caller identification
CREATE TABLE IF NOT EXISTS personas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    persona_type TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'normal',
    percentage REAL DEFAULT 0.0,
    detection_rules TEXT, -- JSON string of detection criteria
    response_adjustments TEXT, -- JSON string of response modifications
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation pathways table
CREATE TABLE IF NOT EXISTS conversation_pathways (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pathway_name TEXT NOT NULL,
    pathway_type TEXT NOT NULL, -- 'main', 'objection', 'success', 'qualifier'
    persona_type TEXT, -- Associated persona if applicable
    sequence_order INTEGER DEFAULT 0,
    content TEXT NOT NULL, -- The actual conversation script/response
    next_conditions TEXT, -- JSON string of branching conditions
    trust_adjustment REAL DEFAULT 0.0,
    momentum_impact REAL DEFAULT 0.0,
    metadata TEXT, -- JSON string of additional data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (persona_type) REFERENCES personas(persona_type)
);

-- Trust scoring events table
CREATE TABLE IF NOT EXISTS trust_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT,
    event_type TEXT NOT NULL, -- 'positive', 'negative', 'neutral'
    event_category TEXT NOT NULL, -- 'engagement', 'objection', 'validation', etc.
    event_description TEXT,
    trust_impact REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- State requirements detailed table
CREATE TABLE IF NOT EXISTS state_requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT NOT NULL,
    state_name TEXT NOT NULL,
    regulatory_body TEXT,
    license_class TEXT,
    license_type TEXT,
    experience_years INTEGER,
    education_requirements TEXT,
    exam_requirements TEXT, -- JSON string
    bond_amount REAL,
    insurance_requirements TEXT, -- JSON string
    application_fees TEXT, -- JSON string
    processing_timeline TEXT,
    renewal_cycle TEXT,
    continuing_education_hours INTEGER DEFAULT 0,
    reciprocity_states TEXT, -- Comma-separated state codes
    special_provisions TEXT, -- JSON array of special requirements
    metadata TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(state_code, license_class, license_type)
);

-- Branching logic table
CREATE TABLE IF NOT EXISTS branching_logic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_name TEXT NOT NULL UNIQUE,
    trigger_patterns TEXT NOT NULL, -- JSON array of patterns
    trigger_keywords TEXT, -- JSON array of keywords
    condition_expression TEXT, -- JSON condition logic
    action_type TEXT NOT NULL, -- 'route', 'response', 'escalate', 'retrieve'
    action_target TEXT, -- Target pathway, response, or knowledge category
    priority TEXT DEFAULT 'normal',
    metadata TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge retrieval configurations
CREATE TABLE IF NOT EXISTS retrieval_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_name TEXT NOT NULL UNIQUE,
    patterns TEXT NOT NULL, -- JSON array of regex patterns
    keywords TEXT, -- JSON array of keywords
    query_template TEXT NOT NULL,
    category_filter TEXT,
    max_results INTEGER DEFAULT 3,
    confidence_threshold REAL DEFAULT 0.7,
    priority TEXT DEFAULT 'normal',
    personalization_enabled BOOLEAN DEFAULT 1,
    metadata TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Success stories and case studies
CREATE TABLE IF NOT EXISTS success_stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_title TEXT NOT NULL,
    customer_profile TEXT, -- JSON with demographics, background
    initial_situation TEXT,
    solution_provided TEXT,
    results_achieved TEXT,
    roi_metrics TEXT, -- JSON with specific metrics
    testimonial_quote TEXT,
    persona_types TEXT, -- Comma-separated personas this resonates with
    state_code TEXT,
    industry TEXT,
    priority TEXT DEFAULT 'normal',
    metadata TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Objection handling scripts
CREATE TABLE IF NOT EXISTS objection_responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    objection_type TEXT NOT NULL,
    objection_pattern TEXT NOT NULL, -- Common phrasing of the objection
    response_script TEXT NOT NULL,
    persona_specific_variation TEXT, -- JSON with persona-specific responses
    trust_requirement REAL DEFAULT 0.0, -- Minimum trust level to use
    success_rate REAL DEFAULT 0.0,
    follow_up_questions TEXT, -- JSON array of follow-up questions
    metadata TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhook configurations
CREATE TABLE IF NOT EXISTS webhook_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    webhook_name TEXT NOT NULL UNIQUE,
    endpoint_url TEXT NOT NULL,
    http_method TEXT DEFAULT 'POST',
    headers TEXT, -- JSON object of headers
    event_types TEXT, -- JSON array of triggering events
    retry_attempts INTEGER DEFAULT 3,
    retry_backoff TEXT DEFAULT 'exponential',
    timeout_ms INTEGER DEFAULT 3000,
    enabled BOOLEAN DEFAULT 1,
    metadata TEXT, -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation analytics
CREATE TABLE IF NOT EXISTS conversation_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id TEXT NOT NULL UNIQUE,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_seconds INTEGER,
    detected_persona TEXT,
    persona_confidence REAL,
    initial_trust_score REAL,
    final_trust_score REAL,
    initial_momentum REAL,
    final_momentum REAL,
    knowledge_queries_made INTEGER DEFAULT 0,
    objections_handled INTEGER DEFAULT 0,
    pathways_traversed TEXT, -- JSON array of pathway IDs
    outcome TEXT, -- 'success', 'callback', 'not_interested', 'disconnected'
    outcome_reason TEXT,
    metadata TEXT, -- JSON string with additional metrics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_personas_type ON personas(persona_type);
CREATE INDEX IF NOT EXISTS idx_pathways_persona ON conversation_pathways(persona_type);
CREATE INDEX IF NOT EXISTS idx_pathways_type ON conversation_pathways(pathway_type);
CREATE INDEX IF NOT EXISTS idx_trust_events_call ON trust_events(call_id);
CREATE INDEX IF NOT EXISTS idx_state_req_code ON state_requirements(state_code);
CREATE INDEX IF NOT EXISTS idx_state_req_class ON state_requirements(license_class);
CREATE INDEX IF NOT EXISTS idx_branching_trigger ON branching_logic(trigger_name);
CREATE INDEX IF NOT EXISTS idx_retrieval_trigger ON retrieval_configs(trigger_name);
CREATE INDEX IF NOT EXISTS idx_success_persona ON success_stories(persona_types);
CREATE INDEX IF NOT EXISTS idx_success_state ON success_stories(state_code);
CREATE INDEX IF NOT EXISTS idx_objection_type ON objection_responses(objection_type);
CREATE INDEX IF NOT EXISTS idx_webhook_event ON webhook_configs(event_types);
CREATE INDEX IF NOT EXISTS idx_analytics_call ON conversation_analytics(call_id);
CREATE INDEX IF NOT EXISTS idx_analytics_persona ON conversation_analytics(detected_persona);
CREATE INDEX IF NOT EXISTS idx_analytics_outcome ON conversation_analytics(outcome);
"""


@dataclass
class Persona:
    """Represents a caller persona with detection rules and response adjustments."""
    id: int
    persona_type: str
    name: str
    description: str
    priority: str
    percentage: float
    detection_rules: Dict[str, Any]
    response_adjustments: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class ConversationPathway:
    """Represents a conversation pathway with branching logic."""
    id: int
    pathway_name: str
    pathway_type: str
    persona_type: Optional[str]
    sequence_order: int
    content: str
    next_conditions: Dict[str, Any]
    trust_adjustment: float
    momentum_impact: float
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class TrustEvent:
    """Represents a trust scoring event during a conversation."""
    id: int
    call_id: str
    event_type: str
    event_category: str
    event_description: str
    trust_impact: float
    timestamp: datetime


@dataclass
class StateRequirement:
    """Represents detailed state licensing requirements."""
    id: int
    state_code: str
    state_name: str
    regulatory_body: str
    license_class: str
    license_type: str
    experience_years: int
    education_requirements: str
    exam_requirements: Dict[str, Any]
    bond_amount: float
    insurance_requirements: Dict[str, Any]
    application_fees: Dict[str, Any]
    processing_timeline: str
    renewal_cycle: str
    continuing_education_hours: int
    reciprocity_states: List[str]
    special_provisions: List[str]
    metadata: Dict[str, Any]


@dataclass
class ConversationAnalytics:
    """Represents analytics for a complete conversation."""
    call_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int
    detected_persona: str
    persona_confidence: float
    initial_trust_score: float
    final_trust_score: float
    initial_momentum: float
    final_momentum: float
    knowledge_queries_made: int
    objections_handled: int
    pathways_traversed: List[str]
    outcome: str
    outcome_reason: str
    metadata: Dict[str, Any]


def validate_extended_schema_integrity(tables_info: List[Dict[str, Any]]) -> bool:
    """
    Validate that the extended database schema matches expected structure.
    
    Args:
        tables_info: Information about database tables
        
    Returns:
        True if schema is valid, False otherwise
    """
    expected_tables = {
        "personas",
        "conversation_pathways", 
        "trust_events",
        "state_requirements",
        "branching_logic",
        "retrieval_configs",
        "success_stories",
        "objection_responses",
        "webhook_configs",
        "conversation_analytics"
    }
    
    actual_tables = {table["name"] for table in tables_info}
    
    missing_tables = expected_tables - actual_tables
    if missing_tables:
        logger.warning("Missing extended tables", missing=list(missing_tables))
        return False
    
    logger.info("Extended database schema validation passed")
    return True
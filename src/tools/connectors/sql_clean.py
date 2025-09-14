"""
SQL Query Tool for FACT System - Knowledge Base Only
Provides secure read-only SQL query access to the knowledge base.
"""

from typing import Dict, Any, List, Optional
import structlog
import time
import uuid

# Initialize logger
logger = structlog.get_logger(__name__)

# SQL query tool metadata
SQL_QUERY_READONLY_METADATA = {
    "name": "SQL_QueryReadonly",
    "description": """Query the FACT knowledge base using SQL SELECT statements.
    
This tool provides read-only access to the knowledge_base table containing contractor licensing information.

Available columns:
- id: Entry ID
- question: The question or topic
- answer: The detailed answer
- category: Category (e.g., payment_options, state_requirements, licensing_process)
- state: State code if applicable (e.g., FL, CA, TX)
- tags: Comma-separated tags
- priority: Priority level (normal, high, critical)
- difficulty: Difficulty level (basic, intermediate, advanced)
- personas: Target user personas
- source: Source reference
- metadata: Additional metadata in JSON format

Example queries:
- SELECT * FROM knowledge_base WHERE category = 'state_requirements' AND state = 'FL'
- SELECT question, answer FROM knowledge_base WHERE tags LIKE '%payment%'
- SELECT * FROM knowledge_base WHERE priority = 'high' ORDER BY id DESC LIMIT 10
""",
    "inputSchema": {
        "type": "object",
        "properties": {
            "statement": {
                "type": "string",
                "description": "SQL SELECT statement to execute on the knowledge_base table. Must be a SELECT query only.",
                "minLength": 10,
                "maxLength": 1000
            }
        },
        "required": ["statement"]
    }
}

async def sql_query_readonly(statement: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a read-only SQL query against the knowledge base.
    
    Args:
        statement: SQL SELECT statement to execute
        context: Optional context containing driver and other metadata
        
    Returns:
        Dictionary containing query results and metadata
    """
    start_time = time.time()
    query_id = f"query_{int(time.time() * 1000)}"
    
    # Get driver from context
    driver = context.get("driver") if context else None
    if not driver:
        logger.error("No driver provided in context")
        return {
            "success": False,
            "error": "Database connection not available",
            "query_id": query_id,
            "execution_time_ms": (time.time() - start_time) * 1000
        }
    
    try:
        # Validate it's a SELECT query
        normalized = statement.strip().lower()
        if not normalized.startswith("select"):
            return {
                "success": False,
                "error": "Only SELECT statements are allowed",
                "query_id": query_id,
                "execution_time_ms": (time.time() - start_time) * 1000
            }
        
        # Execute query through driver
        result = await driver.database_manager.execute_query(statement)
        
        execution_time = (time.time() - start_time) * 1000
        
        # Format response
        response = {
            "success": True,
            "query_id": query_id,
            "statement": statement[:100] + "..." if len(statement) > 100 else statement,
            "row_count": result.row_count,
            "columns": result.columns,
            "rows": result.rows[:100],  # Limit to 100 rows for safety
            "execution_time_ms": execution_time,
            "truncated": len(result.rows) > 100
        }
        
        logger.info(
            "SQL query executed successfully",
            query_id=query_id,
            row_count=result.row_count,
            execution_time_ms=execution_time
        )
        
        return response
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        error_msg = str(e)
        
        logger.error(
            "SQL query execution failed",
            query_id=query_id,
            error=error_msg,
            statement=statement[:100],
            execution_time_ms=execution_time
        )
        
        return {
            "success": False,
            "error": error_msg,
            "query_id": query_id,
            "statement": statement[:100] + "..." if len(statement) > 100 else statement,
            "execution_time_ms": execution_time
        }

def get_sql_tool_metadata() -> Dict[str, Any]:
    """Get SQL tool metadata for registration."""
    return SQL_QUERY_READONLY_METADATA

def get_sample_queries() -> List[Dict[str, str]]:
    """
    Get sample SQL queries for the knowledge base.
    
    Returns:
        List of sample query dictionaries
    """
    return [
        {
            "description": "Get all Florida licensing requirements",
            "query": "SELECT * FROM knowledge_base WHERE state = 'FL' AND category = 'state_requirements'"
        },
        {
            "description": "Find payment and financing options",
            "query": "SELECT question, answer FROM knowledge_base WHERE category = 'payment_options' OR tags LIKE '%payment%' OR tags LIKE '%financing%'"
        },
        {
            "description": "Get high priority entries",
            "query": "SELECT * FROM knowledge_base WHERE priority = 'high' ORDER BY id DESC"
        },
        {
            "description": "Search for NASCLA information",
            "query": "SELECT question, answer, state FROM knowledge_base WHERE question LIKE '%NASCLA%' OR answer LIKE '%NASCLA%'"
        },
        {
            "description": "Get exam preparation content",
            "query": "SELECT * FROM knowledge_base WHERE category = 'exam_preparation' OR tags LIKE '%exam%'"
        },
        {
            "description": "Find content for overwhelmed veterans",
            "query": "SELECT question, answer FROM knowledge_base WHERE personas LIKE '%overwhelmed_veteran%'"
        },
        {
            "description": "Get state-specific licensing costs",
            "query": "SELECT state, question, answer FROM knowledge_base WHERE (question LIKE '%cost%' OR answer LIKE '%$%') AND state IS NOT NULL"
        },
        {
            "description": "Count entries by category",
            "query": "SELECT category, COUNT(*) as entry_count FROM knowledge_base GROUP BY category ORDER BY entry_count DESC"
        },
        {
            "description": "Get troubleshooting help",
            "query": "SELECT * FROM knowledge_base WHERE category = 'troubleshooting' OR difficulty = 'advanced'"
        },
        {
            "description": "Find reciprocity information",
            "query": "SELECT state, question, answer FROM knowledge_base WHERE category = 'reciprocity' OR tags LIKE '%reciprocity%'"
        }
    ]
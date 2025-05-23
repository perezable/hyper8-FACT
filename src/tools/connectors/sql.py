"""
FACT System SQL Query Tool

This module implements the SQL query tool for secure database access
following the FACT architecture specification.
"""

import time
from typing import Dict, Any
import structlog

from src.core.errors import DatabaseError, SecurityError, InvalidSQLError
from src.db.connection import DatabaseManager
from src.tools.decorators import Tool


logger = structlog.get_logger(__name__)


class SQLQueryTool:
    """
    SQL query tool implementation with security validation and connection management.
    
    Provides secure read-only database access through validated SQL queries.
    """
    
    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize SQL query tool.
        
        Args:
            database_manager: DatabaseManager instance for query execution
        """
        self.database_manager = database_manager
        
    async def execute_query(self, statement: str) -> Dict[str, Any]:
        """
        Execute a validated SQL query and return structured results.
        
        Args:
            statement: SQL SELECT statement to execute
            
        Returns:
            Dictionary containing query results and metadata
            
        Raises:
            SecurityError: If statement violates security rules
            InvalidSQLError: If statement has syntax errors
            DatabaseError: If query execution fails
        """
        query_id = f"query_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            # Execute query through database manager (includes validation)
            result = await self.database_manager.execute_query(statement)
            
            # Format response with safe statement handling
            safe_statement = str(statement) if statement is not None else "None"
            # Safe length check to prevent NoneType errors
            safe_statement_len = len(safe_statement) if safe_statement is not None else 0
            truncated_statement = safe_statement[:100] + "..." if safe_statement_len > 100 else safe_statement
            
            # Safe access to result attributes with null checks
            rows = getattr(result, 'rows', []) if result is not None else []
            row_count = getattr(result, 'row_count', 0) if result is not None else 0
            columns = getattr(result, 'columns', []) if result is not None else []
            execution_time_ms = getattr(result, 'execution_time_ms', 0) if result is not None else 0
            
            response = {
                "query_id": query_id,
                "rows": rows,
                "row_count": row_count,
                "columns": columns,
                "execution_time_ms": execution_time_ms,
                "statement": truncated_statement,
                "status": "success"
            }
            
            logger.info("SQL query executed successfully",
                       query_id=query_id,
                       row_count=row_count,
                       execution_time_ms=execution_time_ms)
            
            return response
            
        except (SecurityError, InvalidSQLError, DatabaseError) as e:
            execution_time = (time.time() - start_time) * 1000
            
            logger.error("SQL query failed",
                        query_id=query_id,
                        error=str(e),
                        error_type=type(e).__name__,
                        execution_time_ms=execution_time)
            
            # Return error response with safe statement handling
            safe_statement = str(statement) if statement is not None else "None"
            # Safe length check to prevent NoneType errors
            safe_statement_len = len(safe_statement) if safe_statement is not None else 0
            truncated_statement = safe_statement[:100] + "..." if safe_statement_len > 100 else safe_statement
            
            return {
                "query_id": query_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "execution_time_ms": execution_time,
                "statement": truncated_statement,
                "status": "failed"
            }


# Global SQL tool instance (will be initialized by driver)
_sql_tool_instance = None


def initialize_sql_tool(database_manager: DatabaseManager) -> None:
    """
    Initialize the global SQL tool instance.
    
    Args:
        database_manager: DatabaseManager instance to use
    """
    global _sql_tool_instance
    _sql_tool_instance = SQLQueryTool(database_manager)
    logger.info("SQL query tool initialized")


@Tool(
    name="SQL.QueryReadonly",
    description="Execute SELECT queries on the finance database to retrieve financial data, company information, and analytics. Only read-only SELECT statements are allowed for security. IMPORTANT: Use table names 'companies' and 'financial_records' (NOT 'financials').",
    parameters={
        "statement": {
            "type": "string",
            "description": "SQL SELECT statement to execute. Must start with SELECT and cannot contain data modification operations (INSERT, UPDATE, DELETE, etc.). CRITICAL: Use correct table names: 'companies' and 'financial_records'. Example: 'SELECT * FROM companies WHERE sector = \"Technology\"' or 'SELECT c.name, f.revenue FROM companies c JOIN financial_records f ON c.id = f.company_id'",
            "minLength": 10,
            "maxLength": 1000
        }
    },
    requires_auth=False,
    timeout_seconds=30,
    version="1.0.0"
)
async def sql_query_readonly(statement: str) -> Dict[str, Any]:
    """
    Execute a read-only SQL query on the finance database.
    
    This tool provides secure access to the financial database using validated
    SELECT statements. It prevents data modification and enforces security
    constraints to ensure safe database access.
    
    Args:
        statement: SQL SELECT statement to execute
        
    Returns:
        Dictionary containing query results, metadata, and execution statistics
        
    Example:
        statement = "SELECT name, revenue FROM companies c JOIN financial_records f ON c.id = f.company_id WHERE f.year = 2025"
        result = await sql_query_readonly(statement)
        # Returns: {
        #     "rows": [{"name": "TechCorp", "revenue": 25000000000}, ...],
        #     "row_count": 5,
        #     "columns": ["name", "revenue"],
        #     "execution_time_ms": 15.2,
        #     "status": "success"
        # }
    """
    if _sql_tool_instance is None:
        return {
            "error": "SQL tool not initialized",
            "status": "failed",
            "execution_time_ms": 0
        }
    
    return await _sql_tool_instance.execute_query(statement)


@Tool(
    name="SQL.GetSchema",
    description="Get database schema information including table structures, column details, and relationships",
    parameters={},
    requires_auth=False,
    timeout_seconds=10,
    version="1.0.0"
)
async def sql_get_schema() -> Dict[str, Any]:
    """
    Get database schema information for query construction assistance.
    
    Returns:
        Dictionary containing database schema information
    """
    if _sql_tool_instance is None:
        return {
            "error": "SQL tool not initialized",
            "status": "failed",
            "execution_time_ms": 0
        }
    
    try:
        # Get table information
        tables_query = """
        SELECT name as table_name
        FROM sqlite_master
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
        
        tables_result = await _sql_tool_instance.execute_query(tables_query)
        
        # Safe access to tables_result with comprehensive null checks
        tables_rows = None
        if tables_result is not None and isinstance(tables_result, dict):
            tables_rows = tables_result.get("rows")
        
        # Safe length calculation to prevent NoneType errors
        total_tables = 0
        if tables_rows is not None and hasattr(tables_rows, '__len__'):
            total_tables = len(tables_rows)
        
        schema_info = {
            "tables": [],
            "total_tables": total_tables,
            "database_type": "SQLite",
            "status": "success",
            "important_notes": [
                "CRITICAL: The financial data table is named 'financial_records' (NOT 'financials')",
                "CRITICAL: Always use 'companies' and 'financial_records' as table names",
                "JOIN syntax: companies.id = financial_records.company_id"
            ]
        }
        
        # Safe iteration over potentially None result sets
        if tables_rows is not None:
            for table_row in tables_rows:
                # Additional safety check for table_row
                if table_row is None or not isinstance(table_row, dict):
                    continue
                    
                table_name = table_row["table_name"]
                
                # Validate table name before using in PRAGMA
                if not _sql_tool_instance.database_manager._is_valid_table_name(table_name):
                    logger.warning("Invalid table name in schema query", table_name=table_name)
                    continue
                
                # Use safe table name in PRAGMA (cannot be parameterized)
                # PRAGMA queries are read-only and table name is validated
                columns_query = f'PRAGMA table_info("{table_name}")'
                
                try:
                    columns_result = await _sql_tool_instance.execute_query(columns_query)
                    
                    table_info = {
                        "name": table_name,
                        "columns": []
                    }
                    
                    # Safe iteration over column results
                    columns_rows = None
                    if columns_result is not None and isinstance(columns_result, dict):
                        columns_rows = columns_result.get("rows")
                    
                    if columns_rows is not None:
                        for col_row in columns_rows:
                            # Additional safety check for col_row
                            if col_row is None or not isinstance(col_row, dict):
                                continue
                                
                            column_info = {
                                "name": col_row.get("name", ""),
                                "type": col_row.get("type", ""),
                                "nullable": not col_row.get("notnull", False),
                                "primary_key": bool(col_row.get("pk", False))
                            }
                            table_info["columns"].append(column_info)
                    
                    schema_info["tables"].append(table_info)
                    
                except Exception as e:
                    logger.error("Failed to get column info for table",
                               table_name=table_name,
                               error=str(e))
                    # Continue with other tables
                    continue
        
        return schema_info
        
    except Exception as e:
        logger.error("Failed to get schema information", error=str(e))
        return {
            "error": f"Failed to get schema: {e}",
            "status": "failed",
            "execution_time_ms": 0
        }


@Tool(
    name="SQL.GetSampleQueries",
    description="Get sample SQL queries for exploring the financial database",
    parameters={},
    requires_auth=False,
    timeout_seconds=5,
    version="1.0.0"
)
def sql_get_sample_queries() -> Dict[str, Any]:
    """
    Get sample SQL queries that can be used to explore the financial database.
    
    Returns:
        Dictionary containing sample queries with descriptions
    """
    sample_queries = [
        {
            "description": "Get all companies in the Technology sector",
            "query": "SELECT * FROM companies WHERE sector = 'Technology'"
        },
        {
            "description": "Get total revenue by company for 2024",
            "query": "SELECT c.name, SUM(f.revenue) as total_revenue FROM companies c JOIN financial_records f ON c.id = f.company_id WHERE f.year = 2024 GROUP BY c.id, c.name ORDER BY total_revenue DESC"
        },
        {
            "description": "Get Q1 2025 financial results",
            "query": "SELECT c.name, f.revenue, f.profit, f.expenses FROM companies c JOIN financial_records f ON c.id = f.company_id WHERE f.quarter = 'Q1' AND f.year = 2025 ORDER BY f.revenue DESC"
        },
        {
            "description": "Get company count by sector",
            "query": "SELECT sector, COUNT(*) as company_count FROM companies GROUP BY sector ORDER BY company_count DESC"
        },
        {
            "description": "Get TechCorp's quarterly performance over time",
            "query": "SELECT c.name, f.quarter, f.year, f.revenue, f.profit FROM companies c JOIN financial_records f ON c.id = f.company_id WHERE c.symbol = 'TECH' ORDER BY f.year DESC, f.quarter DESC"
        },
        {
            "description": "Get average metrics for 2024",
            "query": "SELECT AVG(revenue) as avg_revenue, AVG(profit) as avg_profit, AVG(expenses) as avg_expenses FROM financial_records WHERE year = 2024"
        },
        {
            "description": "Get top companies by market cap with latest revenue",
            "query": "SELECT c.name, c.market_cap, f.revenue as q1_2025_revenue FROM companies c JOIN financial_records f ON c.id = f.company_id WHERE f.year = 2025 AND f.quarter = 'Q1' ORDER BY c.market_cap DESC"
        }
    ]
    
    return {
        "sample_queries": sample_queries,
        "total_queries": len(sample_queries),
        "status": "success",
        "execution_time_ms": 0
    }


def get_sql_tool() -> SQLQueryTool:
    """
    Get the global SQL tool instance.
    
    Returns:
        Global SQLQueryTool instance
        
    Raises:
        RuntimeError: If SQL tool is not initialized
    """
    if _sql_tool_instance is None:
        raise RuntimeError("SQL tool not initialized. Call initialize_sql_tool first.")
    
    return _sql_tool_instance
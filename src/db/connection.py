"""
FACT System Database Connection Management

This module handles SQLite database connections, query execution,
and database initialization with sample data.
"""

import aiosqlite
import sqlite3
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from contextlib import asynccontextmanager
import structlog

from ..core.errors import DatabaseError, SecurityError, InvalidSQLError
from .models import (
    DATABASE_SCHEMA, 
    SAMPLE_COMPANIES, 
    SAMPLE_FINANCIAL_RECORDS,
    QueryResult,
    validate_schema_integrity
)


logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections and operations for the FACT system.
    
    Provides secure database access with read-only query validation,
    connection pooling, and performance monitoring.
    """
    
    def __init__(self, database_path: str):
        """
        Initialize database manager.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self._ensure_directory_exists()
        
    def _ensure_directory_exists(self) -> None:
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.database_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info("Created database directory", path=db_dir)
    
    async def initialize_database(self) -> None:
        """
        Initialize database with schema and sample data.
        
        Raises:
            DatabaseError: If database initialization fails
        """
        try:
            async with aiosqlite.connect(self.database_path) as db:
                # Execute schema creation
                await db.executescript(DATABASE_SCHEMA)
                await db.commit()
                
                # Check if data already exists
                cursor = await db.execute("SELECT COUNT(*) FROM companies")
                company_count = (await cursor.fetchone())[0]
                await cursor.close()
                
                if company_count == 0:
                    # Insert sample companies
                    for company in SAMPLE_COMPANIES:
                        await db.execute("""
                            INSERT INTO companies (name, symbol, sector, founded_year, employees, market_cap)
                            VALUES (:name, :symbol, :sector, :founded_year, :employees, :market_cap)
                        """, company)
                    
                    # Insert sample financial records
                    for record in SAMPLE_FINANCIAL_RECORDS:
                        await db.execute("""
                            INSERT INTO financial_records (company_id, quarter, year, revenue, profit, expenses)
                            VALUES (:company_id, :quarter, :year, :revenue, :profit, :expenses)
                        """, record)
                    
                    await db.commit()
                    logger.info("Database initialized with sample data")
                else:
                    logger.info("Database already contains data, skipping sample data insertion")
                
                # Validate schema integrity
                cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = await cursor.fetchall()
                await cursor.close()
                
                tables_info = [{"name": table[0]} for table in tables]
                if not validate_schema_integrity(tables_info):
                    raise DatabaseError("Database schema validation failed")
                
        except Exception as e:
            logger.error("Database initialization failed", error=str(e))
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    def validate_sql_query(self, statement: str) -> None:
        """
        Validate SQL query for security and syntax.
        
        Args:
            statement: SQL statement to validate
            
        Raises:
            SecurityError: If statement contains dangerous operations
            InvalidSQLError: If statement has syntax errors
        """
        normalized_statement = statement.lower().strip()
        
        # Security check: only allow SELECT statements
        if not normalized_statement.startswith("select"):
            raise SecurityError("Only SELECT statements are allowed")
        
        # Check for dangerous keywords
        dangerous_keywords = [
            "drop", "delete", "update", "insert", "alter", "create",
            "truncate", "replace", "merge", "exec", "execute"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in normalized_statement:
                raise SecurityError(f"Dangerous SQL keyword detected: {keyword}")
        
        # Basic syntax validation using sqlite3 parser
        try:
            # Parse SQL to check syntax (without executing)
            conn = sqlite3.connect(":memory:")
            conn.execute(f"EXPLAIN QUERY PLAN {statement}")
            conn.close()
        except sqlite3.Error as e:
            raise InvalidSQLError(f"SQL syntax error: {e}")
        
        logger.debug("SQL query validation passed", statement=statement[:100])
    
    async def execute_query(self, statement: str) -> QueryResult:
        """
        Execute a validated SQL query and return structured results.
        
        Args:
            statement: SQL SELECT statement to execute
            
        Returns:
            QueryResult containing rows, metadata, and timing
            
        Raises:
            DatabaseError: If query execution fails
            SecurityError: If statement violates security rules
            InvalidSQLError: If statement has syntax errors
        """
        # Validate query first
        self.validate_sql_query(statement)
        
        start_time = time.time()
        
        try:
            async with aiosqlite.connect(self.database_path) as db:
                # Enable row factory for dictionary-like access
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute(statement)
                rows = await cursor.fetchall()
                
                # Convert rows to dictionaries
                structured_results = []
                columns = []
                
                if rows:
                    # Get column names from first row
                    columns = list(rows[0].keys())
                    
                    # Convert each row to dictionary
                    for row in rows:
                        row_dict = {col: row[col] for col in columns}
                        structured_results.append(row_dict)
                
                await cursor.close()
                
                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000
                
                result = QueryResult(
                    rows=structured_results,
                    row_count=len(structured_results),
                    columns=columns,
                    execution_time_ms=execution_time_ms
                )
                
                logger.info("Query executed successfully",
                           statement=statement[:100],
                           row_count=result.row_count,
                           execution_time_ms=execution_time_ms)
                
                return result
                
        except Exception as e:
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            
            logger.error("Query execution failed",
                        statement=statement[:100],
                        error=str(e),
                        execution_time_ms=execution_time_ms)
            
            raise DatabaseError(f"Query execution failed: {e}")
    
    async def get_database_info(self) -> Dict[str, Any]:
        """
        Get database metadata and statistics.
        
        Returns:
            Dictionary containing database information
        """
        try:
            async with aiosqlite.connect(self.database_path) as db:
                # Get table information
                cursor = await db.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = await cursor.fetchall()
                await cursor.close()
                
                table_info = {}
                for (table_name,) in tables:
                    # Get row count for each table
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = (await cursor.fetchone())[0]
                    await cursor.close()
                    table_info[table_name] = {"row_count": count}
                
                # Get database file size
                file_size = os.path.getsize(self.database_path) if os.path.exists(self.database_path) else 0
                
                return {
                    "database_path": self.database_path,
                    "file_size_bytes": file_size,
                    "tables": table_info,
                    "total_tables": len(tables)
                }
                
        except Exception as e:
            logger.error("Failed to get database info", error=str(e))
            raise DatabaseError(f"Failed to get database info: {e}")
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Get an async database connection context manager.
        
        Yields:
            aiosqlite.Connection: Database connection
        """
        async with aiosqlite.connect(self.database_path) as conn:
            try:
                yield conn
            except Exception as e:
                logger.error("Database connection error", error=str(e))
                raise DatabaseError(f"Database connection error: {e}")


def create_database_manager(database_path: str) -> DatabaseManager:
    """
    Create and initialize a database manager instance.
    
    Args:
        database_path: Path to SQLite database file
        
    Returns:
        Configured DatabaseManager instance
    """
    return DatabaseManager(database_path)
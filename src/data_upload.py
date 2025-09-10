"""
FACT System Data Upload Module

This module provides functionality for uploading custom data to replace
the sample data in the FACT system database.
"""

import csv
import json
import asyncio
import os
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import structlog

try:
    from .core.config import get_config
    from .db.connection import DatabaseManager
    from .core.errors import DatabaseError, ValidationError
except ImportError:
    import sys
    from pathlib import Path
    src_path = str(Path(__file__).parent)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    from core.config import get_config
    from db.connection import DatabaseManager
    from core.errors import DatabaseError, ValidationError

logger = structlog.get_logger(__name__)


class DataUploader:
    """
    Handles uploading custom data to the FACT system database.
    
    Supports CSV, JSON, and direct data formats for companies and financial records.
    """
    
    def __init__(self, database_manager: Optional[DatabaseManager] = None):
        """
        Initialize data uploader.
        
        Args:
            database_manager: Optional database manager instance
        """
        self.db_manager = database_manager
        if not database_manager:
            config = get_config()
            self.db_manager = DatabaseManager(config.database_path)
    
    async def clear_existing_data(self, table_name: str) -> bool:
        """
        Clear existing data from specified table.
        
        Args:
            table_name: Name of table to clear
            
        Returns:
            True if successful
            
        Raises:
            DatabaseError: If clear operation fails
        """
        valid_tables = {"knowledge_base", "companies", "financial_records", "financial_data", "benchmarks"}
        
        if table_name not in valid_tables:
            raise ValidationError(f"Invalid table name. Must be one of: {valid_tables}")
        
        try:
            async with self.db_manager.get_connection() as conn:
                await conn.execute(f"DELETE FROM {table_name}")
                await conn.commit()
                
                logger.info(f"Cleared existing data from {table_name} table")
                return True
                
        except Exception as e:
            logger.error(f"Failed to clear {table_name} table", error=str(e))
            raise DatabaseError(f"Failed to clear {table_name}: {e}")
    
    def validate_company_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize company data.
        
        Args:
            company_data: Raw company data dictionary
            
        Returns:
            Validated company data
            
        Raises:
            ValidationError: If data is invalid
        """
        required_fields = {"name", "symbol", "sector"}
        
        # Check required fields
        missing_fields = required_fields - set(company_data.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
        
        # Normalize and validate data
        validated = {
            "name": str(company_data["name"]).strip(),
            "symbol": str(company_data["symbol"]).strip().upper(),
            "sector": str(company_data["sector"]).strip(),
            "founded_year": int(company_data.get("founded_year", 2000)) if company_data.get("founded_year") else None,
            "employees": int(company_data.get("employees", 0)) if company_data.get("employees") else None,
            "market_cap": float(company_data.get("market_cap", 0.0)) if company_data.get("market_cap") else None
        }
        
        # Validate ranges
        current_year = datetime.now().year
        if validated["founded_year"] and (validated["founded_year"] < 1800 or validated["founded_year"] > current_year):
            raise ValidationError(f"Invalid founded_year: {validated['founded_year']}")
        
        if validated["employees"] and validated["employees"] < 0:
            raise ValidationError(f"Invalid employees count: {validated['employees']}")
        
        if validated["market_cap"] and validated["market_cap"] < 0:
            raise ValidationError(f"Invalid market_cap: {validated['market_cap']}")
        
        return validated
    
    def validate_knowledge_base_data(self, kb_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize knowledge base data.
        
        Args:
            kb_data: Raw knowledge base data dictionary
            
        Returns:
            Validated knowledge base data
            
        Raises:
            ValidationError: If data is invalid
        """
        required_fields = {"question", "answer", "category"}
        
        # Check required fields
        missing_fields = required_fields - set(kb_data.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
        
        # Normalize and validate data
        validated = {
            "question": str(kb_data["question"]).strip(),
            "answer": str(kb_data["answer"]).strip(),
            "category": str(kb_data["category"]).strip().lower().replace(" ", "_"),
            "tags": str(kb_data.get("tags", "")).strip(),
            "metadata": str(kb_data.get("metadata", "")).strip(),
            "state": str(kb_data.get("state", "")).strip().upper(),
            "priority": str(kb_data.get("priority", "normal")).strip().lower(),
            "personas": str(kb_data.get("personas", "")).strip(),
            "source": str(kb_data.get("source", "")).strip(),
            "difficulty": str(kb_data.get("difficulty", "basic")).strip().lower()
        }
        
        # Validate constraints
        valid_priorities = {"low", "normal", "high", "critical"}
        if validated["priority"] not in valid_priorities:
            validated["priority"] = "normal"
            
        valid_difficulties = {"basic", "intermediate", "advanced"}
        if validated["difficulty"] not in valid_difficulties:
            validated["difficulty"] = "basic"
        
        # Validate minimum content length
        if len(validated["question"]) < 5:
            raise ValidationError("Question must be at least 5 characters long")
        
        if len(validated["answer"]) < 10:
            raise ValidationError("Answer must be at least 10 characters long")
        
        return validated
    
    def validate_financial_data(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize financial data.
        
        Args:
            financial_data: Raw financial data dictionary
            
        Returns:
            Validated financial data
            
        Raises:
            ValidationError: If data is invalid
        """
        required_fields = {"company_id", "quarter", "year", "revenue", "profit", "expenses"}
        
        # Check required fields
        missing_fields = required_fields - set(financial_data.keys())
        if missing_fields:
            raise ValidationError(f"Missing required fields: {missing_fields}")
        
        # Normalize and validate data
        validated = {
            "company_id": int(financial_data["company_id"]),
            "quarter": str(financial_data["quarter"]).strip().upper(),
            "year": int(financial_data["year"]),
            "revenue": float(financial_data["revenue"]),
            "profit": float(financial_data["profit"]),
            "expenses": float(financial_data["expenses"])
        }
        
        # Validate ranges and business logic
        current_year = datetime.now().year
        if validated["year"] < 1900 or validated["year"] > current_year + 5:
            raise ValidationError(f"Invalid year: {validated['year']}")
        
        if validated["quarter"] not in {"Q1", "Q2", "Q3", "Q4"}:
            raise ValidationError(f"Invalid quarter: {validated['quarter']}")
        
        if validated["company_id"] <= 0:
            raise ValidationError(f"Invalid company_id: {validated['company_id']}")
        
        # Validate financial amounts
        if validated["revenue"] < 0:
            raise ValidationError(f"Revenue cannot be negative: {validated['revenue']}")
        
        # Basic business logic check
        if validated["profit"] > validated["revenue"]:
            logger.warning("Profit exceeds revenue - unusual but not invalid", 
                         profit=validated["profit"], revenue=validated["revenue"])
        
        return validated
    
    async def upload_companies(self, companies_data: List[Dict[str, Any]], 
                              clear_existing: bool = False) -> Dict[str, Any]:
        """
        Upload company data to database.
        
        Args:
            companies_data: List of company dictionaries
            clear_existing: Whether to clear existing company data first
            
        Returns:
            Upload result summary
            
        Raises:
            DatabaseError: If upload fails
            ValidationError: If data validation fails
        """
        if clear_existing:
            await self.clear_existing_data("companies")
        
        validated_companies = []
        errors = []
        
        # Validate all companies first
        for i, company in enumerate(companies_data):
            try:
                validated = self.validate_company_data(company)
                validated_companies.append(validated)
            except ValidationError as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        if errors:
            raise ValidationError(f"Validation errors: {'; '.join(errors)}")
        
        # Insert validated companies
        try:
            async with self.db_manager.get_connection() as conn:
                for company in validated_companies:
                    await conn.execute("""
                        INSERT INTO companies (name, symbol, sector, founded_year, employees, market_cap)
                        VALUES (:name, :symbol, :sector, :founded_year, :employees, :market_cap)
                    """, company)
                
                await conn.commit()
                
                logger.info("Successfully uploaded companies", count=len(validated_companies))
                
                return {
                    "status": "success",
                    "companies_uploaded": len(validated_companies),
                    "cleared_existing": clear_existing,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to upload companies", error=str(e))
            raise DatabaseError(f"Failed to upload companies: {e}")
    
    async def upload_knowledge_base(self, kb_data: List[Dict[str, Any]], 
                                   clear_existing: bool = False) -> Dict[str, Any]:
        """
        Upload knowledge base entries to database.
        
        Args:
            kb_data: List of knowledge base entry dictionaries
            clear_existing: Whether to clear existing knowledge base data first
            
        Returns:
            Upload result summary
            
        Raises:
            DatabaseError: If upload fails
            ValidationError: If data validation fails
        """
        # Try to use PostgreSQL if available
        try:
            from db.postgres_adapter import postgres_adapter
            if postgres_adapter and postgres_adapter.initialized:
                logger.info("Using PostgreSQL for knowledge base upload")
                
                # Prepare entries for PostgreSQL
                postgres_entries = []
                errors = []
                
                for i, entry in enumerate(kb_data):
                    try:
                        validated = self.validate_knowledge_base_data(entry)
                        # Add ID if not present
                        if 'id' not in entry:
                            validated['id'] = f"KB_{i+1}_{datetime.now().timestamp()}"
                        else:
                            validated['id'] = str(entry['id'])
                        postgres_entries.append(validated)
                    except ValidationError as e:
                        errors.append(f"Row {i+1}: {str(e)}")
                
                if errors:
                    raise ValidationError(f"Validation errors: {'; '.join(errors)}")
                
                # Insert via PostgreSQL adapter
                success = await postgres_adapter.insert_entries(postgres_entries, clear_existing)
                
                if success:
                    logger.info("Successfully uploaded to PostgreSQL", count=len(postgres_entries))
                    
                    # Refresh enhanced retriever if available
                    try:
                        from retrieval.enhanced_search import EnhancedRetriever
                        if hasattr(self, '_enhanced_retriever'):
                            await self._enhanced_retriever.refresh_index()
                    except:
                        pass
                    
                    return {
                        "status": "success",
                        "records_uploaded": len(postgres_entries),
                        "cleared_existing": clear_existing,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    logger.warning("PostgreSQL upload failed, falling back to SQLite")
        except ImportError:
            logger.info("PostgreSQL adapter not available, using SQLite")
        except Exception as e:
            logger.warning(f"PostgreSQL upload error: {e}, falling back to SQLite")
        
        # Fallback to SQLite
        if clear_existing:
            await self.clear_existing_data("knowledge_base")
        
        validated_entries = []
        errors = []
        
        # Validate all entries first
        for i, entry in enumerate(kb_data):
            try:
                validated = self.validate_knowledge_base_data(entry)
                validated_entries.append(validated)
            except ValidationError as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        if errors:
            raise ValidationError(f"Validation errors: {'; '.join(errors)}")
        
        # Insert validated entries
        try:
            async with self.db_manager.get_connection() as conn:
                for entry in validated_entries:
                    await conn.execute("""
                        INSERT INTO knowledge_base (question, answer, category, tags, metadata, state, priority, personas, source, difficulty)
                        VALUES (:question, :answer, :category, :tags, :metadata, :state, :priority, :personas, :source, :difficulty)
                    """, entry)
                
                await conn.commit()
                
                logger.info("Successfully uploaded knowledge base entries", count=len(validated_entries))
                
                return {
                    "status": "success", 
                    "records_uploaded": len(validated_entries),
                    "cleared_existing": clear_existing,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to upload knowledge base entries", error=str(e))
            raise DatabaseError(f"Failed to upload knowledge base entries: {e}")
    
    async def upload_financial_records(self, financial_data: List[Dict[str, Any]], 
                                     clear_existing: bool = False) -> Dict[str, Any]:
        """
        Upload financial records to database.
        
        Args:
            financial_data: List of financial record dictionaries
            clear_existing: Whether to clear existing financial data first
            
        Returns:
            Upload result summary
            
        Raises:
            DatabaseError: If upload fails
            ValidationError: If data validation fails
        """
        if clear_existing:
            await self.clear_existing_data("financial_records")
            await self.clear_existing_data("financial_data")
        
        validated_records = []
        errors = []
        
        # Validate all records first
        for i, record in enumerate(financial_data):
            try:
                validated = self.validate_financial_data(record)
                validated_records.append(validated)
            except ValidationError as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        if errors:
            raise ValidationError(f"Validation errors: {'; '.join(errors)}")
        
        # Insert validated records
        try:
            async with self.db_manager.get_connection() as conn:
                # Insert into both tables for compatibility
                for record in validated_records:
                    # Insert into financial_records
                    await conn.execute("""
                        INSERT INTO financial_records (company_id, quarter, year, revenue, profit, expenses)
                        VALUES (:company_id, :quarter, :year, :revenue, :profit, :expenses)
                    """, record)
                    
                    # Insert into financial_data
                    await conn.execute("""
                        INSERT INTO financial_data (company_id, quarter, year, revenue, profit, expenses)
                        VALUES (:company_id, :quarter, :year, :revenue, :profit, :expenses)
                    """, record)
                
                await conn.commit()
                
                logger.info("Successfully uploaded financial records", count=len(validated_records))
                
                return {
                    "status": "success",
                    "records_uploaded": len(validated_records),
                    "cleared_existing": clear_existing,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error("Failed to upload financial records", error=str(e))
            raise DatabaseError(f"Failed to upload financial records: {e}")
    
    async def load_from_csv(self, file_path: str, data_type: str, 
                          clear_existing: bool = False) -> Dict[str, Any]:
        """
        Load data from CSV file.
        
        Args:
            file_path: Path to CSV file
            data_type: Type of data ('knowledge_base', 'companies', or 'financial_records')
            clear_existing: Whether to clear existing data first
            
        Returns:
            Upload result summary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If data format is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                data = list(reader)
                
                logger.info(f"Loaded {len(data)} rows from CSV", file_path=file_path)
                
                if data_type == "knowledge_base":
                    return await self.upload_knowledge_base(data, clear_existing)
                elif data_type == "companies":
                    return await self.upload_companies(data, clear_existing)
                elif data_type == "financial_records":
                    return await self.upload_financial_records(data, clear_existing)
                else:
                    raise ValidationError(f"Invalid data_type: {data_type}")
                    
        except Exception as e:
            logger.error("Failed to load CSV file", file_path=file_path, error=str(e))
            raise ValidationError(f"Failed to load CSV: {e}")
    
    async def load_from_json(self, file_path: str, data_type: str, 
                           clear_existing: bool = False) -> Dict[str, Any]:
        """
        Load data from JSON file.
        
        Args:
            file_path: Path to JSON file
            data_type: Type of data ('knowledge_base', 'companies', or 'financial_records')
            clear_existing: Whether to clear existing data first
            
        Returns:
            Upload result summary
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If data format is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
                
                if not isinstance(data, list):
                    raise ValidationError("JSON file must contain an array of objects")
                
                logger.info(f"Loaded {len(data)} records from JSON", file_path=file_path)
                
                if data_type == "knowledge_base":
                    return await self.upload_knowledge_base(data, clear_existing)
                elif data_type == "companies":
                    return await self.upload_companies(data, clear_existing)
                elif data_type == "financial_records":
                    return await self.upload_financial_records(data, clear_existing)
                else:
                    raise ValidationError(f"Invalid data_type: {data_type}")
                    
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON format", file_path=file_path, error=str(e))
            raise ValidationError(f"Invalid JSON format: {e}")
        except Exception as e:
            logger.error("Failed to load JSON file", file_path=file_path, error=str(e))
            raise ValidationError(f"Failed to load JSON: {e}")
    
    async def get_upload_template(self, data_type: str) -> Dict[str, Any]:
        """
        Get data upload template with example data.
        
        Args:
            data_type: Type of template ('knowledge_base', 'companies', or 'financial_records')
            
        Returns:
            Template with example data and field descriptions
        """
        if data_type == "knowledge_base":
            return {
                "description": "Knowledge base Q&A data upload template",
                "required_fields": ["question", "answer", "category"],
                "optional_fields": ["tags", "metadata", "state", "priority", "personas", "source", "difficulty"],
                "example_data": [
                    {
                        "question": "What are the contractor license requirements for Georgia?",
                        "answer": "Georgia requires contractors to be licensed for work over $2,500. General contractor license requires 4 years experience or equivalent education. Application fee is $200, with total costs ranging $300-400.",
                        "category": "state_licensing_requirements",
                        "tags": "georgia,general_contractor,license_requirements,fees",
                        "metadata": '{"state":"GA","difficulty":"basic","urgency":"normal"}',
                        "state": "GA",
                        "priority": "normal",
                        "personas": "confused_newcomer,urgent_operator",
                        "source": "state_requirements_guide",
                        "difficulty": "basic"
                    }
                ],
                "field_descriptions": {
                    "question": "Question or topic (string, required, min 5 chars)",
                    "answer": "Answer or explanation (string, required, min 10 chars)",
                    "category": "Category slug (string, required, auto-normalized)",
                    "tags": "Comma-separated tags (string, optional)",
                    "metadata": "JSON metadata (string, optional)",
                    "state": "State code if applicable (string, optional, auto-uppercased)",
                    "priority": "Priority level: low, normal, high, critical (string, optional, default: normal)",
                    "personas": "Target user personas, comma-separated (string, optional)",
                    "source": "Source reference (string, optional)",
                    "difficulty": "Difficulty level: basic, intermediate, advanced (string, optional, default: basic)"
                }
            }
        elif data_type == "companies":
            return {
                "description": "Company data upload template",
                "required_fields": ["name", "symbol", "sector"],
                "optional_fields": ["founded_year", "employees", "market_cap"],
                "example_data": [
                    {
                        "name": "Example Corp",
                        "symbol": "EXMP",
                        "sector": "Technology",
                        "founded_year": 2000,
                        "employees": 5000,
                        "market_cap": 1000000000.0
                    }
                ],
                "field_descriptions": {
                    "name": "Company name (string, required)",
                    "symbol": "Stock symbol (string, required, will be uppercased)",
                    "sector": "Industry sector (string, required)",
                    "founded_year": "Year company was founded (integer, optional)",
                    "employees": "Number of employees (integer, optional)",
                    "market_cap": "Market capitalization in USD (float, optional)"
                }
            }
        elif data_type == "financial_records":
            return {
                "description": "Financial records upload template",
                "required_fields": ["company_id", "quarter", "year", "revenue", "profit", "expenses"],
                "optional_fields": [],
                "example_data": [
                    {
                        "company_id": 1,
                        "quarter": "Q1",
                        "year": 2025,
                        "revenue": 1000000000.0,
                        "profit": 200000000.0,
                        "expenses": 800000000.0
                    }
                ],
                "field_descriptions": {
                    "company_id": "ID of company (integer, must exist in companies table)",
                    "quarter": "Quarter (Q1, Q2, Q3, or Q4)",
                    "year": "Year (integer, 1900-current year+5)",
                    "revenue": "Total revenue (float, must be >= 0)",
                    "profit": "Net profit (float, can be negative for losses)",
                    "expenses": "Total expenses (float, must be >= 0)"
                }
            }
        else:
            raise ValidationError(f"Invalid data_type: {data_type}. Must be 'companies' or 'financial_records'")


async def main():
    """
    Main function for testing data upload functionality.
    """
    uploader = DataUploader()
    
    # Example usage
    print("Data Upload Module Ready")
    print("Use the DataUploader class to upload custom data")


if __name__ == "__main__":
    asyncio.run(main())
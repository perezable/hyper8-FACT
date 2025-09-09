#!/usr/bin/env python3
"""
FACT System - Bland AI Knowledge Base Import Script

This script imports Q&A knowledge base data from Bland AI CSV and JSON files
into the FACT system database.
"""

import asyncio
import json
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import structlog

# Add src to Python path
script_dir = Path(__file__).parent
src_dir = script_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from db.connection import DatabaseManager
from data_upload import DataUploader
from core.errors import DatabaseError, ValidationError

logger = structlog.get_logger(__name__)


class BlandKnowledgeImporter:
    """Import Bland AI knowledge base files into FACT system."""
    
    def __init__(self, database_path: str = "data/fact_system.db", database_manager: Optional[DatabaseManager] = None):
        """Initialize importer with database manager."""
        if database_manager:
            self.db_manager = database_manager
        else:
            self.db_manager = DatabaseManager(database_path)
        
        self.uploader = DataUploader(self.db_manager)
        
    def parse_csv_metadata(self, metadata_str: str) -> Dict[str, Any]:
        """Parse JSON metadata from CSV field."""
        try:
            return json.loads(metadata_str)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Invalid metadata JSON", metadata=metadata_str[:100])
            return {}
    
    def extract_personas_from_answer(self, answer: str) -> str:
        """Extract persona information from answer text."""
        personas = []
        
        # Look for persona patterns in the answer
        if "[Especially relevant for:" in answer:
            start = answer.find("[Especially relevant for:") + len("[Especially relevant for:")
            end = answer.find("]", start)
            if end > start:
                persona_text = answer[start:end].strip()
                # Split by comma and clean up
                personas = [p.strip() for p in persona_text.split(",")]
        
        return ",".join(personas)
    
    def extract_priority_from_answer(self, answer: str) -> str:
        """Extract priority information from answer text."""
        if "⚡ HIGH PRIORITY" in answer:
            return "high"
        elif "⚡ CRITICAL PRIORITY" in answer:
            return "critical"
        elif "⚡ NORMAL PRIORITY" in answer:
            return "normal"
        else:
            return "normal"
    
    def extract_state_from_tags_or_content(self, tags: str, question: str, metadata: Dict) -> str:
        """Extract state code from tags, question, or metadata."""
        # Check metadata first
        if metadata.get("state"):
            return str(metadata["state"]).upper()
        
        # Common state names/abbreviations to look for
        state_map = {
            "georgia": "GA",
            "florida": "FL", 
            "texas": "TX",
            "california": "CA",
            "new york": "NY",
            "illinois": "IL",
            # Add more states as needed
        }
        
        # Check question content
        question_lower = question.lower()
        for state_name, state_code in state_map.items():
            if state_name in question_lower:
                return state_code
        
        # Check tags
        tags_lower = tags.lower()
        for state_name, state_code in state_map.items():
            if state_name in tags_lower:
                return state_code
                
        return ""
    
    def normalize_csv_entry(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a CSV row to knowledge base format."""
        # Parse metadata
        metadata = self.parse_csv_metadata(row.get("metadata", "{}"))
        
        # Clean answer text by removing persona and priority annotations
        answer = row.get("answer", "").strip()
        
        # Remove persona annotations
        if "[Especially relevant for:" in answer:
            start = answer.find("[Especially relevant for:")
            end = answer.find("]", start) + 1
            if end > start:
                answer = answer[:start] + answer[end:].strip()
        
        # Remove priority annotations  
        priority_patterns = ["⚡ HIGH PRIORITY:", "⚡ CRITICAL PRIORITY:", "⚡ NORMAL PRIORITY:"]
        for pattern in priority_patterns:
            if pattern in answer:
                answer = answer.replace(pattern, "").strip()
        
        # Clean up extra whitespace and newlines
        answer = " ".join(answer.split())
        
        # Extract information
        personas = self.extract_personas_from_answer(row.get("answer", ""))
        priority = self.extract_priority_from_answer(row.get("answer", ""))
        state = self.extract_state_from_tags_or_content(
            row.get("tags", ""), 
            row.get("question", ""), 
            metadata
        )
        
        return {
            "question": row.get("question", "").strip(),
            "answer": answer,
            "category": row.get("category", "general").strip(),
            "tags": row.get("tags", "").strip(),
            "metadata": json.dumps(metadata) if metadata else "",
            "state": state,
            "priority": priority,
            "personas": personas,
            "source": metadata.get("source", "bland_comprehensive_import.csv"),
            "difficulty": metadata.get("difficulty", "basic")
        }
    
    def normalize_json_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a JSON entry to knowledge base format."""
        # Extract personas from personas array or string
        personas = entry.get("personas", [])
        if isinstance(personas, list):
            personas_str = ",".join(personas)
        else:
            personas_str = str(personas) if personas else ""
        
        # Extract tags from tags array or string
        tags = entry.get("tags", [])
        if isinstance(tags, list):
            tags_str = ",".join(tags)
        else:
            tags_str = str(tags) if tags else ""
        
        # Handle different field names (question/title, answer/content)
        question = entry.get("question", entry.get("title", "")).strip()
        answer = entry.get("answer", entry.get("content", "")).strip()
        
        # Extract priority from urgency field if available
        priority = entry.get("priority", entry.get("urgency", "normal")).lower()
        
        # Extract difficulty
        difficulty = entry.get("difficulty", entry.get("difficulty_level", "basic")).lower()
        
        # Extract source reference
        source = entry.get("source", entry.get("source_reference", "MASTER_KNOWLEDGE_BASE.json"))
        
        return {
            "question": question,
            "answer": answer,
            "category": entry.get("category", "general").strip(),
            "tags": tags_str,
            "metadata": json.dumps(entry.get("metadata", {})),
            "state": str(entry.get("state", "")).upper() if entry.get("state") else "",
            "priority": priority,
            "personas": personas_str,
            "source": source,
            "difficulty": difficulty
        }
    
    async def import_csv_file(self, file_path: str, clear_existing: bool = False) -> Dict[str, Any]:
        """Import knowledge base from CSV file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        logger.info("Starting CSV import", file=file_path)
        
        try:
            entries = []
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for i, row in enumerate(reader):
                    try:
                        normalized_entry = self.normalize_csv_entry(row)
                        entries.append(normalized_entry)
                    except Exception as e:
                        logger.error(f"Failed to process CSV row {i+1}", error=str(e), row=row)
                        continue
            
            logger.info(f"Processed {len(entries)} entries from CSV")
            
            # Upload to database
            result = await self.uploader.upload_knowledge_base(entries, clear_existing)
            
            logger.info("CSV import completed successfully", 
                       entries_imported=result.get("records_uploaded", 0))
            return result
            
        except Exception as e:
            logger.error("CSV import failed", error=str(e))
            raise DatabaseError(f"Failed to import CSV: {e}")
    
    async def import_json_file(self, file_path: str, clear_existing: bool = False) -> Dict[str, Any]:
        """Import knowledge base from JSON file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        logger.info("Starting JSON import", file=file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                data = json.load(jsonfile)
            
            entries = []
            
            # Handle different JSON structures
            if isinstance(data, dict):
                # If it's a structured knowledge base with categories
                if "knowledge_base" in data:
                    raw_entries = data["knowledge_base"]
                elif "entries" in data:
                    raw_entries = data["entries"]
                else:
                    # Assume the dict values contain the entries
                    raw_entries = []
                    for key, value in data.items():
                        if isinstance(value, list):
                            raw_entries.extend(value)
                        elif isinstance(value, dict) and "entries" in value:
                            raw_entries.extend(value["entries"])
                        elif isinstance(value, dict) and any(k in value for k in ["question", "answer"]):
                            raw_entries.append(value)
            elif isinstance(data, list):
                raw_entries = data
            else:
                raise ValidationError("Unsupported JSON format")
            
            # Normalize entries
            for i, entry in enumerate(raw_entries):
                try:
                    if isinstance(entry, dict):
                        normalized_entry = self.normalize_json_entry(entry)
                        entries.append(normalized_entry)
                except Exception as e:
                    logger.error(f"Failed to process JSON entry {i+1}", error=str(e), entry=entry)
                    continue
            
            logger.info(f"Processed {len(entries)} entries from JSON")
            
            # Upload to database  
            result = await self.uploader.upload_knowledge_base(entries, clear_existing)
            
            logger.info("JSON import completed successfully",
                       entries_imported=result.get("records_uploaded", 0))
            return result
            
        except Exception as e:
            logger.error("JSON import failed", error=str(e))
            raise DatabaseError(f"Failed to import JSON: {e}")
    
    async def import_bland_files(self, csv_path: str, json_path: str, 
                                clear_existing: bool = True) -> Dict[str, Any]:
        """Import both Bland AI knowledge base files."""
        logger.info("Starting comprehensive Bland AI import")
        
        results = {
            "csv_result": None,
            "json_result": None,
            "total_imported": 0,
            "status": "success"
        }
        
        try:
            # Import CSV first (clear existing data)
            if os.path.exists(csv_path):
                logger.info("Importing CSV knowledge base")
                csv_result = await self.import_csv_file(csv_path, clear_existing)
                results["csv_result"] = csv_result
                results["total_imported"] += csv_result.get("records_uploaded", 0)
            else:
                logger.warning("CSV file not found", path=csv_path)
            
            # Import JSON second (append to existing data)
            if os.path.exists(json_path):
                logger.info("Importing JSON knowledge base")
                json_result = await self.import_json_file(json_path, clear_existing=False)
                results["json_result"] = json_result
                results["total_imported"] += json_result.get("records_uploaded", 0)
            else:
                logger.warning("JSON file not found", path=json_path)
            
            logger.info("Bland AI import completed successfully", 
                       total_imported=results["total_imported"])
            
            return results
            
        except Exception as e:
            logger.error("Bland AI import failed", error=str(e))
            results["status"] = "error"
            results["error"] = str(e)
            raise DatabaseError(f"Failed to import Bland AI files: {e}")


async def main():
    """Main function to run the import."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import Bland AI knowledge base into FACT system")
    parser.add_argument("--csv", 
                       default="/Users/natperez/codebases/hyper8/CLP/bland_ai/bland_comprehensive_import.csv",
                       help="Path to Bland AI CSV file")
    parser.add_argument("--json",
                       default="/Users/natperez/codebases/hyper8/CLP/bland_ai/MASTER_KNOWLEDGE_BASE.json", 
                       help="Path to Bland AI JSON file")
    parser.add_argument("--clear", action="store_true",
                       help="Clear existing knowledge base data before import")
    parser.add_argument("--csv-only", action="store_true",
                       help="Import only CSV file")
    parser.add_argument("--json-only", action="store_true", 
                       help="Import only JSON file")
    
    args = parser.parse_args()
    
    # Configure logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    try:
        # Initialize database
        database_path = "data/fact_system.db"
        db_manager = DatabaseManager(database_path)
        await db_manager.initialize_database()
        
        # Create importer
        importer = BlandKnowledgeImporter(database_path, db_manager)
        
        # Import files based on arguments
        if args.csv_only:
            print(f"🔄 Importing CSV file: {args.csv}")
            result = await importer.import_csv_file(args.csv, args.clear)
            print(f"✅ CSV import completed: {result['records_uploaded']} entries imported")
            
        elif args.json_only:
            print(f"🔄 Importing JSON file: {args.json}")
            result = await importer.import_json_file(args.json, args.clear)
            print(f"✅ JSON import completed: {result['records_uploaded']} entries imported")
            
        else:
            print("🔄 Importing both Bland AI knowledge base files")
            print(f"📁 CSV: {args.csv}")
            print(f"📁 JSON: {args.json}")
            
            results = await importer.import_bland_files(args.csv, args.json, args.clear)
            
            print(f"✅ Import completed successfully!")
            print(f"📊 Total entries imported: {results['total_imported']}")
            
            if results.get("csv_result"):
                print(f"   📄 CSV entries: {results['csv_result']['records_uploaded']}")
            if results.get("json_result"):
                print(f"   📄 JSON entries: {results['json_result']['records_uploaded']}")
        
        # Cleanup
        await db_manager.cleanup()
        print("🎉 Knowledge base import completed successfully!")
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        logger.error("Import script failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
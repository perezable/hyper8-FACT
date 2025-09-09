#!/usr/bin/env python3
"""
FACT System - Complete Bland AI Knowledge Base Import Script

This script imports all Bland AI knowledge base JSON files including:
- State requirements
- Personas
- Conversation pathways
- Branching logic
- Trust scoring
- Success stories
- Objection handling
- Knowledge retrieval configurations
"""

import asyncio
import json
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
from db.extended_models import EXTENDED_DATABASE_SCHEMA
from data_upload import DataUploader
from core.errors import DatabaseError, ValidationError

logger = structlog.get_logger(__name__)


class CompleteKnowledgeImporter:
    """Import complete Bland AI knowledge base with all features."""
    
    def __init__(self, database_path: str = "data/fact_system.db"):
        """Initialize importer with database manager."""
        self.database_path = database_path
        self.db_manager = DatabaseManager(database_path)
        self.uploader = DataUploader(self.db_manager)
        self.bland_dir = Path("/Users/natperez/codebases/hyper8/CLP/bland_ai")
        
    async def initialize_extended_schema(self):
        """Initialize extended database schema for all features."""
        try:
            async with self.db_manager.get_connection() as db:
                # Execute extended schema creation
                await db.executescript(EXTENDED_DATABASE_SCHEMA)
                await db.commit()
                logger.info("Extended database schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize extended schema: {e}")
            raise DatabaseError(f"Schema initialization failed: {e}")
    
    async def import_personas(self, file_path: Path) -> int:
        """Import persona detection configuration."""
        logger.info(f"Importing personas from {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            personas_data = data.get("persona_detection_system", {}).get("personas", {})
            count = 0
            
            async with self.db_manager.get_connection() as conn:
                for persona_type, persona_info in personas_data.items():
                    await conn.execute("""
                        INSERT OR REPLACE INTO personas 
                        (persona_type, name, description, priority, percentage, detection_rules, response_adjustments)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        persona_type,
                        persona_info.get("name", persona_type),
                        persona_info.get("description", ""),
                        persona_info.get("priority", "normal"),
                        persona_info.get("percentage", 0.0),
                        json.dumps(persona_info.get("detection_rules", {})),
                        json.dumps(persona_info.get("response_adjustments", {}))
                    ))
                    count += 1
                
                await conn.commit()
                
            logger.info(f"Imported {count} personas")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import personas: {e}")
            raise DatabaseError(f"Persona import failed: {e}")
    
    async def import_state_requirements(self, file_path: Path) -> int:
        """Import detailed state licensing requirements."""
        logger.info(f"Importing state requirements from {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            states_data = data.get("states", {})
            count = 0
            
            async with self.db_manager.get_connection() as conn:
                for state_code, state_info in states_data.items():
                    # Import general contractor requirements
                    gc_info = state_info.get("general_contractor", {})
                    
                    if gc_info:
                        # Handle different license types
                        license_types = gc_info.get("license_types", [])
                        
                        if not license_types:
                            # If no license types array, create a single entry
                            license_types = [{"class": "B", "name": "General Building Contractor"}]
                        
                        for license_type in license_types:
                            # Handle experience requirements
                            exp_req = gc_info.get("experience_requirements", {})
                            exp_years = exp_req.get("minimum_years", 0) if isinstance(exp_req, dict) else 0
                            
                            # Handle bond requirements
                            bond_req = gc_info.get("bond_requirements", {})
                            bond_amount = bond_req.get("amount", 0) if isinstance(bond_req, dict) else 0
                            
                            await conn.execute("""
                                INSERT OR REPLACE INTO state_requirements 
                                (state_code, state_name, regulatory_body, license_class, license_type,
                                 experience_years, education_requirements, exam_requirements, bond_amount,
                                 insurance_requirements, application_fees, processing_timeline, 
                                 renewal_cycle, continuing_education_hours, reciprocity_states,
                                 special_provisions, metadata)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                state_code,
                                state_info.get("state_name", state_code),
                                state_info.get("regulatory_body", ""),
                                license_type.get("class", "") if isinstance(license_type, dict) else "",
                                license_type.get("name", "") if isinstance(license_type, dict) else "",
                                exp_years,
                                json.dumps(gc_info.get("education_requirements", {})),
                                json.dumps(gc_info.get("exam_requirements", {})),
                                bond_amount,
                                json.dumps(gc_info.get("insurance_requirements", {})),
                                json.dumps(gc_info.get("application_fees", {})),
                                gc_info.get("processing_timeline", ""),
                                gc_info.get("renewal_cycle", ""),
                                gc_info.get("continuing_education_hours", 0),
                                ",".join(gc_info.get("reciprocity_agreements", [])),
                                json.dumps(gc_info.get("special_provisions", [])),
                                json.dumps({"source": "state_requirements_complete.json"})
                            ))
                            count += 1
                
                await conn.commit()
                
            logger.info(f"Imported {count} state requirement entries")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import state requirements: {e}")
            raise DatabaseError(f"State requirements import failed: {e}")
    
    async def import_branching_logic(self, file_path: Path) -> int:
        """Import branching logic configuration."""
        logger.info(f"Importing branching logic from {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            branching_data = data.get("branching_logic", {})
            count = 0
            
            async with self.db_manager.get_connection() as conn:
                # Import persona detection branching
                persona_detection = branching_data.get("persona_detection", {})
                for persona_type, config in persona_detection.items():
                    routing = config.get("routing_conditions", {})
                    await conn.execute("""
                        INSERT OR REPLACE INTO branching_logic 
                        (trigger_name, trigger_patterns, trigger_keywords, condition_expression,
                         action_type, action_target, priority, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"persona_{persona_type}",
                        json.dumps(config.get("detection_criteria", {})),
                        json.dumps([]),  # Keywords extracted from criteria
                        json.dumps(routing),
                        "route",
                        routing.get("then", "continue"),
                        "high",
                        json.dumps(config.get("branch_adjustments", {}))
                    ))
                    count += 1
                
                # Import decision tree branches
                decision_trees = branching_data.get("decision_trees", {})
                for tree_name, tree_config in decision_trees.items():
                    branches = tree_config.get("branches", {})
                    for branch_name, branch_info in branches.items():
                        await conn.execute("""
                            INSERT OR REPLACE INTO branching_logic 
                            (trigger_name, trigger_patterns, trigger_keywords, condition_expression,
                             action_type, action_target, priority, metadata)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            f"{tree_name}_{branch_name}",
                            json.dumps(branch_info.get("conditions", [])),
                            json.dumps(branch_info.get("keywords", [])),
                            json.dumps(branch_info.get("expression", {})),
                            branch_info.get("action", "response"),
                            branch_info.get("target", ""),
                            branch_info.get("priority", "normal"),
                            json.dumps(branch_info)
                        ))
                        count += 1
                
                await conn.commit()
                
            logger.info(f"Imported {count} branching logic entries")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import branching logic: {e}")
            raise DatabaseError(f"Branching logic import failed: {e}")
    
    async def import_trust_monitoring(self, file_path: Path) -> int:
        """Import trust monitoring configuration."""
        logger.info(f"Importing trust monitoring from {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            trust_system = data.get("trust_temperature_system", {})
            count = 0
            
            # Store trust indicators as conversation pathways
            async with self.db_manager.get_connection() as conn:
                indicators = trust_system.get("trust_indicators", {})
                
                for indicator_type, indicator_data in indicators.items():
                    for category, config in indicator_data.items():
                        weight = config.get("weight", 0)
                        phrases = config.get("indicators", [])
                        
                        for phrase in phrases:
                            await conn.execute("""
                                INSERT OR REPLACE INTO conversation_pathways 
                                (pathway_name, pathway_type, content, trust_adjustment, metadata)
                                VALUES (?, ?, ?, ?, ?)
                            """, (
                                f"trust_{indicator_type}_{category}",
                                "trust_indicator",
                                phrase,
                                weight if indicator_type.startswith("positive") else -weight,
                                json.dumps({
                                    "type": indicator_type,
                                    "category": category,
                                    "source": "trust_monitoring.json"
                                })
                            ))
                            count += 1
                
                await conn.commit()
                
            logger.info(f"Imported {count} trust monitoring indicators")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import trust monitoring: {e}")
            raise DatabaseError(f"Trust monitoring import failed: {e}")
    
    async def import_success_stories(self, file_path: Path) -> int:
        """Import success stories and case studies."""
        logger.info(f"Importing success stories from {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stories_data = data.get("success_stories", [])
            count = 0
            
            async with self.db_manager.get_connection() as conn:
                for story in stories_data:
                    customer = story.get("customer_profile", {})
                    results = story.get("results", {})
                    
                    await conn.execute("""
                        INSERT OR REPLACE INTO success_stories 
                        (story_title, customer_profile, initial_situation, solution_provided,
                         results_achieved, roi_metrics, testimonial_quote, persona_types,
                         state_code, industry, priority, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        story.get("title", ""),
                        json.dumps(customer),
                        story.get("initial_situation", ""),
                        story.get("solution_provided", ""),
                        story.get("results_achieved", ""),
                        json.dumps(results.get("roi_metrics", {})),
                        story.get("testimonial", {}).get("quote", ""),
                        ",".join(story.get("target_personas", [])),
                        customer.get("state", ""),
                        customer.get("industry", ""),
                        story.get("priority", "normal"),
                        json.dumps({"source": "success_stories_database.json"})
                    ))
                    count += 1
                
                await conn.commit()
                
            logger.info(f"Imported {count} success stories")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import success stories: {e}")
            raise DatabaseError(f"Success stories import failed: {e}")
    
    async def import_knowledge_retrieval_config(self, file_path: Path) -> int:
        """Import knowledge retrieval configurations."""
        logger.info(f"Importing retrieval config from {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            retrieval_data = data.get("knowledge_retrieval", {})
            triggers = retrieval_data.get("retrieval_triggers", {})
            count = 0
            
            async with self.db_manager.get_connection() as conn:
                for trigger_name, config in triggers.items():
                    await conn.execute("""
                        INSERT OR REPLACE INTO retrieval_configs 
                        (trigger_name, patterns, keywords, query_template, category_filter,
                         max_results, confidence_threshold, priority, personalization_enabled, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trigger_name,
                        json.dumps(config.get("patterns", [])),
                        json.dumps(config.get("keywords", [])),
                        config.get("query_template", ""),
                        config.get("category_filter", ""),
                        config.get("max_results", 3),
                        config.get("confidence_threshold", 0.7),
                        config.get("priority", "normal"),
                        1 if config.get("personalization_enabled", True) else 0,
                        json.dumps(config)
                    ))
                    count += 1
                
                await conn.commit()
                
            logger.info(f"Imported {count} retrieval configurations")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import retrieval config: {e}")
            raise DatabaseError(f"Retrieval config import failed: {e}")
    
    async def import_pathway_config(self, file_path: Path) -> int:
        """Import conversation pathway configurations."""
        logger.info(f"Importing pathway config from {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            pathway_data = data.get("pathway", {})
            nodes = pathway_data.get("nodes", [])
            count = 0
            
            async with self.db_manager.get_connection() as conn:
                for node in nodes:
                    # Import each node as a conversation pathway
                    await conn.execute("""
                        INSERT OR REPLACE INTO conversation_pathways 
                        (pathway_name, pathway_type, sequence_order, content, 
                         next_conditions, trust_adjustment, momentum_impact, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        node.get("id", ""),
                        node.get("type", "main"),
                        count,  # Use count as sequence order
                        node.get("text", ""),
                        json.dumps(node.get("conditions", {})),
                        0.0,  # Default trust adjustment
                        0.0,  # Default momentum impact
                        json.dumps(node)
                    ))
                    count += 1
                
                await conn.commit()
                
            logger.info(f"Imported {count} pathway nodes")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import pathway config: {e}")
            raise DatabaseError(f"Pathway config import failed: {e}")
    
    async def import_webhook_config(self, file_path: Path) -> int:
        """Import webhook configurations."""
        logger.info(f"Importing webhook config from {file_path.name}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            webhooks_data = data.get("webhooks", {})
            endpoints = webhooks_data.get("endpoints", {})
            count = 0
            
            async with self.db_manager.get_connection() as conn:
                for webhook_name, config in endpoints.items():
                    await conn.execute("""
                        INSERT OR REPLACE INTO webhook_configs 
                        (webhook_name, endpoint_url, http_method, headers, event_types,
                         retry_attempts, retry_backoff, timeout_ms, enabled, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        webhook_name,
                        config.get("url", ""),
                        config.get("method", "POST"),
                        json.dumps(config.get("headers", {})),
                        json.dumps(config.get("events", [])),
                        config.get("retry", {}).get("attempts", 3),
                        config.get("retry", {}).get("backoff", "exponential"),
                        config.get("response_handling", {}).get("timeout_ms", 3000),
                        1,  # Enabled by default
                        json.dumps(config)
                    ))
                    count += 1
                
                await conn.commit()
                
            logger.info(f"Imported {count} webhook configurations")
            return count
            
        except Exception as e:
            logger.error(f"Failed to import webhook config: {e}")
            raise DatabaseError(f"Webhook config import failed: {e}")
    
    async def import_all_knowledge_files(self) -> Dict[str, int]:
        """Import all Bland AI knowledge base files."""
        logger.info("Starting comprehensive knowledge base import")
        
        results = {
            "personas": 0,
            "state_requirements": 0,
            "branching_logic": 0,
            "trust_monitoring": 0,
            "success_stories": 0,
            "retrieval_configs": 0,
            "pathway_configs": 0,
            "webhook_configs": 0,
            "total": 0
        }
        
        try:
            # Initialize extended schema
            await self.initialize_extended_schema()
            
            # Import each type of knowledge file
            import_tasks = [
                ("personas", self.bland_dir / "persona_detection.json", self.import_personas),
                ("state_requirements", self.bland_dir / "state_requirements_complete.json", self.import_state_requirements),
                ("branching_logic", self.bland_dir / "branching_logic.json", self.import_branching_logic),
                ("trust_monitoring", self.bland_dir / "trust_monitoring.json", self.import_trust_monitoring),
                ("success_stories", self.bland_dir / "success_stories_database.json", self.import_success_stories),
                ("retrieval_configs", self.bland_dir / "knowledge_retrieval_config.json", self.import_knowledge_retrieval_config),
                ("pathway_configs", self.bland_dir / "pathway_config.json", self.import_pathway_config),
                ("webhook_configs", self.bland_dir / "webhook_config.json", self.import_webhook_config)
            ]
            
            for key, file_path, import_func in import_tasks:
                if file_path.exists():
                    try:
                        count = await import_func(file_path)
                        results[key] = count
                        results["total"] += count
                    except Exception as e:
                        logger.error(f"Failed to import {key}: {e}")
                else:
                    logger.warning(f"File not found: {file_path}")
            
            logger.info("Comprehensive import completed", results=results)
            return results
            
        except Exception as e:
            logger.error(f"Comprehensive import failed: {e}")
            raise DatabaseError(f"Import failed: {e}")


async def main():
    """Main function to run the comprehensive import."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Import complete Bland AI knowledge base")
    parser.add_argument("--database", 
                       default="data/fact_system.db",
                       help="Path to database file")
    parser.add_argument("--bland-dir",
                       default="/Users/natperez/codebases/hyper8/CLP/bland_ai",
                       help="Path to Bland AI directory")
    
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
        print("🚀 Starting comprehensive Bland AI knowledge base import")
        print(f"📁 Bland AI directory: {args.bland_dir}")
        print(f"💾 Database: {args.database}")
        print()
        
        # Create importer
        importer = CompleteKnowledgeImporter(args.database)
        
        # Import all files
        results = await importer.import_all_knowledge_files()
        
        print("✅ Import completed successfully!")
        print("📊 Import Summary:")
        print(f"   👤 Personas: {results['personas']}")
        print(f"   🏛️ State Requirements: {results['state_requirements']}")
        print(f"   🔀 Branching Logic: {results['branching_logic']}")
        print(f"   🤝 Trust Monitoring: {results['trust_monitoring']}")
        print(f"   🌟 Success Stories: {results['success_stories']}")
        print(f"   🔍 Retrieval Configs: {results['retrieval_configs']}")
        print(f"   🗺️ Pathway Configs: {results['pathway_configs']}")
        print(f"   🔗 Webhook Configs: {results['webhook_configs']}")
        print(f"   📦 Total Entries: {results['total']}")
        
        # Cleanup
        await importer.db_manager.cleanup()
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        logger.error("Import script failed", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
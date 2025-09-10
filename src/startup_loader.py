"""
Startup loader for Railway deployment.
Loads knowledge base data on application startup.
"""

import json
import sqlite3
import os
import structlog

logger = structlog.get_logger(__name__)

def load_knowledge_base_on_startup():
    """Load knowledge base data into SQLite on startup."""
    try:
        # Check if we're on Railway
        if not os.getenv("RAILWAY_ENVIRONMENT"):
            logger.info("Not on Railway, skipping startup load")
            return
        
        logger.info("Railway environment detected, loading knowledge base...")
        
        # Connect to database
        db_path = os.getenv("DATABASE_PATH", "data/fact_system.db")
        if not os.path.exists(db_path):
            db_path = "fact_system.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if data already loaded
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        count = cursor.fetchone()[0]
        
        if count >= 400:
            logger.info(f"Knowledge base already has {count} entries, skipping load")
            conn.close()
            return
        
        logger.info(f"Only {count} entries found, loading full knowledge base...")
        
        # Load knowledge export
        knowledge_file = "data/knowledge_export.json"
        if not os.path.exists(knowledge_file):
            # Try to load from embedded data
            logger.warning(f"Knowledge export not found at {knowledge_file}")
            
            # Create minimal data for testing
            test_data = [
                {
                    "id": "KB_001",
                    "question": "California Contractor License Requirements",
                    "answer": "California requires contractors to pass an exam, have 4 years of experience, and obtain a bond.",
                    "category": "state_licensing_requirements",
                    "state": "CA",
                    "tags": "california,license,requirements",
                    "priority": "high",
                    "difficulty": "intermediate"
                },
                {
                    "id": "KB_002", 
                    "question": "How do I prepare for the contractor exam?",
                    "answer": "Study the official guides, take practice tests, and consider a prep course.",
                    "category": "exam_preparation_testing",
                    "tags": "exam,preparation,study",
                    "priority": "high",
                    "difficulty": "basic"
                },
                {
                    "id": "KB_003",
                    "question": "What is the PSI exam?",
                    "answer": "PSI is the testing service that administers contractor license exams in many states.",
                    "category": "exam_preparation_testing",
                    "tags": "PSI,exam,testing",
                    "priority": "normal",
                    "difficulty": "basic"
                },
                {
                    "id": "KB_004",
                    "question": "How do I get a surety bond?",
                    "answer": "Contact a surety bond company, provide financial information, and pay the premium.",
                    "category": "insurance_bonding",
                    "tags": "surety,bond,insurance",
                    "priority": "high",
                    "difficulty": "intermediate"
                }
            ]
            
            # Insert test data
            for entry in test_data:
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_base 
                    (id, question, answer, category, state, tags, priority, difficulty)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.get("id"),
                    entry.get("question"),
                    entry.get("answer"),
                    entry.get("category"),
                    entry.get("state"),
                    entry.get("tags"),
                    entry.get("priority"),
                    entry.get("difficulty")
                ))
            
            conn.commit()
            logger.info(f"Loaded {len(test_data)} test entries")
        else:
            # Load full knowledge base
            with open(knowledge_file, 'r') as f:
                data = json.load(f)
            
            entries = data.get('knowledge_base', [])
            logger.info(f"Loading {len(entries)} entries from export...")
            
            # Clear existing data
            cursor.execute("DELETE FROM knowledge_base")
            
            # Insert all entries
            for entry in entries:
                cursor.execute("""
                    INSERT OR REPLACE INTO knowledge_base 
                    (id, question, answer, category, state, tags, priority, difficulty, personas, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.get("id"),
                    entry.get("question"),
                    entry.get("answer"),
                    entry.get("category"),
                    entry.get("state"),
                    entry.get("tags"),
                    entry.get("priority", "normal"),
                    entry.get("difficulty", "basic"),
                    entry.get("personas"),
                    entry.get("source")
                ))
            
            conn.commit()
            logger.info(f"Successfully loaded {len(entries)} entries")
        
        # Verify load
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        final_count = cursor.fetchone()[0]
        logger.info(f"Database now has {final_count} entries")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to load knowledge base on startup: {e}")

# Run on module import
if os.getenv("RAILWAY_ENVIRONMENT"):
    load_knowledge_base_on_startup()
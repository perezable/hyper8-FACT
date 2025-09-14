#!/usr/bin/env python3
"""
Merge ALL knowledge base entries from multiple sources
"""

import json
import os
from pathlib import Path
from datetime import datetime
import hashlib

def load_json_safely(filepath):
    """Load JSON file safely"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def create_entry_hash(entry):
    """Create hash for deduplication based on question"""
    question = entry.get('question', '').lower().strip()
    return hashlib.md5(question.encode()).hexdigest()

def merge_all_knowledge():
    """Merge all knowledge entries from different sources"""
    
    all_entries = []
    entry_hashes = set()
    sources_info = {}
    
    # Define source files
    sources = [
        # Primary source - 217 entries from Zoho Workdrive analysis
        "/Users/natperez/codebases/hyper8/hyper8-FACT/data/FINAL_DEPLOYMENT_KNOWLEDGE_20250914_013049.json",
        # Additional extracted entries
        "/Users/natperez/codebases/hyper8/hyper8-FACT/data/zoho_extracted_knowledge.json",
        "/Users/natperez/codebases/hyper8/hyper8-FACT/data/consolidated_knowledge_base.json",
        # Other potential sources
        "/Users/natperez/codebases/hyper8/hyper8-FACT/data/deployment_ready_knowledge_20250914_012346.json",
        "/Users/natperez/codebases/hyper8/hyper8-FACT/data/comprehensive_state_knowledge.json"
    ]
    
    # Process each source
    for source_path in sources:
        if not os.path.exists(source_path):
            print(f"Skipping missing file: {source_path}")
            continue
            
        print(f"\nProcessing: {source_path}")
        data = load_json_safely(source_path)
        
        if not data:
            continue
            
        # Extract entries based on structure
        entries = []
        if 'knowledge_entries' in data:
            entries = data['knowledge_entries']
        elif 'deployment_entries' in data:
            entries = data['deployment_entries']
        elif 'entries' in data:
            entries = data['entries']
        elif 'qa_pairs' in data:
            entries = data['qa_pairs']
        elif isinstance(data, list):
            entries = data
            
        source_name = Path(source_path).name
        sources_info[source_name] = {
            'total': len(entries),
            'added': 0,
            'duplicates': 0
        }
        
        # Add unique entries
        for entry in entries:
            entry_hash = create_entry_hash(entry)
            if entry_hash not in entry_hashes:
                # Assign new ID
                entry['id'] = 40000 + len(all_entries) + 1
                entry['source_file'] = source_name
                all_entries.append(entry)
                entry_hashes.add(entry_hash)
                sources_info[source_name]['added'] += 1
            else:
                sources_info[source_name]['duplicates'] += 1
    
    # Sort by quality score if available
    all_entries.sort(key=lambda x: x.get('quality_score', 0) or x.get('priority', 0) == 'critical', reverse=True)
    
    # Create final merged knowledge base
    merged_knowledge = {
        "metadata": {
            "source": "MASTER Consolidation - ALL Sources Merged",
            "extraction_date": datetime.now().strftime("%Y-%m-%d"),
            "generation_timestamp": datetime.now().isoformat(),
            "total_entries": len(all_entries),
            "unique_entries": len(all_entries),
            "sources_processed": len(sources_info),
            "quality_threshold": 7.0,
            "personas_targeted": [
                "price_conscious",
                "overwhelmed_veteran", 
                "skeptical_researcher",
                "time_pressed",
                "ambitious_entrepreneur"
            ]
        },
        "source_breakdown": sources_info,
        "statistics": {
            "total_unique_entries": len(all_entries),
            "by_category": {},
            "by_state": {},
            "by_priority": {},
            "quality_scores": {
                "high_quality_7plus": 0,
                "medium_quality_5to7": 0,
                "needs_improvement_below5": 0
            }
        },
        "knowledge_entries": all_entries,
        "deployment_instructions": {
            "railway_url": "https://hyper8-fact-production.up.railway.app",
            "deployment_note": "Railway app appears to be offline as of 2025-09-14",
            "upload_script": "/scripts/upload_master_knowledge.py",
            "method": "POST to /upload-data endpoint",
            "clear_existing": False,
            "chunk_size": 10,
            "rate_limit": "300ms between chunks"
        }
    }
    
    # Calculate statistics
    for entry in all_entries:
        # Category stats
        category = entry.get('category', 'uncategorized')
        merged_knowledge['statistics']['by_category'][category] = \
            merged_knowledge['statistics']['by_category'].get(category, 0) + 1
        
        # State stats
        state = entry.get('state', 'ALL')
        merged_knowledge['statistics']['by_state'][state] = \
            merged_knowledge['statistics']['by_state'].get(state, 0) + 1
        
        # Priority stats
        priority = entry.get('priority', 'medium')
        merged_knowledge['statistics']['by_priority'][priority] = \
            merged_knowledge['statistics']['by_priority'].get(priority, 0) + 1
        
        # Quality score stats
        score = entry.get('quality_score', 0)
        if score >= 7:
            merged_knowledge['statistics']['quality_scores']['high_quality_7plus'] += 1
        elif score >= 5:
            merged_knowledge['statistics']['quality_scores']['medium_quality_5to7'] += 1
        else:
            merged_knowledge['statistics']['quality_scores']['needs_improvement_below5'] += 1
    
    # Save merged knowledge base
    output_path = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/MASTER_KNOWLEDGE_BASE_COMPLETE.json"
    with open(output_path, 'w') as f:
        json.dump(merged_knowledge, f, indent=2)
    
    print(f"\n{'='*60}")
    print("MERGE COMPLETE")
    print(f"{'='*60}")
    print(f"Total unique entries: {len(all_entries)}")
    print(f"Output saved to: {output_path}")
    print("\nSource breakdown:")
    for source, info in sources_info.items():
        print(f"  {source}:")
        print(f"    - Total: {info['total']}")
        print(f"    - Added: {info['added']}")
        print(f"    - Duplicates: {info['duplicates']}")
    
    return merged_knowledge

if __name__ == "__main__":
    merge_all_knowledge()
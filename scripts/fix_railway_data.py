#!/usr/bin/env python3
"""
Fix Railway data by clearing and re-uploading the correct knowledge base.
"""

import asyncio
import aiohttp
import json
from pathlib import Path

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def fix_railway_data():
    """Clear bad data and upload correct knowledge base."""
    print("🔧 Fixing Railway Knowledge Base Data")
    print("=" * 70)
    
    # Load the CORRECT knowledge base from CLP directory
    clp_kb_path = Path("/Users/natperez/codebases/hyper8/CLP/bland_ai/MASTER_KNOWLEDGE_BASE.json")
    
    if not clp_kb_path.exists():
        print("❌ Master knowledge base not found")
        return False
    
    print(f"📚 Loading: {clp_kb_path}")
    with open(clp_kb_path, 'r') as f:
        master_data = json.load(f)
    
    print(f"Found {len(master_data)} entries in master knowledge base")
    
    # Verify data quality
    sample = master_data[0]
    print(f"\nSample entry:")
    print(f"  Question: {sample['question'][:80]}")
    print(f"  Category: {sample['category']}")
    print(f"  State: {sample.get('state', 'N/A')}")
    
    async with aiohttp.ClientSession() as session:
        # Clear existing bad data
        print("\n🗑️ Clearing existing data...")
        clear_payload = {
            "data_type": "knowledge_base",
            "data": [],
            "clear_existing": True
        }
        
        async with session.post(
            f"{RAILWAY_URL}/upload-data",
            json=clear_payload
        ) as r:
            if r.status == 200:
                print("✅ Existing data cleared")
            else:
                print(f"❌ Failed to clear data: {r.status}")
        
        # Upload correct data in chunks
        print("\n📤 Uploading correct knowledge base...")
        chunk_size = 50
        total_uploaded = 0
        
        for i in range(0, len(master_data), chunk_size):
            chunk = master_data[i:i+chunk_size]
            chunk_num = (i // chunk_size) + 1
            total_chunks = (len(master_data) + chunk_size - 1) // chunk_size
            
            # Ensure proper format
            formatted_chunk = []
            for entry in chunk:
                formatted_entry = {
                    'question': entry.get('question', ''),
                    'answer': entry.get('answer', ''),
                    'category': entry.get('category', 'general'),
                    'state': entry.get('state', ''),
                    'tags': entry.get('tags', ''),
                    'priority': entry.get('priority', 'normal'),
                    'difficulty': entry.get('difficulty', 'basic'),
                    'personas': entry.get('personas', ''),
                    'source': entry.get('source', 'master_kb')
                }
                
                # Only add entries with valid questions and answers
                if formatted_entry['question'] and formatted_entry['answer']:
                    # Avoid duplicate generic questions
                    if not formatted_entry['question'].startswith("What about "):
                        if not formatted_entry['question'].startswith("Tell me about "):
                            formatted_chunk.append(formatted_entry)
            
            upload_data = {
                'data_type': 'knowledge_base',
                'data': formatted_chunk,
                'clear_existing': False
            }
            
            print(f"Uploading chunk {chunk_num}/{total_chunks} ({len(formatted_chunk)} entries)...")
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as r:
                    if r.status == 200:
                        result = await r.json()
                        total_uploaded += result.get('records_uploaded', 0)
                        print(f"✅ Chunk {chunk_num} uploaded")
                    else:
                        print(f"❌ Chunk {chunk_num} failed: {r.status}")
            except Exception as e:
                print(f"❌ Upload error: {e}")
        
        print(f"\n✅ Total uploaded: {total_uploaded} entries")
        
        # Wait for indexing
        await asyncio.sleep(3)
        
        # Verify the fix
        print("\n🧪 Verifying the fix...")
        
        # Check health
        async with session.get(f"{RAILWAY_URL}/health") as r:
            health = await r.json()
            entries = health['metrics'].get('enhanced_retriever_entries', 0)
            print(f"Enhanced retriever entries: {entries}")
        
        # Test specific queries
        test_queries = [
            "What is a mechanics lien",
            "Georgia contractor license requirements",
            "California exam preparation",
            "contractor bond requirements"
        ]
        
        print("\n🔍 Testing search accuracy...")
        success_count = 0
        
        for query in test_queries:
            async with session.post(
                f"{RAILWAY_URL}/knowledge/search",
                json={"query": query, "limit": 1}
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    if data['results']:
                        result = data['results'][0]
                        print(f"✅ '{query[:30]}...' → Found: {result['question'][:40]}...")
                        success_count += 1
                    else:
                        print(f"❌ '{query[:30]}...' → No results")
        
        accuracy = (success_count / len(test_queries)) * 100
        print(f"\nAccuracy: {accuracy:.1f}% ({success_count}/{len(test_queries)})")
        
        return accuracy >= 75

if __name__ == "__main__":
    import sys
    success = asyncio.run(fix_railway_data())
    sys.exit(0 if success else 1)
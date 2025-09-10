#!/usr/bin/env python3
"""
Upload complete knowledge base to Railway PostgreSQL.
"""

import asyncio
import aiohttp
import json
import os
import sys
from pathlib import Path

# Railway URL
RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def upload_knowledge_base():
    """Upload the complete knowledge base to Railway PostgreSQL."""
    print("🚀 PostgreSQL Knowledge Base Upload")
    print("=" * 70)
    
    # Load knowledge base data
    kb_path = Path(__file__).parent.parent / "data" / "knowledge_export.json"
    
    if not kb_path.exists():
        # Try alternative path
        kb_path = Path("/Users/natperez/codebases/hyper8/CLP/bland_ai/MASTER_KNOWLEDGE_BASE.json")
    
    if not kb_path.exists():
        print("❌ Knowledge base file not found")
        return False
    
    print(f"📚 Loading: {kb_path}")
    
    with open(kb_path, 'r') as f:
        data = json.load(f)
    
    # Extract knowledge base entries
    if 'knowledge_base' in data:
        entries = data['knowledge_base']
    elif 'entries' in data:
        entries = data['entries']
    elif isinstance(data, list):
        entries = data
    else:
        print("❌ Invalid knowledge base format")
        return False
    
    print(f"Found {len(entries)} knowledge entries")
    
    # Ensure each entry has required fields
    processed_entries = []
    for i, entry in enumerate(entries):
        processed = {
            'id': entry.get('id', f'KB_{i+1}'),
            'question': entry.get('question', ''),
            'answer': entry.get('answer', ''),
            'category': entry.get('category', 'general'),
            'state': entry.get('state', ''),
            'tags': entry.get('tags', ''),
            'priority': entry.get('priority', 'normal'),
            'difficulty': entry.get('difficulty', 'basic'),
            'personas': entry.get('personas', ''),
            'source': entry.get('source', 'knowledge_base')
        }
        
        # Skip entries without question or answer
        if processed['question'] and processed['answer']:
            processed_entries.append(processed)
    
    print(f"Processed {len(processed_entries)} valid entries")
    
    async with aiohttp.ClientSession() as session:
        # Check health first
        print("\n🔍 Checking Railway health...")
        try:
            async with session.get(f"{RAILWAY_URL}/health") as r:
                health = await r.json()
                print(f"Status: {health['status']}")
                print(f"Enhanced retriever: {health['metrics'].get('enhanced_retriever', False)}")
                print(f"Current entries: {health['metrics'].get('enhanced_retriever_entries', 0)}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
        
        # Upload in chunks
        print("\n📤 Uploading knowledge base...")
        chunk_size = 50
        total_uploaded = 0
        
        for i in range(0, len(processed_entries), chunk_size):
            chunk = processed_entries[i:i+chunk_size]
            chunk_num = (i // chunk_size) + 1
            total_chunks = (len(processed_entries) + chunk_size - 1) // chunk_size
            
            upload_data = {
                'data_type': 'knowledge_base',
                'data': chunk,
                'clear_existing': (i == 0)  # Clear only on first chunk
            }
            
            print(f"Uploading chunk {chunk_num}/{total_chunks} ({len(chunk)} entries)...")
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as r:
                    if r.status == 200:
                        result = await r.json()
                        total_uploaded += result.get('records_uploaded', 0)
                        print(f"✅ Chunk {chunk_num} uploaded successfully")
                    else:
                        text = await r.text()
                        print(f"❌ Chunk {chunk_num} failed: {r.status} - {text}")
            except Exception as e:
                print(f"❌ Upload error: {e}")
        
        print(f"\n✅ Total uploaded: {total_uploaded} entries")
        
        # Verify upload
        print("\n🧪 Verifying upload...")
        await asyncio.sleep(2)  # Wait for indexing
        
        async with session.get(f"{RAILWAY_URL}/health") as r:
            health = await r.json()
            final_count = health['metrics'].get('enhanced_retriever_entries', 0)
            print(f"Final entry count: {final_count}")
        
        # Test retrieval
        test_queries = [
            "Georgia contractor license requirements",
            "What is a subcontractor lien",
            "Who can file a mechanics lien"
        ]
        
        print("\n🔍 Testing retrieval...")
        for query in test_queries:
            async with session.post(
                f"{RAILWAY_URL}/knowledge/search",
                json={"query": query, "limit": 1}
            ) as r:
                if r.status == 200:
                    data = await r.json()
                    if data['results']:
                        result = data['results'][0]
                        print(f"✅ '{query[:30]}...' → Found match")
                    else:
                        print(f"❌ '{query[:30]}...' → No results")
        
        return True

if __name__ == "__main__":
    success = asyncio.run(upload_knowledge_base())
    sys.exit(0 if success else 1)
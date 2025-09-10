#!/usr/bin/env python3
"""
Upload the MASTER_KNOWLEDGE_BASE.json to Railway deployment.
This loads the 400+ Q&A pairs into the FACT system database.
"""

import json
import asyncio
import aiohttp
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"
KNOWLEDGE_FILE = "/Users/natperez/codebases/hyper8/CLP/bland_ai/MASTER_KNOWLEDGE_BASE.json"

async def upload_knowledge_base():
    """Upload knowledge base to Railway deployment."""
    
    print("📚 Uploading Knowledge Base to Railway")
    print("=" * 70)
    
    # Load the knowledge base
    print(f"Loading: {KNOWLEDGE_FILE}")
    with open(KNOWLEDGE_FILE, 'r') as f:
        kb_data = json.load(f)
    
    print(f"Found {len(kb_data.get('knowledge_base', []))} knowledge entries")
    
    # Prepare data for upload
    knowledge_entries = []
    for entry in kb_data.get('knowledge_base', []):
        knowledge_entries.append({
            "id": entry.get("id"),
            "question": entry.get("question"),
            "answer": entry.get("answer"),
            "category": entry.get("category"),
            "state": entry.get("state"),
            "tags": entry.get("tags", []),
            "priority": entry.get("priority", "normal"),
            "difficulty": entry.get("difficulty", "basic"),
            "personas": entry.get("personas", []),
            "source": entry.get("source", "knowledge_base")
        })
    
    # Upload to Railway
    async with aiohttp.ClientSession() as session:
        # First check health
        print("\n🔍 Checking Railway health...")
        async with session.get(f"{RAILWAY_URL}/health") as response:
            health = await response.json()
            print(f"Railway status: {health.get('status')}")
            
            if not health.get('initialized'):
                print("⚠️  System not initialized. Initializing...")
                
                # Try to initialize
                async with session.post(f"{RAILWAY_URL}/initialize") as init_response:
                    if init_response.status == 200:
                        print("✅ System initialized")
                    else:
                        print("❌ Failed to initialize")
        
        # Upload knowledge base
        print(f"\n📤 Uploading {len(knowledge_entries)} entries...")
        
        upload_data = {
            "data_type": "knowledge_base",
            "data": knowledge_entries,
            "clear_existing": True  # Clear any existing data first
        }
        
        try:
            async with session.post(
                f"{RAILWAY_URL}/upload",
                json=upload_data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Upload successful!")
                    print(f"   Records processed: {result.get('records_processed', 0)}")
                    print(f"   Status: {result.get('status')}")
                else:
                    error = await response.text()
                    print(f"❌ Upload failed: {error}")
                    
                    # Try alternative endpoint
                    print("\n🔄 Trying alternative upload method...")
                    
                    # Convert to CSV format and try file upload
                    import csv
                    import io
                    
                    csv_buffer = io.StringIO()
                    fieldnames = ['id', 'question', 'answer', 'category', 'state', 
                                'tags', 'priority', 'difficulty', 'personas', 'source']
                    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for entry in knowledge_entries:
                        # Convert lists to strings for CSV
                        entry_copy = entry.copy()
                        if isinstance(entry_copy.get('tags'), list):
                            entry_copy['tags'] = ','.join(entry_copy['tags'])
                        if isinstance(entry_copy.get('personas'), list):
                            entry_copy['personas'] = ','.join(entry_copy['personas'])
                        writer.writerow(entry_copy)
                    
                    csv_content = csv_buffer.getvalue()
                    
                    # Try file upload endpoint
                    form_data = aiohttp.FormData()
                    form_data.add_field('file',
                                      csv_content,
                                      filename='knowledge_base.csv',
                                      content_type='text/csv')
                    form_data.add_field('data_type', 'knowledge_base')
                    form_data.add_field('clear_existing', 'true')
                    
                    async with session.post(
                        f"{RAILWAY_URL}/upload-file",
                        data=form_data
                    ) as file_response:
                        if file_response.status == 200:
                            result = await file_response.json()
                            print(f"✅ File upload successful!")
                            print(f"   Records: {result.get('records_processed')}")
                        else:
                            print(f"❌ File upload also failed")
                            
        except asyncio.TimeoutError:
            print("❌ Upload timed out. The file may be too large.")
            print("   Try uploading via the web interface instead.")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test the knowledge base
    print("\n🧪 Testing knowledge retrieval...")
    async with aiohttp.ClientSession() as session:
        test_query = {
            "query": "California contractor license requirements",
            "limit": 1
        }
        
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json=test_query
        ) as response:
            if response.status == 200:
                results = await response.json()
                if results.get('results'):
                    print("✅ Knowledge base is working!")
                    print(f"   Found: {results['results'][0]['question'][:50]}...")
                else:
                    print("⚠️  No results found")
            else:
                print("❌ Search endpoint not working")

if __name__ == "__main__":
    asyncio.run(upload_knowledge_base())
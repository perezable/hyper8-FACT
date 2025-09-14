#!/usr/bin/env python3
"""
Monitor Railway deployment and upload knowledge base when ready
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from pathlib import Path

RAILWAY_URL = "https://hyper8-fact-production.up.railway.app"
MASTER_KB_FILE = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/MASTER_KNOWLEDGE_BASE_COMPLETE.json"
MAX_WAIT_TIME = 300  # 5 minutes max wait

async def check_deployment_status():
    """Check if Railway deployment is ready"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{RAILWAY_URL}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return True, data
                else:
                    return False, None
        except Exception as e:
            return False, None

async def upload_knowledge_base():
    """Upload the master knowledge base"""
    print("\n📚 Loading master knowledge base...")
    with open(MASTER_KB_FILE, 'r') as f:
        data = json.load(f)
    
    entries = data.get('knowledge_entries', [])
    print(f"✅ Loaded {len(entries)} entries")
    
    async with aiohttp.ClientSession() as session:
        chunk_size = 10
        successful = 0
        failed = 0
        
        print(f"\n📤 Starting upload of {len(entries)} entries...")
        
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i:i + chunk_size]
            chunk_num = i//chunk_size + 1
            
            # Format for upload
            chunk_data = []
            for j, entry in enumerate(chunk):
                chunk_data.append({
                    'id': entry.get('id', 50000 + i + j),
                    'question': str(entry.get('question', ''))[:500],
                    'answer': str(entry.get('answer', ''))[:1500],
                    'category': entry.get('category', 'general'),
                    'state': entry.get('state', 'ALL'),
                    'tags': entry.get('tags', ''),
                    'priority': entry.get('priority', 'medium'),
                    'difficulty': entry.get('difficulty', 'intermediate')
                })
            
            upload_data = {
                'data_type': 'knowledge_base',
                'data': chunk_data,
                'clear_existing': False  # Append mode
            }
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        successful += len(chunk)
                        if chunk_num % 5 == 0 or chunk_num == 1:
                            print(f"  ✅ Progress: {successful}/{len(entries)} uploaded")
                    else:
                        failed += len(chunk)
                        if chunk_num <= 3:
                            text = await response.text()
                            print(f"  ❌ Chunk {chunk_num} failed: {text[:100]}")
            except Exception as e:
                failed += len(chunk)
                if chunk_num <= 3:
                    print(f"  ❌ Chunk {chunk_num} error: {str(e)[:100]}")
            
            await asyncio.sleep(0.3)  # Rate limiting
        
        return successful, failed

async def main():
    print("\n" + "="*60)
    print("🚀 RAILWAY DEPLOYMENT MONITOR & KNOWLEDGE BASE UPLOADER")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n⏳ Waiting for Railway deployment to be ready...")
    print(f"   URL: {RAILWAY_URL}")
    print(f"   Max wait: {MAX_WAIT_TIME} seconds")
    
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < MAX_WAIT_TIME:
        check_count += 1
        is_ready, health_data = await check_deployment_status()
        
        if is_ready:
            print(f"\n✅ Railway deployment is ready!")
            if health_data:
                entries = health_data.get("metrics", {}).get("enhanced_retriever_entries", 0)
                print(f"   Current entries: {entries}")
            break
        
        # Show progress
        elapsed = int(time.time() - start_time)
        if check_count % 6 == 0:  # Every 30 seconds
            print(f"   ⏳ Still waiting... ({elapsed}s elapsed)")
        
        await asyncio.sleep(5)  # Check every 5 seconds
    else:
        print(f"\n❌ Deployment not ready after {MAX_WAIT_TIME} seconds")
        print("   The deployment might still be building.")
        print("   You can run this script again later to upload the knowledge base.")
        return
    
    # Upload knowledge base
    print("\n📤 Uploading knowledge base...")
    successful, failed = await upload_knowledge_base()
    
    print("\n" + "="*60)
    print("📊 UPLOAD RESULTS")
    print("="*60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if successful > 0:
        success_rate = (successful / (successful + failed)) * 100
        print(f"📈 Success rate: {success_rate:.1f}%")
        
        if success_rate == 100:
            print("\n🎉 Perfect upload! All entries successfully added!")
        elif success_rate >= 90:
            print("\n✅ Upload successful with minimal issues!")
        else:
            print("\n⚠️  Upload completed with some failures")

if __name__ == "__main__":
    asyncio.run(main())
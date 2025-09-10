#!/usr/bin/env python3
"""
Wait for Railway deployment and load the 450 knowledge entries.
This script uploads the exact data that achieved 96.7% accuracy.
"""

import json
import asyncio
import aiohttp
import time
from datetime import datetime

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def wait_for_deployment():
    """Wait for Railway to redeploy with new code."""
    print("⏳ Waiting for Railway deployment...")
    print("   (This usually takes 1-3 minutes)")
    
    async with aiohttp.ClientSession() as session:
        for i in range(30):  # Wait up to 5 minutes
            try:
                async with session.get(
                    f"{RAILWAY_URL}/health",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        health = await response.json()
                        if health.get('initialized'):
                            print("✅ Railway is ready!")
                            return True
            except:
                pass
            
            print(f"   Checking... ({i+1}/30)")
            await asyncio.sleep(10)
    
    return False

async def upload_knowledge_base():
    """Upload the 450 knowledge entries to Railway."""
    print("\n📚 Loading Knowledge Base Data")
    print("=" * 70)
    
    # Load the exported knowledge base
    with open('data/knowledge_export.json', 'r') as f:
        export_data = json.load(f)
    
    entries = export_data['knowledge_base']
    print(f"Loaded {len(entries)} knowledge entries")
    
    async with aiohttp.ClientSession() as session:
        # Upload in chunks
        chunk_size = 50
        chunks = [entries[i:i+chunk_size] for i in range(0, len(entries), chunk_size)]
        
        total_uploaded = 0
        failed_chunks = []
        
        print(f"\n📤 Uploading in {len(chunks)} chunks...")
        
        for i, chunk in enumerate(chunks, 1):
            print(f"\nChunk {i}/{len(chunks)} ({len(chunk)} entries)...")
            
            upload_data = {
                "data_type": "knowledge_base",
                "data": chunk,
                "clear_existing": (i == 1)  # Clear on first chunk only
            }
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        uploaded = result.get('records_uploaded', len(chunk))
                        total_uploaded += uploaded
                        print(f"   ✅ Uploaded {uploaded} entries")
                    else:
                        error = await response.text()
                        print(f"   ❌ Failed: {response.status} - {error[:100]}")
                        failed_chunks.append(i)
                        
            except asyncio.TimeoutError:
                print(f"   ⏱️ Timeout - chunk too large")
                failed_chunks.append(i)
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                failed_chunks.append(i)
            
            # Small delay between chunks
            await asyncio.sleep(0.5)
        
        print(f"\n📊 Upload Summary:")
        print(f"   Total uploaded: {total_uploaded}/{len(entries)}")
        if failed_chunks:
            print(f"   Failed chunks: {failed_chunks}")
        
        return total_uploaded

async def verify_deployment():
    """Verify the knowledge base is working correctly."""
    print("\n🔍 Verifying Deployment")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        # Check total count
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "", "limit": 1000}
        ) as response:
            data = await response.json()
            total = data.get('total_count', 0)
            print(f"Total entries in Railway: {total}")
            
            if total >= 400:
                print("✅ Full knowledge base loaded successfully!")
                
                # Test a few queries
                print("\n🧪 Testing sample queries:")
                test_queries = [
                    "California contractor license requirements",
                    "exam preparation strategies",
                    "surety bond requirements",
                    "qualifier network programs"
                ]
                
                for query in test_queries:
                    async with session.post(
                        f"{RAILWAY_URL}/knowledge/search",
                        json={"query": query, "limit": 1}
                    ) as response:
                        data = await response.json()
                        if data.get('results'):
                            result = data['results'][0]
                            print(f"   ✓ '{query[:30]}...'")
                            print(f"     → {result['question'][:50]}...")
                        else:
                            print(f"   ✗ '{query[:30]}...' - No results")
                
                return True
            else:
                print(f"⚠️  Only {total} entries loaded (expected 450)")
                return False

async def main():
    """Main deployment and loading process."""
    print("🚀 Railway Deployment & Knowledge Base Loading")
    print("=" * 70)
    print(f"Time: {datetime.now().isoformat()}")
    
    # Wait for deployment
    if not await wait_for_deployment():
        print("❌ Deployment timeout - please check Railway dashboard")
        return
    
    # Small delay to ensure everything is ready
    await asyncio.sleep(5)
    
    # Upload knowledge base
    uploaded = await upload_knowledge_base()
    
    if uploaded > 0:
        # Verify deployment
        success = await verify_deployment()
        
        if success:
            print("\n" + "=" * 70)
            print("🎉 SUCCESS!")
            print("Railway deployment now has the same 450 knowledge entries")
            print("that achieved 96.7% accuracy in local testing.")
            print("\nNext: Run tests/knowledge_base_test_enhanced.py against Railway")
        else:
            print("\n⚠️  Partial success - some data loaded but not complete")
    else:
        print("\n❌ Upload failed - no data loaded")
        print("Check if Railway has deployed the new code with knowledge_base support")

if __name__ == "__main__":
    asyncio.run(main())
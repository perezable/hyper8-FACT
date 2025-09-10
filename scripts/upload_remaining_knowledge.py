#!/usr/bin/env python3
"""
Upload the remaining knowledge entries to Railway.
"""

import json
import asyncio
import aiohttp

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def upload_remaining():
    """Upload remaining entries without clearing existing."""
    print("📚 Uploading Remaining Knowledge Entries")
    print("=" * 70)
    
    # Load the full knowledge base
    with open('data/knowledge_export.json', 'r') as f:
        export_data = json.load(f)
    
    all_entries = export_data['knowledge_base']
    print(f"Total entries to upload: {len(all_entries)}")
    
    async with aiohttp.ClientSession() as session:
        # Check current count
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "", "limit": 1}
        ) as response:
            data = await response.json()
            current_count = data.get('total_count', 0)
            print(f"Current entries in Railway: {current_count}")
        
        # Upload ALL entries again without clearing
        # The database should handle duplicates by ID
        chunk_size = 25  # Smaller chunks
        chunks = [all_entries[i:i+chunk_size] for i in range(0, len(all_entries), chunk_size)]
        
        print(f"\n📤 Uploading in {len(chunks)} chunks of {chunk_size} each...")
        print("   (Not clearing existing data)")
        
        total_uploaded = 0
        successful_chunks = 0
        
        for i, chunk in enumerate(chunks, 1):
            if i % 5 == 1:  # Progress every 5 chunks
                print(f"\nProgress: Chunk {i}/{len(chunks)}...")
            
            upload_data = {
                "data_type": "knowledge_base",
                "data": chunk,
                "clear_existing": False  # Never clear
            }
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        uploaded = result.get('records_uploaded', 0)
                        total_uploaded += uploaded
                        successful_chunks += 1
                        print(".", end="", flush=True)
                    else:
                        print("x", end="", flush=True)
                        
            except:
                print("!", end="", flush=True)
            
            # Tiny delay to avoid overwhelming
            await asyncio.sleep(0.1)
        
        print(f"\n\n📊 Upload Complete:")
        print(f"   Successful chunks: {successful_chunks}/{len(chunks)}")
        print(f"   Records processed: {total_uploaded}")
        
        # Check final count
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "", "limit": 1}
        ) as response:
            data = await response.json()
            final_count = data.get('total_count', 0)
            print(f"   Final entries in Railway: {final_count}")
            
            if final_count >= 400:
                print("\n✅ SUCCESS! Full knowledge base loaded!")
            elif final_count > current_count:
                print(f"\n⚠️  Partial improvement: {current_count} → {final_count}")
            else:
                print(f"\n❌ No improvement: still {final_count} entries")

if __name__ == "__main__":
    asyncio.run(upload_remaining())
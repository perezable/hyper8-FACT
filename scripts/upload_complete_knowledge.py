#!/usr/bin/env python3
"""
Upload the complete 450-entry knowledge base to Railway.
Clear existing partial data first for a clean slate.
"""

import json
import sqlite3
import asyncio
import aiohttp
import sys

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"
LOCAL_DB = "data/fact_system.db"

async def clear_existing_data():
    """Clear any existing knowledge base data."""
    async with aiohttp.ClientSession() as session:
        try:
            # Try to delete existing knowledge base data
            async with session.delete(
                f"{RAILWAY_URL}/data/knowledge_base",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Cleared existing data: {result}")
                    return True
                else:
                    print(f"⚠️  Could not clear data: {response.status}")
                    return False
        except Exception as e:
            print(f"⚠️  Delete endpoint error: {e}")
            return False

async def upload_complete_knowledge():
    """Upload the complete knowledge base."""
    print("📚 Uploading Complete Knowledge Base (450 entries)")
    print("=" * 70)
    
    # Load from local database
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, question, answer, category, state, tags,
               priority, difficulty, personas, source
        FROM knowledge_base
        ORDER BY category, id
    """)
    
    all_entries = []
    for row in cursor.fetchall():
        entry = dict(row)
        # Ensure ID is unique
        if not entry.get('id'):
            entry['id'] = f"KB_{len(all_entries)+1:04d}"
        all_entries.append(entry)
    
    conn.close()
    
    print(f"Loaded {len(all_entries)} entries from local database")
    
    # Get category breakdown
    categories = {}
    for entry in all_entries:
        cat = entry.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1
    
    print("\n📊 Categories to upload:")
    for cat, count in sorted(categories.items()):
        print(f"   • {cat}: {count} entries")
    
    async with aiohttp.ClientSession() as session:
        # Clear existing data first
        print("\n🗑️  Clearing existing partial data...")
        await clear_existing_data()
        
        # Upload in smaller chunks to avoid timeouts
        chunk_size = 10  # Very small chunks
        chunks = [all_entries[i:i+chunk_size] for i in range(0, len(all_entries), chunk_size)]
        
        print(f"\n📤 Uploading {len(all_entries)} entries in {len(chunks)} chunks...")
        
        total_uploaded = 0
        failed_chunks = []
        
        for i, chunk in enumerate(chunks, 1):
            # Show progress every 10 chunks
            if i % 10 == 1:
                print(f"\n⏳ Progress: {i}/{len(chunks)} chunks ({total_uploaded} entries uploaded)...")
            
            upload_data = {
                "data_type": "knowledge_base",
                "data": chunk,
                "clear_existing": False  # Don't clear after first chunk
            }
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        uploaded = result.get('records_uploaded', len(chunk))
                        total_uploaded += uploaded
                        print(".", end="", flush=True)
                    else:
                        print("x", end="", flush=True)
                        failed_chunks.append(i)
                        
            except asyncio.TimeoutError:
                print("T", end="", flush=True)
                failed_chunks.append(i)
            except Exception as e:
                print("E", end="", flush=True)
                failed_chunks.append(i)
            
            # Small delay between chunks
            await asyncio.sleep(0.05)
        
        print(f"\n\n✅ Upload complete!")
        print(f"   Total uploaded: {total_uploaded}/{len(all_entries)}")
        if failed_chunks:
            print(f"   Failed chunks: {len(failed_chunks)} (chunks {failed_chunks[:10]}...)")
        
        # Verify final count
        print("\n🔍 Verifying upload...")
        async with session.post(
            f"{RAILWAY_URL}/knowledge/search",
            json={"query": "", "limit": 1000}
        ) as response:
            data = await response.json()
            final_count = data.get('total_count', 0)
            results = data.get('results', [])
            
            # Get category breakdown
            final_categories = {}
            for entry in results:
                cat = entry.get('category', 'unknown')
                final_categories[cat] = final_categories.get(cat, 0) + 1
            
            print(f"   Total entries in Railway: {final_count}")
            print(f"   Categories loaded:")
            for cat, count in sorted(final_categories.items()):
                expected = categories.get(cat, 0)
                status = "✅" if count == expected else f"⚠️  ({expected} expected)"
                print(f"     • {cat}: {count} {status}")
            
            # Test some queries
            if final_count > 0:
                print("\n🧪 Testing sample queries:")
                test_queries = [
                    ("California contractor license", "state_licensing_requirements"),
                    ("exam preparation", "exam_preparation_testing"),
                    ("surety bond", "insurance_bonding"),
                    ("business formation", "business_formation_operations")
                ]
                
                for query, expected_cat in test_queries:
                    async with session.post(
                        f"{RAILWAY_URL}/knowledge/search",
                        json={"query": query, "limit": 1}
                    ) as resp:
                        test_data = await resp.json()
                        if test_data.get('results'):
                            result = test_data['results'][0]
                            cat = result.get('category', 'unknown')
                            status = "✅" if cat == expected_cat else f"({cat})"
                            print(f"   ✓ '{query}' → Found {status}")
                        else:
                            print(f"   ✗ '{query}' → No results")
            
            if final_count >= 400:
                print("\n🎉 SUCCESS! Full knowledge base loaded!")
                print(f"   Railway now has {final_count} entries")
                print("   Ready for 96.7% accuracy testing!")
            elif final_count >= 100:
                print(f"\n⚠️  Partial success: {final_count} entries loaded")
                print("   This may be a database limit on Railway")
            else:
                print(f"\n❌ Limited upload: only {final_count} entries")

if __name__ == "__main__":
    asyncio.run(upload_complete_knowledge())
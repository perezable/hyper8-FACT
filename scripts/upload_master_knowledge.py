#!/usr/bin/env python3
"""
Upload MASTER knowledge base to Railway (292 entries)
APPEND mode - will NOT delete existing records
"""

import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"
MASTER_KB_FILE = "/Users/natperez/codebases/hyper8/hyper8-FACT/data/MASTER_KNOWLEDGE_BASE_COMPLETE.json"

async def check_current_count():
    """Check current number of entries in Railway"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{RAILWAY_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    count = data.get("metrics", {}).get("enhanced_retriever_entries", 0)
                    logger.info(f"📊 Current entries in Railway: {count}")
                    return count
                else:
                    logger.warning(f"Health check returned status {response.status}")
                    return None
        except Exception as e:
            logger.error(f"❌ Error checking count: {str(e)}")
            return None

async def upload_entries(entries):
    """Upload entries to Railway WITHOUT clearing existing"""
    async with aiohttp.ClientSession() as session:
        logger.info(f"📤 Uploading {len(entries)} entries to Railway...")
        logger.info("⚠️  APPEND MODE - Existing records will NOT be deleted")
        
        chunk_size = 10
        successful = 0
        failed = 0
        errors = []
        
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i:i + chunk_size]
            chunk_num = i//chunk_size + 1
            
            # Convert to upload format
            chunk_data = []
            for entry in chunk:
                # Ensure all required fields are present
                chunk_data.append({
                    'id': entry.get('id', 50000 + i),
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
                'clear_existing': False  # CRITICAL: Do NOT clear existing
            }
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        successful += len(chunk)
                        if chunk_num % 5 == 0 or chunk_num == 1:
                            logger.info(f"✅ Progress: {successful}/{len(entries)} entries uploaded")
                    else:
                        failed += len(chunk)
                        text = await response.text()
                        error_msg = f"Chunk {chunk_num} failed with status {response.status}"
                        errors.append(error_msg)
                        if chunk_num <= 3:
                            logger.error(f"❌ {error_msg}: {text[:200]}")
            except asyncio.TimeoutError:
                failed += len(chunk)
                error_msg = f"Chunk {chunk_num} timed out"
                errors.append(error_msg)
                logger.error(f"⏱️ {error_msg}")
            except Exception as e:
                failed += len(chunk)
                error_msg = f"Chunk {chunk_num} error: {str(e)[:100]}"
                errors.append(error_msg)
                if chunk_num <= 3:
                    logger.error(f"❌ {error_msg}")
            
            # Rate limiting
            await asyncio.sleep(0.3)
            
            # Progress indicator
            if chunk_num % 10 == 0:
                logger.info(f"📊 Progress: {chunk_num * chunk_size}/{len(entries)} processed")
        
        return successful, failed, errors

async def verify_upload(expected_increase):
    """Verify the upload was successful"""
    await asyncio.sleep(3)  # Wait for database to update
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{RAILWAY_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    count = data.get("metrics", {}).get("enhanced_retriever_entries", 0)
                    logger.info(f"📊 Final entry count: {count}")
                    return count
        except Exception as e:
            logger.error(f"❌ Error verifying: {str(e)}")
            return None

async def main():
    print("\n" + "="*60)
    print("🚀 UPLOADING MASTER KNOWLEDGE BASE TO RAILWAY")
    print("⚠️  APPEND MODE - EXISTING RECORDS WILL BE PRESERVED")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load the master knowledge base
    print(f"\n📖 Loading master knowledge base...")
    try:
        with open(MASTER_KB_FILE, 'r') as f:
            data = json.load(f)
        
        entries = data.get('knowledge_entries', [])
        metadata = data.get('metadata', {})
        
        print(f"✅ Loaded {len(entries)} entries from master knowledge base")
        print(f"   Average quality score: {metadata.get('total_entries', 0)}")
        print(f"   Sources merged: {metadata.get('sources_processed', 0)}")
    except Exception as e:
        print(f"❌ Error loading master file: {e}")
        return
    
    # Check current count
    print("\n📊 Checking current Railway status...")
    current_count = await check_current_count()
    
    if current_count is None:
        print("⚠️  Could not verify current count, but will proceed with upload")
        current_count = "Unknown"
    
    # Confirm before upload
    print(f"\n📤 Ready to upload:")
    print(f"   Current entries in Railway: {current_count}")
    print(f"   New entries to add: {len(entries)}")
    if isinstance(current_count, int):
        print(f"   Expected total after upload: {current_count + len(entries)}")
    
    # Upload entries
    print(f"\n🚀 Starting upload...")
    successful, failed, errors = await upload_entries(entries)
    
    # Display results
    print(f"\n📊 Upload Results:")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    
    if errors and len(errors) <= 10:
        print(f"\n❌ Errors encountered:")
        for error in errors[:10]:
            print(f"   - {error}")
    elif errors:
        print(f"\n❌ {len(errors)} errors encountered (showing first 10)")
        for error in errors[:10]:
            print(f"   - {error}")
    
    # Verify final count
    print("\n📊 Verifying upload...")
    final_count = await verify_upload(successful)
    
    print("\n" + "="*60)
    print("✅ UPLOAD COMPLETE")
    print("="*60)
    
    if isinstance(current_count, int) and isinstance(final_count, int):
        print(f"Initial entries: {current_count}")
        print(f"Added entries: {successful}")
        print(f"Final entries: {final_count}")
        print(f"Net increase: {final_count - current_count}")
        
        if final_count - current_count == successful:
            print("\n🎉 Perfect upload! All entries successfully added!")
        elif final_count > current_count:
            print("\n✅ Upload successful with some entries added!")
        else:
            print("\n⚠️  Upload completed but verification shows unexpected count")
    else:
        print(f"Added entries: {successful}")
        print(f"Failed entries: {failed}")
        if successful > 0:
            print("\n✅ Upload completed successfully!")
    
    # Success rate
    if successful + failed > 0:
        success_rate = (successful / (successful + failed)) * 100
        print(f"\n📈 Success rate: {success_rate:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
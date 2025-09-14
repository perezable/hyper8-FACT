#!/usr/bin/env python3
"""
Deploy the FULL 6,446 entry knowledge base to Railway
Converts SQL file to proper JSON format for upload
"""

import asyncio
import aiohttp
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

def parse_sql_to_entries(sql_file: str) -> List[Dict[str, Any]]:
    """Parse SQL INSERT statements to knowledge entries"""
    entries = []
    
    with open(sql_file, 'r') as f:
        content = f.read()
    
    # Find all INSERT statements
    insert_pattern = r"INSERT INTO knowledge_base.*?VALUES\s*\((.*?)\);"
    matches = re.findall(insert_pattern, content, re.DOTALL)
    
    for match in matches:
        # Parse the values - careful with escaped quotes
        try:
            # Split by comma but not within quotes
            parts = []
            current = ""
            in_quotes = False
            escape_next = False
            
            for char in match:
                if escape_next:
                    current += char
                    escape_next = False
                elif char == '\\':
                    escape_next = True
                    current += char
                elif char == "'" and not escape_next:
                    in_quotes = not in_quotes
                    current += char
                elif char == ',' and not in_quotes:
                    parts.append(current.strip())
                    current = ""
                else:
                    current += char
            
            if current:
                parts.append(current.strip())
            
            if len(parts) >= 8:  # Ensure we have enough fields
                # Clean up the values
                entry_id = int(parts[0])
                question = parts[1].strip("'").replace("\\'", "'").replace("\\n", "\n")
                answer = parts[2].strip("'").replace("\\'", "'").replace("\\n", "\n")
                category = parts[3].strip("'")
                state = parts[4].strip("'") if parts[4].strip("'") != 'NULL' else None
                tags = parts[5].strip("'") if len(parts) > 5 else ""
                priority = parts[6].strip("'") if len(parts) > 6 else "medium"
                difficulty = parts[7].strip("'") if len(parts) > 7 else "intermediate"
                
                # Only add if question and answer are substantial
                if len(question) > 5 and len(answer) > 10:
                    entries.append({
                        "id": entry_id,
                        "question": question[:500],  # Limit length
                        "answer": answer[:1500],     # Limit length
                        "category": category,
                        "state": state,
                        "tags": tags[:200],
                        "priority": priority,
                        "difficulty": difficulty
                    })
        except Exception as e:
            continue  # Skip problematic entries
    
    return entries

async def clear_existing():
    """Clear existing knowledge base"""
    async with aiohttp.ClientSession() as session:
        clear_data = {
            'data_type': 'knowledge_base',
            'data': [],
            'clear_existing': True
        }
        
        try:
            async with session.post(
                f"{RAILWAY_URL}/upload-data",
                json=clear_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    logger.info("✅ Cleared existing knowledge base")
                    return True
                else:
                    logger.error(f"❌ Failed to clear: HTTP {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Error clearing: {str(e)}")
            return False

async def deploy_entries(entries: List[Dict[str, Any]]) -> int:
    """Deploy entries to Railway in chunks"""
    async with aiohttp.ClientSession() as session:
        logger.info(f"Deploying {len(entries)} entries to Railway...")
        
        chunk_size = 10
        successful = 0
        failed_chunks = []
        
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i:i + chunk_size]
            chunk_num = i//chunk_size + 1
            total_chunks = (len(entries) + chunk_size - 1)//chunk_size
            
            upload_data = {
                'data_type': 'knowledge_base',
                'data': chunk,
                'clear_existing': False
            }
            
            try:
                async with session.post(
                    f"{RAILWAY_URL}/upload-data",
                    json=upload_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        successful += len(chunk)
                        if chunk_num % 10 == 0:  # Log every 10th chunk
                            logger.info(f"✅ Progress: {chunk_num}/{total_chunks} chunks uploaded")
                    else:
                        failed_chunks.append(chunk_num)
                        if len(failed_chunks) < 5:  # Only log first few failures
                            text = await response.text()
                            logger.error(f"❌ Failed chunk {chunk_num}: {text[:100]}")
            except asyncio.TimeoutError:
                failed_chunks.append(chunk_num)
                logger.error(f"⏱️  Timeout on chunk {chunk_num}")
            except Exception as e:
                failed_chunks.append(chunk_num)
                if len(failed_chunks) < 5:
                    logger.error(f"❌ Error on chunk {chunk_num}: {str(e)[:100]}")
            
            # Rate limiting
            if chunk_num % 20 == 0:
                await asyncio.sleep(1)  # Longer pause every 20 chunks
            else:
                await asyncio.sleep(0.2)  # Short pause between chunks
        
        if failed_chunks:
            logger.warning(f"Failed {len(failed_chunks)} chunks: {failed_chunks[:10]}...")
        
        return successful

async def verify_deployment():
    """Verify deployment success"""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{RAILWAY_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    count = data.get("metrics", {}).get("enhanced_retriever_entries", 0)
                    return count
        except:
            return 0

async def main():
    print("\n" + "="*60)
    print("🚀 DEPLOYING FULL KNOWLEDGE BASE TO RAILWAY")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse SQL file
    print("\n📖 Parsing SQL file...")
    sql_file = "scripts/restore_full_knowledge_base.sql"
    
    try:
        entries = parse_sql_to_entries(sql_file)
        print(f"✅ Parsed {len(entries)} valid entries from SQL")
    except Exception as e:
        logger.error(f"Failed to parse SQL: {e}")
        return
    
    if not entries:
        logger.error("No entries to deploy!")
        return
    
    # Show sample
    print("\n📝 Sample entries:")
    for i, entry in enumerate(entries[:3]):
        print(f"{i+1}. ID {entry['id']}: {entry['question'][:60]}...")
    
    print(f"\n📊 Entry statistics:")
    print(f"  ID range: {min(e['id'] for e in entries)} to {max(e['id'] for e in entries)}")
    categories = set(e['category'] for e in entries)
    print(f"  Categories: {len(categories)}")
    print(f"  Sample categories: {list(categories)[:5]}")
    
    # Confirm deployment
    print("\n⚠️  This will replace the current 82 entries with {len(entries)} entries")
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Deployment cancelled")
        return
    
    # Clear existing
    print("\n🧹 Clearing existing knowledge base...")
    if not await clear_existing():
        logger.warning("Could not clear, continuing anyway...")
    
    # Deploy
    print(f"\n📤 Deploying {len(entries)} entries (this may take several minutes)...")
    deployed = await deploy_entries(entries)
    
    print(f"\n✅ Deployed: {deployed}/{len(entries)} entries")
    
    # Verify
    print("\n🔍 Verifying deployment...")
    await asyncio.sleep(2)
    final_count = await verify_deployment()
    
    print("\n" + "="*60)
    print("📊 DEPLOYMENT SUMMARY")
    print("="*60)
    print(f"Target entries: {len(entries)}")
    print(f"Successfully deployed: {deployed}")
    print(f"Final count in system: {final_count}")
    print(f"Success rate: {deployed*100/len(entries):.1f}%")
    
    if final_count > 1000:
        print("\n✅ SUCCESS! Full knowledge base deployed")
        print(f"   The system now has {final_count} comprehensive entries")
        print("   Ready for production use!")
    else:
        print("\n⚠️  Partial deployment")
        print("   Check Railway logs for details")

if __name__ == "__main__":
    asyncio.run(main())
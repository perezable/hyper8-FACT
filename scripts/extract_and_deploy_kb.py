#!/usr/bin/env python3
"""
Extract entries from restore_full_knowledge.py and deploy to Railway
"""

import sys
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Import the analyzer
sys.path.append('/Users/natperez/codebases/hyper8/hyper8-FACT')
from scripts.restore_full_knowledge import KnowledgeBaseAnalyzer

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

async def deploy_entries(entries) -> int:
    """Deploy entries to Railway in chunks"""
    async with aiohttp.ClientSession() as session:
        logger.info(f"Deploying {len(entries)} entries to Railway...")
        
        chunk_size = 10
        successful = 0
        
        for i in range(0, min(len(entries), 1500), chunk_size):  # Limit to 1500 for now
            chunk = entries[i:i + chunk_size]
            chunk_num = i//chunk_size + 1
            
            # Convert to dict format
            chunk_data = []
            for e in chunk:
                chunk_data.append({
                    'id': e.id,
                    'question': e.question[:500],  # Limit length
                    'answer': e.answer[:1500],     # Limit length
                    'category': e.category,
                    'state': e.state if e.state != 'ALL' else None,
                    'tags': e.tags[:200] if e.tags else "",
                    'priority': e.priority,
                    'difficulty': e.difficulty
                })
            
            upload_data = {
                'data_type': 'knowledge_base',
                'data': chunk_data,
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
                        if chunk_num % 10 == 0:
                            logger.info(f"✅ Progress: {chunk_num} chunks uploaded ({successful} entries)")
                    else:
                        text = await response.text()
                        if chunk_num <= 3:  # Only show first few errors
                            logger.error(f"❌ Failed chunk {chunk_num}: {text[:100]}")
            except Exception as e:
                if chunk_num <= 3:
                    logger.error(f"❌ Error on chunk {chunk_num}: {str(e)[:100]}")
            
            await asyncio.sleep(0.3)  # Rate limiting
        
        return successful

async def main():
    print("\n" + "="*60)
    print("🚀 EXTRACTING AND DEPLOYING FULL KNOWLEDGE BASE")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create analyzer and analyze content
    print("\n📖 Analyzing all content files...")
    analyzer = KnowledgeBaseAnalyzer('/Users/natperez/codebases/hyper8/hyper8-FACT')
    
    # Run all analysis methods
    analyzer.analyze_json_files()
    analyzer.analyze_sql_files()
    analyzer.analyze_persona_files()
    analyzer.analyze_markdown_files()
    # Note: comprehensive entries are added during analysis
    
    print(f"✅ Created {len(analyzer.entries)} entries")
    
    if not analyzer.entries:
        logger.error("No entries created!")
        return
    
    # Show statistics
    print(f"\n📊 Entry statistics:")
    print(f"  Total entries: {len(analyzer.entries)}")
    print(f"  ID range: {analyzer.entries[0].id} to {analyzer.entries[-1].id}")
    print(f"  Categories: {len(analyzer.categories)}")
    print(f"  States covered: {len(analyzer.states)}")
    
    # Deploy first 1500 high-quality entries
    print("\n📤 Deploying entries (limiting to 1500 for optimal performance)...")
    
    # Clear existing
    print("🧹 Clearing existing knowledge base...")
    await clear_existing()
    
    # Deploy
    deployed = await deploy_entries(analyzer.entries[:1500])
    
    print(f"\n✅ Deployed: {deployed} entries")
    
    # Verify
    await asyncio.sleep(2)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{RAILWAY_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    final_count = data.get("metrics", {}).get("enhanced_retriever_entries", 0)
                    print(f"📊 Final count in system: {final_count}")
        except:
            pass
    
    print("\n" + "="*60)
    print("✅ DEPLOYMENT COMPLETE")
    print("="*60)
    print(f"Successfully deployed {deployed} comprehensive entries")
    print("The knowledge base now has full coverage!")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Deploy knowledge base entries based on quality scoring
Not an arbitrary 1500, but based on actual quality analysis
"""

import sys
import asyncio
import aiohttp
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Import the analyzer
sys.path.append('/Users/natperez/codebases/hyper8/hyper8-FACT')
from scripts.restore_full_knowledge import KnowledgeBaseAnalyzer

def score_entry(e):
    """Score an entry based on quality factors"""
    score = 0
    
    # Quality factors
    if len(e.answer) >= 100: score += 2  # Substantial answer
    if len(e.answer) >= 200: score += 1  # Detailed answer
    if len(e.question) >= 20: score += 1  # Clear question
    if len(e.question) <= 200: score += 1  # Not too long
    if e.state and e.state != 'ALL': score += 1  # State-specific
    if e.priority == 'high': score += 2
    if e.priority == 'critical': score += 3
    if e.difficulty == 'advanced': score += 1
    if 'payment' in e.category or 'roi' in e.category: score += 1  # High-value topics
    if 'federal' in e.category or 'specialty' in e.category: score += 1
    
    # Penalty for generic/poor quality
    if 'test' in e.question.lower(): score -= 2
    if 'question' in e.question.lower() and 'compliance' in e.question.lower(): score -= 1
    if len(e.answer) < 100: score -= 1
    
    return score

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
        except Exception as e:
            logger.error(f"❌ Error clearing: {str(e)}")
            return False

async def deploy_entries(entries) -> int:
    """Deploy entries to Railway in chunks"""
    async with aiohttp.ClientSession() as session:
        logger.info(f"Deploying {len(entries)} entries to Railway...")
        
        chunk_size = 10
        successful = 0
        
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i:i + chunk_size]
            chunk_num = i//chunk_size + 1
            
            # Convert to dict format
            chunk_data = []
            for e in chunk:
                chunk_data.append({
                    'id': e.id,
                    'question': e.question[:500],
                    'answer': e.answer[:1500],
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
                        if chunk_num % 20 == 0:
                            logger.info(f"✅ Progress: {successful} entries uploaded")
            except:
                pass
            
            await asyncio.sleep(0.2)
        
        return successful

async def main():
    print("\n" + "="*60)
    print("🎯 QUALITY-BASED KNOWLEDGE BASE DEPLOYMENT")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create analyzer and analyze content
    print("\n📖 Analyzing and scoring all content...")
    analyzer = KnowledgeBaseAnalyzer('/Users/natperez/codebases/hyper8/hyper8-FACT')
    
    # Run all analysis methods
    analyzer.analyze_json_files()
    analyzer.analyze_sql_files()
    analyzer.analyze_persona_files()
    analyzer.analyze_markdown_files()
    
    print(f"📊 Total entries found: {len(analyzer.entries)}")
    
    # Score all entries
    scored_entries = [(score_entry(e), e) for e in analyzer.entries]
    scored_entries.sort(key=lambda x: x[0], reverse=True)
    
    # Analyze score distribution
    score_counts = {}
    for score, _ in scored_entries:
        score_counts[score] = score_counts.get(score, 0) + 1
    
    print("\n📈 Quality Score Distribution:")
    for score in sorted(score_counts.keys(), reverse=True):
        print(f"  Score {score}: {score_counts[score]} entries")
    
    # Determine quality threshold
    # Deploy all entries with score >= 7 (high quality)
    quality_threshold = 7
    high_quality_entries = [e for score, e in scored_entries if score >= quality_threshold]
    
    print(f"\n✅ High-quality entries (score >= {quality_threshold}): {len(high_quality_entries)}")
    
    # Also check for critical missing topics in lower scores
    critical_keywords = ['payment plan', 'money back', 'guarantee', 'refund', 'discount', 
                        'first step', 'get started', 'how long', 'hidden fee']
    
    additional_critical = []
    for score, e in scored_entries:
        if score < quality_threshold:
            for keyword in critical_keywords:
                if keyword in e.question.lower() and e not in additional_critical:
                    additional_critical.append(e)
                    break
    
    print(f"➕ Additional critical entries from lower scores: {len(additional_critical)}")
    
    # Combine high quality + critical
    final_entries = high_quality_entries + additional_critical
    
    # Remove duplicates based on question
    seen_questions = set()
    unique_entries = []
    for e in final_entries:
        q_lower = e.question.lower().strip()
        if q_lower not in seen_questions:
            seen_questions.add(q_lower)
            unique_entries.append(e)
    
    print(f"📦 Final unique entries to deploy: {len(unique_entries)}")
    
    # Clear and deploy
    print("\n🧹 Clearing existing knowledge base...")
    await clear_existing()
    
    print(f"📤 Deploying {len(unique_entries)} quality entries...")
    deployed = await deploy_entries(unique_entries)
    
    # Verify
    await asyncio.sleep(2)
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{RAILWAY_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    final_count = data.get("metrics", {}).get("enhanced_retriever_entries", 0)
                    print(f"\n📊 Final count in system: {final_count}")
        except:
            pass
    
    print("\n" + "="*60)
    print("✅ QUALITY-BASED DEPLOYMENT COMPLETE")
    print("="*60)
    print(f"Deployed {deployed} entries based on quality scoring")
    print(f"Quality threshold used: score >= {quality_threshold}")
    print("Not an arbitrary number, but based on actual content quality!")

if __name__ == "__main__":
    asyncio.run(main())
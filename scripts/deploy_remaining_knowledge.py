#!/usr/bin/env python3
"""
Deploy remaining knowledge entries to Railway using the same method I used earlier
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

def get_remaining_entries() -> List[Dict[str, Any]]:
    """Get all remaining knowledge entries to deploy."""
    entries = []
    
    # High-priority states entries
    state_entries = [
        # New York
        {
            "question": "New York contractor license requirements",
            "answer": "New York requires: General contractor license through local municipalities. NYC has specific requirements: $25,000-$50,000 insurance, business license, tax ID. State doesn't have unified licensing but most cities require: 2+ years experience, insurance, exam passage. Timeline: 2-8 weeks depending on locality.",
            "category": "state_requirements",
            "state": "NY",
            "tags": "new_york,requirements,nyc,insurance,experience",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "question": "New York contractor license cost",
            "answer": "New York costs vary by locality: NYC: $200-400 application, $25,000-50,000 insurance ($2,000-5,000/year), business license $100-300. Total initial investment: $5,500-13,550. Timeline affects cost - expedited processing available.",
            "category": "costs",
            "state": "NY",
            "tags": "new_york,costs,nyc,insurance,fees",
            "priority": "high",
            "difficulty": "basic"
        },
        # Illinois
        {
            "question": "Illinois contractor license requirements",
            "answer": "Illinois has limited state licensing - only for roofing and plumbing. Chicago requires: General Contractor License for projects over $10,000, 3 classifications based on project size, exam required, insurance requirements vary by class.",
            "category": "state_requirements",
            "state": "IL",
            "tags": "illinois,chicago,requirements,classifications,exam",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "question": "Illinois contractor license cost Chicago",
            "answer": "Chicago contractor licensing costs: Limited License: $250 application, $5,000 bond. Unlimited License: $500 application, $10,000 bond. Insurance: $1,500-4,000/year. Total initial: $2,575-15,075 depending on classification.",
            "category": "costs",
            "state": "IL",
            "tags": "illinois,chicago,costs,bond,insurance",
            "priority": "high",
            "difficulty": "basic"
        },
        # Pennsylvania
        {
            "question": "Pennsylvania contractor license requirements",
            "answer": "Pennsylvania has minimal requirements - one of the easiest states! Home Improvement Contractor (HIC) registration required for residential work over $5,000. Requirements: $50 registration fee, liability insurance, no exam required, no experience requirement.",
            "category": "state_requirements",
            "state": "PA",
            "tags": "pennsylvania,hic,easy,no_exam,registration",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "question": "Pennsylvania contractor license cost",
            "answer": "Pennsylvania is one of the most affordable states: HIC registration: $50, liability insurance: $500-2,000/year, no bond required, no exam fees. Total initial cost: $600-2,550. Extremely fast approval.",
            "category": "costs",
            "state": "PA",
            "tags": "pennsylvania,affordable,costs,hic,low_barrier",
            "priority": "high",
            "difficulty": "basic"
        },
        # Ohio
        {
            "question": "Ohio contractor license requirements",
            "answer": "Ohio requires state licenses for specialty trades (electrical, plumbing, HVAC) but not general contractors. Specialty requirements: Pass state exam, prove 5 years experience, business liability insurance.",
            "category": "state_requirements",
            "state": "OH",
            "tags": "ohio,specialty,electrical,plumbing,hvac,experience",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "question": "Ohio contractor license cost",
            "answer": "Ohio licensing costs: State specialty license: $100 application, $50 exam fee. Insurance: $1,000-3,000/year. Bond varies by locality. Total initial: $1,500-5,000 depending on trade and location.",
            "category": "costs",
            "state": "OH",
            "tags": "ohio,costs,specialty,insurance,exam",
            "priority": "high",
            "difficulty": "basic"
        },
        # Michigan
        {
            "question": "Michigan contractor license requirements",
            "answer": "Michigan requires state licenses for residential builders. Requirements: 60 hours pre-licensure education, pass state exam, 2 years experience OR 1 year + education, liability insurance.",
            "category": "state_requirements",
            "state": "MI",
            "tags": "michigan,education,exam,residential,builders",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "question": "Michigan contractor license cost",
            "answer": "Michigan licensing costs: Education: $600-1,200, Application: $195, Exam: $75, Insurance: $1,000-3,000/year. Total initial investment: $2,000-4,500. Timeline: 6-8 weeks including education.",
            "category": "costs",
            "state": "MI",
            "tags": "michigan,costs,education,exam,insurance",
            "priority": "high",
            "difficulty": "basic"
        }
    ]
    
    # ROI entries
    roi_entries = [
        {
            "question": "ROI calculation contractor license investment $30,000 income",
            "answer": "Starting at $30,000 annual income, licensing ROI is exceptional: Licensed income potential $60,000-$90,000 (100-200% increase). Investment: $4,995 program + $1,000 fees = $5,995 total. First year gain: $30,000-$60,000. ROI: 500-1,000% first year.",
            "category": "roi_analysis",
            "state": None,
            "tags": "roi,income_30k,investment,payback,qualifier",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "question": "Commercial contractor ROI qualifier network income",
            "answer": "Qualifier network provides exceptional passive income: Loan your license to 3-5 contractors, earn $1,000-$2,000 per contractor monthly. Total: $3,000-$10,000 monthly passive income ($36,000-$120,000 annually).",
            "category": "roi_analysis",
            "state": None,
            "tags": "qualifier_network,passive_income,commercial,hourly_rate",
            "priority": "high",
            "difficulty": "advanced"
        },
        {
            "question": "Geographic arbitrage contractor licensing opportunities",
            "answer": "Geographic arbitrage creates massive opportunities: Rural to urban move: 35-80% income increase. State-to-state: FL to NY (+40%), TX to CA (+35%). Investment: Additional state licenses $2,000-5,000. ROI: 1,300-3,200% first year.",
            "category": "roi_analysis",
            "state": None,
            "tags": "geographic_arbitrage,multi_state,income_increase",
            "priority": "high",
            "difficulty": "advanced"
        }
    ]
    
    # Case studies
    case_studies = [
        {
            "question": "John Tampa roofing contractor success story income increase",
            "answer": "John, Tampa roofing contractor, transformed his business: Started at $45,000/year unlicensed. Got Florida CBC license in 6 weeks. First commercial job: $85,000. Year 1: $125,000 (178% increase). Added qualifier income: $4,000/month. Total year 2: $233,000.",
            "category": "success_stories",
            "state": "FL",
            "tags": "case_study,roofing,tampa,commercial,qualifier",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "question": "Sarah Georgia Florida expansion doubled income success",
            "answer": "Sarah, Atlanta-based remodeler: Georgia income plateaued at $72,000. Added Florida license. Combined market income: $145,000 year 1. Year 2: $198,000. Added qualifier network: $5,000/month. Total: $258,000 (258% increase).",
            "category": "success_stories",
            "state": "GA",
            "tags": "case_study,expansion,multi_state,georgia,florida",
            "priority": "high",
            "difficulty": "basic"
        }
    ]
    
    entries.extend(state_entries)
    entries.extend(roi_entries)
    entries.extend(case_studies)
    
    return entries

async def check_health():
    """Check system health and entry count."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{RAILWAY_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("metrics", {}).get("enhanced_retriever_entries", 0)
        except:
            return 0

async def deploy_entries(entries: List[Dict[str, Any]]) -> int:
    """Deploy entries to Railway using upload-data endpoint."""
    async with aiohttp.ClientSession() as session:
        logger.info(f"Deploying {len(entries)} entries to Railway...")
        
        # Upload in chunks
        chunk_size = 10
        successful_uploads = 0
        
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i:i + chunk_size]
            
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
                        successful_uploads += len(chunk)
                        logger.info(f"✅ Uploaded chunk {i//chunk_size + 1}/{(len(entries) + chunk_size - 1)//chunk_size}")
                    else:
                        logger.error(f"❌ Failed chunk {i//chunk_size + 1}: HTTP {response.status}")
                        # Try to get error message
                        try:
                            error_text = await response.text()
                            logger.error(f"   Error: {error_text[:200]}")
                        except:
                            pass
            except asyncio.TimeoutError:
                logger.error(f"⏱️  Timeout on chunk {i//chunk_size + 1}")
            except Exception as e:
                logger.error(f"❌ Error on chunk {i//chunk_size + 1}: {str(e)}")
            
            # Small delay between chunks
            await asyncio.sleep(0.5)
        
        return successful_uploads

async def main():
    """Main deployment function."""
    print("\n" + "=" * 60)
    print("🚀 DEPLOYING REMAINING KNOWLEDGE TO RAILWAY")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check starting count
    start_count = await check_health()
    print(f"\n📊 Current Railway entries: {start_count}")
    
    # Get entries to deploy
    entries = get_remaining_entries()
    print(f"📦 Entries to deploy: {len(entries)}")
    
    # Deploy entries
    deployed = await deploy_entries(entries)
    
    # Check final count
    await asyncio.sleep(2)
    end_count = await check_health()
    
    print("\n" + "=" * 60)
    print("📊 DEPLOYMENT SUMMARY")
    print("=" * 60)
    print(f"Starting entries: {start_count}")
    print(f"Deployed: {deployed}/{len(entries)}")
    print(f"Current total: {end_count}")
    print(f"Change: {end_count - start_count}")
    
    if end_count > start_count:
        print("\n✅ SUCCESS! Knowledge base updated")
        print(f"   Added {end_count - start_count} new entries")
    else:
        print("\n⚠️  No change detected")
        print("   Entries may be duplicates or endpoint may not be working")
    
    print("\n📋 Categories deployed:")
    print("  • State requirements (NY, IL, PA, OH, MI)")
    print("  • Cost breakdowns")
    print("  • ROI analysis")
    print("  • Success stories")

if __name__ == "__main__":
    asyncio.run(main())
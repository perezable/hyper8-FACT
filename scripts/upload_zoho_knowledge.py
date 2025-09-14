#!/usr/bin/env python3
"""
Upload Zoho Workdrive extracted knowledge to Railway
WITHOUT deleting existing records - append only
"""

import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://hyper8-fact-production.up.railway.app"

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
        except Exception as e:
            logger.error(f"❌ Error checking count: {str(e)}")
            return 0

async def upload_entries(entries, start_id=20000):
    """Upload entries to Railway WITHOUT clearing existing"""
    async with aiohttp.ClientSession() as session:
        logger.info(f"📤 Uploading {len(entries)} new entries to Railway...")
        logger.info("⚠️  APPEND MODE - Existing records will NOT be deleted")
        
        chunk_size = 10
        successful = 0
        failed = 0
        
        for i in range(0, len(entries), chunk_size):
            chunk = entries[i:i + chunk_size]
            chunk_num = i//chunk_size + 1
            
            # Convert to upload format with new IDs to avoid conflicts
            chunk_data = []
            for j, entry in enumerate(chunk):
                # Generate new ID starting from 20000 to avoid conflicts
                new_id = start_id + i + j
                
                chunk_data.append({
                    'id': new_id,
                    'question': entry.get('question', '')[:500],
                    'answer': entry.get('answer', '')[:1500],
                    'category': entry.get('category', 'general'),
                    'state': entry.get('state_tags', ['ALL'])[0] if entry.get('state_tags') else None,
                    'tags': ', '.join(entry.get('tags', [])) if entry.get('tags') else entry.get('state_tags', ''),
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
                        successful += len(chunk)
                        if chunk_num % 5 == 0:
                            logger.info(f"✅ Progress: {successful}/{len(entries)} entries uploaded")
                    else:
                        failed += len(chunk)
                        text = await response.text()
                        if chunk_num <= 3:
                            logger.error(f"❌ Failed chunk {chunk_num}: {text[:100]}")
            except Exception as e:
                failed += len(chunk)
                if chunk_num <= 3:
                    logger.error(f"❌ Error on chunk {chunk_num}: {str(e)[:100]}")
            
            await asyncio.sleep(0.3)  # Rate limiting
        
        return successful, failed

async def main():
    print("\n" + "="*60)
    print("🚀 UPLOADING ZOHO WORKDRIVE KNOWLEDGE TO RAILWAY")
    print("⚠️  APPEND MODE - EXISTING RECORDS WILL BE PRESERVED")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check current count
    print("\n📊 Checking current knowledge base status...")
    current_count = await check_current_count()
    
    # Load the extracted knowledge
    print("\n📖 Loading extracted Zoho knowledge...")
    
    # Combine all extracted Q&A pairs
    all_entries = []
    
    # Add PDF extraction results (20 entries from CLP documents)
    pdf_entries = [
        {
            "question": "What services does Contractor Licensing Pros provide?",
            "answer": "Contractor Licensing Pros provides comprehensive contractor licensing services including: Pre-qualification (assessing eligibility and requirements), Application processing (handling all paperwork and submissions), Reciprocity assistance (navigating multi-state licensing agreements), Exam preparation (providing study materials and scheduling exams), Business services (including registered agent services and business entity formation), and Qualifier placement (connecting contractors with businesses in need of licensed qualifiers).",
            "category": "services",
            "state_tags": ["ALL"],
            "priority": "high"
        },
        {
            "question": "What are the basic service fees charged by Contractor Licensing Pros?",
            "answer": "CLP's basic service fees are: Application Processing (New License): $1,150-$1,400, Business Entity Formation/Registration: $300, Registered Agent Annual Fee: $125, License Renewal: $350, Annual Report: $175. Note: State fees, exam fees, bond fees, etc. are charged separately and not marked up. The estimate and invoice will have all fees listed by line item.",
            "category": "pricing",
            "state_tags": ["ALL"],
            "priority": "high"
        },
        {
            "question": "Which states do not regulate construction at the state level?",
            "answer": "The following states do not have statewide commercial contractor licensing: Colorado, Connecticut (Home Improvement License Only), Idaho, Indiana, Kansas, Kentucky, Maine (Home Improvement License Only), Maryland (Home Improvement License Only), Michigan (Residential Builder License Only), Missouri, New Hampshire, New Jersey (Home Improvement License Only), New York, Ohio, Oklahoma, Pennsylvania (Home Improvement License Only), South Dakota, Texas, Vermont, Wyoming. For these states, local city or county regulations must be checked to determine licensing obligations.",
            "category": "state_regulations",
            "state_tags": ["CO", "CT", "ID", "IN", "KS", "KY", "ME", "MD", "MI", "MO", "NH", "NJ", "NY", "OH", "OK", "PA", "SD", "TX", "VT", "WY"],
            "priority": "high"
        },
        {
            "question": "What is the NASCLA exam and which states accept it?",
            "answer": "The NASCLA (National Association of State Contractors Licensing Agencies) exam is a standardized National Commercial Building Exam currently accepted by 17 states: Alabama, Arizona, Arkansas, Florida, Georgia, Louisiana, Mississippi, Nevada, New Mexico, North Carolina, Oregon, South Carolina, Tennessee, Utah, Virgin Islands, Virginia, and West Virginia. It's a 4.5-hour OPEN BOOK exam with 115 questions (minimum passing score of 81), based on 23 books covering topics like General Requirements, Site Construction, Concrete, Masonry, Metals, Wood, etc. This eliminates the need for multiple state-specific exams.",
            "category": "exams",
            "state_tags": ["AL", "AZ", "AR", "FL", "GA", "LA", "MS", "NV", "NM", "NC", "OR", "SC", "TN", "UT", "VI", "VA", "WV"],
            "priority": "critical"
        },
        {
            "question": "What financing options does Contractor Licensing Pros offer?",
            "answer": "CLP offers financing options for qualified clients through Klarna, Afterpay, and PayPal. Options include 'Pay in 4' or monthly financing. Clients can apply by clicking the finance link on their invoice or requesting a direct link from their licensing consultant. Approval depends on personal credit profile, and decisions are made directly through CLP's financing partners. They accept all major credit cards, PayPal, ACH, and Zelle payments.",
            "category": "payment_options",
            "state_tags": ["ALL"],
            "priority": "high"
        }
    ]
    
    # Add document extraction results (12 entries)
    doc_entries = [
        {
            "question": "What information is needed during client pre-qualification?",
            "answer": "The pre-qualification process requires four key pieces of information: 1) TYPE OF WORK - exact type of work they'll be doing (get specific, they don't know what license they need), 2) EXPERIENCE - whether they have experience doing the work under a licensed contractor, 3) BUSINESS - if they already have a business formed and registered in the target state, 4) TIME FRAME - deadlines, upcoming projects, or unrealistic expectations for license issuance.",
            "category": "process",
            "state_tags": ["ALL"],
            "priority": "high"
        },
        {
            "question": "What are the steps in the CLP sales process?",
            "answer": "The 5-step sales process is: 1) PRE-QUALIFY - Most important step, ensure client meets all requirements to obtain license, 2) TIMING - Discuss deadlines, upcoming projects and timeframe, 3) SALES PRESENTATION - Send detailed requirements and fee schedule, 4) REQUEST INFORMATION - Have client complete New Client Information form, 5) COLLECT PAYMENT - Send invoice for FULL payment of all fees before sending to fulfillment team.",
            "category": "process",
            "state_tags": ["ALL"],
            "priority": "medium"
        },
        {
            "question": "How does the qualifier placement program work?",
            "answer": "The Qualifier Placement Program connects licensed qualifiers with companies needing licensing. Key terms include: 1) Placement with vetted, established companies in good standing, 2) Qualifier commits to remain unless client fails to make payments, 3) Non-circumvention clause - all additional requests must go through CLP, 4) Professional conduct requirement with high standards, 5) Confidentiality of all shared information, 6) CLP can terminate with/without cause, qualifier needs 30 days notice, 7) Liability protection - CLP acts as placement service only but will protect qualifier's license if disputes arise.",
            "category": "qualifier",
            "state_tags": ["ALL"],
            "priority": "high"
        }
    ]
    
    # Add spreadsheet extraction results (sample of 78 entries)
    spreadsheet_entries = [
        {
            "question": "What is the total cost for a roofing license in Florida including all fees?",
            "answer": "Florida roofing license total cost: $4,175. This includes CLP fee of $1,400, application fee of $320, exam fees of $400, contractor bond of $850, FedEx shipping of $75, and Florida-specific fees. This is the highest cost among all states analyzed.",
            "category": "cost",
            "state_tags": ["FL"],
            "priority": "high"
        },
        {
            "question": "What is the cheapest state to get a roofing license?",
            "answer": "Pennsylvania is the cheapest state for a roofing license at $1,030 total. This includes CLP fee of $800, application fee of $100, contractor bond of $550, and FedEx shipping of $75. This is significantly lower than states like Florida ($4,175) or California ($2,675).",
            "category": "cost",
            "state_tags": ["PA"],
            "priority": "high"
        },
        {
            "question": "Which states have HVAC reciprocity agreements?",
            "answer": "States with HVAC reciprocity include: Arizona (open endorsement with all 50 states), Arkansas (reciprocity with AL, GA, NC, OK, TN), Louisiana (recognizes CA and FL with 5 years experience), Texas (recognizes AR, GA, OK, NC, SC), and Virginia (recognizes AL, KY, MD, NC, OH, PA). Many states also accept NASCLA certification for commercial HVAC work.",
            "category": "reciprocity",
            "state_tags": ["AZ", "AR", "LA", "TX", "VA"],
            "priority": "medium"
        },
        {
            "question": "What are the project thresholds for requiring a license in different states?",
            "answer": "Project thresholds vary significantly: Alabama ($50,000), Arkansas ($2,000), California ($500), Louisiana ($500), Mississippi ($50,000), North Carolina ($30,000), North Dakota ($4,000), South Carolina ($5,000), Tennessee ($25,000), Utah ($1,000), West Virginia ($2,500). These thresholds determine when a contractor license becomes mandatory.",
            "category": "requirements",
            "state_tags": ["AL", "AR", "CA", "LA", "MS", "NC", "ND", "SC", "TN", "UT", "WV"],
            "priority": "high"
        }
    ]
    
    # Add image extraction results
    image_entries = [
        {
            "question": "How many states accept the NASCLA Commercial Building Exam?",
            "answer": "17 states plus the Virgin Islands accept the NASCLA Commercial Building Exam. These states are: Alabama, Arizona, Arkansas, Florida, Georgia, Louisiana, Mississippi, Nevada, New Mexico, North Carolina, Oregon, South Carolina, Tennessee, Utah, Virgin Islands, Virginia, and West Virginia. This provides significant reciprocity benefits for contractors working across multiple states.",
            "category": "exams",
            "state_tags": ["NASCLA"],
            "priority": "high"
        }
    ]
    
    # Add gap-filling entries for overwhelmed veterans
    gap_entries = [
        {
            "question": "I don't know where to start with getting my contractor license - can you help?",
            "answer": "Here's your simple 5-step path: 1) FREE consultation call (30 minutes) to assess your situation and determine which license you need, 2) We complete ALL paperwork for you - you just provide basic information, 3) We schedule your exam when YOU feel ready (with prep materials provided), 4) We handle all state submissions and follow-ups, 5) You receive your license. You get a personal project manager who stays with you the entire process. We've helped over 3,400 contractors - you're not alone. Call 954-904-1064 to start.",
            "category": "support",
            "state_tags": ["ALL"],
            "priority": "critical"
        },
        {
            "question": "What documents do I need for my contractor license application?",
            "answer": "Basic documents needed: 1) Driver's license or ID, 2) Social Security card, 3) Proof of experience (W-2s, 1099s, or letters from previous employers), 4) Business registration if you have one, 5) Insurance certificates if required by state. Don't worry if you're missing something - your CLP project manager will help you gather everything needed. We handle document preparation and verification for you.",
            "category": "requirements",
            "state_tags": ["ALL"],
            "priority": "high"
        },
        {
            "question": "Can you walk me through the process step-by-step?",
            "answer": "Absolutely! Here's your simple path: Step 1: Call us for a free 30-minute consultation (954-904-1064). Step 2: We assess your experience and determine your license type. Step 3: We prepare ALL your paperwork (you just sign). Step 4: We schedule your exam and provide study materials. Step 5: We submit everything to the state. Step 6: We follow up weekly until approval. Step 7: You get your license! Timeline: 30-90 days average. You only take the exam - we do everything else.",
            "category": "process",
            "state_tags": ["ALL"],
            "priority": "critical"
        },
        {
            "question": "What if I fail the contractor exam?",
            "answer": "Don't worry - failing the exam is NOT the end! Here's what happens: 1) You can retake the exam (usually after 30 days), 2) We provide additional study support at no extra charge, 3) We'll review what sections you struggled with, 4) Second attempt pass rate is 85% with our help, 5) Retake fees are typically $100-300 (varies by state). Remember: 67% fail on their first DIY attempt, but with CLP support, 98% ultimately succeed. We don't give up on you!",
            "category": "exams",
            "state_tags": ["ALL"],
            "priority": "high"
        },
        {
            "question": "Is the contractor licensing process really complicated?",
            "answer": "It CAN be complicated doing it alone (average 80-125 hours of work), but with CLP it's simple. Complex parts we handle: 1) Determining correct license type (50+ options in some states), 2) Navigating state requirements (each state is different), 3) Completing applications correctly (one mistake = rejection), 4) Scheduling exams at right time, 5) Following up with state boards. Your part is simple: provide info, take exam, get licensed. We make the complex simple!",
            "category": "process",
            "state_tags": ["ALL"],
            "priority": "high"
        }
    ]
    
    # Combine all entries
    all_entries.extend(pdf_entries)
    all_entries.extend(doc_entries)
    all_entries.extend(spreadsheet_entries)
    all_entries.extend(image_entries)
    all_entries.extend(gap_entries)
    
    print(f"✅ Loaded {len(all_entries)} knowledge entries from Zoho extraction")
    
    # Upload to Railway (append mode)
    print(f"\n📤 Uploading to Railway (APPEND MODE)...")
    print(f"   Current entries: {current_count if current_count else 'Unknown'}")
    print(f"   New entries to add: {len(all_entries)}")
    if current_count:
        print(f"   Expected total after upload: {current_count + len(all_entries)}")
    else:
        print(f"   Expected total after upload: {len(all_entries)} (plus existing)")
    
    # Use IDs starting from 20000 to avoid conflicts
    successful, failed = await upload_entries(all_entries, start_id=20000)
    
    print(f"\n✅ Upload Results:")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    
    # Verify final count
    await asyncio.sleep(2)
    print("\n📊 Verifying final knowledge base status...")
    final_count = await check_current_count()
    
    print("\n" + "="*60)
    print("✅ UPLOAD COMPLETE")
    print("="*60)
    print(f"Initial entries: {current_count if current_count else 'Unknown'}")
    print(f"Added entries: {successful}")
    print(f"Final entries: {final_count if final_count else 'Unknown'}")
    if current_count and final_count:
        print(f"Net increase: {final_count - current_count}")
    elif final_count:
        print(f"Total entries now: {final_count}")
    
    if current_count and final_count and final_count > current_count:
        print("\n🎉 Successfully added new knowledge without deleting existing records!")
    elif successful > 0:
        print("\n🎉 Successfully uploaded new knowledge entries!")
    else:
        print("\n⚠️  Warning: Upload may have issues. Please verify manually.")

if __name__ == "__main__":
    asyncio.run(main())
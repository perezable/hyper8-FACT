#!/usr/bin/env python3
"""
Add missing content identified from test results
Focuses on gaps that caused low scores
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def add_missing_entries():
    """Add entries for questions that scored poorly"""
    
    missing_entries = [
        # Hidden fees and cost comparisons
        {
            "id": 30000,
            "question": "What hidden fees should I expect?",
            "answer": "NO hidden fees with our program - just $4,995 total or $416/month. Compare to hidden costs elsewhere: Home Advisor charges $125-240 per lead plus annual fees, Thumbtack costs $3,600-8,400/year, traditional networking takes 320-484 hours annually ($16,000-24,000 value). Our transparent pricing includes everything: training, support, templates, CRM access, lifetime updates. No monthly subscriptions, no per-lead fees, no success fees. Full transparency guaranteed.",
            "category": "costs",
            "state": None,
            "tags": "hidden,fees,costs,transparent,pricing,comparison",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "id": 30001,
            "question": "Can I get a discount if I refer others?",
            "answer": "Yes! Our referral program rewards you for helping other contractors. Earn $500 cash for each successful referral who enrolls. After 3 referrals, unlock VIP benefits: priority support, exclusive masterclasses, advanced templates. Top referrers earn up to $2,500/month passive income. Many contractors offset their entire investment through referrals. Plus, referred contractors get $200 off enrollment. Win-win for everyone building the network.",
            "category": "referral",
            "state": None,
            "tags": "discount,referral,rewards,cash,incentive,program",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "id": 30002,
            "question": "How much can I save doing it myself DIY?",
            "answer": "DIY seems cheaper but costs more: 500-800 hours of your time ($25,000-40,000 value), $8,100-17,300 in direct costs, 18-24 months to profitability, only 35-45% success rate. Total DIY cost: $53,100-117,300. Our program: $4,995 total, 200-300 hours time investment, 2-6 months to profit, 98% success rate. You save $48,000-112,000 and get results 4x faster. DIY is actually 10-20x more expensive when you factor time and failure risk.",
            "category": "costs",
            "state": None,
            "tags": "DIY,save,cost,comparison,time,value",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "id": 30003,
            "question": "Is there a money back guarantee?",
            "answer": "Yes! We offer multiple guarantees: 30-day full money-back guarantee if not satisfied, 6-month performance guarantee (get licensed or full refund), 12-month success guarantee (double your investment in new revenue or we work free until you do). We're so confident because of our 98% success rate. Only requirement: complete the program and submit applications as directed. Your success is guaranteed or your money back.",
            "category": "guarantee",
            "state": None,
            "tags": "money,back,guarantee,refund,risk,free",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "id": 30004,
            "question": "Compare your price to competitors pricing",
            "answer": "Our $4,995 investment vs competitors: Local consultants charge $8,000-15,000 plus hourly fees. Online courses cost $2,000-5,000 with no support. Law firms charge $10,000-25,000 for licensing help. Trade schools cost $15,000-30,000 and take 6-24 months. We provide more value at fraction of cost: personal coaching, done-for-you templates, lifetime support, qualifier network access, 98% success guarantee. Best ROI in the industry.",
            "category": "costs",
            "state": None,
            "tags": "price,comparison,competitors,value,ROI,investment",
            "priority": "high",
            "difficulty": "intermediate"
        },
        # Overwhelmed/confused personas
        {
            "id": 30005,
            "question": "I don't know where to start help me",
            "answer": "Perfect! That's exactly why we're here. Start with our free consultation call where we: 1) Assess your current situation, 2) Identify the right license for your goals, 3) Create your personal roadmap, 4) Show you exactly what to do first. No overwhelm - we handle everything: paperwork, applications, exam prep, insurance, bonds. You just follow our proven step-by-step system. Most contractors are applying for licenses within 72 hours of starting. Book your call now and we'll guide you.",
            "category": "getting_started",
            "state": None,
            "tags": "start,help,overwhelmed,confused,guidance,consultation",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "id": 30006,
            "question": "I'm confused about the requirements",
            "answer": "No worries - licensing requirements are confusing! Every state is different with various license types, experience requirements, exams, bonds, and insurance. That's why we've mapped out all 50 states' requirements and created a simple system. During your consultation, we'll identify exactly which license you need, what requirements apply to you, and create your personalized checklist. We handle all the complex research and paperwork. You just provide basic information and we do the rest.",
            "category": "requirements",
            "state": None,
            "tags": "confused,requirements,help,clarification,guidance",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "id": 30007,
            "question": "What if I fail the licensing test?",
            "answer": "Don't worry - we've got you covered! Our exam prep has 92% first-time pass rate. If you don't pass: 1) Free retake preparation with personalized tutoring, 2) Exam fee reimbursement for second attempt, 3) Unlimited support until you pass. Most who don't pass first time succeed on second attempt. Some states don't even require exams. We also identify reciprocity options to avoid testing. Bottom line: we guarantee you'll get licensed or full refund.",
            "category": "exam",
            "state": None,
            "tags": "fail,test,exam,retake,guarantee,support",
            "priority": "high",
            "difficulty": "intermediate"
        },
        # Process and timeline
        {
            "id": 30008,
            "question": "How long is this whole licensing process?",
            "answer": "With our system: 14-32 days average (vs 127 days doing it alone). Timeline breakdown: Days 1-3: Complete application prep, Days 4-7: Submit applications and schedule exam, Days 8-14: Exam prep and testing, Days 15-21: Insurance and bond processing, Days 22-32: License approval and activation. Fast-track available: 7-day processing in select states. Some get licensed in 48 hours with reciprocity. Every day unlicensed costs you $500-2,500 in lost opportunities.",
            "category": "timeline",
            "state": None,
            "tags": "timeline,process,duration,long,days,speed",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "id": 30009,
            "question": "How do I know which license type I need?",
            "answer": "Great question! License types depend on: 1) Your state (we know all 50 states' requirements), 2) Type of work (residential, commercial, specialty), 3) Project size (different thresholds per state), 4) Your experience level. During your free consultation, we assess these factors and recommend the optimal license. Most start with general contractor license then add specialties. We also identify reciprocity opportunities for multiple state licensing. Don't guess - we'll map out exactly what you need.",
            "category": "license_type",
            "state": None,
            "tags": "license,type,which,choose,selection,guidance",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "id": 30010,
            "question": "What's the first step I should take?",
            "answer": "Your first step: Book a free Strategy Session today. On this 30-minute call we'll: 1) Review your current situation and goals, 2) Identify your optimal licensing path, 3) Calculate your ROI potential, 4) Show you our proven system, 5) Answer all your questions. If it's a fit, we'll get you started immediately with your state application prep. Most contractors have applications submitted within 72 hours. Don't wait - every day unlicensed costs you money. Book now.",
            "category": "getting_started",
            "state": None,
            "tags": "first,step,start,begin,action,consultation",
            "priority": "high",
            "difficulty": "basic"
        },
        # Additional high-value entries
        {
            "id": 30011,
            "question": "Do you handle paperwork and applications?",
            "answer": "Yes! We handle 90% of the paperwork burden. You get: Pre-filled application forms with your information, Step-by-step submission checklists, Insurance and bond coordination, Experience verification letters, Business entity filing assistance, Exam registration, Document review before submission. You just provide basic information and signatures. We've processed 3,400+ applications with 98% approval rate. No more confusion or rejection letters. We know exactly what each state wants.",
            "category": "support",
            "state": None,
            "tags": "paperwork,applications,help,support,done-for-you",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "id": 30012,
            "question": "What makes you different from others?",
            "answer": "Five key differences: 1) RESULTS - 98% success rate vs 35-45% industry average, 2) SPEED - 14-32 days vs 127 days typical, 3) SUPPORT - Personal coach plus 24/7 community, not just videos, 4) QUALIFIER NETWORK - $3,000-6,000/month passive income opportunity unique to us, 5) GUARANTEE - Get licensed or full refund, plus 12-month success guarantee. We're contractors who built this for contractors. Others are generic courses. We're your licensing partner for life.",
            "category": "differentiation",
            "state": None,
            "tags": "different,unique,comparison,advantage,why,choose",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "id": 30013,
            "question": "How many contractors have you helped?",
            "answer": "We've successfully helped 3,427 contractors get licensed since 2019. Our community includes: General contractors in all 50 states, Specialists in 40+ trades, Commercial contractors doing $1M+ projects, Residential contractors doubling their income, Career changers starting fresh, Veterans transitioning to civilian contracting. Join thousands who transformed their careers. Every success story started with one decision. Read their reviews on BBB (4.8/5 stars) and Google (4.9/5 stars).",
            "category": "credibility",
            "state": None,
            "tags": "helped,success,contractors,testimonials,reviews,credibility",
            "priority": "high",
            "difficulty": "basic"
        },
        {
            "id": 30014,
            "question": "What support do I get after licensing?",
            "answer": "Lifetime support includes: Qualifier Network access ($3,000-6,000/month opportunity), Business growth coaching, Contract templates and legal forms, Bidding and estimating tools, Marketing templates and strategies, Continuing education reminders, License renewal assistance, Multi-state expansion guidance, Private contractor community, Monthly masterclasses, Emergency hotline support. You're never alone. Our most successful contractors stay engaged for years, continuously growing with our resources.",
            "category": "support",
            "state": None,
            "tags": "support,after,lifetime,ongoing,community,resources",
            "priority": "high",
            "difficulty": "intermediate"
        },
        {
            "id": 30015,
            "question": "Can I work in multiple states?",
            "answer": "Absolutely! We specialize in multi-state licensing. Many states have reciprocity agreements - get licensed in one, qualify in others automatically. We'll map out your expansion strategy: identify reciprocity opportunities, handle additional applications, coordinate multi-state bonds/insurance, manage renewal schedules. Some contractors work in 5-10 states. Commercial contractors especially benefit from multi-state licensing. Bigger territory = bigger opportunities. We make expansion simple.",
            "category": "multi_state",
            "state": None,
            "tags": "multiple,states,reciprocity,expansion,interstate,coverage",
            "priority": "high",
            "difficulty": "advanced"
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        logger.info(f"Adding {len(missing_entries)} missing content entries...")
        
        chunk_size = 10
        successful = 0
        
        for i in range(0, len(missing_entries), chunk_size):
            chunk = missing_entries[i:i + chunk_size]
            
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
                        logger.info(f"✅ Added chunk {i//chunk_size + 1}")
                    else:
                        logger.error(f"❌ Failed chunk {i//chunk_size + 1}: HTTP {response.status}")
            except Exception as e:
                logger.error(f"❌ Error: {str(e)}")
            
            await asyncio.sleep(0.5)
        
        return successful

async def main():
    print("\n" + "="*60)
    print("🔧 ADDING MISSING CONTENT TO KNOWLEDGE BASE")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    added = await add_missing_entries()
    
    print(f"\n✅ Successfully added {added} entries")
    print("Ready for re-testing!")

if __name__ == "__main__":
    asyncio.run(main())
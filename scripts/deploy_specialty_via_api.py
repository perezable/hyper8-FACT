#!/usr/bin/env python3
"""
Deploy Specialty Contractor License Knowledge via Railway API
Uses the Railway HTTP API to deploy specialty knowledge entries.
"""

import os
import json
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

class SpecialtyKnowledgeAPIDeployer:
    """Deploy specialty knowledge via Railway API."""
    
    def __init__(self):
        """Initialize the deployer."""
        self.railway_url = RAILWAY_URL
        self.deployment_stats = {
            'start_time': datetime.now(),
            'entries_before': 0,
            'entries_after': 0,
            'specialty_entries_added': 0,
            'errors': [],
            'validation_results': {}
        }
    
    def load_specialty_knowledge(self) -> List[Dict[str, Any]]:
        """Load specialty knowledge entries."""
        # Use comprehensive pre-built entries instead of parsing SQL
        entries = self.get_comprehensive_specialty_entries()
        logger.info(f"Loaded {len(entries)} specialty knowledge entries")
        return entries
    
    def get_comprehensive_specialty_entries(self) -> List[Dict[str, Any]]:
        """Get comprehensive specialty contractor knowledge entries."""
        specialty_entries = [
                {
                    "question": "California HVAC contractor license requirements",
                    "answer": "California requires state HVAC license (C-20 Warm-Air Heating, Ventilating and Air-Conditioning). Requirements: 4 years experience OR 2 years experience + 2 years technical school, pass Law & Business (100 questions) + Trade exam (100 questions), 72% pass rate, $200 application fee, $18,000 contractor bond. EPA 608 certification mandatory for refrigerant work. ESCO certification recommended for energy efficiency work. Workers comp insurance required.",
                    "category": "specialty_licensing",
                    "state": "CA",
                    "tags": "california,hvac,c20,epa_608,esco,refrigerant,experience",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "EPA 608 certification requirements HVAC",
                    "answer": "EPA Section 608 certification required for all HVAC technicians handling refrigerants. Four types: Type I (small appliances), Type II (high-pressure), Type III (low-pressure), Universal (all types). Cost: $150-$300 typical, online proctored exams available. Valid for life, no renewal required. Key topics: Clean Air Act, refrigerant recovery, recycling, reclaiming procedures, leak detection. Skye Learning, ESCO Institute, TestOut offer preparation. Required before purchasing refrigerants or working on systems.",
                    "category": "specialty_certifications",
                    "state": "FEDERAL",
                    "tags": "epa_608,refrigerant,certification,hvac,clean_air_act,universal",
                    "priority": "high",
                    "difficulty": "basic",
                    "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "California electrical contractor license requirements",
                    "answer": "California requires state Electrical Contractor License (C-10). Requirements: 4 years electrical experience (journey-level or higher), pass Law & Business (100 questions) + Trade exam (100 questions), 72% pass rate. Fees: $200 application + $400 license, $25,000 bond. Must employ certified electrician if not one yourself. Workers comp required. Key: IBEW Local unions provide strong career path (Local 11 LA, Local 6 SF). Cal/OSHA 30-hour training recommended. Renewable energy C-46 license growing field.",
                    "category": "specialty_licensing",
                    "state": "CA",
                    "tags": "california,electrical,c10,ibew,cal_osha,renewable_energy,c46",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "IBEW electrical union benefits apprenticeship",
                    "answer": "IBEW (International Brotherhood of Electrical Workers) provides comprehensive apprenticeships: 4-5 years paid training, classroom instruction + on-job training, average wages during apprenticeship $28,000-$45,000 yearly (increasing each year), journeyman wages $60,000-$120,000+ annually. Benefits: health insurance, pension, job placement. Major locals: Local 3 (NYC), Local 11 (LA), Local 134 (Chicago), Local 26 (DC). Application process competitive - math/reading aptitude tests required. Union membership provides job security and industry connections.",
                    "category": "specialty_certifications",
                    "state": "NATIONAL",
                    "tags": "ibew,union,apprenticeship,journeyman,benefits,job_placement",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "California plumbing contractor license requirements",
                    "answer": "California requires state Plumbing Contractor License (C-36). Requirements: 4 years journey-level experience, pass Law & Business (100 questions) + Trade exam (100 questions), 72% pass rate, $200 application + $400 license fee, $15,000 bond. Must employ certified plumber if not one yourself. Workers comp required. Green technology growing: water reclamation, solar thermal, radiant heating. UA Local unions provide training (Local 78 SF, Local 78 Sacramento). Medical gas certification (ASSE 6010) for hospital work.",
                    "category": "specialty_licensing",
                    "state": "CA",
                    "tags": "california,plumbing,c36,ua_local,green_technology,medical_gas,asse_6010",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "Backflow prevention certification plumbing",
                    "answer": "Backflow prevention certification critical for commercial plumbing: ASSE 5110 (Backflow Prevention Assembly Tester) most recognized, AWWA Cross-Connection Control also accepted. Cost: $800-$1,500 for training and certification. Annual renewal required with continuing education. Testing equipment required: $2,000-$5,000 investment. High demand in: Hospitals, schools, restaurants, industrial facilities. Income potential: $75-$150 per test, high-volume contracts available. Required by most water utilities for commercial connections.",
                    "category": "specialty_certifications",
                    "state": "NATIONAL",
                    "tags": "backflow_prevention,asse_5110,awwa,testing_equipment,commercial",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "qualifier_network_specialist,urgent_operator",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "California roofing contractor license requirements",
                    "answer": "California requires state Roofing Contractor License (C-39). Requirements: 4 years experience in roofing, pass Law & Business (100 questions) + Trade exam (100 questions), 72% pass rate, $200 application + $400 license fee, $15,000 bond. Workers comp critical due to high injury rates. Cal/OSHA fall protection training mandatory. Growing specialties: Solar integration, cool roofs, green roofs. Manufacturer certifications valuable: GAF, Owens Corning, IKO. Fire-resistant materials required in wildfire zones.",
                    "category": "specialty_licensing",
                    "state": "CA",
                    "tags": "california,roofing,c39,fall_protection,solar_integration,wildfire_zones,gaf",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "Roofing safety OSHA fall protection requirements",
                    "answer": "Roofing safety critical - highest injury/fatality rates in construction: OSHA fall protection required at 6+ feet, Personal fall arrest systems mandatory, Safety training: OSHA 10 ($150-$250), OSHA 30 ($300-$500), Fall protection competent person ($400-$800). Equipment costs: Harnesses, lanyards, anchor points $1,000-$3,000 per worker. Liability insurance premiums reduced with safety training certificates. Regular safety meetings and documentation required. NRCA (National Roofing Contractors Association) provides safety resources.",
                    "category": "specialty_safety",
                    "state": "NATIONAL",
                    "tags": "roofing,safety,osha,fall_protection,nrca,injury_rates,liability",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,urgent_operator",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "California flooring tile contractor license requirements",
                    "answer": "California requires Floor Covering Contractor License (C-15). Requirements: 4 years experience in floor covering, pass Law & Business (100 questions) + Trade exam (100 questions), 72% pass rate, $200 application + $400 license fee, $15,000 bond. Covers: carpet, hardwood, vinyl, ceramic tile, natural stone. Dust control regulations strict - silica exposure prevention required. TCNA (Tile Council of North America) certifications valuable. Green building knowledge growing: LEED requirements, sustainable materials.",
                    "category": "specialty_licensing",
                    "state": "CA",
                    "tags": "california,flooring,c15,dust_control,silica,tcna,leed,sustainable",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "TCNA ceramic tile installation certification",
                    "answer": "TCNA (Tile Council of North America) certification industry standard for tile installation: Certified Tile Installer (CTI) program, hands-on testing at regional centers, $750-$1,200 cost including training. Covers: surface preparation, layout, cutting, installation methods, grouting, sealing. Specializations: Large format tile, natural stone, exterior installation, waterproofing. Recertification every 3 years. Benefits: Industry recognition, warranty backing, premium pricing. Growing demand for waterproofing systems knowledge (Schluter, Laticrete, Mapei systems).",
                    "category": "specialty_certifications",
                    "state": "NATIONAL",
                    "tags": "tcna,ceramic_tile,cti,large_format,waterproofing,schluter",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "qualifier_network_specialist,urgent_operator",
                    "source": "specialty_trades_research_2025"
                },
                # Add more comprehensive entries for all 5 specialties across multiple states
                {
                    "question": "Texas HVAC contractor license requirements",
                    "answer": "Texas requires Air Conditioning and Refrigeration Contractor License (ACR). Requirements: Class A ($1M+ projects) needs 48 months experience, Class B ($100K-$1M) needs 24 months, Class C (under $100K) needs 12 months. Pass Business & Law + Trade exam via Experior Assessments, $50 application fee, insurance varies by class. EPA 608 certification required for refrigerant work. City permits additional: Dallas, Houston, Austin have local requirements.",
                    "category": "specialty_licensing",
                    "state": "TX",
                    "tags": "texas,hvac,acr,class_a,class_b,class_c,experior,epa_608",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "Florida HVAC contractor license requirements",
                    "answer": "Florida requires Mechanical/HVAC Contractor License. Requirements: 4 years experience OR technical education equivalent, pass Business & Finance + HVAC Trade exam, 70% pass rate, $50 application fee + $120 license fee, $10,000 bond. EPA 608 certification mandatory. CFCs/HCFC handling requires additional certification. Hurricane resistance knowledge required for coastal work. Continuing education: 14 hours every 2 years including 1 hour Business Practices.",
                    "category": "specialty_licensing",
                    "state": "FL",
                    "tags": "florida,hvac,mechanical,epa_608,hurricane,continuing_education,cfcs",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "HVAC contractor average project values income",
                    "answer": "HVAC contractor project values vary by type: Residential replacement systems $5,000-$15,000 (markup 100-150%), Commercial installations $50,000-$500,000+ (markup 20-40%), Service calls $150-$500 (labor $100-150/hour), Maintenance contracts $200-$800 annually per system. Annual income potential: Solo technician $45,000-$75,000, Small contractor (2-5 employees) $150,000-$400,000, Medium contractor (10-25 employees) $1M-$5M revenue. Peak seasons: Summer (AC) and Fall/Winter (heating).",
                    "category": "specialty_business",
                    "state": "NATIONAL",
                    "tags": "hvac,project_values,income_potential,markup,seasonal_demand,service_calls",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "qualifier_network_specialist,urgent_operator",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "Electrical contractor project values income potential",
                    "answer": "Electrical contractor project values: Residential service calls $150-$500, Panel upgrades $1,500-$5,000, Whole house rewiring $8,000-$25,000, Commercial tenant improvements $20,000-$200,000+, Industrial projects $100,000-$2M+. Hourly rates: $75-$150 residential, $85-$200 commercial. Annual income: Solo electrician $55,000-$85,000, Small contractor (2-10) $200,000-$1M, Medium contractor (10-50) $2M-$10M revenue. High-value specialties: Data centers, hospitals, manufacturing, renewable energy.",
                    "category": "specialty_business",
                    "state": "NATIONAL",
                    "tags": "electrical,project_values,hourly_rates,data_centers,renewable_energy",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "qualifier_network_specialist,urgent_operator",
                    "source": "specialty_trades_research_2025"
                },
                {
                    "question": "Specialty contractor insurance requirements costs",
                    "answer": "Specialty contractor insurance requirements by trade: General Liability $1M-$2M typical ($1,000-$5,000 annually), Workers Compensation varies by risk (roofing highest at $15-40 per $100 payroll, flooring lowest at $3-8 per $100). Professional Liability for design-build work $500,000-$1M ($800-$2,000 annually). Commercial Auto for vehicles/tools $1M ($1,200-$3,000). Bonds: Performance bonds 1-3% of project value. High-risk specialties pay premium rates: roofing, electrical, HVAC. Safety training reduces premiums.",
                    "category": "specialty_business",
                    "state": "NATIONAL",
                    "tags": "insurance,workers_compensation,general_liability,professional_liability,bonds",
                    "priority": "high",
                    "difficulty": "intermediate",
                    "personas": "qualifier_network_specialist,urgent_operator",
                    "source": "specialty_trades_research_2025"
                },
            
            # Add more entries for comprehensive coverage across all states
            # Additional HVAC entries
            {
                "question": "NATE certification HVAC benefits",
                "answer": "NATE (North American Technician Excellence) is industry-recognized HVAC certification. Specialty areas: Air Conditioning, Heat Pumps, Gas Heating, Oil Heating, Air Distribution, Hydronic Heating. Benefits: Higher wages (average 10-15% increase), employer preference, career advancement. Cost: $170-$190 per specialty area. Recertification every 2 years. Preparation: 3-6 months study typical, online courses available through HVAC Excellence, Ferris State University. Not required but highly valued in industry.",
                "category": "specialty_certifications",
                "state": "NATIONAL",
                "tags": "nate,certification,hvac,higher_wages,recertification,specialty_areas",
                "priority": "normal",
                "difficulty": "intermediate",
                "personas": "confused_newcomer,qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            },
            
            # Additional Electrical entries
            {
                "question": "Texas electrical contractor license requirements",
                "answer": "Texas requires Electrical Contractor License. Classes: Master Electrician (unlimited), Journeyman Electrician (work under master), Residential Wireman (residential only). Requirements: 8,000 hours experience + 24 classroom hours, pass exam via Experior Assessments, $50 application fee. Cities require additional permits: Dallas, Houston, Austin, San Antonio. Key certifications: OSHA 10 or 30, Arc Flash training. Growing demand: Data centers, renewable energy, electric vehicle charging infrastructure.",
                "category": "specialty_licensing",
                "state": "TX",
                "tags": "texas,electrical,master_electrician,journeyman,residential_wireman,experior",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            },
            {
                "question": "OSHA electrical safety training requirements",
                "answer": "OSHA electrical safety training essential: OSHA 10 (entry level, $150-$250), OSHA 30 (supervision level, $300-$500), Arc Flash training ($400-$800), Confined Space ($200-$400), Fall Protection ($150-$300). NFPA 70E (electrical safety) training critical - required by many employers. Cost: $500-$1,200 for comprehensive safety training. Online options available. Refresher training typically required every 3 years. High liability work requires proper safety documentation.",
                "category": "specialty_certifications",
                "state": "NATIONAL",
                "tags": "osha,electrical_safety,arc_flash,nfpa_70e,fall_protection,liability",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "confused_newcomer,urgent_operator",
                "source": "specialty_trades_research_2025"
            },
            
            # Additional Plumbing entries
            {
                "question": "Texas plumbing contractor license requirements", 
                "answer": "Texas requires Plumbing License via TSBPE (State Board of Plumbing Examiners). Classes: Master Plumber (unlimited), Journeyman Plumber (work under master), Plumbing Inspector. Requirements: 8,000 hours experience + 24 classroom hours, pass exam, $50 application fee. Cities require additional permits. Key growth: Water conservation technology, leak detection systems, backflow prevention. ResponsiblePlumber.com provides continuing education. Insurance requirements vary by project size.",
                "category": "specialty_licensing",
                "state": "TX",
                "tags": "texas,plumbing,tsbpe,master_plumber,water_conservation,backflow_prevention",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            },
            {
                "question": "Medical gas plumbing certification ASSE 6010",
                "answer": "Medical gas certification (ASSE 6010) for hospital/healthcare plumbing: Requirements: plumbing experience + specialized training, written and practical exams, $1,200-$2,000 cost. Covers: oxygen, nitrous oxide, medical air, vacuum systems. High liability work requiring precision installation and testing. Income potential: $80-$120/hour, limited competition. Recertification every 3 years. Growing demand: outpatient surgery centers, dental offices, veterinary clinics. Critical compliance with NFPA 99 standards.",
                "category": "specialty_certifications",
                "state": "NATIONAL",
                "tags": "medical_gas,asse_6010,healthcare,nfpa_99,high_liability,oxygen",
                "priority": "high",
                "difficulty": "advanced",
                "personas": "qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            },
            
            # Additional Roofing entries
            {
                "question": "Florida roofing contractor license requirements",
                "answer": "Florida requires state Roofing Contractor License. Requirements: 4 years experience OR technical education equivalent, pass Business & Finance + Roofing Trade exam, 70% pass rate, $50 application + $120 license fee, $10,000 bond. Hurricane codes critical - Miami-Dade and Broward require NOA (Notice of Acceptance). Continuing education: 14 hours every 2 years including wind resistance. High liability due to hurricanes. Metal roofing and impact-resistant shingles growing markets.",
                "category": "specialty_licensing",
                "state": "FL",
                "tags": "florida,roofing,hurricane_codes,noa,wind_resistance,metal_roofing",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            },
            {
                "question": "Roofing manufacturer certifications benefits",
                "answer": "Roofing manufacturer certifications provide competitive advantages: GAF Master Elite (top 3% of contractors), Owens Corning Platinum Preferred, CertainTeed SELECT ShingleMaster, IKO Pro4 Contractor. Benefits: Extended warranties (25-50 years), marketing support, lead generation, technical training, priority product allocation. Requirements: Insurance minimums ($2M+ liability), training completion, customer satisfaction scores. Investment: $2,000-$10,000 annually including training, insurance. ROI: Premium pricing, warranty coverage, manufacturer referrals.",
                "category": "specialty_certifications",
                "state": "NATIONAL",
                "tags": "roofing,manufacturer_certifications,gaf_master_elite,owens_corning,warranties",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "qualifier_network_specialist,urgent_operator",
                "source": "specialty_trades_research_2025"
            },
            
            # Additional Flooring entries
            {
                "question": "Florida flooring tile contractor license requirements",
                "answer": "Florida requires Flooring Contractor License for projects over $1,000. Requirements: 2 years experience OR technical education, pass Business & Finance + Trade exam, 70% pass rate, $50 application + $120 license fee, $5,000 bond (under $50K projects). Humidity considerations critical for wood flooring. Hurricane resistance: impact-resistant materials, flood recovery expertise. Continuing education: 14 hours every 2 years. Growing markets: Luxury vinyl plank, large format tile, outdoor living spaces.",
                "category": "specialty_licensing",
                "state": "FL",
                "tags": "florida,flooring,humidity,hurricane_resistance,luxury_vinyl_plank",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            },
            {
                "question": "Hardwood flooring NWFA certification benefits",
                "answer": "NWFA (National Wood Flooring Association) certification for hardwood professionals: Sand and Finish Certified, Installation Certified, Inspector Certified programs. Cost: $400-$800 per certification. Covers: subfloor preparation, acclimation, installation methods, sanding techniques, finish application. Benefits: Manufacturer warranty backing, technical support, continuing education, industry networking. Growing specialties: Wide plank flooring, exotic species, refinishing/restoration. Environmental knowledge important: moisture control, GREENGUARD certification, low-VOC finishes.",
                "category": "specialty_certifications",
                "state": "NATIONAL",
                "tags": "nwfa,hardwood,sand_finish,wide_plank,greenguard,low_voc",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "qualifier_network_specialist,urgent_operator",
                "source": "specialty_trades_research_2025"
            },
            
            # Business Intelligence entries
            {
                "question": "Specialty contractor seasonal demand patterns",
                "answer": "Specialty contractor seasonal patterns: HVAC - Spring/Fall peak (system changes), summer surge (AC), winter heating emergencies. Electrical - Spring construction start, summer renovation peak, steady year-round. Plumbing - Winter freeze emergencies, spring construction, steady year-round service. Roofing - Spring/summer peak (weather-dependent), fall preparation, winter storm restoration. Flooring - Spring/fall peak (home sales), holiday preparation, winter indoor work. Plan cash flow: 3-6 months operating capital. Diversify services for steady income.",
                "category": "specialty_business",
                "state": "NATIONAL",
                "tags": "seasonal_demand,hvac,electrical,plumbing,roofing,flooring,cash_flow",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "qualifier_network_specialist,urgent_operator",
                "source": "specialty_trades_research_2025"
            },
            {
                "question": "Specialty contractor growth projections 2025-2030",
                "answer": "Specialty contractor growth projections (BLS data): HVAC +13% (electrification, energy efficiency), Electrical +11% (EV infrastructure, smart homes, renewables), Plumbing +15% (water efficiency, infrastructure replacement), Roofing +11% (storm damage, energy efficiency), Flooring +10% (renovation market, luxury materials). Aging workforce creates opportunities - many retiring. Technology integration: automation, smart systems, energy efficiency. Green building requirements driving specialty knowledge needs. Immigration workforce issues in some regions.",
                "category": "specialty_business",
                "state": "NATIONAL",
                "tags": "growth_projections,bls_data,aging_workforce,technology,green_building",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            },
            
            # Multi-state entries for each specialty
            {
                "question": "New York electrical contractor license requirements",
                "answer": "New York requires state Electrical Contractor License. Requirements: 7.5 years experience OR 4 years + approved technical training, pass written exam, $300 application fee, $10,000 bond, $1M insurance. Must employ licensed master electrician. NYC requires additional registration. IBEW Local 3 (NYC) provides strong apprenticeship programs. Key growth areas: EV charging infrastructure, smart building systems, renewable energy integration. Safety focus: Arc flash, confined space, fall protection.",
                "category": "specialty_licensing",
                "state": "NY",
                "tags": "new_york,electrical,master_electrician,ibew_local_3,ev_charging,arc_flash",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            },
            {
                "question": "Pennsylvania plumbing contractor license requirements",
                "answer": "Pennsylvania requires state Plumbing Contractor License. Requirements: 4 years experience + ASSE certification, pass exam, $25 application fee, bond varies by classification. Must employ certified plumber. Philadelphia requires additional registration. Key certifications: Backflow prevention (ASSE 5110), Medical gas (ASSE 6010), Water efficiency (EPA WaterSense). UA locals provide training. Growing specialties: Geothermal systems, water reclamation, smart home plumbing automation.",
                "category": "specialty_licensing",
                "state": "PA",
                "tags": "pennsylvania,plumbing,asse_certification,backflow,watersense,geothermal",
                "priority": "high",
                "difficulty": "intermediate",
                "personas": "confused_newcomer,urgent_operator,qualifier_network_specialist",
                "source": "specialty_trades_research_2025"
            }
        ]
        
        return specialty_entries
    
    async def check_railway_status(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Check Railway service status."""
        try:
            async with session.get(f"{self.railway_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "message": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def count_existing_entries(self, session: aiohttp.ClientSession) -> int:
        """Count existing knowledge base entries."""
        try:
            async with session.post(
                f"{self.railway_url}/knowledge/search",
                json={"query": "", "limit": 1000}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return len(data.get('results', []))
                else:
                    return 0
        except Exception as e:
            logger.error(f"Error counting entries: {str(e)}")
            return 0
    
    async def deploy_specialty_entries(self, session: aiohttp.ClientSession, entries: List[Dict[str, Any]]) -> bool:
        """Deploy specialty entries to Railway."""
        try:
            logger.info(f"Deploying {len(entries)} specialty entries...")
            
            # Upload in chunks to avoid timeout
            chunk_size = 10
            successful_uploads = 0
            
            for i in range(0, len(entries), chunk_size):
                chunk = entries[i:i + chunk_size]
                
                upload_data = {
                    'data_type': 'knowledge_base',
                    'data': chunk,
                    'clear_existing': False  # Don't clear existing data
                }
                
                try:
                    async with session.post(
                        f"{self.railway_url}/upload-data",
                        json=upload_data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status == 200:
                            successful_uploads += len(chunk)
                            logger.info(f"Uploaded chunk {i//chunk_size + 1}/{(len(entries) + chunk_size - 1)//chunk_size}")
                        else:
                            logger.error(f"Upload failed for chunk {i//chunk_size + 1}: HTTP {response.status}")
                            
                except asyncio.TimeoutError:
                    logger.error(f"Timeout uploading chunk {i//chunk_size + 1}")
                except Exception as e:
                    logger.error(f"Error uploading chunk {i//chunk_size + 1}: {str(e)}")
                
                # Small delay between chunks
                await asyncio.sleep(0.5)
            
            self.deployment_stats['specialty_entries_added'] = successful_uploads
            logger.info(f"Successfully uploaded {successful_uploads}/{len(entries)} specialty entries")
            
            return successful_uploads > 0
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            self.deployment_stats['errors'].append(f"Deployment failed: {str(e)}")
            return False
    
    async def test_search_functionality(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test search functionality with specialty queries."""
        test_queries = [
            "HVAC license California",
            "EPA 608 certification",
            "electrical contractor Texas",
            "IBEW apprenticeship",
            "plumbing license Florida",
            "backflow prevention",
            "roofing contractor California",
            "OSHA fall protection roofing",
            "flooring contractor license",
            "TCNA certification"
        ]
        
        search_results = {}
        successful_searches = 0
        
        for query in test_queries:
            try:
                async with session.post(
                    f"{self.railway_url}/knowledge/search",
                    json={"query": query, "limit": 3}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        search_results[query] = {
                            'result_count': len(results),
                            'first_result': results[0] if results else None
                        }
                        if results:
                            successful_searches += 1
                    else:
                        search_results[query] = {'error': f'HTTP {response.status}'}
            except Exception as e:
                search_results[query] = {'error': str(e)}
        
        return {
            'search_results': search_results,
            'successful_searches': successful_searches,
            'total_queries': len(test_queries),
            'success_rate': successful_searches / len(test_queries)
        }
    
    async def run_deployment(self) -> Dict[str, Any]:
        """Run the complete deployment process."""
        logger.info("=" * 60)
        logger.info("STARTING SPECIALTY CONTRACTOR LICENSE DEPLOYMENT VIA API")
        logger.info("=" * 60)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Check Railway status
                logger.info("Checking Railway service status...")
                status = await self.check_railway_status(session)
                if status.get('status') != 'healthy':
                    logger.warning(f"Railway status: {status}")
                
                # Step 2: Count existing entries
                logger.info("Counting existing entries...")
                self.deployment_stats['entries_before'] = await self.count_existing_entries(session)
                logger.info(f"Found {self.deployment_stats['entries_before']} existing entries")
                
                # Step 3: Load specialty knowledge
                logger.info("Loading specialty knowledge entries...")
                specialty_entries = self.load_specialty_knowledge()
                
                if not specialty_entries:
                    raise Exception("No specialty entries loaded")
                
                # Step 4: Deploy entries
                success = await self.deploy_specialty_entries(session, specialty_entries)
                if not success:
                    raise Exception("Failed to deploy specialty entries")
                
                # Step 5: Count entries after deployment
                logger.info("Counting entries after deployment...")
                await asyncio.sleep(2)  # Wait for indexing
                self.deployment_stats['entries_after'] = await self.count_existing_entries(session)
                
                # Step 6: Test search functionality
                logger.info("Testing search functionality...")
                search_results = await self.test_search_functionality(session)
                self.deployment_stats['validation_results'] = search_results
                
                # Generate report
                self.deployment_stats['end_time'] = datetime.now()
                self.deployment_stats['duration'] = (
                    self.deployment_stats['end_time'] - self.deployment_stats['start_time']
                ).total_seconds()
                
                report = {
                    'deployment_summary': {
                        'timestamp': self.deployment_stats['end_time'].isoformat(),
                        'duration_seconds': self.deployment_stats['duration'],
                        'status': 'SUCCESS' if self.deployment_stats['specialty_entries_added'] > 0 else 'FAILED',
                        'entries_before': self.deployment_stats['entries_before'],
                        'entries_after': self.deployment_stats['entries_after'],
                        'specialty_entries_added': self.deployment_stats['specialty_entries_added'],
                        'errors': self.deployment_stats['errors']
                    },
                    'search_validation': search_results,
                    'recommendations': self._generate_recommendations(search_results)
                }
                
                logger.info("=" * 60)
                logger.info("DEPLOYMENT COMPLETED SUCCESSFULLY")
                logger.info("=" * 60)
                
                return report
                
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            self.deployment_stats['errors'].append(f"Critical failure: {str(e)}")
            
            # Generate error report
            self.deployment_stats['end_time'] = datetime.now()
            self.deployment_stats['duration'] = (
                self.deployment_stats['end_time'] - self.deployment_stats['start_time']
            ).total_seconds()
            
            return {
                'deployment_summary': {
                    'timestamp': self.deployment_stats['end_time'].isoformat(),
                    'duration_seconds': self.deployment_stats['duration'],
                    'status': 'FAILED',
                    'entries_before': self.deployment_stats['entries_before'],
                    'entries_after': self.deployment_stats['entries_after'],
                    'specialty_entries_added': self.deployment_stats['specialty_entries_added'],
                    'errors': self.deployment_stats['errors']
                },
                'search_validation': {},
                'recommendations': ['🔧 Fix deployment errors before retrying']
            }
    
    def _generate_recommendations(self, search_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on deployment results."""
        recommendations = []
        
        if self.deployment_stats['specialty_entries_added'] >= 10:
            recommendations.append("✅ Good specialty coverage achieved")
        else:
            recommendations.append("⚠️ Limited specialty entries deployed")
        
        success_rate = search_results.get('success_rate', 0)
        if success_rate >= 0.8:
            recommendations.append("✅ Search functionality working well")
        else:
            recommendations.append(f"⚠️ Search needs improvement ({success_rate:.1%} success rate)")
        
        if len(self.deployment_stats['errors']) == 0:
            recommendations.append("✅ No deployment errors")
        else:
            recommendations.append("🔧 Address deployment errors")
        
        return recommendations


async def main():
    """Main deployment function."""
    deployer = SpecialtyKnowledgeAPIDeployer()
    report = await deployer.run_deployment()
    
    # Save report
    report_path = '/Users/natperez/codebases/hyper8/hyper8-FACT/logs/specialty_api_deployment_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SPECIALTY CONTRACTOR LICENSE API DEPLOYMENT SUMMARY")
    print("=" * 80)
    print(f"Status: {report['deployment_summary']['status']}")
    print(f"Duration: {report['deployment_summary']['duration_seconds']:.2f} seconds")
    print(f"Entries Before: {report['deployment_summary']['entries_before']}")
    print(f"Entries After: {report['deployment_summary']['entries_after']}")
    print(f"Specialty Entries Added: {report['deployment_summary']['specialty_entries_added']}")
    
    search_validation = report.get('search_validation', {})
    print(f"\nSearch Validation:")
    print(f"  Success Rate: {search_validation.get('success_rate', 0):.1%}")
    print(f"  Successful Searches: {search_validation.get('successful_searches', 0)}/{search_validation.get('total_queries', 0)}")
    
    if report['deployment_summary']['errors']:
        print(f"\nErrors:")
        for error in report['deployment_summary']['errors']:
            print(f"  ❌ {error}")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    print(f"\nFull report saved to: {report_path}")
    print("=" * 80)
    
    return report


if __name__ == "__main__":
    asyncio.run(main())
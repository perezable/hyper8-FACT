#!/usr/bin/env python3
"""
Add specific Georgia entries for common query patterns to improve accuracy.
"""

import json

# Load existing data
with open('data/knowledge_export_fixed.json', 'r') as f:
    data = json.load(f)

# Find the highest ID
max_id = max(entry['id'] for entry in data['knowledge_base'])
next_id = max_id + 1

# Add specific Georgia entries for common queries
new_entries = [
    {
        "id": next_id,
        "question": "How much does a Georgia contractor license cost?",
        "answer": "Georgia contractor license costs: Application fee is $200. Total costs range from $300-400 including all fees. Additionally, a $10,000 surety bond is required for general contractors. Exam fees are separate. Total investment typically ranges from $2,500-3,500 including preparation and all requirements.",
        "category": "state_licensing_requirements",
        "state": "GA",
        "tags": "georgia,cost,price,fees,license_cost,application_fee",
        "priority": "high",
        "difficulty": "basic",
        "personas": "confused_newcomer,qualifier_network_specialist",
        "source": "georgia_specific_additions"
    },
    {
        "id": next_id + 1,
        "question": "What is the Georgia contractor license application process?",
        "answer": "Georgia contractor license application process: 1) Submit application with $200 fee, 2) Provide proof of 4 years experience or equivalent education, 3) Pass Business & Law exam (110 questions, 4 hours), 4) Pass Trade exam (110 questions, 4 hours), 5) Obtain $10,000 surety bond, 6) Complete background check. Process typically takes 30-45 days.",
        "category": "state_licensing_requirements",
        "state": "GA",
        "tags": "georgia,application,process,steps,how_to_apply",
        "priority": "high",
        "difficulty": "basic",
        "personas": "confused_newcomer,urgent_operator",
        "source": "georgia_specific_additions"
    },
    {
        "id": next_id + 2,
        "question": "Georgia license cost",
        "answer": "Georgia contractor license costs: $200 application fee, $300-400 total fees, $10,000 surety bond required. Total investment including preparation: $2,500-3,500.",
        "category": "state_licensing_requirements",
        "state": "GA",
        "tags": "georgia,cost,price,fees",
        "priority": "high",
        "difficulty": "basic",
        "personas": "confused_newcomer",
        "source": "georgia_specific_additions"
    },
    {
        "id": next_id + 3,
        "question": "Georgia exam requirements",
        "answer": "Georgia contractor exam requirements: Two exams required - Business & Law exam (110 questions, 4 hours) and Trade exam (110 questions, 4 hours). Both require 70% passing score. Exams cover business practices, law, safety, and trade-specific knowledge.",
        "category": "exam_preparation_testing",
        "state": "GA",
        "tags": "georgia,exam,test,requirements,passing_score",
        "priority": "high",
        "difficulty": "basic",
        "personas": "confused_newcomer,overwhelmed_veteran",
        "source": "georgia_specific_additions"
    },
    {
        "id": next_id + 4,
        "question": "Georgia bond requirements",
        "answer": "Georgia contractor bond requirements: General contractors must obtain a $10,000 surety bond. The bond protects consumers from contractor default or failure to meet obligations. Bond costs typically 1-3% of bond amount annually ($100-300/year) based on credit score.",
        "category": "insurance_bonding",
        "state": "GA",
        "tags": "georgia,bond,surety,requirements,insurance",
        "priority": "high",
        "difficulty": "basic",
        "personas": "confused_newcomer,qualifier_network_specialist",
        "source": "georgia_specific_additions"
    },
    {
        "id": next_id + 5,
        "question": "Georgia experience requirements",
        "answer": "Georgia contractor experience requirements: 4 years of verifiable experience in the construction industry OR equivalent education (bachelor's degree in construction-related field counts as 2 years, associate's degree counts as 1 year). Experience must be documented with tax records, W-2s, or employer verification.",
        "category": "state_licensing_requirements",
        "state": "GA",
        "tags": "georgia,experience,requirements,qualification,years",
        "priority": "high",
        "difficulty": "basic",
        "personas": "confused_newcomer,overwhelmed_veteran",
        "source": "georgia_specific_additions"
    },
    {
        "id": next_id + 6,
        "question": "cost in Georgia",
        "answer": "Georgia contractor license costs breakdown: $200 application fee, $300-400 total processing fees, $10,000 surety bond (costs $100-300/year), exam fees, and preparation materials. Total initial investment: $2,500-3,500.",
        "category": "financial_planning_roi",
        "state": "GA",
        "tags": "georgia,cost,price,investment,fees",
        "priority": "high",
        "difficulty": "basic",
        "personas": "confused_newcomer,qualifier_network_specialist",
        "source": "georgia_specific_additions"
    },
    {
        "id": next_id + 7,
        "question": "application Georgia",
        "answer": "Georgia contractor license application: Submit online or mail application with $200 fee, provide experience documentation (4 years required), pass both exams (Business & Law, Trade), obtain $10,000 bond, complete background check. Processing time: 30-45 days.",
        "category": "state_licensing_requirements",
        "state": "GA",
        "tags": "georgia,application,apply,process",
        "priority": "high",
        "difficulty": "basic",
        "personas": "confused_newcomer,urgent_operator",
        "source": "georgia_specific_additions"
    }
]

# Add new entries to knowledge base
data['knowledge_base'].extend(new_entries)
data['metadata']['total_entries'] = len(data['knowledge_base'])

# Save updated data
with open('data/knowledge_export_enhanced.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"✅ Added {len(new_entries)} Georgia-specific entries")
print(f"   Total entries now: {len(data['knowledge_base'])}")
print(f"   New IDs: {next_id} to {next_id + len(new_entries) - 1}")

# Count Georgia entries
ga_count = sum(1 for entry in data['knowledge_base'] if entry.get('state') == 'GA')
print(f"   Total Georgia entries: {ga_count}")
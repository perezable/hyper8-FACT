#!/usr/bin/env python3

import json

def extract_questions_by_score(json_file, max_score=69):
    """Extract questions with scores at or below max_score"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    low_scoring = []
    for result in data.get('all_results', []):  # Changed from 'results' to 'all_results'
        if result.get('score', 0) <= max_score:
            low_scoring.append({
                'question_id': result.get('question_id'),
                'question': result.get('question'),
                'persona': result.get('persona'),
                'category': result.get('category'),
                'score': result.get('score')
            })
    
    return low_scoring

if __name__ == "__main__":
    json_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/fact_test_200_results_20250911_223949.json"
    low_scoring = extract_questions_by_score(json_file, 69)
    
    print(f"Found {len(low_scoring)} questions scoring 69 or below:")
    print()
    
    # Group by persona and category for analysis
    personas = {}
    categories = {}
    
    for q in low_scoring:
        persona = q['persona']
        category = q['category']
        
        if persona not in personas:
            personas[persona] = []
        personas[persona].append(q)
        
        if category not in categories:
            categories[category] = []
        categories[category].append(q)
    
    print("=== BY PERSONA ===")
    for persona, questions in personas.items():
        print(f"\n{persona.upper()} ({len(questions)} questions):")
        for q in questions:
            print(f"  [{q['score']}] {q['question']}")
    
    print("\n=== BY CATEGORY ===")
    for category, questions in categories.items():
        print(f"\n{category.upper()} ({len(questions)} questions):")
        for q in questions:
            print(f"  [{q['score']}] {q['question']}")
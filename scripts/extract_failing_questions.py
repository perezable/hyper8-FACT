#!/usr/bin/env python3

import json
import sys

def extract_failing_questions(json_file):
    """Extract questions with scores below 70"""
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    failing_questions = []
    for result in data.get('results', []):
        if result.get('score', 0) < 70:
            failing_questions.append({
                'question_id': result.get('question_id'),
                'question': result.get('question'),
                'persona': result.get('persona'),
                'category': result.get('category'),
                'score': result.get('score')
            })
    
    return failing_questions

if __name__ == "__main__":
    json_file = "/Users/natperez/codebases/hyper8/hyper8-FACT/fact_test_200_results_20250911_223949.json"
    failing = extract_failing_questions(json_file)
    
    print(f"Found {len(failing)} questions scoring below 70:")
    print()
    
    for q in failing:
        print(f"ID: {q['question_id']}")
        print(f"Question: {q['question']}")
        print(f"Persona: {q['persona']}")
        print(f"Category: {q['category']}")
        print(f"Score: {q['score']}")
        print("-" * 50)
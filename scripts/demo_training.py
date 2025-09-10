#!/usr/bin/env python3
"""
Demonstration of the FACT system's training capabilities.
Shows how the system learns from feedback to improve accuracy.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from retrieval.enhanced_search import EnhancedRetriever
from training.knowledge_trainer import KnowledgeTrainer


async def demo_training():
    """Demonstrate the training capabilities."""
    print("🧠 FACT System Training Demonstration")
    print("=" * 70)
    
    # Initialize components
    retriever = EnhancedRetriever()
    await retriever.initialize()
    
    trainer = KnowledgeTrainer(retriever)
    
    print(f"\n📚 Loaded {len(retriever.in_memory_index.entries)} knowledge entries")
    
    # Simulate user interactions with feedback
    test_interactions = [
        {
            "query": "What are the requirements for a contractor license in Nevada?",
            "feedback": "correct",
            "explanation": "User confirmed the Nevada requirements were correct"
        },
        {
            "query": "How much does a surety bond cost?",
            "feedback": "partial",
            "explanation": "Answer was helpful but missing state-specific details"
        },
        {
            "query": "What's the ROI on getting licensed?",
            "feedback": "incorrect",
            "expected": "First project typically returns 3-10x the licensing investment",
            "explanation": "System didn't understand 'ROI' abbreviation well"
        },
        {
            "query": "Can I DIY the licensing process?",
            "feedback": "correct",
            "explanation": "Found the DIY vs professional comparison"
        },
        {
            "query": "What if I flunk the test?",
            "feedback": "incorrect",
            "expected": "You can retake the exam after a waiting period, additional fees apply",
            "explanation": "System didn't understand 'flunk' as synonym for 'fail'"
        }
    ]
    
    print("\n🎯 Running Training Interactions:")
    print("-" * 70)
    
    for interaction in test_interactions:
        query = interaction["query"]
        
        # Perform search
        results = await retriever.search(query, limit=1)
        
        if results:
            result = results[0]
            result_dict = {
                'answer': result.answer,
                'score': result.score,
                'category': result.category,
                'match_type': result.match_type,
                'confidence': result.confidence
            }
            
            print(f"\n📝 Query: '{query}'")
            print(f"   Result: {result.question[:50]}...")
            print(f"   Score: {result.score:.2f}, Type: {result.match_type}")
        else:
            result_dict = {
                'answer': '',
                'score': 0.0,
                'match_type': 'none',
                'confidence': 0.0
            }
            print(f"\n📝 Query: '{query}'")
            print(f"   Result: No results found")
        
        # Provide feedback
        feedback = interaction["feedback"]
        expected = interaction.get("expected")
        
        await trainer.train_from_feedback(query, result_dict, feedback, expected)
        
        print(f"   Feedback: {feedback} - {interaction['explanation']}")
        
        if expected:
            print(f"   Expected: {expected[:50]}...")
    
    # Show training statistics
    print("\n📊 Training Statistics:")
    print("-" * 70)
    
    stats = trainer.get_training_stats()
    print(f"Total Examples: {stats['total_examples']}")
    print(f"Correct: {stats['correct']}")
    print(f"Incorrect: {stats['incorrect']}")
    print(f"Partial: {stats['partial']}")
    print(f"Current Accuracy: {stats['accuracy']:.1%}")
    print(f"Target Accuracy: {stats['target_accuracy']:.1%}")
    
    # Show learned patterns
    print(f"\n🔍 Learned Patterns:")
    print(f"Synonyms Learned: {stats['learned_synonyms']}")
    print(f"Query Patterns: {stats['learned_patterns']}")
    
    # Show learned synonyms
    if trainer.synonym_mappings:
        print("\n📖 Sample Learned Synonyms:")
        for word, synonyms in list(trainer.synonym_mappings.items())[:5]:
            print(f"   '{word}' → {list(synonyms)}")
    
    # Show weight adjustments
    print(f"\n⚖️ Weight Adjustments:")
    for weight_type, value in stats['current_weights'].items():
        print(f"   {weight_type}: {value:.3f}")
    
    # Get improvement suggestions
    suggestions = await trainer.suggest_improvements()
    
    if suggestions:
        print("\n💡 Improvement Suggestions:")
        for i, suggestion in enumerate(suggestions[:3], 1):
            print(f"{i}. {suggestion['suggestion']}")
            if 'examples' in suggestion:
                print(f"   Examples: {suggestion['examples'][:2]}")
    
    # Trigger retraining
    print("\n🔄 Applying learned patterns through retraining...")
    await trainer.retrain()
    
    # Test improvement on previously failed queries
    print("\n✅ Testing Improvement on Previously Failed Queries:")
    print("-" * 70)
    
    improved_queries = [
        "What's the ROI on getting licensed?",
        "What if I flunk the test?"
    ]
    
    for query in improved_queries:
        results = await retriever.search(query, limit=1)
        
        if results:
            result = results[0]
            print(f"\n📝 Query: '{query}'")
            print(f"   New Result: {result.question[:50]}...")
            print(f"   New Score: {result.score:.2f} (Type: {result.match_type})")
            
            # Check if improvement happened
            if result.score > 0.3:
                print(f"   ✅ Improved! System learned from feedback.")
            else:
                print(f"   ⚠️ Still needs more training examples.")
        else:
            print(f"\n📝 Query: '{query}'")
            print(f"   ❌ Still no results - needs more training")
    
    # Export training data
    export_path = "data/demo_training_export.json"
    await trainer.export_training_data(export_path)
    print(f"\n💾 Training data exported to: {export_path}")
    
    # Summary
    print("\n" + "=" * 70)
    print("🎓 Training Demonstration Complete!")
    print("\nKey Training Features Demonstrated:")
    print("✅ Learning from user feedback (correct/incorrect/partial)")
    print("✅ Synonym discovery from successful matches")
    print("✅ Weight adjustment based on performance")
    print("✅ Pattern recognition from query types")
    print("✅ Improvement suggestions generation")
    print("✅ Export/import training data for persistence")
    print("\nThe system can continuously improve through:")
    print("• API feedback endpoints (/training/feedback)")
    print("• Auto-training from high-confidence matches")
    print("• Manual retraining triggers")
    print("• Imported training data from other deployments")


if __name__ == "__main__":
    asyncio.run(demo_training())
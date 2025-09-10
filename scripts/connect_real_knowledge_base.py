#!/usr/bin/env python3
"""
Connect the REAL knowledge base to the VAPI webhook.
Replace mock data with actual enhanced retriever search.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def show_changes_needed():
    """Show exactly what needs to be changed."""
    
    print("🎯 CONNECTING REAL KNOWLEDGE BASE TO VAPI")
    print("=" * 70)
    
    print("\n📍 CURRENT PROBLEM:")
    print("- VAPI webhook uses MOCK/FAKE data")
    print("- Real knowledge base with 400+ Q&A pairs is NOT connected")
    print("- Enhanced retriever (96.7% accuracy) exists but isn't used by VAPI")
    
    print("\n✅ SOLUTION:")
    print("Replace the mock search_knowledge_base() function in vapi_webhook.py")
    print("with a call to the real enhanced retriever.")
    
    print("\n📝 CHANGES NEEDED IN /src/api/vapi_webhook.py:")
    print("-" * 70)
    
    print("""
REPLACE THIS (lines 82-129):
```python
async def search_knowledge_base(query: str, state: Optional[str] = None, 
                               category: Optional[str] = None, 
                               limit: int = 3) -> Dict[str, Any]:
    # Mock implementation - replace with actual database query
    mock_results = {
        "georgia": { ... },  # FAKE DATA
        "exam": { ... },     # FAKE DATA
        "cost": { ... }      # FAKE DATA
    }
    # ... returns mock data ...
```

WITH THIS:
```python
async def search_knowledge_base(query: str, state: Optional[str] = None, 
                               category: Optional[str] = None, 
                               limit: int = 3) -> Dict[str, Any]:
    '''Search the REAL knowledge base using enhanced retriever.'''
    
    # Import the web server's enhanced retriever
    from src.web_server import _enhanced_retriever, _driver
    
    # Check if system is initialized
    if not _enhanced_retriever:
        # Fallback to basic SQL search if enhanced retriever not ready
        if _driver and _driver.database_manager:
            # Use SQL query directly
            sql = f'''
                SELECT question, answer, category, state, confidence 
                FROM knowledge_base 
                WHERE question LIKE '%{query}%' OR answer LIKE '%{query}%'
                LIMIT {limit}
            '''
            result = await _driver.database_manager.execute_query(sql)
            
            if result.rows:
                row = result.rows[0]
                return {
                    "answer": row["answer"],
                    "category": row.get("category", "general"),
                    "confidence": row.get("confidence", 0.8),
                    "source": "knowledge_base",
                    "state": state,
                    "voice_optimized": True
                }
    else:
        # Use the REAL enhanced retriever (96.7% accuracy)
        search_results = await _enhanced_retriever.search(
            query=query,
            category=category,
            state=state,
            limit=limit
        )
        
        if search_results:
            best_result = search_results[0]
            return {
                "answer": best_result.answer,
                "category": best_result.category or "general",
                "confidence": best_result.score,
                "source": best_result.source or "enhanced_search",
                "state": state,
                "voice_optimized": True,
                "match_type": best_result.match_type
            }
    
    # Default response if no results
    return {
        "answer": "I can help you with contractor licensing. What specific information do you need?",
        "category": "general",
        "confidence": 0.5,
        "source": "default",
        "voice_optimized": True
    }
```
""")
    
    print("\n🚀 DEPLOYMENT STEPS:")
    print("1. Make the code change above in vapi_webhook.py")
    print("2. Test locally to ensure it works")
    print("3. Commit and push to repository")
    print("4. Deploy to Railway (automatic or manual)")
    print("5. Test VAPI calls to verify real data is returned")
    
    print("\n⚠️ IMPORTANT:")
    print("- The knowledge base must be loaded first (CSV upload)")
    print("- Enhanced retriever needs to be initialized")
    print("- Railway deployment must have the knowledge data")
    
    print("\n📊 EXPECTED RESULT:")
    print("Instead of returning fake Georgia/exam/cost data,")
    print("VAPI will get REAL answers from your 400+ Q&A knowledge base!")

if __name__ == "__main__":
    show_changes_needed()
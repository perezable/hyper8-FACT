#!/usr/bin/env python3
"""
Test Groq API integration locally
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from groq import Groq

def test_groq_api():
    """Test basic Groq API functionality"""
    
    print("\n" + "="*60)
    print("🧪 TESTING GROQ API INTEGRATION")
    print("="*60)
    
    # Get API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        # Try to load from .env
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    print(f"✅ GROQ_API_KEY found (length: {len(api_key)})")
    
    try:
        # Create client
        client = Groq(api_key=api_key)
        print("✅ Groq client created")
        
        # Test simple query
        print("\n📝 Testing simple query...")
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant for contractor licensing questions."
                },
                {
                    "role": "user",
                    "content": "What states accept NASCLA certification?"
                }
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        print("✅ Response received!")
        print(f"\nModel: {response.model}")
        print(f"Response: {response.choices[0].message.content[:200]}...")
        print(f"Tokens used: {response.usage.total_tokens}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_groq_adapter():
    """Test the Groq adapter with Anthropic-compatible interface"""
    
    print("\n" + "="*60)
    print("🔧 TESTING GROQ ADAPTER")
    print("="*60)
    
    try:
        from core.groq_client import GroqAdapter
        
        # Load API key
        from dotenv import load_dotenv
        load_dotenv()
        
        adapter = GroqAdapter()
        print("✅ Groq adapter created")
        
        # Test with Anthropic-style call
        response = adapter.messages.create(
            model="claude-3-haiku",  # Will be mapped to Groq model
            messages=[
                {"role": "user", "content": "What is the cost of a Florida contractor license?"}
            ],
            system="You are a helpful assistant for contractor licensing.",
            max_tokens=200
        )
        
        print("✅ Adapter response received!")
        print(f"\nResponse type: {type(response)}")
        print(f"Response content: {str(response)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test basic Groq API
    success1 = test_groq_api()
    
    # Test adapter
    success2 = test_groq_adapter()
    
    if success1 and success2:
        print("\n✅ All tests passed! Groq integration is working.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
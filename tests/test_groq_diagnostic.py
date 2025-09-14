#!/usr/bin/env python3
"""
Diagnostic test for Groq API configuration
Tests local setup to ensure everything works before Railway deployment
"""

import os
import sys
from pathlib import Path

# Add src to path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

def diagnose_groq_setup():
    """Run comprehensive diagnostics on Groq setup"""
    
    print("\n" + "="*60)
    print("🔍 GROQ API DIAGNOSTIC TEST")
    print("="*60)
    
    # 1. Check environment variable
    print("\n1. Environment Variable Check:")
    print("-" * 40)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"✅ GROQ_API_KEY found (length: {len(groq_key)})")
        print(f"   First 10 chars: {groq_key[:10]}...")
    else:
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    # 2. Test Groq client import
    print("\n2. Import Check:")
    print("-" * 40)
    
    try:
        from groq import Groq
        print("✅ Groq package imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Groq: {e}")
        return False
    
    # 3. Test client creation
    print("\n3. Client Creation:")
    print("-" * 40)
    
    try:
        client = Groq(api_key=groq_key)
        print("✅ Groq client created successfully")
    except Exception as e:
        print(f"❌ Failed to create client: {e}")
        return False
    
    # 4. Test API call with openai/gpt-oss-120b
    print("\n4. API Call Test (openai/gpt-oss-120b):")
    print("-" * 40)
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'test successful' if you can hear me."}
            ],
            max_tokens=50,
            temperature=0.1
        )
        
        content = response.choices[0].message.content
        print(f"✅ API call successful")
        print(f"   Model: {response.model}")
        print(f"   Response: {content}")
        print(f"   Tokens: {response.usage.total_tokens}")
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        
        # Try alternative models
        print("\n   Trying alternative models...")
        
        models_to_try = [
            "llama-3.1-70b-versatile",
            "mixtral-8x7b-32768",
            "llama3-70b-8192"
        ]
        
        for model in models_to_try:
            try:
                print(f"\n   Testing {model}...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "test"}
                    ],
                    max_tokens=10
                )
                print(f"   ✅ {model} works!")
                break
            except Exception as e:
                error_msg = str(e)
                if "decommissioned" in error_msg.lower():
                    print(f"   ❌ {model} has been decommissioned")
                else:
                    print(f"   ❌ {model} failed: {error_msg[:100]}")
        
        return False
    
    # 5. Test custom adapter
    print("\n5. Custom Adapter Test:")
    print("-" * 40)
    
    try:
        from core.groq_client import GroqAdapter
        
        adapter = GroqAdapter(api_key=groq_key)
        print("✅ GroqAdapter created successfully")
        
        # Test with adapter
        response = adapter.messages.create(
            model="claude-3-haiku",  # Will be mapped
            messages=[
                {"role": "user", "content": "What is 2+2?"}
            ],
            system="You are a math tutor.",
            max_tokens=50
        )
        
        print(f"✅ Adapter call successful")
        print(f"   Response: {str(response)[:100]}...")
        
    except Exception as e:
        print(f"❌ Adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. Test driver integration
    print("\n6. Driver Integration Test:")
    print("-" * 40)
    
    try:
        from core.driver import FACTDriver
        import asyncio
        
        async def test_driver():
            driver = FACTDriver()
            await driver.initialize()
            response = await driver.process_fact_query("What is NASCLA?")
            return response
        
        response = asyncio.run(test_driver())
        if response:
            print("✅ Driver integration successful")
            print(f"   Response length: {len(response)} chars")
        else:
            print("⚠️  Driver returned empty response")
        
    except Exception as e:
        print(f"❌ Driver test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("✅ ALL DIAGNOSTICS PASSED!")
    print("="*60)
    print("\nThe Groq integration is properly configured locally.")
    print("If Railway is still failing, check:")
    print("1. GROQ_API_KEY is set in Railway environment variables")
    print("2. Railway has restarted after setting the variable")
    print("3. Check Railway logs for specific initialization errors")
    
    return True

if __name__ == "__main__":
    success = diagnose_groq_setup()
    exit(0 if success else 1)
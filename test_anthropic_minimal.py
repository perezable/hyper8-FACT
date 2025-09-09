#!/usr/bin/env python3
"""
Minimal test script to diagnose Anthropic client proxy injection issue.
Run this directly to test various initialization methods.
"""

import os
import sys
import json

def test_anthropic_client():
    """Test different Anthropic client initialization methods."""
    
    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
    
    if not api_key or api_key == "your_anthropic_api_key_here":
        print("ERROR: Valid ANTHROPIC_API_KEY not found in environment")
        return
    
    print("=" * 60)
    print("Testing Anthropic Client Initialization")
    print("=" * 60)
    
    # 1. Test environment variables
    print("\n1. CHECKING ENVIRONMENT VARIABLES:")
    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 
                  'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
    
    found_proxies = False
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"   {var} = {value}")
            found_proxies = True
    
    if not found_proxies:
        print("   No proxy environment variables found")
    
    # 2. Test direct import
    print("\n2. TESTING DIRECT IMPORT:")
    try:
        import anthropic
        print(f"   anthropic module location: {anthropic.__file__}")
        print(f"   anthropic version: {getattr(anthropic, '__version__', 'unknown')}")
    except Exception as e:
        print(f"   ERROR importing anthropic: {e}")
        return
    
    # 3. Test client initialization with no arguments except API key
    print("\n3. TESTING BASIC CLIENT INITIALIZATION:")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("   ✓ Basic client initialization succeeded")
    except Exception as e:
        print(f"   ✗ Basic client initialization failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check if the error mentions 'proxies'
        if 'proxies' in str(e).lower():
            print("\n   PROXY INJECTION DETECTED!")
            print("   Something is injecting proxy arguments into the client.")
    
    # 4. Test with httpx client
    print("\n4. TESTING WITH HTTPX CLIENT:")
    try:
        import httpx
        print(f"   httpx version: {httpx.__version__}")
        
        # Create httpx client with explicit no proxy
        http_client = httpx.Client(
            proxies=None,
            trust_env=False
        )
        
        client = anthropic.Anthropic(
            api_key=api_key,
            http_client=http_client
        )
        print("   ✓ Client with httpx succeeded")
    except Exception as e:
        print(f"   ✗ Client with httpx failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    # 5. Test with environment cleared
    print("\n5. TESTING WITH CLEARED ENVIRONMENT:")
    
    # Save and clear proxy vars
    saved_env = {}
    for var in proxy_vars:
        if var in os.environ:
            saved_env[var] = os.environ.pop(var)
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("   ✓ Client with cleared environment succeeded")
    except Exception as e:
        print(f"   ✗ Client with cleared environment failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    finally:
        # Restore environment
        for var, value in saved_env.items():
            os.environ[var] = value
    
    # 6. Check for monkey patching
    print("\n6. CHECKING FOR MONKEY PATCHING:")
    try:
        import inspect
        
        # Check Anthropic class __init__
        init_signature = inspect.signature(anthropic.Anthropic.__init__)
        print(f"   Anthropic.__init__ parameters: {list(init_signature.parameters.keys())}")
        
        # Check if 'proxies' is in the signature
        if 'proxies' in init_signature.parameters:
            print("   WARNING: 'proxies' parameter found in Anthropic.__init__!")
            print("   This suggests the module has been patched.")
    except Exception as e:
        print(f"   Could not inspect signature: {e}")
    
    # 7. Test actual API call
    print("\n7. TESTING ACTUAL API CALL:")
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "Say 'test' in one word"}],
            max_tokens=10
        )
        print("   ✓ API call succeeded")
        if hasattr(response, 'content') and response.content:
            for block in response.content:
                if hasattr(block, 'text'):
                    print(f"   Response: {block.text}")
    except Exception as e:
        print(f"   ✗ API call failed: {e}")
        print(f"   Error type: {type(e).__name__}")
    
    print("\n" + "=" * 60)
    print("DIAGNOSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_anthropic_client()
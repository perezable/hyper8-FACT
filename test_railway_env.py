#!/usr/bin/env python3
"""
Test script that simulates Railway environment to diagnose proxy injection.
This script should be run in Railway to understand what's happening.
"""

import os
import sys
import traceback

def diagnose_railway_environment():
    """Diagnose the Railway environment and Anthropic client issues."""
    
    print("=" * 70)
    print("RAILWAY ENVIRONMENT DIAGNOSTIC")
    print("=" * 70)
    
    # 1. Check Python version and path
    print("\n1. PYTHON ENVIRONMENT:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Python path: {sys.path[:3]}...")
    
    # 2. Check all environment variables
    print("\n2. ALL ENVIRONMENT VARIABLES:")
    env_vars = dict(os.environ)
    
    # Group by category
    proxy_vars = {}
    railway_vars = {}
    api_vars = {}
    other_vars = {}
    
    for key, value in env_vars.items():
        # Mask sensitive values
        if 'KEY' in key or 'SECRET' in key or 'PASSWORD' in key or 'TOKEN' in key:
            display_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
        else:
            display_value = value
            
        if 'PROXY' in key.upper():
            proxy_vars[key] = display_value
        elif 'RAILWAY' in key:
            railway_vars[key] = display_value
        elif 'API' in key or 'ANTHROPIC' in key or 'ARCADE' in key:
            api_vars[key] = display_value
        else:
            other_vars[key] = display_value
    
    if proxy_vars:
        print("\n   PROXY VARIABLES:")
        for key, value in proxy_vars.items():
            print(f"      {key} = {value}")
    
    if railway_vars:
        print("\n   RAILWAY VARIABLES:")
        for key, value in railway_vars.items():
            print(f"      {key} = {value}")
    
    if api_vars:
        print("\n   API VARIABLES:")
        for key, value in api_vars.items():
            print(f"      {key} = {value}")
    
    # 3. Check installed packages
    print("\n3. CHECKING INSTALLED PACKAGES:")
    try:
        import pkg_resources
        packages = ['anthropic', 'httpx', 'httpcore', 'requests']
        for pkg in packages:
            try:
                version = pkg_resources.get_distribution(pkg).version
                print(f"   {pkg}: {version}")
            except:
                print(f"   {pkg}: NOT INSTALLED")
    except Exception as e:
        print(f"   Error checking packages: {e}")
    
    # 4. Import and inspect anthropic module
    print("\n4. INSPECTING ANTHROPIC MODULE:")
    try:
        import anthropic
        print(f"   Module location: {anthropic.__file__}")
        print(f"   Module version: {getattr(anthropic, '__version__', 'unknown')}")
        
        # Check for modifications
        import inspect
        
        # Get Anthropic class init signature
        init_signature = inspect.signature(anthropic.Anthropic.__init__)
        params = list(init_signature.parameters.keys())
        print(f"   Anthropic.__init__ parameters: {params}")
        
        if 'proxies' in params:
            print("   ⚠️  WARNING: 'proxies' parameter detected in Anthropic.__init__!")
            print("   This indicates the module has been modified or patched!")
        
        # Check for httpx modifications
        import httpx
        client_signature = inspect.signature(httpx.Client.__init__)
        httpx_params = list(client_signature.parameters.keys())
        if 'proxies' in httpx_params:
            print(f"   httpx.Client has 'proxies' parameter (expected)")
        
    except Exception as e:
        print(f"   Error inspecting anthropic: {e}")
        traceback.print_exc()
    
    # 5. Test different initialization methods
    print("\n5. TESTING ANTHROPIC CLIENT INITIALIZATION:")
    
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
    
    if not api_key:
        print("   No ANTHROPIC_API_KEY found - skipping client tests")
    else:
        print(f"   API key found (length: {len(api_key)})")
        
        # Test 1: Direct initialization
        print("\n   Test 1: Direct initialization")
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            print("      ✓ Success")
        except Exception as e:
            print(f"      ✗ Failed: {e}")
            if 'proxies' in str(e):
                print("      PROXY INJECTION CONFIRMED!")
        
        # Test 2: With cleared environment
        print("\n   Test 2: With cleared proxy environment")
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                         'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']
        saved = {}
        for var in proxy_env_vars:
            if var in os.environ:
                saved[var] = os.environ.pop(var)
        
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            print("      ✓ Success")
        except Exception as e:
            print(f"      ✗ Failed: {e}")
            if 'proxies' in str(e):
                print("      PROXY INJECTION STILL OCCURS!")
        finally:
            # Restore
            for var, val in saved.items():
                os.environ[var] = val
        
        # Test 3: With module reload
        print("\n   Test 3: With module reload")
        try:
            import importlib
            import anthropic
            importlib.reload(anthropic)
            client = anthropic.Anthropic(api_key=api_key)
            print("      ✓ Success")
        except Exception as e:
            print(f"      ✗ Failed: {e}")
    
    # 6. Check for Railway-specific modifications
    print("\n6. CHECKING FOR RAILWAY-SPECIFIC MODIFICATIONS:")
    
    # Check if there are any Railway-specific packages or patches
    railway_specific = []
    try:
        import pkg_resources
        for dist in pkg_resources.working_set:
            if 'railway' in dist.key.lower() or 'nixpacks' in dist.key.lower():
                railway_specific.append(f"{dist.key} ({dist.version})")
    except:
        pass
    
    if railway_specific:
        print("   Railway-specific packages found:")
        for pkg in railway_specific:
            print(f"      - {pkg}")
    else:
        print("   No Railway-specific packages detected")
    
    # 7. Summary and recommendations
    print("\n" + "=" * 70)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 70)
    
    if proxy_vars:
        print("\n⚠️  Proxy environment variables are set")
        print("   Recommendation: Clear these in Dockerfile or runtime")
    
    print("\nTo fix the issue, try:")
    print("1. Add to Dockerfile: ENV HTTP_PROXY='' HTTPS_PROXY=''")
    print("2. Use a wrapper script that clears proxy vars before running Python")
    print("3. Check Railway's build and runtime settings for proxy configuration")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    diagnose_railway_environment()
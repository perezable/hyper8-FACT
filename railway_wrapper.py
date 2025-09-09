#!/usr/bin/env python3
"""
Railway deployment wrapper that patches Anthropic client to prevent proxy injection.
This should be used as the main entry point in Railway.
"""

import os
import sys

def patch_anthropic_globally():
    """
    Globally patch the Anthropic client to prevent proxy injection.
    This must be done before any imports of the anthropic module.
    """
    # Clear all proxy environment variables
    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
        'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'
    ]
    
    print("Railway wrapper: Clearing proxy environment variables...")
    for var in proxy_vars:
        if var in os.environ:
            print(f"  Removing {var}")
            del os.environ[var]
    
    # Set NO_PROXY to everything
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    
    # Now import and patch anthropic
    print("Railway wrapper: Patching Anthropic client...")
    import anthropic
    
    # Save the original Anthropic class
    _OriginalAnthropic = anthropic.Anthropic
    
    # Create a patched version that filters out proxy parameters
    class PatchedAnthropic:
        """Patched Anthropic client that filters out proxy parameters."""
        
        def __init__(self, api_key=None, **kwargs):
            # Remove any proxy-related parameters
            proxy_params = ['proxies', 'proxy', 'http_proxy', 'https_proxy']
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in proxy_params}
            
            if filtered_kwargs != kwargs:
                removed = set(kwargs.keys()) - set(filtered_kwargs.keys())
                print(f"Railway wrapper: Filtered out parameters: {removed}")
            
            # Create the actual client
            if api_key:
                self._client = _OriginalAnthropic(api_key=api_key, **filtered_kwargs)
            else:
                self._client = _OriginalAnthropic(**filtered_kwargs)
        
        def __getattr__(self, name):
            return getattr(self._client, name)
        
        def __setattr__(self, name, value):
            if name == '_client':
                object.__setattr__(self, name, value)
            else:
                setattr(self._client, name, value)
    
    # Replace the Anthropic class globally
    anthropic.Anthropic = PatchedAnthropic
    print("Railway wrapper: Anthropic client patched successfully")

def main():
    """Run the main application with patched Anthropic."""
    print("=" * 60)
    print("Railway Deployment Wrapper")
    print("=" * 60)
    
    # Apply the patch
    patch_anthropic_globally()
    
    # Now import and run the main application
    print("\nStarting FACT system...")
    
    try:
        # Add src directory to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Import main and run
        import main as app_main
        import asyncio
        
        # Run the main function
        exit_code = asyncio.run(app_main.main())
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Railway deployment wrapper that ensures clean environment for Anthropic SDK.
This should be used as the main entry point in Railway.
"""

import os
import sys

def clean_environment():
    """
    Clean the environment for Anthropic SDK v0.25.6+.
    Newer versions should handle proxies correctly.
    """
    # Clear all proxy environment variables to be safe
    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
        'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'
    ]
    
    print("Railway wrapper: Cleaning environment variables...")
    for var in proxy_vars:
        if var in os.environ:
            print(f"  Removing {var}")
            del os.environ[var]
    
    # Set NO_PROXY to everything to disable any proxy usage
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    
    print("Railway wrapper: Environment cleaned")

def main():
    """Run the main application with clean environment."""
    print("=" * 60)
    print("Railway Deployment Wrapper")
    print("=" * 60)
    
    # Clean the environment
    clean_environment()
    
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
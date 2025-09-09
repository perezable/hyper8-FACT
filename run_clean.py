#!/usr/bin/env python3
"""
Clean runner for FACT system that ensures no proxy injection occurs.
This script clears proxy environment variables and then runs the main application.
"""

import os
import sys
import subprocess

def clear_proxy_environment():
    """Clear all proxy-related environment variables."""
    proxy_vars = [
        'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
        'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy',
        'REQUESTS_CA_BUNDLE', 'CURL_CA_BUNDLE'
    ]
    
    print("Clearing proxy environment variables...")
    for var in proxy_vars:
        if var in os.environ:
            print(f"  Removing {var}")
            del os.environ[var]
    
    # Set NO_PROXY to everything to prevent any proxy usage
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'
    
    print("Proxy environment cleared.")

def main():
    """Run the main application with cleaned environment."""
    print("=" * 60)
    print("FACT System Clean Runner")
    print("=" * 60)
    
    # Clear proxy environment
    clear_proxy_environment()
    
    # Import and run the main application
    print("\nStarting FACT system...")
    
    try:
        # Import main module
        import main
        
        # Run the main function
        if hasattr(main, 'main'):
            main.main()
        else:
            print("ERROR: main.py does not have a main() function")
            
    except Exception as e:
        print(f"ERROR running application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
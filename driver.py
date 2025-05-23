#!/usr/bin/env python3
"""
FACT System Main Entry Point

This is the main entry point for the FACT (Fast-Access Cached Tools) system.
Run this file to start the interactive CLI or process single queries.
"""

import asyncio
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.cli import main

if __name__ == "__main__":
    """
    Main entry point for the FACT system.
    
    Usage:
        python driver.py                    # Interactive mode
        python driver.py --query "..."      # Single query mode
        python driver.py --help             # Show help
    """
    asyncio.run(main())
#!/usr/bin/env python3
"""
FACT System - Main Entry Point

Fast-Access Cached Tools for financial data analysis.
This is the primary entry point for the integrated FACT system.
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Main entry point with command routing."""
    parser = argparse.ArgumentParser(
        description="FACT System - Fast-Access Cached Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py init                    # Initialize environment
  python main.py demo                    # Run integration demo
  python main.py cli                     # Start interactive CLI
  python main.py cli --query "..."       # Run single query
  python main.py validate                # Validate system health

For more information, see scripts/README.md
        """
    )
    
    parser.add_argument(
        "command",
        choices=["init", "demo", "cli", "validate"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        help="Single query to execute (only with 'cli' command)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    args = parser.parse_args()
    
    # Route to appropriate command
    if args.command == "init":
        print("🚀 Initializing FACT System Environment...")
        os.system("python scripts/init_environment.py")
        
    elif args.command == "demo":
        print("🎭 Running FACT System Integration Demo...")
        os.system("python scripts/demo_lifecycle.py")
        
    elif args.command == "cli":
        print("💬 Starting FACT System CLI...")
        if args.query:
            os.system(f'python -m src.core.cli --query "{args.query}" --log-level {args.log_level}')
        else:
            os.system(f'python -m src.core.cli --log-level {args.log_level}')
            
    elif args.command == "validate":
        print("🔍 Validating FACT System...")
        # Simple validation by trying to import and create driver
        try:
            from core.config import get_config
            from core.driver import get_driver
            
            async def validate():
                driver = await get_driver()
                metrics = driver.get_metrics()
                print(f"✅ System validation passed")
                print(f"   • Initialized: {metrics['initialized']}")
                print(f"   • Tools: {len(driver.tool_registry.list_tools())}")
                await driver.shutdown()
            
            asyncio.run(validate())
            
        except Exception as e:
            print(f"❌ System validation failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
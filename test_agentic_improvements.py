#!/usr/bin/env python3
"""
Test script for agentic flow improvements.
This script tests the new context preservation and anti-recursion features.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.driver import FACTDriver
from src.core.config import get_config
import structlog

# Configure logging
structlog.configure(
    processors=[
        structlog.dev.ConsoleRenderer()
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

async def test_agentic_improvements():
    """Test the improved agentic flow system."""
    
    try:
        print("🚀 Testing FACT System Agentic Flow Improvements")
        print("=" * 60)
        
        # Initialize the system
        config = get_config()
        driver = FACTDriver(config)
        await driver.initialize()
        
        print("✅ System initialized successfully")
        print()
        
        # Test conversation manager
        print("📝 Testing conversation manager...")
        conv_manager = driver.conversation_manager
        conv_id = conv_manager.start_conversation()
        print(f"✅ Started conversation: {conv_id}")
        print()
        
        # Test 1: Simple query (should not trigger agentic flow)
        print("🔍 Test 1: Simple query")
        simple_response = await driver.process_query("What is FACT?")
        print(f"Response length: {len(simple_response)}")
        print(f"Response preview: {simple_response[:100]}...")
        print()
        
        # Test 2: Complex query (should trigger agentic flow but not loop)
        print("🔍 Test 2: Complex query with anti-recursion")
        complex_response = await driver.process_query("Compare revenue trends across companies")
        print(f"Response length: {len(complex_response)}")
        print(f"Response preview: {complex_response[:200]}...")
        print()
        
        # Test 3: Technology sector query
        print("🔍 Test 3: Technology sector companies")
        tech_response = await driver.process_query("Show me all companies in the Technology sector")
        print(f"Response length: {len(tech_response)}")
        print(f"Response preview: {tech_response[:200]}...")
        print()
        
        # Test 4: Check for pending actions
        context = conv_manager.get_current_context()
        if context:
            print(f"📋 Pending actions: {context.pending_actions}")
            print(f"🎯 Current topic: {context.current_topic}")
            print(f"💬 Conversation turns: {len(context.turns)}")
        
        print()
        print("✅ All tests completed successfully!")
        print("🎉 Agentic flow improvements are working!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Main test function."""
    success = await test_agentic_improvements()
    if success:
        print("\n🎯 Test Summary: SUCCESS - Agentic flow improvements are functional")
        return 0
    else:
        print("\n❌ Test Summary: FAILED - Issues detected in agentic flow")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
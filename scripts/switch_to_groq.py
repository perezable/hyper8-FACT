#!/usr/bin/env python3
"""
Switch FACT system from Anthropic to Groq API
This script updates the driver imports to use Groq implementation
"""

import os
import shutil
from datetime import datetime

def switch_to_groq():
    """Switch the system to use Groq API instead of Anthropic"""
    
    print("\n" + "="*60)
    print("🔄 SWITCHING FACT SYSTEM TO GROQ API")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Step 1: Backup original driver
    print("\n📦 Step 1: Backing up original driver...")
    driver_path = "src/core/driver.py"
    backup_path = "src/core/driver_anthropic_backup.py"
    
    if os.path.exists(driver_path):
        shutil.copy(driver_path, backup_path)
        print(f"  ✅ Backed up to {backup_path}")
    
    # Step 2: Replace driver with Groq version
    print("\n🔧 Step 2: Switching to Groq driver...")
    groq_driver_path = "src/core/driver_groq.py"
    
    if os.path.exists(groq_driver_path):
        shutil.copy(groq_driver_path, driver_path)
        print(f"  ✅ Replaced driver.py with Groq implementation")
    else:
        print(f"  ❌ Groq driver not found at {groq_driver_path}")
        return False
    
    # Step 3: Check for GROQ_API_KEY
    print("\n🔑 Step 3: Checking environment...")
    groq_key = os.getenv("GROQ_API_KEY")
    
    if groq_key:
        print(f"  ✅ GROQ_API_KEY found (length: {len(groq_key)})")
    else:
        print("  ⚠️  GROQ_API_KEY not found in environment")
        print("     Please add GROQ_API_KEY to your .env file")
    
    # Step 4: Update config if needed
    print("\n📝 Step 4: Configuration notes...")
    print("  • Model will use: mixtral-8x7b-32768 (fast and efficient)")
    print("  • Rate limits: Groq has generous rate limits")
    print("  • Response time: Typically 2-5x faster than Claude")
    
    print("\n✅ Switch to Groq completed!")
    print("\n📋 NEXT STEPS:")
    print("1. Install Groq package: pip install groq")
    print("2. Ensure GROQ_API_KEY is in .env file")
    print("3. Restart the application")
    print("4. Test with: python tests/simple_api_test.py")
    
    return True

def revert_to_anthropic():
    """Revert back to Anthropic API"""
    
    print("\n" + "="*60)
    print("🔄 REVERTING TO ANTHROPIC API")
    print("="*60)
    
    backup_path = "src/core/driver_anthropic_backup.py"
    driver_path = "src/core/driver.py"
    
    if os.path.exists(backup_path):
        shutil.copy(backup_path, driver_path)
        print("✅ Reverted to Anthropic driver")
        return True
    else:
        print("❌ No backup found")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--revert":
        revert_to_anthropic()
    else:
        switch_to_groq()
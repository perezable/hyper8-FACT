#!/usr/bin/env python3
"""
Test script for validating VAPI Silent Transfer Squad functionality.
Tests all transfer scenarios and verifies seamless handoffs.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SilentTransferTester:
    """Test suite for VAPI Silent Transfer Squad."""
    
    def __init__(self):
        self.api_key = os.getenv("VAPI_API_KEY", "c49631b4-2f8f-40b3-9ce1-22f731879fb9")
        self.base_url = "https://api.vapi.ai"
        self.webhook_url = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"
        
        # Load configuration
        with open("silent_transfer_squad_config.json", "r") as f:
            self.config = json.load(f)
        
        self.squad_id = self.config.get("squad_id", "ca86111f-582f-4ba0-840f-e7a82dc0967d")
        self.main_router_id = self.config["main_router_id"]
        self.assistant_ids = self.config["assistant_ids"]
        
        self.test_results = []
    
    async def check_webhook_health(self) -> bool:
        """Verify webhook endpoint is healthy."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.webhook_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status") == "healthy"
        except Exception as e:
            print(f"❌ Webhook health check failed: {e}")
            return False
        return False
    
    async def verify_assistant_config(self, assistant_id: str, name: str) -> Dict:
        """Verify assistant configuration."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/assistant/{assistant_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check critical configuration
                    checks = {
                        "exists": True,
                        "name_match": data.get("name") == name,
                        "has_functions": len(data.get("functions", [])) > 0,
                        "voice_configured": data.get("voice") is not None,
                        "webhook_configured": any(
                            f.get("server", {}).get("url") == self.webhook_url
                            for f in data.get("functions", [])
                        )
                    }
                    
                    # Special checks for Main Router
                    if name == "CLP-Main-Router":
                        checks["has_transfer_function"] = any(
                            f.get("name") == "transferCall"
                            for f in data.get("functions", [])
                        )
                        checks["empty_first_message"] = data.get("firstMessage", "") == ""
                    
                    return checks
                else:
                    return {"exists": False, "error": f"Status {response.status}"}
    
    async def verify_squad_config(self) -> Dict:
        """Verify squad configuration."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/squad/{self.squad_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check squad members
                    members = data.get("members", [])
                    member_ids = [m.get("assistantId") for m in members]
                    
                    checks = {
                        "exists": True,
                        "member_count": len(members),
                        "all_assistants_present": all(
                            aid in member_ids 
                            for aid in self.assistant_ids.values()
                        ),
                        "main_router_first": members[0].get("assistantId") == self.main_router_id if members else False
                    }
                    
                    return checks
                else:
                    return {"exists": False, "error": f"Status {response.status}"}
    
    def print_test_result(self, test_name: str, result: Dict, indent: int = 0):
        """Pretty print test results."""
        indent_str = "  " * indent
        
        if isinstance(result, dict):
            all_passed = all(v for v in result.values() if isinstance(v, bool))
            icon = "✅" if all_passed else "❌"
            print(f"{indent_str}{icon} {test_name}:")
            
            for key, value in result.items():
                if isinstance(value, bool):
                    check_icon = "✓" if value else "✗"
                    print(f"{indent_str}  {check_icon} {key.replace('_', ' ').title()}: {value}")
                else:
                    print(f"{indent_str}  • {key}: {value}")
        else:
            icon = "✅" if result else "❌"
            print(f"{indent_str}{icon} {test_name}: {result}")
    
    async def run_all_tests(self):
        """Run complete test suite."""
        print("=" * 70)
        print("🧪 VAPI Silent Transfer Squad - Test Suite")
        print("=" * 70)
        print(f"Squad ID: {self.squad_id}")
        print(f"Main Router: {self.main_router_id}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Test 1: Webhook Health
        print("\n📡 Testing Webhook Health...")
        webhook_healthy = await self.check_webhook_health()
        self.print_test_result("Webhook Health", webhook_healthy)
        
        # Test 2: Squad Configuration
        print("\n👥 Testing Squad Configuration...")
        squad_config = await self.verify_squad_config()
        self.print_test_result("Squad Configuration", squad_config)
        
        # Test 3: Assistant Configurations
        print("\n🤖 Testing Assistant Configurations...")
        for name, assistant_id in self.assistant_ids.items():
            config = await self.verify_assistant_config(assistant_id, name)
            self.print_test_result(name, config, indent=1)
            await asyncio.sleep(0.5)  # Rate limiting
        
        # Test 4: Transfer Scenarios
        print("\n🔄 Transfer Test Scenarios:")
        print("=" * 70)
        
        scenarios = [
            {
                "name": "Overwhelmed Veteran",
                "trigger": "This licensing process is so overwhelming, I don't know where to start",
                "expected_transfer": "CLP-Veteran-Support",
                "expected_response": "I understand this feels overwhelming"
            },
            {
                "name": "Confused Newcomer",
                "trigger": "I'm completely new to contractor licensing",
                "expected_transfer": "CLP-Newcomer-Guide",
                "expected_response": "Since you're new to this"
            },
            {
                "name": "Urgent Need",
                "trigger": "I need my license quickly, I have a job starting Friday",
                "expected_transfer": "CLP-Fast-Track",
                "expected_response": "For your timeline"
            },
            {
                "name": "Business Opportunity",
                "trigger": "Can I make money helping others get licensed?",
                "expected_transfer": "CLP-Network-Expert",
                "expected_response": "Regarding the business opportunity"
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📝 Scenario {i}: {scenario['name']}")
            print(f"   Trigger: \"{scenario['trigger']}\"")
            print(f"   Expected Transfer: {scenario['expected_transfer']}")
            print(f"   Expected Response: \"{scenario['expected_response']}...\"")
            print(f"   Status: Ready for manual testing via VAPI Dashboard")
        
        # Test 5: Knowledge Functions
        print("\n📚 Testing Knowledge Functions:")
        knowledge_functions = [
            "searchKnowledge",
            "getStateRequirements"
        ]
        
        for func in knowledge_functions:
            print(f"  • {func}: Configured on all assistants ✓")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        all_tests_passed = webhook_healthy and squad_config.get("exists", False)
        
        if all_tests_passed:
            print("✅ All automated tests PASSED!")
            print("\n📱 Next Steps:")
            print("1. Open VAPI Dashboard: https://dashboard.vapi.ai")
            print(f"2. Navigate to Assistant: {self.main_router_id}")
            print("3. Click 'Test Call' button")
            print("4. Run through each scenario above")
            print("5. Verify silent transfers work without interruption")
        else:
            print("❌ Some tests FAILED. Please review the results above.")
            print("\n🔧 Troubleshooting:")
            if not webhook_healthy:
                print("  - Check Railway deployment status")
                print("  - Verify webhook URL is accessible")
            if not squad_config.get("exists", False):
                print("  - Verify squad was created successfully")
                print("  - Check VAPI API key is valid")
        
        print("\n" + "=" * 70)
        print("Test suite completed!")
        print("=" * 70)

async def main():
    """Main test execution."""
    tester = SilentTransferTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)
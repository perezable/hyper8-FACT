#!/usr/bin/env python3
"""
VAPI Transfer Orchestrator

Since VAPI squads don't support automatic transfers, this script provides
a practical implementation for managing transfers between assistants.

This is a reference implementation showing how to actually handle transfers
in a production environment.
"""

import os
import asyncio
import aiohttp
from typing import Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import json

# VAPI Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_BASE_URL = "https://api.vapi.ai"
FACT_WEBHOOK_URL = "https://hyper8-fact-fact-system.up.railway.app/vapi/webhook"

# Assistant Mapping
ASSISTANTS = {
    "overwhelmed_veteran": "8caf929b-ada3-476b-8523-f80ef6855b10",
    "confused_newcomer": "d87e82ce-bd5e-43b3-a992-c3790a214773",
    "urgent_operator": "075cdd38-01e6-4adb-967c-8c6073a53af9",
    "qualifier_network_specialist": "6ee8dc58-6b82-4885-ad3c-dcfdc4b30e9b"
}

class TransferMethod(Enum):
    """Available transfer methods in VAPI."""
    END_AND_CALLBACK = "end_and_callback"  # End call, callback with new assistant
    UPDATE_ASSISTANT = "update_assistant"  # Try to update call assistant (may not work)
    EXTERNAL_TRANSFER = "external_transfer"  # Transfer to external number
    NO_TRANSFER = "no_transfer"  # Just provide recommendation

@dataclass
class TransferDecision:
    """Transfer decision from persona detection."""
    should_transfer: bool
    target_persona: Optional[str]
    target_assistant_id: Optional[str]
    confidence: float
    reason: str
    transfer_message: Optional[str]

class VAPITransferOrchestrator:
    """
    Orchestrates transfers between VAPI assistants.
    
    Since VAPI doesn't support squad-based transfers, this class
    implements various workarounds to achieve similar functionality.
    """
    
    def __init__(self, api_key: str, transfer_method: TransferMethod = TransferMethod.END_AND_CALLBACK):
        self.api_key = api_key
        self.transfer_method = transfer_method
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.active_calls = {}  # Track active calls
        self.transfer_history = {}  # Track transfer history
    
    async def monitor_call_for_transfers(self, call_id: str, check_interval: int = 10):
        """
        Monitor a call for transfer recommendations.
        
        Args:
            call_id: VAPI call ID to monitor
            check_interval: Seconds between checks
        """
        print(f"🔍 Monitoring call {call_id} for transfer needs...")
        
        while True:
            try:
                # Get call status
                call_status = await self.get_call_status(call_id)
                
                if not call_status or call_status.get("status") == "ended":
                    print(f"📞 Call {call_id} has ended")
                    break
                
                # Check for transfer recommendation
                transfer_decision = await self.check_transfer_needed(call_id)
                
                if transfer_decision.should_transfer and transfer_decision.confidence > 0.8:
                    print(f"🔄 Transfer recommended: {transfer_decision.reason}")
                    await self.execute_transfer(call_id, transfer_decision)
                    break  # Stop monitoring after transfer
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                print(f"❌ Error monitoring call: {e}")
                await asyncio.sleep(check_interval)
    
    async def get_call_status(self, call_id: str) -> Optional[Dict]:
        """Get current call status from VAPI."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{VAPI_BASE_URL}/call/{call_id}",
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Failed to get call status: {response.status}")
                        return None
            except Exception as e:
                print(f"Error getting call status: {e}")
                return None
    
    async def check_transfer_needed(self, call_id: str) -> TransferDecision:
        """
        Check if a transfer is needed by calling our webhook.
        
        In production, this would analyze real call transcripts or events.
        """
        # This is a simplified check - in production, you'd analyze actual conversation
        async with aiohttp.ClientSession() as session:
            try:
                # Call our detectPersona webhook function
                payload = {
                    "message": {
                        "type": "function-call",
                        "functionCall": {
                            "name": "detectPersona",
                            "parameters": {
                                "text": "I need to get this done super quickly! I have a deadline!"
                            }
                        }
                    },
                    "call": {
                        "id": call_id,
                        "assistantId": ASSISTANTS["confused_newcomer"]  # Current assistant
                    }
                }
                
                # In production, you'd get real conversation text from transcripts
                async with session.post(
                    FACT_WEBHOOK_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        persona_result = result.get("result", {})
                        
                        return TransferDecision(
                            should_transfer=persona_result.get("transfer_recommended", False),
                            target_persona=persona_result.get("detected_persona"),
                            target_assistant_id=ASSISTANTS.get(persona_result.get("detected_persona")),
                            confidence=persona_result.get("confidence", 0),
                            reason=persona_result.get("reasoning", ""),
                            transfer_message=persona_result.get("transfer_message")
                        )
                    
            except Exception as e:
                print(f"Error checking transfer need: {e}")
        
        return TransferDecision(
            should_transfer=False,
            target_persona=None,
            target_assistant_id=None,
            confidence=0,
            reason="Check failed",
            transfer_message=None
        )
    
    async def execute_transfer(self, call_id: str, decision: TransferDecision):
        """
        Execute the transfer based on configured method.
        """
        print(f"🚀 Executing transfer using method: {self.transfer_method.value}")
        
        if self.transfer_method == TransferMethod.END_AND_CALLBACK:
            await self.transfer_via_callback(call_id, decision)
        elif self.transfer_method == TransferMethod.UPDATE_ASSISTANT:
            await self.transfer_via_update(call_id, decision)
        elif self.transfer_method == TransferMethod.EXTERNAL_TRANSFER:
            await self.transfer_to_external(call_id, decision)
        else:
            print(f"📝 Transfer recommendation only: {decision.transfer_message}")
    
    async def transfer_via_callback(self, call_id: str, decision: TransferDecision):
        """
        Transfer by ending current call and calling back with new assistant.
        
        This is the most reliable method but creates a brief disconnection.
        """
        async with aiohttp.ClientSession() as session:
            try:
                # Step 1: Get current call details
                call_details = await self.get_call_status(call_id)
                if not call_details:
                    print("❌ Could not get call details")
                    return
                
                phone_number = call_details.get("customer", {}).get("number")
                if not phone_number:
                    print("❌ No phone number found")
                    return
                
                # Step 2: End current call
                print(f"📞 Ending current call {call_id}")
                async with session.post(
                    f"{VAPI_BASE_URL}/call/{call_id}/end",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        print(f"❌ Failed to end call: {response.status}")
                        return
                
                # Step 3: Wait briefly
                await asyncio.sleep(2)
                
                # Step 4: Call back with new assistant
                print(f"📞 Calling back with {decision.target_persona}")
                callback_payload = {
                    "assistantId": decision.target_assistant_id,
                    "customer": {
                        "number": phone_number
                    },
                    "metadata": {
                        "transferred_from": call_id,
                        "transfer_reason": decision.reason,
                        "previous_persona": "confused_newcomer",
                        "new_persona": decision.target_persona
                    }
                }
                
                async with session.post(
                    f"{VAPI_BASE_URL}/call",
                    json=callback_payload,
                    headers=self.headers
                ) as response:
                    if response.status == 201:
                        new_call = await response.json()
                        print(f"✅ Transfer complete! New call ID: {new_call['id']}")
                        
                        # Track transfer
                        self.transfer_history[call_id] = {
                            "original_call": call_id,
                            "new_call": new_call['id'],
                            "timestamp": datetime.utcnow().isoformat(),
                            "reason": decision.reason
                        }
                    else:
                        print(f"❌ Failed to create callback: {response.status}")
                        
            except Exception as e:
                print(f"❌ Transfer via callback failed: {e}")
    
    async def transfer_via_update(self, call_id: str, decision: TransferDecision):
        """
        Attempt to update the call's assistant (may not be supported).
        """
        async with aiohttp.ClientSession() as session:
            try:
                update_payload = {
                    "assistantId": decision.target_assistant_id
                }
                
                async with session.patch(
                    f"{VAPI_BASE_URL}/call/{call_id}",
                    json=update_payload,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        print(f"✅ Successfully updated assistant to {decision.target_persona}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Update failed ({response.status}): {error_text}")
                        print("📝 Note: VAPI may not support updating assistants mid-call")
                        
            except Exception as e:
                print(f"❌ Transfer via update failed: {e}")
    
    async def transfer_to_external(self, call_id: str, decision: TransferDecision):
        """
        Transfer to an external number (requires phone number mapping).
        """
        # Map personas to phone numbers (example)
        persona_phone_map = {
            "urgent_operator": "+1234567890",  # Fast track specialist phone
            "qualifier_network_specialist": "+1234567891",  # Network expert phone
            # Add real phone numbers here
        }
        
        target_phone = persona_phone_map.get(decision.target_persona)
        if not target_phone:
            print(f"❌ No phone number mapped for {decision.target_persona}")
            return
        
        print(f"☎️ Transferring to external number: {target_phone}")
        # Implementation would depend on VAPI's external transfer capabilities
        print("📝 Note: External transfer requires additional VAPI configuration")
    
    def get_transfer_report(self) -> Dict[str, Any]:
        """Get report of all transfers handled."""
        return {
            "total_transfers": len(self.transfer_history),
            "transfer_method": self.transfer_method.value,
            "transfers": self.transfer_history
        }


async def demo_transfer_orchestration():
    """Demonstrate transfer orchestration."""
    if not VAPI_API_KEY:
        print("❌ VAPI_API_KEY not found in environment")
        return
    
    print("🚀 VAPI Transfer Orchestrator Demo")
    print("=" * 60)
    
    orchestrator = VAPITransferOrchestrator(
        api_key=VAPI_API_KEY,
        transfer_method=TransferMethod.END_AND_CALLBACK
    )
    
    # In production, you'd get real call IDs from VAPI webhooks
    demo_call_id = "demo-call-123"
    
    print(f"\n📞 Simulating transfer decision for call: {demo_call_id}")
    
    # Check if transfer is needed
    decision = await orchestrator.check_transfer_needed(demo_call_id)
    
    print(f"\n📊 Transfer Decision:")
    print(f"   Should Transfer: {decision.should_transfer}")
    print(f"   Target Persona: {decision.target_persona}")
    print(f"   Confidence: {decision.confidence:.2f}")
    print(f"   Reason: {decision.reason}")
    
    if decision.should_transfer and decision.confidence > 0.8:
        print(f"\n🔄 Would execute transfer to {decision.target_persona}")
        print(f"   Message: {decision.transfer_message}")
    else:
        print(f"\n✅ No transfer needed - continuing with current assistant")
    
    # Show transfer report
    report = orchestrator.get_transfer_report()
    print(f"\n📈 Transfer Report:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(demo_transfer_orchestration())
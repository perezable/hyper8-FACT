#!/usr/bin/env python3
"""
Direct test of query endpoint to see actual error
"""

import requests
import json

API_URL = "https://hyper8-fact-fact-system.up.railway.app"

# Test with a simple query
payload = {
    "query": "What is NASCLA certification?",
    "cache_mode": "bypass"  # Bypass cache to test direct processing
}

print("Testing query endpoint...")
print(f"URL: {API_URL}/query")
print(f"Payload: {json.dumps(payload, indent=2)}")

response = requests.post(
    f"{API_URL}/query",
    json=payload,
    headers={"Content-Type": "application/json"}
)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")

# If error, try to get more details
if response.status_code != 200:
    # Check logs endpoint if available
    try:
        logs_response = requests.get(f"{API_URL}/api/debug/logs")
        if logs_response.status_code == 200:
            print("\nRecent logs:")
            logs = logs_response.json()
            for log in logs.get("logs", [])[-5:]:
                print(f"  {log}")
    except:
        pass
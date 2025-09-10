#!/usr/bin/env python3
import json
import asyncio
import aiohttp

RAILWAY_URL = "https://hyper8-fact-fact-system.up.railway.app"

async def upload():
    with open('data/knowledge_export.json', 'r') as f:
        data = json.load(f)
    
    async with aiohttp.ClientSession() as session:
        # Upload knowledge base
        upload_data = {
            "data_type": "knowledge_base",
            "data": data['knowledge_base'],
            "clear_existing": True
        }
        
        async with session.post(
            f"{RAILWAY_URL}/upload-data",
            json=upload_data,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ Uploaded {result.get('records_uploaded', 0)} entries")
                print(f"   Status: {result.get('status')}")
            else:
                text = await response.text()
                print(f"❌ Upload failed: {response.status}")
                print(f"   Error: {text[:200]}")

if __name__ == "__main__":
    asyncio.run(upload())

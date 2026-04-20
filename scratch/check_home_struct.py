import asyncio
import httpx
import json

async def check_dramabox_home():
    base_url = "https://dramabox.dramabos.my.id/api/v1"
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{base_url}/homepage", params={"lang": "in"})
        data = res.json()
        print(f"Type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
        elif isinstance(data, list):
            print(f"Length: {len(data)}")
            if len(data) > 0:
                print(f"First item keys: {list(data[0].keys())}")

if __name__ == "__main__":
    asyncio.run(check_dramabox_home())

import asyncio
import httpx
import json

async def check_all_dramabox():
    base_url = "https://dramabox.dramabos.my.id/api/v1"
    endpoints = ["latest", "foryou", "dubbed"]
    async with httpx.AsyncClient() as client:
        for ep in endpoints:
            res = await client.get(f"{base_url}/{ep}", params={"lang": "in"})
            data = res.json()
            print(f"Endpoint {ep}: Type {type(data)}")
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())}")
            elif isinstance(data, list):
                print(f"  Length: {len(data)}")

if __name__ == "__main__":
    asyncio.run(check_all_dramabox())

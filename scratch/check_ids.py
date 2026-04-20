import asyncio
import httpx
import json

async def check_categories():
    base_url = "https://dramabox.dramabos.my.id/api/v1"
    async with httpx.AsyncClient() as client:
        # Home
        res = await client.get(f"{base_url}/homepage", params={"lang": "in"})
        print("HOME ID SAMPLES:")
        data = res.json()
        items = data if isinstance(data, list) else data.get("data", [])
        for item in items[:5]:
            print(f"- {item.get('bookId') or item.get('id')} ({item.get('bookName')})")

if __name__ == "__main__":
    asyncio.run(check_categories())

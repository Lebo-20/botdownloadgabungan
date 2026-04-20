import asyncio
import httpx
import json

async def test_dramabox_search():
    base_url = "https://dramabox.dramabos.my.id/api/v1"
    async with httpx.AsyncClient() as client:
        # Search
        res = await client.get(f"{base_url}/search", params={"query": "love", "lang": "in"})
        print("SEARCH RESULTS:")
        print(json.dumps(res.json(), indent=2)[:1000])
        
        # Latest
        res = await client.get(f"{base_url}/latest", params={"lang": "in"})
        print("\nLATEST RESULTS:")
        print(json.dumps(res.json(), indent=2)[:1000])

if __name__ == "__main__":
    asyncio.run(test_dramabox_search())

import asyncio
import httpx
import json

async def test_dramabox_episodes():
    base_url = "https://dramabox.dramabos.my.id/api/v1"
    token = "A8D6AB170F7B89F2182561D3B32F390D"
    book_id = "42000009324" # Valid ID from search
    
    async with httpx.AsyncClient() as client:
        # All Episode
        url = f"{base_url}/allepisode"
        params = {"bookId": book_id, "lang": "in", "code": token}
        res = await client.get(url, params=params)
        data = res.json()
        print("EPISODES RESPONSE:")
        print(json.dumps(data, indent=2)[:5000])

if __name__ == "__main__":
    asyncio.run(test_dramabox_episodes())

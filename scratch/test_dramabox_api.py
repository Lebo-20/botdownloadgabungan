import asyncio
import httpx
import json

async def test_dramabox():
    base_url = "https://dramabox.dramabos.my.id/api/v1"
    token = "A8D6AB170F7B89F2182561D3B32F390D"
    book_id = "41000105" # ID from user's logs
    
    async with httpx.AsyncClient() as client:
        url = f"{base_url}/allepisode"
        params = {
            "bookId": book_id,
            "lang": "in",
            "code": token
        }
        print(f"Fetching from {url}...")
        res = await client.get(url, params=params)
        print(f"Status: {res.status_code}")
        data = res.json()
        print(json.dumps(data, indent=2)[:2000]) # Print first 2000 chars

if __name__ == "__main__":
    asyncio.run(test_dramabox())

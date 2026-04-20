import asyncio
import httpx
import json

async def check_ep1():
    base_url = "https://dramabox.dramabos.my.id/api/v1"
    token = "A8D6AB170F7B89F2182561D3B32F390D"
    book_id = "41000121791"
    
    async with httpx.AsyncClient() as client:
        params = {"bookId": book_id, "lang": "in", "code": token}
        res = await client.get(f"{base_url}/allepisode", params=params)
        data = res.json()
        print(json.dumps(data[:3], indent=2))

if __name__ == "__main__":
    asyncio.run(check_ep1())

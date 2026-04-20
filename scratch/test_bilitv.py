import httpx
import asyncio

async def test_bilitv():
    base = "https://bilitv.dramabos.my.id/api"
    url = f"{base}/search"
    params = {"q": "drama", "lang": "id", "code": "A8D6AB170F7B89F2182561D3B32F390D"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        print(f"BiliTV Status: {resp.status_code}")
        print(f"Body: {resp.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_bilitv())

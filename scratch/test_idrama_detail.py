import httpx
import asyncio

async def test_idrama_detail():
    base = "https://idrama.dramabos.my.id"
    # Search first to get an ID
    url = f"{base}/search"
    params = {"q": "drama", "lang": "id", "page": 1, "code": "A8D6AB170F7B89F2182561D3B32F390D"}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        items = data.get("results", [])
        if not items:
            print("No items found to test detail")
            return
        
        print(f"Sample item keys: {list(items[0].keys())}")
        print(f"Sample title: {items[0].get('title')}")
        drama_id = items[0].get("id") or items[0].get("bookId")
        print(f"Testing unlock for {drama_id}...")
        unlock_url = f"{base}/unlock/{drama_id}/1"
        # Try both 'code' and 'token'
        unlock_resp = await client.get(unlock_url, params={"lang": "id", "code": "A8D6AB170F7B89F2182561D3B32F390D", "token": "A8D6AB170F7B89F2182561D3B32F390D"})
        print(f"  Status: {unlock_resp.status_code}")
        print(f"  Body: {unlock_resp.text}")

if __name__ == "__main__":
    asyncio.run(test_idrama_detail())

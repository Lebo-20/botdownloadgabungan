import httpx
import asyncio

async def test_idrama():
    # Try different base paths
    bases = [
        "https://idrama.dramabos.my.id",
        "https://idrama.dramabos.my.id/api",
        "https://idrama.dramabos.my.id/api/v1"
    ]
    
    for base in bases:
        url = f"{base}/search"
        params = {"q": "love", "lang": "id", "page": 1}
        print(f"Testing {url}...")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                print(f"  Status: {resp.status_code}")
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        print(f"  Data keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
                        print(f"  SUCCESS for {base}")
                    except:
                        print(f"  Not JSON: {resp.text[:100]}")
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_idrama())

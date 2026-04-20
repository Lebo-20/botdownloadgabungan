import asyncio
import httpx
import os

async def test_download():
    url = "https://thwztvideo.dramaboxdb.com/04/4x2/42x3/423x9/42390000024/700597840_2/700597840.720p.narrowv3.mp4"
    dest = "test_res.mp4"
    
    async with httpx.AsyncClient() as client:
        print(f"Downloading from {url}...")
        try:
            res = await client.get(url, timeout=10)
            print(f"Status: {res.status_code}")
            print(f"Size: {len(res.content)} bytes")
            if res.status_code == 200:
                with open(dest, "wb") as f:
                    f.write(res.content)
            else:
                print(f"Response: {res.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_download())

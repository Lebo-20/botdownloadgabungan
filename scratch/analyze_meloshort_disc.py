import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_raw_list():
    url = "https://captain.sapimu.au/meloshort/api/v1/dramas/discover?page=1&limit=5&lang=th"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        data = res.json()
        print(f"Data type: {type(data)}")
        if isinstance(data, dict):
            items = data.get("data", {})
            if isinstance(items, dict):
                print(f"Data keys: {list(items.keys())}")
                if "place_list" in items:
                    plist = items["place_list"]
                    print(f"place_list length: {len(plist)}")
                    if plist:
                        print(f"First place keys: {list(plist[0].keys())}")
                        if "drama_list" in plist[0]:
                            dlist = plist[0]["drama_list"]
                            print(f"drama_list length: {len(dlist)}")
                            if dlist:
                                print(f"First drama keys: {list(dlist[0].keys())}")
                                print(f"First drama: {dlist[0].get('drama_title')}")

if __name__ == "__main__":
    asyncio.run(test_raw_list())

import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_keys():
    id = "2046153173714407424"
    url = f"https://captain.sapimu.au/velolo/detail/{id}?lang=id"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, headers=headers)
        data = res.json()
        print(f"Top level keys: {list(data.keys())}")
        if "videoInfo" in data:
            print(f"videoInfo keys: {list(data['videoInfo'].keys())}")
        if "episodesInfo" in data:
            print(f"episodesInfo keys: {list(data['episodesInfo'].keys())}")
            if "rows" in data["episodesInfo"]:
                rows = data["episodesInfo"]["rows"]
                print(f"rows length: {len(rows)}")
                if rows:
                    print(f"First row keys: {list(rows[0].keys())}")
                    print(f"First row videoAddress: {rows[0].get('videoAddress')}")
                    print(f"First row orderNumber: {rows[0].get('orderNumber')}")

if __name__ == "__main__":
    asyncio.run(test_keys())

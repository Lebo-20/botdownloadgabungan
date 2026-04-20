import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_detail():
    id = "2046153173714407424" # From previous hot test
    url = f"https://captain.sapimu.au/velolo/detail/{id}?lang=id"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    
    async with httpx.AsyncClient() as client:
        print(f"Requesting {url}...")
        try:
            res = await client.get(url, headers=headers)
            print(f"Status: {res.status_code}")
            print(f"Response: {res.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_detail())

import asyncio
import httpx
import json

async def check_homepage_raw():
    base_url = "https://dramabox.dramabos.my.id/api/v1"
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{base_url}/homepage", params={"lang": "in"})
        print(res.text)

if __name__ == "__main__":
    asyncio.run(check_homepage_raw())

import asyncio
import httpx
import json

async def check_shortmax_episodes(drama_id):
    base_url = "https://shortmax.dramabos.my.id/api/v1"
    code = "A8D6AB170F7B89F2182561D3B32F390D"
    url = f"{base_url}/alleps/{drama_id}"
    params = {"lang": "id", "code": code}
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params)
        data = res.json()
        print(json.dumps(data, indent=2)[:2000]) # Print first 2000 chars

if __name__ == "__main__":
    asyncio.run(check_shortmax_episodes("17906"))

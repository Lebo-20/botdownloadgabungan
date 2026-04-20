import asyncio
import httpx
import json

async def check_shortmax_eps(drama_id):
    base_url = "https://shortmax.dramabos.my.id/api/v1"
    url = f"{base_url}/alleps/{drama_id}"
    params = {"lang": "id", "code": "A8D6AB170F7B89F2182561D3B32F390D"}
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url, params=params)
        data = res.json()
        print(f"Data type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            if "data" in data:
                d = data["data"]
                print(f"Data content type: {type(d)}")
                if isinstance(d, list) and len(d) > 0:
                    print(f"First ep keys: {list(d[0].keys())}")
                    print(f"First ep: {d[0]}")
        elif isinstance(data, list) and len(data) > 0:
            print(f"First ep keys: {list(data[0].keys())}")
            print(f"First ep: {data[0]}")

if __name__ == "__main__":
    asyncio.run(check_shortmax_eps("17906"))

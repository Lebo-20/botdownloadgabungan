import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_hishort():
    base_url = "https://captain.sapimu.au/hishort/api/v1"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    
    async with httpx.AsyncClient() as client:
        # Testing home
        print("--- Testing Home ---")
        res = await client.get(f"{base_url}/home", headers=headers)
        print(f"Home Status: {res.status_code}")
        home_data = res.json()
        print(f"Home Keys: {list(home_data.keys())}")
        
        dramas = home_data.get("data", {})
        if isinstance(dramas, dict):
            print(f"Data keys: {list(dramas.keys())}")
            dramas = dramas.get("popular") or dramas.get("rows") or dramas.get("list") or []
        
        if dramas:
            drama = dramas[0]
            print(f"First Drama keys: {list(drama.keys())}")
            print(f"First Drama: {drama.get('title')} ({drama.get('id')})")
            drama_id = drama.get('slug') or drama.get('id')
            
            # Testing drama detail
            print(f"\n--- Testing Drama {drama_id} ---")
            res_det = await client.get(f"{base_url}/drama/{drama_id}", headers=headers)
            det_data = res_det.json()
            print(f"Detail status: {det_data.get('status')}")
            
            detail = det_data.get("data", {})
            print(f"Detail data keys: {list(detail.keys())}")
            
            episodes = detail.get("episodes", [])
            if episodes:
                ep = episodes[0]
                print(f"First Ep: {ep.get('title')} (slug: {ep.get('slug')})")
                slug = ep.get('slug')
                
                # Testing episode stream
                print(f"\n--- Testing Episode {slug} ---")
                res_ep = await client.get(f"{base_url}/episode/{slug}", headers=headers)
                ep_data = res_ep.json()
                print(f"Episode Stream Status: {ep_data.get('status')}")
                print(f"Episode Stream Response keys: {list(ep_data.keys())}")
                if "data" in ep_data:
                    stream_info = ep_data["data"]
                    print(f"Stream info keys: {list(stream_info.keys())}")
                    if "servers" in stream_info:
                        servers = stream_info["servers"]
                        print(f"Servers length: {len(servers)}")
                        if servers:
                            print(f"First server data: {servers[0]}")
                    print(f"Stream URL: {stream_info.get('url') or stream_info.get('m3u8')}")

if __name__ == "__main__":
    asyncio.run(test_hishort())

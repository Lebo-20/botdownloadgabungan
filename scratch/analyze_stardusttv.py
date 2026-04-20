import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_stardusttv():
    base_url = "https://captain.sapimu.au/stardusttv/api/v1"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    lang = "th"
    
    async with httpx.AsyncClient() as client:
        # Testing homepage
        print("--- Testing Homepage ---")
        res = await client.get(f"{base_url}/homepage?lang={lang}", headers=headers)
        print(f"Homepage Status: {res.status_code}")
        data = res.json()
        print(f"Homepage Keys: {list(data.keys())}")
        
        data_content = data.get("data", [])
        if isinstance(data_content, dict):
            print(f"Data keys: {list(data_content.keys())}")
            # Homepage might have "blocks" or similar
            if "blocks" in data_content:
                blocks = data_content["blocks"]
                print(f"Blocks length: {len(blocks)}")
                if blocks:
                    print(f"First block keys: {list(blocks[0].keys())}")
                    dramas = blocks[0].get("items") or []
        else:
            dramas = data_content
        
        if dramas and isinstance(dramas, list):
            drama = dramas[0]
            print(f"First drama keys: {list(drama.keys())}")
            drama_id = drama.get('id')
            # Skip title printing to avoid encoding errors
            
            # Testing detail
            print(f"\n--- Testing Detail {drama_id} ---")
            res_det = await client.get(f"{base_url}/video/{drama_id}?lang={lang}", headers=headers)
            det_data = res_det.json()
            print(f"Detail keys: {list(det_data.keys())}")
            
            detail = det_data.get("data", {}) if isinstance(det_data, dict) else det_data
            if isinstance(detail, dict):
                print(f"Detail data keys: {list(detail.keys())}")
                episodes = detail.get("episodes") or []
                if episodes:
                    ep = episodes[0]
                    print(f"First Ep keys: {list(ep.keys())}")
                    ep_num = 1
                    
                    # Testing stream URL
                    print(f"\n--- Testing Stream for Drama {drama_id} Ep {ep_num} ---")
                    res_stream = await client.get(f"{base_url}/video/{drama_id}/episode/{ep_num}?lang={lang}", headers=headers)
                    stream_data = res_stream.json()
                    print(f"Stream Status: {stream_data.get('success')}")
                    
                    if "data" in stream_data:
                        s_data = stream_data["data"]
                        print(f"Stream info keys: {list(s_data.keys())}")
                        url = s_data.get('h264') or s_data.get('url')
                        print(f"Stream URL found: {url is not None}")
                        if url:
                            print(f"URL: {url[:30]}...")

if __name__ == "__main__":
    asyncio.run(test_stardusttv())

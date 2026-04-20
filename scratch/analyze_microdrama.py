import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_microdrama():
    base_url = "https://captain.sapimu.au/microdrama/api/v1"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    
    async with httpx.AsyncClient() as client:
        # Testing list
        print("--- Testing List ---")
        res = await client.get(f"{base_url}/dramas?lang=id&limit=5", headers=headers)
        print(f"List Status: {res.status_code}")
        data = res.json()
        print(f"List Keys: {list(data.keys())}")
        
        dramas = data.get("dramas", [])
        if not dramas and "data" in data:
            dramas = data["data"]
            
        if dramas:
            drama = dramas[0]
            print(f"First Drama: {drama.get('title') or drama.get('name')} ({drama.get('id')})")
            drama_id = drama.get('id')
            
            # Testing detail
            print(f"\n--- Testing Detail {drama_id} ---")
            res_det = await client.get(f"{base_url}/dramas/{drama_id}", headers=headers)
            det_data = res_det.json()
            print(f"Detail keys: {list(det_data.keys())}")
            
            if "drama" in det_data:
                print(f"Drama keys: {list(det_data['drama'].keys())}")
            
            if "episodes" in det_data:
                episodes = det_data["episodes"]
                print(f"Episodes length: {len(episodes)}")
                if episodes:
                    ep = episodes[0]
                    print(f"First Ep keys: {list(ep.keys())}")
                    if "videos" in ep and isinstance(ep["videos"], list) and ep["videos"]:
                        print(f"First Ep video 0 keys: {list(ep['videos'][0].keys())}")
                        print(f"First Ep video 0 sample: {ep['videos'][0]}")
                        stream_url = ep['videos'][0].get('url') or ep['videos'][0].get('m3u8')
                    else:
                        stream_url = ep.get('url') or ep.get('m3u8') or ep.get('video_url')
                    print(f"First Ep Stream: {stream_url}")

if __name__ == "__main__":
    asyncio.run(test_microdrama())

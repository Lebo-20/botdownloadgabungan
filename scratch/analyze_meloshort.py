import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_meloshort():
    base_url = "https://captain.sapimu.au/meloshort/api/v1"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    lang = "th" # Use 'en' or 'id' for testing
    
    async with httpx.AsyncClient() as client:
        # Testing list
        print("--- Testing List ---")
        res = await client.get(f"{base_url}/dramas?page=1&limit=5&lang={lang}", headers=headers)
        print(f"List Status: {res.status_code}")
        data = res.json()
        print(f"List Keys: {list(data.keys())}")
        
        data_content = data.get("data", {})
        print(f"Raw data_content type: {type(data_content)}")
        if isinstance(data_content, dict):
            print(f"Data content keys: {list(data_content.keys())}")
            dramas = data_content.get("rows") or data_content.get("list") or data_content.get("items") or []
        else:
            dramas = data_content or []
            
        if dramas:
            drama = dramas[0]
            print(f"First Drama Keys: {list(drama.keys())}")
            drama_id = drama.get('drama_id')
            print(f"First Drama: {drama.get('drama_title')} ({drama_id})")
            
            # Testing episodes
            print(f"\n--- Testing Episodes for {drama_id} ---")
            res_eps = await client.get(f"{base_url}/dramas/{drama_id}/episodes?page=1&limit=10&lang={lang}", headers=headers)
            eps_data = res_eps.json()
            print(f"Episodes keys: {list(eps_data.keys())}")
            
            episodes = eps_data.get("data", [])
            if isinstance(episodes, dict):
                episodes = episodes.get("rows") or episodes.get("list") or []

            if episodes:
                ep = episodes[0]
                print(f"First Ep Keys: {list(ep.keys())}")
                ep_id = ep.get('chapter_id')
                print(f"First Ep: {ep.get('chapter_name')} ({ep_id})")
                
                # Testing stream URL
                print(f"\n--- Testing Stream for Drama {drama_id} Ep {ep_id} ---")
                res_stream = await client.get(f"{base_url}/dramas/{drama_id}/episodes/{ep_id}?lang={lang}", headers=headers)
                stream_data = res_stream.json()
                print(f"Stream status: {res_stream.status_code}")
                # Print sample of where the URL might be
                print(f"Stream keys: {list(stream_data.keys())}")
                if "data" in stream_data:
                    s_data = stream_data["data"]
                    print(f"Stream data keys: {list(s_data.keys())}")
                    print(f"Stream URL: {s_data.get('play_url') or s_data.get('play_url_720p') or s_data.get('url')}")

if __name__ == "__main__":
    asyncio.run(test_meloshort())

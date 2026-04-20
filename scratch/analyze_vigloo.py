import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_vigloo():
    base_url = "https://captain.sapimu.au/vigloo/api/v1"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    lang = "en"
    
    async with httpx.AsyncClient() as client:
        # Testing browse
        print("--- Testing Browse ---")
        res = await client.get(f"{base_url}/browse?sort=POPULAR&limit=5&lang=id", headers=headers)
        print(f"Browse Status: {res.status_code}")
        data = res.json()
        
        items = data.get("data", [])
        if not items:
            print("No items found. Trying search...")
            res = await client.get(f"{base_url}/search?q=love&limit=5&lang=id", headers=headers)
            data = res.json()
            items = data.get("data", [])
            
        if items:
            drama = items[0]
            program_id = drama.get('programId') or drama.get('id')
            print(f"First Drama ID: {program_id}")
            
            # Testing drama detail
            print(f"\n--- Testing Detail for {program_id} ---")
            res_det = await client.get(f"{base_url}/drama/{program_id}?lang={lang}", headers=headers)
            det_data = res_det.json()
            print(f"Detail keys: {list(det_data.keys())}")
            
            detail = det_data.get("data", {})
            print(f"Detail data keys: {list(detail.keys())}")
            
            # Find seasonId
            season_id = None
            if "seasons" in detail and detail["seasons"]:
                season_id = detail["seasons"][0].get("id")
            elif "seasonId" in detail:
                season_id = detail["seasonId"]
            
            print(f"Season ID found: {season_id}")
            
            if program_id and season_id:
                # Testing episode list
                print(f"\n--- Testing episodes for Program {program_id} Season {season_id} ---")
                res_eps = await client.get(f"{base_url}/drama/{program_id}/season/{season_id}/episodes?lang={lang}", headers=headers)
                eps_data = res_eps.json()
                print(f"Episodes Status: {res_eps.status_code}")
                
                episodes = eps_data.get("data", [])
                if episodes:
                    ep = episodes[0]
                    print(f"First Ep keys: {list(ep.keys())}")
                    ep_no = ep.get('ep') or 1
                    
                    # Testing stream
                    print(f"\n--- Testing Stream for Season {season_id} Ep {ep_no} ---")
                    res_stream = await client.get(f"{base_url}/stream?seasonId={season_id}&ep={ep_no}", headers=headers)
                    print(f"Stream Status: {res_stream.status_code}")
                    print(f"Stream Response: {res_stream.text[:200]}")

if __name__ == "__main__":
    asyncio.run(test_vigloo())

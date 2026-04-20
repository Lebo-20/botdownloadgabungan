import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_snackshort():
    base_url = "https://captain.sapimu.au/snackshort/api/v1"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    lang = "Indonesian"
    
    async with httpx.AsyncClient() as client:
        # Testing browsing
        print("--- Testing Browsing ---")
        res = await client.get(f"{base_url}/browsing?page=1&pageSize=5&lang={lang}", headers=headers)
        print(f"Browsing Status: {res.status_code}")
        data = res.json()
        print(f"Browsing Keys: {list(data.keys())}")
        
        data_content = data.get("data", {})
        if isinstance(data_content, dict) and "data" in data_content:
            data_content = data_content["data"]
            
        print(f"Innermost data type: {type(data_content)}")
        if isinstance(data_content, dict):
            print(f"Innermost data keys: {list(data_content.keys())}")
            dramas = data_content.get("items") or data_content.get("list") or data_content.get("rows") or []
        else:
            dramas = data_content or []
            
        if dramas:
            drama = dramas[0]
            print(f"First Drama Keys: {list(drama.keys())}")
            if "chapter" in drama and isinstance(drama["chapter"], dict):
                print(f"Chapter keys: {list(drama['chapter'].keys())}")
            
            if "book" in drama:
                print(f"Book keys: {list(drama['book'].keys())}")
                drama_id = drama['book'].get('book_id') or drama['book'].get('id')
            else:
                drama_id = drama.get('book_id') or drama.get('bookId') or drama.get('id')
            
            # Testing detail
            print(f"\n--- Testing Detail {drama_id} ---")
            res_det = await client.get(f"{base_url}/book/{drama_id}?lang={lang}", headers=headers)
            det_data = res_det.json()
            print(f"Detail keys: {list(det_data.keys())}")
            
            detail_content = det_data.get("data", {})
            if isinstance(detail_content, dict) and "data" in detail_content:
                detail_content = detail_content["data"]
            
            print(f"Detail content type: {type(detail_content)}")
            if isinstance(detail_content, dict):
                print(f"Detail content keys: {list(detail_content.keys())}")
                for k, v in detail_content.items():
                    print(f"  {k}: {type(v)}")
                
                if "book" in detail_content and isinstance(detail_content["book"], dict):
                    print(f"Detail book keys: {list(detail_content['book'].keys())}")
                    for k, v in detail_content["book"].items():
                        print(f"    {k}: {type(v)}")
                
                # Try to find a list
                episodes = None
                for k, v in detail_content.items():
                    if isinstance(v, list) and v:
                        print(f"Found list in root key: {k}")
                        episodes = v
                        break
                
                if not episodes and "book" in detail_content:
                    for k, v in detail_content["book"].items():
                        if isinstance(v, list) and v:
                            print(f"Found list in book key: {k}")
                            episodes = v
                            break
                
                if episodes:
                    ep = episodes[0]
                    print(f"First Ep keys: {list(ep.keys())}")
                    ep_id = ep.get('chapter_id') or ep.get('id')
                    print(f"First Ep: {ep.get('chapter_name') or ep.get('name')} ({ep_id})")
                    
                    # Testing stream URL
                    print(f"\n--- Testing Stream for Drama {drama_id} Ep {ep_id} ---")
                    res_stream = await client.get(f"{base_url}/book/{drama_id}/episode/{ep_id}?lang={lang}", headers=headers)
                    stream_data = res_stream.json()
                    print(f"Stream status: {res_stream.status_code}")
                    
                    s_wrap = stream_data.get("data", {})
                    if isinstance(s_wrap, dict) and "data" in s_wrap:
                        s_wrap = s_wrap["data"]
                    
                    if isinstance(s_wrap, dict):
                        print(f"Stream keys: {list(s_wrap.keys())}")
                        url = s_wrap.get('play_url') or s_wrap.get('url') or s_wrap.get('video_url')
                        print(f"Stream URL: {url[:30] if url else 'None'}...")

def drama_content_to_str(drama):
    try:
        return drama.get('bookName') or drama.get('title') or drama.get('name')
    except:
        return "Unknown"

if __name__ == "__main__":
    asyncio.run(test_snackshort())

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_snack_stream():
    base_url = "https://captain.sapimu.au/snackshort/api/v1"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    lang = "Indonesian"
    
    async with httpx.AsyncClient() as client:
        # Get detail first
        book_id = 129
        print(f"--- Fetching Detail for {book_id} ---")
        res_det = await client.get(f"{base_url}/book/{book_id}?lang={lang}", headers=headers)
        det_data = res_det.json()
        
        detail = det_data.get("data", {}).get("data", {})
        if not detail:
            print("No detail found")
            return
            
        chapter = detail.get("chapter", {})
        chapter_id = chapter.get("chapter_id")
        is_locked = detail.get("is_lock")
        play_url = detail.get("play_url")
        print(f"Chapter ID: {chapter_id}, Locked: {is_locked}, Play URL: {play_url is not None}")
        
        if not chapter_id:
            print("No chapter ID")
            return
            
        # Fetch stream
        print(f"--- Fetching Stream for {book_id} / {chapter_id} ---")
        res_stream = await client.get(f"{base_url}/book/{book_id}/episode/{chapter_id}?lang={lang}", headers=headers)
        stream_data = res_stream.json()
        print(f"Raw Stream Response: {stream_data}")

if __name__ == "__main__":
    asyncio.run(test_snack_stream())

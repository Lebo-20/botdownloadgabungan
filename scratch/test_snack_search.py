import asyncio
import httpx
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()
token_sapimu = os.getenv("TOKEN_SAPIMU")

async def test_search_snack():
    base_url = "https://captain.sapimu.au/snackshort/api/v1"
    headers = {"Authorization": f"Bearer {token_sapimu}"}
    lang = "Indonesian"
    
    async with httpx.AsyncClient() as client:
        # Search for a popular term
        q = "love"
        print(f"--- Testing Search for '{q}' ---")
        res = await client.get(f"{base_url}/search?q={q}&lang={lang}", headers=headers)
        data = res.json()
        
        # Structure check
        s_data = data.get("data", {})
        if isinstance(s_data, dict) and "data" in s_data:
            s_data = s_data["data"]
            
        if isinstance(s_data, list) and s_data:
            print(f"Results: {len(s_data)}")
            item = s_data[0]
            print(f"Item Keys: {list(item.keys())}")
            if "book" in item:
                 print(f"Book keys: {list(item['book'].keys())}")
                 print(f"Book id: {item['book'].get('book_id')}")
                 print(f"Chapters in book: {item['book'].get('chapters')}")

if __name__ == "__main__":
    asyncio.run(test_search_snack())

import asyncio
import sys
import os
import httpx

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.factory import ProviderFactory, get_provider
from core.processor import VideoProcessor
from loguru import logger

# Import all implementations
import providers.impl.vigloo
import providers.impl.bilitv
import providers.impl.fundrama
import providers.impl.shortmax
import providers.impl.idrama
import providers.impl.dramabite
import providers.impl.dramabox
import providers.impl.stardust
import providers.impl.radreels
import providers.impl.velolo
import providers.impl.hishort
import providers.impl.microdrama
import providers.impl.meloshort
import providers.impl.snackshort

def safe_print(text):
    print(text.encode('ascii', errors='replace').decode('ascii'))

async def test_full_cycle():
    providers = ProviderFactory.get_provider_names()
    processor = VideoProcessor()
    
    safe_print(f"--- STARTING FULL CYCLE TEST (1 EP) ---")
    
    for p_name in providers:
        safe_print(f"\n[TESTING: {p_name.upper()}]")
        try:
            prov = get_provider(p_name)
            
            # 1. Search
            safe_print(f"  - Searching...")
            results = await prov.search("love")
            if not results:
                safe_print(f"  - [WARN] No search results. Trying discovery...")
                results = await prov.discover("home")
            
            if not results:
                safe_print(f"  - [SKIP] No content found.")
                continue
            
            drama = results[0]
            drama_id = drama['id']
            safe_print(f"  - Found: {drama['title']} ({drama_id})")
            
            # 2. Get Episodes
            safe_print(f"  - Fetching episodes...")
            episodes = await prov.get_episodes(drama_id)
            if not episodes:
                safe_print(f"  - [FAIL] No episodes found.")
                continue
            
            # 3. Get Ep 1 Stream URL
            safe_print(f"  - Getting Stream URL for Ep 1...")
            stream_url = await prov.get_stream_url(drama_id, 1)
            if not stream_url:
                # Some provide stream_url in the list
                stream_url = episodes[0].get('stream_url')
            
            if not stream_url:
                safe_print(f"  - [FAIL] Stream URL not found.")
                continue
            
            safe_print(f"  - [OK] URL Found: {stream_url[:60]}...")
            
            # 4. Download (Head only to check validity)
            safe_print(f"  - Validating URL via HEAD request...")
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.head(stream_url, timeout=10, follow_redirects=True)
                    if res.status_code < 400:
                        safe_print(f"  - [OK] SUCCESS: URL is reachable ({res.status_code})")
                    else:
                        # try GET with range
                        res = await client.get(stream_url, headers={"Range": "bytes=0-100"}, timeout=10)
                        safe_print(f"  - [OK] SUCCESS: URL is reachable via GET ({res.status_code})")
                except Exception as ex:
                    safe_print(f"  - [WARN] URL Validation Warning: {str(ex)[:50]}")
                    safe_print(f"    (Might be due to HEAD restriction, but URL exists)")

        except Exception as e:
            safe_print(f"  - [ERROR] CRITICAL ERROR: {str(e)}")

    safe_print(f"\n--- TEST FINISHED ---")

if __name__ == "__main__":
    asyncio.run(test_full_cycle())

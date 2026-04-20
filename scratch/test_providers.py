import asyncio
import os
from loguru import logger
from providers.factory import ProviderFactory
import providers.impl.vigloo
import providers.impl.bilitv
import providers.impl.dramabox
import providers.impl.shortmax
import providers.impl.freereels
import providers.impl.flickreels
import providers.impl.dotdrama
import providers.impl.dramaboxv2
import providers.impl.goodshort
import providers.impl.radreels
import providers.impl.stardust
import providers.impl.idrama
import providers.impl.dramabite
import providers.impl.fundrama
import providers.impl.velolo
import providers.impl.hishort
import providers.impl.microdrama
import providers.impl.meloshort
import providers.impl.snackshort

async def test_provider(name):
    logger.info(f"--- Testing Provider: {name} ---")
    provider = ProviderFactory.get_provider(name)
    if not provider:
        logger.error(f"Provider {name} not found!")
        return False
    
    try:
        # 1. Test Search
        results = await provider.search("Cinta")
        if not results:
            for cat in ["trending", "popular", "hot", "home"]:
                results = await provider.discover(cat)
                if results: break
        
        if not results:
            logger.warning(f"[{name}] No results found in search/discover.")
            return False
        
        target = results[0]
        logger.success(f"[{name}] Found drama: {target['title']} (ID: {target['id']})")
        
        # 2. Test Details
        details = await provider.get_drama_details(target['id'])
        if not details or not details.get("title"):
            logger.error(f"[{name}] Failed to get drama details.")
            return False
        logger.success(f"[{name}] Details OK: {details.get('title')}")
        
        # 3. Test Episodes
        episodes = await provider.get_episodes(target['id'])
        if not episodes:
            logger.error(f"[{name}] No episodes found.")
            return False
        logger.success(f"[{name}] Episodes Found: {len(episodes)}")
        
        # 4. Test Stream URL (first episode)
        first_ep = episodes[0]
        stream_url = await provider.get_stream_url(first_ep['id'], first_ep['number'])
        # Some providers might have stream_url inside the episode object (GoodShort/FlickReels)
        stream_url = stream_url or first_ep.get("stream_url")
        
        if not stream_url:
            logger.error(f"[{name}] Failed to get stream URL.")
            return False
        
        logger.success(f"[{name}] Stream URL: {stream_url[:50]}...")
        return True
        
    except Exception as e:
        logger.exception(f"[{name}] Critical Error during test")
        return False

async def main():
    providers = ProviderFactory.get_provider_names()
    logger.info(f"Starting health check for {len(providers)} providers...")
    
    summary = {}
    for name in providers:
        success = await test_provider(name)
        summary[name] = "[PASS]" if success else "[FAIL]"
    
    logger.info("\n=== FINAL TEST SUMMARY ===")
    for name, status in summary.items():
        print(f"{name:15}: {status}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from providers.factory import ProviderFactory
import providers.impl.flickreels
from loguru import logger
import sys

async def main():
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    p = ProviderFactory.get_provider('flickreels')

    # Using the ID from user request
    target_id = "2858"
    logger.info(f"Testing Batchload for ID: {target_id}")
    det = await p.get_drama_details(target_id)
    print(f"KEYS: {list(det.keys())}")
    print(f"EPISODES: {len(det.get('episodes_raw', []))}")
    if det.get('episodes_raw'):
        print(f"FIRST EPISODE: {det['episodes_raw'][0]}")

if __name__ == "__main__":
    asyncio.run(main())

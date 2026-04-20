import asyncio
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.factory import ProviderFactory, get_provider
from loguru import logger

# Import all implementations for registration
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

async def test_all():
    providers = ProviderFactory.get_provider_names()
    print(f"--- TESTING {len(providers)} PROVIDERS ---")
    
    results = {}
    for p_name in providers:
        print(f"Testing [{p_name}]...", end=" ", flush=True)
        try:
            prov = get_provider(p_name)
            search_res = await prov.search("love")
            count = len(search_res)
            
            if count > 0:
                print(f"[OK] ({count} items found)")
                results[p_name] = f"Success ({count})"
            else:
                # Try empty search or fallback
                print(f"[EMPTY] (No results)")
                results[p_name] = "Empty"
        except Exception as e:
            print(f"[FAIL] : {str(e)[:50]}...")
            results[p_name] = f"Error: {str(e)[:30]}"
            
    print("\n--- SUMMARY ---")
    for p, status in results.items():
        print(f"{p:15} : {status}")

if __name__ == "__main__":
    asyncio.run(test_all())

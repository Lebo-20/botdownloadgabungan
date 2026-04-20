import asyncio
import httpx
import os
import sys

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from providers.impl.velolo import VeloloProvider

async def test_velolo():
    prov = VeloloProvider()
    print("--- Testing Velolo Discovery (HOT) ---")
    results = await prov.discover("home")
    if results:
        print(f"Found {len(results)} dramas")
        for r in results[:3]:
            print(f"- {r['title']} ({r['id']})")
            
            print(f"  Fetching episodes for {r['id']}...")
            eps = await prov.get_episodes(r['id'])
            print(f"  Found {len(eps)} episodes")
            if eps:
                print(f"  Ep 1 URL: {eps[0].get('stream_url')[:60]}...")
    else:
        print("No results found.")

if __name__ == "__main__":
    asyncio.run(test_velolo())

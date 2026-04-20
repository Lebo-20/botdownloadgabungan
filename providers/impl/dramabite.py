from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class DramaBiteProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://dramabite.dramabos.my.id"
        self.global_code = settings.token_dramabos

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "lang": "id"
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            # Extract results
            if data is None: return []
            results = data if isinstance(data, list) else data.get("data", [])
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("cid") or item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "dramabite",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"DramaBite Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/drama/{drama_id}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            return data if isinstance(data, dict) else data.get("data", {})
        except Exception as e:
            logger.error(f"DramaBite Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/episodes/{drama_id}"
        params = {
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            episodes = data if isinstance(data, list) else data.get("data", [])
            
            normalized = []
            for ep in episodes:
                normalized.append({
                    "id": str(ep.get("vid") or ep.get("id") or ep.get("episode_id")),
                    "number": ep.get("episode_no") or ep.get("number") or ep.get("index"),
                    "title": f"Episode {ep.get('episode_no') or ep.get('number') or ep.get('index')}"
                })
            return normalized
        except Exception as e:
            logger.error(f"DramaBite Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # video_id in this context is cid (drama_id)
        url = f"{self.base_url}/play/{video_id}/{episode_no}"
        params = {
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            return data.get("url") or data.get("data", {}).get("url") or data.get("play_url")
        except Exception as e:
            logger.error(f"DramaBite Play Error: {e}")
            return None

# Register the provider
ProviderFactory.register("dramabite", DramaBiteProvider)

from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class BiliTVProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://bilitv.dramabos.my.id/api"
        self.global_code = settings.token_dramabos

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {"q": query, "lang": "id"}
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            # Better handling for nested structures like {"data": {"records": [...]}}
            results = data
            if isinstance(data, dict):
                # Try getting 'data' -> 'records' or just 'data' or 'list'
                results = data.get("data", [])
                if isinstance(results, dict):
                    results = results.get("records") or results.get("list") or [results]
                elif not isinstance(results, list):
                    results = [results]
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "bilitv",
                    "poster": item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"BiliTV Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/short/{drama_id}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"BiliTV Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/short/{drama_id}/episode"
        
        try:
            response = await self.client.get(url)
            data = response.json()
            # Better handling for nested structures
            episodes = data
            if isinstance(data, dict):
                episodes = data.get("data", [])
                if isinstance(episodes, dict):
                    episodes = episodes.get("records") or episodes.get("list") or [episodes]
                elif not isinstance(episodes, list):
                    episodes = [episodes]

            normalized = []
            for i, ep in enumerate(episodes, 1):
                if not isinstance(ep, dict): continue
                ep_id = str(ep.get("id") or i)
                ep_num = ep.get("episode_no") or ep.get("number") or i
                normalized.append({
                    "id": ep_id,
                    "number": ep_num,
                    "title": f"Episode {ep_num}"
                })
            return normalized
        except Exception as e:
            logger.error(f"BiliTV Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # The user provided: /api/stream/:id/:ep?quality=720&lang=id&code=TOKEN
        # Note: video_id here usually refers to the drama_id in this context
        url = f"{self.base_url}/stream/{video_id}/{episode_no}"
        params = {
            "quality": "720",
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            # Often it's in a 'url' or 'data' field
            return data.get("url") or data.get("data", {}).get("url")
        except Exception as e:
            logger.error(f"BiliTV Stream URL Error: {e}")
            return None

    async def get_subtitle_url(self, drama_id: str, episode_no: int = 1) -> Optional[str]:
        # The user provided: /api/subtitle/:id/:ep?lang=id&format=json&code=TOKEN
        url = f"{self.base_url}/subtitle/{drama_id}/{episode_no}"
        params = {
            "lang": "id",
            "format": "json",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            return data.get("url") or data.get("data", {}).get("url")
        except Exception as e:
            logger.error(f"BiliTV Subtitle Error: {e}")
            return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        # /api/home for BiliTV discovery
        url = f"{self.base_url}/home"
        try:
            response = await self.client.get(url, params={"lang": "id"})
            data = response.json()
            results = data if isinstance(data, list) else data.get("data", [])
            
            # Handle nested records if any
            if isinstance(results, dict):
                results = results.get("records") or results.get("list") or [results]

            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "bilitv",
                    "poster": item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"BiliTV Discovery Error: {e}")
            return []

# Register the provider
ProviderFactory.register("bilitv", BiliTVProvider)

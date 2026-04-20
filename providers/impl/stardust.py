from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class StardustTVProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/stardusttv/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.token_sapimu}"
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # Search endpoint: /api/v1/search?q=...&lang=id
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "lang": "id",
            "page": 1,
            "page_size": 20
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # Stardust returns results in data -> list or just data
            results = data.get("data", [])
            if isinstance(results, dict):
                results = results.get("list") or results.get("rows") or []
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or "No Title",
                    "platform": "stardust",
                    "poster": item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"Stardust Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        # Detail endpoint: /api/v1/video/:id
        url = f"{self.base_url}/video/{drama_id}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            if data.get("success") and "data" in data:
                detail = data["data"]
                return {
                    "id": str(detail.get("id")),
                    "title": detail.get("title"),
                    "description": detail.get("intro"),
                    "poster": detail.get("poster"),
                    "episodes_raw": detail.get("episodes", [])
                }
            return {}
        except Exception as e:
            logger.error(f"Stardust Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        details = await self.get_drama_details(drama_id)
        episodes_raw = details.get("episodes_raw", [])
        
        normalized = []
        for i, ep in enumerate(episodes_raw, 1):
            if not isinstance(ep, dict): continue
            
            # Use sort or index as number
            episode_num = ep.get("sort") or i
            
            normalized.append({
                "id": str(ep.get("id")),
                "number": episode_num,
                "title": f"Episode {episode_num}"
            })
        
        return normalized

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # Stream endpoint: /api/v1/video/:id/episode/:episode
        # video_id is the drama_id
        url = f"{self.base_url}/video/{video_id}/episode/{episode_no}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            if data.get("success") and "data" in data:
                ep_data = data["data"]
                return ep_data.get("h264") or ep_data.get("url") or ep_data.get("h265")
            return None
        except Exception as e:
            logger.error(f"Stardust Stream URL Error: {e}")
            return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        url = f"{self.base_url}/homepage"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            results = data.get("data", [])
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or "No Title",
                    "platform": "stardust",
                    "poster": item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"Stardust Discovery Error: {e}")
            return []

# Register the provider
ProviderFactory.register("stardust", StardustTVProvider)

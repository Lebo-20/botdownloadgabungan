from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class DotDramaProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/dotdrama/api/v1"
        self.token = settings.token_sapimu
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.lang = "id"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # DotDrama search pattern: typically dramas?q= or dramas?query=
        url = f"{self.base_url}/dramas"
        params = {
            "q": query,
            "page": 1,
            "limit": 20,
            "lang": self.lang
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # DotDrama structure
            items = data if isinstance(data, list) else data.get("data", [])
            if isinstance(items, dict):
                items = items.get("rows") or items.get("list") or [items]

            normalized = []
            for item in items:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "dotdrama",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"DotDrama Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/dramas/{drama_id}"
        
        try:
            response = await self.client.get(url, headers=self.headers)
            data = response.json()
            # Detail might be nested or direct
            detail = data.get("data") if isinstance(data, dict) else data
            if not isinstance(detail, dict): detail = {}

            return {
                "id": drama_id,
                "title": detail.get("title"),
                "description": detail.get("description"),
                "poster": detail.get("poster") or detail.get("cover"),
                "total_episodes": len(detail.get("episodes", [])),
                "episodes_raw": detail.get("episodes", [])
            }
        except Exception as e:
            logger.error(f"DotDrama Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        details = await self.get_drama_details(drama_id)
        episodes_raw = details.get("episodes_raw", [])
        
        normalized = []
        for i, ep in enumerate(episodes_raw, 1):
            if not isinstance(ep, dict): continue
            
            ep_num = ep.get("number") or ep.get("index") or i
            # DotDrama detail includes video URL
            normalized.append({
                "id": str(ep.get("id") or i),
                "number": ep_num,
                "title": ep.get("title") or f"Episode {ep_num}",
                "stream_url": ep.get("url") or ep.get("video_url") or ep.get("play_url")
            })
        return normalized

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # Typically the 'dramas/:id' endpoint already provided stream URLs for all episodes.
        # But if video_id is passed, we check if it's the stream URL directly or search in ep list.
        if video_id.startswith("http"): return video_id
        
        # Fallback: search in episodes list
        # Note: video_id here would be the drama_id if called from the bot's standard flow
        episodes = await self.get_episodes(video_id)
        for ep in episodes:
            if str(ep.get("number")) == str(episode_no):
                return ep.get("stream_url")
        return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        if category == "latest":
            url = f"{self.base_url}/dramas"
            params = {"page": 1, "limit": 20, "lang": self.lang}
        else:
            # collections endpoint
            url = f"{self.base_url}/collections"
            params = {"lang": self.lang}
            
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # Simple list extraction
            items = data if isinstance(data, list) else data.get("data", [])
            if isinstance(items, dict):
                items = items.get("rows") or items.get("list") or []

            normalized = []
            for item in items:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "dotdrama",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"DotDrama Discovery Error ({category}): {e}")
            return []

# Register
ProviderFactory.register("dotdrama", DotDramaProvider)

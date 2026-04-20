from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class FunDramaProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://drakula.dramabos.my.id/api/fundrama"
        self.global_code = settings.token_dramabos

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            # Extract results
            results = data if isinstance(data, list) else data.get("data", [])
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "fundrama",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"FunDrama Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/drama/{drama_id}"
        params = {"code": self.global_code}
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"FunDrama Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/drama/{drama_id}/episodes"
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
                    "id": str(ep.get("id")),
                    "number": ep.get("episode_no") or ep.get("number"),
                    "title": f"Episode {ep.get('episode_no') or ep.get('number')}",
                    "stream_url": ep.get("video_url") or ep.get("play_url") # Try to find video url
                })
            return normalized
        except Exception as e:
            logger.error(f"FunDrama Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # Note: FunDrama stream URL is likely in the episode list response.
        # If it needs a separate call, we'd implement it here.
        # For now, we try to gather it from episodes list if possible or return None.
        # If the user provides a specific stream endpoint later, we can update this.
        logger.warning(f"FunDrama get_stream_url called for {video_id} Ep {episode_no}. Checking episodes...")
        episodes = await self.get_episodes(video_id)
        for ep in episodes:
            if str(ep.get("number")) == str(episode_no):
                return ep.get("stream_url")
        return None

# Register the provider
ProviderFactory.register("fundrama", FunDramaProvider)

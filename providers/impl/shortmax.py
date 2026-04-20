from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class ShortMaxProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://shortmax.dramabos.my.id/api/v1"
        self.global_code = settings.token_dramabos

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "lang": "id",
            "q": query
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            # Better handling for nested structures
            results = []
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict):
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
                    "platform": "shortmax",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"ShortMax Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/detail/{drama_id}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            return data if isinstance(data, dict) else data.get("data", {})
        except Exception as e:
            logger.error(f"ShortMax Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/alleps/{drama_id}"
        params = {
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            # Better handling for nested structures and error strings
            episodes = []
            if isinstance(data, list):
                episodes = data
            elif isinstance(data, dict):
                episodes = data.get("data", [])
                if isinstance(episodes, dict):
                    episodes = episodes.get("episodes") or episodes.get("records") or episodes.get("list") or [episodes]
                elif not isinstance(episodes, list):
                    episodes = [episodes]
            
            normalized = []
            for ep in episodes:
                if not isinstance(ep, dict): continue
                # Extract stream URL from nested video object if present
                video_obj = ep.get("video")
                stream_url = ep.get("video_url") or ep.get("play_url") or ep.get("url")
                
                if isinstance(video_obj, dict):
                    stream_url = stream_url or video_obj.get("video_1080") or video_obj.get("video_720") or video_obj.get("video_480")

                normalized.append({
                    "id": str(ep.get("id")),
                    "number": ep.get("episode_no") or ep.get("number") or ep.get("index") or ep.get("episode"),
                    "title": f"Episode {ep.get('episode_no') or ep.get('number') or ep.get('index') or ep.get('episode')}",
                    "stream_url": stream_url
                })
            return normalized
        except Exception as e:
            logger.error(f"ShortMax Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # Typically ShortMax provides all info in the 'alleps' endpoint
        logger.info(f"ShortMax searching stream for {video_id} Ep {episode_no}")
        episodes = await self.get_episodes(video_id)
        for ep in episodes:
            if str(ep.get("number")) == str(episode_no):
                return ep.get("stream_url")
        return None

# Register the provider
ProviderFactory.register("shortmax", ShortMaxProvider)

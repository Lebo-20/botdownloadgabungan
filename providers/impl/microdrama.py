from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class MicroDramaProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/microdrama/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.token_sapimu}"
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # Search endpoint: /api/v1/dramas/search?q=...&lang=id
        url = f"{self.base_url}/dramas/search"
        params = {
            "q": query,
            "lang": "id"
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # MicroDrama usually returns a list of dramas in 'dramas' or 'data'
            results = data.get("dramas") or data.get("data") or []
            if isinstance(results, dict):
                results = results.get("rows") or results.get("list") or [results]
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "microdrama",
                    "poster": item.get("cover") or item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"MicroDrama Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        # Detail endpoint: /api/v1/dramas/:id
        url = f"{self.base_url}/dramas/{drama_id}"
        
        try:
            response = await self.client.get(url, headers=self.headers)
            data = response.json()
            # Returns { drama: {...}, episodes: [...] }
            if isinstance(data, dict) and "drama" in data:
                drama = data["drama"]
                return {
                    "id": str(drama.get("id")),
                    "title": drama.get("title"),
                    "description": drama.get("description"),
                    "poster": drama.get("cover"),
                    "episodes_raw": data.get("episodes", [])
                }
            return data
        except Exception as e:
            logger.error(f"MicroDrama Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        details = await self.get_drama_details(drama_id)
        episodes_raw = details.get("episodes_raw", [])
        
        normalized = []
        for i, ep in enumerate(episodes_raw, 1):
            if not isinstance(ep, dict): continue
            
            # Extract stream URL from 'videos' list
            stream_url = None
            videos = ep.get("videos", [])
            if isinstance(videos, list) and videos:
                # Use first available video quality
                stream_url = videos[0].get("url") or videos[0].get("m3u8")
            
            if not stream_url:
                stream_url = ep.get("url") or ep.get("video_url") or ep.get("play_url")

            # Episode number is usually 'index'
            episode_num = ep.get("index") or i
            
            normalized.append({
                "id": f"{drama_id}_{episode_num}",
                "number": episode_num,
                "title": f"Episode {episode_num}",
                "stream_url": stream_url
            })
        
        return normalized

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # If video_id contains underscore, it's likely our internal {drama}_{ep} format
        drama_id = video_id.split("_")[0] if "_" in video_id else video_id
        
        episodes = await self.get_episodes(drama_id)
        for ep in episodes:
            if str(ep.get("number")) == str(episode_no):
                return ep.get("stream_url")
        return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        # Map categories to the /dramas endpoint with different limits or sorting if available
        # Based on docs, we just have /dramas
        url = f"{self.base_url}/dramas"
        params = {"lang": "id", "limit": 20}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            results = data.get("dramas", [])
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "microdrama",
                    "poster": item.get("cover") or item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"MicroDrama Discovery Error: {e}")
            return []

    def get_supported_categories(self) -> List[Dict[str, str]]:
        return [{"id": "home", "label": "🏠 Home"}]

# Register the provider
ProviderFactory.register("microdrama", MicroDramaProvider)

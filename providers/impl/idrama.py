from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class IDramaProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://idrama.dramabos.my.id"
        self.global_code = settings.token_dramabos

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "lang": "id",
            "page": "1"
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            # iDrama search results are typically in the 'results' key
            if isinstance(data, dict):
                results = data.get("results") or data.get("data", [])
            else:
                results = data if isinstance(data, list) else []
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id") or item.get("bookId")),
                    "title": item.get("short_play_name") or item.get("title") or item.get("name") or "No Title",
                    "platform": "idrama",
                    "poster": item.get("cover_url") or item.get("poster") or item.get("cover") or item.get("bookCover")
                })
            return normalized
        except Exception as e:
            logger.error(f"iDrama Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/drama/{drama_id}"
        params = {
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            return data if isinstance(data, dict) else data.get("data", {})
        except Exception as e:
            logger.error(f"iDrama Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        # Usually iDrama detail returns episodes list directly
        data = await self.get_drama_details(drama_id)
        
        # Flexibly find the episodes list
        episodes = []
        if isinstance(data, dict):
            # Check root keys
            episodes = data.get("episodes") or data.get("list") or data.get("records") or \
                       data.get("chapter_list") or data.get("chapters")
            # Check nested data
            if not episodes and "data" in data:
                d = data["data"]
                if isinstance(d, dict):
                    episodes = d.get("episodes") or d.get("list") or d.get("records") or \
                               d.get("chapter_list") or d.get("chapters") or [d]

                elif isinstance(d, list):
                    episodes = d
            elif not episodes:
                # Might be the data itself if it's a list
                episodes = data if isinstance(data, list) else []

        normalized = []
        for i, ep in enumerate(episodes or [], 1):
            if not isinstance(ep, dict): continue
            
            raw_id = ep.get("id") or ep.get("episode_id") or ep.get("chapterId") or i
            raw_num = ep.get("episode_no") or ep.get("number") or ep.get("chapterIndex") or i
            
            normalized.append({
                "id": str(raw_id),
                "number": int(raw_num) if str(raw_num).isdigit() else i,
                "title": ep.get("title") or f"Episode {raw_num}"
            })
        return normalized

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # iDrama has an 'unlock' endpoint for the stream URL
        url = f"{self.base_url}/unlock/{video_id}/{episode_no}"
        params = {
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            # Try to find the URL in response
            return data.get("url") or data.get("data", {}).get("url") or data.get("play_url")
        except Exception as e:
            logger.error(f"iDrama Unlock Error: {e}")
            return None

# Register the provider
ProviderFactory.register("idrama", IDramaProvider)

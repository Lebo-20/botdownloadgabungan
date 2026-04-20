from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class DramaBoxProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://dramabox.dramabos.my.id/api/v1"
        self.global_code = settings.token_dramabos

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "query": query,
            "lang": "id"
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
                    "id": str(item.get("bookId") or item.get("id")),
                    "title": item.get("title") or item.get("name") or item.get("bookName") or "No Title",
                    "platform": "dramabox",
                    "poster": item.get("poster") or item.get("cover") or item.get("bookCover")
                })
            return normalized
        except Exception as e:
            logger.error(f"DramaBox Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/detail"
        params = {
            "bookId": drama_id,
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            if isinstance(data, dict) and "data" in data:
                return data["data"]
            return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"DramaBox Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/allepisode"
        params = {
            "bookId": drama_id,
            "lang": "id",
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            # Often it's in data['episodes'] or data['list']
            episodes = data if isinstance(data, list) else data.get("data", {}).get("episodes", [])
            if not episodes and isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                episodes = data["data"]

            normalized = []
            for i, ep in enumerate(episodes, 1):
                # Priority: chapterIndex -> episode_no -> number -> chapterNo
                raw_num = ep.get("chapterIndex") or ep.get("episode_no") or ep.get("number") or ep.get("chapterNo")
                episode_num = int(raw_num) if raw_num is not None else i
                
                # Priority for stream URL: 1080p -> videoUrl -> play_url ...
                stream_url = ep.get("1080p") or ep.get("720p") or ep.get("videoUrl") or ep.get("video_url") or ep.get("play_url") or ep.get("url")
                
                normalized.append({
                    "id": str(ep.get("chapterId") or ep.get("id") or i),
                    "number": episode_num,
                    "title": f"Episode {episode_num}",
                    "stream_url": stream_url
                })
            return normalized
        except Exception as e:
            logger.error(f"DramaBox Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # Typically provided in the allepisode list for DramaBox
        episodes = await self.get_episodes(video_id)
        for ep in episodes:
            if str(ep.get("number")) == str(episode_no):
                return ep.get("stream_url")
        return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        category_map = {
            "home": "homepage",
            "latest": "latest",
            "foryou": "foryou",
            "dubbed": "dubbed"
        }
        endpoint = category_map.get(category, "homepage")
        url = f"{self.base_url}/{endpoint}"
        params = {"lang": "id", "page": 1}
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            
            # Hybrid extraction for BiliTV discovery
            results = data
            if isinstance(data, dict):
                results = data.get("recommendList") or data.get("data") or []
            
            if not isinstance(results, list):
                results = []
                
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("bookId") or item.get("id")),
                    "title": item.get("title") or item.get("name") or item.get("bookName") or "No Title",
                    "platform": "dramabox",
                    "poster": item.get("poster") or item.get("cover") or item.get("bookCover")
                })
            return normalized
        except Exception as e:
            logger.error(f"DramaBox Discovery Error ({category}): {e}")
            return []

# Register the provider
ProviderFactory.register("dramabox", DramaBoxProvider)

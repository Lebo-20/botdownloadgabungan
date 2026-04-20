from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class FlickReelsProvider(BaseProvider):
    """
    FlickReels Provider (DramaBos API Version)
    Subtitles and decryption handled via HLSProxy if needed.
    """
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://flickreels.dramabos.my.id"
        self.token = settings.token_dramabos
        self.lang = "6" # Indonesian as per sample

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "lang": self.lang,
            "code": self.token
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            if not isinstance(data, dict): return []
            
            results = data.get("data")
            if not isinstance(results, (list, dict)):
                results = []
            
            if isinstance(results, dict):
                results = results.get("records") or results.get("list") or [results]

            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                drama_id = item.get("id") or item.get("bookId") or item.get("playlet_id")
                normalized.append({
                    "id": str(drama_id) if drama_id else None,
                    "title": item.get("title") or item.get("bookName") or item.get("playlet_title") or "No Title",
                    "platform": "flickreels",
                    "poster": item.get("poster") or item.get("bookCover") or item.get("cover")
                })
            return normalized
        except Exception:
            logger.exception("FlickReels Search Error")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        if not drama_id or drama_id == "None": return {}
        
        url = f"{self.base_url}/batchload/{drama_id}"
        params = {
            "lang": self.lang,
            "code": self.token
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            if not isinstance(data, dict): return {}
            
            detail = data.get("data")
            if not isinstance(detail, dict):
                detail = {}
            
            # The list of episodes is in 'list' for FlickReels
            raw_eps = detail.get("list") or detail.get("episodes") or detail.get("chapter_list") or []
            
            return {
                "id": drama_id,
                "title": detail.get("title") or detail.get("bookName") or "Unknown",
                "description": detail.get("introduction") or "No description.",
                "poster": detail.get("cover") or detail.get("bookCover") or detail.get("poster"),
                "total_episodes": detail.get("totalEpisode") or detail.get("total_chapters") or len(raw_eps),
                "video_key": detail.get("videoKey"),
                "episodes_raw": raw_eps
            }
        except Exception:
            logger.exception("FlickReels Detail Error")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        details = await self.get_drama_details(drama_id)
        raw_episodes = details.get("episodes_raw")
        if not isinstance(raw_episodes, list): raw_episodes = []
        video_key = details.get("video_key")
        
        normalized = []
        for i, ep in enumerate(raw_episodes, 1):
            if not isinstance(ep, dict): continue
            ep_no = ep.get("number") or ep.get("index") or i
            normalized.append({
                "id": str(ep.get("id") or ep.get("chapterId") or i),
                "number": ep_no,
                "title": ep.get("title") or f"Episode {ep_no}",
                "stream_url": ep.get("play_url") or ep.get("m3u8") or ep.get("url"),
                "video_key": video_key
            })
        return normalized

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        endpoints = {
            "home": "api/home",
            "trending": "trending",
            "popular": "trending"
        }
        target = endpoints.get(category, "api/home")
        url = f"{self.base_url}/{target}"
        params = {"lang": self.lang, "page": 1, "code": self.token}
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            if not isinstance(data, dict): return []
            
            results = data.get("data")
            if not isinstance(results, (list, dict)):
                results = []
                
            if isinstance(results, dict):
                results = results.get("records") or results.get("list") or []

            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                drama_id = item.get("id") or item.get("bookId")
                normalized.append({
                    "id": str(drama_id) if drama_id else None,
                    "title": item.get("title") or item.get("bookName") or "No Title",
                    "platform": "flickreels",
                    "poster": item.get("poster") or item.get("bookCover")
                })
            return normalized
        except Exception:
            logger.exception(f"FlickReels Discovery Error ({category})")
            return []

def get_supported_categories(self) -> List[Dict[str, str]]:
        return [{"id": "trending", "label": "📈 Trending"}]

# Register
ProviderFactory.register("flickreels", FlickReelsProvider)

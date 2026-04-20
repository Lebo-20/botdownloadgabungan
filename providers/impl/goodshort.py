from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class GoodShortProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://goodshort.dramabos.my.id"
        self.global_code = settings.token_dramabos
        self.lang = "in"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # Using search endpoint
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "lang": self.lang,
            "code": self.global_code
        }
        
        try:
            response = await self.client.get(url, params=params)
            data = response.json()
            if not isinstance(data, dict): return []
            
            # Extract results
            results = data.get("data")
            if not isinstance(results, (list, dict)):
                results = []

            if isinstance(results, dict):
                results = results.get("records") or results.get("list") or [results]
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id") or item.get("bookId")),
                    "title": item.get("title") or item.get("bookName") or "No Title",
                    "platform": "goodshort",
                    "poster": item.get("poster") or item.get("cover") or item.get("bookCover")
                })
            return normalized
        except Exception as e:
            logger.error(f"GoodShort Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        # Using book endpoint for metadata
        url = f"{self.base_url}/book/{drama_id}"
        params = {"lang": self.lang}
        
        # We still need rawurl for the video key
        raw_url = f"{self.base_url}/rawurl/{drama_id}"
        raw_params = {
            "lang": self.lang,
            "q": "720p",
            "code": self.global_code
        }
        
        try:
            # Metadata
            resp_book = await self.client.get(url, params=params)
            data_book = resp_book.json()
            if not isinstance(data_book, dict): data_book = {}
            detail = data_book.get("data") if isinstance(data_book.get("data"), dict) else {}
            
            # Key and Episodes
            resp_raw = await self.client.get(raw_url, params=raw_params)
            data_raw = resp_raw.json()
            if not isinstance(data_raw, dict): data_raw = {}
            raw_data = data_raw.get("data") if isinstance(data_raw.get("data"), dict) else {}
            
            return {
                "id": drama_id,
                "title": detail.get("title") or raw_data.get("bookName") or "Unknown",
                "description": detail.get("introduction") or raw_data.get("introduction"),
                "poster": detail.get("poster") or raw_data.get("bookCover"),
                "total_episodes": detail.get("total_chapters") or raw_data.get("totalEpisode") or len(raw_data.get("episodes") or raw_data.get("list") or []),
                "video_key": raw_data.get("videoKey"),
                "episodes_raw": raw_data.get("episodes") or raw_data.get("list") or []
            }
        except Exception:
            logger.exception("GoodShort Detail Error")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        details = await self.get_drama_details(drama_id)
        ep_list = details.get("episodes_raw")
        if not isinstance(ep_list, list): ep_list = []
        video_key = details.get("video_key")
        
        normalized = []
        for ep in ep_list:
            if not isinstance(ep, dict): continue
            ep_no = ep.get("number") or ep.get("index")
            normalized.append({
                "id": str(ep.get("id")),
                "number": ep_no,
                "title": f"Episode {ep_no}",
                "stream_url": ep.get("m3u8"),
                "video_key": video_key
            })
        return normalized

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        endpoints = {
            "home": "home",
            "trending": "hot",
            "popular": "hot"
        }
        target = endpoints.get(category, "home")
        url = f"{self.base_url}/{target}"
        params = {"lang": self.lang, "page": 1, "size": 20}
        if target == "home": params["channel"] = -1
        
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
                normalized.append({
                    "id": str(item.get("id") or item.get("bookId")),
                    "title": item.get("title") or item.get("bookName") or "No Title",
                    "platform": "goodshort",
                    "poster": item.get("poster") or item.get("cover") or item.get("bookCover")
                })
            return normalized
        except Exception as e:
            logger.error(f"GoodShort Discovery Error ({category}): {e}")
            return []

def get_supported_categories(self) -> List[Dict[str, str]]:
        return [{"id": "home", "label": "🏠 Home"}, {"id": "trending", "label": "📈 Hot"}]

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        return None 

# Register
ProviderFactory.register("goodshort", GoodShortProvider)

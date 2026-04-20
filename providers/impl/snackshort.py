from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class SnackShortProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/snackshort/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.token_sapimu}"
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # Search endpoint: /api/v1/search?q=...&lang=Indonesian
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "lang": "Indonesian",
            "page": 1,
            "limit": 20
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # SnackShort search returns { data: { data: [ {book_id...} ] } }
            search_content = data.get("data", {})
            if isinstance(search_content, dict) and "data" in search_content:
                search_content = search_content["data"]
            
            results = []
            if isinstance(search_content, dict):
                results = search_content.get("data") or []
            elif isinstance(search_content, list):
                results = search_content
                
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                # Search items have 'book_id' or 'book' dict
                book_id = item.get("book_id")
                if "book" in item and isinstance(item["book"], dict):
                    book_id = item["book"].get("book_id")
                
                normalized.append({
                    "id": str(book_id or item.get("id")),
                    "title": item.get("title") or item.get("book_name") or "No Title",
                    "platform": "snackshort",
                    "poster": item.get("cover_key") or item.get("image")
                })
            return normalized
        except Exception as e:
            logger.error(f"SnackShort Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        # Detail endpoint: /api/v1/book/:bookId?lang=Indonesian
        url = f"{self.base_url}/book/{drama_id}"
        params = {"lang": "Indonesian"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # Returns { data: { data: { book: {...}, chapter: {...} } } }
            detail_content = data.get("data", {})
            if isinstance(detail_content, dict) and "data" in detail_content:
                detail_content = detail_content["data"]
            
            if isinstance(detail_content, dict) and "book" in detail_content:
                book = detail_content["book"]
                return {
                    "id": str(book.get("book_id")),
                    "title": book.get("book_name"),
                    "description": book.get("introduce"),
                    "poster": book.get("cover_key") or book.get("image"),
                    "total_episodes": book.get("chapters") or book.get("onlineChapter"),
                    # Store current chapter as a starting point
                    "first_chapter": detail_content.get("chapter")
                }
            return {}
        except Exception as e:
            logger.error(f"SnackShort Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        details = await self.get_drama_details(drama_id)
        if not details:
            return []
            
        total = details.get("total_episodes") or 1
        first_chap = details.get("first_chapter", {})
        
        normalized = []
        # Since we don't have a reliable episode list endpoint yet,
        # we'll provide the first episode if we have it.
        # Note: chapter_id is needed for stream URL
        if first_chap:
            normalized.append({
                "id": str(first_chap.get("chapter_id")),
                "number": 1,
                "title": first_chap.get("chapter_name") or "Episode 1",
                "chapter_id": first_chap.get("chapter_id")
            })
            
        # If total > 1, we could potentially fetch more if we knew how.
        # For now, we only show the first one or a placeholder to indicate more exist.
        for i in range(2, total + 1):
             normalized.append({
                "id": f"dummy_{i}",
                "number": i,
                "title": f"Episode {i} (Check App)"
            })
            
        return normalized

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        drama_id = video_id
        
        # In SnackShort, the book detail endpoint often ALREADY contains the play_url 
        # for the first/current chapter. Let's try that first for Ep 1.
        if episode_no == 1:
            url = f"{self.base_url}/book/{drama_id}"
            params = {"lang": "Indonesian"}
            try:
                response = await self.client.get(url, params=params, headers=self.headers)
                data = response.json()
                detail_wrap = data.get("data", {}).get("data", {})
                if isinstance(detail_wrap, dict):
                    play_url = detail_wrap.get("play_url") or detail_wrap.get("sd_264_url")
                    if play_url:
                        return play_url
            except:
                pass

        # Fallback to episode endpoint if needed or for other episodes
        details = await self.get_drama_details(drama_id)
        if not details:
            return None
            
        first_chap = details.get("first_chapter")
        chapter_id = first_chap.get("chapter_id") if first_chap and episode_no == 1 else None
        
        if not chapter_id:
            return None
            
        url = f"{self.base_url}/book/{drama_id}/episode/{chapter_id}"
        params = {"lang": "Indonesian"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # Nested: { data: { data: { play_url: ... } } }
            s_content = data.get("data", {})
            if isinstance(s_content, dict) and "data" in s_content:
                s_content = s_content["data"]
            
            if isinstance(s_content, dict):
                return s_content.get("play_url") or s_content.get("url") or s_content.get("sd_264_url")
            return None
        except Exception as e:
            logger.error(f"SnackShort Stream URL Error: {e}")
            return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        # categories: /home, /browsing, /tabs
        url = f"{self.base_url}/browsing"
        params = {"page": 1, "pageSize": 20, "lang": "Indonesian"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            data_content = data.get("data", {})
            if isinstance(data_content, dict) and "data" in data_content:
                data_content = data_content["data"]
                
            results = data_content if isinstance(data_content, list) else []
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                book = item.get("book", {})
                normalized.append({
                    "id": str(book.get("book_id") or item.get("bookId")),
                    "title": book.get("book_name") or item.get("title") or "No Title",
                    "platform": "snackshort",
                    "poster": book.get("cover_key") or book.get("image")
                })
            return normalized
        except Exception as e:
            logger.error(f"SnackShort Discovery Error: {e}")
            return []

# Register the provider
ProviderFactory.register("snackshort", SnackShortProvider)

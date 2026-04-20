from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class FreeReelsProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/freereels/api/v1"
        self.token = settings.token_sapimu
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.lang = "id-ID"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "page": 0,
            "lang": self.lang
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # FreeReels results
            results = data.get("data", [])
            if isinstance(results, dict):
                results = results.get("rows") or results.get("list") or [results]
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "freereels",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"FreeReels Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/dramas/{drama_id}"
        params = {"lang": self.lang}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            # Returns data directly or in 'data' key
            detail = data.get("data", {}) if isinstance(data, dict) else {}
            
            return {
                "id": drama_id,
                "title": detail.get("title"),
                "description": detail.get("description") or detail.get("intro"),
                "poster": detail.get("poster") or detail.get("cover"),
                "total_episodes": detail.get("episodeCount") or detail.get("total_episodes")
            }
        except Exception as e:
            logger.error(f"FreeReels Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dramas/{drama_id}/episodes"
        params = {"lang": self.lang}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            episodes_raw = data.get("data", [])
            if isinstance(episodes_raw, dict):
                episodes_raw = episodes_raw.get("rows") or episodes_raw.get("list") or []

            normalized = []
            for i, ep in enumerate(episodes_raw, 1):
                if not isinstance(ep, dict): continue
                ep_no = ep.get("episode_no") or ep.get("index") or ep.get("number") or i
                normalized.append({
                    "id": f"{drama_id}|{ep_no}", # Keep context for play endpoint
                    "number": ep_no,
                    "title": f"Episode {ep_no}"
                })
            return normalized
        except Exception as e:
            logger.error(f"FreeReels Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # video_id can be drama_id or drama_id|ep_no
        drama_id = video_id.split("|")[0] if "|" in video_id else video_id
        
        url = f"{self.base_url}/dramas/{drama_id}/play/{episode_no}"
        params = {"lang": self.lang}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            # Response structure: data -> url
            play_data = data.get("data", {})
            return play_data.get("url") or play_data.get("video_url") or play_data.get("hls")
        except Exception as e:
            logger.error(f"FreeReels Stream Error: {e}")
            return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        # Map categories to endpoints
        endpoints = {
            "home": "foryou",
            "foryou": "foryou",
            "popular": "popular",
            "latest": "new",
            "female": "female",
            "male": "male",
            "anime": "anime",
            "dubbed": "dubbing",
            "coming-soon": "coming-soon"
        }
        
        target = endpoints.get(category, "foryou")
        url = f"{self.base_url}/{target}"
        params = {"lang": self.lang, "page": 0}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            results = data.get("data", [])
            if isinstance(results, dict):
                results = results.get("rows") or results.get("list") or []

            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "freereels",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"FreeReels Discovery Error ({category}): {e}")
            return []

# Register the provider
ProviderFactory.register("freereels", FreeReelsProvider)

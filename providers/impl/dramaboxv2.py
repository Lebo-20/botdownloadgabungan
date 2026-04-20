from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class DramaBoxV2Provider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/dramaboxv2/api"
        self.token = settings.token_sapimu
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.lang = "in"

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "keyword": query,
            "page": 1,
            "lang": self.lang
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # DramaBoxV2 structure: data -> records/list/rows
            results = data.get("data", [])
            if isinstance(results, dict):
                results = results.get("records") or results.get("list") or results.get("rows") or [results]

            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id") or item.get("playletId")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "dramaboxv2",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"DramaBoxV2 Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/drama/{drama_id}"
        params = {"lang": self.lang}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            detail = data.get("data", {})
            
            return {
                "id": drama_id,
                "title": detail.get("title"),
                "description": detail.get("introduction") or detail.get("desc"),
                "poster": detail.get("poster") or detail.get("cover"),
                "total_episodes": detail.get("count") or detail.get("episodeCount")
            }
        except Exception as e:
            logger.error(f"DramaBoxV2 Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        # Check chapters endpoint
        url = f"{self.base_url}/drama/{drama_id}/chapters"
        params = {"lang": self.lang}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            chapters = data.get("data", [])
            if isinstance(chapters, dict):
                chapters = chapters.get("records") or chapters.get("list") or []

            # We also need stream URLs. endpoint /video-urls/:id might have them all.
            # We'll fetch stream URLs in get_stream_url or here.
            # Strategy: Store chapter IDs for mapped stream lookup.
            
            normalized = []
            for i, ch in enumerate(chapters, 1):
                if not isinstance(ch, dict): continue
                ep_no = ch.get("orderNumber") or ch.get("index") or i
                normalized.append({
                    "id": str(ch.get("id")),
                    "number": ep_no,
                    "title": f"Episode {ep_no}"
                })
            return normalized
        except Exception as e:
            logger.error(f"DramaBoxV2 Chapters Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # video_id can be the drama_id. 
        # The /video-urls/:id endpoint seems to return all URLs for the drama.
        drama_id = video_id
        url = f"{self.base_url}/video-urls/{drama_id}"
        params = {"lang": self.lang}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # data content is likely a list of play URLs mapping to chapter IDs
            video_data = data.get("data", [])
            
            # Strategy: find entry matching episode_no or chapter_id
            # Usually it's a list where index corresponds to episode_no (1-indexed)
            if isinstance(video_data, list):
                # Check if it's a direct list of URLs
                if len(video_data) >= episode_no:
                    target = video_data[episode_no - 1]
                    if isinstance(target, str): return target
                    if isinstance(target, dict): return target.get("url") or target.get("hls")
            
            return None
        except Exception as e:
            logger.error(f"DramaBoxV2 Stream Error: {e}")
            return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        endpoints = {
            "home": "home",
            "trending": "rank",
            "popular": "rank",
            "recommend": "recommend"
        }
        target = endpoints.get(category, "home")
        url = f"{self.base_url}/{target}"
        params = {"lang": self.lang, "page": 1, "size": 20}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            results = data.get("data", [])
            if isinstance(results, dict):
                results = results.get("records") or results.get("list") or []

            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id") or item.get("playletId")),
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "dramaboxv2",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"DramaBoxV2 Discovery Error ({category}): {e}")
            return []

# Register
ProviderFactory.register("dramaboxv2", DramaBoxV2Provider)

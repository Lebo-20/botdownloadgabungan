from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class MeloShortProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/meloshort/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.token_sapimu}"
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dramas/search"
        params = {
            "q": query,
            "lang": "id"
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # MeloShort search usually returns a list in 'data'
            data_content = data.get("data", [])
            results = []
            if isinstance(data_content, list):
                results = data_content
            elif isinstance(data_content, dict):
                results = data_content.get("rows") or data_content.get("list") or [data_content]
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("drama_id")),
                    "title": item.get("drama_title") or "No Title",
                    "platform": "meloshort",
                    "poster": item.get("drama_cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"MeloShort Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        # Fetching episodes is the main way to get details if needed
        return {"id": drama_id}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dramas/{drama_id}/episodes"
        params = {
            "page": 1,
            "limit": 100,
            "lang": "id"
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            episodes_raw = data.get("data", [])
            if isinstance(episodes_raw, dict):
                episodes_raw = episodes_raw.get("rows") or episodes_raw.get("list") or []
                
            normalized = []
            for i, ep in enumerate(episodes_raw, 1):
                if not isinstance(ep, dict): continue
                
                ep_id = ep.get("chapter_id")
                raw_idx = ep.get("chapter_index")
                episode_num = int(raw_idx) if raw_idx is not None else i
                
                normalized.append({
                    "id": ep_id,
                    "number": episode_num,
                    "title": ep.get("chapter_name") or f"Episode {episode_num}",
                    "chapter_id": ep_id
                })
            return normalized
        except Exception as e:
            logger.error(f"MeloShort Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        drama_id = video_id
        episodes = await self.get_episodes(drama_id)
        
        chapter_id = None
        for ep in episodes:
            if str(ep.get("number")) == str(episode_no):
                chapter_id = ep.get("id")
                break
        
        if not chapter_id:
            return None
            
        url = f"{self.base_url}/dramas/{drama_id}/episodes/{chapter_id}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            stream_info = data.get("data", {})
            if isinstance(stream_info, dict):
                return stream_info.get("play_url") or stream_info.get("play_url_720p") or stream_info.get("url")
            return None
        except Exception as e:
            logger.error(f"MeloShort Stream URL Error: {e}")
            return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        category_map = {
            "home": "discover",
            "trending": "top",
            "latest": "dramas",
            "discover": "discover",
            "top": "top"
        }
        endpoint = category_map.get(category, "discover")
        url = f"{self.base_url}/dramas/{endpoint}" if endpoint in ["discover", "top"] else f"{self.base_url}/{endpoint}"
        params = {"page": 1, "limit": 20, "lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            data_content = data.get("data", [])
            results = []
            if isinstance(data_content, list):
                results = data_content
            elif isinstance(data_content, dict):
                # Handle discover which has place_list
                if "place_list" in data_content:
                    plist = data_content["place_list"]
                    for p in plist:
                        results.extend(p.get("list", []) or p.get("drama_list", []))
                else:
                    results = data_content.get("rows") or data_content.get("list") or [data_content]
                
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("drama_id")),
                    "title": item.get("drama_title") or "No Title",
                    "platform": "meloshort",
                    "poster": item.get("drama_cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"MeloShort Discovery Error ({category}): {e}")
            return []

# Register the provider
ProviderFactory.register("meloshort", MeloShortProvider)

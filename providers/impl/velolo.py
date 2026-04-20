from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class VeloloProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/velolo"
        self.headers = {
            "Authorization": f"Bearer {settings.token_sapimu}"
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/dramas"
        params = {
            "q": query,
            "page": 1,
            "limit": 15,
            "lang": "id"
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # Velolo uses 'rows' for the result list
            results = data.get("rows", []) if isinstance(data, dict) else data
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("name") or item.get("title") or "No Title",
                    "platform": "velolo",
                    "poster": item.get("cover") or item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"Velolo Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/detail/{drama_id}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            # Returns a dict with videoInfo, episodesInfo, etc.
            if isinstance(data, dict) and "videoInfo" in data:
                info = data["videoInfo"]
                return {
                    "id": info.get("id"),
                    "title": info.get("name"),
                    "description": info.get("introduction"),
                    "poster": info.get("cover"),
                    "raw_data": data # Keep full data for episode extraction
                }
            return data
        except Exception as e:
            logger.error(f"Velolo Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        details = await self.get_drama_details(drama_id)
        raw_data = details.get("raw_data", {})
        
        # episodesInfo -> rows
        episodes_raw = []
        if isinstance(raw_data, dict):
            ep_info = raw_data.get("episodesInfo", {})
            if isinstance(ep_info, dict):
                episodes_raw = ep_info.get("rows", [])
        
        normalized = []
        for i, ep in enumerate(episodes_raw, 1):
            if not isinstance(ep, dict): continue
            
            # videoAddress is the stream URL
            stream_url = ep.get("videoAddress")
            # orderNumber is the episode number (often 0-indexed or 1-indexed)
            raw_num = ep.get("orderNumber")
            episode_num = int(raw_num) + 1 if raw_num is not None else i
            
            normalized.append({
                "id": str(ep.get("id") or i),
                "number": episode_num,
                "title": f"Episode {episode_num}",
                "stream_url": stream_url
            })
        
        return normalized

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        episodes = await self.get_episodes(video_id)
        for ep in episodes:
            if str(ep.get("number")) == str(episode_no):
                return ep.get("stream_url")
        return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        category_map = {
            "home": "hot",
            "latest": "new",
            "trending": "hot",
            "new": "new"
        }
        endpoint = category_map.get(category, "hot")
        url = f"{self.base_url}/{endpoint}"
        params = {"page": 1, "limit": 15, "lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            # Velolo uses 'rows' for hot/new lists
            results = data.get("rows", []) if isinstance(data, dict) else data
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("id")),
                    "title": item.get("name") or item.get("title") or "No Title",
                    "platform": "velolo",
                    "poster": item.get("cover") or item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"Velolo Discovery Error ({category}): {e}")
            return []

    def get_supported_categories(self) -> List[Dict[str, str]]:
        return [{"id": "home", "label": "🏠 Home"}]

# Register the provider
ProviderFactory.register("velolo", VeloloProvider)

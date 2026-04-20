from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class HiShortProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/hishort/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.token_sapimu}"
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # Search endpoint: /api/v1/search/:q
        url = f"{self.base_url}/search/{query}"
        
        try:
            response = await self.client.get(url, headers=self.headers)
            data = response.json()
            
            results = data.get("data", [])
            if isinstance(results, dict):
                results = results.get("rows") or results.get("list") or [results]
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                # Slug seems to be the reliable ID
                internal_id = item.get("slug") or str(item.get("id"))
                normalized.append({
                    "id": internal_id,
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "hishort",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"HiShort Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        # Detail endpoint: /api/v1/drama/:id
        url = f"{self.base_url}/drama/{drama_id}"
        
        try:
            response = await self.client.get(url, headers=self.headers)
            data = response.json()
            # Status check for API consistency
            if data.get("status") == 200 and "data" in data:
                detail = data["data"]
                return {
                    "id": drama_id,
                    "title": detail.get("title"),
                    "description": detail.get("synopsis"),
                    "poster": detail.get("poster"),
                    "episodes_raw": detail.get("episodes", [])
                }
            return data.get("data", {}) if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"HiShort Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        details = await self.get_drama_details(drama_id)
        episodes_raw = details.get("episodes_raw", [])
        
        normalized = []
        for i, ep in enumerate(episodes_raw, 1):
            if not isinstance(ep, dict): continue
            
            # The 'slug' is used for fetching the stream URL
            episode_slug = ep.get("slug")
            # Construct episode number from index if not explicitly provided
            # Some APIs provide 'episode_no' or 'order'
            episode_num = ep.get("number") or ep.get("index") or i
            
            normalized.append({
                "id": episode_slug or f"{drama_id}_{i}",
                "number": episode_num,
                "title": ep.get("title") or f"Episode {episode_num}",
                "slug": episode_slug
            })
        
        return normalized

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # HiShort is unique: we usually have the slug directly if video_id is passed as episode slug
        # However, following the BaseProvider pattern, video_id is often the drama_id
        
        target_slug = None
        if "_" in video_id:
            # Likely already a slug like '5034_1'
            target_slug = video_id
        else:
            # Need to find slug from episode list
            episodes = await self.get_episodes(video_id)
            for ep in episodes:
                if str(ep.get("number")) == str(episode_no):
                    target_slug = ep.get("slug")
                    break
        
        if not target_slug:
            return None
            
        url = f"{self.base_url}/episode/{target_slug}"
        try:
            response = await self.client.get(url, headers=self.headers)
            data = response.json()
            if data.get("status") == 200 and "data" in data:
                ep_data = data["data"]
                servers = ep_data.get("servers", [])
                if servers:
                    return servers[0].get("url")
            return None
        except Exception as e:
            logger.error(f"HiShort Stream URL Error: {e}")
            return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        # HiShort currently only has /home
        url = f"{self.base_url}/home"
        
        try:
            response = await self.client.get(url, headers=self.headers)
            data = response.json()
            
            # Structure: data -> popular
            data_obj = data.get("data", {})
            results = data_obj.get("popular", []) if isinstance(data_obj, dict) else []
            
            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                internal_id = item.get("slug") or str(item.get("id"))
                normalized.append({
                    "id": internal_id,
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "hishort",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"HiShort Discovery Error: {e}")
            return []

# Register the provider
ProviderFactory.register("hishort", HiShortProvider)

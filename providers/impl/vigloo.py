from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class ViglooProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/vigloo/api/v1"
        self.headers = {
            "Authorization": f"Bearer {settings.token_sapimu}"
        }

    async def search(self, query: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "limit": 20,
            "lang": "id"
        }
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            items = data.get("data", [])
            normalized = []
            for item in items:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("programId") or item.get("id")),
                    "title": item.get("title") or "No Title",
                    "platform": "vigloo",
                    "poster": item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"Vigloo Search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/drama/{drama_id}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            return data.get("data", {}) if isinstance(data, dict) else {}
        except Exception as e:
            logger.error(f"Vigloo Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        # Need season_id from drama details
        details = await self.get_drama_details(drama_id)
        
        season_id = None
        # Seasons might be a list or a single ID
        seasons = details.get("seasons", [])
        if seasons and isinstance(seasons, list):
            season_id = seasons[0].get("id")
        else:
            season_id = details.get("seasonId")
            
        if not season_id:
            logger.warning(f"No seasonId found for Vigloo drama {drama_id}")
            return []
            
        url = f"{self.base_url}/drama/{drama_id}/season/{season_id}/episodes"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            episodes_raw = data.get("data", [])
            normalized = []
            for ep in episodes_raw:
                if not isinstance(ep, dict): continue
                
                ep_no = ep.get("ep") or ep.get("episode")
                normalized.append({
                    "id": f"{season_id}|{ep_no}", # Combined ID for stream retrieval
                    "number": ep_no,
                    "title": ep.get("title") or f"Episode {ep_no}",
                    "season_id": season_id,
                    "ep_no": ep_no
                })
            return normalized
        except Exception as e:
            logger.error(f"Vigloo Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # video_id here is usually programId from search/details
        # But our get_episodes returns "season_id|ep_no" in 'id' field if accessed via episode item.
        # However, the bot often calls get_stream_url(drama_id, episode_no).
        
        drama_id = video_id
        
        # We need seasonId. 
        # If we didn't store it in a way that correlates programId/episode_no to seasonId,
        # we have to fetch details again.
        
        details = await self.get_drama_details(drama_id)
        season_id = None
        seasons = details.get("seasons", [])
        if seasons and isinstance(seasons, list):
            season_id = seasons[0].get("id")
        else:
            season_id = details.get("seasonId")
            
        if not season_id:
            return None
            
        # Use stream endpoint as per doc
        url = f"{self.base_url}/stream"
        params = {
            "seasonId": season_id,
            "ep": episode_no
        }
        
        try:
            # Note: stream response might be the URL directly or a JSON with 'url'
            response = await self.client.get(url, params=params, headers=self.headers)
            
            # Use raw text if it looks like a URL, or JSON if it is
            content = response.text.strip()
            if content.startswith("http"):
                return content
                
            data = response.json()
            return data.get("data", {}).get("url") or data.get("url")
        except Exception as e:
            logger.error(f"Vigloo Stream Error: {e}")
            return None

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        # Categories: home (tabs), trending (rank), latest (browse)
        if category == "trending":
            url = f"{self.base_url}/rank"
            params = {"lang": "id"}
        elif category == "latest":
            url = f"{self.base_url}/browse"
            params = {"sort": "NEW", "limit": 20, "lang": "id"}
        else:
            # Default home browsing
            url = f"{self.base_url}/browse"
            params = {"sort": "POPULAR", "limit": 20, "lang": "id"}
            
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            items = data.get("data", [])
            normalized = []
            for item in items:
                if not isinstance(item, dict): continue
                normalized.append({
                    "id": str(item.get("programId") or item.get("id")),
                    "title": item.get("title") or "No Title",
                    "platform": "vigloo",
                    "poster": item.get("poster")
                })
            return normalized
        except Exception as e:
            logger.error(f"Vigloo Discovery Error ({category}): {e}")
            return []

# Register the provider
ProviderFactory.register("vigloo", ViglooProvider)

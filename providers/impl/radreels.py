from typing import List, Dict, Any, Optional
from providers.base import BaseProvider
from providers.factory import ProviderFactory
from utils.http_client import AsyncHTTPClient
from loguru import logger

from config import settings

class RadReelsProvider(BaseProvider):
    def __init__(self):
        self.client = AsyncHTTPClient()
        self.base_url = "https://captain.sapimu.au/radreels/api/v1"
        self.token = settings.token_sapimu # Use Sapimu token
        self.headers = {"Authorization": f"Bearer {self.token}"}

    async def search(self, query: str) -> List[Dict[str, Any]]:
        # GET /api/v1/search/:query
        url = f"{self.base_url}/search/{query}"
        params = {"page": "1", "lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            
            results = data if isinstance(data, list) else data.get("data", [])
            # If data is a dict with list under something else
            if isinstance(data, dict) and "list" in data:
                results = data["list"]

            normalized = []
            for item in results:
                if not isinstance(item, dict): continue
                # We need keyword and fakeId. 
                keyword = item.get("keyword")
                fake_id = item.get("fakeId")
                combined_id = f"{keyword}|{fake_id}"
                
                normalized.append({
                    "id": combined_id,
                    "title": item.get("title") or item.get("name") or "No Title",
                    "platform": "radreels",
                    "poster": item.get("poster") or item.get("cover")
                })
            return normalized
        except Exception as e:
            logger.error(f"RadReels search Error: {e}")
            return []

    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        # drama_id format: keyword|fakeId
        try:
            keyword, fake_id = drama_id.split("|")
        except ValueError:
            return {}

        url = f"{self.base_url}/drama/{keyword}"
        params = {"page": "1", "lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            return data if isinstance(data, dict) else data.get("data", {})
        except Exception as e:
            logger.error(f"RadReels Detail Error: {e}")
            return {}

    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        try:
            keyword, fake_id = drama_id.split("|")
        except ValueError:
            return []

        url = f"{self.base_url}/episodes/{fake_id}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            episodes = data if isinstance(data, list) else data.get("data", [])
            if isinstance(data, dict) and "episodes" in data:
                episodes = data["episodes"]

            normalized = []
            for ep in episodes:
                # video_id in stream URL requires videoFakeId and episodicDramaId
                v_fake_id = ep.get("videoFakeId")
                drama_id_internal = ep.get("episodicDramaId")
                combined_v_id = f"{v_fake_id}|{drama_id_internal}"

                normalized.append({
                    "id": combined_v_id,
                    "number": ep.get("episode_no") or ep.get("number") or ep.get("index"),
                    "title": f"Episode {ep.get('episode_no') or ep.get('number')}"
                })
            return normalized
        except Exception as e:
            logger.error(f"RadReels Episodes Error: {e}")
            return []

    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        # video_id format: videoFakeId|episodicDramaId
        try:
            v_fake_id, drama_id_internal = video_id.split("|")
        except ValueError:
            # If not in combined format, we might have to search in episode list
            return None

        url = f"{self.base_url}/video/{v_fake_id}/{drama_id_internal}"
        params = {"lang": "id"}
        
        try:
            response = await self.client.get(url, params=params, headers=self.headers)
            data = response.json()
            return data.get("url") or data.get("data", {}).get("url") or data.get("play_url") or data.get("video_url")
        except Exception as e:
            logger.error(f"RadReels Video URL Error: {e}")
            return None

    def get_supported_categories(self) -> List[Dict[str, str]]:
        return []

# Register the provider
ProviderFactory.register("radreels", RadReelsProvider)

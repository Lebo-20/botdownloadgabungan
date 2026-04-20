from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for dramas on the platform."""
        pass

    @abstractmethod
    async def get_drama_details(self, drama_id: str) -> Dict[str, Any]:
        """Get detailed information about a drama."""
        pass

    @abstractmethod
    async def get_episodes(self, drama_id: str) -> List[Dict[str, Any]]:
        """Get list of episodes for a drama."""
        pass

    @abstractmethod
    async def get_stream_url(self, video_id: str, episode_no: int = 1) -> Optional[str]:
        """Get the direct stream URL for a specific episode/video."""
        pass

    async def discover(self, category: str = "home") -> List[Dict[str, Any]]:
        """Optional method for discovering content (Home, Latest, etc)."""
        return []

    def get_supported_categories(self) -> List[Dict[str, str]]:
        """
        Return a list of supported discovery categories with labels.
        Example: [{"id": "home", "label": "🏠 Home"}]
        """
        return []

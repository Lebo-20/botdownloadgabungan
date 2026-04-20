from typing import Dict, Type, List
from providers.base import BaseProvider
from loguru import logger

class ProviderFactory:
    _providers: Dict[str, Type[BaseProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseProvider]):
        cls._providers[name.lower()] = provider_cls
        logger.info(f"Registered provider: {name}")

    @classmethod
    def get_provider(cls, name: str) -> BaseProvider:
        provider_cls = cls._providers.get(name.lower())
        if not provider_cls:
            raise ValueError(f"Provider '{name}' not found.")
        return provider_cls()

    @classmethod
    def get_provider_names(cls) -> List[str]:
        return list(cls._providers.keys())

def get_provider(name: str) -> BaseProvider:
    return ProviderFactory.get_provider(name)

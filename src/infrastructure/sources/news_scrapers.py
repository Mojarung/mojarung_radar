from abc import ABC, abstractmethod
from typing import Any

from src.core.logging import get_logger

logger = get_logger(__name__)


class NewsSource(ABC):
    @abstractmethod
    async def fetch_news(self, limit: int = 100) -> list[dict[str, Any]]:
        pass


class BloombergScraper(NewsSource):
    async def fetch_news(self, limit: int = 100) -> list[dict[str, Any]]:
        logger.info("bloomberg_scraper_placeholder")
        return []


class ReutersScraper(NewsSource):
    async def fetch_news(self, limit: int = 100) -> list[dict[str, Any]]:
        logger.info("reuters_scraper_placeholder")
        return []


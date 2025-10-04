"""Base parser class for all news sources"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.core.logging_config import log


class BaseParser(ABC):
    """Abstract base class for news parsers"""
    
    def __init__(self, source_name: str, source_url: str):
        self.source_name = source_name
        self.source_url = source_url
        self._last_fetch_time: Optional[datetime] = None
    
    @abstractmethod
    async def fetch_news(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetch news articles from the source.
        
        Returns:
            List of dictionaries with keys:
                - url: str
                - title: str
                - content: str
                - published_at: str (ISO format)
        """
        pass
    
    def format_article(
        self,
        url: str,
        title: str,
        content: str,
        published_at: datetime
    ) -> Dict[str, Any]:
        """Format article for RabbitMQ message"""
        return {
            "source_name": self.source_name,
            "url": url,
            "title": title,
            "content": content,
            "published_at": published_at.isoformat() if isinstance(published_at, datetime) else published_at,
        }
    
    def get_parser_info(self) -> Dict[str, str]:
        """Get parser metadata"""
        return {
            "name": self.source_name,
            "url": self.source_url,
            "last_fetch": self._last_fetch_time.isoformat() if self._last_fetch_time else None,
        }
    
    def update_last_fetch_time(self):
        """Update the last fetch timestamp"""
        self._last_fetch_time = datetime.utcnow()
        log.debug(f"Updated last fetch time for {self.source_name}: {self._last_fetch_time}")


from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from app.models import News, Story, Source
from app.schemas.response import HotStoryResponse
from app.graph import create_radar_graph
from app.graph.state import RadarState
from app.core.logging import get_logger

logger = get_logger(__name__)


class NewsService:
    """Сервис для работы с новостями."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph = create_radar_graph()
    
    async def process_news(self, news_id: UUID) -> Story:
        """Обработка новости через граф агента."""
        result = await self.db.execute(
            select(News).where(News.id == news_id)
        )
        news = result.scalar_one_or_none()
        
        if not news:
            raise ValueError(f"News {news_id} not found")
        
        initial_state: RadarState = {
            "news_id": news.id,
            "news_title": news.title,
            "news_content": news.content,
            "news_url": news.url,
            "published_at": news.published_at,
            "cluster_id": None,
            "related_articles": [],
            "entities": [],
            "timeline": [],
            "source_reputation": 0.7,
            "hotness_score": 0.0,
            "context": None,
            "why_now": None,
            "draft": None,
            "is_duplicate": False,
            "should_generate_draft": False,
        }
        
        logger.info(f"Processing news {news_id} through graph")
        
        final_state = await self.graph.ainvoke(initial_state)
        
        if final_state["should_generate_draft"]:
            story = Story(
                headline=news.title,
                hotness_score=final_state["hotness_score"],
                why_now=final_state["why_now"],
                entities=final_state["entities"],
                sources=[{"url": news.url, "timestamp": news.published_at.isoformat()}],
                timeline=final_state["timeline"],
                draft=final_state["draft"],
            )
            self.db.add(story)
            await self.db.commit()
            await self.db.refresh(story)
            
            news.story_id = story.id
            await self.db.commit()
            
            logger.info(f"Created story {story.id} for news {news_id}")
            return story
        
        logger.info(f"News {news_id} did not pass hotness threshold")
        return None
    
    async def get_top_stories(
        self,
        hours: int = 24,
        limit: int = 10
    ) -> List[Story]:
        """Получение топ-K горячих сюжетов за период."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        result = await self.db.execute(
            select(Story)
            .where(Story.created_at >= cutoff_time)
            .order_by(desc(Story.hotness_score))
            .limit(limit)
        )
        
        stories = result.scalars().all()
        logger.info(f"Found {len(stories)} hot stories in last {hours} hours")
        
        return stories


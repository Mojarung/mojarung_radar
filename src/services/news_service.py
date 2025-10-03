from uuid import UUID

from src.core.logging import get_logger
from src.domain.entities import News, Story
from src.infrastructure.database.repositories import NewsRepository, StoryRepository

logger = get_logger(__name__)


class NewsService:
    def __init__(
        self,
        news_repository: NewsRepository,
        story_repository: StoryRepository,
    ):
        self.news_repo = news_repository
        self.story_repo = story_repository

    async def add_news(self, news: News) -> News:
        existing = await self.news_repo.get_by_url(news.url)
        if existing:
            logger.info("news_duplicate", url=news.url)
            return existing

        saved = await self.news_repo.add(news)
        logger.info("news_added", news_id=str(saved.id), source=saved.source)
        return saved

    async def get_news_by_cluster(self, cluster_id: UUID) -> list[News]:
        return await self.news_repo.get_by_cluster(cluster_id)

    async def create_story(self, story: Story) -> Story:
        saved = await self.story_repo.add(story)
        logger.info("story_created", story_id=str(saved.id), hotness=saved.hotness_score)
        return saved

    async def update_story(self, story: Story) -> Story:
        updated = await self.story_repo.update(story)
        logger.info("story_updated", story_id=str(updated.id), hotness=updated.hotness_score)
        return updated

    async def get_top_stories(self, limit: int = 10) -> list[Story]:
        return await self.story_repo.get_top_hot_stories(limit)


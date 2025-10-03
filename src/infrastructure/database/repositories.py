from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NewsNotFoundException
from src.domain.entities import Entity, News, Story
from src.infrastructure.database.models import EntityModel, NewsModel, StoryModel


class NewsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, news: News) -> News:
        news_model = NewsModel(
            id=news.id,
            title=news.title,
            content=news.content,
            source=news.source,
            url=news.url,
            published_at=news.published_at,
            cluster_id=news.cluster_id,
            metadata=news.metadata,
        )
        self.session.add(news_model)
        await self.session.flush()
        return news

    async def get_by_id(self, news_id: UUID) -> News:
        result = await self.session.execute(select(NewsModel).where(NewsModel.id == news_id))
        news_model = result.scalar_one_or_none()
        if not news_model:
            raise NewsNotFoundException(f"News with id {news_id} not found")
        return self._to_entity(news_model)

    async def get_by_url(self, url: str) -> News | None:
        result = await self.session.execute(select(NewsModel).where(NewsModel.url == url))
        news_model = result.scalar_one_or_none()
        return self._to_entity(news_model) if news_model else None

    async def get_by_cluster(self, cluster_id: UUID) -> list[News]:
        result = await self.session.execute(
            select(NewsModel).where(NewsModel.cluster_id == cluster_id)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    def _to_entity(self, model: NewsModel) -> News:
        return News(
            id=model.id,
            title=model.title,
            content=model.content,
            source=model.source,
            url=model.url,
            published_at=model.published_at,
            cluster_id=model.cluster_id,
            metadata=model.metadata,
            created_at=model.created_at,
        )


class StoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, story: Story) -> Story:
        story_model = StoryModel(
            id=story.id,
            headline=story.headline,
            hotness_score=story.hotness_score,
            why_now=story.why_now,
            sources=story.sources,
            timeline=[e.model_dump() for e in story.timeline] if story.timeline else [],
            draft=story.draft,
            news_count=story.news_count,
        )
        self.session.add(story_model)
        await self.session.flush()
        return story

    async def update(self, story: Story) -> Story:
        result = await self.session.execute(select(StoryModel).where(StoryModel.id == story.id))
        story_model = result.scalar_one_or_none()
        if not story_model:
            raise NewsNotFoundException(f"Story with id {story.id} not found")

        story_model.headline = story.headline
        story_model.hotness_score = story.hotness_score
        story_model.why_now = story.why_now
        story_model.sources = story.sources
        story_model.timeline = [e if isinstance(e, dict) else e.model_dump() for e in story.timeline]
        story_model.draft = story.draft
        story_model.news_count = story.news_count

        await self.session.flush()
        return story

    async def get_by_id(self, story_id: UUID) -> Story | None:
        result = await self.session.execute(
            select(StoryModel)
            .options(selectinload(StoryModel.entities))
            .where(StoryModel.id == story_id)
        )
        story_model = result.scalar_one_or_none()
        return self._to_entity(story_model) if story_model else None

    async def get_top_hot_stories(self, limit: int = 10) -> list[Story]:
        result = await self.session.execute(
            select(StoryModel)
            .options(selectinload(StoryModel.entities))
            .order_by(desc(StoryModel.hotness_score))
            .limit(limit)
        )
        return [self._to_entity(model) for model in result.scalars().all()]

    def _to_entity(self, model: StoryModel) -> Story:
        return Story(
            id=model.id,
            headline=model.headline,
            hotness_score=model.hotness_score,
            why_now=model.why_now,
            entities=[self._entity_to_domain(e) for e in model.entities] if model.entities else [],
            sources=model.sources or [],
            timeline=model.timeline or [],
            draft=model.draft,
            news_count=model.news_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _entity_to_domain(self, model: EntityModel) -> Entity:
        return Entity(
            id=model.id,
            name=model.name,
            entity_type=model.entity_type,
            ticker=model.ticker,
            sector=model.sector,
            country=model.country,
            metadata=model.metadata or {},
        )


class EntityRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, entity: Entity) -> Entity:
        entity_model = EntityModel(
            id=entity.id,
            name=entity.name,
            entity_type=entity.entity_type,
            ticker=entity.ticker,
            sector=entity.sector,
            country=entity.country,
            metadata=entity.metadata,
        )
        self.session.add(entity_model)
        await self.session.flush()
        return entity

    async def get_or_create(self, name: str, entity_type: str, **kwargs: Any) -> Entity:
        result = await self.session.execute(
            select(EntityModel).where(EntityModel.name == name)
        )
        entity_model = result.scalar_one_or_none()

        if entity_model:
            return self._to_entity(entity_model)

        entity = Entity(name=name, entity_type=entity_type, **kwargs)
        return await self.add(entity)

    def _to_entity(self, model: EntityModel) -> Entity:
        return Entity(
            id=model.id,
            name=model.name,
            entity_type=model.entity_type,
            ticker=model.ticker,
            sector=model.sector,
            country=model.country,
            metadata=model.metadata or {},
        )


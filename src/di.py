from collections.abc import AsyncIterator

from dishka import Provider, Scope, from_context, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.agents.graph import create_radar_graph
from src.agents.nodes import (
    ContextRAGNode,
    DeduplicationNode,
    DraftGeneratorNode,
    EnrichmentNode,
    ScoringNode,
)
from src.core.config import Settings, get_settings
from src.infrastructure.database import (
    EntityRepository,
    NewsRepository,
    StoryRepository,
    create_engine,
    create_session_factory,
)
from src.infrastructure.llm import BaseLLM, OpenRouterLLM
from src.infrastructure.redis import CacheService, RedisClient
from src.services import EmbeddingsService, NewsService, ScoringService


class ConfigProvider(Provider):
    scope = Scope.APP

    @provide
    def get_settings(self) -> Settings:
        return get_settings()


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    def get_engine(self, settings: Settings) -> AsyncEngine:
        return create_engine(settings)

    @provide(scope=Scope.APP)
    def get_session_factory(self, engine: AsyncEngine) -> sessionmaker:
        return create_session_factory(engine)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_factory: sessionmaker
    ) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def get_news_repository(self, session: AsyncSession) -> NewsRepository:
        return NewsRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_story_repository(self, session: AsyncSession) -> StoryRepository:
        return StoryRepository(session)

    @provide(scope=Scope.REQUEST)
    def get_entity_repository(self, session: AsyncSession) -> EntityRepository:
        return EntityRepository(session)


class RedisProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_redis_client(self, settings: Settings) -> AsyncIterator[RedisClient]:
        client = RedisClient(settings)
        await client.connect()
        yield client
        await client.disconnect()

    @provide(scope=Scope.REQUEST)
    def get_cache_service(self, redis_client: RedisClient) -> CacheService:
        return CacheService(redis_client)


class LLMProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_llm(self, settings: Settings) -> AsyncIterator[BaseLLM]:
        llm = OpenRouterLLM(settings)
        yield llm
        await llm.close()


class ServicesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_embeddings_service(
        self, settings: Settings, redis_client: RedisClient
    ) -> EmbeddingsService:
        return EmbeddingsService(settings, redis_client)

    @provide(scope=Scope.REQUEST)
    def get_scoring_service(self) -> ScoringService:
        return ScoringService()

    @provide(scope=Scope.REQUEST)
    def get_news_service(
        self,
        news_repository: NewsRepository,
        story_repository: StoryRepository,
    ) -> NewsService:
        return NewsService(news_repository, story_repository)


class AgentsProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_dedup_node(
        self, embeddings_service: EmbeddingsService, settings: Settings
    ) -> DeduplicationNode:
        return DeduplicationNode(embeddings_service, settings)

    @provide(scope=Scope.REQUEST)
    def get_enrichment_node(self) -> EnrichmentNode:
        return EnrichmentNode()

    @provide(scope=Scope.REQUEST)
    def get_scoring_node(
        self, scoring_service: ScoringService, settings: Settings
    ) -> ScoringNode:
        return ScoringNode(scoring_service, settings)

    @provide(scope=Scope.REQUEST)
    def get_context_rag_node(self, llm: BaseLLM) -> ContextRAGNode:
        return ContextRAGNode(llm)

    @provide(scope=Scope.REQUEST)
    def get_draft_generator_node(self, llm: BaseLLM) -> DraftGeneratorNode:
        return DraftGeneratorNode(llm)

    @provide(scope=Scope.REQUEST)
    def get_radar_graph(
        self,
        dedup_node: DeduplicationNode,
        enrichment_node: EnrichmentNode,
        scoring_node: ScoringNode,
        context_rag_node: ContextRAGNode,
        draft_generator_node: DraftGeneratorNode,
    ):
        return create_radar_graph(
            dedup_node,
            enrichment_node,
            scoring_node,
            context_rag_node,
            draft_generator_node,
        )


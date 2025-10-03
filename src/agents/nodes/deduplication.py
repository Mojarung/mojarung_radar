from src.agents.state import RadarState
from src.core.config import Settings
from src.core.logging import get_logger
from src.services.embeddings_service import EmbeddingsService

logger = get_logger(__name__)


class DeduplicationNode:
    def __init__(self, embeddings_service: EmbeddingsService, settings: Settings):
        self.embeddings = embeddings_service
        self.settings = settings

    async def __call__(self, state: RadarState) -> RadarState:
        logger.info("deduplication_started")

        news_text = state["initial_news"].get("title", "") + " " + state["initial_news"].get("content", "")

        similarity = 0.0
        if state.get("related_articles"):
            for article in state["related_articles"]:
                article_text = article.get("title", "") + " " + article.get("content", "")
                sim = await self.embeddings.compute_similarity(news_text, article_text)
                similarity = max(similarity, sim)

        is_duplicate = similarity > self.settings.dedup_similarity_threshold

        logger.info(
            "deduplication_completed",
            similarity=similarity,
            is_duplicate=is_duplicate,
            threshold=self.settings.dedup_similarity_threshold,
        )

        return {
            **state,
            "is_new_cluster": not is_duplicate,
        }


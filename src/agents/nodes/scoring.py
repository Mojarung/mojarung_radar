from src.agents.state import RadarState
from src.core.config import Settings
from src.core.logging import get_logger
from src.services.scoring_service import ScoringService

logger = get_logger(__name__)


class ScoringNode:
    def __init__(self, scoring_service: ScoringService, settings: Settings):
        self.scoring = scoring_service
        self.settings = settings

    async def __call__(self, state: RadarState) -> RadarState:
        logger.info("scoring_started")

        unexpectedness = 0.5
        materiality = 0.6
        velocity = len(state.get("related_articles", [])) * 0.1
        breadth = len(state.get("entities", {}).get("companies", [])) * 0.1
        credibility = state.get("source_reputation", 0.5)

        hotness = await self.scoring.calculate_hotness(
            unexpectedness=unexpectedness,
            materiality=materiality,
            velocity=min(velocity, 1.0),
            breadth=min(breadth, 1.0),
            credibility=credibility,
        )

        is_hot = hotness.value >= self.settings.hotness_threshold

        logger.info(
            "scoring_completed",
            hotness_score=hotness.value,
            is_hot=is_hot,
            threshold=self.settings.hotness_threshold,
        )

        return {
            **state,
            "hotness_score": hotness.value,
            "is_hot": is_hot,
        }


from src.core.logging import get_logger
from src.domain.value_objects import HotnessScore

logger = get_logger(__name__)


class ScoringService:
    def __init__(self):
        pass

    async def calculate_hotness(
        self,
        unexpectedness: float = 0.0,
        materiality: float = 0.0,
        velocity: float = 0.0,
        breadth: float = 0.0,
        credibility: float = 0.0,
    ) -> HotnessScore:
        weights = {
            "unexpectedness": 0.25,
            "materiality": 0.30,
            "velocity": 0.20,
            "breadth": 0.15,
            "credibility": 0.10,
        }

        total_score = (
            unexpectedness * weights["unexpectedness"]
            + materiality * weights["materiality"]
            + velocity * weights["velocity"]
            + breadth * weights["breadth"]
            + credibility * weights["credibility"]
        )

        logger.info(
            "hotness_calculated",
            total_score=total_score,
            unexpectedness=unexpectedness,
            materiality=materiality,
            velocity=velocity,
            breadth=breadth,
            credibility=credibility,
        )

        return HotnessScore(
            value=min(max(total_score, 0.0), 1.0),
            unexpectedness=unexpectedness,
            materiality=materiality,
            velocity=velocity,
            breadth=breadth,
            credibility=credibility,
        )


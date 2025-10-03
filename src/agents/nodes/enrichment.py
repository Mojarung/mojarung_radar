from src.agents.state import RadarState
from src.core.logging import get_logger

logger = get_logger(__name__)


class EnrichmentNode:
    def __init__(self):
        pass

    async def __call__(self, state: RadarState) -> RadarState:
        logger.info("enrichment_started")

        entities = {
            "companies": [],
            "tickers": [],
            "sectors": [],
            "countries": [],
        }

        logger.info("enrichment_completed", entities_count=sum(len(v) for v in entities.values()))

        return {
            **state,
            "entities": entities,
            "source_reputation": 0.7,
        }


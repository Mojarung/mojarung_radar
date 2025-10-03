from app.graph.state import RadarState
from app.core.logging import get_logger

logger = get_logger(__name__)


async def ingestion_node(state: RadarState) -> RadarState:
    """Узел приема новостей.
    
    В реальной системе здесь будет подключение к внешним источникам:
    - RSS feeds
    - API новостных агентств
    - Социальные сети
    """
    logger.info(f"Ingestion node processing: {state['news_title']}")
    
    state["is_duplicate"] = False
    state["should_generate_draft"] = False
    state["hotness_score"] = 0.0
    state["related_articles"] = []
    state["entities"] = []
    state["timeline"] = []
    
    return state


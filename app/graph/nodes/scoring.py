from app.graph.state import RadarState
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


async def scoring_node(state: RadarState) -> RadarState:
    """Узел оценки горячести новости.
    
    Рассчитывает hotness_score на основе:
    - Неожиданности (новизна темы)
    - Материальности (ключевые слова)
    - Скорости распространения (количество связанных статей)
    - Широты охвата (количество затронутых сущностей)
    - Достоверности источника
    """
    logger.info(f"Scoring node processing: {state['news_id']}")
    
    score = 0.0
    
    materiality_keywords = [
        "слияние", "поглощение", "банкротство", "регулятор",
        "санкции", "иск", "guidance", "прогноз", "дефолт"
    ]
    
    content_lower = state["news_content"].lower()
    materiality_score = sum(
        0.2 for keyword in materiality_keywords if keyword in content_lower
    )
    score += min(materiality_score, 0.4)
    
    breadth_score = min(len(state["entities"]) * 0.1, 0.3)
    score += breadth_score
    
    velocity_score = min(len(state["related_articles"]) * 0.05, 0.2)
    score += velocity_score
    
    score += state.get("source_reputation", 0.5) * 0.1
    
    state["hotness_score"] = min(score, 1.0)
    
    state["should_generate_draft"] = state["hotness_score"] >= settings.hotness_threshold
    
    logger.info(f"Hotness score: {state['hotness_score']:.2f}")
    
    return state


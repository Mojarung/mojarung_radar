from app.graph.state import RadarState
from app.core.logging import get_logger
from app.llm import OpenRouterProvider
from datetime import datetime

logger = get_logger(__name__)


async def enrichment_node(state: RadarState) -> RadarState:
    """Узел обогащения - извлечение сущностей и метаданных.
    
    Использует LLM для:
    - Извлечения компаний, тикеров, стран
    - Классификации типа новости
    """
    logger.info(f"Enrichment node processing: {state['news_id']}")
    
    llm = OpenRouterProvider()
    
    prompt = f"""Проанализируй следующую новость и извлеки:
1. Компании, тикеры, страны, сектора (список через запятую)
2. Тип новости (merger, acquisition, regulatory, guidance, earnings, lawsuit, другое)

Новость:
Заголовок: {state['news_title']}
Содержание: {state['news_content']}
"""
    
    try:
        result = await llm.generate_structured(
            prompt,
            response_format={
                "entities": ["entity1", "entity2"],
                "news_type": "type"
            }
        )
        
        state["entities"] = result.get("entities", [])
        
        state["timeline"].append({
            "timestamp": state["published_at"].isoformat(),
            "event": f"Первое упоминание: {state['news_title']}",
            "source_url": state["news_url"]
        })
        
        logger.info(f"Extracted entities: {state['entities']}")
    except Exception as e:
        logger.error(f"Error in enrichment: {e}")
        state["entities"] = []
    
    return state


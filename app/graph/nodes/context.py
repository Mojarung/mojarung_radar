from app.graph.state import RadarState
from app.core.logging import get_logger
from app.llm import OpenRouterProvider

logger = get_logger(__name__)


async def context_builder_node(state: RadarState) -> RadarState:
    """Узел сборки контекста через RAG.
    
    Генерирует объяснение "почему сейчас" на основе:
    - Всех статей в кластере
    - Временной шкалы событий
    - Извлеченных сущностей
    """
    logger.info(f"Context builder node processing: {state['news_id']}")
    
    llm = OpenRouterProvider()
    
    articles_context = "\n".join([
        f"- {art.get('title', '')}: {art.get('content', '')[:200]}"
        for art in state["related_articles"]
    ])
    
    timeline_context = "\n".join([
        f"- {entry['timestamp']}: {entry['event']}"
        for entry in state["timeline"]
    ])
    
    prompt = f"""На основе предоставленных данных объясни в 1-2 предложениях, почему этот сюжет важен именно сейчас.

Основная новость:
{state['news_title']}
{state['news_content']}

Связанные статьи:
{articles_context or 'Нет связанных статей'}

Временная шкала:
{timeline_context}

Затронутые сущности: {', '.join(state['entities'])}
"""
    
    try:
        why_now = await llm.generate(
            prompt,
            system_prompt="Ты финансовый аналитик. Будь кратким и конкретным.",
            max_tokens=300
        )
        state["why_now"] = why_now.strip()
        logger.info(f"Generated why_now: {state['why_now'][:100]}...")
    except Exception as e:
        logger.error(f"Error in context builder: {e}")
        state["why_now"] = "Информация недоступна"
    
    return state


from app.graph.state import RadarState
from app.core.logging import get_logger
from app.llm import OpenRouterProvider

logger = get_logger(__name__)


async def draft_generator_node(state: RadarState) -> RadarState:
    """Узел генерации черновика публикации.
    
    Создает структурированный текст:
    - Заголовок
    - Лид-абзац
    - 3 ключевых пункта
    - Цитата/ссылка на источник
    """
    logger.info(f"Draft generator node processing: {state['news_id']}")
    
    llm = OpenRouterProvider()
    
    sources_list = "\n".join([
        f"- {entry['source_url']}"
        for entry in state["timeline"]
    ])
    
    prompt = f"""Создай черновик поста о финансовой новости со следующей структурой:

1. Заголовок (привлекательный, но точный)
2. Лид-абзац (1-2 предложения - суть новости)
3. Три ключевых пункта (bullet points)
4. Заключение с указанием источника

Данные:
Заголовок новости: {state['news_title']}
Почему это важно: {state['why_now']}
Затронутые компании/активы: {', '.join(state['entities'])}

Источники:
{sources_list}

Важно: Используй только предоставленную информацию, все утверждения должны быть проверяемы по источникам.
"""
    
    try:
        draft = await llm.generate(
            prompt,
            system_prompt="Ты финансовый журналист. Пиши четко, фактически точно, без преувеличений.",
            max_tokens=800
        )
        state["draft"] = draft.strip()
        logger.info("Draft generated successfully")
    except Exception as e:
        logger.error(f"Error in draft generator: {e}")
        state["draft"] = f"# {state['news_title']}\n\n{state['why_now']}"
    
    return state


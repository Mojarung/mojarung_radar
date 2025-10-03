from src.agents.state import RadarState
from src.core.logging import get_logger
from src.infrastructure.llm.base import BaseLLM

logger = get_logger(__name__)


class DraftGeneratorNode:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def __call__(self, state: RadarState) -> RadarState:
        logger.info("draft_generation_started")

        headline = state["initial_news"].get("title", "")
        why_now = state.get("narrative_summary", "")
        entities = state.get("entities", {})

        prompt = f"""Создай черновик поста на основе следующей информации:

Заголовок: {headline}
Почему важно сейчас: {why_now}
Затронутые компании: {', '.join(entities.get('companies', [])[:5])}

Формат:
- Заголовок (краткий, цепляющий)
- Лид-абзац (1-2 предложения)
- 3 буллета с ключевыми фактами
- Цитата/источник

Пиши профессионально, кратко, без эмодзи."""

        try:
            draft = await self.llm.generate(prompt, temperature=0.5, max_tokens=500)
        except Exception as e:
            logger.error("draft_generation_failed", error=str(e))
            draft = f"# {headline}\n\n{why_now}"

        final_output = {
            "headline": headline,
            "hotness": state.get("hotness_score", 0.0),
            "why_now": why_now,
            "entities": entities,
            "sources": [state["initial_news"].get("url", "")],
            "timeline": state.get("timeline", []),
            "draft": draft,
        }

        logger.info("draft_generation_completed")

        return {
            **state,
            "final_output": final_output,
        }


from src.agents.state import RadarState
from src.core.logging import get_logger
from src.infrastructure.llm.base import BaseLLM

logger = get_logger(__name__)


class ContextRAGNode:
    def __init__(self, llm: BaseLLM):
        self.llm = llm

    async def __call__(self, state: RadarState) -> RadarState:
        logger.info("context_rag_started")

        articles = state.get("related_articles", [])
        context = "\n\n".join(
            [f"- {a.get('title', '')}: {a.get('content', '')[:200]}" for a in articles[:5]]
        )

        prompt = f"""На основе следующих статей кратко объясни, почему этот сюжет важен именно сейчас:

{context}

Ответ должен быть 1-2 предложения."""

        try:
            why_now = await self.llm.generate(prompt, temperature=0.3, max_tokens=200)
        except Exception as e:
            logger.error("context_rag_failed", error=str(e))
            why_now = "Не удалось сгенерировать контекст"

        timeline = [
            {
                "timestamp": state["initial_news"].get("published_at"),
                "event": "Первое упоминание",
                "source": state["initial_news"].get("source"),
            }
        ]

        logger.info("context_rag_completed")

        return {
            **state,
            "narrative_summary": why_now,
            "timeline": timeline,
        }


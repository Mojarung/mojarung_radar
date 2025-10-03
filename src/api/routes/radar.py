from datetime import datetime

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.agents.state import RadarState
from src.core.config import Settings
from src.core.logging import get_logger
from src.services import NewsService

logger = get_logger(__name__)

router = APIRouter(prefix="/radar", tags=["radar"])


class NewsInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1, max_length=1000)
    published_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessNewsResponse(BaseModel):
    status: str
    news_id: str | None = None
    hotness_score: float | None = None
    is_hot: bool = False
    final_output: dict | None = None


@router.post("/process-news", response_model=ProcessNewsResponse)
@inject
async def process_news(
    news_input: NewsInput,
    radar_graph: FromDishka,
    news_service: FromDishka[NewsService],
):
    logger.info("processing_news", source=news_input.source, url=news_input.url)

    initial_state: RadarState = {
        "initial_news": news_input.model_dump(),
        "related_articles": [],
        "is_new_cluster": True,
    }

    try:
        result = await radar_graph.ainvoke(initial_state)

        logger.info(
            "news_processed",
            hotness=result.get("hotness_score"),
            is_hot=result.get("is_hot"),
        )

        return ProcessNewsResponse(
            status="processed",
            hotness_score=result.get("hotness_score"),
            is_hot=result.get("is_hot", False),
            final_output=result.get("final_output"),
        )
    except Exception as e:
        logger.error("news_processing_failed", error=str(e))
        return ProcessNewsResponse(status="failed")


@router.get("/top-stories")
@inject
async def get_top_stories(
    limit: int = 10,
    news_service: FromDishka[NewsService],
    settings: FromDishka[Settings],
):
    limit = min(limit, settings.top_k_stories)
    stories = await news_service.get_top_stories(limit)

    return {
        "count": len(stories),
        "stories": [
            {
                "id": str(story.id),
                "headline": story.headline,
                "hotness": story.hotness_score,
                "why_now": story.why_now,
                "entities": [e.model_dump() for e in story.entities],
                "sources": story.sources,
                "draft": story.draft,
                "created_at": story.created_at.isoformat(),
            }
            for story in stories
        ],
    }


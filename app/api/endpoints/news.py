from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.dependencies import get_db
from app.schemas.news import NewsCreate, NewsResponse
from app.schemas.response import TopStoriesResponse, HotStoryResponse
from app.models import News, Source
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/news", response_model=NewsResponse)
async def create_news(
    news_data: NewsCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание новости в БД."""
    news = News(
        title=news_data.title,
        content=news_data.content,
        url=str(news_data.url),
        source_id=news_data.source_id,
        published_at=news_data.published_at
    )

    db.add(news)
    await db.commit()
    await db.refresh(news)

    logger.info(f"Created news {news.id}")

    return news


@router.get("/stories/top", response_model=TopStoriesResponse)
async def get_top_stories(
    hours: int = Query(24, ge=1, le=168, description="Временное окно в часах"),
    limit: int = Query(10, ge=1, le=100, description="Количество сюжетов"),
    db: AsyncSession = Depends(get_db)
):
    """Получение топ-K горячих сюжетов за временное окно."""
    news_service = NewsService(db)
    stories = await news_service.get_top_stories(hours=hours, limit=limit)
    
    stories_response = [
        HotStoryResponse(
            id=story.id,
            headline=story.headline,
            hotness_score=story.hotness_score,
            why_now=story.why_now or "",
            entities=story.entities or [],
            sources=[s.get("url", "") for s in (story.sources or [])],
            timeline=[
                {
                    "timestamp": t.get("timestamp"),
                    "event": t.get("event"),
                    "source_url": t.get("source_url")
                }
                for t in (story.timeline or [])
            ],
            draft=story.draft or "",
            created_at=story.created_at,
            updated_at=story.updated_at
        )
        for story in stories
    ]
    
    return TopStoriesResponse(
        stories=stories_response,
        total=len(stories_response),
        time_window_hours=hours
    )


@router.get("/news/{news_id}", response_model=NewsResponse)
async def get_news(
    news_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Получение новости по ID."""
    from sqlalchemy import select
    
    result = await db.execute(
        select(News).where(News.id == news_id)
    )
    news = result.scalar_one_or_none()
    
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    return news


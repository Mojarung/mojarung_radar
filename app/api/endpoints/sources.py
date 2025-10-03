from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from app.core.dependencies import get_db
from app.models import Source
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class SourceCreate(BaseModel):
    name: str
    url: str


class SourceResponse(BaseModel):
    id: UUID
    name: str
    url: str
    reputation_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("/sources", response_model=SourceResponse)
async def create_source(
    source_data: SourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание источника новостей."""
    # Проверяем, что источник с таким именем не существует
    result = await db.execute(select(Source).where(Source.name == source_data.name))
    existing_source = result.scalar_one_or_none()
    if existing_source:
        raise HTTPException(status_code=400, detail="Source with this name already exists")

    source = Source(
        name=source_data.name,
        url=source_data.url
    )

    db.add(source)
    await db.commit()
    await db.refresh(source)

    logger.info(f"Created source {source.id}")

    return source

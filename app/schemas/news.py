from pydantic import BaseModel, HttpUrl
from datetime import datetime
from uuid import UUID
from typing import Optional


class NewsBase(BaseModel):
    title: str
    content: str
    url: HttpUrl
    published_at: datetime


class NewsCreate(NewsBase):
    source_id: UUID


class NewsResponse(NewsBase):
    id: UUID
    source_id: UUID
    story_id: Optional[UUID] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


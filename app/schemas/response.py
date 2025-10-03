from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime


class TimelineEntry(BaseModel):
    timestamp: datetime
    event: str
    source_url: str


class HotStoryResponse(BaseModel):
    id: UUID
    headline: str
    hotness_score: float
    why_now: str
    entities: List[str]
    sources: List[str]
    timeline: List[TimelineEntry]
    draft: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TopStoriesResponse(BaseModel):
    stories: List[HotStoryResponse]
    total: int
    time_window_hours: int


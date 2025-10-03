from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class News(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    cluster_id: UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Entity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    entity_type: str
    ticker: str | None = None
    sector: str | None = None
    country: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Story(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    headline: str
    hotness_score: float = Field(ge=0.0, le=1.0)
    why_now: str
    entities: list[Entity] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    draft: str | None = None
    news_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TimelineEvent(BaseModel):
    timestamp: datetime
    event_type: str
    description: str
    source_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: UUID
    event_type: str
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)


class NewsIngested(DomainEvent):
    event_type: str = "news_ingested"


class NewsDeduped(DomainEvent):
    event_type: str = "news_deduped"


class NewsEnriched(DomainEvent):
    event_type: str = "news_enriched"


class StoryScored(DomainEvent):
    event_type: str = "story_scored"


class DraftGenerated(DomainEvent):
    event_type: str = "draft_generated"


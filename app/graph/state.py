from typing import TypedDict, Optional, List, Dict
from uuid import UUID
from datetime import datetime


class RadarState(TypedDict):
    """Состояние графа агента RADAR."""
    
    news_id: Optional[UUID]
    news_title: str
    news_content: str
    news_url: str
    published_at: datetime
    
    cluster_id: Optional[UUID]
    related_articles: List[Dict]
    
    entities: List[str]
    timeline: List[Dict]
    source_reputation: float
    
    hotness_score: float
    
    context: Optional[str]
    why_now: Optional[str]
    draft: Optional[str]
    
    is_duplicate: bool
    should_generate_draft: bool


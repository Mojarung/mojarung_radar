"""Pydantic schemas for API request/response validation"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request schema for news analysis endpoint"""
    
    time_window_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Time window in hours (1-168)"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Number of top stories to return (1-50)"
    )


class TimelineEvent(BaseModel):
    """Timeline event in the news story"""
    
    time: str = Field(description="Timestamp of the event")
    event: str = Field(description="Description of the event")


class NewsSource(BaseModel):
    """Source reference for a news story"""
    
    url: str = Field(description="URL of the source article")
    title: str = Field(description="Title of the source article")
    published_at: Optional[str] = Field(None, description="Publication timestamp")


class AnalysisResult(BaseModel):
    """Single news story analysis result"""
    
    dedup_group: str = Field(description="Deduplication group ID")
    hotness: float = Field(
        ge=0.0,
        le=1.0,
        description="Hotness score between 0 and 1"
    )
    headline: str = Field(description="Concise headline for the story")
    why_now: str = Field(description="1-2 sentences explaining current importance")
    entities: List[str] = Field(
        default_factory=list,
        description="Companies, tickers, countries, sectors mentioned"
    )
    sources: List[NewsSource] = Field(
        default_factory=list,
        description="3-5 verifiable source links"
    )
    timeline: List[TimelineEvent] = Field(
        default_factory=list,
        description="Key timestamps in the story development"
    )
    draft: str = Field(description="Draft post with lead, bullets, and quote")
    telegram_post: str = Field(
        default="",
        description="Ready-to-publish Telegram post with emoji and interactive elements"
    )


class AnalysisResponse(BaseModel):
    """Response schema for news analysis endpoint"""
    
    results: List[AnalysisResult] = Field(
        description="List of top K news stories"
    )
    total_articles_analyzed: int = Field(
        description="Total number of articles in time window"
    )
    total_clusters: int = Field(
        description="Total number of news clusters found"
    )
    analysis_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this analysis was performed"
    )


class HealthResponse(BaseModel):
    """Health check response"""
    
    status: str = Field(default="healthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


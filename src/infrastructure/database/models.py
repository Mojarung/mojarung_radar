from datetime import datetime
from uuid import uuid4

from sqlalchemy import TIMESTAMP, JSON, Column, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


story_entities = Table(
    "story_entities",
    Base.metadata,
    Column("story_id", UUID(as_uuid=True), ForeignKey("stories.id"), primary_key=True),
    Column("entity_id", UUID(as_uuid=True), ForeignKey("entities.id"), primary_key=True),
)


class NewsModel(Base):
    __tablename__ = "news"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    published_at = Column(TIMESTAMP, nullable=False)
    cluster_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=True)
    metadata = Column(JSON, default={})
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    story = relationship("StoryModel", back_populates="news_items")


class EntityModel(Base):
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(200), nullable=False, unique=True)
    entity_type = Column(String(50), nullable=False)
    ticker = Column(String(20), nullable=True)
    sector = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    metadata = Column(JSON, default={})

    stories = relationship("StoryModel", secondary=story_entities, back_populates="entities")


class StoryModel(Base):
    __tablename__ = "stories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    headline = Column(String(500), nullable=False)
    hotness_score = Column(Float, nullable=False, default=0.0)
    why_now = Column(Text, nullable=True)
    sources = Column(JSON, default=[])
    timeline = Column(JSON, default=[])
    draft = Column(Text, nullable=True)
    news_count = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    news_items = relationship("NewsModel", back_populates="story")
    entities = relationship("EntityModel", secondary=story_entities, back_populates="stories")


class TimelineModel(Base):
    __tablename__ = "timelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=True)
    metadata = Column(JSON, default={})


class SourceReputationModel(Base):
    __tablename__ = "source_reputations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_name = Column(String(100), nullable=False, unique=True)
    reputation_score = Column(Float, nullable=False, default=0.5)
    trust_level = Column(String(20), nullable=False, default="unknown")
    verification_count = Column(Integer, default=0)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


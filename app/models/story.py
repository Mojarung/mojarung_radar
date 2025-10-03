from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.session import Base


class Story(Base):
    __tablename__ = "stories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    headline = Column(String, nullable=False)
    hotness_score = Column(Float, default=0.0, index=True)
    why_now = Column(String)
    entities = Column(JSON, default=list)
    sources = Column(JSON, default=list)
    timeline = Column(JSON, default=list)
    draft = Column(String)
    embedding = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.db.session import Base


class News(Base):
    __tablename__ = "news"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String, unique=True, nullable=False, index=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"))
    story_id = Column(UUID(as_uuid=True), ForeignKey("stories.id"), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)


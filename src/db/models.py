"""SQLAlchemy models for PostgreSQL"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Source(Base):
    """News source model with reputation score"""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, unique=True, nullable=False)
    reputation_score = Column(Float, default=0.5, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Source(id={self.id}, name='{self.name}', reputation_score={self.reputation_score})>"


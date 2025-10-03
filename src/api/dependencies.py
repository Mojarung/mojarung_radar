"""FastAPI dependencies"""
from sqlalchemy.orm import Session
from src.db.session import SessionLocal


def get_db():
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


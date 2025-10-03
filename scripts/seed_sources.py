"""Seed the database with initial news sources"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db.session import get_db_context
from src.db.models import Source
from src.core.logging_config import log


INITIAL_SOURCES = [
    {"name": "Bloomberg", "url": "https://www.bloomberg.com", "reputation_score": 0.9},
    {"name": "Reuters", "url": "https://www.reuters.com", "reputation_score": 0.9},
    {"name": "Financial Times", "url": "https://www.ft.com", "reputation_score": 0.85},
    {"name": "Wall Street Journal", "url": "https://www.wsj.com", "reputation_score": 0.85},
    {"name": "CNBC", "url": "https://www.cnbc.com", "reputation_score": 0.75},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com", "reputation_score": 0.65},
    {"name": "MarketWatch", "url": "https://www.marketwatch.com", "reputation_score": 0.70},
]


def main():
    """Seed initial news sources"""
    log.info("Seeding news sources...")
    
    try:
        with get_db_context() as db:
            for source_data in INITIAL_SOURCES:
                # Check if source already exists
                existing = db.query(Source).filter(
                    Source.name == source_data["name"]
                ).first()
                
                if existing:
                    log.info(f"Source '{source_data['name']}' already exists, skipping")
                    continue
                
                # Create new source
                source = Source(**source_data)
                db.add(source)
                log.info(f"Created source: {source_data['name']} (reputation: {source_data['reputation_score']})")
            
            db.commit()
        
        log.info("Source seeding completed successfully!")
        
    except Exception as e:
        log.error(f"Source seeding failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


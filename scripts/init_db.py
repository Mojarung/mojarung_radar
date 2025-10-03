"""Initialize databases and create tables"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db.session import init_db
from src.db.clickhouse_client import get_clickhouse_client
from src.core.logging_config import log


def main():
    """Initialize PostgreSQL and ClickHouse databases"""
    log.info("Initializing databases...")
    
    try:
        # Initialize PostgreSQL tables
        log.info("Creating PostgreSQL tables...")
        init_db()
        
        # Initialize ClickHouse tables (happens in constructor)
        log.info("Ensuring ClickHouse tables...")
        clickhouse = get_clickhouse_client()
        
        log.info("Database initialization completed successfully!")
        
    except Exception as e:
        log.error(f"Database initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()


"""ClickHouse client for storing and querying news articles"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import clickhouse_connect
from src.core.config import get_settings
from src.core.logging_config import log

settings = get_settings()


class ClickHouseClient:
    """Client for interacting with ClickHouse database"""

    def __init__(self):
        self.client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_db,
        )
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Create news_articles table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS news_articles (
            id UUID,
            source_id Int16,
            url String,
            title String,
            content String,
            published_at DateTime,
            scraped_at DateTime DEFAULT now(),
            dedup_group UUID,
            companies String DEFAULT '',
            people String DEFAULT ''
        ) ENGINE = MergeTree()
        ORDER BY (published_at, id)
        SETTINGS index_granularity = 8192
        """
        try:
            self.client.command(create_table_query)
            log.info("ClickHouse news_articles table ensured")
        except Exception as e:
            log.error(f"Failed to create ClickHouse table: {e}")
            raise

    def insert_article(
        self,
        article_id: uuid.UUID,
        source_id: int,
        url: str,
        title: str,
        content: str,
        published_at: datetime,
        dedup_group: uuid.UUID,
        companies: str = "",
        people: str = "",
    ) -> bool:
        """Insert a single news article with NER entities"""
        try:
            self.client.insert(
                "news_articles",
                [[
                    str(article_id),
                    source_id,
                    url,
                    title,
                    content,
                    published_at,
                    datetime.utcnow(),
                    str(dedup_group),
                    companies,
                    people,
                ]],
                column_names=[
                    "id",
                    "source_id",
                    "url",
                    "title",
                    "content",
                    "published_at",
                    "scraped_at",
                    "dedup_group",
                    "companies",
                    "people",
                ],
            )
            log.info(f"Inserted article {article_id} into ClickHouse")
            return True
        except Exception as e:
            log.error(f"Failed to insert article into ClickHouse: {e}")
            return False

    def get_recent_articles(
        self, time_window_hours: int = 720
    ) -> List[Dict[str, Any]]:
        """Fetch articles from the specified time window"""
        query = f"""
        SELECT 
            id,
            source_id,
            url,
            title,
            content,
            published_at,
            scraped_at,
            dedup_group,
            companies,
            people
        FROM news_articles
        WHERE published_at >= now() - INTERVAL {time_window_hours} HOUR
        ORDER BY published_at DESC
        """
        try:
            result = self.client.query(query)
            articles = []
            for row in result.result_rows:
                articles.append({
                    "id": row[0],
                    "source_id": row[1],
                    "url": row[2],
                    "title": row[3],
                    "content": row[4],
                    "published_at": row[5],
                    "scraped_at": row[6],
                    "dedup_group": row[7],
                    "companies": row[8],
                    "people": row[9],
                })
            log.info(f"Fetched {len(articles)} articles from last {time_window_hours} hours")
            return articles
        except Exception as e:
            log.error(f"Failed to fetch recent articles: {e}")
            return []

    def get_articles_by_dedup_group(self, dedup_group: uuid.UUID) -> List[Dict[str, Any]]:
        """Fetch all articles belonging to a deduplication group"""
        query = """
        SELECT 
            id,
            source_id,
            url,
            title,
            content,
            published_at,
            scraped_at,
            dedup_group,
            companies,
            people
        FROM news_articles
        WHERE dedup_group = %(dedup_group)s
        ORDER BY published_at ASC
        """
        try:
            result = self.client.query(
                query,
                parameters={"dedup_group": str(dedup_group)}
            )
            articles = []
            for row in result.result_rows:
                articles.append({
                    "id": row[0],
                    "source_id": row[1],
                    "url": row[2],
                    "title": row[3],
                    "content": row[4],
                    "published_at": row[5],
                    "scraped_at": row[6],
                    "dedup_group": row[7],
                    "companies": row[8],
                    "people": row[9],
                })
            return articles
        except Exception as e:
            log.error(f"Failed to fetch articles by dedup group: {e}")
            return []

    def count_articles_by_dedup_group_over_time(
        self, dedup_group: uuid.UUID, time_window_hours: int = 720
    ) -> int:
        """Count articles in a dedup group within a time window"""
        query = """
        SELECT COUNT(*) as count
        FROM news_articles
        WHERE dedup_group = %(dedup_group)s
        AND published_at >= now() - INTERVAL %(hours)s HOUR
        """
        try:
            result = self.client.query(
                query,
                parameters={
                    "dedup_group": str(dedup_group),
                    "hours": time_window_hours
                }
            )
            return result.result_rows[0][0] if result.result_rows else 0
        except Exception as e:
            log.error(f"Failed to count articles by dedup group: {e}")
            return 0

    def close(self):
        """Close the ClickHouse connection"""
        self.client.close()


# Singleton instance
_clickhouse_client: Optional[ClickHouseClient] = None


def get_clickhouse_client() -> ClickHouseClient:
    """Get singleton ClickHouse client instance"""
    global _clickhouse_client
    if _clickhouse_client is None:
        _clickhouse_client = ClickHouseClient()
    return _clickhouse_client


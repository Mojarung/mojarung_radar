"""RabbitMQ consumer for processing incoming news articles"""
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from aio_pika import connect_robust, Message, IncomingMessage
from aio_pika.abc import AbstractRobustConnection
from src.core.config import get_settings
from src.core.logging_config import log
from src.db.session import get_db_context
from src.db.models import Source
from src.db.clickhouse_client import get_clickhouse_client
from src.services.dedup import get_dedup_service

settings = get_settings()


class NewsProcessor:
    """Worker that processes incoming news from RabbitMQ"""

    def __init__(self):
        self.connection: AbstractRobustConnection = None
        self.clickhouse = get_clickhouse_client()
        self.dedup_service = get_dedup_service()

    async def connect(self):
        """Establish connection to RabbitMQ"""
        log.info(f"Connecting to RabbitMQ: {settings.rabbitmq_url}")
        self.connection = await connect_robust(settings.rabbitmq_url)
        log.info("Connected to RabbitMQ")

    async def process_message(self, message: IncomingMessage):
        """Process a single news article message"""
        async with message.process():
            try:
                # Parse message
                body = json.loads(message.body.decode())
                log.info(f"Processing news: {body.get('title', '')[:50]}...")

                # Extract fields
                source_name = body.get("source_name")
                url = body.get("url")
                title = body.get("title")
                content = body.get("content")
                published_at_str = body.get("published_at")

                # Validate required fields
                if not all([source_name, url, title, content, published_at_str]):
                    log.error(f"Missing required fields in message: {body}")
                    return

                # Parse published_at
                try:
                    published_at = datetime.fromisoformat(
                        published_at_str.replace("Z", "+00:00")
                    )
                except Exception as e:
                    log.error(f"Invalid date format: {published_at_str}, error: {e}")
                    published_at = datetime.utcnow()

                # Get or create source in PostgreSQL
                source_id = self._get_or_create_source(source_name, url)

                # Generate article ID
                article_id = uuid.uuid4()

                # Check for duplicates using Faiss
                combined_text = f"{title} {content}"
                is_duplicate, existing_dedup_group = self.dedup_service.find_duplicate(
                    combined_text, article_id
                )

                if is_duplicate and existing_dedup_group:
                    dedup_group = existing_dedup_group
                    log.info(f"Article is a duplicate, assigned to group {dedup_group}")
                else:
                    # New unique article
                    dedup_group = uuid.uuid4()
                    log.info(f"Article is unique, created new group {dedup_group}")

                # Insert into ClickHouse
                success = self.clickhouse.insert_article(
                    article_id=article_id,
                    source_id=source_id,
                    url=url,
                    title=title,
                    content=content,
                    published_at=published_at,
                    dedup_group=dedup_group,
                )

                if success:
                    # Add to Faiss index
                    self.dedup_service.add_article(
                        combined_text, article_id, dedup_group
                    )
                    log.info(f"Successfully processed article {article_id}")
                else:
                    log.error(f"Failed to insert article {article_id} into ClickHouse")

            except Exception as e:
                log.error(f"Error processing message: {e}", exc_info=True)

    def _get_or_create_source(self, source_name: str, source_url: str) -> int:
        """Get or create a source in PostgreSQL"""
        with get_db_context() as db:
            # Try to find existing source
            source = db.query(Source).filter(Source.name == source_name).first()

            if source:
                return source.id

            # Create new source with default reputation
            new_source = Source(
                name=source_name,
                url=source_url,
                reputation_score=0.5,  # Default middle reputation
            )
            db.add(new_source)
            db.commit()
            db.refresh(new_source)

            log.info(f"Created new source: {source_name} (id={new_source.id})")
            return new_source.id

    async def start_consuming(self):
        """Start consuming messages from the queue"""
        await self.connect()

        channel = await self.connection.channel()
        await channel.set_qos(prefetch_count=settings.prefetch_count)

        # Declare queue
        queue = await channel.declare_queue(
            settings.news_queue_name,
            durable=True,
        )

        log.info(f"Started consuming from queue: {settings.news_queue_name}")

        # Start consuming
        await queue.consume(self.process_message)

    async def run(self):
        """Run the worker"""
        log.info("Starting News Processor Worker")
        try:
            await self.start_consuming()
            # Keep running
            await asyncio.Future()
        except KeyboardInterrupt:
            log.info("Worker interrupted by user")
        except Exception as e:
            log.error(f"Worker error: {e}", exc_info=True)
        finally:
            if self.connection:
                await self.connection.close()
            log.info("Worker stopped")


async def main():
    """Main entry point for the worker"""
    processor = NewsProcessor()
    await processor.run()


if __name__ == "__main__":
    asyncio.run(main())


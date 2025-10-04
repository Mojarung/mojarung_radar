"""News parser scheduler"""
import asyncio
from typing import List, Dict, Any, Set
from datetime import datetime
import json
from aio_pika import connect_robust, Message
from src.core.config import get_settings
from src.core.logging_config import log
from src.parsers.base import BaseParser
from src.parsers.rbc_parser import RBCParser
from src.db.clickhouse_client import get_clickhouse_client

settings = get_settings()


class ParserScheduler:
    """Manages and schedules multiple news parsers"""
    
    def __init__(self, interval_minutes: int = 5):
        self.interval_minutes = interval_minutes
        self.parsers: List[BaseParser] = []
        self.connection = None
        self.channel = None
        self.clickhouse = get_clickhouse_client()
        self._seen_urls: Set[str] = set()
        self._load_existing_urls()
    
    def _load_existing_urls(self):
        """Load existing article URLs from ClickHouse to avoid duplicates"""
        try:
            query = "SELECT DISTINCT url FROM radar_clickhouse.news_articles"
            result = self.clickhouse.client.query(query)
            self._seen_urls = set(row[0] for row in result.result_rows)
            log.info(f"Loaded {len(self._seen_urls)} existing URLs for deduplication")
        except Exception as e:
            log.warning(f"Could not load existing URLs: {e}")
            self._seen_urls = set()
    
    def register_parser(self, parser: BaseParser):
        """Register a news parser"""
        self.parsers.append(parser)
        log.info(f"Registered parser: {parser.source_name}")
    
    async def connect_rabbitmq(self):
        """Establish connection to RabbitMQ"""
        log.info(f"Connecting to RabbitMQ: {settings.rabbitmq_url}")
        self.connection = await connect_robust(settings.rabbitmq_url)
        self.channel = await self.connection.channel()
        
        # Declare queue
        await self.channel.declare_queue(
            settings.news_queue_name,
            durable=True,
        )
        log.info("Connected to RabbitMQ")
    
    async def send_to_queue(self, articles: List[Dict[str, Any]]):
        """Send articles to RabbitMQ queue"""
        if not self.channel:
            await self.connect_rabbitmq()
        
        sent_count = 0
        duplicate_count = 0
        
        for article in articles:
            url = article.get("url")
            
            # Check for duplicates by URL
            if url in self._seen_urls:
                duplicate_count += 1
                log.debug(f"Skipping duplicate URL: {url}")
                continue
            
            try:
                message_body = json.dumps(article).encode()
                message = Message(
                    body=message_body,
                    delivery_mode=2,  # Persistent
                )
                
                await self.channel.default_exchange.publish(
                    message,
                    routing_key=settings.news_queue_name,
                )
                
                # Add to seen URLs
                self._seen_urls.add(url)
                sent_count += 1
                
                log.debug(f"Sent to queue: {article.get('title', '')[:50]}...")
                
            except Exception as e:
                log.error(f"Failed to send article to queue: {e}")
        
        if sent_count > 0:
            log.info(f"Sent {sent_count} new articles to queue (skipped {duplicate_count} duplicates)")
        else:
            log.info(f"No new articles to send (skipped {duplicate_count} duplicates)")
    
    async def run_parser(self, parser: BaseParser, **kwargs):
        """Run a single parser"""
        log.info(f"Running parser: {parser.source_name}")
        
        try:
            articles = await parser.fetch_news(**kwargs)
            
            if articles:
                await self.send_to_queue(articles)
                log.info(f"Parser {parser.source_name} completed: {len(articles)} articles fetched")
            else:
                log.info(f"Parser {parser.source_name} found no new articles")
                
        except Exception as e:
            log.error(f"Parser {parser.source_name} failed: {e}", exc_info=True)
    
    async def run_all_parsers(self):
        """Run all registered parsers"""
        log.info(f"Running {len(self.parsers)} parsers...")
        
        tasks = []
        for parser in self.parsers:
            # Each parser can have its own configuration
            if isinstance(parser, RBCParser):
                task = self.run_parser(
                    parser,
                    hours_back=0,    # Today only (0 = from midnight)
                    max_pages=10,    # 10 pages
                    include_text=True,
                    classify=True    # Enable FastText classification
                )
            else:
                task = self.run_parser(parser)
            
            tasks.append(task)
        
        # Run all parsers concurrently
        await asyncio.gather(*tasks, return_exceptions=True)
        
        log.info("All parsers completed")
    
    async def start(self):
        """Start the scheduler"""
        log.info(f"Starting parser scheduler (interval: {self.interval_minutes} minutes)")
        
        # Connect to RabbitMQ
        await self.connect_rabbitmq()
        
        # Run parsers immediately on start
        await self.run_all_parsers()
        
        # Then run on schedule
        while True:
            try:
                await asyncio.sleep(self.interval_minutes * 60)
                
                log.info(f"[Scheduled run] Starting parsers at {datetime.utcnow().isoformat()}")
                await self.run_all_parsers()
                
            except asyncio.CancelledError:
                log.info("Scheduler cancelled")
                break
            except Exception as e:
                log.error(f"Scheduler error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait a bit before retrying
    
    async def stop(self):
        """Stop the scheduler and close connections"""
        log.info("Stopping scheduler...")
        
        if self.connection:
            await self.connection.close()
        
        log.info("Scheduler stopped")


async def main():
    """Main entry point for the scheduler"""
    # Get interval from environment or use default
    interval = int(settings.__dict__.get('parser_interval_minutes', 5))
    
    scheduler = ParserScheduler(interval_minutes=interval)
    
    # Register parsers
    scheduler.register_parser(RBCParser())
    
    # Add more parsers here:
    # scheduler.register_parser(BloombergParser())
    # scheduler.register_parser(ReutersParser())
    
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        log.info("Scheduler interrupted by user")
    finally:
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())


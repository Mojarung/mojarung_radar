"""Mock news parser for testing - sends sample news to RabbitMQ"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from aio_pika import connect_robust, Message
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.config import get_settings
from src.core.logging_config import log

settings = get_settings()


# Sample news articles for testing
SAMPLE_NEWS = [
    {
        "source_name": "Bloomberg",
        "url": "https://example.com/news/1",
        "title": "Tech Giant Announces Major Acquisition of AI Startup",
        "content": """A leading technology company announced today a $5 billion acquisition 
        of a prominent artificial intelligence startup. The deal represents one of the 
        largest AI acquisitions this year and is expected to significantly expand the 
        company's machine learning capabilities. Industry analysts suggest this move 
        could reshape the competitive landscape in the enterprise AI market. The 
        acquisition is subject to regulatory approval and is expected to close in Q2.""",
        "published_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
    },
    {
        "source_name": "Reuters",
        "url": "https://example.com/news/2",
        "title": "Tech Company to Acquire AI Firm for $5B",
        "content": """In a major industry move, a tech company confirmed its acquisition 
        of an AI startup for approximately $5 billion. The transaction marks a significant 
        investment in artificial intelligence capabilities. Sources close to the deal 
        indicate that the acquisition will help the company compete more effectively in 
        the growing enterprise AI market. Regulatory filings are expected next week.""",
        "published_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
    },
    {
        "source_name": "Financial Times",
        "url": "https://example.com/news/3",
        "title": "Federal Reserve Signals Potential Rate Cut in Next Quarter",
        "content": """Federal Reserve officials indicated today that a rate cut may be 
        on the table for the next quarter, citing moderating inflation and concerns 
        about economic growth. The announcement sent stock markets higher, with the 
        S&P 500 gaining 2.3% in afternoon trading. Bond yields fell sharply as investors 
        repositioned for a more dovish monetary policy stance. Economists are now 
        revising their forecasts for interest rates through 2025.""",
        "published_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
    },
    {
        "source_name": "Wall Street Journal",
        "url": "https://example.com/news/4",
        "title": "Energy Sector Faces Supply Chain Disruptions",
        "content": """Major energy companies are grappling with supply chain disruptions 
        following geopolitical tensions in key oil-producing regions. Crude oil prices 
        jumped 5% to $85 per barrel amid concerns about potential supply constraints. 
        Industry executives warn that the situation could persist for several months, 
        potentially impacting fuel prices for consumers. The International Energy Agency 
        is monitoring the situation closely.""",
        "published_at": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
    },
    {
        "source_name": "CNBC",
        "url": "https://example.com/news/5",
        "title": "Pharmaceutical Company Reports Breakthrough in Cancer Treatment",
        "content": """A leading pharmaceutical company announced promising results from 
        Phase III clinical trials of its new cancer treatment. The experimental drug 
        showed a 40% improvement in patient outcomes compared to existing therapies. 
        The company's stock surged 15% on the news, adding $20 billion to its market 
        capitalization. FDA approval is anticipated by year-end if the data holds up 
        under regulatory scrutiny. Patients groups have welcomed the development.""",
        "published_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
    },
]


async def send_news_to_queue(news_items: List[Dict[str, Any]]):
    """Send news articles to RabbitMQ queue"""
    log.info(f"Connecting to RabbitMQ: {settings.rabbitmq_url}")
    
    connection = await connect_robust(settings.rabbitmq_url)
    
    try:
        channel = await connection.channel()
        
        # Declare queue (idempotent)
        queue = await channel.declare_queue(
            settings.news_queue_name,
            durable=True,
        )
        
        log.info(f"Sending {len(news_items)} news articles to queue: {settings.news_queue_name}")
        
        for news in news_items:
            message_body = json.dumps(news).encode()
            message = Message(
                body=message_body,
                delivery_mode=2,  # Persistent
            )
            
            await channel.default_exchange.publish(
                message,
                routing_key=settings.news_queue_name,
            )
            
            log.info(f"Sent: {news['title'][:50]}...")
            
            # Small delay between messages
            await asyncio.sleep(0.5)
        
        log.info(f"Successfully sent {len(news_items)} articles to queue")
        
    finally:
        await connection.close()


async def main():
    """Main entry point"""
    log.info("Mock News Parser - Sending sample news to RabbitMQ")
    
    try:
        await send_news_to_queue(SAMPLE_NEWS)
        log.info("Done!")
    except Exception as e:
        log.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())


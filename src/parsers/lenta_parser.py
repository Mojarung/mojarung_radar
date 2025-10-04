"""Lenta.ru News Parser"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests as rq
import pandas as pd
from bs4 import BeautifulSoup as bs
from src.parsers.base import BaseParser
from src.core.logging_config import log


class LentaParser(BaseParser):
    """Parser for Lenta.ru news"""

    def __init__(self):
        super().__init__(
            source_name="Lenta.ru",
            source_url="https://lenta.ru"
        )

    def _get_url(self, param_dict: dict) -> str:
        """Build API URL for Lenta.ru search"""
        # Lenta.ru uses different structure, we'll use their main page and category pages
        base_url = "https://lenta.ru"
        if 'category' in param_dict:
            return f"{base_url}/{param_dict['category']}"
        return base_url

    def _is_relevant_url(self, url: str) -> bool:
        """Check if URL is relevant for parsing"""
        if not url:
            return False
        # Filter out non-news URLs
        irrelevant_patterns = ['/photo/', '/video/', '/live/', '/tags/']
        return not any(pattern in url for pattern in irrelevant_patterns)

    def _get_article_data(self, url: str) -> tuple:
        """Extract article overview and text from URL"""
        try:
            r = rq.get(url, timeout=10)
            soup = bs(r.text, features="lxml")

            # Lenta.ru specific selectors
            title_elem = soup.find('h1', {'class': 'topic-body__title'})
            title = title_elem.text.strip() if title_elem else "No title"

            content_elem = soup.find('div', {'class': 'topic-body__content'})
            if content_elem:
                paragraphs = content_elem.find_all('p')
                content = ' '.join(p.text.strip() for p in paragraphs)
            else:
                content = "No content available"

            return title, content
        except Exception as e:
            log.error(f"Failed to fetch article from {url}: {e}")
            return None, None

    def _get_search_results(self, category: str = 'news') -> pd.DataFrame:
        """Fetch search results from Lenta.ru category page"""
        try:
            url = self._get_url({'category': category})
            r = rq.get(url, timeout=10)
            soup = bs(r.text, features="lxml")

            articles = []
            # Lenta.ru specific article selectors
            news_items = soup.find_all('div', {'class': 'news-item'})

            for item in news_items[:20]:  # Limit to 20 articles
                link_elem = item.find('a', {'class': 'news-item__title'})
                if link_elem:
                    article_url = f"https://lenta.ru{link_elem['href']}"
                    title = link_elem.text.strip()

                    time_elem = item.find('time', {'class': 'news-item__time'})
                    published_at = datetime.utcnow()
                    if time_elem:
                        try:
                            # Parse relative time if needed
                            published_at = datetime.utcnow() - timedelta(hours=1)
                        except:
                            pass

                    articles.append({
                        'url': article_url,
                        'title': title,
                        'published_at': published_at,
                        'category': category
                    })

            return pd.DataFrame(articles)
        except Exception as e:
            log.error(f"Failed to fetch search results: {e}")
            return pd.DataFrame()

    async def fetch_news(
        self,
        hours_back: int = 24,
        max_pages: int = 5,
        include_text: bool = True,
        classify: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent news from Lenta.ru

        Args:
            hours_back: Hours back to fetch (0 = today only)
            max_pages: Maximum pages to fetch
            include_text: Whether to fetch full article text
            classify: Whether to use classification
        """
        now = datetime.now()

        if hours_back == 0:
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            log.info(f"Fetching Lenta.ru news for today: {date_from.strftime('%d.%m.%Y')}")
        else:
            date_from = now - timedelta(hours=hours_back)
            log.info(f"Fetching Lenta.ru news (hours_back={hours_back})")

        # Categories to fetch from
        categories = ['politics', 'economics', 'society', 'culture', 'sport']

        all_articles = []
        loop = asyncio.get_event_loop()

        for category in categories:
            try:
                log.info(f"Fetching category: {category}")

                # Fetch articles from category
                df = await loop.run_in_executor(
                    None,
                    self._get_search_results,
                    category
                )

                if df.empty:
                    log.info(f"No articles found in category {category}")
                    continue

                log.info(f"Got {len(df)} articles from category {category}")

                # Process each article
                for _, row in df.iterrows():
                    try:
                        url = row.get('url', '')
                        title = row.get('title', 'No title')
                        published_at = row.get('published_at', datetime.utcnow())

                        # Filter by date if needed
                        if hours_back > 0 and published_at < date_from:
                            continue

                        # Get article content if requested
                        content = ""
                        if include_text:
                            _, content = await loop.run_in_executor(
                                None, self._get_article_data, url
                            )

                        if not self._is_relevant_url(url):
                            log.debug(f"Skipping non-relevant URL: {url}")
                            continue

                        formatted_article = self.format_article(
                            url=url,
                            title=title,
                            content=content,
                            published_at=published_at
                        )

                        all_articles.append(formatted_article)

                    except Exception as e:
                        log.error(f"Failed to process article {url}: {e}")
                        continue

                log.info(f"Category {category} complete: {len(all_articles)} articles added")

            except Exception as e:
                log.error(f"Failed to fetch category {category}: {e}")
                continue

        self.update_last_fetch_time()
        log.info(f"Total fetched: {len(all_articles)} articles from Lenta.ru")

        return all_articles

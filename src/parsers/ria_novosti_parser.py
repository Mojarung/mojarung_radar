"""RIA Novosti News Parser"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests as rq
import pandas as pd
from bs4 import BeautifulSoup as bs
from src.parsers.base import BaseParser
from src.core.logging_config import log


class RiaNovostiParser(BaseParser):
    """Parser for RIA Novosti news"""

    def __init__(self):
        super().__init__(
            source_name="РИА Новости",
            source_url="https://ria.ru"
        )

    def _get_url(self, param_dict: dict) -> str:
        """Build API URL for RIA Novosti search"""
        base_url = "https://ria.ru/services/search/getmore/"
        url = base_url + '?' + \
            f'query=&' + \
            f'date_from={param_dict["date_from"]}&' + \
            f'date_to={param_dict["date_to"]}&' + \
            f'offset={param_dict["offset"]}'
        return url

    def _is_relevant_url(self, url: str) -> bool:
        """Check if URL is relevant for parsing"""
        if not url:
            return False
        # Filter out non-news URLs
        irrelevant_patterns = ['/photo/', '/video/', '/infografika/']
        return not any(pattern in url for pattern in irrelevant_patterns)

    def _get_article_data(self, url: str) -> tuple:
        """Extract article overview and text from URL"""
        try:
            r = rq.get(url, timeout=10)
            soup = bs(r.text, features="lxml")

            # RIA Novosti specific selectors
            title_elem = soup.find('h1', {'class': 'article__title'})
            title = title_elem.text.strip() if title_elem else "No title"

            content_elem = soup.find('div', {'class': 'article__body'})
            if content_elem:
                paragraphs = content_elem.find_all('p')
                content = ' '.join(p.text.strip() for p in paragraphs)
            else:
                content = "No content available"

            return title, content
        except Exception as e:
            log.error(f"Failed to fetch article from {url}: {e}")
            return None, None

    def _get_search_results(self, date_from: str, date_to: str, offset: int = 0) -> pd.DataFrame:
        """Fetch search results from RIA Novosti API"""
        try:
            url = self._get_url({
                'date_from': date_from,
                'date_to': date_to,
                'offset': str(offset)
            })

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            r = rq.get(url, headers=headers, timeout=10)
            data = r.json()

            articles = []
            if 'items' in data:
                for item in data['items'][:20]:  # Limit to 20 articles
                    article_url = item.get('url', '')
                    title = item.get('title', 'No title')

                    # Parse publication date
                    published_at = datetime.utcnow()
                    if 'date' in item:
                        try:
                            published_at = datetime.fromtimestamp(item['date'])
                        except:
                            pass

                    articles.append({
                        'url': article_url,
                        'title': title,
                        'published_at': published_at,
                        'category': item.get('category', 'general')
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
        Fetch recent news from RIA Novosti

        Args:
            hours_back: Hours back to fetch (0 = today only)
            max_pages: Maximum pages to fetch
            include_text: Whether to fetch full article text
            classify: Whether to use classification
        """
        now = datetime.now()

        if hours_back == 0:
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            log.info(f"Fetching RIA Novosti news for today: {date_from.strftime('%d.%m.%Y')}")
        else:
            date_from = now - timedelta(hours=hours_back)
            log.info(f"Fetching RIA Novosti news (hours_back={hours_back})")

        date_from_str = date_from.strftime("%Y-%m-%d")
        date_to_str = now.strftime("%Y-%m-%d")

        all_articles = []
        loop = asyncio.get_event_loop()

        try:
            log.info("Fetching articles from RIA Novosti API")

            # Fetch articles from API
            df = await loop.run_in_executor(
                None,
                self._get_search_results,
                date_from_str,
                date_to_str,
                0
            )

            if df.empty:
                log.info("No articles found in RIA Novosti")
            else:
                log.info(f"Got {len(df)} articles from RIA Novosti")

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

        except Exception as e:
            log.error(f"Failed to fetch from RIA Novosti: {e}")

        self.update_last_fetch_time()
        log.info(f"Total fetched: {len(all_articles)} articles from RIA Novosti")

        return all_articles

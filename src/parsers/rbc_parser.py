"""RBC News Parser"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests as rq
import pandas as pd
from bs4 import BeautifulSoup as bs
from src.parsers.base import BaseParser
from src.parsers.fasttext_classifier import get_fasttext_classifier
from src.core.logging_config import log


class RBCParser(BaseParser):
    """Parser for RBC (РБК) news"""
    
    def __init__(self):
        super().__init__(
            source_name="РБК",
            source_url="https://www.rbc.ru"
        )
    
    # Relevant URL categories for financial news
    RELEVANT_CATEGORIES = ['business', 'technology_and_media', 'politics', 'economics', 'finance']
    
    def _get_url(self, param_dict: dict) -> str:
        """Build API URL for RBC search"""
        url = 'https://www.rbc.ru/search/ajax/?' + \
            f'dateFrom={param_dict["dateFrom"]}&' + \
            f'dateTo={param_dict["dateTo"]}&' + \
            f'page={param_dict["page"]}'
        return url
    
    def _is_relevant_url(self, url: str) -> bool:
        """Check if URL belongs to relevant categories"""
        if not url:
            return False
        # Check if any relevant category is in the URL
        return any(category in url for category in self.RELEVANT_CATEGORIES)
    
    def _get_article_data(self, url: str) -> tuple:
        """Extract article overview and text from URL"""
        try:
            r = rq.get(url, timeout=10)
            soup = bs(r.text, features="lxml")
            
            div_overview = soup.find('div', {'class': 'article__text__overview'})
            overview = div_overview.text.replace('<br />', '\n').strip() if div_overview else None
            
            p_text = soup.find_all('p')
            text = ' '.join(p.text.replace('<br />', '\n').strip() for p in p_text) if p_text else None
            
            return overview, text
        except Exception as e:
            log.error(f"Failed to fetch article from {url}: {e}")
            return None, None
    
    def _get_search_table(
        self,
        param_dict: dict,
        include_text: bool = True
    ) -> pd.DataFrame:
        """Fetch search results from RBC API"""
        try:
            url = self._get_url(param_dict)
            r = rq.get(url, timeout=10)
            search_table = pd.DataFrame(r.json().get('items', []))
            
            if search_table.empty:
                return search_table
            
            if include_text:
                def get_text(x):
                    overview, text = self._get_article_data(x['fronturl'])
                    return pd.Series([overview, text])
                
                search_table[['overview', 'text']] = search_table.apply(
                    get_text, axis=1
                )
            
            if 'publish_date_t' in search_table.columns:
                search_table = search_table.sort_values(
                    'publish_date_t', ignore_index=True
                )
            
            return search_table
        except Exception as e:
            log.error(f"Failed to fetch search table: {e}")
            return pd.DataFrame()
    
    async def fetch_news(
        self,
        hours_back: int = 168,
        max_pages: int = 50,
        include_text: bool = True,
        classify: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent news from RBC (simplified version).
        
        Args:
            hours_back: How many hours back to fetch (0 = today only)
            max_pages: Maximum pages to fetch
            include_text: Whether to fetch full article text
            classify: Whether to use FastText classification
        """
        now = datetime.now()
        
        # If hours_back is 0, parse only today
        if hours_back == 0:
            date_from = now.replace(hour=0, minute=0, second=0, microsecond=0)
            log.info(f"Fetching RBC news for today: {date_from.strftime('%d.%m.%Y')}")
        else:
            date_from = now - timedelta(hours=hours_back)
            log.info(f"Fetching RBC news (hours_back={hours_back})")
        
        param_dict = {
            'dateFrom': date_from.strftime("%d.%m.%Y"),
            'dateTo': now.strftime("%d.%m.%Y"),
            'page': '1',
        }
        
        all_articles = []
        classifier = get_fasttext_classifier() if classify else None
        
        # Run blocking I/O in executor
        loop = asyncio.get_event_loop()
        
        for page in range(1, max_pages + 1):
            param_dict['page'] = str(page)
            
            try:
                log.info(f"Fetching page {page}...")
                
                # Fetch page WITH full text for better classification
                df = await loop.run_in_executor(
                    None,
                    self._get_search_table,
                    param_dict,
                    True  # Fetch full text for classification!
                )
                
                if df.empty:
                    log.info(f"No more articles found on page {page}")
                    break
                
                log.info(f"Got {len(df)} articles from page {page}")
                
                # Process each article
                page_articles = []
                for _, row in df.iterrows():
                    try:
                        url = row.get('fronturl', '')
                        title = row.get('title', 'No title')
                        
                        # Filter by URL category
                        if not self._is_relevant_url(url):
                            log.debug(f"Skipping non-relevant URL: {url}")
                            continue
                        
                        # Parse publish date
                        if 'publish_date_t' in row:
                            published_at = datetime.fromtimestamp(row['publish_date_t'])
                        else:
                            published_at = datetime.utcnow()
                        
                        # Get FULL description for classification
                        overview = row.get('overview', '') or ''
                        text = row.get('text', '') or ''
                        
                        # Combine overview and text (limit to first 1000 chars for FastText)
                        full_content = f"{overview}\n\n{text}".strip()
                        if len(full_content) > 1000:
                            full_content = full_content[:1000]
                        
                        article_preview = {
                            'url': url,
                            'title': title,
                            'overview': full_content,  # Full description!
                            'published_at': published_at,
                            'full_text': f"{overview}\n\n{text}".strip(),  # Save full for later
                        }
                        
                        log.debug(
                            f"Article: title='{title[:50]}...', "
                            f"content_length={len(full_content)}"
                        )
                        
                        page_articles.append(article_preview)
                        
                    except Exception as e:
                        log.error(f"Failed to process article: {e}")
                        continue
                
                log.info(f"Filtered to {len(page_articles)} articles with relevant URLs")
                
                # Classify articles (if enabled) - NOT await, it's synchronous!
                if classify and classifier and page_articles:
                    page_articles = classifier.batch_classify(page_articles)
                    log.info(f"After FastText classification: {len(page_articles)} relevant articles")
                
                # Use already loaded full text for relevant articles
                for article in page_articles:
                    try:
                        # We already have the full text from earlier
                        content = article.get('full_text', article.get('overview', ''))
                        
                        if not content:
                            log.warning(f"Empty content for article: {article['url']}")
                            continue
                        
                        formatted_article = self.format_article(
                            url=article['url'],
                            title=article['title'],
                            content=content,
                            published_at=article['published_at']
                        )
                        
                        # Add classification info if available
                        if 'classification' in article:
                            formatted_article['classification'] = article['classification']
                        
                        all_articles.append(formatted_article)
                        
                    except Exception as e:
                        log.error(f"Failed to process article {article['url']}: {e}")
                        continue
                
                log.info(f"Page {page} complete: {len(page_articles)} articles added")
                
            except Exception as e:
                log.error(f"Failed to fetch page {page}: {e}")
                break
        
        self.update_last_fetch_time()
        log.info(f"Total fetched: {len(all_articles)} relevant articles from RBC")
        
        return all_articles


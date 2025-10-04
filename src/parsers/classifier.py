"""News relevance classifier using LLM"""
from typing import Dict, Any, Optional
from src.services.llm_client import get_llm_client
from src.core.logging_config import log


class NewsClassifier:
    """Classifies news articles for financial relevance"""
    
    def __init__(self):
        self.llm = get_llm_client()
        
        # Financial keywords for quick pre-filtering
        self.financial_keywords = {
            # Русские
            'экономика', 'финансы', 'банк', 'кредит', 'инвестиц', 'акци',
            'биржа', 'валюта', 'рубль', 'доллар', 'евро', 'цб', 'центробанк',
            'нефть', 'газ', 'золото', 'металл', 'сырье', 'экспорт', 'импорт',
            'инфляция', 'ввп', 'бюджет', 'налог', 'тариф', 'пошлин',
            'ценные бумаги', 'облигаци', 'фонд', 'дивиденд', 'прибыл',
            'убыток', 'выручка', 'капитализаци', 'ipo', 'сделка', 'поглощение',
            'слияние', 'санкци', 'торговля', 'бизнес', 'компания', 'корпораци',
            'производство', 'промышленность', 'отрасл', 'сектор',
            'криптовалюта', 'биткоин', 'блокчейн', 'майнинг', 'токен',
            'рынок', 'цена', 'стоимость', 'котировк', 'индекс',
            'рост', 'падение', 'динамика', 'тренд', 'прогноз',
            'недвижимость', 'ипотека', 'строительство', 'девелопер',
            
            # Английские (для интернациональных новостей)
            'economy', 'finance', 'bank', 'investment', 'stock', 'market',
            'currency', 'dollar', 'euro', 'bitcoin', 'crypto', 'trading',
            'merger', 'acquisition', 'ipo', 'fund', 'bond', 'dividend',
        }
    
    def quick_filter(self, title: str, content_preview: str = "") -> bool:
        """
        Quick keyword-based pre-filter.
        Returns True if article might be financially relevant.
        """
        text = (title + " " + content_preview).lower()
        
        # Check for financial keywords
        for keyword in self.financial_keywords:
            if keyword in text:
                return True
        
        return False
    
    async def classify_article(
        self,
        title: str,
        content_preview: str = "",
        full_content: str = ""
    ) -> Dict[str, Any]:
        """
        Classify article using LLM.
        
        Returns:
            {
                'is_relevant': bool,
                'confidence': float (0-1),
                'categories': List[str],
                'reason': str
            }
        """
        # Use preview if available, otherwise full content
        text_to_analyze = content_preview if content_preview else full_content[:500]
        
        prompt = f"""Ты эксперт-аналитик финансовых новостей. Определи, относится ли эта новость к финансам, экономике, бизнесу или инвестициям.

Заголовок: {title}

Текст: {text_to_analyze}

Ответь в формате JSON:
{{
  "is_relevant": true/false,
  "confidence": 0.0-1.0,
  "categories": ["категория1", "категория2"],
  "reason": "краткое объяснение"
}}

Категории могут быть: "макроэкономика", "банки", "фондовый_рынок", "криптовалюты", "недвижимость", "корпоративные_новости", "сырьевые_рынки", "валютный_рынок", "регулирование", "инвестиции", "другое"

Считай РЕЛЕВАНТНЫМИ новости о:
- Экономических показателях (ВВП, инфляция, и т.д.)
- Финансовых рынках (акции, облигации, валюты)
- Компаниях и бизнесе (сделки, результаты, стратегии)
- Банках и финансовых институтах
- Криптовалютах и блокчейне
- Сырьевых рынках (нефть, газ, металлы)
- Недвижимости и строительстве
- Торговле и инвестициях
- Экономической политике и регулировании

Считай НЕ РЕЛЕВАНТНЫМИ новости о:
- Спорте (если не о финансах спортивных клубов)
- Культуре и развлечениях
- Общественных событиях без экономического контекста
- Погоде
- Происшествиях (если не влияют на экономику)
- Личной жизни знаменитостей"""

        try:
            result = self.llm.generate_json(prompt, temperature=0.3, max_tokens=500)
            
            # Validate and normalize result
            classification = {
                'is_relevant': result.get('is_relevant', False),
                'confidence': min(max(result.get('confidence', 0.5), 0.0), 1.0),
                'categories': result.get('categories', []),
                'reason': result.get('reason', '')
            }
            
            log.debug(
                f"Classified: '{title[:50]}...' -> "
                f"relevant={classification['is_relevant']}, "
                f"confidence={classification['confidence']:.2f}"
            )
            
            return classification
            
        except Exception as e:
            log.error(f"Classification failed: {e}")
            # Fallback: assume relevant if quick filter passed
            return {
                'is_relevant': True,
                'confidence': 0.5,
                'categories': ['unknown'],
                'reason': 'Classification failed, using fallback'
            }
    
    async def batch_classify(
        self,
        articles: list,
        use_quick_filter: bool = True
    ) -> list:
        """
        Classify multiple articles efficiently.
        
        Args:
            articles: List of dicts with 'title' and optionally 'content_preview'
            use_quick_filter: If True, skip LLM for obviously irrelevant articles
        
        Returns:
            List of articles with added 'classification' field
        """
        classified = []
        
        for article in articles:
            title = article.get('title', '')
            content_preview = article.get('overview', '') or article.get('content_preview', '')
            
            # Quick pre-filter
            if use_quick_filter and not self.quick_filter(title, content_preview):
                # Skip LLM classification for obviously irrelevant
                article['classification'] = {
                    'is_relevant': False,
                    'confidence': 1.0,
                    'categories': [],
                    'reason': 'Filtered by keywords'
                }
                log.debug(f"Quick-filtered out: {title[:50]}...")
                continue
            
            # LLM classification
            classification = await self.classify_article(
                title=title,
                content_preview=content_preview
            )
            
            article['classification'] = classification
            
            # Only keep relevant articles
            if classification['is_relevant']:
                classified.append(article)
        
        log.info(f"Classified {len(articles)} articles -> {len(classified)} relevant")
        
        return classified


# Singleton instance
_classifier: Optional[NewsClassifier] = None


def get_classifier() -> NewsClassifier:
    """Get singleton classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = NewsClassifier()
    return _classifier


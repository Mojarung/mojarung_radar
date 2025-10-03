# Руководство по расширению RADAR

## Добавление нового источника новостей

### 1. Создание коллектора

Создайте новый файл `app/services/collectors/your_source.py`:

```python
from app.models import News, Source
from app.core.logging import get_logger

logger = get_logger(__name__)

class YourSourceCollector:
    async def fetch_news(self) -> list[dict]:
        """Получение новостей из источника."""
        # Реализуйте логику получения новостей
        pass
```

### 2. Регистрация источника

Добавьте источник в БД через API или миграцию.

## Замена LLM провайдера

### Пример: Использование Anthropic напрямую

Создайте `app/llm/anthropic_provider.py`:

```python
from anthropic import AsyncAnthropic
from app.llm.base import BaseLLMProvider
from app.core.config import settings

class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 2000)
        )
        return response.content[0].text
```

Затем замените в узлах графа:

```python
# Было:
from app.llm import OpenRouterProvider
llm = OpenRouterProvider()

# Стало:
from app.llm.anthropic_provider import AnthropicProvider
llm = AnthropicProvider()
```

## Добавление нового узла в граф

### 1. Создание узла

`app/graph/nodes/sentiment.py`:

```python
from app.graph.state import RadarState
from app.llm import OpenRouterProvider

async def sentiment_analysis_node(state: RadarState) -> RadarState:
    """Анализ тональности новости."""
    llm = OpenRouterProvider()
    
    prompt = f"Оцени тональность новости (positive/negative/neutral): {state['news_content']}"
    sentiment = await llm.generate(prompt, max_tokens=50)
    
    state["sentiment"] = sentiment.strip().lower()
    return state
```

### 2. Обновление состояния

В `app/graph/state.py` добавьте поле:

```python
class RadarState(TypedDict):
    ...
    sentiment: Optional[str]
```

### 3. Интеграция в граф

В `app/graph/graph.py`:

```python
from app.graph.nodes.sentiment import sentiment_analysis_node

def create_radar_graph():
    workflow = StateGraph(RadarState)
    ...
    workflow.add_node("sentiment", sentiment_analysis_node)
    
    # Добавьте ребро после enrichment
    workflow.add_edge("enrichment", "sentiment")
    workflow.add_edge("sentiment", "scoring")
```

## Добавление векторного поиска

### 1. Установка pgvector

Добавьте в `pyproject.toml`:

```toml
dependencies = [
    ...
    "pgvector>=0.3.0",
]
```

### 2. Создание миграции

```bash
alembic revision -m "add pgvector extension"
```

В миграции:

```python
def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column('stories', 
        sa.Column('embedding', Vector(1536))
    )
    op.create_index(
        'ix_stories_embedding',
        'stories',
        ['embedding'],
        postgresql_using='ivfflat',
        postgresql_with={'lists': 100},
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )
```

### 3. Обновление сервиса эмбеддингов

В `app/services/embeddings.py`:

```python
from openai import AsyncOpenAI

class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI()
    
    async def generate_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    async def find_similar(self, embedding: list[float], limit: int = 5):
        # SQL запрос с vector similarity search
        query = """
        SELECT id, headline, embedding <=> :embedding as distance
        FROM stories
        ORDER BY distance
        LIMIT :limit
        """
        # Выполните через SQLAlchemy
```

## Добавление кеширования

### 1. Декоратор для кеширования

`app/core/cache.py`:

```python
import functools
import json
from app.db.redis import get_redis

def cache_result(ttl: int = 3600):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            redis = await get_redis()
            cache_key = f"{func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"
            
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            await redis.setex(cache_key, ttl, json.dumps(result))
            return result
        
        return wrapper
    return decorator
```

### 2. Использование

```python
from app.core.cache import cache_result

@cache_result(ttl=3600)
async def get_top_stories(hours: int, limit: int):
    # Ваша логика
    pass
```

## Добавление асинхронных задач

### 1. Установка Celery

```toml
dependencies = [
    ...
    "celery[redis]>=5.4.0",
]
```

### 2. Создание задач

`app/tasks/news_processing.py`:

```python
from celery import Celery
from app.core.config import settings

celery_app = Celery('radar', broker=settings.redis_url)

@celery_app.task
def process_news_async(news_id: str):
    # Асинхронная обработка новости
    pass
```

## Мониторинг и метрики

### Добавление Prometheus метрик

```toml
dependencies = [
    ...
    "prometheus-client>=0.20.0",
]
```

В `app/main.py`:

```python
from prometheus_client import Counter, Histogram, make_asgi_app

news_processed = Counter('news_processed_total', 'Total news processed')
processing_time = Histogram('news_processing_seconds', 'Time to process news')

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

## Тестирование

### Unit тесты для узлов графа

`tests/test_nodes.py`:

```python
import pytest
from app.graph.nodes.scoring import scoring_node
from app.graph.state import RadarState

@pytest.mark.asyncio
async def test_scoring_node():
    state: RadarState = {
        "news_content": "слияние компаний",
        "entities": ["Company A", "Company B"],
        "related_articles": [],
        "source_reputation": 0.8,
        ...
    }
    
    result = await scoring_node(state)
    
    assert result["hotness_score"] > 0
    assert result["hotness_score"] <= 1.0
```

## Интеграция с внешними API

### Пример: News API

`app/services/collectors/newsapi.py`:

```python
import httpx
from app.core.config import settings

class NewsAPICollector:
    def __init__(self):
        self.api_key = settings.newsapi_key
        self.base_url = "https://newsapi.org/v2"
    
    async def fetch_latest(self, query: str = "finance"):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/everything",
                params={
                    "q": query,
                    "apiKey": self.api_key,
                    "language": "ru",
                    "sortBy": "publishedAt"
                }
            )
            return response.json()["articles"]
```


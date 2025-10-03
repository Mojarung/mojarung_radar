# Руководство по реализации RADAR

## Обзор реализации

Проект RADAR реализован согласно следующим принципам:
- Clean Architecture (слои: domain, application, infrastructure, presentation)
- Dependency Injection с использованием Dishka
- ReAct архитектура через LangGraph
- Асинхронная обработка (async/await)
- Структурированное логирование

## Ключевые компоненты

### 1. Core (src/core/)

**config.py** - Конфигурация приложения через Pydantic Settings
- Все настройки загружаются из переменных окружения
- Использует lru_cache для синглтона
- Типобезопасность через Pydantic

**logging.py** - Настройка логирования через structlog
- JSON формат для production
- Human-readable для development
- Контекстные логи

**exceptions.py** - Кастомные исключения
- Иерархия исключений от базового RadarException
- Специфичные исключения для каждого слоя

### 2. Domain (src/domain/)

**entities.py** - Доменные сущности
- News - новость
- Story - сюжет (кластер новостей)
- Entity - извлеченная сущность (компания, тикер)
- TimelineEvent - событие на временной шкале

**value_objects.py** - Value Objects
- HotnessScore - оценка горячести с компонентами
- SourceReputation - репутация источника

**events.py** - Доменные события
- NewsIngested, NewsDeduped, NewsEnriched, StoryScored, DraftGenerated
- Для event sourcing (будущее расширение)

### 3. Infrastructure (src/infrastructure/)

**database/** - Работа с PostgreSQL
- models.py - SQLAlchemy модели
- session.py - управление сессиями
- repositories.py - репозитории для работы с сущностями

**redis/** - Работа с Redis
- client.py - клиент Redis с поддержкой embeddings
- cache.py - сервис кеширования

**llm/** - Интеграция с LLM
- base.py - базовый интерфейс
- openrouter.py - реализация для OpenRouter
- Легко заменяем на другой провайдер

**sources/** - Источники новостей
- news_scrapers.py - заглушки для скрейперов
- Требуется реализация конкретных источников

### 4. Services (src/services/)

**embeddings_service.py** - Генерация векторных представлений
- Использует sentence-transformers
- Кеширование в Redis
- Косинусное сходство для дедупликации

**scoring_service.py** - Расчет hotness score
- Взвешенная сумма 5 компонентов
- Настраиваемые веса

**news_service.py** - Бизнес-логика работы с новостями
- CRUD операции
- Оркестрация между репозиториями

### 5. Agents (src/agents/)

**state.py** - Определение состояния графа
- TypedDict для типобезопасности
- Все поля с описанием

**graph.py** - Построение LangGraph
- Условные переходы (conditional edges)
- Логика маршрутизации

**nodes/** - Узлы графа
- deduplication.py - дедупликация через embeddings
- enrichment.py - извлечение сущностей (заглушка для NER)
- scoring.py - расчет hotness
- context_rag.py - RAG для контекста
- draft_generator.py - генерация черновиков

### 6. API (src/api/)

**routes/health.py** - Health check эндпоинты
**routes/radar.py** - Основные эндпоинты RADAR
- POST /radar/process-news - обработка новости
- GET /radar/top-stories - топ истории

### 7. DI Container (src/di.py)

Провайдеры Dishka:
- ConfigProvider - настройки (APP scope)
- DatabaseProvider - БД и репозитории (REQUEST scope)
- RedisProvider - Redis клиент (APP scope)
- LLMProvider - LLM клиент (APP scope)
- ServicesProvider - бизнес-сервисы (REQUEST scope)
- AgentsProvider - граф LangGraph (REQUEST scope)

## Граф обработки (LangGraph)

```
START
  ↓
Deduplication (проверка на дубликаты через embeddings)
  ↓
Enrichment (извлечение сущностей - заглушка)
  ↓
Scoring (расчет hotness_score)
  ↓
[is_hot >= threshold?]
  ↓ YES              ↓ NO
Context RAG         END
  ↓
Draft Generator
  ↓
END
```

## Точки расширения

### 1. Добавление нового источника новостей

1. Создать класс в `src/infrastructure/sources/`
2. Наследоваться от `NewsSource`
3. Реализовать метод `fetch_news()`
4. Добавить в список источников в настройках

### 2. Замена LLM провайдера

Пример замены OpenRouter на Anthropic напрямую:

```python
# src/infrastructure/llm/anthropic.py
import anthropic
from src.infrastructure.llm.base import BaseLLM

class AnthropicLLM(BaseLLM):
    def __init__(self, settings: Settings):
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key
        )
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.content[0].text
```

Обновить в `src/di.py`:
```python
class LLMProvider(Provider):
    @provide(scope=Scope.APP)
    async def get_llm(self, settings: Settings) -> AsyncIterator[BaseLLM]:
        llm = AnthropicLLM(settings)  # Изменить здесь
        yield llm
        # await llm.close() если нужно
```

### 3. Добавление NER для извлечения сущностей

В `src/agents/nodes/enrichment.py` интегрировать NER модель:

```python
from transformers import pipeline

class EnrichmentNode:
    def __init__(self):
        self.ner = pipeline("ner", model="dslim/bert-base-NER")
    
    async def __call__(self, state: RadarState) -> RadarState:
        text = state["initial_news"]["content"]
        entities = self.ner(text)
        # Обработка и структурирование
        ...
```

### 4. Добавление нового узла в граф

1. Создать класс узла в `src/agents/nodes/`
2. Добавить провайдер в `AgentsProvider`
3. Обновить `create_radar_graph()` в `src/agents/graph.py`

## База данных

### Миграции

Создание:
```bash
alembic revision --autogenerate -m "description"
```

Применение:
```bash
alembic upgrade head
```

### Основные таблицы

- **news** - входящие новости
- **stories** - сюжеты (кластеры)
- **entities** - компании, тикеры
- **story_entities** - связь M2M
- **timelines** - временные метки
- **source_reputations** - репутация источников

## Тестирование

### Unit тесты
Изолированное тестирование сервисов:
```python
# tests/unit/test_scoring_service.py
```

### Integration тесты
Тестирование API:
```python
# tests/integration/test_api.py
```

## Логирование

Структурированные логи с контекстом:
```python
from src.core.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "news_processed",
    news_id=str(news_id),
    hotness=hotness_score,
    source=source_name
)
```

## Мониторинг

Рекомендуемые метрики для добавления:
- Время обработки новости (p50, p95, p99)
- Количество обработанных новостей/мин
- Распределение hotness_score
- Cache hit rate (Redis)
- Latency LLM запросов
- Ошибки по типам

## Производительность

### Оптимизации

1. **Кеширование embeddings** - уже реализовано в Redis
2. **Batch обработка** - можно добавить пакетную обработку новостей
3. **Connection pooling** - настроено для PostgreSQL
4. **Async/await** - используется везде

### Узкие места

1. **LLM запросы** - самая медленная часть
   - Решение: кеширование, параллелизация
2. **Генерация embeddings** - CPU-intensive
   - Решение: кеширование, использование GPU
3. **Database writes** - при большом потоке
   - Решение: batch inserts, партиционирование

## Безопасность

1. **API Keys** - через переменные окружения
2. **SQL Injection** - защита через SQLAlchemy ORM
3. **Input validation** - Pydantic models
4. **Rate limiting** - нужно добавить middleware

## Масштабирование

### Горизонтальное

1. Запустить несколько инстансов app за load balancer
2. Shared state через PostgreSQL и Redis
3. Без состояния в приложении

### Вертикальное

1. Увеличить pool_size PostgreSQL
2. Добавить Redis Cluster
3. Использовать GPU для embeddings

## Что нужно доделать

### Критичное

1. **Реализовать скрейперы новостей** - `src/infrastructure/sources/`
2. **Добавить NER модель** - в `EnrichmentNode`
3. **Настроить реальный источник репутации** - `SourceReputationModel`

### Желательно

1. Добавить Rate Limiting middleware
2. Реализовать Batch processing для новостей
3. Добавить WebSocket для real-time updates
4. Метрики и трейсинг (Prometheus, Jaeger)
5. CI/CD пайплайн
6. Helm charts для Kubernetes

### Nice to have

1. Admin панель
2. Графики и дашборды
3. A/B тестирование различных промптов
4. Fine-tuning embedding модели
5. Multi-language support


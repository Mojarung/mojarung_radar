# Архитектура проекта RADAR

## Обзор

RADAR - система для выявления и оценки горячих новостей в финансовой сфере, построенная на основе ReAct-архитектуры с использованием LangGraph.

## Технологический стек

- **FastAPI** - веб-фреймворк для API
- **LangGraph** - граф агентов для обработки новостей
- **PostgreSQL** - основная БД для хранения новостей, сюжетов, сущностей
- **Redis** - кеширование и хранение векторов для дедупликации
- **Alembic** - миграции БД
- **Dishka** - Dependency Injection контейнер
- **OpenRouter** - провайдер LLM (легко заменяем)

## Структура проекта

```
mojarung_radar/
├── src/
│   ├── api/                    # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── routes/             # Группы роутов
│   │   │   ├── __init__.py
│   │   │   ├── health.py       # Health check
│   │   │   └── radar.py        # Основные эндпоинты RADAR
│   │   └── dependencies.py     # API-специфичные зависимости
│   │
│   ├── core/                   # Ядро приложения
│   │   ├── __init__.py
│   │   ├── config.py           # Настройки (Pydantic Settings)
│   │   ├── logging.py          # Конфигурация логирования
│   │   └── exceptions.py       # Кастомные исключения
│   │
│   ├── domain/                 # Доменная модель
│   │   ├── __init__.py
│   │   ├── entities.py         # Доменные сущности
│   │   ├── value_objects.py    # Value Objects
│   │   └── events.py           # Доменные события
│   │
│   ├── infrastructure/         # Внешние интеграции
│   │   ├── __init__.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── models.py       # SQLAlchemy модели
│   │   │   ├── repositories.py # Репозитории
│   │   │   └── session.py      # Управление сессиями
│   │   ├── redis/
│   │   │   ├── __init__.py
│   │   │   ├── client.py       # Redis клиент
│   │   │   └── cache.py        # Кеширование
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Базовый интерфейс LLM
│   │   │   └── openrouter.py   # Имплементация OpenRouter
│   │   └── sources/
│   │       ├── __init__.py
│   │       └── news_scrapers.py # Сборщики новостей
│   │
│   ├── agents/                 # LangGraph агенты
│   │   ├── __init__.py
│   │   ├── state.py            # Определение State графа
│   │   ├── graph.py            # Построение графа
│   │   └── nodes/              # Узлы графа
│   │       ├── __init__.py
│   │       ├── ingest.py       # Сборщик новостей
│   │       ├── deduplication.py # Дедупликация
│   │       ├── enrichment.py   # Обогащение (NER)
│   │       ├── scoring.py      # Оценка горячести
│   │       ├── context_rag.py  # RAG для контекста
│   │       └── draft_generator.py # Генерация черновиков
│   │
│   ├── services/               # Бизнес-логика
│   │   ├── __init__.py
│   │   ├── news_service.py     # Работа с новостями
│   │   ├── scoring_service.py  # Расчет hotness
│   │   └── embeddings_service.py # Векторные представления
│   │
│   ├── di.py                   # Dishka DI контейнер
│   └── main.py                 # Точка входа приложения
│
├── alembic/                    # Миграции БД
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/                      # Тесты
│   ├── __init__.py
│   ├── unit/
│   └── integration/
│
├── docker/                     # Docker конфиги
│   ├── Dockerfile
│   └── nginx.conf (optional)
│
├── .env.example                # Пример переменных окружения
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
└── README.md
```

## Граф LangGraph

Система построена как направленный граф с узлами-обработчиками:

```
START -> Ingest -> Deduplication -> {new_cluster, existing_cluster}
                                          ↓                ↓
                                    Enrichment  ←─────────┘
                                          ↓
                                       Scoring
                                          ↓
                                  {hot, not_hot}
                                          ↓
                                    Context_RAG (если hot)
                                          ↓
                                   Draft_Generator
                                          ↓
                                        END
```

### State графа

Центральный объект, передаваемый между узлами:

```python
{
    "initial_news": dict,           # Исходная новость
    "cluster_id": str | None,       # ID сюжета
    "related_articles": list[dict], # Связанные статьи
    "entities": dict,               # Извлеченные сущности
    "timeline": list[dict],         # Временная шкала
    "source_reputation": float,     # Репутация источника
    "hotness_score": float,         # Оценка [0,1]
    "narrative_summary": str,       # Промежуточная сводка
    "final_output": dict | None,    # Готовый результат
}
```

## Dependency Injection (Dishka)

Используется Dishka для управления зависимостями с различными scope:

- **APP** - на весь жизненный цикл приложения (config, логгер)
- **REQUEST** - на один HTTP запрос (DB сессия, Redis клиент)
- **SESSION** - долгоживущие сессии (для WebSocket, если потребуется)

### Провайдеры

1. **ConfigProvider** - настройки приложения
2. **DatabaseProvider** - DB сессии, репозитории
3. **RedisProvider** - Redis клиенты
4. **LLMProvider** - LLM клиенты (OpenRouter)
5. **ServicesProvider** - бизнес-сервисы
6. **AgentsProvider** - LangGraph графы

## Слои приложения

### 1. API Layer (src/api)

Endpoints для:
- Health check
- Запуск обработки новостей
- Получение топ-K горячих событий
- Получение черновиков

### 2. Domain Layer (src/domain)

Чистая бизнес-логика, не зависящая от инфраструктуры:
- Entities: News, Story, Entity, Timeline
- Value Objects: HotnessScore, SourceReputation
- Events: NewsIngested, StoryScored

### 3. Service Layer (src/services)

Оркестрация бизнес-логики:
- NewsService: управление новостями
- ScoringService: расчет hotness_score
- EmbeddingsService: векторные представления

### 4. Infrastructure Layer (src/infrastructure)

Внешние зависимости:
- Database: SQLAlchemy, репозитории
- Redis: кеширование, векторные операции
- LLM: абстракция + реализация OpenRouter
- Sources: скрейперы новостей

### 5. Agents Layer (src/agents)

LangGraph агенты:
- Определение State
- Построение графа
- Узлы обработки (nodes/)

## Логирование

Structured logging с использованием structlog:
- JSON формат для продакшена
- Human-readable для разработки
- Уровни: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Контекстные логи (request_id, user_id и т.д.)

## База данных

### Основные таблицы

1. **news** - входящие новости
2. **stories** - кластеры новостей (сюжеты)
3. **entities** - извлеченные сущности (компании, тикеры)
4. **story_entities** - связь many-to-many
5. **timelines** - временные метки событий
6. **sources** - источники новостей с репутацией

### Индексы

- Полнотекстовый поиск по новостям
- Индексы по cluster_id, timestamp
- GIN индексы для JSONB полей

## Redis

Использование:
1. **Кеш** - результаты обработки, embeddings
2. **Векторные операции** - для дедупликации (косинусное сходство)
3. **Rate limiting** - ограничение запросов к LLM

## Замена LLM провайдера

Для замены OpenRouter на другой провайдер:

1. Создать новую реализацию в `src/infrastructure/llm/`
2. Реализовать интерфейс `BaseLLM`
3. Обновить `LLMProvider` в `src/di.py`
4. Обновить переменные окружения в `.env`

Пример:
```python
# src/infrastructure/llm/anthropic.py
class AnthropicLLM(BaseLLM):
    async def generate(self, prompt: str) -> str:
        ...
```

## Масштабирование

Система спроектирована для горизонтального масштабирования:

1. **Stateless API** - можно запускать несколько инстансов
2. **Shared State** - PostgreSQL + Redis
3. **Task Queue** (будущее) - Celery/RQ для фоновой обработки
4. **Sharding** (будущее) - партиционирование БД по времени

## Мониторинг и метрики

Рекомендуемые метрики:
- Время обработки новости (end-to-end)
- Количество обработанных новостей/минуту
- Hotness score распределение
- Точность дедупликации
- Latency LLM запросов
- Cache hit rate

## Безопасность

1. **Валидация входных данных** - Pydantic
2. **SQL Injection** - SQLAlchemy ORM
3. **Rate Limiting** - Redis
4. **Secrets** - переменные окружения
5. **API Keys** - хранятся в .env, не коммитятся

## Расширяемость

Легко добавить:
- Новые источники новостей (src/infrastructure/sources/)
- Новые узлы в граф (src/agents/nodes/)
- Новые сервисы (src/services/)
- Новые endpoints (src/api/routes/)
- Новые LLM провайдеры (src/infrastructure/llm/)


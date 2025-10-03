# Список файлов проекта RADAR

## Документация

- `README.md` - основная документация с инструкциями запуска
- `ARCHITECTURE.md` - детальное описание архитектуры проекта
- `IMPLEMENTATION_GUIDE.md` - руководство по реализации и расширению
- `QUICKSTART.md` - быстрый старт для новых пользователей
- `PROJECT_FILES.md` - этот файл (список всех файлов)

## Конфигурация

- `pyproject.toml` - зависимости и настройки проекта
- `docker-compose.yml` - конфигурация Docker Compose
- `alembic.ini` - настройки Alembic для миграций
- `.gitignore` - игнорируемые файлы Git
- `.python-version` - версия Python для uv
- `env.example` - пример переменных окружения
- `Makefile` - команды для разработки

## Docker

- `docker/Dockerfile` - образ приложения

## Точка входа

- `main.py` - точка входа для локального запуска
- `src/main.py` - создание FastAPI приложения

## Core (Ядро)

- `src/core/__init__.py`
- `src/core/config.py` - настройки приложения (Pydantic Settings)
- `src/core/logging.py` - конфигурация логирования (structlog)
- `src/core/exceptions.py` - кастомные исключения

## Domain (Доменный слой)

- `src/domain/__init__.py`
- `src/domain/entities.py` - доменные сущности (News, Story, Entity)
- `src/domain/value_objects.py` - value objects (HotnessScore, SourceReputation)
- `src/domain/events.py` - доменные события

## Infrastructure (Инфраструктурный слой)

### Database
- `src/infrastructure/__init__.py`
- `src/infrastructure/database/__init__.py`
- `src/infrastructure/database/models.py` - SQLAlchemy модели
- `src/infrastructure/database/session.py` - управление сессиями БД
- `src/infrastructure/database/repositories.py` - репозитории

### Redis
- `src/infrastructure/redis/__init__.py`
- `src/infrastructure/redis/client.py` - Redis клиент
- `src/infrastructure/redis/cache.py` - сервис кеширования

### LLM
- `src/infrastructure/llm/__init__.py`
- `src/infrastructure/llm/base.py` - базовый интерфейс LLM
- `src/infrastructure/llm/openrouter.py` - реализация OpenRouter

### Sources
- `src/infrastructure/sources/__init__.py`
- `src/infrastructure/sources/news_scrapers.py` - скрейперы новостей (заглушки)

## Services (Сервисный слой)

- `src/services/__init__.py`
- `src/services/embeddings_service.py` - генерация embeddings
- `src/services/scoring_service.py` - расчет hotness score
- `src/services/news_service.py` - бизнес-логика новостей

## Agents (LangGraph агенты)

- `src/agents/__init__.py`
- `src/agents/state.py` - определение State графа
- `src/agents/graph.py` - построение LangGraph

### Nodes
- `src/agents/nodes/__init__.py`
- `src/agents/nodes/deduplication.py` - дедупликация новостей
- `src/agents/nodes/enrichment.py` - обогащение (NER)
- `src/agents/nodes/scoring.py` - оценка горячести
- `src/agents/nodes/context_rag.py` - RAG для контекста
- `src/agents/nodes/draft_generator.py` - генерация черновиков

## API

- `src/api/__init__.py`
- `src/api/dependencies.py` - зависимости API
- `src/api/routes/__init__.py`
- `src/api/routes/health.py` - health check эндпоинты
- `src/api/routes/radar.py` - основные эндпоинты RADAR

## Dependency Injection

- `src/di.py` - Dishka контейнер с провайдерами

## Database Migrations

- `alembic/env.py` - конфигурация Alembic
- `alembic/script.py.mako` - шаблон миграций
- `alembic/versions/__init__.py`
- `alembic/versions/001_initial_schema.py` - начальная схема БД

## Tests

- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/unit/test_scoring_service.py` - тесты scoring service
- `tests/integration/__init__.py`
- `tests/integration/test_api.py` - интеграционные тесты API

## Общая статистика

- **Всего файлов**: ~60
- **Строк кода**: ~2500+
- **Python модулей**: ~40
- **Тестов**: 4
- **Таблиц БД**: 6

## Ключевые паттерны

1. **Clean Architecture** - разделение на слои
2. **Dependency Injection** - через Dishka
3. **Repository Pattern** - для работы с БД
4. **Factory Pattern** - создание объектов
5. **Strategy Pattern** - LLM провайдеры
6. **State Pattern** - LangGraph состояния

## Технологический стек

- **Python 3.12+**
- **FastAPI** - веб-фреймворк
- **LangGraph** - граф агентов
- **PostgreSQL** - основная БД
- **Redis** - кеш и векторные операции
- **SQLAlchemy 2.0** - ORM
- **Alembic** - миграции
- **Dishka** - DI контейнер
- **Pydantic** - валидация
- **structlog** - логирование
- **sentence-transformers** - embeddings
- **Docker** - контейнеризация


# RADAR - Сервис поиска и оценки горячих новостей

Система поиска и оценки новостей в финансовой сфере с генерацией черновика для поста/статьи на основе ReAct-архитектуры с использованием LangGraph.

## Требования

- Python 3.12
- uv (установить: `pip install uv`)
- Docker и Docker Compose

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd radar
```

### 2. Настройка переменных окружения

Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите ваш API ключ OpenRouter:

```
OPENROUTER_API_KEY=your_actual_api_key_here
```

### 3. Запуск через Docker Compose

```bash
docker-compose up --build
```

Сервис будет доступен по адресу: `http://localhost:8000`

Adminer (веб-интерфейс для БД) будет доступен по адресу: `http://localhost:8080`

### 4. Запуск миграций БД

После запуска контейнеров выполните миграции:

```bash
docker-compose exec app alembic upgrade head
```

## Локальная разработка (без Docker)

### 1. Установка зависимостей

```bash
uv pip install -e .
```

### 2. Запуск PostgreSQL и Redis

```bash
docker-compose up postgres redis
```

### 3. Применение миграций

```bash
alembic upgrade head
```

### 4. Запуск приложения

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Использование API

### Документация API

После запуска доступна автоматическая документация:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Основные endpoints

#### Проверка здоровья сервиса

```bash
curl http://localhost:8000/api/v1/health
```

#### Получение топ-K горячих сюжетов

```bash
curl "http://localhost:8000/api/v1/stories/top?hours=24&limit=10"
```

Параметры:
- `hours` - временное окно в часах (по умолчанию 24)
- `limit` - количество сюжетов (по умолчанию 10)

#### Создание новости

```bash
curl -X POST "http://localhost:8000/api/v1/news" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Компания X объявила о слиянии",
    "content": "Полный текст новости...",
    "url": "https://example.com/news/1",
    "source_id": "uuid-источника",
    "published_at": "2025-10-03T10:00:00Z"
  }'
```

## Структура проекта

Подробное описание архитектуры см. в файле `ARCHITECTURE.md`.

```
radar/
├── app/                    # Основной код приложения
│   ├── api/               # API endpoints
│   ├── core/              # Конфигурация и базовые модули
│   ├── db/                # Подключения к БД и Redis
│   ├── graph/             # LangGraph агент
│   ├── llm/               # LLM провайдеры
│   ├── models/            # SQLAlchemy модели
│   ├── schemas/           # Pydantic схемы
│   └── services/          # Бизнес-логика
├── alembic/               # Миграции БД
├── docker-compose.yml     # Конфигурация Docker
└── pyproject.toml         # Зависимости проекта
```

## Создание миграций

```bash
alembic revision --autogenerate -m "Описание изменений"
alembic upgrade head
```

## Остановка сервиса

```bash
docker-compose down
```

Для удаления данных БД:

```bash
docker-compose down -v
```

## Логи

Просмотр логов в режиме реального времени:

```bash
docker-compose logs -f app
```

Уровень логирования настраивается в `.env`:

```
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

## Архитектура агента

Система использует граф LangGraph для обработки новостей:

1. Ingestion - Прием новостей
2. Deduplication - Дедупликация через векторное сходство
3. Enrichment - Извлечение сущностей
4. Scoring - Оценка горячести
5. Context Builder (RAG) - Сборка контекста
6. Draft Generator - Генерация черновика публикации

Новости с оценкой горячести выше порога (по умолчанию 0.7) проходят полный цикл обработки и генерируют черновик публикации.

## Замена LLM провайдера

Для замены OpenRouter на другой LLM провайдер:

1. Создайте новый класс в `app/llm/`, наследуя `BaseLLMProvider`
2. Реализуйте методы `generate()` и `generate_structured()`
3. Используйте новый провайдер в узлах графа

Пример смотрите в `app/llm/openrouter.py`.


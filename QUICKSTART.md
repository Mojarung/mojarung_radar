# Быстрый старт RADAR

## Минимальная настройка для запуска

### 1. Клонировать и настроить окружение

```bash
git clone <repo>
cd mojarung_radar
cp env.example .env
```

### 2. Отредактировать .env

Минимально необходимо:
```bash
OPENROUTER_API_KEY=ваш_ключ_здесь
```

### 3. Запустить через Docker Compose

```bash
docker-compose up --build
```

Сервис будет доступен на http://localhost:8000

### 4. Проверить работоспособность

```bash
curl http://localhost:8000/health
```

Ответ:
```json
{"status": "ok"}
```

## Пример использования API

### Обработка новости

```bash
curl -X POST http://localhost:8000/radar/process-news \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Apple announces record quarterly earnings",
    "content": "Apple Inc. reported record-breaking quarterly earnings today, exceeding analyst expectations by 15%. The company cited strong iPhone sales and growth in services revenue as key drivers.",
    "source": "Bloomberg",
    "url": "https://example.com/apple-earnings",
    "published_at": "2025-10-03T10:00:00Z"
  }'
```

Ответ:
```json
{
  "status": "processed",
  "hotness_score": 0.68,
  "is_hot": false,
  "final_output": null
}
```

### Получить топ историй

```bash
curl http://localhost:8000/radar/top-stories?limit=5
```

## Локальная разработка (без Docker)

### 1. Установить зависимости

```bash
uv pip install -e .
```

### 2. Запустить PostgreSQL и Redis

```bash
# PostgreSQL
docker run -d -p 5432:5432 \
  -e POSTGRES_DB=radar \
  -e POSTGRES_USER=radar_user \
  -e POSTGRES_PASSWORD=radar_password \
  postgres:16-alpine

# Redis
docker run -d -p 6379:6379 redis:7-alpine
```

### 3. Применить миграции

```bash
alembic upgrade head
```

### 4. Запустить приложение

```bash
uvicorn src.main:app --reload
```

## Структура ответов

### Горячая новость (is_hot=true)

```json
{
  "status": "processed",
  "hotness_score": 0.85,
  "is_hot": true,
  "final_output": {
    "headline": "Apple announces record quarterly earnings",
    "hotness": 0.85,
    "why_now": "Превышение ожиданий аналитиков на 15% сигнализирует о сильной позиции компании",
    "entities": {
      "companies": ["Apple Inc."],
      "tickers": ["AAPL"],
      "sectors": ["Technology"],
      "countries": ["USA"]
    },
    "sources": ["https://example.com/apple-earnings"],
    "timeline": [...],
    "draft": "# Apple бьет рекорды\n\n..."
  }
}
```

## Следующие шаги

1. Изучить ARCHITECTURE.md для понимания структуры
2. Прочитать IMPLEMENTATION_GUIDE.md для деталей реализации
3. Реализовать конкретные источники новостей
4. Добавить NER модель для извлечения сущностей
5. Настроить мониторинг и алерты


# Parser System Guide

## Архитектура системы парсеров

RADAR использует модульную архитектуру для парсинга новостей из различных источников.

### Компоненты

1. **BaseParser** (`src/parsers/base.py`) - абстрактный базовый класс
2. **RBCParser** (`src/parsers/rbc_parser.py`) - парсер РБК новостей
3. **ParserScheduler** (`src/parsers/scheduler.py`) - планировщик запуска парсеров

### Как это работает

```
┌─────────────────┐
│ ParserScheduler │  ◄── Запускается каждые N минут
└────────┬────────┘
         │
         ├──► RBCParser ──┐
         │                │
         ├──► (другие)    │
         │                │
         └────────────────┴──► RabbitMQ Queue ──► Worker ──► ClickHouse
                                                   │
                                                   └──► Faiss (дедупликация)
```

## Конфигурация

### Переменные окружения

```bash
# Интервал запуска парсеров (минуты)
PARSER_INTERVAL_MINUTES=5

# RabbitMQ настройки
NEWS_QUEUE_NAME=news_ingestion_queue
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
```

### Как изменить интервал

**В docker-compose.yml:**
```yaml
parser:
  environment:
    PARSER_INTERVAL_MINUTES: 10  # Изменить на нужное значение
```

**Локально в .env:**
```
PARSER_INTERVAL_MINUTES=10
```

## Добавление нового парсера

### Шаг 1: Создайте класс парсера

```python
# src/parsers/your_parser.py
from src.parsers.base import BaseParser
from typing import List, Dict, Any

class YourParser(BaseParser):
    def __init__(self):
        super().__init__(
            source_name="Your Source Name",
            source_url="https://yoursource.com"
        )
    
    async def fetch_news(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch news from your source"""
        articles = []
        
        # Ваша логика парсинга
        # ...
        
        # Форматируйте каждую статью
        for article_data in your_raw_data:
            article = self.format_article(
                url=article_data['url'],
                title=article_data['title'],
                content=article_data['content'],
                published_at=article_data['date']
            )
            articles.append(article)
        
        self.update_last_fetch_time()
        return articles
```

### Шаг 2: Зарегистрируйте парсер

В `src/parsers/scheduler.py`, добавьте в функцию `main()`:

```python
async def main():
    scheduler = ParserScheduler(interval_minutes=interval)
    
    # Существующие парсеры
    scheduler.register_parser(RBCParser())
    
    # Добавьте ваш парсер
    scheduler.register_parser(YourParser())
    
    await scheduler.start()
```

### Шаг 3: Настройте параметры (опционально)

Если вашему парсеру нужны специальные параметры, добавьте их в `run_all_parsers()`:

```python
async def run_all_parsers(self):
    tasks = []
    for parser in self.parsers:
        if isinstance(parser, YourParser):
            task = self.run_parser(
                parser,
                your_param1="value1",
                your_param2="value2"
            )
        # ... остальные парсеры
        
        tasks.append(task)
    
    await asyncio.gather(*tasks, return_exceptions=True)
```

## Дедупликация

Система автоматически избегает дубликатов двумя способами:

1. **URL-based deduplication** (в ParserScheduler):
   - Загружает все существующие URLs из ClickHouse
   - Проверяет каждую новую статью перед отправкой в очередь
   - Пропускает статьи с уже существующими URLs

2. **Semantic deduplication** (в Worker):
   - Использует Faiss для семантического поиска похожих статей
   - Группирует похожие статьи по `dedup_group`
   - Порог схожести настраивается через `DEDUP_SIMILARITY_THRESHOLD`

## Логирование

Все парсеры пишут детальные логи:

```bash
# Посмотреть логи парсера
docker logs radar-parser -f

# Посмотреть логи worker (обработка новостей)
docker logs radar-worker -f
```

Уровни логирования:
- `INFO`: Основные события (запуск, количество статей, ошибки)
- `DEBUG`: Детальная информация (каждая статья, дубликаты)
- `ERROR`: Ошибки парсинга

Изменить уровень:
```yaml
environment:
  LOG_LEVEL: DEBUG  # INFO, DEBUG, WARNING, ERROR
```

## Тестирование

### Локально

```bash
# Запустить парсер один раз
python -m src.parsers.scheduler

# Или напрямую тестировать парсер
python -c "
import asyncio
from src.parsers.rbc_parser import RBCParser

async def test():
    parser = RBCParser()
    articles = await parser.fetch_news(hours_back=168, max_pages=10)
    print(f'Found {len(articles)} articles')

asyncio.run(test())
"
```

### В Docker

```bash
# Перезапустить только парсер
docker-compose restart parser

# Посмотреть логи
docker logs radar-parser --tail 100 -f
```

## Мониторинг

### Проверить что парсер работает

```bash
# Количество статей в ClickHouse
docker exec -it radar-clickhouse clickhouse-client --query \
  "SELECT count() FROM radar_clickhouse.news_articles"

# Статьи за последний час
docker exec -it radar-clickhouse clickhouse-client --query \
  "SELECT count() FROM radar_clickhouse.news_articles 
   WHERE scraped_at >= now() - INTERVAL 1 HOUR"

# Источники
docker exec -it radar-clickhouse clickhouse-client --query \
  "SELECT source_id, count() as cnt 
   FROM radar_clickhouse.news_articles 
   GROUP BY source_id 
   ORDER BY cnt DESC"
```

### Очередь RabbitMQ

Откройте http://localhost:15672 (user: `radar_user`, password: `radar_password`)

Там можно увидеть:
- Количество сообщений в очереди `news_ingestion_queue`
- Скорость обработки
- Ошибки

## Troubleshooting

### Парсер не находит новые статьи

- Проверьте интервал `hours_back` - может быть слишком коротким
- Убедитесь что источник доступен (проверьте логи)

### Слишком много дубликатов

- Уменьшите интервал запуска парсера
- Проверьте что `hours_back` не слишком большой

### Парсер падает с ошибкой

- Проверьте логи: `docker logs radar-parser`
- Возможно изменилась структура сайта-источника
- Проверьте что все зависимости установлены (requests, beautifulsoup4, lxml)

### Worker не обрабатывает сообщения

- Проверьте логи worker: `docker logs radar-worker`
- Убедитесь что RabbitMQ работает: `docker ps | grep rabbitmq`
- Проверьте очередь в RabbitMQ UI

## Best Practices

1. **Уважайте источники**: не парсите слишком часто (рекомендуется минимум 5 минут)
2. **Обрабатывайте ошибки**: добавляйте try-except в критичные места
3. **Логируйте всё**: используйте `log.info()`, `log.error()` для отладки
4. **Тестируйте локально**: перед добавлением в production протестируйте парсер
5. **Добавляйте timeout**: используйте timeout для HTTP запросов
6. **Проверяйте контент**: убедитесь что text/content не пустые перед отправкой


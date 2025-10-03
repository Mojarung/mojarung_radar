# Быстрый старт RADAR

## За 5 минут до первого запуска

### 1. Подготовка окружения

```bash
git clone <repository-url>
cd radar
cp .env.example .env
```

### 2. Настройка .env

Отредактируйте `.env` и укажите ваш OpenRouter API ключ:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

### 3. Запуск

```bash
docker-compose up --build -d
```

### 4. Миграции

```bash
docker-compose exec app alembic upgrade head
```

### 5. Проверка

```bash
curl http://localhost:8000/api/v1/health
```

Должен вернуть: `{"status": "ok"}`

## Первые запросы

### Получить топ горячих новостей

```bash
curl "http://localhost:8000/api/v1/stories/top?hours=24&limit=10"
```

### Документация API

Откройте в браузере: http://localhost:8000/docs

## Остановка

```bash
docker-compose down
```

## Логи

```bash
docker-compose logs -f app
```

## Дальнейшие шаги

1. Прочитайте ARCHITECTURE.md для понимания структуры
2. Изучите EXTENDING.md для расширения функционала
3. Прочитайте DEPLOYMENT.md для production развертывания


# Руководство по развертыванию RADAR

## Требования к окружению

### Минимальные требования

- CPU: 2 ядра
- RAM: 4 GB
- Диск: 20 GB
- Python 3.12
- Docker 24.0+
- Docker Compose 2.0+

### Рекомендуемые требования для production

- CPU: 4+ ядра
- RAM: 8+ GB
- Диск: 50+ GB SSD
- PostgreSQL 16
- Redis 7

## Развертывание для разработки

### 1. Клонирование и настройка

```bash
git clone <repository-url>
cd radar
cp .env.example .env
```

Отредактируйте `.env` и укажите реальные значения.

### 2. Запуск через Docker Compose

```bash
docker-compose up --build -d
```

### 3. Применение миграций

```bash
docker-compose exec app alembic upgrade head
```

### 4. Проверка работоспособности

```bash
curl http://localhost:8000/api/v1/health
```

## Развертывание для production

### 1. Настройка переменных окружения

Создайте `.env` со следующими параметрами:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/radar
REDIS_URL=redis://redis-host:6379/0
OPENROUTER_API_KEY=sk-or-...
LOG_LEVEL=INFO
```

### 2. Использование внешних баз данных

Для production рекомендуется использовать управляемые сервисы:

- PostgreSQL: AWS RDS, Google Cloud SQL, Azure Database
- Redis: AWS ElastiCache, Google Cloud Memorystore, Azure Cache

Обновите `docker-compose.yml`, убрав секции `postgres` и `redis`.

### 3. Настройка HTTPS

Добавьте reverse proxy (nginx/traefik) с SSL сертификатами.

Пример nginx конфигурации:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Масштабирование

Для горизонтального масштабирования:

```yaml
version: '3.8'
services:
  app:
    ...
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 2G
```

Используйте load balancer для распределения нагрузки.

## Мониторинг

### Логи

```bash
docker-compose logs -f app
```

### Метрики

Интеграция с Prometheus (добавить в будущем):

- Количество обработанных новостей
- Время обработки через граф
- Количество запросов к LLM
- Использование памяти и CPU

## Резервное копирование

### PostgreSQL

```bash
docker-compose exec postgres pg_dump -U radar radar > backup.sql
```

Восстановление:

```bash
docker-compose exec -T postgres psql -U radar radar < backup.sql
```

### Redis

Redis данные можно восстановить из PostgreSQL при необходимости.

## Обновление версии

```bash
git pull
docker-compose build
docker-compose up -d
docker-compose exec app alembic upgrade head
```

## Безопасность

1. Используйте сильные пароли для БД
2. Ограничьте доступ к портам БД через firewall
3. Регулярно обновляйте зависимости
4. Используйте secrets management (AWS Secrets Manager, HashiCorp Vault)
5. Настройте rate limiting для API

## Troubleshooting

### Проблема: Сервис не стартует

```bash
docker-compose logs app
```

Проверьте переменные окружения и доступность БД.

### Проблема: Миграции не применяются

```bash
docker-compose exec app alembic current
docker-compose exec app alembic history
```

### Проблема: Высокое потребление памяти

Проверьте количество одновременных запросов к LLM и настройте лимиты в docker-compose.yml.


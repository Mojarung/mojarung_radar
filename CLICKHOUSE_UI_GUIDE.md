# ClickHouse UI Guide

## Tabix Web Interface

После запуска `docker-compose up`, откройте браузер: **http://localhost:8081**

### Подключение к ClickHouse

1. В интерфейсе Tabix нажмите на **"+"** или **"Add connection"**
2. Заполните параметры подключения:
   - **Name**: `RADAR ClickHouse` (любое имя)
   - **Host**: `clickhouse` (имя контейнера в docker-compose)
   - **Port**: `8123`
   - **User**: `default`
   - **Password**: оставьте пустым
   - **Database**: `radar_clickhouse`

3. Нажмите **"Connect"** или **"Test & Save"**

### Просмотр данных

После подключения:

1. В левой панели выберите базу данных `radar_clickhouse`
2. Найдите таблицу `news_articles`
3. Нажмите на неё для просмотра структуры

### Полезные запросы

#### Посмотреть все статьи
```sql
SELECT * FROM news_articles
ORDER BY published_at DESC
LIMIT 100
```

#### Статистика по источникам
```sql
SELECT 
    source_id,
    count() as article_count,
    min(published_at) as first_article,
    max(published_at) as last_article
FROM news_articles
GROUP BY source_id
ORDER BY article_count DESC
```

#### Группировка по dedup_group
```sql
SELECT 
    dedup_group,
    count() as cluster_size,
    groupArray(5)(title) as sample_titles
FROM news_articles
GROUP BY dedup_group
HAVING cluster_size > 1
ORDER BY cluster_size DESC
LIMIT 20
```

#### Статьи за последние 24 часа
```sql
SELECT 
    title,
    published_at,
    source_id
FROM news_articles
WHERE published_at >= now() - INTERVAL 24 HOUR
ORDER BY published_at DESC
```

#### Топ дублирующихся новостей
```sql
SELECT 
    dedup_group,
    count() as duplicate_count,
    any(title) as sample_title
FROM news_articles
GROUP BY dedup_group
ORDER BY duplicate_count DESC
LIMIT 10
```

## Альтернатива: командная строка

Если Tabix не работает, можно использовать clickhouse-client:

```bash
# Войти в контейнер ClickHouse
docker exec -it radar-clickhouse clickhouse-client

# Выполнить запрос
clickhouse-client --query "SELECT count() FROM radar_clickhouse.news_articles"
```

## Альтернатива: HTTP API

ClickHouse также доступен через HTTP на порту 8123:

```bash
# Простой запрос
curl "http://localhost:8123/?query=SELECT+count()+FROM+radar_clickhouse.news_articles"

# С форматированием JSON
curl "http://localhost:8123/?query=SELECT+*+FROM+radar_clickhouse.news_articles+LIMIT+5+FORMAT+JSON"
```


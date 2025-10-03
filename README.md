# RADAR - Система выявления и оценки горячих новостей в финансовой сфере

Система на основе ReAct-архитектуры с использованием LangGraph для выявления и оценки значимых новостей в финансовой сфере.

## Технологии

- FastAPI - веб-фреймворк
- LangGraph - граф агентов
- PostgreSQL - основная БД
- Redis - кеширование и векторные операции
- Dishka - Dependency Injection
- OpenRouter - провайдер LLM
- Alembic - миграции БД

## Требования

- Python 3.12+
- uv (установщик пакетов)
- Docker и Docker Compose

## Установка и запуск

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd mojarung_radar
```

### 2. Настройка переменных окружения

Скопируйте env.example в .env и заполните необходимые значения:

```bash
cp env.example .env
```

Обязательно укажите:
- `OPENROUTER_API_KEY` - ваш API ключ OpenRouter

### 3. Запуск через Docker Compose

```bash
docker-compose up --build
```

Приложение будет доступно по адресу: http://localhost:8000

API документация (Swagger): http://localhost:8000/docs

### 4. Запуск локально (для разработки)

Установите зависимости с помощью uv:

```bash
uv pip install -e .
```

Запустите PostgreSQL и Redis (через Docker или локально).

Примените миграции:

```bash
alembic upgrade head
```

Запустите приложение:

```bash
uvicorn src.main:app --reload
```

## Основные эндпоинты

- `GET /health` - проверка здоровья сервиса
- `POST /radar/process-news` - обработка новости
- `GET /radar/top-stories` - получение топ-K горячих историй

## Миграции базы данных

Создание новой миграции:

```bash
alembic revision --autogenerate -m "description"
```

Применение миграций:

```bash
alembic upgrade head
```

Откат миграции:

```bash
alembic downgrade -1
```

## Структура проекта

Подробное описание архитектуры см. в файле ARCHITECTURE.md

```
mojarung_radar/
├── src/
│   ├── api/              # FastAPI endpoints
│   ├── core/             # Настройки, логирование
│   ├── domain/           # Доменная модель
│   ├── infrastructure/   # БД, Redis, LLM
│   ├── agents/           # LangGraph агенты
│   ├── services/         # Бизнес-логика
│   ├── di.py             # DI контейнер
│   └── main.py           # Точка входа
├── alembic/              # Миграции
├── tests/                # Тесты
└── docker/               # Docker конфиги
```

## Замена LLM провайдера

Для замены OpenRouter на другой провайдер:

1. Создайте класс в `src/infrastructure/llm/` наследующий `BaseLLM`
2. Обновите `LLMProvider` в `src/di.py`
3. Обновите переменные окружения

## Разработка

Форматирование кода:

```bash
black src/
```

Линтинг:

```bash
ruff check src/
```

Проверка типов:

```bash
mypy src/
```

Запуск тестов:

```bash
pytest
```

## Логи

Логи выводятся в stdout в формате JSON (production) или human-readable (development).

Уровень логирования настраивается через переменную `LOG_LEVEL`.


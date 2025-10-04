# 🏢 NER Analyzer Guide

## Обзор

**NER (Named Entity Recognition) Analyzer** — это модуль для автоматического извлечения именованных сущностей из текста новостей с использованием библиотеки **Natasha**.

### Что извлекается?

1. **Компании (companies)** — коммерческие организации, упомянутые в новости
2. **Персоны (people)** — имена людей, упомянутых в новости

### Технологии

- **Natasha** — библиотека для русскоязычного NLP
- **NewsEmbedding** — векторные представления для новостного текста
- **NewsNERTagger** — специализированная модель для распознавания сущностей в новостях

---

## 📦 Установка

Зависимости уже добавлены в проект:

```toml
# pyproject.toml
"natasha>=1.6.0",
"razdel>=0.5.0",
```

При первом запуске Docker контейнера модели Natasha будут автоматически загружены.

---

## 🗄️ Структура данных в ClickHouse

### Таблица `news_articles`

```sql
CREATE TABLE IF NOT EXISTS news_articles (
    id UUID,
    source_id Int16,
    url String,
    title String,
    content String,
    published_at DateTime,
    scraped_at DateTime DEFAULT now(),
    dedup_group UUID,
    companies String DEFAULT '',  -- NEW: "Компания1; Компания2; Компания3"
    people String DEFAULT ''       -- NEW: "Персона1; Персона2; Персона3"
) ENGINE = MergeTree()
ORDER BY (published_at, id)
```

**Формат хранения:**
- Сущности хранятся в виде строки через разделитель `"; "`
- Пример: `"Газпром; Сбербанк; Яндекс"`

---

## 🚀 Использование

### 1. Автоматическая обработка (в Worker)

NER автоматически применяется ко всем новостям в `NewsProcessor`:

```python
# src/workers/news_processor.py

from src.parsers.ner_analyzer import get_ner_analyzer

class NewsProcessor:
    def __init__(self):
        self.ner_analyzer = get_ner_analyzer()
    
    async def process_message(self, message: IncomingMessage):
        # ... получение title и content ...
        
        # Извлечение сущностей
        entities = self.ner_analyzer.analyze_article(title, content)
        
        # Результат:
        # {
        #     'companies': ['Газпром', 'Сбербанк'],
        #     'people': ['Владимир Путин', 'Сергей Иванов'],
        #     'companies_count': 2,
        #     'people_count': 2,
        #     'companies_str': 'Газпром; Сбербанк',
        #     'people_str': 'Владимир Путин; Сергей Иванов'
        # }
        
        # Сохранение в ClickHouse
        self.clickhouse.insert_article(
            ...
            companies=entities['companies_str'],
            people=entities['people_str']
        )
```

### 2. Ручное использование

```python
from src.parsers.ner_analyzer import get_ner_analyzer

analyzer = get_ner_analyzer()

# Анализ статьи
title = "Газпром подписал контракт с Китаем"
content = "Глава Газпрома Алексей Миллер встретился с представителями..."

result = analyzer.analyze_article(title, content)

print(f"Компании: {', '.join(result['companies'])}")
print(f"Люди: {', '.join(result['people'])}")
```

---

## 🎯 Фильтрация организаций

### Исключенные категории

Не все организации считаются "компаниями". Исключаются:

#### 1. Государственные органы
`Минобороны`, `Госдума`, `Правительство`, `ЦБ`, `ФСБ`, `МВД`, `Роскомнадзор`

#### 2. Военные структуры
`ВСУ`, `Армия`, `ПВО`, `ВКС`, `ВМФ`

#### 3. СМИ и соцсети
`РБК`, `ТАСС`, `Telegram`, `Bloomberg`, `Reuters`, `VK`

#### 4. Образовательные учреждения
`МГУ`, `НИУ ВШЭ`, `Университет`, `Школа`

#### 5. Общие термины
`Министерство`, `Департамент`, `Комитет`, `Агентство`

#### 6. Геополитические
`ООН`, `НАТО`, `ЕС`, `СНГ`, `БРИКС`, `G7`

### Настройка фильтра

Редактируйте список в `src/parsers/ner_analyzer.py`:

```python
class NERAnalyzer:
    EXCLUDED_ORGS = {
        'ВСУ', 'Минобороны', 'РБК', ...
        # Добавьте свои исключения
    }
```

---

## 🧹 Очистка текста

NER анализатор автоматически очищает текст перед обработкой:

1. **Удаление футеров РБК**
   ```
   "Читайте РБК в Telegram!"
   "РБК в Telegram На связи с проверенными новостями"
   ```

2. **Нормализация пробелов**
   ```python
   text = re.sub(r'\s+', ' ', text)
   ```

### Добавление своих паттернов

```python
class NERAnalyzer:
    RBC_FOOTER_PATTERNS = [
        r'РБК в Telegram.*?(?=РБК|$)',
        r'Ваш паттерн здесь.*?(?=РБК|$)',
    ]
```

---

## 📊 Запросы к ClickHouse

### 1. Получить все новости с компаниями

```sql
SELECT title, companies, people 
FROM news_articles 
WHERE companies != ''
LIMIT 10
```

### 2. Найти новости о конкретной компании

```sql
SELECT title, companies, published_at
FROM news_articles
WHERE companies LIKE '%Газпром%'
ORDER BY published_at DESC
```

### 3. Топ-10 упоминаемых компаний

```sql
SELECT 
    arrayJoin(splitByString('; ', companies)) as company,
    count() as mentions
FROM news_articles
WHERE companies != ''
GROUP BY company
ORDER BY mentions DESC
LIMIT 10
```

### 4. Топ-10 упоминаемых персон

```sql
SELECT 
    arrayJoin(splitByString('; ', people)) as person,
    count() as mentions
FROM news_articles
WHERE people != ''
GROUP BY person
ORDER BY mentions DESC
LIMIT 10
```

### 5. Новости с конкретной персоной

```sql
SELECT title, people, published_at
FROM news_articles
WHERE people LIKE '%Путин%'
ORDER BY published_at DESC
LIMIT 10
```

---

## 🔧 Миграция существующей БД

Если у вас уже есть данные в ClickHouse, выполните миграцию:

```bash
# В контейнере
docker exec -it radar-api python scripts/migrate_clickhouse_add_ner_columns.py
```

Или вручную:

```sql
ALTER TABLE news_articles 
ADD COLUMN IF NOT EXISTS companies String DEFAULT '';

ALTER TABLE news_articles 
ADD COLUMN IF NOT EXISTS people String DEFAULT '';
```

---

## 📈 Производительность

### Скорость обработки

- **~100-200 мс** на статью среднего размера (500-1000 слов)
- **Batching** не поддерживается напрямую, но можно оптимизировать:

```python
# Для batch обработки
for article in articles:
    entities = analyzer.analyze_article(article['title'], article['content'])
    # ...
```

### Оптимизация

1. **Singleton pattern** — модели Natasha загружаются один раз
2. **Lazy loading** — инициализация только при первом использовании
3. **Кэширование** — результаты можно кэшировать по хэшу текста

---

## 🐛 Отладка

### Логирование

```python
# Включить debug логи
from src.core.logging_config import log

log.debug(f"Companies: {entities['companies']}")
log.debug(f"People: {entities['people']}")
```

### Типичные проблемы

#### 1. Пустой результат

**Причина:** Текст слишком короткий или не содержит сущностей

**Решение:** Проверьте длину текста и наличие имен/компаний

#### 2. Ложные срабатывания

**Причина:** Natasha может ошибочно определить обычное слово как сущность

**Решение:** Добавьте в `EXCLUDED_ORGS`

#### 3. Медленная обработка

**Причина:** Первая инициализация загружает модели (~100-200 MB)

**Решение:** Модели кэшируются после первой загрузки

---

## 🧪 Тестирование

```python
# Тестовый скрипт
from src.parsers.ner_analyzer import get_ner_analyzer

analyzer = get_ner_analyzer()

test_cases = [
    {
        "title": "Газпром и Роснефть подписали соглашение",
        "content": "Гендиректор Газпрома Алексей Миллер встретился с главой Роснефти Игорем Сечиным..."
    },
    {
        "title": "ЦБ повысил ключевую ставку",
        "content": "Центральный банк принял решение повысить ставку..."
    }
]

for test in test_cases:
    result = analyzer.analyze_article(test['title'], test['content'])
    print(f"\n📰 {test['title']}")
    print(f"🏢 Компании: {', '.join(result['companies']) or 'нет'}")
    print(f"👤 Люди: {', '.join(result['people']) or 'нет'}")
```

---

## 🎓 Примеры

### Пример 1: Финансовая новость

**Вход:**
```
Title: "Сбербанк увеличил прибыль на 20%"
Content: "Президент Сбербанка Герман Греф сообщил о росте прибыли..."
```

**Выход:**
```python
{
    'companies': ['Сбербанк'],
    'people': ['Герман Греф'],
    'companies_str': 'Сбербанк',
    'people_str': 'Герман Греф'
}
```

### Пример 2: Политическая новость

**Вход:**
```
Title: "Путин встретился с главами регионов"
Content: "Президент России Владимир Путин провел совещание..."
```

**Выход:**
```python
{
    'companies': [],  # Нет коммерческих компаний
    'people': ['Владимир Путин'],
    'companies_str': '',
    'people_str': 'Владимир Путин'
}
```

### Пример 3: Новость с исключениями

**Вход:**
```
Title: "РБК: Минобороны закупает новое оборудование"
Content: "Министерство обороны России объявило тендер..."
```

**Выход:**
```python
{
    'companies': [],  # РБК и Минобороны исключены
    'people': [],
    'companies_str': '',
    'people_str': ''
}
```

---

## 📚 Дополнительные ресурсы

- [Natasha Documentation](https://github.com/natasha/natasha)
- [ClickHouse String Functions](https://clickhouse.com/docs/en/sql-reference/functions/string-functions)
- [RADAR Architecture Overview](./README.md)

---

## 🤝 Вклад в проект

Если вы хотите улучшить NER анализатор:

1. Добавьте новые паттерны очистки
2. Расширьте список исключений
3. Оптимизируйте производительность
4. Добавьте тесты

---

**🎉 Готово! Теперь все новости автоматически обогащаются данными о компаниях и персонах!**


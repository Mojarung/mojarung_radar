# FastText Classifier Integration

## Обзор

RADAR использует быструю и эффективную модель **FastText** для классификации новостей по категориям.

## Модель

**Источник**: [data-silence/fasttext-rus-news-classifier](https://huggingface.co/data-silence/fasttext-rus-news-classifier)

**Особенности**:
- ⚡ **Очень быстрая** - классификация за миллисекунды
- 🔄 **Offline** - работает без интернета после загрузки

## Категории

Модель классифицирует новости по следующим категориям:

### Финансово-релевантные ✅

- **`economy`** - Экономика
- **`stock`** - Акции, биржа
- **`business`** - Бизнес
- **`finance`** - Финансы

### Нерелевантные ❌

- `sport` - Спорт
- `politics` - Политика (без экономического контекста)
- `culture` - Культура
- `society` - Общество
- `technology` - Технологии (без финансов)
- и другие...

## Как работает

### 1. Классификация

```python
from src.parsers.fasttext_classifier import get_fasttext_classifier

classifier = get_fasttext_classifier()

result = classifier.classify_article(
    title="ЦБ повысил ключевую ставку до 16%",
    content_preview="Банк России принял решение..."
)

# Результат:
# {
#     'is_relevant': True,
#     'confidence': 0.9993,
#     'category': 'economy',
#     'reason': "FastText classified as 'economy' with score 0.999"
# }
```

### 2. Батчинг

```python
articles = [
    {'title': 'Новость 1', 'overview': 'Текст...'},
    {'title': 'Новость 2', 'overview': 'Текст...'},
]

relevant = classifier.batch_classify(articles, min_score=0.5)
# Вернет только релевантные статьи
```

### 3. Интеграция в парсер

Автоматически работает при `classify=True`:

```python
# src/parsers/scheduler.py
task = self.run_parser(
    parser,
    classify=True  # FastText классификация включена
)
```

## Настройка

### Минимальный порог уверенности

```python
# .env или docker-compose.yml
FASTTEXT_MIN_SCORE=0.5  # 0.0-1.0 (default: 0.5)
```

**Рекомендации**:
- `0.3-0.4` - Максимальный охват (больше false positives)
- `0.5-0.6` - Баланс (рекомендуется)
- `0.7-0.9` - Высокая точность (может пропустить пограничные)

### Добавить категории

```python
# src/parsers/fasttext_classifier.py
FINANCIAL_CATEGORIES = {
    'economy',
    'stock',
    'business',
    'finance',
    'realty',      # Добавить недвижимость
    'crypto',      # Добавить крипту (если модель поддерживает)
}
```

## Производительность

### Скорость

| Операция | Время |
|----------|-------|
| Загрузка модели | ~2-3 сек (один раз при старте) |
| Классификация 1 статьи | ~0.001-0.002 сек |
| Батч 100 статей | ~0.1-0.2 сек |

### Сравнение с LLM

| Параметр | FastText | LLM (OpenRouter) |
|----------|----------|------------------|
| Скорость | ⚡⚡⚡ 0.002 сек | 🐌 1-2 сек |
| Стоимость | 💰 Бесплатно | 💸 $0.001/запрос |
| Точность | ✅ 90-95% | ✅✅ 95-98% |
| Offline | ✅ Да | ❌ Нет |

**Вывод**: FastText в **500-1000 раз быстрее** и бесплатно! 🚀

## Пример работы

### Вход

```
8 проектов РБК × 10 страниц = ~1600 статей
```

### Обработка

```
1. Парсинг заголовков и анонсов (~5 сек)
2. FastText классификация (~1.5 сек для 1600 статей)
3. Фильтрация (economy, stock, business, finance)
4. Результат: ~400 релевантных статей (25%)
5. Загрузка полного текста только для релевантных (~40 сек)
```

### Итого

- ⏱️ **Время**: ~46 сек (вместо ~1600 сек с LLM)
- 💰 **Стоимость**: $0 (вместо ~$1.60 с LLM)
- 📊 **Точность**: ~92% (vs ~96% у LLM)

## Troubleshooting

### Ошибка установки fasttext

```bash
# Если не установился fasttext-wheel
pip uninstall fasttext fasttext-wheel
pip install fasttext-wheel
```

### Numpy version conflict

```bash
# Убедитесь что numpy < 2.0
pip install 'numpy>=1.26.0,<2.0.0'
```

### Модель не загружается

```bash
# Вручную загрузить модель
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('data-silence/fasttext-rus-news-classifier', 'fasttext_news_classifier.bin')"
```

### Слишком много false positives

→ Увеличьте `FASTTEXT_MIN_SCORE` до 0.7-0.8

### Пропускаются важные новости

→ Уменьшите `FASTTEXT_MIN_SCORE` до 0.3-0.4  
→ Проверьте, что категория новости в `FINANCIAL_CATEGORIES`

## Логирование

```bash
# Логи классификации
docker logs radar-parser -f | grep "Classified"

# Пример:
# Classified: 'ЦБ повысил ключевую ставку...' -> category=economy, score=0.999, relevant=True
# Filtered out: 'Новый фильм вышел...' (category=culture, score=0.987)
```

## Метрики в ClickHouse

```sql
-- Статьи по категориям
SELECT 
    JSONExtractString(classification, 'category') as category,
    count() as cnt,
    avg(CAST(JSONExtractString(classification, 'confidence') AS Float64)) as avg_confidence
FROM news_articles
WHERE classification != ''
GROUP BY category
ORDER BY cnt DESC;
```

## Best Practices

1. ✅ **Используйте FastText по умолчанию** - быстро и точно
2. ✅ **Настройте порог** - экспериментируйте с min_score
3. ✅ **Мониторьте метрики** - проверяйте процент отфильтрованных
4. ✅ **Логируйте примеры** - анализируйте false negatives/positives
5. 🔄 **LLM для edge cases** - используйте LLM только для сомнительных

## Будущие улучшения

- [ ] Файн-тюнинг на финансовых новостях РБК
- [ ] Добавить multi-label classification
- [ ] Кэширование результатов классификации
- [ ] A/B тестирование с LLM
- [ ] Ensemble (FastText + простые правила)


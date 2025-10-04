Отлично! Сейчас детально распишу каждую фичу с практической точки зрения.

---

# 📋 ДЕТАЛЬНАЯ РАЗБИВКА ИННОВАЦИЙ

## **1. Sentiment Drift Detector (Детектор изменения настроения)**

### 🎯 Простыми словами:
*Представь, что ты читаешь новости о компании. Утром пишут "компания обсуждает возможности", в обед "возможны проблемы", вечером "компания на грани краха". Вот это **изменение** настроения от нейтрального к негативному и есть сигнал опасности. Мы автоматически отслеживаем, как меняется тон новостей во времени.*

### 📦 Что нужно подготовить:

**Данные:**
- ✅ У вас уже есть: статьи с `published_at` и `content`
- ❌ Нужно добавить: sentiment метки для обучения

**Модели:**
```python
# 1. Sentiment Analysis модель
- Вариант A (простой): RuSentiment или dostoevsky (готовые для русского)
- Вариант B (точный): Fine-tuned BERT на финансовых новостях
- Размер: ~500MB для BERT, ~100MB для легкой модели

# 2. Drift вычисление (без ML, просто математика)
- Moving average sentiment
- Standard deviation
- Z-score для аномалий
```

**Инфраструктура:**
```yaml
Новые таблицы:
  - news_sentiment:
      - article_id
      - sentiment_score: float (-1 to 1)
      - confidence: float (0 to 1)
      - computed_at: timestamp

Изменения в коде:
  - src/services/sentiment_analyzer.py  # новый файл
  - src/services/hotness_scorer.py      # добавить sentiment_drift компонент
  - src/workers/news_processor.py       # интеграция
```

### 🔨 Сложность реализации:

**Уровень:** ⭐⭐⭐ (средняя)

**Этапы работы:**
1. **День 1-2:** Интеграция готовой sentiment модели
   - Установка: `pip install dostoevsky`
   - Тестирование на 100 статьях
   - Проверка качества (precision ~70-80% ОК для MVP)

2. **День 3:** Добавление в pipeline
   ```python
   # В news_processor.py добавить:
   async def process_article(article):
       sentiment = sentiment_analyzer.analyze(article['content'])
       article['sentiment'] = sentiment
       # ... existing code
   ```

3. **День 4:** Вычисление drift
   ```python
   def calculate_sentiment_drift(articles):
       sentiments = sorted(articles, key=lambda x: x['published_at'])
       scores = [a['sentiment'] for a in sentiments]
       
       # Простая версия: разница начало-конец
       drift = abs(scores[-1] - scores[0])
       
       # Продвинутая: взвешенная по velocity
       drift_weighted = drift * velocity_factor
       return drift_weighted
   ```

4. **День 5:** Тестирование и тюнинг весов

**Подводные камни:**
- ⚠️ Sentiment модели для русского языка хуже английских (70-75% vs 85-90% accuracy)
- ⚠️ Финансовый сленг может не распознаваться ("бычий тренд", "медвежий рынок")
- ⚠️ Нужна калибровка порогов "значимого" drift

**Что делать если мало времени:**
- Используйте готовую модель `dostoevsky` без fine-tuning
- Простой drift = `sentiment_last - sentiment_first`
- Минимальная интеграция: только в `hotness_scorer.py`

---

## **2. Cross-Asset Contagion Score (Заражение между активами)**

### 🎯 Простыми словами:
*Если падает крупный поставщик чипов, пострадают все компании, которые делают смартфоны и компьютеры. Мы строим карту "кто на кого влияет" и автоматически находим, какие другие компании могут пострадать от новости.*

### 📦 Что нужно подготовить:

**Данные:**
```python
# 1. Граф связей компаний
company_relationships = {
    "supplier_of": [...],      # Tesla поставщик для X, Y, Z
    "competitor_of": [...],    # Tesla конкурент BMW, Toyota
    "same_sector": [...],      # Tesla в автосекторе с Ford
    "customer_of": [...]       # Tesla клиент TSMC (чипы)
}

# Источники данных:
- Bloomberg Supply Chain данные (платно, ~$1000/month)
- ИЛИ Wikipedia/Wikidata (бесплатно, но менее точно)
- ИЛИ парсинг годовых отчетов (SEC 10-K, раздел "Principal Suppliers")
```

**Модели:**
```python
# Graph algorithms (без ML)
1. PageRank для определения важности компаний
2. Shortest Path для расстояния между компаниями
3. Community Detection для отраслевых кластеров

# Библиотека: networkx (уже популярная)
pip install networkx
```

**Инфраструктура:**
```yaml
Новые компоненты:
  - data/company_graph.json          # граф связей
  - src/services/graph_analyzer.py   # анализ графа
  - src/db/models.py:
      - CompanyRelationship(from_id, to_id, type, strength)

Изменения:
  - src/services/hotness_scorer.py   # добавить contagion_score
```

### 🔨 Сложность реализации:

**Уровень:** ⭐⭐⭐⭐ (высокая)

**Этапы работы:**

1. **День 1-3:** Сбор данных о связях
   ```python
   # Упрощенный подход для MVP:
   # Используем только отраслевую принадлежность
   sectors = {
       "Automotive": ["Tesla", "Ford", "BMW", "Toyota"],
       "Tech": ["Apple", "Microsoft", "Google"],
       # ...
   }
   
   # Все в одном секторе = связаны
   ```

2. **День 4-5:** Построение графа
   ```python
   import networkx as nx
   
   G = nx.Graph()
   
   # Добавляем компании как узлы
   for company in companies:
       G.add_node(company, market_cap=..., sector=...)
   
   # Добавляем связи как ребра
   for rel in relationships:
       G.add_edge(rel['from'], rel['to'], 
                  type=rel['type'],
                  weight=rel['strength'])
   
   # Вычисляем PageRank
   centrality = nx.pagerank(G)
   ```

3. **День 6-7:** Интеграция в скоринг
   ```python
   def calculate_contagion(affected_company, graph):
       # Найти соседей в графе
       neighbors = list(graph.neighbors(affected_company))
       
       # Вычислить централизованность
       centrality_score = pagerank[affected_company]
       
       # Подсчитать затронутых
       affected_count = len(neighbors)
       
       # Финальная формула
       contagion = centrality_score * affected_count / 100
       return min(1.0, contagion)
   ```

4. **День 8-10:** Тестирование на реальных кейсах
   - Проверить на известных событиях (например, санкции против РФ → влияние на европейские банки)

**Подводные камни:**
- ⚠️ **ГЛАВНАЯ ПРОБЛЕМА:** Качественные данные о supply chains дорогие или отсутствуют
- ⚠️ Граф может быть огромным (>10K компаний) → нужна оптимизация
- ⚠️ Связи меняются во времени (компании меняют поставщиков)

**Что делать если мало времени:**
```python
# Минимальная версия: только sector-based
def simple_contagion(company, articles):
    company_sector = get_sector(company)
    
    # Считаем, сколько других компаний из того же сектора упомянуты
    same_sector_count = sum(
        1 for art in articles 
        if get_sector(art['entity']) == company_sector
    )
    
    # Нормализуем
    return min(1.0, same_sector_count / 5.0)
```

**Для питча:**
- Покажите граф из 20-30 ключевых компаний (визуально красиво!)
- Демо на конкретном примере: "Новость о Tesla → автоматически нашли 8 связанных компаний"

---

## **3. Institutional Source Authority Matrix (Матрица авторитетности)**

### 🎯 Простыми словами:
*Не все источники одинаково хороши во всем. BBC отлично для политики, но не лучший для финансов. Forbes хорош для бизнеса, но медленнее Twitter для breaking news. Мы создаем "табель успеваемости" каждого источника по разным темам.*

### 📦 Что нужно подготовить:

**Данные:**
```python
# Историческая оценка источников
source_performance = {
    "source_id": "bloomberg",
    "accuracy_by_type": {
        "m&a": 0.95,           # 95% новостей подтверждаются
        "earnings": 0.92,
        "bankruptcy": 0.88,
        "rumor": 0.45
    },
    "speed_rank": 2,            # 2-й по скорости (1=fastest)
    "correction_rate": 0.02     # 2% статей корректируются позже
}

# Источники данных:
1. Ваша собственная история (если есть >3 месяцев данных)
2. Публичные репутационные базы (Media Bias Chart, AllSides)
3. Экспертная разметка (вручную оценить топ-20 источников)
```

**Модели:**
```python
# Классификатор типов новостей
- Input: текст новости
- Output: [m&a, earnings, bankruptcy, regulatory, other]

# Можно использовать:
1. Keyword-based (простой)
2. FastText classifier (средний)
3. BERT classifier (сложный)
```

**Инфраструктура:**
```yaml
Новые таблицы:
  - source_authority_matrix:
      - source_id
      - news_type
      - accuracy_score
      - sample_count
      - last_updated

Файлы:
  - src/services/news_classifier.py    # определение типа новости
  - src/services/source_evaluator.py   # оценка источника
  - data/source_matrix.json            # предварительные данные
```

### 🔨 Сложность реализации:

**Уровень:** ⭐⭐⭐ (средняя)

**Этапы работы:**

1. **День 1-2:** Классификация типов новостей
   ```python
   # Keyword-based для MVP
   NEWS_TYPE_KEYWORDS = {
       "m&a": ["merger", "acquisition", "слияние", "поглощение", "M&A"],
       "earnings": ["earnings", "прибыль", "revenue", "выручка"],
       "bankruptcy": ["bankruptcy", "банкротство", "default"],
       "regulatory": ["regulation", "SEC", "регулирование", "закон"]
   }
   
   def classify_news_type(title, content):
       text = (title + " " + content).lower()
       scores = {}
       for news_type, keywords in NEWS_TYPE_KEYWORDS.items():
           score = sum(1 for kw in keywords if kw in text)
           scores[news_type] = score
       
       return max(scores, key=scores.get) if max(scores.values()) > 0 else "other"
   ```

2. **День 3-4:** Создание начальной матрицы
   ```python
   # Экспертная разметка топ источников
   INITIAL_MATRIX = {
       "bloomberg": {
           "m&a": 0.95,
           "earnings": 0.92,
           "bankruptcy": 0.90,
           "regulatory": 0.88,
           "other": 0.80
       },
       "reuters": {...},
       "rbc.ru": {...},
       # ... топ 20 источников
   }
   
   # Для неизвестных источников: средние значения
   DEFAULT_SCORES = {
       "m&a": 0.60,
       "earnings": 0.65,
       # ...
   }
   ```

3. **День 5-6:** Интеграция в scoring
   ```python
   def calculate_enhanced_credibility(articles):
       scores = []
       for article in articles:
           source = article['source_id']
           news_type = classify_news_type(article['title'], article['content'])
           
           # Получить score из матрицы
           authority = get_authority_score(source, news_type)
           scores.append(authority)
       
       return np.mean(scores)
   ```

4. **День 7:** (Опционально) Автоматическое обновление
   ```python
   # Отслеживание подтверждений
   def update_authority_matrix(source, news_type, was_confirmed):
       current_score = matrix[source][news_type]
       
       # Экспоненциальное скользящее среднее
       alpha = 0.1
       new_score = alpha * (1.0 if was_confirmed else 0.0) + (1-alpha) * current_score
       
       matrix[source][news_type] = new_score
   ```

**Подводные камни:**
- ⚠️ Cold start problem: что делать с новыми источниками?
- ⚠️ Нужен механизм подтверждения (как узнать, что новость оказалась правдой?)
- ⚠️ Может быть предвзятость в экспертной разметке

**Что делать если мало времени:**
```python
# Минимум: только для топ-10 источников
# Остальные получают базовый reputation_score из БД
def get_authority(source, news_type):
    if source in KNOWN_MATRIX:
        return KNOWN_MATRIX[source].get(news_type, 0.7)
    else:
        # Fallback to basic reputation
        return sources_db.get_reputation(source)
```

---

## **4. Market Reaction Predictor (Предиктор влияния на рынок)**

### 🎯 Простыми словами:
*Когда ты видишь новость "Apple выпустила новый iPhone", хочется знать: "Это важно? Акции вырастут?" Мы обучаем систему предсказывать, насколько сильно цена акций может измениться после новости — вроде прогноза погоды, но для биржи.*

### 📦 Что нужно подготовить:

**Данные:**
```python
# Обучающий датасет (нужно собрать!)
training_data = {
    "news_features": {
        "text": "Apple announces merger with...",
        "sentiment": -0.3,
        "source_authority": 0.95,
        "entities": ["AAPL"],
        "news_type": "m&a",
        "time_of_day": "09:30",  # важно! до/после открытия биржи
        "market_cap": 2.8e12
    },
    "target": {
        "price_change_1h": 0.03,      # +3% за час
        "price_change_24h": 0.05,     # +5% за день
        "volatility_spike": True,     # была ли резкая волатильность
        "volume_spike": 2.5           # объем торгов x2.5 от нормы
    }
}

# Источники:
1. Исторические новости + цены акций (Yahoo Finance API - бесплатно)
2. Нужно минимум 1000-5000 примеров для обучения
3. Временной период: 6-12 месяцев истории
```

**Модели:**
```python
# ML модель для регрессии
Варианты:
1. LightGBM (рекомендую для MVP)
   - Быстрый, работает на CPU
   - Хорошо с табличными данными
   - 2-3 дня на обучение

2. XGBoost
   - Чуть точнее LightGBM
   - Стандарт индустрии

3. Neural Network (LSTM)
   - Для временных рядов
   - Сложнее, требует GPU
   - Не рекомендую для первой версии
```

**Инфраструктура:**
```yaml
Скрипты сбора данных:
  - scripts/collect_historical_prices.py    # Yahoo Finance
  - scripts/match_news_to_prices.py         # соединение новостей и цен
  - scripts/train_market_predictor.py       # обучение модели

Новые файлы:
  - src/services/market_predictor.py        # inference
  - models/market_impact_lgbm.pkl           # сохраненная модель
  - data/market_impact_features.json        # feature engineering

Зависимости:
  - yfinance  # API для цен
  - lightgbm
  - scikit-learn
```

### 🔨 Сложность реализации:

**Уровень:** ⭐⭐⭐⭐⭐ (очень высокая - самая сложная!)

**Этапы работы:**

1. **Неделя 1: Сбор данных**
   ```python
   import yfinance as yf
   
   # 1. Скачать исторические цены
   tickers = ["AAPL", "TSLA", "GAZP.ME", ...]  # топ 50-100 компаний
   
   for ticker in tickers:
       data = yf.download(ticker, start="2024-01-01", end="2024-12-31")
       # data содержит: Open, High, Low, Close, Volume
       save_to_database(ticker, data)
   
   # 2. Соединить с новостями
   for news in historical_news:
       entity = news['entities'][0]  # основная компания
       ticker = entity_to_ticker(entity)  # "Apple" -> "AAPL"
       
       # Найти цену до и после новости
       price_before = get_price(ticker, news['published_at'])
       price_after_1h = get_price(ticker, news['published_at'] + 1hour)
       price_after_24h = get_price(ticker, news['published_at'] + 24hours)
       
       # Вычислить изменение
       change_1h = (price_after_1h - price_before) / price_before
       
       # Сохранить как обучающий пример
       training_examples.append({
           "features": extract_features(news),
           "target": change_1h
       })
   ```

2. **Неделя 2: Feature Engineering**
   ```python
   def extract_features(news):
       return {
           # Текстовые фичи
           "sentiment": news['sentiment'],
           "sentiment_magnitude": abs(news['sentiment']),
           "title_length": len(news['title']),
           "content_length": len(news['content']),
           
           # Категориальные
           "news_type": news['news_type'],  # one-hot encoding
           "source_tier": get_source_tier(news['source']),  # 1,2,3
           
           # Временные
           "hour_of_day": news['published_at'].hour,
           "is_trading_hours": is_market_open(news['published_at']),
           "day_of_week": news['published_at'].weekday(),
           
           # Контекстные
           "market_cap": get_market_cap(news['entities'][0]),
           "recent_volatility": get_historical_volatility(ticker, 30days),
           "sector": get_sector(news['entities'][0]),
           
           # Метрики новости
           "hotness_base": news['hotness_score'],
           "num_sources": len(news['cluster']),
           "velocity": news['velocity']
       }
   ```

3. **Неделя 3: Обучение модели**
   ```python
   import lightgbm as lgb
   from sklearn.model_selection import train_test_split
   
   # Подготовка данных
   X = pd.DataFrame([ex['features'] for ex in training_examples])
   y = np.array([ex['target'] for ex in training_examples])
   
   # Категориальные переменные
   categorical_features = ['news_type', 'source_tier', 'sector']
   
   X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
   
   # Обучение
   params = {
       'objective': 'regression',
       'metric': 'rmse',
       'num_leaves': 31,
       'learning_rate': 0.05,
       'feature_fraction': 0.9
   }
   
   model = lgb.train(
       params,
       lgb.Dataset(X_train, y_train, categorical_feature=categorical_features),
       num_boost_round=1000,
       valid_sets=[lgb.Dataset(X_test, y_test)]
   )
   
   # Сохранить
   model.save_model('models/market_impact_lgbm.pkl')
   ```

4. **Неделя 4: Интеграция и оценка**
   ```python
   # В hotness_scorer.py
   def calculate_market_adjusted_hotness(news, base_hotness):
       features = extract_features(news)
       
       # Предсказание
       predicted_impact = market_predictor.predict(features)
       
       # Интерпретация
       if abs(predicted_impact) > 0.02:  # >2% движение
           impact_multiplier = 1.0 + abs(predicted_impact) * 5  # усиление
       else:
           impact_multiplier = 1.0
       
       return base_hotness * impact_multiplier
   ```

**Подводные камни:**
- ⚠️ **ОГРОМНАЯ ПРОБЛЕМА:** Причинно-следственная связь vs корреляция
  - Не каждое движение цены вызвано новостями!
  - Может быть обратная связь: цена двигается → появляются новости
- ⚠️ Нужны данные минимум за 6 месяцев (лучше год)
- ⚠️ Качество сильно зависит от качества entity extraction
- ⚠️ Разные рынки ведут себя по-разному (US vs RU)
- ⚠️ Overfitting — модель может "запомнить" прошлое, но не предсказать будущее

**Метрики успеха:**
```python
# Оценка модели
from sklearn.metrics import mean_squared_error, r2_score

y_pred = model.predict(X_test)

rmse = mean_squared_error(y_test, y_pred, squared=False)
r2 = r2_score(y_test, y_pred)

print(f"RMSE: {rmse:.4f}")  # Цель: <0.03 (3% ошибка)
print(f"R²: {r2:.3f}")      # Цель: >0.3 (объясняет 30%+ вариации)

# Для питча:
# "Модель предсказывает ценовое движение с точностью ±2.8%"
# "R² = 0.42 означает, что мы объясняем 42% движений цены новостями"
```

**Что делать если мало времени:**
```python
# Упрощенная версия: rule-based predictor
def simple_market_impact(news):
    impact = 0.0
    
    # Правила
    if news['news_type'] == 'm&a':
        impact += 0.05  # M&A обычно дает 5%
    
    if news['sentiment'] < -0.7:
        impact += 0.03  # сильный негатив
    
    if news['source_authority'] > 0.9:
        impact *= 1.5  # авторитетный источник усиливает
    
    return min(0.10, impact)  # cap на 10%
```

---

## **5. Breaking News Velocity Spike Detection (Детектор всплесков)**

### 🎯 Простыми словами:
*Разница между "новости выходят постепенно" и "БАХ! все СМИ одновременно пишут!". Второе — сигнал, что случилось что-то ОЧЕНЬ важное прямо сейчас. Как сейсмограф для информационных землетрясений.*

### 📦 Что нужно подготовить:

**Данные:**
```python
# Нужны только временные метки (уже есть!)
article_timestamps = [
    "2024-10-04T09:00:00",
    "2024-10-04T09:05:00",
    "2024-10-04T09:08:00",
    # ...
]

# Никакого дополнительного сбора не требуется!
```

**Модели:**
- Никаких ML моделей!
- Только математика: производные, скользящие средние

**Инфраструктура:**
```yaml
Изменения:
  - src/services/hotness_scorer.py  # модифицировать _calculate_velocity
  
Новые функции:
  - calculate_velocity_spike()
  - calculate_acceleration()
```

### 🔨 Сложность реализации:

**Уровень:** ⭐ (очень низкая - самая простая!)

**Этапы работы:**

1. **День 1: Реализация**
   ```python
   def calculate_velocity_spike(articles, time_window_hours=24):
       """
       Вычисляет spike в velocity публикаций
       """
       if len(articles) < 3:
           return 0.0
       
       # Сортировка по времени
       sorted_articles = sorted(articles, key=lambda x: x['published_at'])
       
       # Разбить на временные окна (каждые 10 минут)
       window_size = timedelta(minutes=10)
       bins = defaultdict(int)
       
       first_time = sorted_articles[0]['published_at']
       for article in sorted_articles:
           time_diff = article['published_at'] - first_time
           bin_index = int(time_diff.total_seconds() / window_size.total_seconds())
           bins[bin_index] += 1
       
       # Найти максимальный spike
       counts = list(bins.values())
       if not counts:
           return 0.0
       
       max_spike = max(counts)
       avg_rate = np.mean(counts) if counts else 1
       
       # Нормализованный spike
       spike_ratio = max_spike / (avg_rate + 1e-6)
       
       # Логарифмическая нормализация
       spike_score = min(1.0, np.log1p(spike_ratio) / np.log1p(10))
       
       return spike_score
   ```

2. **День 2: Интеграция**
   ```python
   # В hotness_scorer.py
   def _calculate_velocity(self, articles, time_window_hours):
       # Существующий код для average velocity
       base_velocity = len(articles) / time_span
       normalized_velocity = min(1.0, base_velocity / 2.0)
       
       # НОВОЕ: добавить spike detection
       spike_score = calculate_velocity_spike(articles, time_window_hours)
       
       # Комбинировать
       # Если spike высокий, усиливаем velocity
       velocity_with_spike = normalized_velocity * (1 + spike_score * 0.5)
       
       return min(1.0, velocity_with_spike)
   ```

3. **День 3: Тестирование**
   ```python
   # Тест на синтетических данных
   
   # Сценарий A: Равномерное распределение
   articles_steady = create_articles_every_hour(count=24)
   spike_steady = calculate_velocity_spike(articles_steady)
   # Ожидаем: ~0.0-0.2
   
   # Сценарий B: Внезапный всплеск
   articles_spike = [
       *create_articles_at_time("09:00", count=1),
       *create_articles_at_time("10:00", count=15),  # SPIKE!
       *create_articles_at_time("11:00", count=1)
   ]
   spike_breaking = calculate_velocity_spike(articles_spike)
   # Ожидаем: ~0.7-0.9
   ```

**Подводные камни:**
- ⚠️ Минимальные! Это самая простая фича
- ⚠️ Нужно выбрать правильный размер временного окна (10 мин? 30 мин?)
- ⚠️ Может давать false positives если источник публикует пакетами (например, утренний дайджест)

**Визуализация для питча:**
```python
import matplotlib.pyplot as plt

# График публикаций во времени
plt.figure(figsize=(12, 4))

# Пример 1: Равномерный поток
plt.subplot(1, 2, 1)
plt.hist(steady_timestamps, bins=24, alpha=0.7, color='blue')
plt.title("Обычная новость\nSpike Score: 0.15")
plt.xlabel("Время (часы)")
plt.ylabel("Количество публикаций")

# Пример 2: Breaking news
plt.subplot(1, 2, 2)
plt.hist(spike_timestamps, bins=24, alpha=0.7, color='red')
plt.axvline(x=10, color='red', linestyle='--', label='Breaking moment')
plt.title("Breaking News!\nSpike Score: 0.87")
plt.xlabel("Время (часы)")
plt.legend()

plt.tight_layout()
plt.savefig('velocity_spike_demo.png')
```

---

## **6. Narrative Coherence & Contradiction Detector**

### 🎯 Простыми словами:
*Иногда разные СМИ пишут противоречивые вещи: одни говорят "компания отрицает", другие "инсайдеры подтверждают". Мы автоматически находим такие противоречия и понижаем рейтинг "мутных" историй, где непонятно кому верить.*

### 📦 Что нужно подготовить:

**Данные:**
```python
# Примеры для обучения NLI модели (если fine-tuning)
nli_examples = [
    {
        "text1": "Компания подтвердила слияние",
        "text2": "Представитель опроверг информацию о сделке",
        "label": "contradiction"  # противоречие
    },
    {
        "text1": "Акции выросли на 5%",
        "text2": "Котировки показали рост",
        "label": "entailment"  # согласуется
    },
    {
        "text1": "Запущен новый продукт",
        "text2": "Погода в Москве дождливая",
        "label": "neutral"  # не связано
    }
]

# Для MVP: используем готовую модель, данные не нужны!
```

**Модели:**
```python
# Natural Language Inference (NLI) модель
Варианты:
1. Готовая RuBERT-NLI (для русского)
   - Уже обучена
   - ~500MB
   - Точность ~75-80%

2. Multilingual NLI (для англ+рус)
   - xlm-roberta-large-xnli
   - ~1GB
   - Точность ~80-85%

3. API (если нет GPU)
   - OpenAI API
   - Yandex Cloud
   - Стоимость: ~$0.01 за пару текстов
```

**Инфраструктура:**
```yaml
Зависимости:
  - transformers  # Hugging Face
  - torch или tensorflow

Файлы:
  - src/services/nli_analyzer.py           # анализатор противоречий
  - src/services/narrative_coherence.py    # оценка когерентности
  - models/rubert_nli/                     # модель (если локально)
```

### 🔨 Сложность реализации:

**Уровень:** ⭐⭐⭐⭐ (высокая)

**Этапы работы:**

1. **День 1-2: Загрузка NLI модели**
   ```python
   from transformers import pipeline
   
   # Вариант A: Готовая модель
   nli_model = pipeline(
       "text-classification",
       model="cointegrated/rubert-base-cased-nli-threeway",
       device=0  # GPU, или -1 для CPU
   )
   
   # Тест
   result = nli_model({
       "text": "Компания подтвердила сделку",
       "text_pair": "Представитель опроверг слияние"
   })
   # Output: {'label': 'contradiction', 'score': 0.89}
   ```

2. **День 3-4: Попарное сравнение статей**
   ```python
   def find_contradictions(articles):
       """
       Находит противоречащие пары статей в кластере
       """
       contradictions = []
       
       # Извлечь ключевые утверждения из каждой статьи
       # (можно упростить: использовать title или первый абзац)
       statements = [extract_key_statement(art) for art in articles]
       
       # Попарное сравнение O(n²) - может быть медленно!
       for i in range(len(statements)):
           for j in range(i+1, len(statements)):
               result = nli_model({
                   "text": statements[i],
                   "text_pair": statements[j]
               })
               
               if result['label'] == 'contradiction' and result['score'] > 0.75:
                   contradictions.append({
                       "article1": articles[i],
                       "article2": articles[j],
                       "confidence": result['score']
                   })
       
       return contradictions
   ```

3. **День 5-6: Вычисление coherence score**
   ```python
   def calculate_narrative_coherence(articles):
       """
       Оценка связности нарратива
       """
       if len(articles) < 2:
           return 1.0  # Одна статья - нет противоречий
       
       # 1. Найти противоречия
       contradictions = find_contradictions(articles)
       contradiction_ratio = len(contradictions) / (len(articles) * (len(articles)-1) / 2)
       
       # 2. Проверить паттерн подтверждений
       confirmation_pattern = detect_confirmation_chain(articles)
       # Идеальный паттерн: "rumor" -> "industry_report" -> "official_release"
       
       # 3. Итоговый score
       coherence = 1.0 - contradiction_ratio * 0.5  # противоречия снижают
       coherence *= confirmation_pattern_bonus      # хороший паттерн повышает
       
       return max(0.0, min(1.0, coherence))
   ```

4. **День 7-8: Интеграция в scoring**
   ```python
   # В hotness_scorer.py
   def calculate_hotness(self, articles, ...):
       # ... existing components ...
       
       # НОВОЕ: narrative coherence
       coherence = calculate_narrative_coherence(articles)
       
       # Применить как модификатор
       if coherence < 0.5:
           # Низкая coherence = снижаем доверие
           credibility *= 0.7
       elif coherence > 0.8:
           # Высокая coherence = усиливаем
           credibility *= 1.2
       
       # ... rest of calculation ...
   ```

**Подводные камни:**
- ⚠️ **ПРОИЗВОДИТЕЛЬНОСТЬ:** NLI модели медленные (0.1-0.5 сек на пару)
  - Для 10 статей = 45 пар = 4-20 секунд!
  - Решение: кэширование, батчинг, GPU
- ⚠️ Модели для русского языка менее точные чем для английского
- ⚠️ Сложно извлечь "ключевое утверждение" из статьи

**Оптимизации:**
```python
# 1. Сравнивать только заголовки (быстро но менее точно)
def quick_contradiction_check(articles):
    titles = [art['title'] for art in articles]
    # ...

# 2. Ограничить попарное сравнение
def smart_contradiction_check(articles, max_pairs=20):
    # Сравнить только топ-N по authority источников
    top_articles = sorted(articles, key=lambda x: x['authority'])[:5]
    # ...

# 3. Использовать batch inference
results = nli_model([
    {"text": t1, "text_pair": t2} 
    for t1, t2 in pairs
], batch_size=8)
```

**Для питча:**
```
Слайд: "Детектор противоречий"

[Визуализация: 2 колонки]

Левая: "Source A (Bloomberg): Company confirms merger"
Правая: "Source B (Twitter): CEO denies any talks"

[Красная линия между ними]
Contradiction Detected! ⚠️
Confidence: 87%

Action: Lowered credibility score by 30%
→ Story flagged as "developing" (требует осторожности)
```

---

## **7-10: Более Простые Фичи (Кратко)**

### **7. Entity Network Centrality**

**Простыми словами:** *Присваиваем "важность" каждой компании. Apple важнее местного стартапа.*

**Сложность:** ⭐⭐⭐  
**Время:** 3-5 дней  
**Нужно:**
- Граф из п.2 (Cross-Asset Contagion) — переиспользуем!
- Просто добавить: `centrality_weight` к breadth компоненту

```python
def enhanced_breadth(articles):
    entities = extract_entities(articles)
    
    # Взвешенная важность
    weighted_count = sum(
        centrality_scores.get(entity, 0.1) 
        for entity in entities
    )
    
    return min(1.0, weighted_count / 3.0)
```

---

### **8. Temporal Decay Adaptation**

**Простыми словами:** *M&A важно неделями, earnings важно часами.*

**Сложность:** ⭐  
**Время:** 1 день  
**Нужно:** Только правила decay rates

```python
DECAY_RATES = {
    "m&a": 0.05,           # 5% затухание в день
    "earnings": 0.5,       # 50% затухание в день
    "bankruptcy": 0.1,
    "default": 0.2
}

def apply_time_decay(hotness, news_type, age_hours):
    rate = DECAY_RATES.get(news_type, 0.2)
    decay_factor = math.exp(-rate * age_hours / 24)
    return hotness * decay_factor
```

---

### **9. Multi-Language Consensus**

**Простыми словами:** *Если пишут на русском И английском одновременно = глобальная важность.*

**Сложность:** ⭐⭐  
**Время:** 2 дня  
**Нужно:**
- Language detection (langdetect library)
- Подсчет уникальных языков

```python
from langdetect import detect

def calculate_language_diversity(articles):
    languages = set()
    for art in articles:
        try:
            lang = detect(art['title'])
            languages.add(lang)
        except:
            pass
    
    # Бонус за разнообразие
    diversity_bonus = len(languages) / 5.0  # 5+ языков = max
    return min(1.0, diversity_bonus)
```

---

### **10. Controversy Detector (упрощенная версия)**

**Простыми словами:** *Ищем слова "отрицает", "опровергает" рядом с "подтверждает".*

**Сложность:** ⭐ (без NLI модели)  
**Время:** 1 день  
**Keyword-based вариант:**

```python
CONTROVERSY_KEYWORDS = {
    "deny": ["denies", "отрицает", "опровергает", "refutes"],
    "confirm": ["confirms", "подтверждает", "announces", "объявляет"]
}

def detect_controversy_simple(articles):
    texts = [art['title'] + " " + art['content'] for art in articles]
    combined = " ".join(texts).lower()
    
    has_denial = any(kw in combined for kw in CONTROVERSY_KEYWORDS["deny"])
    has_confirmation = any(kw in combined for kw in CONTROVERSY_KEYWORDS["confirm"])
    
    if has_denial and has_confirmation:
        return 0.8  # высокая вероятность противоречия
    return 0.0
```

---

## 🎯 ФИНАЛЬНЫЕ РЕКОМЕНДАЦИИ

### **Для MVP на неделю:**
1. ✅ Breaking News Spike (1 день) — ЛЕГКО
2. ✅ Sentiment Drift (3 дня) — СРЕДНЕ
3. ✅ Simple Controversy (1 день) — ЛЕГКО
4. ✅ Multi-Language (1 день) — ЛЕГКО

**Total: ~6 дней + 1 день на презентацию**

### **Для впечатляющего питча:**
1. ✅ Market Reaction Predictor (2 недели) — WOW!
2. ✅ Cross-Asset Contagion с визуализацией графа (1.5 недели) — WOW!
3. ✅ Sentiment Drift (3 дня)

**Total: ~4 недели**

### **Что точно показать жюри:**
- **Graф компаний** (даже если упрощенный) — визуально красиво
- **Prediction accuracy метрики** — цифры убеждают
- **Side-by-side противоречий** — демонстрирует детекцию дезинформации

Какие из фич хотите реализовать? Могу начать с кода! 🚀
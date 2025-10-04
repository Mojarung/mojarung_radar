# 🚀 NVIDIA API Setup Guide

## Переход с OpenRouter на NVIDIA API

Система RADAR теперь использует **NVIDIA API** с моделью **Qwen3-Next-80B-A3B-Instruct** для генерации новостного контента и Telegram постов.

---

## ⚙️ Конфигурация

### 1. Создайте `.env` файл

Создайте файл `.env` в корне проекта со следующим содержимым:

```bash
# NVIDIA API Configuration
NVIDIA_API_KEY=ваш_ключ_nvidia_api
NVIDIA_MODEL=qwen/qwen3-next-80b-a3b-instruct
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

### 2. Получите NVIDIA API Key

1. Зарегистрируйтесь на [NVIDIA NGC](https://catalog.ngc.nvidia.com/)
2. Перейдите в раздел API Keys
3. Создайте новый API ключ
4. Скопируйте ключ и вставьте в `.env` файл

---

## 🔧 Изменения в коде

### Обновленные файлы:

#### 1. `src/core/config.py`
```python
# LLM Configuration (NVIDIA API)
nvidia_api_key: str = "your_api_key_here"
nvidia_model: str = "qwen/qwen3-next-80b-a3b-instruct"
nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
```

#### 2. `src/services/llm_client.py`
- Заменен `OpenRouterClient` на `NvidiaClient`
- Используется `openai` SDK для взаимодействия с API
- Параметры по умолчанию:
  - `temperature=0.58`
  - `top_p=0.7`
  - `max_tokens=4096`

#### 3. `docker-compose.yml`
```yaml
environment:
  NVIDIA_API_KEY: ${NVIDIA_API_KEY}
  NVIDIA_MODEL: qwen/qwen3-next-80b-a3b-instruct
  NVIDIA_BASE_URL: https://integrate.api.nvidia.com/v1
```

---

## 🎯 Использование

### API остается неизменным

```bash
POST http://localhost:8000/api/v1/analyze
Content-Type: application/json

{
  "time_window_hours": 720,
  "top_k": 5
}
```

### Ответ включает новое поле `telegram_post`

```json
{
  "results": [
    {
      "dedup_group": "uuid",
      "hotness": 0.95,
      "headline": "Краткий заголовок",
      "why_now": "Объяснение актуальности",
      "entities": ["Газпром", "Сбербанк"],
      "sources": [...],
      "timeline": [...],
      "draft": "Черновик поста...",
      "telegram_post": "⚡️Готовый пост для Telegram\n\nС эмодзи и интерактивом..."
    }
  ]
}
```

---

## 🐳 Запуск с новой конфигурацией

### 1. Остановите текущие контейнеры
```bash
docker compose down
```

### 2. Убедитесь, что `.env` файл создан с вашим API ключом

### 3. Пересоберите и запустите
```bash
docker compose up -d --build
```

### 4. Проверьте логи
```bash
docker compose logs api -f
```

Вы должны увидеть:
```
LLM generation successful (model: qwen/qwen3-next-80b-a3b-instruct)
```

---

## 📊 Преимущества NVIDIA API + Qwen

### ✅ Быстрая генерация
- Модель оптимизирована для скорости
- `max_tokens=4096` для полных ответов

### ✅ Качественная генерация на русском
- Qwen 3 отлично работает с русским языком
- Поддержка JSON-режима

### ✅ Экономия
- Конкурентные цены NVIDIA API
- Высокая скорость → меньше времени ожидания

---

## 🔍 Отладка

### Проверка подключения к API

```bash
# Войдите в контейнер API
docker exec -it radar-api bash

# Проверьте переменные окружения
env | grep NVIDIA

# Должно быть:
# NVIDIA_API_KEY=ваш_ключ
# NVIDIA_MODEL=qwen/qwen3-next-80b-a3b-instruct
# NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

### Тест API вручную

```python
from openai import OpenAI

client = OpenAI(
  base_url="https://integrate.api.nvidia.com/v1",
  api_key="ваш_ключ"
)

completion = client.chat.completions.create(
  model="qwen/qwen3-next-80b-a3b-instruct",
  messages=[{"role":"user","content":"Привет! Как дела?"}],
  temperature=0.58,
  top_p=0.7,
  max_tokens=100,
)

print(completion.choices[0].message.content)
```

---

## ❗ Важные замечания

### 1. Формат ключа
- Используйте ключ без дополнительных символов
- Формат: `nvapi-xxxxxxxxxxxxx`

### 2. Rate Limits
- Проверьте лимиты вашего аккаунта NVIDIA
- При превышении лимитов добавьте задержки

### 3. Промпты на русском
- Все промпты в системе теперь на русском
- LLM будет отвечать на русском языке

---

## 🎉 Готово!

Теперь ваша система использует NVIDIA API с моделью Qwen для генерации качественных постов на русском языке! 🚀

---

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `docker compose logs api`
2. Убедитесь, что API ключ правильный
3. Проверьте подключение к интернету
4. Проверьте квоты NVIDIA API


"""Пример использования RADAR API.

Этот скрипт демонстрирует:
1. Создание источника новостей
2. Добавление новостей
3. Получение топ-K горячих сюжетов
"""

import httpx
import asyncio
from datetime import datetime
from uuid import uuid4


BASE_URL = "http://localhost:8000/api/v1"


async def main():
    async with httpx.AsyncClient() as client:
        print("1. Проверка здоровья сервиса...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"   Статус: {response.json()}")
        
        print("\n2. Примечание: Для полноценной работы необходимо:")
        print("   - Создать источник новостей в БД")
        print("   - Указать OPENROUTER_API_KEY в .env")
        
        print("\n3. Получение топ-сюжетов за последние 24 часа...")
        try:
            response = await client.get(f"{BASE_URL}/stories/top?hours=24&limit=10")
            if response.status_code == 200:
                data = response.json()
                print(f"   Найдено сюжетов: {data['total']}")
                for story in data['stories']:
                    print(f"   - {story['headline']} (hotness: {story['hotness_score']:.2f})")
            else:
                print(f"   Ошибка: {response.status_code}")
        except Exception as e:
            print(f"   Ошибка: {e}")
        
        print("\nДля добавления новости используйте POST запрос:")
        print(f"POST {BASE_URL}/news")
        print("Content-Type: application/json")
        print("""{
    "title": "Заголовок новости",
    "content": "Полный текст новости...",
    "url": "https://example.com/news/1",
    "source_id": "uuid-источника",
    "published_at": "2025-10-03T10:00:00Z"
}""")


if __name__ == "__main__":
    asyncio.run(main())


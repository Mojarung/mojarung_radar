import json
from typing import Any

import numpy as np
from redis.asyncio import Redis

from src.core.config import Settings
from src.core.exceptions import CacheException


class RedisClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: Redis | None = None

    async def connect(self) -> None:
        self._client = Redis.from_url(
            str(self.settings.redis_url),
            encoding="utf-8",
            decode_responses=False,
        )

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()

    @property
    def client(self) -> Redis:
        if not self._client:
            raise CacheException("Redis client not connected")
        return self._client

    async def get(self, key: str) -> str | None:
        value = await self.client.get(key)
        return value.decode("utf-8") if value else None

    async def set(
        self, key: str, value: str, ttl: int | None = None
    ) -> None:
        await self.client.set(key, value, ex=ttl or self.settings.redis_cache_ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    async def set_json(
        self, key: str, value: dict[str, Any], ttl: int | None = None
    ) -> None:
        await self.set(key, json.dumps(value), ttl)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        value = await self.get(key)
        return json.loads(value) if value else None

    async def set_embedding(
        self, key: str, embedding: np.ndarray, ttl: int | None = None
    ) -> None:
        embedding_bytes = embedding.tobytes()
        await self.client.set(key, embedding_bytes, ex=ttl or self.settings.redis_cache_ttl)

    async def get_embedding(self, key: str) -> np.ndarray | None:
        value = await self.client.get(key)
        if not value:
            return None
        return np.frombuffer(value, dtype=np.float32)


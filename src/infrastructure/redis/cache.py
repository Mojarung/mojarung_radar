from typing import Any

from src.infrastructure.redis.client import RedisClient


class CacheService:
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client

    async def get_cached_result(self, key: str) -> dict[str, Any] | None:
        return await self.redis.get_json(f"result:{key}")

    async def cache_result(
        self, key: str, result: dict[str, Any], ttl: int | None = None
    ) -> None:
        await self.redis.set_json(f"result:{key}", result, ttl)

    async def invalidate_cache(self, key: str) -> None:
        await self.redis.delete(f"result:{key}")


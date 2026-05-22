from typing import Optional, Any
from .interfaces import CacheInterface

CACHE_TTL_SECONDS = 300


class RedisCache(CacheInterface):
    def __init__(self, redis_client: Any):
        self.redis = redis_client

    async def get(self, key: str) -> Any:
        return await self.redis.get(key)

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> Any:
        return await self.redis.set(key, value, ex=ex)

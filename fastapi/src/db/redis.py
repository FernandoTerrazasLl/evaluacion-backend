from typing import Optional

from redis.asyncio import Redis

redis: Optional[Redis] = None


def create_redis_client(host: str, port: int) -> Redis:
    return Redis(host=host, port=port)


async def get_redis() -> Redis:
    if not redis:
        raise RuntimeError("Redis client is not initialized")
    return redis

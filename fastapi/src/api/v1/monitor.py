from fastapi import APIRouter, HTTPException
from db import postgres, redis as db_redis

router = APIRouter()

@router.get('/healthz')
async def healthz() -> dict:
    postgres_ok = False
    try:
        pool = postgres.get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
            postgres_ok = True
    except Exception:
        pass

    redis_ok = False
    try:
        r = await db_redis.get_redis()
        await r.ping()
        redis_ok = True
    except Exception:
        pass

    if not postgres_ok or not redis_ok:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "postgres": "healthy" if postgres_ok else "unhealthy",
                "redis": "healthy" if redis_ok else "unhealthy"
            }
        )

    return {
        "status": "healthy",
        "postgres": "healthy",
        "redis": "healthy"
    }
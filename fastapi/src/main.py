import logging

import uvicorn
from fastapi import FastAPI
from redis.asyncio import Redis

from api.v1 import events, monitor
from core import config
from core.logger import LOGGING
from core.limiter import limiter
from db import postgres, redis
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event('startup')
async def startup():
    redis.redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    await postgres.init_db_pool()

@app.on_event('shutdown')
async def shutdown():
    await redis.redis.close()
    await postgres.close_db_pool()

app.include_router(monitor.router, prefix='/api/v1', tags=['monitor'])
app.include_router(events.router, prefix='/api/v1/events', tags=['events'])

@app.get('/healthz')
async def healthz():
    from api.v1.monitor import healthz as monitor_healthz
    return await monitor_healthz()

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        log_config=LOGGING,
        log_level=logging.DEBUG,
)
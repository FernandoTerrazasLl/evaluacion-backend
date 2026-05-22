from slowapi import Limiter
from slowapi.util import get_remote_address
from core import config

limiter = Limiter(key_func=get_remote_address)

def get_rate_limit() -> str:
    return config.RATE_LIMIT


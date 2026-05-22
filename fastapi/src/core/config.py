import os
from logging import config as logging_config
from pathlib import Path
from dotenv import load_dotenv
from core.logger import LOGGING

root = Path(__file__).resolve().parents[3]
dotenv_path = root / '.env'
if dotenv_path.exists():
    load_dotenv(dotenv_path)

logging_config.dictConfig(LOGGING)
PROJECT_NAME = os.getenv('PROJECT_NAME', 'events')
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
POSTGRES_DSN = os.getenv('POSTGRES_URL', '')
RATE_LIMIT = os.getenv('RATE_LIMIT', '100/minute')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
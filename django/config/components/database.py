import os
from urllib.parse import urlparse

postgres_url = os.environ.get('POSTGRES_URL')
if postgres_url:
    url = urlparse(postgres_url)
    db_name = url.path.lstrip('/')
    db_user = url.username
    db_password = url.password
    db_host = url.hostname
    db_port = url.port or 5432
else:
    db_name = os.environ.get('DB_NAME')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')
    db_host = os.environ.get('DB_HOST', '127.0.0.1')
    db_port = os.environ.get('DB_PORT', 5432)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_name,
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': db_host,
        'PORT': int(db_port),
        'OPTIONS': {
            'options': '-c search_path=public,content'
        }
    }
}
from django.shortcuts import render
from django.http import JsonResponse
from django.db import connections
import socket

def healthz(request):
    postgres_ok = False
    try:
        db_conn = connections['default']
        with db_conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        postgres_ok = True
    except Exception:
        pass

    redis_ok = False
    try:
        s = socket.create_connection(("redis", 6379), timeout=2)
        s.close()
        redis_ok = True
    except Exception:
        pass

    status = 200 if (postgres_ok and redis_ok) else 503
    response_data = {
        "status": "healthy" if status == 200 else "unhealthy",
        "postgres": "healthy" if postgres_ok else "unhealthy",
        "redis": "healthy" if redis_ok else "unhealthy",
    }
    return JsonResponse(response_data, status=status)


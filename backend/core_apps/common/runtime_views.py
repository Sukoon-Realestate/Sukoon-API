"""Minimal dependency health for the App Platform API probe."""

from django.db import connection
from django.http import JsonResponse

from config.runtime import redis_client


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        redis_client().ping()
    except Exception:
        return JsonResponse({"ready": False}, status=503)
    return JsonResponse({"ready": True})

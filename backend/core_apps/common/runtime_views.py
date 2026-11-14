"""Minimal dependency health for the App Platform API probe."""

from django.db import connection
from django.http import JsonResponse
from django.views import View

from config.runtime import redis_client


class HealthView(View):
    """Every HTTP method retains the legacy dependency-probe response."""

    def dispatch(self, request, *args, **kwargs):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            redis_client().ping()
        except Exception:
            return JsonResponse({"ready": False}, status=503)
        return JsonResponse({"ready": True})


# Stable import for existing probe callers.
health = HealthView.as_view()

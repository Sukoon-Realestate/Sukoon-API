import time
from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import Throttled


def enforce_rate(user, operation, *, maximum=60):
    maximum = getattr(settings, "CHAT_RATE_LIMITS", {}).get(operation, maximum)
    key = f"chat-rate:{user.pk}:{operation}:{int(time.time() // 60)}"
    if cache.add(key, 1, timeout=65):
        return
    try:
        count = cache.incr(key)
    except ValueError:
        cache.add(key, 1, timeout=65)
        return
    if count > maximum:
        raise Throttled(wait=60)

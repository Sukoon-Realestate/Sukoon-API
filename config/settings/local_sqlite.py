from .local import *  # noqa
from .local import BASE_DIR, MIDDLEWARE

# * SQLite Database configuration for local standalone development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "dev.sqlite3",
    }
}

# ? In-memory channels layer to remove Redis requirement for local SQLite dev
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# * Relax cookie security for local HTTP development
COOKIE_SECURE = False
COOKIE_SAMESITE = "Lax"

# * Insert Dev CORS middleware for frontend (:3000) -> backend (:8000) requests
if "core_apps.common.cors_middleware.DevCorsMiddleware" not in MIDDLEWARE:
    MIDDLEWARE = [
        "core_apps.common.cors_middleware.DevCorsMiddleware",
        *MIDDLEWARE,
    ]

# * Allowed Hosts & CSRF
ALLOWED_HOSTS = ["*"]
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# * Console email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# * Cloudinary dummy configuration fallback if not set
import cloudinary  # noqa

if not cloudinary.config().cloud_name:
    cloudinary.config(
        cloud_name="dev_cloud",
        api_key="dev_key",
        api_secret="dev_secret",
    )

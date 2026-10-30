"""Offline demo environment. Database and media are separate from development."""
from .local_sqlite import *  # noqa: F401,F403
from .local_sqlite import BASE_DIR

DEMO_SEED_ENABLED = True
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / ".demo" / "database.sqlite3"}}
MEDIA_ROOT = BASE_DIR / ".demo" / "media"
MEDIA_URL = "/media/"
DEMO_PUBLIC_ORIGIN = "http://127.0.0.1:8010"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
CELERY_TASK_ALWAYS_EAGER = False
EVIDENCE_STORAGE_PROVIDER = "database"
SUPPORT_PRIVATE_STORAGE_PROVIDER = "local"
EVIDENCE_SCANNER_BACKEND = "fake"
RENTAL_RUNTIME_ENVIRONMENT = "development"
COMMERCE_STORE_PURCHASES_ENABLED = False
COMMERCE_STORE_ADAPTERS = {}
COMMERCE_ENTITLEMENTS_ENABLED = False
# Test accounts use the normal password hasher, not the test settings' MD5 hasher.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]

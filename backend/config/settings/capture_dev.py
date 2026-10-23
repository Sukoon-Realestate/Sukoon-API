"""Isolated local capture workbench; never use this settings module in production."""

from .local_sqlite import *  # noqa: F403
from .local_sqlite import BASE_DIR

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "capture_dev",
        "USER": "capture_dev",
        "PASSWORD": (
            (BASE_DIR / ".envs" / "property-capture-postgres-password")
            .read_text()
            .strip()
            if (BASE_DIR / ".envs" / "property-capture-postgres-password").exists()
            else ""
        ),
        "HOST": "127.0.0.1",
        "PORT": "55435",
    }
}
PROPERTY_CAPTURE_ENABLED = True
VIRTUAL_TOUR_PRIVATE_ROOT = str(BASE_DIR / "private_virtual_tours" / "capture-dev")
VIRTUAL_TOUR_STORAGE_PROVIDER = "s3"
VIRTUAL_TOUR_S3_BUCKET = ""
VIRTUAL_TOUR_PROCESSOR_MODE = "polling"
CELERY_TASK_ALWAYS_EAGER = False
SECURITY_TEST_BYPASS = False
CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:8026", "http://localhost:8026"]

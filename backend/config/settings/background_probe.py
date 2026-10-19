"""Isolated connectivity scheduling; never consumes a business queue."""

from .production import *  # noqa

DEBUG = False
RENTAL_PROVIDER_BACKEND = "disabled"
RENTAL_FAKE_PROVIDER_ALLOWED = False
RUNTIME_EVIDENCE_ENABLED = True
RUNTIME_EVIDENCE_NAMESPACE = "sokoun-background-probe"
CELERY_TASK_DEFAULT_QUEUE = "sokoun-background-probe"
CELERY_TASK_CREATE_MISSING_QUEUES = False
from kombu import Queue

CELERY_TASK_QUEUES = (Queue(CELERY_TASK_DEFAULT_QUEUE),)
CELERY_BEAT_SCHEDULE = {
    "background-connectivity-probe": {
        "task": "core_apps.common.tasks.background_probe",
        "schedule": 30.0,
        "options": {"queue": CELERY_TASK_DEFAULT_QUEUE},
    }
}

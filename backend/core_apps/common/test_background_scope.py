from unittest.mock import patch
import pytest
from celery.exceptions import Reject
from config.background import configure, AllowedTask
from config.celery import app


def test_every_registered_schedule_uses_a_real_task_name(settings):
    app.loader.import_default_modules()
    assert not [
        entry["task"]
        for entry in settings.BACKGROUND_SCHEDULE_CATALOG.values()
        if entry["task"] not in app.tasks
    ]


def test_bounded_profile_only_consumes_explicit_schedules(settings, monkeypatch):
    monkeypatch.setenv("SOKOUN_GENERAL_BACKGROUND_ENABLED", "true")
    monkeypatch.setenv("SOKOUN_BACKGROUND_SCHEDULES", "background-probe")
    scope = {"CELERY_BEAT_SCHEDULE": settings.CELERY_BEAT_SCHEDULE}
    configure(scope)
    assert set(scope["CELERY_BEAT_SCHEDULE"]) == {
        "background-probe",
        "maintain-chat",
        "purge-chat-policy",
        "maintain-support-uploads",
        "deliver-notification-push",
    }
    assert (
        scope["CELERY_BEAT_SCHEDULE"]["background-probe"]["options"]["queue"]
        == "sokoun-general"
    )
    settings.GENERAL_BACKGROUND_ENABLED = True
    settings.GENERAL_BACKGROUND_ALLOWED_TASKS = scope[
        "GENERAL_BACKGROUND_ALLOWED_TASKS"
    ]
    monkeypatch.setenv("SOKOUN_WORKER_PROFILE", "general")
    task = AllowedTask()
    task.name = "unreviewed-financial-task"
    with pytest.raises(Reject):
        task.before_start("id", (), {})
    task.name = "core_apps.common.tasks.background_probe"
    task.before_start("id", (), {})


def test_unknown_schedule_is_configuration_error(settings, monkeypatch):
    from django.core.exceptions import ImproperlyConfigured

    monkeypatch.setenv("SOKOUN_BACKGROUND_SCHEDULES", "typo")
    with pytest.raises(ImproperlyConfigured):
        configure({"CELERY_BEAT_SCHEDULE": settings.CELERY_BEAT_SCHEDULE})

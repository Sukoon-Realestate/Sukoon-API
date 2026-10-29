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
        "generate-requested-rental-statements",
        "maintain-chat",
        "purge-chat-policy",
        "maintain-support-uploads",
        "deliver-notification-push",
    }
    assert scope["CELERY_BEAT_SCHEDULE"]["background-probe"]["options"]["queue"] == "sokoun-general"
    settings.GENERAL_BACKGROUND_ENABLED = True
    settings.GENERAL_BACKGROUND_ALLOWED_TASKS = scope["GENERAL_BACKGROUND_ALLOWED_TASKS"]
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


def test_statement_schedule_admits_only_dedicated_durable_generation(settings, monkeypatch):
    monkeypatch.setenv("SOKOUN_GENERAL_BACKGROUND_ENABLED", "true")
    monkeypatch.setenv("SOKOUN_BACKGROUND_SCHEDULES", "background-probe")
    scope = {"CELERY_BEAT_SCHEDULE": settings.CELERY_BEAT_SCHEDULE}
    configure(scope)
    entry = scope["CELERY_BEAT_SCHEDULE"]["generate-requested-rental-statements"]
    assert entry["schedule"] == 10.0
    assert entry["options"] == {"queue": "sokoun-general"}
    assert (
        entry["task"]
        == "core_apps.features.tasks_parts.rental_statement_delivery.generate_requested_rental_statements"
    )
    assert set(scope["GENERAL_BACKGROUND_ALLOWED_TASKS"]) == {
        value["task"] for value in scope["CELERY_BEAT_SCHEDULE"].values()
    }
    settings.GENERAL_BACKGROUND_ENABLED = True
    settings.GENERAL_BACKGROUND_ALLOWED_TASKS = scope["GENERAL_BACKGROUND_ALLOWED_TASKS"]
    monkeypatch.setenv("SOKOUN_WORKER_PROFILE", "general")
    task = AllowedTask()
    task.name = entry["task"]
    task.before_start("statement-task", (), {})
    for name in (
        "core_apps.features.tasks_parts.process_rental_closure.process_rental_closure",
        "core_apps.features.tasks_parts.expire_rental_sources_and_holds.run_rental_billing_cycle",
        "arbitrary.generate_document",
    ):
        task.name = name
        with pytest.raises(Reject):
            task.before_start("not-admitted", (), {})


def test_standalone_profile_does_not_auto_enable_statement_maintenance(settings, monkeypatch):
    monkeypatch.setenv("SOKOUN_GENERAL_BACKGROUND_ENABLED", "false")
    monkeypatch.setenv("SOKOUN_BACKGROUND_SCHEDULES", "background-probe")
    original = {"only-original": {"task": "original.task", "schedule": 30}}
    scope = {"CELERY_BEAT_SCHEDULE": original}
    configure(scope)
    assert "generate-requested-rental-statements" in scope["BACKGROUND_SCHEDULE_CATALOG"]
    assert "generate-requested-rental-statements" not in scope["CELERY_BEAT_SCHEDULE"]
    assert scope["CELERY_BEAT_SCHEDULE"]["only-original"] == original["only-original"]

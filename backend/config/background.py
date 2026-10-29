"""Explicit task admission for the bounded general worker on the API service."""

import os
from celery import Task
from celery.exceptions import Reject
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

TASK_MODULES = {
    "expire_rental_sources_and_holds": "expire_rental_sources_and_holds",
    "reconcile_rental_provider_sessions": "expire_rental_sources_and_holds",
    "reconcile_ambiguous_rental_payments": "expire_rental_sources_and_holds",
    "process_planning_jobs": "expire_rental_sources_and_holds",
    "scan_rental_evidence": "process_rental_changes",
    "reconcile_approved_payouts": "process_rental_changes",
    "process_rental_changes": "process_rental_changes",
    "process_rental_closure": "process_rental_closure",
}


def canonical_task(name):
    leaf = name.rsplit(".", 1)[-1]
    if name == f"core_apps.features.tasks.{leaf}" and leaf in TASK_MODULES:
        return f"core_apps.features.tasks_parts.{TASK_MODULES[leaf]}.{leaf}"
    return name


def configure(scope):
    catalog = {
        name: {**value, "task": canonical_task(value["task"])}
        for name, value in scope["CELERY_BEAT_SCHEDULE"].items()
    }
    catalog["maintain-support-uploads"] = {
        "task": "core_apps.support.tasks.maintain_support_uploads",
        "schedule": 10.0,
    }
    catalog["deliver-notification-push"] = {"task": "core_apps.notifications.tasks.deliver_push", "schedule": 5.0}
    original = dict(catalog)
    catalog["background-probe"] = {
        "task": "core_apps.common.tasks.background_probe",
        "schedule": 30.0,
    }
    catalog["dispatch-admin-campaigns"] = {
        "task": "core_apps.admin_api.tasks.dispatch_campaigns",
        "schedule": 15.0,
    }
    catalog["monitor-runtime"] = {
        "task": "core_apps.common.tasks.monitor_runtime",
        "schedule": 60.0,
    }
    # These replace the existing policy-maintenance process in the combined
    # worker. They retain its mode/privacy gates and do not enable new business.
    maintenance = {
        # Only new, explicitly marked statement requests; never old private docs
        # or the financial/closure worker. The DB row survives broker outages.
        "generate-requested-rental-statements": {
            "task": "core_apps.features.tasks_parts.rental_statement_delivery.generate_requested_rental_statements",
            "schedule": 10.0,
        },
        "deliver-notification-push": catalog["deliver-notification-push"],
        "maintain-support-uploads": catalog["maintain-support-uploads"],
        "maintain-chat": {
            "task": "core_apps.common.tasks.maintain_chat",
            "schedule": (
                60.0 if scope.get("CHAT_MODERATION_MODE", "off") == "off" else 5.0
            ),
        },
        "purge-chat-policy": {
            "task": "core_apps.common.tasks.purge_chat_policy",
            "schedule": 600.0,
        },
    }
    catalog.update(maintenance)
    scope["BACKGROUND_SCHEDULE_CATALOG"] = catalog
    scope["GENERAL_BACKGROUND_ENABLED"] = (
        os.getenv("SOKOUN_GENERAL_BACKGROUND_ENABLED", "false").lower() == "true"
    )
    selected = [
        part.strip()
        for part in os.getenv(
            "SOKOUN_BACKGROUND_SCHEDULES", "background-probe,monitor-runtime"
        ).split(",")
        if part.strip()
    ]
    unknown = set(selected) - set(catalog)
    if unknown:
        raise ImproperlyConfigured(
            "Unknown background schedule names: " + ", ".join(sorted(unknown))
        )
    if scope["GENERAL_BACKGROUND_ENABLED"]:
        selected = list(dict.fromkeys([*selected, *maintenance]))
    scope["GENERAL_BACKGROUND_ALLOWED_TASKS"] = tuple(
        catalog[name]["task"] for name in selected
    )
    # Preserve existing standalone deployments unless explicitly moving to this
    # bounded profile. Its separate queue never consumes old financial backlog.
    scope["CELERY_BEAT_SCHEDULE"] = (
        original
        if not scope["GENERAL_BACKGROUND_ENABLED"]
        else {
            name: {**catalog[name], "options": {"queue": "sokoun-general"}}
            for name in selected
        }
    )
    if scope["GENERAL_BACKGROUND_ENABLED"]:
        scope["RUNTIME_EVIDENCE_ENABLED"] = True
        scope["CELERY_WORKER_PREFETCH_MULTIPLIER"] = 1
    scope["RUNTIME_METRICS_ENABLED"] = (
        os.getenv("SOKOUN_RUNTIME_METRICS_ENABLED", "false").lower() == "true"
    )


class AllowedTask(Task):
    abstract = True

    def before_start(self, task_id, args, kwargs):
        if os.getenv("SOKOUN_WORKER_PROFILE") == "general" and (
            not settings.GENERAL_BACKGROUND_ENABLED
            or self.name not in settings.GENERAL_BACKGROUND_ALLOWED_TASKS
        ):
            raise Reject("Task is outside the approved worker scope", requeue=False)
        super().before_start(task_id, args, kwargs)

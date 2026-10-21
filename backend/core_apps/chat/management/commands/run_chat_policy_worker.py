"""Run beside the API in its existing service; PostgreSQL leases allow replicas."""

import signal
import threading
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from core_apps.chat.moderation.queue import process_one
from core_apps.chat.models import (
    ChatModerationInput,
    ChatMediaAnalysis,
    ChatModerationCase,
    ChatModerationAppeal,
    ChatModerationBatch,
)


def purge():
    now = timezone.now()
    # Long outages must not retain raw model inputs indefinitely or produce
    # week-old automatic sanctions. Invalidate only leases that are no longer live.
    with transaction.atomic():
        for batch in (
            ChatModerationBatch.objects.select_for_update(skip_locked=True)
            .filter(
                created_at__lt=now - timedelta(days=7), state__in=["running", "retry"]
            )
            .filter(Q(lease_until__lte=now) | Q(lease_until__isnull=True))[:100]
        ):
            batch.state = "failed"
            batch.diagnostics = {"code": "input_expired"}
            batch.lease_token = None
            batch.save()
            ChatModerationInput.objects.filter(pk__in=batch.input_ids).update(
                state="failed", ciphertext=""
            )
        ChatModerationInput.objects.filter(
            state="pending", created_at__lt=now - timedelta(days=7)
        ).update(state="failed", ciphertext="")
    # Never remove inputs belonging to an active/retrying batch. Closed case
    # evidence has its own longer clock. Active appeals/reviews do not expire.
    ChatModerationInput.objects.filter(created_at__lt=now - timedelta(days=7)).exclude(
        state__in=["pending", "claimed"]
    ).update(ciphertext="")
    ChatMediaAnalysis.objects.filter(created_at__lt=now - timedelta(days=7)).delete()
    ChatModerationCase.objects.filter(
        state="warning",
        created_at__lt=now - timedelta(days=30),
        resolved_at__isnull=True,
    ).update(resolved_at=now)
    cases = ChatModerationCase.objects.filter(resolved_at__lt=now - timedelta(days=90))
    ChatModerationAppeal.objects.filter(case__in=cases).update(ciphertext="")
    cases.update(evidence_ciphertext="")


class Command(BaseCommand):
    help = (
        "Review dirty rental conversations; no polling of idle chats or unread counts."
    )

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        stop = threading.Event()
        for signum in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signum, lambda *_: stop.set())
        last_purge = None
        while not stop.is_set():
            close_old_connections()
            worked = process_one()
            from core_apps.chat.moderation.notifications import deliver_pending
            from core_apps.chat.services.group_outbox import drain_outbox

            deliver_pending()
            drain_outbox(limit=20)
            if last_purge is None or timezone.now() - last_purge >= timedelta(
                minutes=10
            ):
                purge()
                last_purge = timezone.now()
            if options["once"]:
                return
            from core_apps.chat.moderation.policy import mode

            stop.wait(60 if mode() == "off" else (1 if worked else 5))

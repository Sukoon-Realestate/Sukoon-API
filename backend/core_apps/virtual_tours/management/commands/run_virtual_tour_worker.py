"""Consume only tour jobs, using their existing durable, transaction-claimed outbox."""

import signal
import time

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import close_old_connections

from core_apps.virtual_tours.models import TourRevision
from core_apps.virtual_tours.processing import process_revision
from core_apps.virtual_tours.tasks import cleanup_tours, recover_interrupted_tours


class Command(BaseCommand):
    help = "Run the dedicated tour processor and hourly retention cleanup."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")
        parser.add_argument("--interval", type=float, default=5)

    def handle(self, *, once, interval, **options):
        if settings.VIRTUAL_TOUR_PROCESSOR_MODE != "polling":
            raise CommandError(
                "Set VIRTUAL_TOUR_PROCESSOR_MODE=polling on API and worker."
            )
        if interval < 1:
            raise CommandError("The poll interval must be at least one second.")
        self.stopping = False
        previous = {}
        if not once:
            for sig in (signal.SIGTERM, signal.SIGINT):
                previous[sig] = signal.signal(sig, self.stop)
        next_cleanup = 0.0
        try:
            while not self.stopping:
                close_old_connections()
                recover_interrupted_tours()
                job = (
                    TourRevision.objects.filter(processing_state="queued")
                    .order_by("updated_at")
                    .values_list("id", "source_hash")
                    .first()
                )
                if job:
                    process_revision(str(job[0]), job[1])
                    self.stdout.write("Tour job checked: " + str(job[0]))
                if time.monotonic() >= next_cleanup:
                    cleanup_tours.run()
                    next_cleanup = time.monotonic() + 3600
                if once:
                    break
                if not job:
                    time.sleep(interval)
        finally:
            close_old_connections()
            for sig, handler in previous.items():
                signal.signal(sig, handler)

    def stop(self, *_):
        self.stopping = True

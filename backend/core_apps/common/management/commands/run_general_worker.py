"""Bounded worker and leased scheduler sharing one Django process."""

import logging
import os
import signal
import threading

from celery import bootsteps
from celery.beat import Service
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from config.celery import app

logger = logging.getLogger(__name__)


class ThreadedScheduler(bootsteps.StartStopStep):
    requires = ("celery.worker.components:Pool",)

    def start(self, worker):
        self.stopping = threading.Event()
        self.service = Service(app=worker.app, scheduler_cls="config.runtime.LeaseScheduler", max_interval=5)

        def run():
            worker.app.set_current()
            try:
                self.service.start()
            except Exception as error:
                logger.error("Background scheduler stopped (%s)", type(error).__name__)
            finally:
                if not self.stopping.is_set():
                    worker.scheduler_failed = True
                    # The worker must not remain apparently healthy without
                    # scheduling. Its supervisor will restart the service.
                    os.kill(os.getpid(), signal.SIGTERM)

        self.thread = threading.Thread(target=run, name="sokoun-beat", daemon=True)
        self.thread.start()

    def stop(self, worker):
        self.stopping.set()
        self.service.stop(wait=False)
        self.thread.join(timeout=20)
        if self.thread.is_alive():
            worker.scheduler_failed = True

    terminate = stop


class Command(BaseCommand):
    help = "Run only admitted tasks with a leased scheduler, within one process."

    def handle(self, *args, **options):
        if not settings.GENERAL_BACKGROUND_ENABLED:
            raise CommandError("General background work is not enabled.")
        os.environ["SOKOUN_WORKER_PROFILE"] = "general"
        app.steps["worker"].add(ThreadedScheduler)
        worker = app.Worker(
            pool="solo", concurrency=1, prefetch_multiplier=1,
            queues=["sokoun-general"], without_gossip=True, without_mingle=True,
            loglevel="WARNING", beat=False,
        )
        worker.scheduler_failed = False
        worker.start()
        if worker.scheduler_failed or worker.exitcode:
            raise CommandError("Background service stopped before a clean shutdown.")

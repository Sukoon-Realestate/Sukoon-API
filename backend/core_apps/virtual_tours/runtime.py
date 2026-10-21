"""Opt-in tour processing within an existing ASGI service, without another process.

One thread per container may hold the file lock. Database row claims continue to
protect jobs during rolling deployments. Interrupted jobs remain in the outbox.
"""

import asyncio
import fcntl
import logging
import threading
import time

from django.conf import settings
from django.db import close_old_connections, connections

from .models import TourRevision
from .processing import process_revision
from .storage import root
from .tasks import cleanup_tours, recover_interrupted_tours

logger = logging.getLogger(__name__)


def run_processor(stop):
    next_cleanup = 0.0
    try:
        with (root().parent / ".virtual-tour-processor.lock").open("a") as lock:
            while not stop.is_set():
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    stop.wait(5)
            while not stop.is_set():
                try:
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
                        logger.info("tour_job_checked revision=%s", job[0])
                    if time.monotonic() >= next_cleanup:
                        # A provider cleanup failure must not block subsequent jobs.
                        next_cleanup = time.monotonic() + 3600
                        cleanup_tours.run()
                except Exception as exc:
                    logger.error(
                        "tour_processor_retry error_type=%s", type(exc).__name__
                    )
                stop.wait(5)
    finally:
        connections.close_all()


async def lifespan(scope, receive, send):
    stop, thread = threading.Event(), None
    try:
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                if settings.VIRTUAL_TOUR_PROCESSOR_MODE == "inline":
                    thread = threading.Thread(
                        target=run_processor,
                        args=(stop,),
                        daemon=True,
                        name="virtual-tour-processor",
                    )
                    thread.start()
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                stop.set()
                if thread:
                    await asyncio.to_thread(thread.join, 5)
                await send({"type": "lifespan.shutdown.complete"})
                return
    finally:
        stop.set()

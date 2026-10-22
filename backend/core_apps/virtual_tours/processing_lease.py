"""Fence each processing attempt and renew it only while work makes progress."""

import time

from django.utils import timezone

from .models import TourRevision


class ProcessingSuperseded(Exception):
    """Another attempt owns the revision; discard this attempt's output."""


class ProcessingLease:
    def __init__(self, revision):
        self.revision_id = revision.id
        self.source_hash = revision.source_hash
        self.token = revision.processing_token
        self.next_heartbeat = 0.0

    def heartbeat(self):
        now = time.monotonic()
        if now < self.next_heartbeat:
            return
        renewed = TourRevision.objects.filter(
            id=self.revision_id,
            source_hash=self.source_hash,
            processing_state="processing",
            processing_token=self.token,
        ).update(updated_at=timezone.now())
        if not renewed:
            raise ProcessingSuperseded
        self.next_heartbeat = now + 30

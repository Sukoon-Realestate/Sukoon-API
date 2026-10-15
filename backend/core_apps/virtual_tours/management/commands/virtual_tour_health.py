"""Aggregate operational counters without user data, paths, credentials or URLs."""

import json
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from django.utils import timezone
from core_apps.virtual_tours.models import (
    TourAsset,
    TourRevision,
    TourUploadSession,
    TourViewerSession,
)


class Command(BaseCommand):
    help = "Print aggregate tour processing, upload and retention health as JSON."

    def handle(self, **options):
        now = timezone.now()
        self.stdout.write(
            json.dumps(
                {
                    "observed_at": now.isoformat(),
                    "revision_states": list(
                        TourRevision.objects.values(
                            "processing_state", "review_state"
                        ).annotate(count=Count("pk"))
                    ),
                    "queued_over_5_minutes": TourRevision.objects.filter(
                        processing_state="queued",
                        updated_at__lt=now - timedelta(minutes=5),
                    ).count(),
                    "processing_over_20_minutes": TourRevision.objects.filter(
                        processing_state="processing",
                        updated_at__lt=now - timedelta(minutes=20),
                    ).count(),
                    "logical_source_bytes": TourAsset.objects.aggregate(
                        total=Sum("size")
                    )["total"]
                    or 0,
                    "open_uploads": TourUploadSession.objects.filter(
                        state="open", expires_at__gt=now
                    ).count(),
                    "active_sessions": TourViewerSession.objects.filter(
                        expires_at__gt=now, revoked_at__isnull=True
                    ).count(),
                },
                indent=2,
            )
        )

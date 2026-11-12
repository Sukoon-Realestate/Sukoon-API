"""Prepare active baseline compatibility before rolling back to an older reader."""

from collections import Counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from core_apps.properties.models import SavedSearchVisit, SavedSearchRead
from core_apps.properties.services.saved_search_items import materialize_legacy_baseline, retire_expired_itemized_reads


class Command(BaseCommand):
    help = "Dry-run by default; --apply materializes one bounded batch of legacy saved-search baselines."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--retire-expired-receipts", action="store_true")
        parser.add_argument("--batch-size", type=int, default=20)

    def handle(self, *args, **options):
        if not 1 <= options["batch_size"] <= 100:
            raise CommandError("--batch-size must be between 1 and 100.")
        if options["apply"] and getattr(settings, "SAVED_SEARCH_ITEMIZED_READS", False):
            raise CommandError(
                "Disable itemized creation on every API process and drain live read receipts before applying."
            )
        rows = (
            SavedSearchVisit.objects.filter(acknowledged_read__isnull=False)
            .select_related("acknowledged_read")
            .order_by("pk")[: options["batch_size"]]
        )
        result = Counter(materialize_legacy_baseline(row, apply=options["apply"]) for row in rows)
        if options["retire_expired_receipts"] and options["apply"]:
            result["retired_receipts"] = retire_expired_itemized_reads(options["batch_size"])
        result["baselines_remaining"] = SavedSearchVisit.objects.filter(acknowledged_read__isnull=False).count()
        result["itemized_receipts_remaining"] = SavedSearchRead.objects.filter(itemized=True).count()
        self.stdout.write(str(dict(result)))

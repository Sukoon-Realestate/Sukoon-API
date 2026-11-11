"""Create catalog intents explicitly for specified historical leases."""

from django.core.management.base import BaseCommand
from django.db import transaction
from core_apps.features.models import Lease
from core_apps.features.services.document_intents import backfill


class Command(BaseCommand):
    help = "Idempotently backfill rental document catalog intents for explicit lease UUIDs."

    def add_arguments(self, parser):
        parser.add_argument("lease_ids", nargs="+")

    def handle(self, *args, **options):
        for identity in options["lease_ids"]:
            with transaction.atomic():
                lease = Lease.objects.select_for_update().get(id=identity)
                backfill(lease)
            self.stdout.write(f"Document intents recorded for {identity}")

"""Read-only candidate inspection is the default; dispatch requires --execute."""

import json
from django.core.management.base import BaseCommand
from core_apps.features.services.rent_payment_reminders import record_reminders


class Command(BaseCommand):
    help = "Inspect current rent reminder candidates without sending; --execute runs the bounded job."

    def add_arguments(self, parser):
        modes = parser.add_mutually_exclusive_group()
        modes.add_argument("--dry-run", action="store_true")
        modes.add_argument("--execute", action="store_true")

    def handle(self, *args, **options):
        if options["execute"]:
            from core_apps.features.tasks import process_rent_payment_notifications

            result = process_rent_payment_notifications()
        else:
            result = record_reminders(dry_run=True)
        self.stdout.write(json.dumps(result, indent=2))

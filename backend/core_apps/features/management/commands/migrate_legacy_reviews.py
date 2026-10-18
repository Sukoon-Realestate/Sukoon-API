from django.core.management.base import BaseCommand
from django.db import transaction
from core_apps.features.services.reputation.legacy import migrate_legacy


class Command(BaseCommand):
    help = "Import legacy reviews without verifying, relabeling or enlarging their audience. Safe to rerun."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(str(migrate_legacy()))
        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write("Dry run: all database changes rolled back.")

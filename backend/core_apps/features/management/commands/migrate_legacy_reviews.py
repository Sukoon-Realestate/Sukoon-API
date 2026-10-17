from django.core.management.base import BaseCommand
from core_apps.features.services.reputation.legacy import migrate_legacy


class Command(BaseCommand):
    help = "Import legacy reviews without verifying, relabeling or enlarging their audience. Safe to rerun."

    def handle(self, *args, **options):
        self.stdout.write(str(migrate_legacy()))

from django.core.management.base import BaseCommand
from core_apps.features.services.living_lab.retention import purge_due


class Command(BaseCommand):
    help = (
        "Purge expired private living-lab inputs and uncommitted outputs while "
        "retaining accepted records and operation receipts."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(f"Purged {purge_due()} living labs."))

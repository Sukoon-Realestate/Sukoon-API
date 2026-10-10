from django.core.management.base import BaseCommand

from core_apps.advertising.tasks import expire_advertisements


class Command(BaseCommand):
    help = "Persist the expired status for advertisements past their end time."

    def handle(self, *args, **options):
        count = expire_advertisements()
        self.stdout.write(self.style.SUCCESS(f"Expired {count} advertisement(s)."))

from django.core.management.base import BaseCommand
from core_apps.features.services.reputation.tasks import reconcile


class Command(BaseCommand):
    help = "Reconcile recent eligible review sources, fixed gates, reminders and expired drafts."

    def handle(self, *args, **options):
        self.stdout.write(str(reconcile()))

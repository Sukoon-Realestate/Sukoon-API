from django.core.management.base import BaseCommand
from core_apps.features.planning_models import HousingGroup
from core_apps.chat.services.group_provisioning import provision_group


class Command(BaseCommand):
    help = "Idempotently provision canonical chats for existing active housing groups."

    def handle(self, *args, **options):
        count = 0
        for group in HousingGroup.objects.filter(status="active").iterator():
            provision_group(group)
            count += 1
        self.stdout.write(
            self.style.SUCCESS(f"Reconciled {count} group conversations.")
        )

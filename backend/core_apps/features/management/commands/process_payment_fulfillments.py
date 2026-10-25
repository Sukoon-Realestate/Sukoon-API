from django.core.management.base import BaseCommand
from core_apps.features.models import PaymentFulfillment
from core_apps.features.services.payment_fulfillment import deliver


class Command(BaseCommand):
    help = "Retry pending paid service delivery without collecting money."

    def handle(self, *args, **options):
        identities = list(
            PaymentFulfillment.objects.filter(status="pending")
            .order_by("updated_at")
            .values_list("pk", flat=True)[:100]
        )
        for identity in identities:
            deliver(identity)
        self.stdout.write(f"Processed {len(identities)} fulfillment records")

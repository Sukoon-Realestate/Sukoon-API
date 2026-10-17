"""Install the explicitly selected simulation policy without touching live data."""

from django.core.management.base import BaseCommand, CommandError
from config.advanced_housing import POLICY_VERSION, mock_mode_available
from core_apps.features.models import RentalCommercialPolicy


class Command(BaseCommand):
    help = "Install the versioned advanced mock commercial policy idempotently."

    def handle(self, *args, **options):
        if not mock_mode_available():
            raise CommandError(
                "This command requires the explicit advanced mock environment."
            )
        rules = {
            "approved": True,
            "reservations": True,
            "application_sharing": True,
            "independent_group_booking": True,
            "hold_minutes": 30,
            "max_extensions": 1,
            "max_active_holds": 10,
            "availability_hours": 24,
            "turnover_days": 1,
            "reconciliation_minutes": 30,
            "max_booking_days": 1096,
            "share_days": 7,
            "case_hours": 24,
        }
        policy, created = RentalCommercialPolicy.objects.get_or_create(
            version=POLICY_VERSION,
            defaults={
                "lifecycle_rules": rules,
                "summary": {
                    "en": "Simulation policy. No real payment or legally effective signature.",
                    "ar": "سياسة محاكاة. لا ينتج عنها دفع فعلي أو توقيع نافذ قانونًا.",
                },
            },
        )
        if policy.lifecycle_rules != rules or not policy.is_active:
            raise CommandError(
                "The existing version differs; create a reviewed new version instead."
            )
        self.stdout.write(
            f"{POLICY_VERSION}: {'created' if created else 'already configured'} (mock)"
        )

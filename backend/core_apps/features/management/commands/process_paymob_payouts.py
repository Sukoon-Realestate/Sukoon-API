from django.core.management.base import BaseCommand
from core_apps.features.services.paymob_payouts import process_pending


class Command(BaseCommand):
    help = "Dispatch approved staging payouts once and inquire about original unknown transfers."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        result = process_pending(limit=options["limit"])
        self.stdout.write(
            f"Paid: {result['paid']}; pending: {result['pending']}; unavailable: {result['unavailable']}."
        )

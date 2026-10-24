from django.core.management.base import BaseCommand
from rest_framework.exceptions import APIException
from core_apps.features.models import PaymobRefund
from core_apps.features.services.paymob_refunds import process


class Command(BaseCommand):
    help = (
        "Dispatch queued Paymob refunds once and reconcile their original transactions."
    )

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument(
            "--refund-id", help="Public refund UUID for a specific original operation."
        )
        parser.add_argument(
            "--provider-transaction-id",
            help="Recover an unknown submission by querying this original Paymob refund transaction.",
        )

    def handle(self, *args, **options):
        query = PaymobRefund.objects.exclude(refund__status="succeeded")
        if options.get("refund_id"):
            query = query.filter(refund__id=options["refund_id"])
        if options.get("provider_transaction_id"):
            from django.core.management.base import CommandError
            import re

            if not options.get("refund_id") or not re.fullmatch(
                r"[0-9]{1,18}", options["provider_transaction_id"]
            ):
                raise CommandError(
                    "An original refund UUID and numeric provider transaction ID are required."
                )
            # Supplying an ID never grants success; the provider inquiry must
            # verify parent capture, order, environment, amount and status.
            query.filter(status__in=["unknown", "submitting"]).update(
                provider_transaction_id=options["provider_transaction_id"],
                status="processing",
            )
        checked = pending = 0
        for item in query.order_by("pkid")[: max(1, min(options["limit"], 1000))]:
            try:
                process(item)
                checked += 1
            except APIException:
                pending += 1
        self.stdout.write(
            f"Checked: {checked}; unresolved: {pending}. Unknown submissions were not retried."
        )

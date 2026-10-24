"""Recover original Paymob operations; never create or retry a charge."""

from django.core.management.base import BaseCommand
from rest_framework.exceptions import APIException
from core_apps.features.models import PaymobPayment
from core_apps.features.services.paymob_payments import reconcile


class Command(BaseCommand):
    help = "Query unresolved Paymob payments using their original references. Does not create intentions."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        limit = max(1, min(options["limit"], 1000))
        checked = pending = 0
        for payment in (
            PaymobPayment.objects.exclude(status="captured")
            .select_related("attempt__invoice")
            .order_by("reconciled_at", "pkid")[:limit]
        ):
            try:
                reconcile(payment)
                checked += 1
            except APIException:
                pending += 1
        self.stdout.write(
            f"Reconciled: {checked}; unresolved: {pending}. No new checkout was submitted."
        )

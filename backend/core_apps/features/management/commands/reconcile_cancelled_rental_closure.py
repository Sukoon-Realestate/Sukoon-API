"""Explicit repair of historical clean cancellations; GET never repairs rows."""

from django.core.management.base import BaseCommand
from django.db import transaction

from core_apps.features.models import Lease
from core_apps.features.services.rental_phase6 import (
    closure_blocking_reasons,
    evaluate_financial_closure,
)


class Command(BaseCommand):
    help = "Dry-run closure of cancelled, never occupied rentals with no blockers."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--lease-id", type=str)

    def handle(self, *args, **options):
        candidates = Lease.objects.filter(
            status=Lease.Status.CANCELLED,
            occupancy_status=Lease.OccupancyStatus.NOT_STARTED,
            financial_closure_status=Lease.FinancialClosureStatus.OPEN,
        )
        if options["lease_id"]:
            candidates = candidates.filter(id=options["lease_id"])
        eligible = blocked = 0
        for candidate_id in candidates.values_list("pk", flat=True).iterator():
            with transaction.atomic():
                lease = Lease.objects.select_for_update().get(pk=candidate_id)
                reasons = closure_blocking_reasons(lease)
                if reasons:
                    blocked += 1
                    self.stdout.write(f"blocked {lease.id}: {'; '.join(reasons)}")
                    continue
                eligible += 1
                if options["apply"]:
                    evaluate_financial_closure(lease)
                self.stdout.write(
                    f"{'closed' if options['apply'] else 'eligible'} {lease.id}"
                )
        self.stdout.write(
            f"mode={'apply' if options['apply'] else 'dry-run'} eligible={eligible} blocked={blocked}"
        )

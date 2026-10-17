"""Copy only ancestry already present in original contract or handover records."""

from django.core.management.base import BaseCommand
from django.db import transaction
from core_apps.features.models import RentalHandover, ReviewCase
from core_apps.features.services.reputation.ancestry import from_snapshot, for_stay


class Command(BaseCommand):
    help = "Freeze known original ancestry for existing stays. Unknown history stays unknown."

    def handle(self, **options):
        handovers = cases = unknown = 0
        for source in RentalHandover.objects.filter(
            kind="move_in", status="accepted", context_snapshot={}
        ):
            with transaction.atomic():
                item = RentalHandover.objects.select_for_update().get(pk=source.pk)
                if item.context_snapshot:
                    continue
                snapshot = from_snapshot(item.lease.offer_snapshot, item.lease.property)
                if snapshot["basis"] == "historical_ancestry_unavailable":
                    unknown += 1
                    continue
                item.context_snapshot = snapshot
                item.save(update_fields=["context_snapshot", "updated_at"])
                handovers += 1
        for source in ReviewCase.objects.filter(
            context_type="tenancy", employee_assignment__isnull=True
        ):
            with transaction.atomic():
                case = ReviewCase.objects.select_for_update().get(pk=source.pk)
                snap = case.source_snapshot
                if (
                    snap.get("building_id")
                    or snap.get("complex_id")
                    or not snap.get("move_in_id")
                ):
                    continue
                start = RentalHandover.objects.filter(
                    id=snap["move_in_id"],
                    lease__tenancy_root_id=case.lease.tenancy_root_id,
                ).first()
                if not start:
                    continue
                ancestry = for_stay(start)
                if ancestry.get("basis") == "historical_ancestry_unavailable":
                    continue
                case.source_snapshot = {**snap, **ancestry}
                case.save(update_fields=["source_snapshot", "updated_at"])
                cases += 1
        self.stdout.write(
            f"Frozen handovers: {handovers}; updated cases: {cases}; unknown history: {unknown}"
        )

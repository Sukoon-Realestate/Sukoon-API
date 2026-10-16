"""Report legacy allocations and convert only unambiguous roots under a lock."""

import json
from django.core.management.base import BaseCommand
from django.db import transaction
from core_apps.properties.models import Property
from core_apps.features.models import RentalInventoryDayLock
from core_apps.features.services.rental_lifecycle.inventory import (
    ensure_units,
    unit_keys,
)
from core_apps.features.services.rental_lifecycle.cases import open_system_case
from core_apps.features.services.rental_phase2 import RentalConflict


class Command(BaseCommand):
    help = "Audit legacy physical allocations; --apply converts only complete, unambiguous property roots."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--property-id")

    def handle(self, *args, **options):
        roots = Property.objects.filter(
            rental_day_locks__unit__isnull=True, rental_day_locks__isnull=False
        ).distinct()
        if options["property_id"]:
            roots = roots.filter(id=options["property_id"])
        report = {
            "mode": "apply" if options["apply"] else "report",
            "eligible_properties": [],
            "converted_properties": [],
            "review_required": [],
        }
        for identifier in roots.order_by("pk").values_list("pk", flat=True):
            with transaction.atomic():
                prop = Property.objects.select_for_update().get(pk=identifier)
                rows = list(prop.rental_day_locks.select_related("lease", "hold"))
                claims, expansion, problem = set(), [], False
                for row in rows:
                    if row.unit_id:
                        keys = [row.unit.physical_key]
                    elif row.lease and row.lease.offer_snapshot:
                        try:
                            keys = unit_keys(prop, row.lease.offer_snapshot)
                        except RentalConflict:
                            problem = True
                            break
                    else:
                        problem = True
                        break
                    for key in keys:
                        identity = (key, row.stay_on)
                        if identity in claims:
                            problem = True
                        claims.add(identity)
                    if not row.unit_id:
                        expansion.append((row, keys))
                if problem:
                    report["review_required"].append(str(prop.id))
                    if options["apply"]:
                        item = open_system_case(
                            kind="inventory_conflict",
                            source_key=f"inventory-migration:{prop.id}",
                            reason="Historical allocations need a reviewed physical map. Existing blocks are retained.",
                            next_action="Resolve the historical selection before enabling new reservations.",
                        )
                        item.property = prop
                        item.save(update_fields=["property", "updated_at"])
                    continue
                if options["apply"]:
                    for row, keys in expansion:
                        units = ensure_units(prop, row.lease.offer_snapshot)
                        row.unit = units[0]
                        row.save(update_fields=["unit", "updated_at"])
                        for unit in units[1:]:
                            RentalInventoryDayLock.objects.create(
                                property=prop,
                                unit=unit,
                                lease=row.lease,
                                hold=row.hold,
                                offer_id=row.offer_id,
                                stay_on=row.stay_on,
                                kind=row.kind,
                                expires_at=row.expires_at,
                            )
                report["eligible_properties"].append(str(prop.id))
                if options["apply"]:
                    report["converted_properties"].append(str(prop.id))
        self.stdout.write(json.dumps(report, sort_keys=True))

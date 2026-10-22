"""Validate reviewed academic catalog data before an explicit, atomic import.

Universities and campuses are separate manifests. Campuses refer to existing
university/city UUIDs; this tool never guesses geography from display names.
"""
import hashlib
import json
import uuid
from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from rest_framework.exceptions import PermissionDenied
from core_apps.admin_api.models import StaffProfile
from core_apps.admin_api.permissions import require_staff_actor
from core_apps.common.idempotency import fingerprint
from core_apps.common.management.commands.audit_release_catalog import https_destination
from core_apps.features.models import RentalAuditEvent
from core_apps.features.student_models import University, Campus
from core_apps.properties.models import City
from core_apps.users.models import User

COMMON = {"name_ar", "name_en", "active", "source_url", "checked_on"}
CAMPUS = {"university_id", "city_id", "latitude", "longitude"}


def state(row):
    if row is None:
        return "absent"
    values = {name: getattr(row, name) for name in COMMON}
    if isinstance(row, Campus):
        values.update(university_id=str(row.university.id), city_id=str(row.city.id),
            latitude=str(row.latitude) if row.latitude is not None else None,
            longitude=str(row.longitude) if row.longitude is not None else None)
    return fingerprint(values)


class Command(BaseCommand):
    help = "Validate approved academic catalog JSON; --apply requires its exact hash and a current system owner."

    def add_arguments(self, parser):
        parser.add_argument("--manifest", required=True)
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--manifest-sha256")
        parser.add_argument("--reviewer-id")
        parser.add_argument("--reason")

    def handle(self, **options):
        path = Path(options["manifest"])
        if not path.is_file() or path.stat().st_size > 2 * 1024**2:
            raise CommandError("Use a JSON manifest up to 2 MiB.")
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        try:
            manifest = json.loads(raw)
            if (set(manifest) != {"version", "kind", "records"} or manifest["version"] != 1
                or manifest["kind"] not in {"university", "campus"}
                or not isinstance(manifest["records"], list) or not 1 <= len(manifest["records"]) <= 500):
                raise ValueError()
        except (ValueError, TypeError):
            raise CommandError("Expected version 1, kind university/campus and 1–500 records.")
        apply = options["apply"]
        if apply and (options["manifest_sha256"] != digest or not options["reviewer_id"] or not (options["reason"] or "").strip()):
            raise CommandError("Review the exact manifest hash, then supply reviewer and reason.")
        model = University if manifest["kind"] == "university" else Campus
        fields = COMMON | (CAMPUS if model is Campus else set())
        identities = set()
        prepared, report = [], []
        with transaction.atomic():
            actor = None
            if apply:
                try:
                    actor = User.objects.select_for_update().get(id=options["reviewer_id"])
                    require_staff_actor(actor, {StaffProfile.RoleName.SYSTEM_OWNER}, lock=True)
                except (User.DoesNotExist, ValidationError, ValueError, PermissionDenied):
                    raise CommandError("A current authorized system owner is required. Nothing applied.")
            for index, record in enumerate(manifest["records"]):
                try:
                    if not isinstance(record, dict) or set(record) - {"id", "expected_state", "values"}:
                        raise ValueError()
                    identity = uuid.UUID(record["id"])
                    if identity in identities: raise ValueError()
                    identities.add(identity)
                    values = record["values"]
                    if not isinstance(values, dict) or set(values) != fields: raise ValueError()
                    if (not isinstance(values["active"], bool)
                        or not all(isinstance(values[n], str) and values[n].strip() for n in ("name_ar", "name_en"))
                        or not isinstance(values["source_url"], str) or not https_destination(values["source_url"])
                        or date.fromisoformat(values["checked_on"]) > date.today()):
                        raise ValueError()
                    query = model.objects.select_for_update() if apply else model.objects
                    previous = query.filter(id=identity).first()
                    expected = state(previous)
                    if apply and record.get("expected_state") != expected:
                        raise CommandError(f"Record {index}: state changed or not reviewed. Recreate the report.")
                    row = model(id=identity) if previous is None else previous
                    for name in COMMON:
                        setattr(row, name, values[name])
                    if model is Campus:
                        # Exact catalog identities only; nullable coordinates stay unknown.
                        row.university = University.objects.get(id=uuid.UUID(values["university_id"]))
                        row.city = City.objects.get(id=uuid.UUID(values["city_id"]))
                        row.latitude, row.longitude = values["latitude"], values["longitude"]
                    row.full_clean()
                    prepared.append(row)
                    report.append({"id": str(identity), "expected_state": expected,
                        "action": "create" if previous is None else "update",
                        "coordinates_known": model is Campus and row.latitude is not None})
                except (ValueError, TypeError, KeyError, ValidationError, University.DoesNotExist, City.DoesNotExist):
                    raise CommandError(f"Record {index}: invalid fields, provenance, coordinates or catalog identity. Nothing applied.")
            if apply:
                for row in prepared:
                    row.save()
                RentalAuditEvent.objects.create(actor=actor, subject_kind="academic_catalog_import",
                    subject_id=uuid.uuid5(uuid.NAMESPACE_URL, f"sokoun:academic-catalog:{digest}"),
                    subject_revision=1, action="catalog.import", reason=options["reason"],
                    metadata={"manifest_sha256": digest, "kind": manifest["kind"], "count": len(prepared)})
        self.stdout.write(json.dumps({"applied": apply, "manifest_sha256": digest, "records": report}, sort_keys=True))

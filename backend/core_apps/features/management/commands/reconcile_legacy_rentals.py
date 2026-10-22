import json
from core_apps.common.idempotency import fingerprint
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from uuid import UUID

from core_apps.features.models import Lease


class Command(BaseCommand):
    help = "Conservatively classify unsupported historical rentals without inventing financial facts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true", help="Persist read-only classifications."
        )
        parser.add_argument("--lease-id", type=UUID, help="Inspect one reviewed lease.")
        parser.add_argument("--expected-revision", type=int)
        parser.add_argument("--expected-digest")
        parser.add_argument("--reason")
        parser.add_argument("--json", action="store_true")

    @staticmethod
    def supported_at_current_stage(lease):
        terms = lease.terms
        structured = bool(
            isinstance(terms, dict)
            and terms.get("policy_version") == "rental-policy-v1"
            and lease.offer_id
        )
        # The canonical creation path saves a structured draft before producing
        # a signing document. Its absent document is not a historical defect.
        return structured and bool(
            lease.status == Lease.Status.DRAFT
            or (lease.document_id and lease.document_hash)
        )

    @staticmethod
    def digest(lease):
        return fingerprint({key: getattr(lease, key) for key in (
            "revision", "status", "occupancy_status", "terms", "offer_id", "offer_snapshot",
            "policy_version", "document_id", "document_hash", "legacy_read_only", "rent_amount_minor",
        )})

    def handle(self, *args, **options):
        if options["apply"] and (not options["lease_id"] or options["expected_revision"] is None or not options["expected_digest"] or not options["reason"]):
            raise CommandError("Apply requires one reviewed lease, expected revision, expected digest, and reason.")
        candidates = Lease.objects.all()
        if options["lease_id"]:
            candidates = candidates.filter(id=options["lease_id"])
        unsupported = classified = 0
        identifiers = list(candidates.order_by("pk").values_list("pk", flat=True))
        for identifier in identifiers:
            with transaction.atomic():
                # Re-evaluate the current snapshot under the same row lock as
                # lease transitions; a stale audit cannot classify a repaired row.
                current = (
                    Lease.objects.select_for_update()
                    if options["apply"]
                    else Lease.objects
                )
                lease = current.get(pk=identifier)
                digest = self.digest(lease)
                if options["json"]:
                    self.stdout.write(json.dumps({"lease_id": str(lease.id), "expected_revision": lease.revision, "expected_digest": digest, "supported": self.supported_at_current_stage(lease), "read_only": lease.legacy_read_only}))
                if options["apply"] and (lease.revision != options["expected_revision"] or digest != options["expected_digest"]):
                    raise CommandError("Lease changed since review; classify only a fresh reviewed snapshot.")
                if lease.legacy_read_only or self.supported_at_current_stage(lease):
                    continue
                unsupported += 1
                if options["apply"]:
                    lease.legacy_read_only = True
                    lease.revision += 1
                    lease.save(
                        update_fields=["legacy_read_only", "revision", "updated_at"]
                    )
                    from core_apps.features.models import RentalAuditEvent
                    RentalAuditEvent.objects.create(subject_kind="legacy_lease", subject_id=lease.id,
                        subject_revision=lease.revision, action="lease.legacy_classified", reason=options["reason"], metadata={"before_digest": digest})
                    classified += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"classified={classified} "
                f"would_classify={unsupported} preserved_ids=true invented_financial_facts=false"
            )
        )

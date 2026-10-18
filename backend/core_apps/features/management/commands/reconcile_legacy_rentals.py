from django.core.management.base import BaseCommand
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

    def handle(self, *args, **options):
        candidates = Lease.objects.filter(legacy_read_only=False)
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
                if lease.legacy_read_only or self.supported_at_current_stage(lease):
                    continue
                unsupported += 1
                if options["apply"]:
                    lease.legacy_read_only = True
                    lease.revision += 1
                    lease.save(
                        update_fields=["legacy_read_only", "revision", "updated_at"]
                    )
                    classified += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"classified={classified} "
                f"would_classify={unsupported} preserved_ids=true invented_financial_facts=false"
            )
        )

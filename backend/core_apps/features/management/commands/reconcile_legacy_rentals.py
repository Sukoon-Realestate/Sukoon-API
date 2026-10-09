from django.core.management.base import BaseCommand
from django.db import transaction

from core_apps.features.models import Lease


class Command(BaseCommand):
    help = "Conservatively classify unsupported historical rentals without inventing financial facts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply", action="store_true", help="Persist read-only classifications."
        )

    def handle(self, *args, **options):
        candidates = Lease.objects.filter(legacy_read_only=False)
        unsupported = []
        for lease in candidates.iterator():
            complete = bool(
                lease.terms
                and lease.terms.get("policy_version") == "rental-policy-v1"
                and lease.offer_id
                and lease.document_id
                and lease.document_hash
            )
            if not complete:
                unsupported.append(lease.pk)
        if options["apply"] and unsupported:
            with transaction.atomic():
                Lease.objects.filter(pk__in=unsupported).update(legacy_read_only=True)
        self.stdout.write(
            self.style.SUCCESS(
                f"classified={len(unsupported) if options['apply'] else 0} "
                f"would_classify={len(unsupported)} preserved_ids=true invented_financial_facts=false"
            )
        )

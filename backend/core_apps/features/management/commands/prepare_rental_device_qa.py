"""Local prerequisites, not evidence of contract authoring or a funded tenancy."""

import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core_apps.features.management.cycle_qa import (
    prepare_cycle_run,
    write_private_json,
    agreement_terms,
)
from core_apps.features.models import Lease
from core_apps.features.providers import fake_provider_available
from core_apps.features.services.rental_phase2 import reserve_inventory_days
from core_apps.properties.models import Property
from core_apps.users.models import User


class Command(BaseCommand):
    help = "Prepare a fresh signing-ready lease for native mock signature/payment QA."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1/")

    @transaction.atomic
    def handle(self, *args, **options):
        if (
            getattr(settings, "RENTAL_RUNTIME_ENVIRONMENT", "production")
            not in {
                "development",
                "test",
            }
            or not getattr(settings, "OWNER_TENANT_QA_ENABLED", False)
            or not fake_provider_available()
        ):
            raise CommandError("Explicit local/test QA settings are required.")
        base = urlsplit(options["base_url"])
        if (
            base.scheme != "http"
            or base.hostname != "127.0.0.1"
            or base.path != "/api/v1/"
            or base.username
            or base.query
            or base.fragment
        ):
            raise CommandError("Use an isolated loopback HTTP API.")
        output = Path(options["output"])
        if output.exists() or output.is_symlink():
            raise CommandError("Use a fresh private output path.")
        run = "device-" + uuid.uuid4().hex[:12]
        with tempfile.TemporaryDirectory(prefix="rental-device-qa-") as directory:
            import json

            credentials = Path(directory) / "actors.json"
            manifest = prepare_cycle_run(run, str(credentials))
            actors = json.loads(credentials.read_text())["actors"]
        owner = User.objects.get(id=actors["owner_a"]["id"])
        tenant = User.objects.get(id=actors["tenant_a"]["id"])
        branch = manifest["structured"]
        prop = Property.objects.get(id=branch["property_id"])
        start = timezone.localdate() + timedelta(days=10)
        end = start + timedelta(days=60)
        # This test begins at signatures. Owner A's beneficiary is a known
        # prerequisite; owner B's onboarding is executed through the native UI.
        from core_apps.features.models import OwnerPaymentProfile

        profile = OwnerPaymentProfile.objects.get(owner=owner)
        profile.status = "ready"
        profile.provider = "fake"
        profile.provider_account_id = f"local-qa-{run}"
        profile.payout_ready = True
        profile.accepted_policy_versions = ["rental-policy-v1"]
        profile.save()
        terms = agreement_terms(start, end, 1000000)
        lease = Lease.objects.create(
            property=prop,
            owner=owner,
            tenant=tenant,
            offer_id=branch["offer_id"],
            offer_snapshot={
                "rental_scope": "entire_property",
                "offer_id": branch["offer_id"],
            },
            template_id="eg-residential-v1",
            template_version="1",
            start_date=start,
            end_date=end,
            rent_amount_minor=1000000,
            status=Lease.Status.PENDING_SIGNATURES,
            legacy_read_only=False,
            terms=terms,
            policy_version="rental-policy-v1",
            document_id=uuid.uuid4(),
            document_hash="a" * 64,
            hold_expires_at=timezone.now() + timedelta(minutes=30),
        )
        reserve_inventory_days(lease, start, end, lease.hold_expires_at)
        write_private_json(
            output,
            {
                "base_url": options["base_url"],
                "actors": actors,
                "lease_id": str(lease.id),
                "prerequisites": "Seeded signing-ready lease and owner A beneficiary; no signatures/invoice/payment seeded",
            },
        )
        self.stdout.write(
            "Prepared isolated signing prerequisites; credentials are in the private file."
        )

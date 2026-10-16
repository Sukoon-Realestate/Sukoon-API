"""Install an append-only reviewed lifecycle policy; dry-run unless --apply."""

import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core_apps.features.models import RentalCommercialPolicy
from core_apps.features.services.rental_lifecycle.common import validate_lifecycle_rules
from core_apps.features.services.rental_phase2 import RentalConflict


class Command(BaseCommand):
    help = "Validate a reviewed policy file, preserving the named base policy fees. Use --apply to install a new version."

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        try:
            value = json.loads(Path(options["input"]).read_text())
        except (OSError, ValueError) as error:
            raise CommandError("Provide a readable JSON policy file.") from error
        if (
            not isinstance(value, dict)
            or set(value) != {"version", "base_policy_version", "lifecycle_rules"}
            or not isinstance(value["version"], str)
            or not 1 <= len(value["version"]) <= 40
            or not isinstance(value["base_policy_version"], str)
        ):
            raise CommandError(
                "Expected version, base_policy_version and lifecycle_rules."
            )
        rules = value["lifecycle_rules"]
        if (
            not isinstance(rules, dict)
            or not isinstance(rules.get("approval_reference"), str)
            or not rules["approval_reference"].strip()
        ):
            raise CommandError(
                "Record the actual policy review reference; this command does not grant legal or operational approval."
            )
        try:
            validate_lifecycle_rules(rules)
        except RentalConflict as error:
            raise CommandError(str(error.detail)) from error
        with transaction.atomic():
            base = RentalCommercialPolicy.objects.filter(
                version=value["base_policy_version"], is_active=True
            ).first()
            if not base:
                raise CommandError(
                    "The active base commercial policy must already exist."
                )
            if RentalCommercialPolicy.objects.filter(version=value["version"]).exists():
                raise CommandError(
                    "Policy versions are immutable. Choose a new reviewed version."
                )
            fields = (
                "commission_rate_bps",
                "commission_payer",
                "commission_basis",
                "processing_fee_payer",
                "renewal_commission_rate_bps",
                "timezone",
                "billing_cycle",
                "currency",
                "exponent",
                "summary",
            )
            item = RentalCommercialPolicy.objects.create(
                version=value["version"],
                lifecycle_rules=rules,
                **{name: getattr(base, name) for name in fields}
            )
            self.stdout.write(
                json.dumps(
                    {
                        "version": item.version,
                        "base_policy_version": base.version,
                        "mode": "installed" if options["apply"] else "validated_only",
                        "activation": "Set RENTAL_LIFECYCLE_POLICY_VERSION only after deployment checks.",
                    }
                )
            )
            if not options["apply"]:
                transaction.set_rollback(True)

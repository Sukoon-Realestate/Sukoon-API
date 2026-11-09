"""A1-01: read-only report of profile media without an upload receipt.

Lists, without changing anything, stored profile references that no ProfileMediaUpload
proves were uploaded by their account, references shared by several accounts, and
closure erasures held for unverified provenance. Use the output to decide, per asset,
whether to record a receipt (after confirming ownership out of band) or leave it held.
"""

import json
from collections import defaultdict

from django.core.management.base import BaseCommand

FIELDS = ("avatar", "id_face", "id_back", "confirmation_selfi")


class Command(BaseCommand):
    help = "Report profile media lacking upload provenance (read-only)."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")

    def handle(self, *args, **options):
        from core_apps.profiles.models import Profile, ProfileMediaUpload
        from core_apps.users.models import AccountProfileErasureFile

        receipts = set(ProfileMediaUpload.objects.values_list("user_id", "public_id"))
        owners = defaultdict(set)
        unproven = []
        for row in Profile.objects.values("user_id", *FIELDS).iterator():
            for field in FIELDS:
                value = row[field]
                if not value:
                    continue
                public_id = _public_id(value)
                owners[public_id].add(row["user_id"])
                if (row["user_id"], public_id) not in receipts:
                    unproven.append({"user_id": row["user_id"], "field": field, "public_id": public_id})
        report = {
            "unproven_references": len(unproven),
            "shared_references": sorted(p for p, users in owners.items() if len(users) > 1),
            "held_erasures": AccountProfileErasureFile.objects.filter(
                deleted_at__isnull=True
            ).exclude(held_reason="").count(),
            "unproven": unproven,
        }
        if options["json"]:
            self.stdout.write(json.dumps(report, indent=2, default=str))
            return
        self.stdout.write(
            f"unproven references: {report['unproven_references']}; "
            f"shared references: {len(report['shared_references'])}; "
            f"held erasures: {report['held_erasures']}"
        )


def _public_id(value):
    from cloudinary.models import CloudinaryField

    asset = CloudinaryField().to_python(value)
    return str(getattr(asset, "public_id", None) or value)

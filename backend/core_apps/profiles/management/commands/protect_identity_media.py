"""Plan/convert only canonical legacy identity assets; retain a private checkpoint.

No user verification flag, KYC decision, legal or financial record is changed.
Run without --apply first. The manifest must be retained outside an ephemeral
application instance before applying. Existing versioned KYC evidence is left
for a separately reviewed conversion, never rewritten to manufacture a digest.
"""

import hashlib
import json
import os
from pathlib import Path
import cloudinary.api
import cloudinary.uploader
from cloudinary import CloudinaryResource
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from cloudinary.models import CloudinaryField
from core_apps.profiles.identity_media import IDENTITY_FIELDS, reference
from core_apps.profiles.models import Profile


def checkpoint(path, manifest):
    temporary = path.with_suffix(".pending")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        json.dump(manifest, stream, sort_keys=True, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def key(value):
    return (value.resource_type, value.type, value.public_id)


class Command(BaseCommand):
    help = "Audit legacy public identity storage, or apply a resumable authenticated-delivery conversion."

    def add_arguments(self, parser):
        parser.add_argument("--manifest", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        original_path = Path(options["manifest"])
        path = original_path.resolve()
        if (
            not path.parent.is_dir()
            or original_path.is_symlink()
            or path.parent.stat().st_mode & 0o077
        ):
            raise CommandError(
                "Use an existing private directory and an ordinary manifest file."
            )
        if path.exists():
            if path.stat().st_mode & 0o077:
                raise CommandError("The private manifest must have mode 0600.")
            manifest = json.loads(path.read_text())
            if manifest.get("version") != 1:
                raise CommandError("Unsupported identity conversion manifest.")
        else:
            if options["apply"]:
                raise CommandError("Create and review the manifest before applying it.")
            assets = {}
            for profile in Profile.objects.all():
                for field in sorted(IDENTITY_FIELDS):
                    asset = getattr(profile, field)
                    if not asset or asset.type == "authenticated":
                        continue
                    if (
                        asset.resource_type != "image"
                        or asset.type != "upload"
                        or "://" in asset.public_id
                    ):
                        raise CommandError(
                            "An unsupported legacy reference needs private manual review."
                        )
                    identifier = hashlib.sha256(
                        json.dumps(key(asset)).encode()
                    ).hexdigest()
                    item = assets.setdefault(
                        identifier,
                        {
                            "public_id": asset.public_id,
                            "resource_type": asset.resource_type,
                            "type": asset.type,
                            "references": [],
                            "state": "planned",
                            "blocked": [],
                        },
                    )
                    item["references"].append(
                        {
                            "profile_id": str(profile.id),
                            "field": field,
                            "before": reference(asset),
                        }
                    )
                    if profile.kyc_submissions.exists():
                        item["blocked"].append("versioned_kyc_requires_separate_review")
            # Do not accidentally revoke a public avatar/listing that reuses an asset.
            by_key = {
                (i["resource_type"], i["type"], i["public_id"]): i
                for i in assets.values()
            }
            for model in apps.get_models():
                fields = [
                    f
                    for f in model._meta.fields
                    if isinstance(f, CloudinaryField)
                    and not (model is Profile and f.name in IDENTITY_FIELDS)
                ]
                for field in fields:
                    for value in model.objects.values_list(
                        field.name, flat=True
                    ).iterator():
                        if value and key(value) in by_key:
                            by_key[key(value)]["blocked"].append(
                                "also_referenced_outside_identity"
                            )
            manifest = {"version": 1, "assets": assets}
            checkpoint(path, manifest)
        if options["apply"]:
            for identifier, item in manifest["assets"].items():
                if item["state"] == "complete" or item["blocked"]:
                    continue
                if "asset_id" not in item:
                    source = cloudinary.api.resource(
                        item["public_id"], resource_type="image", type="upload"
                    )
                    item["asset_id"] = source["asset_id"]
                    checkpoint(path, manifest)
                # Reconcile an interrupted provider rename before deciding to issue it.
                try:
                    target = cloudinary.api.resource(
                        item["public_id"], resource_type="image", type="authenticated"
                    )
                except cloudinary.api.NotFound:
                    target = None
                if target is None:
                    item["state"] = "provider_result_unknown"
                    checkpoint(path, manifest)
                    target = cloudinary.uploader.rename(
                        item["public_id"],
                        item["public_id"],
                        resource_type="image",
                        type="upload",
                        to_type="authenticated",
                        invalidate=True,
                    )
                if (
                    target.get("asset_id") != item["asset_id"]
                    or target.get("type") != "authenticated"
                ):
                    raise CommandError(
                        "Provider identity mismatch; keep the manifest for reconciliation."
                    )
                protected = CloudinaryResource(metadata=target)
                item["after"] = reference(protected)
                item["state"] = "provider_confirmed"
                checkpoint(path, manifest)
                with transaction.atomic():
                    for row in item["references"]:
                        profile = Profile.objects.select_for_update().get(
                            id=row["profile_id"]
                        )
                        current = reference(getattr(profile, row["field"]))
                        if (
                            current not in {row["before"], item["after"]}
                            or profile.kyc_submissions.exists()
                        ):
                            raise CommandError(
                                "Identity evidence changed; reconcile the protected asset before updating its reference."
                            )
                        setattr(profile, row["field"], protected)
                        profile.save(update_fields=[row["field"]])
                item["state"] = "complete"
                checkpoint(path, manifest)
        self.stdout.write(
            json.dumps(
                {
                    "assets": len(manifest["assets"]),
                    "references": sum(
                        len(i["references"]) for i in manifest["assets"].values()
                    ),
                    "complete": sum(
                        i["state"] == "complete" for i in manifest["assets"].values()
                    ),
                    "blocked": sum(
                        bool(i["blocked"]) for i in manifest["assets"].values()
                    ),
                    "applied": options["apply"],
                },
                sort_keys=True,
            )
        )

"""Resumable, non-destructive transfer of existing private support originals."""

import json
import hashlib
from pathlib import Path
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from core_apps.support.services.private_attachments import clean_image
import io
from django.core.management.base import BaseCommand, CommandError
from core_apps.support.models import TicketAttachment
from core_apps.support.storage import SupportPrivateStorage


class Command(BaseCommand):
    help = "Report private support files; --apply copies and verifies durable bytes. Never deletes originals."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--attachment-id", action="append", default=[])

    def handle(self, *args, **options):
        storage = SupportPrivateStorage()
        if options["apply"] and not storage.remote:
            raise CommandError("Configure SUPPORT_PRIVATE_STORAGE_PROVIDER=cloudinary first.")
        items = TicketAttachment.objects.order_by("id")
        if options["attachment_id"]:
            items = items.filter(id__in=options["attachment_id"])
        failed = 0
        for item in items.iterator():
            output = {"id": str(item.id), "status": "not_verified", "has_private_reference": bool(item.private_file), "has_legacy_reference": bool(item.file), "digest_bound": bool(item.content_sha256)}
            if options["apply"]:
                try:
                    field = item.private_file or item.file
                    if not field:
                        raise ValueError("Missing source")
                    with field.open("rb") as stream:
                        content = stream.read(storage.maximum_bytes + 1)
                    if not 0 < len(content) <= storage.maximum_bytes:
                        raise ValueError("Invalid source size")
                    clean_image(io.BytesIO(content))
                    digest = hashlib.sha256(content).hexdigest()
                    if item.content_sha256 and item.content_sha256 != digest:
                        raise ValueError("Source differs from the recorded digest")
                    name = item.private_file.name or f"attachments/legacy-{item.id.hex}.original"
                    local = Path(storage.path(name))
                    if not local.exists():
                        saved = FileSystemStorage._save(storage, name, ContentFile(content))
                        if saved != name:
                            raise ValueError("Unexpected concurrent destination")
                    if hashlib.sha256(local.read_bytes()).hexdigest() != digest or storage.ensure_remote(name) != digest:
                        raise ValueError("Backup differs from the source")
                    changed = TicketAttachment.objects.filter(
                        pk=item.pk, file=item.file.name or "",
                        private_file=item.private_file.name or "",
                        content_sha256=item.content_sha256,
                    ).update(private_file=name, content_sha256=digest)
                    if changed != 1:
                        raise ValueError("Attachment changed since review")
                    output.update(status="verified", sha256=digest, digest_bound=True, legacy_reference_retained=bool(item.file))
                except Exception:
                    output["status"] = "failed_original_retained"
                    failed += 1
            self.stdout.write(json.dumps(output))
        if failed:
            raise CommandError(f"{failed} private files require storage review; no originals deleted.")

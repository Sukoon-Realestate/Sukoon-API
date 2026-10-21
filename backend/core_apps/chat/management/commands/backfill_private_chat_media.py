"""Copy active legacy media without changing attachment or message identities."""

import hashlib
import time
from django.core.management.base import BaseCommand, CommandError
from core_apps.chat.models import ChatAttachment
from core_apps.chat.services import group_media_remote as remote
from core_apps.chat.services.group_media_storage import private_path


class Command(BaseCommand):
    help = "Copy and verify active private chat files in the configured durable store."

    def add_arguments(self, parser):
        parser.add_argument("--watch-seconds", type=int, default=0)

    def handle(self, *args, **options):
        if not remote.configured():
            raise CommandError("Enable the private chat storage provider first.")
        deadline = time.monotonic() + max(0, options["watch_seconds"])
        verified = {}
        while True:
            active = ChatAttachment.objects.filter(state__in=["ready", "attached"])
            keys = set(active.values_list("storage_key", flat=True)) | set(
                active.values_list("thumbnail_key", flat=True)
            )
            keys.discard("")
            missing = 0
            for key in keys:
                source = private_path(key)
                if not source.is_file() or source.is_symlink():
                    missing += 1
                    continue
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                if verified.get(key) == digest:
                    continue
                remote.persist(key, source)
                remote.verify_backup(key, source)
                verified[key] = digest
            self.stdout.write(
                f"active={len(keys)} verified={len(keys & verified.keys())} missing={missing}"
            )
            self.stdout.flush()
            if missing:
                raise CommandError(
                    "Some active source files are missing; do not replace this service yet."
                )
            if time.monotonic() >= deadline:
                break
            time.sleep(2)

"""Explicit, opt-in recovery of original advertising bytes; never runs on GET."""

import hashlib
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core_apps.advertising.models import Advertisement


class Command(BaseCommand):
    help = "Verify original artwork against its stored digest; write only with --apply."

    def add_arguments(self, parser):
        parser.add_argument("advertisement_id")
        parser.add_argument("source", type=Path)
        parser.add_argument("--apply", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        ad = Advertisement.objects.select_for_update().get(
            id=options["advertisement_id"]
        )
        media = ad.media
        source = options["source"]
        if source.stat().st_size != media.size_bytes or media.size_bytes <= 0:
            raise CommandError(
                "Original byte length does not match the recorded source."
            )
        content = source.read_bytes()
        if hashlib.sha256(content).hexdigest() != media.sha256:
            raise CommandError("Original digest does not match the recorded source.")
        if media.banner.storage.exists(media.banner.name):
            raise CommandError(
                "Destination exists; review it explicitly before recovery."
            )
        if options["apply"]:
            name = media.banner.storage.save(media.banner.name, ContentFile(content))
            if name != media.banner.name:
                media.banner.storage.delete(name)
                raise CommandError(
                    "Destination changed concurrently; no binding changed."
                )
            self.stdout.write("Original bytes restored; metadata unchanged.")
        else:
            self.stdout.write("Verified original bytes; dry run, no storage write.")

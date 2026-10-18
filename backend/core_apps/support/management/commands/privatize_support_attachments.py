"""Move legacy originals without changing evidence bytes; dry run by default."""

import hashlib
import uuid
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core_apps.support.models import TicketAttachment


class Command(BaseCommand):
    help = "Privatize legacy support files. --apply copies; --remove-public additionally removes verified public originals."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--remove-public", action="store_true")

    def handle(self, *args, **options):
        if options["remove_public"] and not options["apply"]:
            raise CommandError(
                "--remove-public requires --apply after storage and backup review."
            )
        count = 0
        for pk in (
            TicketAttachment.objects.exclude(file="")
            .values_list("pk", flat=True)
            .iterator()
        ):
            if not options["apply"]:
                count += 1
                continue
            with transaction.atomic():
                item = TicketAttachment.objects.select_for_update().get(pk=pk)
                if not item.file:
                    continue
                if not item.file.storage.exists(item.file.name):
                    # A previous on_commit callback may have removed the public
                    # object before its final DB field clear was interrupted.
                    if (
                        options["remove_public"]
                        and item.private_file
                        and item.private_file.storage.exists(item.private_file.name)
                    ):
                        item.file = ""
                        item.save(update_fields=["file"])
                        count += 1
                        continue
                    raise CommandError(
                        "Legacy original is missing; retain the record for storage review."
                    )
                with item.file.open("rb") as original:
                    content = original.read()
                digest = hashlib.sha256(content).digest()
                if not item.private_file:
                    item.private_file.save(
                        f"{uuid.uuid4().hex}.original", ContentFile(content), save=False
                    )
                    try:
                        item.save(update_fields=["private_file"])
                    except Exception:
                        item.private_file.delete(save=False)
                        raise
                with item.private_file.open("rb") as copied:
                    if hashlib.sha256(copied.read()).digest() != digest:
                        raise CommandError(
                            "Private copy differs; public original was retained."
                        )
                if options["remove_public"]:
                    # Keep the reference until deletion succeeds. Rerunning is safe.
                    legacy_name, storage = item.file.name, item.file.storage
                    # The private copy is committed first. No delete precedes its durable reference.
                    transaction.on_commit(
                        lambda storage=storage, name=legacy_name, pk=pk: self.remove_public(
                            storage, name, pk
                        )
                    )
                count += 1
        self.stdout.write(
            f"{'Applied' if options['apply'] else 'Dry run'}: {count} legacy attachment(s)."
        )

    def remove_public(self, storage, name, pk):
        storage.delete(name)
        TicketAttachment.objects.filter(pk=pk, file=name).update(file="")

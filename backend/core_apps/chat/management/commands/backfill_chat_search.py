from django.core.management.base import BaseCommand
from django.db import transaction
from core_apps.chat.models import Message
from core_apps.chat.services.search_index import index_message


class Command(BaseCommand):
    help = "Rebuild derived chat search documents without changing messages."

    def add_arguments(self, parser):
        parser.add_argument("--after", type=int, default=0)
        parser.add_argument("--batch-size", type=int, default=200)

    def handle(self, *args, **options):
        after = options["after"]
        size = max(1, min(options["batch_size"], 500))
        while True:
            with transaction.atomic():
                rows = list(
                    Message.objects.select_for_update()
                    .filter(pkid__gt=after)
                    .order_by("pkid")[:size]
                )
                if not rows:
                    break
                for row in rows:
                    index_message(row)
                after = rows[-1].pkid
            self.stdout.write(f"Indexed through message pkid {after}")

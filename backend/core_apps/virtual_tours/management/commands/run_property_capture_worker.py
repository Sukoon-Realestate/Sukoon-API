import time
from django.core.management.base import BaseCommand
from core_apps.virtual_tours.capture_worker import claim, run


class Command(BaseCommand):
    help = "Process private phone-capture revisions with fenced job leases."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            job = claim()
            if job:
                run(job)
            if options["once"]:
                return
            if not job:
                time.sleep(2)

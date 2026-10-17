from django.core.management.base import BaseCommand
from core_apps.features.transition_network_models import TransitionMatchRun
from core_apps.features.services.transition_network.jobs import process_transition_match


class Command(BaseCommand):
    help = "Resume a bounded batch of queued assisted move matches without business execution."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=25)

    def handle(self, *args, **options):
        ids = (
            TransitionMatchRun.objects.filter(status="queued")
            .order_by("created_at")
            .values_list("id", flat=True)[: max(1, min(options["limit"], 100))]
        )
        count = 0
        for identifier in list(ids):
            process_transition_match(str(identifier))
            count += 1
        self.stdout.write(f"Reviewed {count} queued match jobs.")

"""Recover a bounded batch after broker interruption without exposing inputs."""

from django.core.management.base import BaseCommand
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from core_apps.features.housing_scenario_models import HousingScenarioRun
from core_apps.features.transition_network_models import TransitionMatchRun
from core_apps.features.advanced_tender_models import TenderPackageRun
from core_apps.features.services.housing_scenarios.jobs import calculate
from core_apps.features.services.transition_network.jobs import process_transition_match
from core_apps.features.services.housing_tenders.jobs import process_tender_packages


class Command(BaseCommand):
    help = (
        "Process bounded queued advanced housing jobs using current capability gates."
    )

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)

    def handle(self, *args, **options):
        limit = max(1, min(options["limit"], 500))
        count = 0
        cutoff = timezone.now() - timedelta(minutes=15)
        for model, busy in (
            (HousingScenarioRun, "running"),
        ):
            with transaction.atomic():
                stale = (
                    model.objects.select_for_update(skip_locked=True)
                    .filter(
                        state=busy,
                        updated_at__lte=cutoff,
                        cancellation_requested=False,
                    )
                    .order_by("updated_at")[:limit]
                )
                for item in stale:
                    # Invalidates the abandoned worker's revision claim before
                    # another invocation may compute the immutable inputs.
                    item.state = "queued"
                    item.revision += 1
                    item.failure_code = "worker_recovered"
                    item.save(
                        update_fields=[
                            "state",
                            "revision",
                            "failure_code",
                            "updated_at",
                        ]
                    )
        for model, state, worker in (
            (TenderPackageRun, "status", process_tender_packages),
            (HousingScenarioRun, "state", calculate),
            (TransitionMatchRun, "status", process_transition_match),
        ):
            ids = list(
                model.objects.filter(**{state: "queued"})
                .order_by("created_at")
                .values_list("id", flat=True)[:limit]
            )
            for identifier in ids:
                worker(str(identifier))
                count += 1
        self.stdout.write(
            f"Reviewed {count} queued jobs under current capability policy."
        )

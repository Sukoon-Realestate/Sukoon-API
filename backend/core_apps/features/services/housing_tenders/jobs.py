"""Compute from the recorded source outside locks; revalidate finalists at commit."""

from celery import shared_task
from django.http import Http404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import APIException
from core_apps.users.models import User
from core_apps.properties.models import Property
from ...advanced_tender_models import TenderPackageRun, TenderBidLine
from ..planning import enabled_services
from ..rental_phase2 import fingerprint
from .construction import calculate, persist_options, source
from .access import get_tender, current, admin

RELATED = ("tender__active_snapshot", "tender__group", "tender__request", "snapshot", "created_by")


@shared_task(name="features.process_tender_packages")
def process_tender_packages(identifier):
    run = TenderPackageRun.objects.select_related(*RELATED).get(id=identifier)
    if run.status != "queued":
        return run.status
    if "collective_tender_planning" not in enabled_services():
        return "paused"
    proposals = calculate(run)
    with transaction.atomic():
        participants = [row["participant_id"] for row in run.snapshot.private_requirements]
        line_ids = {row["line_id"] for proposed in proposals for row in proposed}
        lines = list(TenderBidLine.objects.filter(id__in=line_ids).values("offer__property_id", "bid__owner_id"))
        users = list(
            User.objects.select_for_update(no_key=True)
            .filter(Q(pk__in={run.created_by_id, *(row["bid__owner_id"] for row in lines)}) | Q(id__in=participants))
            .order_by("pk")
        )
        try:
            tender = get_tender(run.created_by, run.tender.id, lock=True)
        except (APIException, Http404):
            tender = None
        list(
            Property.objects.select_for_update(no_key=True)
            .filter(pk__in={row["offer__property_id"] for row in lines})
            .order_by("pk")
        )
        locked = TenderPackageRun.objects.select_for_update(of=("self",)).get(pk=run.pk)
        if locked.status != "queued" or locked.revision != run.revision:
            return locked.status
        if "collective_tender_planning" not in enabled_services():
            return "paused"
        actor = next((user for user in users if user.pk == run.created_by_id), None)
        if (
            not tender
            or not actor
            or not actor.is_active
            or not actor.is_verified
            or not admin(actor, tender)
            or not current(tender)
            or tender.status != "published"
            or tender.active_snapshot_id != run.snapshot_id
            or fingerprint(source(tender)) != run.source_digest
            or run.status == "source_changed"
        ):
            run.status = "source_changed"
            run.result = {"optimality_proven": False, "feasible_count": 0}
        else:
            run.tender, run.created_by = tender, actor
            persist_options(run, proposals)
        run.completed_at = timezone.now()
        run.revision += 1
        run.save()
        from ..advanced_planning_notifications import record

        record(run, None, "tender.result")
        return run.status


def enqueue(identifier):
    try:
        process_tender_packages.delay(identifier)
    except Exception:
        return False
    return True

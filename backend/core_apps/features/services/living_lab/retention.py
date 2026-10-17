"""Product retention cleanup. Accepted business snapshots and receipt metadata survive."""

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from ...living_lab_models import SharedLivingLab, LivingLabAuditEvent
from ...models import IdempotencyRecord
from .policies import limit


def scrub_disclosure_receipts(lab, user_ids=None):
    """Revocation also removes optional preferences embedded in recovered results."""
    identifiers = {str(value) for value in user_ids} if user_ids is not None else None
    for record in (
        IdempotencyRecord.objects.select_for_update(of=("self",))
        .select_related("user")
        .filter(result_subject_id=lab.id, operation__startswith="living_lab.")
    ):
        resource = record.response_data.get("resource", {})
        disclosures = resource.get("disclosures", [])
        retained = [
            row
            for row in disclosures
            if identifiers is not None and str(row.get("user_id")) not in identifiers
        ]
        own = identifiers is None or str(record.user.id) in identifiers
        if retained != disclosures or (own and resource.get("my_disclosure_fields")):
            resource["disclosures"] = retained
            if own:
                resource["my_disclosure_fields"] = []
            record.save(update_fields=["response_data", "updated_at"])


@transaction.atomic
def purge_lab(identifier, *, now=None):
    now = now or timezone.now()
    lab = SharedLivingLab.objects.select_for_update().get(pk=identifier)
    private_cutoff = now - timedelta(days=limit("PRIVATE_RETENTION_DAYS", 30))
    output_cutoff = now - timedelta(days=limit("UNCOMMITTED_RETENTION_DAYS", 30))
    changed = False
    rows = lab.requirements.filter(updated_at__lte=private_cutoff).exclude(
        private_values={}
    )
    if rows.exists():
        users = list(rows.values_list("user_id", flat=True))
        lab.disclosures.filter(user_id__in=users).update(
            values={}, fields=[], revoked_at=now
        )
        scrub_disclosure_receipts(lab, rows.values_list("user__id", flat=True))
        # Retain minimized purpose and consent evidence; purged status cannot be
        # used by the solver and carries no raw preferences or financial bounds.
        rows.update(private_values={}, status="purged")
        # A digest includes low-entropy private bounds. It is not a substitute
        # for erasing those inputs, even though it was never a public value.
        lab.runs.exclude(input_digest="").update(input_digest="")
        lab.input_revision += 1
        changed = True
    if lab.expires_at <= output_cutoff:
        for run in lab.runs.all():
            agreed = {
                str(value)
                for value in lab.agreements.filter(run=run).values_list(
                    "candidate_id", flat=True
                )
            }
            retained = [
                candidate for candidate in run.candidates if candidate["id"] in agreed
            ]
            if len(retained) != len(run.candidates) or run.input_digest:
                run.candidates, run.input_digest = retained, ""
                if not retained:
                    run.status, run.explanation_code = "expired", "retention_expired"
                run.save(
                    update_fields=[
                        "candidates",
                        "input_digest",
                        "status",
                        "explanation_code",
                        "updated_at",
                    ]
                )
                changed = True
        # Operation receipts stay recoverable. Minimize the embedded ephemeral
        # projection too, otherwise an old receipt would bypass output retention.
        for record in IdempotencyRecord.objects.select_for_update().filter(
            result_subject_id=lab.id, operation__startswith="living_lab."
        ):
            resource = record.response_data.get("resource", {})
            run = resource.get("latest_run")
            if isinstance(run, dict):
                accepted_ids = {
                    str(value)
                    for value in lab.agreements.values_list("candidate_id", flat=True)
                }
                run["candidates"] = [
                    c for c in run.get("candidates", []) if c.get("id") in accepted_ids
                ]
                run["current"] = False
                run["outcome"] = "expired"
            resource["disclosures"] = []
            resource["my_disclosure_fields"] = []
            resource["allowed_actions"] = ["withdraw"]
            resource["status"] = "expired"
            record.save(update_fields=["response_data", "updated_at"])
    if changed:
        lab.revision += 1
        if lab.status != "closed":
            lab.status = "expired" if lab.expires_at <= now else "needs_revision"
        lab.purged_at = now
        lab.save(
            update_fields=[
                "revision",
                "input_revision",
                "status",
                "purged_at",
                "updated_at",
            ]
        )
        LivingLabAuditEvent.objects.create(
            lab=lab, actor=None, event="retention_purged"
        )
    return changed


def purge_due(*, now=None, batch_size=200):
    now = now or timezone.now()
    cutoff = now - timedelta(
        days=min(
            limit("PRIVATE_RETENTION_DAYS", 30), limit("UNCOMMITTED_RETENTION_DAYS", 30)
        )
    )
    count = 0
    identifiers = (
        SharedLivingLab.objects.filter(created_at__lte=cutoff)
        .order_by("pkid")
        .values_list("pk", flat=True)
    )
    for identifier in identifiers.iterator(chunk_size=batch_size):
        count += purge_lab(identifier, now=now)
    return count

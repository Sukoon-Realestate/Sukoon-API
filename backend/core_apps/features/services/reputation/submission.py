"""Durable receipts use the existing operation registry, with no expiry replay."""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.exceptions import NotFound
from core_apps.common.idempotency import fingerprint
from ...models import (
    ReviewCase,
    ReviewOpportunity,
    ReviewSubmission,
    ReviewSection,
    ReviewAuditEvent,
    IdempotencyRecord,
)
from .policy import (
    ReviewError,
    require_enabled,
    require_actor,
    revision,
    validate_sections,
)
from .eligibility import valid_source
from .generation import event


def opportunity_for(user, identity):
    require_actor(user)
    try:
        item = ReviewOpportunity.objects.select_related(
            "case",
            "case__lease",
            "case__visit",
            "case__peer_lease",
            "case__company_binding",
            "reviewer_company",
        ).get(id=identity)
    except ReviewOpportunity.DoesNotExist:
        raise NotFound()
    if item.reviewer_company_id:
        from .company_authority import require_opportunity

        require_opportunity(user, item, submit=True)
    elif item.reviewer_id != user.pk:
        raise NotFound()
    return item


def audit(item, actor, action, reason=""):
    return ReviewAuditEvent.objects.create(
        subject_id=item.id, actor=actor, action=action, reason=reason
    )


def release(case):
    if case.gate_released_at or case.revocation_reason:
        return
    if timezone.now() >= case.closes_at or (
        case.release_mode == "mutual_or_deadline"
        and not case.opportunities.filter(submitted_once_at__isnull=True).exists()
    ):
        case.gate_released_at = timezone.now()
        case.revision += 1
        case.save(update_fields=["gate_released_at", "revision", "updated_at"])
        audit(case, None, "gate_released")
        from .visibility import notify_subject

        for section in ReviewSection.objects.filter(submission__opportunity__case=case):
            if section.content_state == "approved":
                notify_published(section)
            for decision in section.decisions.all():
                notify_subject(
                    section,
                    "review_moderation_decision",
                    str(decision.id),
                )


def notify_published(section):
    from .visibility import notify_subject

    # Notifications never contain a comment, score, counterparty or contract ID.
    notify_subject(section, "review_published")


def operation_key(body):
    key = body.get("request_key") if isinstance(body, dict) else None
    if not isinstance(key, str) or not 8 <= len(key) <= 100:
        raise ReviewError("invalid_review_target", 400)
    return key


@transaction.atomic
def command(user, operation, body, action, subject_id=None):
    require_actor(user)
    key = operation_key(body)
    # This short account lock also serializes reuse of a key across routes.
    current_user = get_user_model().objects.select_for_update().get(pk=user.pk)
    require_actor(current_user)
    digest = fingerprint(body)
    existing = IdempotencyRecord.objects.filter(
        user=user, request_key=key, operation__startswith="review."
    ).first()
    if existing:
        if existing.operation != operation or existing.fingerprint != digest:
            raise ReviewError("idempotency_payload_mismatch")
        return existing.response_data
    resource = action()
    IdempotencyRecord.objects.create(
        user=user,
        operation=operation,
        request_key=key,
        fingerprint=digest,
        response_data=resource,
        request_subject_id=subject_id,
        recovery_status="confirmed",
    )
    return resource


def submit(user, identity, body):
    # Authorization is checked even on replay and independently of the kill switch.
    opp = opportunity_for(user, identity)

    def action():
        require_enabled()
        case = ReviewCase.objects.select_for_update().get(pk=opp.case_id)
        item = (
            ReviewOpportunity.objects.select_for_update()
            .select_related("case")
            .get(pk=opp.pk)
        )
        if item.reviewer_company_id:
            from .company_authority import require_opportunity

            require_opportunity(user, item, submit=True, lock=True)
        if item.submitted_once_at:
            existing = ReviewSubmission.objects.get(opportunity=item)
            return {
                **existing.receipt,
                "request_key": body["request_key"],
                "canonical_request_key": existing.request_key,
                "already_submitted": True,
            }
        if not get_user_model().objects.get(pk=user.pk).is_verified:
            raise ReviewError("review_not_eligible", 403)
        if item.state != "open" or not valid_source(case):
            raise ReviewError("experience_not_confirmed")
        if timezone.now() >= case.closes_at:
            raise ReviewError("review_window_closed")
        revision(item, body.get("expected_revision"))
        sections = validate_sections(item, body)
        submission = ReviewSubmission.objects.create(
            opportunity=item,
            acting_user=user,
            request_key=body["request_key"],
            payload_hash=fingerprint(body),
        )
        ids = []
        for target, score, criteria, comment, tags in sections:
            if target["id"] == str(user.id) and not target["kind"].startswith(
                "property_"
            ):
                raise ReviewError("self_review_forbidden")
            section = ReviewSection.objects.create(
                submission=submission,
                target_key=target["key"],
                subject_kind=target["kind"],
                subject_id=target["id"],
                audience=(
                    "public"
                    if target["visibility"] == "public_after_release"
                    else "private"
                ),
                overall_score=score,
                criteria=criteria,
                tag_codes=tags,
                original_comment=comment,
                public_comment=comment,
                verification_basis=(
                    "recorded_viewing"
                    if case.context_type == "viewing"
                    else "recorded_occupancy"
                ),
            )
            ids.append(str(section.id))
        item.state, item.submitted_once_at = "submitted", timezone.now()
        item.revision += 1
        item.save(
            update_fields=["state", "submitted_once_at", "revision", "updated_at"]
        )
        item.draft.delete() if hasattr(item, "draft") else None
        release(case)
        receipt = {
            "id": str(submission.id),
            "opportunity_id": str(item.id),
            "request_key": body["request_key"],
            "section_ids": ids,
            "state": "succeeded",
            "content_state": "pending",
            "gate_state": "released" if case.gate_released_at else "waiting",
            "received_at": item.submitted_once_at.isoformat(),
            "revision": item.revision,
        }
        submission.receipt = receipt
        submission.save(update_fields=["receipt", "updated_at"])
        audit(item, user, "submitted")
        return receipt

    return command(user, f"review.submit.{identity}", body, action, opp.id)


def lookup(user, key):
    require_actor(user)
    record = IdempotencyRecord.objects.filter(
        user=user, request_key=key, operation__startswith="review."
    ).first()
    if not record:
        # No claim of final absence; safe retry retains the original key/payload.
        return {"state": "unknown", "request_key": key}
    if record.operation.startswith(
        ("review.submit.", "review.draft.", "review.draft_delete.", "review.reminders.")
    ):
        opportunity_for(user, record.request_subject_id)
    if record.operation.startswith("review.binding."):
        from . import company_bindings
        from ...models import CompanyReviewAuthority

        if record.operation.startswith("review.binding.authority."):
            authority = CompanyReviewAuthority.objects.get(
                id=record.response_data["id"]
            )
            company_bindings.membership(user, authority.membership.company, admin=True)
        else:
            company_bindings.get(user, record.response_data["id"])
    elif record.operation.startswith(("review.assignment.", "review.occupancy.")):
        from .employee_occupancy import read
        from ...models import EmployeeAssignment

        read(user, EmployeeAssignment.objects.get(id=record.response_data["id"]))
    elif record.operation.startswith("review.ownership."):
        from .responsibility import participant
        from ...models import LeaseResponsibilityTransition

        participant(
            user,
            LeaseResponsibilityTransition.objects.get(id=record.response_data["id"]),
        )
    return {"state": "succeeded", "request_key": key, "receipt": record.response_data}

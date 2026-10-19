"""Immutable decisions; separate content decisions from the time gate."""

from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied
from ...models import (
    ReviewCase,
    ReviewSection,
    ReviewReply,
    ReviewReport,
    ReviewModerationDecision,
    ReviewAppeal,
    ReviewAuditEvent,
)
from .policy import (
    ReviewError,
    REPORT_REASONS,
    keys,
    revision,
    text_value,
    require_actor,
)
from .submission import command, audit, notify_published
from .visibility import (
    section_for,
    is_author,
    is_subject,
    visible,
    published,
    sections,
    subject_user,
    subject_company,
    notify_subject,
    notify_author,
    released,
    decision_notice,
)
from .generation import event


def section_action(user, identity, action_name, body):
    item = section_for(user, identity)

    def action():
        keys(
            body,
            ["request_key", "expected_revision", "comment", "reason_code", "detail"],
            ["request_key", "expected_revision"],
        )
        ReviewCase.objects.select_for_update().get(
            pk=item.submission.opportunity.case_id
        )
        locked = ReviewSection.objects.select_for_update().get(pk=item.pk)
        revision(locked, body.get("expected_revision"))
        if action_name == "withdraw":
            if not is_author(locked, user):
                raise NotFound()
            locked.content_state = "withdrawn"
            locked.revision += 1
            locked.save(update_fields=["content_state", "revision", "updated_at"])
            audit(locked, user, "withdrawn")
            return {
                "id": str(locked.id),
                "state": "withdrawn",
                "revision": locked.revision,
            }
        if not visible(locked, user):
            raise NotFound()
        if action_name == "reply":
            if not is_subject(locked, user):
                raise NotFound()
            if subject_company(locked):
                from .company_authority import permitted

                if not permitted(
                    user,
                    locked.submission.opportunity.case.company_binding,
                    subject_company(locked),
                    submit=True,
                    lock=True,
                ):
                    raise NotFound()
            if hasattr(locked, "reply"):
                raise ReviewError("review_not_eligible")
            comment = text_value(body.get("comment", ""), 1000)
            if not comment:
                raise ReviewError("invalid_review_text", 400)
            reply = ReviewReply.objects.create(
                section=locked,
                author=user,
                author_company=subject_company(locked),
                original_comment=comment,
                public_comment=comment,
            )
            audit(reply, user, "reply_submitted")
            return {
                "id": str(reply.id),
                "state": reply.content_state,
                "revision": reply.revision,
            }
        reason = body.get("reason_code")
        if action_name != "reports" or reason not in REPORT_REASONS:
            raise ReviewError("invalid_review_target", 400)
        report, _ = ReviewReport.objects.get_or_create(
            section=locked,
            reporter=user,
            reason_code=reason,
            defaults={"detail": text_value(body.get("detail", ""), 1500)},
        )
        # Report counts and star values never trigger automatic removal.
        return {
            "id": str(report.id),
            "state": report.state,
            "revision": report.revision,
        }

    return command(user, f"review.{action_name}.{identity}", body, action, item.id)


def withdraw_reply(user, identity, body):
    reply = ReviewReply.objects.filter(id=identity).first()

    def authorized(item):
        if item.author_company_id:
            from .company_authority import permitted

            return permitted(
                user,
                item.section.submission.opportunity.case.company_binding,
                item.author_company,
                submit=True,
            )
        return item.author_id == user.pk

    if not reply or not authorized(reply):
        raise NotFound()

    def action():
        locked = ReviewReply.objects.select_for_update().get(pk=reply.pk)
        if not authorized(locked):
            raise NotFound()
        revision(locked, body.get("expected_revision"))
        locked.content_state = "withdrawn"
        locked.revision += 1
        locked.save(update_fields=["content_state", "revision", "updated_at"])
        audit(locked, user, "reply_withdrawn")
        return {
            "id": str(locked.id),
            "state": locked.content_state,
            "revision": locked.revision,
        }

    return command(user, f"review.reply_withdraw.{identity}", body, action, reply.id)


def require_moderator(user, section, permission="moderate_reviews"):
    require_actor(user)
    if not user.has_perm(f"features.{permission}"):
        raise PermissionDenied()
    if is_author(section, user) or is_subject(section, user):
        raise ReviewError("conflict_of_interest")
    case = section.submission.opportunity.case
    for company in (case.company, case.landlord_company):
        if company and company.memberships.filter(user=user, is_active=True).exists():
            raise ReviewError("conflict_of_interest")


def report_resolution(report):
    if report.state != "resolved":
        return ""
    return (
        ReviewAuditEvent.objects.filter(
            subject_id=report.id, action="operator_case_resolved"
        )
        .order_by("-created_at", "-id")
        .values_list("reason", flat=True)
        .first()
        or ""
    )


def resolve_report(user, identity, body):
    report = ReviewReport.objects.select_related("section").filter(id=identity).first()
    if not report:
        raise NotFound()
    require_moderator(user, report.section)

    def action():
        keys(
            body,
            ["request_key", "expected_revision", "reason"],
            ["request_key", "expected_revision", "reason"],
        )
        locked = ReviewReport.objects.select_for_update().get(pk=report.pk)
        require_moderator(user, locked.section)
        revision(locked, body["expected_revision"])
        if locked.state != "open":
            raise ReviewError("review_not_eligible")
        reason = text_value(body["reason"], 1000)
        if not reason:
            raise ReviewError("invalid_review_text", 400)
        locked.state = "resolved"
        locked.revision += 1
        locked.save(update_fields=["state", "revision", "updated_at"])
        audit(locked, user, "operator_case_resolved", reason)
        return {"id": str(locked.id), "state": "resolved", "revision": locked.revision}

    return command(user, f"review.resolve_case.{identity}", body, action, report.id)


def moderate(user, identity, body, *, appeal=None):
    item = sections().filter(id=identity).first()
    if not item:
        raise NotFound()
    require_moderator(user, item)

    def action():
        keys(
            body,
            [
                "request_key",
                "expected_revision",
                "action",
                "reason",
                "redacted_comment",
                "reply_id",
            ],
            ["request_key", "expected_revision", "action", "reason"],
        )
        case = ReviewCase.objects.select_for_update().get(
            pk=item.submission.opportunity.case_id
        )
        section = ReviewSection.objects.select_for_update().get(pk=item.pk)
        content = section
        if body.get("reply_id"):
            content = (
                ReviewReply.objects.select_for_update()
                .filter(id=body["reply_id"], section=section)
                .first()
            )
            if not content:
                raise NotFound()
        revision(content, body["expected_revision"])
        reason = text_value(body["reason"], 1000)
        if not reason:
            raise ReviewError("invalid_review_text", 400)
        states = {
            "approve": "approved",
            "keep": content.content_state,
            "hold": "held",
            "reject": "rejected",
            "remove": "removed",
            "restore": "approved",
            "redact": content.content_state,
            "revoke_eligibility": content.content_state,
        }
        name = body["action"]
        if name not in states or content.content_state == "withdrawn":
            raise ReviewError("review_not_eligible")
        if name == "revoke_eligibility":
            require_moderator(user, section, "review_eligibility")
            case.revocation_reason = reason
            case.revision += 1
            case.save(update_fields=["revocation_reason", "revision", "updated_at"])
            case.opportunities.update(state="revoked")
        if name == "redact":
            redacted = text_value(
                body.get("redacted_comment", ""), 1500 if content == section else 1000
            )
            # Redaction is deletion only, never a rewritten opinion or added claim.
            iterator = iter(content.public_comment)
            if not all(any(c == candidate for candidate in iterator) for c in redacted):
                raise ReviewError("invalid_review_text", 400)
            content.public_comment = redacted
        decision = ReviewModerationDecision.objects.create(
            section=section,
            reply=None if content == section else content,
            actor=user,
            action=name,
            reason=reason,
            before_state=content.content_state,
            after_state=states[name],
            policy_version=case.policy_version,
        )
        content.content_state = states[name]
        content.revision += 1
        content.save(
            update_fields=["content_state", "public_comment", "revision", "updated_at"]
        )
        audit(content, user, "moderation_decision", reason)
        notify_author(
            section,
            "review_moderation_decision",
            str(decision.id),
        )
        if released(case):
            notify_subject(
                section,
                "review_moderation_decision",
                str(decision.id),
            )
        if published(section):
            notify_published(section)
            if content != section and content.content_state == "approved":
                notify_author(
                    section,
                    "review_reply_published",
                    str(content.id),
                )
        return {
            "id": str(decision.id),
            "section_id": str(section.id),
            "state": content.content_state,
            "revision": content.revision,
        }

    return command(user, f"review.moderate.{identity}", body, action, item.id)


def appeal_decision(user, identity, body):
    decision = (
        ReviewModerationDecision.objects.select_related("section")
        .filter(id=identity)
        .first()
    )
    if not decision:
        raise NotFound()
    section = decision.section
    if not (
        is_author(section, user)
        or (is_subject(section, user) and released(section.submission.opportunity.case))
    ):
        raise NotFound()

    def action():
        ReviewModerationDecision.objects.select_for_update().get(pk=decision.pk)
        notice = decision_notice(decision, user)
        if timezone.now() >= notice.notified_at + timedelta(days=14):
            raise ReviewError("review_window_closed")
        detail = text_value(body.get("detail", ""), 1500)
        if not detail:
            raise ReviewError("invalid_review_text", 400)
        item = decision.appeals.filter(state="open").first()
        if item:
            if item.appellant_id != user.pk:
                raise ReviewError("review_not_eligible")
            revision(item, body.get("expected_revision"))
            item.detail = text_value(item.detail + "\n" + detail, 4000)
            item.revision += 1
            item.save(update_fields=["detail", "revision", "updated_at"])
        else:
            item = ReviewAppeal.objects.create(
                decision=decision, appellant=user, detail=detail
            )
        return {"id": str(item.id), "state": item.state, "revision": item.revision}

    return command(user, f"review.appeal.{identity}", body, action, decision.id)


def resolve_appeal(user, identity, body):
    appeal = (
        ReviewAppeal.objects.select_related("decision__section")
        .filter(id=identity)
        .first()
    )
    if not appeal:
        raise NotFound()
    require_moderator(user, appeal.decision.section)
    if appeal.decision.actor_id == user.pk or appeal.appellant_id == user.pk:
        raise ReviewError("conflict_of_interest")

    def action():
        locked = ReviewAppeal.objects.select_for_update().get(pk=appeal.pk)
        revision(locked, body.get("expected_revision"))
        if locked.state != "open":
            raise ReviewError("review_not_eligible")
        locked.resolution = text_value(body.get("reason", ""), 1000)
        if not locked.resolution:
            raise ReviewError("invalid_review_text", 400)
        outcome = body.get("outcome", "uphold")
        if outcome not in {"uphold", "restore", "remove", "reject", "hold"}:
            raise ReviewError("invalid_review_target", 400)
        if outcome != "uphold":
            section = sections().get(pk=appeal.decision.section_id)
            content = appeal.decision.reply or section
            moderate(
                user,
                section.id,
                {
                    "request_key": body["request_key"] + ":decision",
                    "expected_revision": content.revision,
                    "action": outcome,
                    "reason": locked.resolution,
                    **({"reply_id": str(content.id)} if content != section else {}),
                },
                appeal=locked,
            )
        locked.state, locked.resolved_by = "resolved", user
        locked.revision += 1
        locked.save()
        audit(locked, user, "appeal_resolved", locked.resolution)
        event(
            appeal.decision.section,
            locked.appellant,
            "review_appeal_resolved",
            str(locked.id),
        )
        return {
            "id": str(locked.id),
            "state": locked.state,
            "revision": locked.revision,
        }

    return command(user, f"review.resolve_appeal.{identity}", body, action, appeal.id)

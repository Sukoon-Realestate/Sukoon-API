"""Separate participant/public projections; recompute aggregates from visible rows."""

from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...models import ReviewSection, ReviewOpportunity, ReviewDecisionNotice
from .policy import label, require_actor
from .eligibility import valid_source


def subject_user(section):
    case = section.submission.opportunity.case
    if subject_company(section):
        return None
    if section.subject_kind.startswith("property_"):
        if case.context_type == "legacy" and not case.source_snapshot.get(
            "historical_reply_authority"
        ):
            return None
        return case.party_b
    if section.subject_id == case.party_a.id:
        return case.party_a
    if section.subject_id == case.party_b.id:
        return case.party_b
    return None


def subject_company(section):
    case = section.submission.opportunity.case
    if section.subject_kind == "organization_renter":
        return case.company
    if (
        section.subject_kind == "organization_landlord"
        or section.subject_kind.startswith("property_")
    ):
        return case.landlord_company
    return None


def is_author(section, user):
    opportunity = section.submission.opportunity
    if opportunity.reviewer_company_id:
        from .company_authority import permitted

        return permitted(
            user,
            opportunity.case.company_binding,
            opportunity.reviewer_company,
            submit=True,
        )
    return bool(user and user.is_authenticated and opportunity.reviewer_id == user.pk)


def is_subject(section, user):
    company = subject_company(section)
    if company:
        from .company_authority import permitted

        return permitted(
            user,
            section.submission.opportunity.case.company_binding,
            company,
            history=True,
        )
    target = subject_user(section)
    return bool(user and user.is_authenticated and target and target.pk == user.pk)


def released(case):
    # Deadline is fixed and irreversible even when the worker is delayed.
    return bool(
        case.gate_released_at
        or timezone.now() >= case.closes_at
        or case.release_mode == "after_moderation"
    )


def published(section):
    return (
        section.content_state == "approved"
        and released(section.submission.opportunity.case)
        and valid_source(section.submission.opportunity.case)
    )


def visible(section, user=None, *, public_only=False):
    if not published(section):
        return False
    if section.audience == "public":
        return True
    return not public_only and (is_author(section, user) or is_subject(section, user))


def sections():
    return ReviewSection.objects.select_related(
        "submission__opportunity__reviewer",
        "submission__opportunity__case__party_a",
        "submission__opportunity__case__party_b",
        "submission__opportunity__case__lease",
        "submission__opportunity__case__peer_lease",
        "submission__opportunity__case__visit",
    )


def participant_metadata(section, user):
    return (
        is_subject(section, user)
        and released(section.submission.opportunity.case)
        and (section.decisions.exists() or hasattr(section, "reply"))
    )


def decision_notice(decision, user):
    # The first authorized in-app read is also an actual decision notification.
    notice, _ = ReviewDecisionNotice.objects.get_or_create(
        decision=decision, recipient=user, defaults={"notified_at": timezone.now()}
    )
    return notice


def section_for(user, identity):
    item = sections().filter(id=identity).first()
    if not item or not (
        visible(item, user) or is_author(item, user) or participant_metadata(item, user)
    ):
        raise NotFound()
    return item


def opportunity_payload(item, user=None):
    case = item.case
    state = item.state
    if state == "open" and timezone.now() >= case.closes_at:
        state = "expired"
    if case.revocation_reason:
        state = "revoked"
    from django.conf import settings

    from .company_authority import permitted

    authorized = (
        permitted(user, case.company_binding, item.reviewer_company, submit=True)
        if item.reviewer_company_id
        else bool(
            item.reviewer and item.reviewer.is_active and item.reviewer.is_verified
        )
    )
    can_submit = (
        authorized
        and state == "open"
        and valid_source(case)
        and getattr(settings, "REVIEWS_ENABLED", False)
    )
    targets = [
        {
            **{k: v for k, v in t.items() if k != "id"},
            "label": label(t["kind"]),
            "criteria": [
                {"code": code, "label": label(code)} for code in t["criteria"]
            ],
            "tags": [{"code": code, "label": label(code)} for code in t["tag_codes"]],
        }
        for t in item.allowed_targets
    ]
    return {
        "id": str(item.id),
        "context_type": case.context_type,
        "state": state,
        "revision": item.revision,
        "policy_version": case.policy_version,
        "criteria_schema_version": case.criteria_schema_version,
        "opens_at": case.opens_at.isoformat(),
        "closes_at": case.closes_at.isoformat(),
        "release_mode": case.release_mode,
        "gate_state": "released" if released(case) else "waiting",
        "reviewer": {
            "kind": "company" if item.reviewer_company_id else "person",
            "role": item.reviewer_role,
            "company_id": (
                str(item.reviewer_company.id) if item.reviewer_company_id else None
            ),
            "company_name": (
                item.reviewer_company.name if item.reviewer_company_id else None
            ),
        },
        "allowed_targets": targets,
        "allowed_actions": ["save_draft", "submit"] if can_submit else [],
        "blocking_reason_codes": (
            []
            if can_submit or state == "submitted"
            else [
                "review_window_closed" if state == "expired" else "review_not_eligible"
            ]
        ),
        "reminders_enabled": item.reminders_enabled,
    }


def section_payload(item, user=None, *, public_only=False):
    author = not public_only and is_author(item, user)
    metadata_only = (
        not public_only and participant_metadata(item, user) and not visible(item, user)
    )
    if (
        not author
        and not metadata_only
        and not visible(item, user, public_only=public_only)
    ):
        raise NotFound()
    case = item.submission.opportunity.case
    # No person/profile link, precise dates, accommodation ID, or acting user.
    data = {
        "id": str(item.id),
        "subject_kind": item.subject_kind,
        "label": label(item.subject_kind),
        "overall_score": item.overall_score,
        "criteria": item.criteria,
        "comment": item.public_comment,
        "tag_codes": item.tag_codes,
        "month": item.created_at.strftime("%Y-%m"),
        "verification_basis": item.verification_basis,
        "audience": item.audience,
        "revision": item.revision,
        "allowed_actions": [],
        "management_changed": bool(
            item.subject_kind.startswith("property_")
            and case.property.owner_id != case.party_b_id
        ),
    }
    if metadata_only:
        for field in ["overall_score", "criteria", "comment", "tag_codes"]:
            data.pop(field, None)
        data.update(content_state=item.content_state, gate_state="released")
    if author:
        data.update(
            content_state=item.content_state,
            gate_state="released" if released(case) else "waiting",
            opportunity_id=str(item.submission.opportunity.id),
        )
        if item.content_state != "withdrawn":
            data["allowed_actions"].append("withdraw")
    if user and user.is_authenticated and visible(item, user):
        data["allowed_actions"].append("report")
        if is_subject(item, user) and not hasattr(item, "reply"):
            from .company_authority import permitted

            company = subject_company(item)
            if not company or permitted(
                user, case.company_binding, company, submit=True
            ):
                data["allowed_actions"].append("reply")
    if hasattr(item, "reply") and (
        (
            visible(item, user, public_only=public_only)
            and item.reply.content_state == "approved"
        )
        or (not public_only and reply_authorized(item.reply, user))
    ):
        data["reply"] = {
            "id": str(item.reply.id),
            "comment": item.reply.public_comment,
            "revision": item.reply.revision,
            "content_state": item.reply.content_state,
            "can_withdraw": not public_only
            and item.reply.content_state != "withdrawn"
            and reply_authorized(item.reply, user),
        }
    if not public_only and (author or is_subject(item, user)):
        data["decisions"] = []
        for decision in item.decisions.all():
            notice = decision_notice(decision, user)
            data["decisions"].append(
                {
                    "id": str(decision.id),
                    "reason": decision.reason,
                    "action": decision.action,
                    "notified_at": notice.notified_at.isoformat(),
                    "can_appeal": timezone.now()
                    < notice.notified_at
                    + timedelta(days=case.policy_snapshot.get("appeal_window_days", 14))
                    and not decision.appeals.filter(state="open").exists(),
                }
            )
    return data


def subject_rows(kind, identity, user=None, *, aggregate=False):
    public = kind in {
        "property_visit",
        "property_stay",
        "person_landlord",
        "organization_landlord",
    }
    if not public:
        require_actor(user)
        # A former landlord can inspect their own section, never a tenant's entire history.
        if kind == "organization_renter":
            from .company_authority import company_history

            if not company_history(user, identity):
                raise NotFound()
        elif str(user.id) != str(identity):
            raise NotFound()
    return [
        s
        for s in sections()
        .filter(subject_kind=kind, subject_id=identity, content_state="approved")
        .order_by("-created_at", "-id")
        if visible(s, user, public_only=public)
        and (not aggregate or s.verification_basis != "legacy_unverified")
    ]


def summary(kind, identity, user=None):
    return summarize_rows(kind, subject_rows(kind, identity, user, aggregate=True))


def summarize_rows(kind, rows):
    def avg(values):
        return (
            float(
                (sum(Decimal(v) for v in values) / len(values)).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
            )
            if values
            else None
        )

    criteria = {}
    for row in rows:
        for key, value in row.criteria.items():
            if value is not None:
                criteria.setdefault(key, []).append(value)
    return {
        "subject_kind": kind,
        "average": avg([s.overall_score for s in rows]),
        "review_count": len(rows),
        "distinct_experience_count": len(
            {
                s.submission.opportunity.case.source_snapshot.get(
                    "experience_group_id", str(s.submission.opportunity.case_id)
                )
                for s in rows
            }
        ),
        "limited_sample": len(rows) < 3,
        "distribution": {
            str(i): sum(s.overall_score == i for s in rows) for i in range(1, 6)
        },
        "criteria": {
            k: {"average": avg(v), "answered_count": len(v), "label": label(k)}
            for k, v in criteria.items()
        },
        "aggregation_version": "rating-v1-live",
        "computed_at": timezone.now().isoformat(),
    }


def subject_recipients(section):
    company = subject_company(section)
    if company:
        from .company_authority import recipients, permitted

        binding = section.submission.opportunity.case.company_binding
        return [
            u
            for u in recipients(binding, company)
            if permitted(u, binding, company, history=True)
        ]
    person = subject_user(section)
    return [person] if person else []


def author_recipients(section):
    opp = section.submission.opportunity
    if opp.reviewer_company_id:
        from .company_authority import recipients

        return recipients(opp.case.company_binding, opp.reviewer_company, submit=True)
    return [opp.reviewer]


def notify_subject(section, kind, suffix=""):
    from .generation import event

    for user in subject_recipients(section):
        event(section, user, kind, suffix)


def notify_author(section, kind, suffix=""):
    from .generation import event

    for user in author_recipients(section):
        event(section, user, kind, suffix)


def reply_authorized(reply, user):
    if reply.author_company_id:
        from .company_authority import permitted

        return permitted(
            user,
            reply.section.submission.opportunity.case.company_binding,
            reply.author_company,
            submit=True,
        )
    return reply.author_id == getattr(user, "pk", None)

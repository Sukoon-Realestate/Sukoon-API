from django.utils import timezone
from rest_framework.exceptions import NotFound, APIException
from ...models import CompanyTermsNegotiation, RentalAuditEvent
from ...planning_models import PlanningEvent
from . import negotiation_access as access, negotiation_binding as binding


def actions(item, user):
    role = access.role(item, user)
    available = []
    if role in {"owner", "coordinator"}:
        if item.status in {"proposed", "changes_requested"}:
            available = (
                ["edit"]
                if item.author_id == user.pk
                else ["counter", "accept", "reject", "request-changes"]
            ) + ["withdraw"]
        elif item.status == "accepted":
            available = ["withdraw"]
    blockers = []
    if item.expires_at <= timezone.now():
        blockers.append("negotiation_expired")
    if (
        item.followed_at
        or item.booking.hold_id
        or item.booking.invitation_id
        or item.booking.lease_id
    ):
        blockers.append("followup_started")
    if not blockers and available:
        try:
            binding.current(item)
        except APIException as exc:
            code = exc.get_codes()
            blockers.append(code if isinstance(code, str) else "source_changed")
    allowed = available
    if blockers:
        allowed = (
            ["withdraw"]
            if "withdraw" in available
            and not {"negotiation_expired", "followup_started"}.intersection(blockers)
            else []
        )
    from core_apps.users.services.new_business import restricted_accounts
    from .access import booking_account_parties

    if available and restricted_accounts(
        *booking_account_parties(item.booking.id, include_preparation=False)
    ):
        blockers.append("account_closure_pending")
        allowed = [
            action for action in allowed if action not in {"edit", "counter", "accept"}
        ]
    return available, allowed, blockers


def payload(item, user):
    available, allowed, blockers = actions(item, user)
    return {
        "id": str(item.id),
        "booking_id": str(item.booking.id),
        "company_id": str(item.booking.request.company.id),
        "company_name": item.booking.request.company.name,
        "revision": item.revision,
        "content_revision": item.content_revision,
        "status": (
            "expired"
            if item.expires_at <= timezone.now()
            and not item.followed_at
            and item.status in {"proposed", "changes_requested", "accepted"}
            else item.status
        ),
        "author_id": str(item.author.id),
        "author_name": item.author.get_full_name,
        "workspace": "owner" if access.role(item, user) == "owner" else "company",
        "terms": item.terms,
        "terms_digest": item.terms_digest,
        "inventory": item.source_snapshot["inventory"],
        "expires_at": item.expires_at.isoformat(),
        "followed_at": item.followed_at.isoformat() if item.followed_at else None,
        "available_actions": available,
        "allowed_actions": allowed,
        "blocking_reasons": blockers,
        "versions": [
            {
                "version": v.version,
                "author_name": v.author.get_full_name,
                "terms": v.terms,
                "expires_at": v.expires_at.isoformat(),
                "created_at": v.created_at.isoformat(),
            }
            for v in item.versions.select_related("author").order_by("version")
        ],
        "history": [
            {
                "action": e.action,
                "revision": e.subject_revision,
                "reason": e.reason,
                "created_at": e.created_at.isoformat(),
            }
            for e in RentalAuditEvent.objects.filter(
                subject_kind="companytermsnegotiation", subject_id=item.id
            ).order_by("created_at", "pk")
        ],
    }


def notify(item, action):
    users = [item.owner, item.coordinator]
    if item.booking.assigned_approver_id:
        users.append(item.booking.assigned_approver.user)
    for user in {u.pk: u for u in users}.values():
        role = access.role(item, user)
        if not role:
            continue
        PlanningEvent.objects.get_or_create(
            recipient=user,
            event_key=f"company.terms:{item.id}:{item.revision}",
            defaults={
                "destination": {
                    "action_type": "open_company_terms",
                    "target_id": str(item.id),
                    "company_id": str(item.booking.request.company.id),
                    "booking_id": str(item.booking.id),
                    "workspace": "owner" if role == "owner" else "company",
                    "schema_version": "1",
                    "revision": item.revision,
                    "event_kind": "company_terms_updated",
                    "change_kind": action,
                }
            },
        )


def authorize(event):
    item = access.get(event.recipient, event.destination["target_id"])
    scope = "owner" if access.role(item, event.recipient) == "owner" else "company"
    if (
        event.destination.get("company_id") != str(item.booking.request.company.id)
        or event.destination.get("booking_id") != str(item.booking.id)
        or event.destination.get("workspace") != scope
    ):
        raise NotFound()
    return {
        "title": "تحديث شروط سكن الشركة / Company terms updated",
        "body": (
            "راجع النسخة الحالية والتاريخ والموافقة المطلوبة. / "
            "Review the current version, history and required approval."
        ),
    }


def visible(user):
    from django.db.models import Q

    return CompanyTermsNegotiation.objects.filter(
        Q(owner=user, booking__offer__owner=user)
        | Q(coordinator=user, booking__request__coordinator=user)
        | Q(booking__assigned_approver__user=user)
    )

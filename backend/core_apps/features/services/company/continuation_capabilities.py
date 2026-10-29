"""Read-only authority for a company's existing continuation signing session."""

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from ...models import CompanyTenancyChange
from ...providers import signing_available
from ..rental_phase2 import RentalConflict
from .tenancy_changes import authorize_role
from .tenancy_commercial import KINDS


def authorize_current_signatory(user, event):
    """Reauthorize receipts independently of a session's pending/completed state."""
    current = User.objects.get(pk=user.pk)
    review = (
        CompanyTenancyChange.objects.select_related("tenancy__lease")
        .filter(rental_change=event, tenancy__lease=event.lease, kind__in=KINDS)
        .first()
    )
    if review and event.lease.renter_company_id:
        for role in ("owner", "signer"):
            if review.snapshot["required"].get(role) == str(current.id):
                authorize_role(review.tenancy, review, current, role, positive=True)
                return review
    raise PermissionDenied(
        "Only the named participant may decide their responsibility."
    )


def require_pending_session(user, event, review, *, session=None):
    """A fresh synthetic completion must identify this actor's current document."""
    if (
        signing_available()
        and review.state == "pending_signatures"
        and event.status == "pending_signatures"
        and event.document_id
        and event.document_hash
        and str(user.id) not in event.signed_by
    ):
        sessions = event.signing_sessions.filter(
            signer=user,
            status="pending",
            expires_at__gt=timezone.now(),
            change_revision=event.revision,
            document_id=event.document_id,
            document_hash=event.document_hash,
        )
        if session is not None:
            sessions = sessions.filter(pk=session.pk)
        if sessions.exists():
            return
    raise RentalConflict(
        "The requested rental action is not available yet.",
        code="continuation_signing_unavailable",
    )


def completion_actions(user, event):
    try:
        review = authorize_current_signatory(user, event)
        require_pending_session(user, event, review)
    except (PermissionDenied, RentalConflict):
        return []
    return ["sign"]

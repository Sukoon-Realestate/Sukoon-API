from core_apps.users.models import User
from core_apps.properties.models import Property
from ...models import (
    ApplicationProfile,
    ApplicationProfileVersion,
    ApplicationAccessGrant,
    ReservationHold,
    GroupBookingProposal,
    Lease,
    TermsProposal,
)
from ...planning_models import GroupProcess
from .common import policy_available
from .reservations import hold_actions
from .group_bookings import booking_payload
from .cases import case_payload


def lifecycle_capabilities(user, subject):
    actions = []
    if isinstance(subject, User) and subject.pk == user.pk:
        actions = ["save_application"]
    elif isinstance(subject, ApplicationProfile) and subject.applicant_id == user.pk:
        actions = ["save_application", "freeze_application"]
    elif (
        isinstance(subject, ApplicationProfileVersion)
        and subject.profile.applicant_id == user.pk
        and policy_available("application_sharing")
    ):
        actions = ["share_application"]
    elif (
        isinstance(subject, ApplicationAccessGrant)
        and subject.applicant_id == user.pk
        and not subject.revoked_at
    ):
        actions = ["revoke_application_share"]
    elif isinstance(subject, Property):
        if subject.owner_id == user.pk:
            actions = ["confirm_availability", "save_decision_fact"]
            if policy_available("reservations"):
                actions.append("create_availability_block")
        elif policy_available("reservations"):
            actions.append("create_hold")
    elif isinstance(subject, ReservationHold):
        actions = hold_actions(subject, user)
    elif (
        isinstance(subject, Lease)
        and user.pk in {subject.owner_id, subject.tenant_id}
        and not subject.legacy_read_only
    ):
        actions = ["create_rental_case"]
    elif (
        isinstance(subject, TermsProposal)
        and subject.owner_id == user.pk
        and not subject.invitations.filter(lease__isnull=False).exists()
        and subject.status not in {"rejected", "superseded"}
    ):
        actions = ["propose_answer"]
    elif (
        isinstance(subject, GroupProcess)
        and subject.property.owner_id == user.pk
        and policy_available("independent_group_booking")
    ):
        actions = ["create_group_booking"]
    elif isinstance(subject, GroupBookingProposal):
        actions = booking_payload(subject, user)["allowed_actions"]
    else:
        from ...models import RentalOperationalCase

        if isinstance(subject, RentalOperationalCase):
            actions = case_payload(subject, user)["allowed_actions"]
    return (["rental_lifecycle"] if actions else []), actions

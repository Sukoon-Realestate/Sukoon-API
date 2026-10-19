"""Review exact tenancy changes without proxy consent or automatic debt transfer."""

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from ...models import CompanyTenancyChange, CompanyMembership
from ..rental_phase2 import RentalConflict, fingerprint
from ..rental_lifecycle.common import audit
from . import tenancy_access as access


def current_roles(item):
    return {
        "owner": str(item.lease.owner.id),
        "coordinator": str(item.coordinator.id),
        "signer": str(item.signer_mandate.membership.user.id),
        "payer": str(item.payer_mandate.membership.user.id),
    }


def propose(item, user, kind, content, required, reason):
    if item.changes.filter(
        kind=kind, state__in=["pending", "waiting_departure"]
    ).exists():
        raise RentalConflict(
            "Resolve or withdraw the existing change before proposing another."
        )
    snapshot = {
        "content": content,
        "required": required,
        "terms_digest": item.terms_digest,
        "actor_epochs": {
            str(u.id): u.security_epoch
            for u in User.objects.filter(id__in=required.values())
        },
    }
    change = CompanyTenancyChange.objects.create(
        tenancy=item,
        kind=kind,
        proposed_by=user,
        snapshot=snapshot,
        snapshot_digest=fingerprint(snapshot),
        reason=reason,
    )
    audit(change, user, "company_tenancy_change_proposed", reason)
    return access.changed(item, user, "company_tenancy_change_opened", reason)


def authorize_role(item, change, user, role, *, positive):
    if not user.is_active or (positive and not user.is_verified):
        raise PermissionDenied("Current verified account access is required.")
    if change.snapshot["required"].get(role) != str(user.id):
        raise PermissionDenied(
            "Only the named participant may decide their responsibility."
        )
    roles = current_roles(item)
    if role in roles and roles[role] != str(user.id):
        raise PermissionDenied("This responsibility has been reassigned.")
    if role in {"owner", "coordinator", "signer", "payer", "administrator"}:
        access.require_role(item, user, {role}, sensitive=positive)
    if positive and role in {"signer", "payer"}:
        access.require_delegate(item, user, "sign" if role == "signer" else "pay")
    if positive and role in {"new_signer", "new_payer"}:
        from ...models import CompanyMandate

        key = "signer" if role == "new_signer" else "payer"
        mandate = CompanyMandate.objects.get(
            id=change.snapshot["content"][key + "_mandate_id"]
        )
        if mandate.membership.user_id != user.pk or not access.execution_mandate(
            mandate,
            exposure=item.source_snapshot["full_term_rent_minor"]
            + item.source_snapshot["deposit_minor"],
        ):
            raise PermissionDenied(
                "Replacement execution authority is no longer valid."
            )
    if (
        positive
        and role == "incoming_employee"
        and not CompanyMembership.objects.filter(
            company=item.lease.renter_company,
            user=user,
            is_active=True,
            is_employee=True,
            user__is_verified=True,
            user__sensitive_actions_frozen=False,
        ).exists()
    ):
        raise PermissionDenied(
            "The incoming employee needs current active company access."
        )
    if (
        positive
        and role == "new_coordinator"
        and not CompanyMembership.objects.filter(
            company=item.lease.renter_company,
            user=user,
            is_active=True,
            is_coordinator=True,
            id=change.snapshot["content"]["coordinator_membership_id"],
            revision=change.snapshot["content"]["coordinator_revision"],
        ).exists()
    ):
        raise PermissionDenied(
            "The incoming coordinator needs current assigned company authority."
        )
    if positive and (
        user.security_epoch != change.snapshot["actor_epochs"].get(str(user.id))
        or user.sensitive_actions_frozen
    ):
        raise RentalConflict("Account authority changed; propose a fresh review.")


def respond(item, user, data):
    change = get_object_or_404(
        CompanyTenancyChange.objects.select_for_update(),
        id=data["change_id"],
        tenancy=item,
    )
    if change.state != "pending" or change.snapshot_digest != data["digest"]:
        raise RentalConflict("Review the current pending change.")
    role, decision = data["role"], data["decision"]
    if decision not in {"accept", "decline"}:
        raise RentalConflict("Choose accept or decline.")
    authorize_role(item, change, user, role, positive=decision == "accept")
    if role in change.decisions:
        raise RentalConflict("Your decision is already recorded for this revision.")
    change.decisions[role] = {"actor_id": str(user.id), "decision": decision}
    if decision == "decline":
        change.state = "declined"
    elif set(change.snapshot["required"]).issubset(change.decisions):
        for name, actor_id in change.snapshot["required"].items():
            actor = User.objects.get(id=actor_id)
            if not actor.is_active or not actor.is_verified:
                raise RentalConflict(
                    "A required participant no longer has active verified access."
                )
            authorize_role(item, change, actor, name, positive=True)
        change.state = "accepted"
    change.revision += 1
    change.save()
    if change.state == "accepted":
        apply(item, change)
    audit(change, user, "company_tenancy_change_" + decision, data["reason"])
    return access.changed(
        item, user, "company_tenancy_decision_recorded", data["reason"]
    )


def withdraw(item, user, data):
    change = get_object_or_404(
        CompanyTenancyChange.objects.select_for_update(),
        id=data["change_id"],
        tenancy=item,
    )
    if change.state not in {"pending", "waiting_departure"}:
        raise RentalConflict("An applied or closed change cannot be withdrawn.")
    if user.pk != change.proposed_by_id and not access.roles(item, user) & {
        "coordinator"
    }:
        raise PermissionDenied(
            "Only the proposer or assigned coordinator can withdraw this change."
        )
    change.state = "withdrawn"
    change.revision += 1
    change.save()
    audit(change, user, "company_tenancy_change_withdrawn", data["reason"])
    return access.changed(
        item, user, "company_tenancy_change_withdrawn", data["reason"]
    )


def apply(item, change):
    from . import tenancy_occupancy, tenancy_closure

    if change.snapshot["terms_digest"] != item.terms_digest:
        raise RentalConflict("The underlying company contract changed.")
    if change.kind == "replacement":
        applied = tenancy_occupancy.apply_replacement(item, change)
        if not applied:
            change.state = "waiting_departure"
            change.save()
            return
    elif change.kind in {"move_in", "move_out"}:
        tenancy_occupancy.apply_handover(item, change)
    elif change.kind == "termination":
        tenancy_closure.apply_termination(item, change)
    elif change.kind == "settlement":
        tenancy_closure.apply_settlement(item, change)
    elif change.kind == "authority":
        tenancy_closure.apply_authority(item, change)
    else:
        raise RentalConflict("Unsupported company tenancy change.")
    change.state, change.applied_at = "applied", timezone.now()
    change.save()


def resume(item, user, data):
    access.require_role(item, user, {"coordinator"})
    change = get_object_or_404(
        CompanyTenancyChange.objects.select_for_update(),
        id=data["change_id"],
        tenancy=item,
    )
    if change.state != "waiting_departure":
        raise RentalConflict(
            "Only a reviewed replacement awaiting departure can resume."
        )
    for name, identity in change.snapshot["required"].items():
        authorize_role(item, change, User.objects.get(id=identity), name, positive=True)
    apply(item, change)
    return access.changed(item, user, "company_tenancy_change_resumed")

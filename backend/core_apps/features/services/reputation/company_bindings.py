"""Bind a genuinely signed canonical lease to explicitly confirmed company parties."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound
from ...models import (
    Company,
    CompanyBookingItem,
    CompanyLeaseBinding,
    CompanyMembership,
    CompanyReviewAuthority,
    Lease,
    ReviewCase,
)
from .company_authority import membership
from .policy import ReviewError, revision, require_actor, require_enabled
from .submission import command, audit


def signed(lease):
    signers = set(
        lease.signing_sessions.filter(
            status="completed",
            completed_at__isnull=False,
            document_id=lease.document_id,
            document_hash=lease.document_hash,
        ).values_list("signer_id", flat=True)
    )
    if (
        lease.legacy_read_only
        or lease.status not in {"signed", "active", "termination_pending", "ended"}
        or not lease.document_id
        or not lease.document_hash
        or not {lease.owner_id, lease.tenant_id}.issubset(signers)
    ):
        raise ReviewError("signed_lease_required")


def required_roles(item):
    roles = ["lease_owner", "lease_tenant"]
    return roles + [
        role
        for role in ("renter_company", "landlord_company")
        if getattr(item, f"{role}_id")
    ]


def check_role(user, item, role):
    require_actor(user)
    if role in {"lease_owner", "lease_tenant"}:
        if user.pk != getattr(
            item.lease, "owner_id" if role == "lease_owner" else "tenant_id"
        ):
            raise NotFound()
        if not user.is_verified:
            raise ReviewError("review_not_eligible", 403)
    elif role in {"renter_company", "landlord_company"} and getattr(item, f"{role}_id"):
        member = membership(user, getattr(item, role), signer=True)
        if not member.is_admin and (
            role != "renter_company"
            or not item.booking_id
            or item.booking.request.coordinator_id != user.pk
        ):
            raise NotFound()
    else:
        raise NotFound()


def can_read(user, item):
    require_actor(user)
    if user.pk in {item.lease.owner_id, item.lease.tenant_id}:
        return True
    from .responsibility import transitions

    if transitions(item.lease).filter(next_owner=user).exists():
        return True
    return (
        CompanyMembership.objects.filter(
            user=user,
            is_active=True,
            company_id__in=[item.renter_company_id, item.landlord_company_id],
        )
        .filter(
            Q(is_admin=True)
            | Q(
                is_coordinator=True,
                user_id=(
                    item.booking.request.coordinator_id if item.booking_id else None
                ),
            )
        )
        .exists()
    )


def get(user, identity):
    item = get_object_or_404(CompanyLeaseBinding, id=identity)
    if not can_read(user, item):
        raise NotFound()
    return item


def payload(item, user):
    roles = []
    for role in required_roles(item):
        try:
            check_role(user, item, role)
            roles.append(role)
        except (NotFound, ReviewError):
            pass
    return {
        "id": str(item.id),
        "lease_id": str(item.lease.id),
        "property_name": item.lease.property.title,
        "state": item.state,
        "revision": item.revision,
        "can_assign": item.state == "accepted"
        and item.booking_id is not None
        and (
            user.pk == item.booking.request.coordinator_id
            or CompanyMembership.objects.filter(
                user=user,
                company_id=item.renter_company_id,
                is_active=True,
                is_admin=True,
            ).exists()
        ),
        "can_manage_authorities": item.state == "accepted"
        and CompanyMembership.objects.filter(
            user=user,
            is_active=True,
            is_admin=True,
            company_id__in=[item.renter_company_id, item.landlord_company_id],
        ).exists(),
        "renter_company_id": (
            str(item.renter_company.id) if item.renter_company_id else None
        ),
        "landlord_company_id": (
            str(item.landlord_company.id) if item.landlord_company_id else None
        ),
        "can_view_assignments": item.state == "accepted"
        and item.booking_id is not None,
        "required_roles": required_roles(item),
        "confirmed_roles": list(item.approvals),
        "allowed_roles": (
            [r for r in roles if r not in item.approvals]
            if item.state == "pending"
            else []
        ),
    }


def source(item):
    signed(item.lease)
    lease = item.lease
    data = {
        "document_id": str(lease.document_id),
        "document_hash": lease.document_hash,
        "owner_id": str(lease.owner.id),
        "tenant_id": str(lease.tenant.id),
        "property_id": str(lease.property.id),
    }
    if item.renter_company_id:
        booking = item.booking
        if (
            not booking
            or booking.request.company_id != item.renter_company_id
            or booking.offer.owner_id != lease.owner_id
            or booking.lease_id not in {None, lease.pk}
            or not any(
                str(u.get("id")) == str(lease.property.id)
                for u in booking.snapshot.get("units", [])
            )
            or lease.start_date < booking.request.starts_on
            or lease.end_date > booking.request.ends_on_exclusive
            or not booking.approvals.filter(
                decision="approved",
                commercial_revision=booking.commercial_revision,
                snapshot_digest=booking.snapshot_digest,
            ).exists()
        ):
            raise ReviewError("company_lease_mismatch")
        data.update(
            booking_id=str(booking.id),
            booking_revision=booking.commercial_revision,
            booking_digest=booking.snapshot_digest,
            inventory_snapshot=booking.snapshot,
        )
    return data


def propose(user, body):
    require_actor(user)
    lease = get_object_or_404(Lease, id=body.get("lease_id"))

    def action():
        require_enabled()
        from .eligibility import lock_tenancy

        locked = lock_tenancy(lease)
        if (
            CompanyLeaseBinding.objects.filter(
                lease__tenancy_root_id=locked.tenancy_root_id
            ).exists()
            or ReviewCase.objects.filter(
                lease__tenancy_root_id=locked.tenancy_root_id
            ).exists()
        ):
            raise ReviewError("revision_conflict")
        renter = (
            get_object_or_404(Company, id=body["renter_company_id"])
            if body.get("renter_company_id")
            else None
        )
        landlord = (
            get_object_or_404(Company, id=body["landlord_company_id"])
            if body.get("landlord_company_id")
            else None
        )
        if not (renter or landlord) or renter == landlord:
            raise ReviewError("invalid_review_target", 400)
        booking = (
            get_object_or_404(
                CompanyBookingItem.objects.select_for_update(),
                id=body.get("booking_id"),
            )
            if renter
            else None
        )
        item = CompanyLeaseBinding(
            lease=locked,
            renter_company=renter,
            landlord_company=landlord,
            booking=booking,
            proposed_by=user,
        )
        if not can_read(user, item):
            raise NotFound()
        item.source_snapshot = source(item)
        item.save()
        audit(item, user, "company_lease_binding_proposed")
        return payload(item, user)

    return command(user, f"review.binding.propose.{lease.id}", body, action, lease.id)


def confirm(user, identity, body):
    item = get(user, identity)
    role = body.get("role")
    check_role(user, item, role)

    def action():
        from .eligibility import lock_tenancy

        lock_tenancy(item.lease)
        locked = CompanyLeaseBinding.objects.select_for_update().get(pk=item.pk)
        check_role(user, locked, role)
        revision(locked, body.get("expected_revision"))
        if locked.state != "pending" or source(locked) != locked.source_snapshot:
            raise ReviewError("revision_conflict")
        locked.approvals[role] = {
            "user_id": str(user.id),
            "at": timezone.now().isoformat(),
        }
        if set(required_roles(locked)).issubset(locked.approvals):
            from django.contrib.auth import get_user_model

            for name, approval in locked.approvals.items():
                actor = get_object_or_404(get_user_model(), id=approval["user_id"])
                check_role(actor, locked, name)
            if ReviewCase.objects.filter(
                lease__tenancy_root_id=locked.lease.tenancy_root_id
            ).exists():
                raise ReviewError("revision_conflict")
            locked.state, locked.accepted_at = "accepted", timezone.now()
            if locked.booking_id:
                locked.booking.lease = locked.lease
                locked.booking.save(update_fields=["lease", "updated_at"])
        locked.revision += 1
        locked.save()
        audit(locked, user, "company_lease_binding_confirmed")
        if locked.state == "accepted":
            from django.conf import settings

            if getattr(settings, "REVIEWS_ENABLED", False):
                from .generation import generate_tenancy

                try:
                    generate_tenancy(locked.lease)
                except ReviewError as error:
                    if error.get_codes() not in {
                        "experience_not_confirmed",
                        "occupancy_not_ended",
                        "review_window_closed",
                    }:
                        raise
        return payload(locked, user)

    return command(user, f"review.binding.confirm.{identity}", body, action, item.id)


def authority(user, identity, body):
    item = get(user, identity)
    member = get_object_or_404(
        CompanyMembership,
        id=body.get("membership_id"),
        company_id__in=[item.renter_company_id, item.landlord_company_id],
    )
    membership(user, member.company, admin=True)

    def action():
        locked = CompanyLeaseBinding.objects.select_for_update().get(pk=item.pk)
        membership(user, member.company, admin=True, lock=True)
        current = CompanyMembership.objects.select_for_update().get(pk=member.pk)
        if locked.state != "accepted" or not current.is_active:
            raise ReviewError("review_not_eligible")
        fields = ("is_active", "can_submit", "can_view_reputation")
        if any(type(body.get(k)) is not bool for k in fields):
            raise ReviewError("invalid_review_target", 400)
        record = CompanyReviewAuthority.objects.filter(
            binding=locked, membership=member
        ).first()
        if body.get("expected_revision") != (record.revision if record else 0):
            raise ReviewError("revision_conflict")
        record = record or CompanyReviewAuthority(
            binding=locked, membership=member, granted_by=user, revision=0
        )
        for key in fields:
            setattr(record, key, body[key])
        record.revision += 1
        record.granted_by = user
        record.save()
        audit(record, user, "company_review_authority_changed")
        if record.is_active and record.can_submit:
            from .generation import event
            from ...models import ReviewOpportunity

            for opp in ReviewOpportunity.objects.filter(
                case__company_binding=locked,
                case__revocation_reason="",
                reviewer_company=member.company,
                state="open",
                case__closes_at__gt=timezone.now(),
            ):
                event(opp, member.user, "review_opportunity_opened")
        return {
            "id": str(record.id),
            "membership_id": str(member.id),
            "revision": record.revision,
            **{k: getattr(record, k) for k in fields},
        }

    return command(user, f"review.binding.authority.{identity}", body, action, item.id)

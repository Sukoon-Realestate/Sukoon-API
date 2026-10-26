"""One account-wide review; erasure never cancels an obligation or a payment."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from core_apps.common.idempotency import execute_idempotent, request_key
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.admin_api.permissions import require_staff_actor
from ..models import (
    User,
    AccountClosureRequest,
    AccountClosureDecision,
    AccountClosureNotice,
)
from .closure_blockers import blockers
from .sessions import validate_session, revoke_all
from .sensitive_actions import consume

REVIEW_ROLES = {"system_owner", "account_closure_reviewer"}


def latest(user):
    return (
        AccountClosureRequest.objects.filter(user=user).order_by("-created_at").first()
    )


def projection(item, *, review=False):
    if item is None:
        return None
    value = {
        "id": str(item.id),
        "revision": item.revision,
        "status": item.status,
        "active": item.active,
        "reason": item.reason,
        "decision_reason": item.decision_reason,
        "created_at": item.created_at.isoformat(),
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "erasure_pending": item.accountprofileerasurefile_set.filter(
            deleted_at__isnull=True
        ).exists(),
        "blockers": blockers(item.user) if item.active else [],
        "history": [
            {
                "action": d.action,
                "revision": d.revision,
                "reason": d.reason,
                "at": d.created_at.isoformat(),
                "blockers": d.blockers,
            }
            for d in item.decisions.order_by("created_at")
        ],
    }
    if review:
        value.update(user_id=str(item.user.id), account_name=item.user.get_full_name)
    return value


def summary(user):
    item = latest(user)
    return {
        "account_id": str(user.id),
        "request": projection(item),
        "expected_revision": item.revision if item else 0,
        "new_business_restricted": bool(item and item.active),
        "history": [
            {
                "request_id": str(event.request.id),
                "action": event.action,
                "revision": event.revision,
                "reason": event.reason,
                "at": event.created_at.isoformat(),
            }
            for event in AccountClosureDecision.objects.filter(request__user=user)
            .select_related("request")
            .order_by("created_at")
        ],
    }


def _event(item, actor, action, reason="", barriers=None):
    decision = AccountClosureDecision.objects.create(
        request=item,
        actor=actor,
        action=action,
        revision=item.revision,
        reason=reason,
        blockers=barriers or [],
    )
    AccountClosureNotice.objects.create(decision=decision, email_to=item.user.email)
    if action != "completed":
        from core_apps.notifications.models import Notification
        from core_apps.notifications.services.push_delivery import queue_notification

        notification = Notification.objects.create(
            user=item.user,
            notification_type="security_alert",
            title="متابعة طلب حذف الحساب / Account closure update",
            body=(
                "راجع إعدادات الحساب لمعرفة الحالة الحالية والسجل. / "
                "Review account settings for the current status and history."
            ),
            category="security_alerts",
            icon_type="shield",
            data={
                "scope": "account",
                "action_type": "open_account_closure",
                "target_id": str(item.id),
                "revision": item.revision,
            },
        )
        queue_notification(notification)


def _version(item, expected):
    if (item.revision if item else 0) != expected:
        raise RentalConflict(
            "Refresh the current account closure request.", code="stale_revision"
        )


def _run(request, operation, data, action):
    key = request_key(request)
    if not key:
        raise ValidationError({"Idempotency-Key": "A recovery identity is required."})
    payload, code, replay = execute_idempotent(
        user=request.user,
        operation=operation,
        key=key,
        payload=data,
        action=action,
        auth_claims=request.auth or {},
    )
    return payload, code, replay


@transaction.atomic
def submit(request, data):
    user = User.objects.select_for_update().get(pk=request.user.pk)
    validate_session(user, request.auth or {})

    def apply():
        item = latest(user)
        if item and item.active:
            return summary(user), 200, item.id
        _version(item, data["expected_revision"])
        consume(
            request,
            action="account.closure.request",
            resource_id=user.id,
            revision=data["expected_revision"],
            payload=data,
        )
        item = AccountClosureRequest.objects.create(
            user=user,
            reason=data.get("reason", ""),
            revision=(item.revision + 1) if item else 1,
        )
        _event(item, user, "requested", item.reason, blockers(user))
        return summary(user), 201, item.id

    return _run(request, "account.closure.submit", data, apply)


@transaction.atomic
def withdraw(request, identity, data):
    user = User.objects.select_for_update().get(pk=request.user.pk)
    validate_session(user, request.auth or {})

    def apply():
        item = (
            AccountClosureRequest.objects.select_for_update()
            .filter(id=identity, user=user)
            .first()
        )
        if not item:
            raise NotFound()
        _version(item, data["expected_revision"])
        if not item.active:
            raise RentalConflict("This request is already closed.")
        item.active, item.status = False, AccountClosureRequest.Status.WITHDRAWN
        item.revision += 1
        item.save()
        _event(item, user, "withdrawn")
        return summary(user), 200, item.id

    return _run(request, f"account.closure.withdraw:{identity}", data, apply)


def require_reviewer(request, *, lock=False):
    return require_staff_actor(request.user, REVIEW_ROLES, lock=lock)


def _erase_profile(user, actor, item):
    from core_apps.profiles.models import Profile, UserSettings
    from ..models import (
        SocialAccount,
        SensitiveAuthorization,
        AccountProfileErasureFile,
    )
    from core_apps.features.models import SearchAlert
    from core_apps.features.company_models import CompanyMembership

    # Versioned KYC and signed/audit evidence keep their protected access.
    # Erase the mutable profile, retaining only media referenced by KYC snapshots.
    profile = Profile.objects.filter(user=user).first()
    if profile:
        from cloudinary.models import CloudinaryField

        def asset_identity(value):
            asset = CloudinaryField().to_python(value)
            return (
                (
                    asset.public_id,
                    asset.type or "upload",
                    asset.resource_type or "image",
                )
                if asset
                else None
            )

        snapshots = list(
            profile.kyc_submissions.values_list("evidence_snapshot", flat=True)
        )
        retained = {
            asset_identity(snapshot.get(field))
            for snapshot in snapshots
            for field in ("avatar", "id_face", "id_back", "confirmation_selfi")
            if snapshot.get(field)
        }
        for field in ("avatar", "id_face", "id_back", "confirmation_selfi"):
            asset = getattr(profile, field)
            # Provider deletion targets the resource, not one URL/version.
            if not asset or asset_identity(asset) in retained:
                continue
            AccountProfileErasureFile.objects.create(
                request=item,
                public_id=asset.public_id,
                storage_type=getattr(asset, "type", None)
                or ("upload" if field == "avatar" else "authenticated"),
            )
    Profile.objects.filter(user=user).update(
        phone_number="",
        birth_date=None,
        city=None,
        gender=None,
        avatar=None,
        national_id="",
        id_face=None,
        id_back=None,
        confirmation_selfi=None,
    )
    UserSettings.objects.filter(user=user).update(
        show_profile_in_search=False, share_location_for_search=False
    )
    SocialAccount.objects.filter(user=user).delete()
    from core_apps.features.decision_models import DecisionNotebook

    # Notes and their conflict copies are private profile data, not evidence
    # required by a rental, payment, company or support obligation.
    DecisionNotebook.objects.filter(user=user).delete()
    from core_apps.features.models import OwnerBeneficiarySubmission

    # Unverified receiving details never became a financial record. Keep only
    # their receipt/version; confirmed recipients remain protected history.
    OwnerBeneficiarySubmission.objects.filter(profile__owner=user).exclude(
        status="confirmed"
    ).update(
        recipient_ciphertext="", beneficiary_name="", bank_name="", account_last4=""
    )
    SearchAlert.objects.filter(user=user).update(
        enabled=False, deleted_at=timezone.now()
    )
    CompanyMembership.objects.filter(user=user).update(is_active=False)
    SensitiveAuthorization.objects.filter(user=user, consumed_at__isnull=True).update(
        consumed_at=timezone.now()
    )
    user = revoke_all(user, actor=actor, action="account.closure.completed")
    user.first_name, user.last_name = "حساب محذوف", ""
    user.email = f"deleted-{user.id}@account.invalid"
    user.closed_at = timezone.now()
    user.is_active = user.is_verified = user.is_email_verified = False
    user.set_unusable_password()
    user.save(
        update_fields=[
            "first_name",
            "last_name",
            "email",
            "closed_at",
            "is_active",
            "is_verified",
            "is_email_verified",
            "password",
        ]
    )


@transaction.atomic
def decide(request, identity, data):
    target = AccountClosureRequest.objects.filter(id=identity).first()
    if not target:
        raise NotFound()
    list(
        User.objects.select_for_update()
        .filter(pk__in=[target.user_id, request.user.pk])
        .order_by("pk")
    )
    reviewer = require_reviewer(request, lock=True)
    if reviewer.pk == target.user_id:
        raise PermissionDenied("An independent reviewer is required.")
    from ..models import StaffSecurityIdentity

    person = (
        StaffSecurityIdentity.objects.filter(user=reviewer)
        .values_list("person_reference", flat=True)
        .first()
    )
    if (
        person
        and StaffSecurityIdentity.objects.filter(
            user_id=target.user_id, person_reference=person
        ).exists()
    ):
        raise PermissionDenied(
            "A second account cannot review its own person's request."
        )

    def apply():
        item = (
            AccountClosureRequest.objects.select_for_update()
            .select_related("user")
            .get(pk=target.pk)
        )
        _version(item, data["expected_revision"])
        if not item.active:
            raise RentalConflict("This request is already closed.")
        barriers = blockers(item.user)
        action = data["decision"]
        if action == "complete" and barriers:
            raise RentalConflict(
                "Settle the current barriers before completing deletion.",
                code="closure_blocked",
            )
        consume(
            request,
            action="account.closure.review",
            resource_id=item.id,
            revision=item.revision,
            payload=data,
        )
        item.status = {
            "wait": "awaiting_settlement",
            "reject": "rejected",
            "complete": "completed",
        }[action]
        item.active = action == "wait"
        item.decision_reason = data["reason"]
        item.revision += 1
        if action == "complete":
            item.completed_at = timezone.now()
        item.save()
        _event(item, reviewer, item.status, data["reason"], barriers)
        if action == "complete":
            _erase_profile(item.user, reviewer, item)
            item.user.refresh_from_db()
        return projection(item, review=True), 200, item.id

    return _run(request, f"account.closure.review:{identity}", data, apply)

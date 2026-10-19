"""Durable, bounded activation delivery. Unknown SMTP outcomes are never auto-retried."""

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from ...company_models import Company, CompanyMembership
from ...company_staff_models import CompanyAccountProvisioning, CompanyWorkContactProof
from .staff import activation_token, delivery_ready


def deliver(identity):

    initial = CompanyAccountProvisioning.objects.select_related("staff").get(
        pk=identity
    )
    with transaction.atomic():
        Company.objects.select_for_update().get(pk=initial.staff.company_id)
        row = CompanyAccountProvisioning.objects.select_for_update().get(pk=identity)
        if row.delivery_status != "queued":
            return False
        current_grant = CompanyMembership.objects.filter(
            company_id=initial.staff.company_id,
            user=row.requested_by,
            is_active=True,
            is_admin=True,
        ).exists()
        if (
            not current_grant
            or row.status != "pending_activation"
            or row.expires_at <= timezone.now()
            or row.staff.proposal_revision != row.proposal_revision
        ):
            row.delivery_status = "cancelled"
            row.save(update_fields=["delivery_status", "updated_at"])
            return False
        if not delivery_ready():
            return False  # Durable intention survives a temporary provider disable.
        row.delivery_status = "sending"
        row.delivery_claimed_at = timezone.now()
        row.save(update_fields=["delivery_status", "delivery_claimed_at", "updated_at"])
    # No database lock is held during SMTP. Revocation always blocks acceptance,
    # including when an already-claimed email is delivered after revocation.
    try:
        sent = send_mail(
            subject="Sokoun company access / تفعيل حساب الشركة في سكون",
            message=(
                "Sign in to your existing Sokoun account, or complete personal registration. Open Companies, then Activate company access. If your login uses another email, verify this work contact in the app. Review the company and roles before accepting.\n"
                "سجل الدخول إلى حسابك الحالي في سكون أو أكمل التسجيل الشخصي، ثم افتح الشركات وتفعيل حساب الشركة. إذا كان بريد الدخول مختلفاً، وثق بريد العمل داخل التطبيق. راجع الشركة والصلاحيات قبل القبول.\n\n"
                + activation_token(row)
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[row.recipient_email],
            fail_silently=False,
        )
    except Exception:
        CompanyAccountProvisioning.objects.filter(
            pk=identity, delivery_status="sending"
        ).update(delivery_status="unknown")
        return False
    CompanyAccountProvisioning.objects.filter(
        pk=identity, delivery_status="sending"
    ).update(
        delivery_status="sent" if sent else "failed",
        delivered_at=timezone.now() if sent else None,
    )
    return bool(sent)


def deliver_contact_proof(identity):

    from .contact_proof import proof_code
    from .staff import validate_proposal
    from ..rental_phase2 import RentalConflict

    initial = CompanyWorkContactProof.objects.select_related("provisioning__staff").get(
        pk=identity
    )
    with transaction.atomic():
        Company.objects.select_for_update().get(
            pk=initial.provisioning.staff.company_id
        )
        row = (
            CompanyWorkContactProof.objects.select_for_update()
            .select_related("provisioning__staff", "user")
            .get(pk=identity)
        )
        if row.delivery_status != "queued":
            return False
        try:
            validate_proposal(row.provisioning)
            valid = (
                not row.revoked_at
                and not row.verified_at
                and row.expires_at > timezone.now()
                and row.user.is_active
                and row.user.is_verified
            )
        except RentalConflict:
            valid = False
        if not valid:
            row.delivery_status = "cancelled"
            row.save(update_fields=["delivery_status", "updated_at"])
            return False
        if not delivery_ready():
            return False
        row.delivery_status = "sending"
        row.delivery_claimed_at = timezone.now()
        row.save(update_fields=["delivery_status", "delivery_claimed_at", "updated_at"])
    try:
        sent = send_mail(
            subject="Sokoun work email verification / توثيق بريد العمل في سكون",
            message=(
                f"You requested to link company access to your signed-in Sokoun account ({row.user.email}). Enter this code only in that app session. It expires in ten minutes. Do not share it. This does not change your personal login.\n"
                "أدخل الرمز في الحساب الذي طلبته منه فقط. لا تشاركه مع أي شخص. ينتهي خلال عشر دقائق ولا يغير بيانات دخولك الشخصية.\n\n"
                + proof_code(row)
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[row.provisioning.recipient_email],
            fail_silently=False,
        )
    except Exception:
        CompanyWorkContactProof.objects.filter(
            pk=identity, delivery_status="sending"
        ).update(delivery_status="unknown")
        return False
    CompanyWorkContactProof.objects.filter(
        pk=identity, delivery_status="sending"
    ).update(
        delivery_status="sent" if sent else "failed",
        delivered_at=timezone.now() if sent else None,
    )
    return bool(sent)


def drain(limit=100):
    # A worker that died after claiming may have sent. Require explicit resend.
    from datetime import timedelta

    CompanyAccountProvisioning.objects.filter(
        delivery_status="sending",
        delivery_claimed_at__lt=timezone.now() - timedelta(minutes=15),
    ).update(delivery_status="unknown")
    ids = list(
        CompanyAccountProvisioning.objects.filter(delivery_status="queued")
        .order_by("created_at")
        .values_list("pk", flat=True)[:limit]
    )
    CompanyWorkContactProof.objects.filter(
        delivery_status="sending",
        delivery_claimed_at__lt=timezone.now() - timedelta(minutes=15),
    ).update(delivery_status="unknown")
    proof_ids = list(
        CompanyWorkContactProof.objects.filter(delivery_status="queued")
        .order_by("created_at")
        .values_list("pk", flat=True)[: max(0, limit - len(ids))]
    )
    return sum(deliver(identity) for identity in ids) + sum(
        deliver_contact_proof(identity) for identity in proof_ids
    )

"""Verify a work contact without replacing an existing personal login identifier."""

import hashlib
from datetime import timedelta
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.crypto import salted_hmac, constant_time_compare
from ...company_models import Company
from ...company_staff_models import CompanyAccountProvisioning, CompanyWorkContactProof
from ..rental_lifecycle.common import require_actor, audit
from ..rental_phase2 import RentalConflict
from .staff import resolve_token, validate_proposal, delivery_ready


def proof_code(proof):
    value = f"{proof.id}:{proof.provisioning_id}:{proof.user_id}"
    digest = salted_hmac(
        "sokoun.company.work-contact.v1", value, algorithm="sha256"
    ).hexdigest()
    return str(int(digest, 16) % 100000000).zfill(8)


def verified(provisioning, user):
    return CompanyWorkContactProof.objects.filter(
        provisioning=provisioning,
        user=user,
        verified_at__isnull=False,
        revoked_at__isnull=True,
        expires_at__gt=timezone.now(),
    ).exists()


@transaction.atomic
def request_proof(user, token):
    require_actor(user)
    initial = resolve_token(token)
    Company.objects.select_for_update().get(pk=initial.staff.company_id)
    provisioning = CompanyAccountProvisioning.objects.select_for_update().get(
        pk=initial.pk
    )
    validate_proposal(provisioning)
    if not delivery_ready():
        raise RentalConflict(
            "Company activation email delivery is not configured.",
            code="provider_not_ready",
        )
    now = timezone.now()
    # Recipient-scoped cooldown applies even if different accounts request proof.
    if provisioning.contact_proofs.filter(
        created_at__gt=now - timedelta(seconds=60)
    ).exists():
        raise RentalConflict(
            "Wait before requesting another activation email.",
            code="activation_cooldown",
        )
    provisioning.contact_proofs.filter(user=user, revoked_at__isnull=True).update(
        revoked_at=now
    )
    proof = CompanyWorkContactProof(
        provisioning=provisioning,
        user=user,
        expires_at=min(provisioning.expires_at, now + timedelta(minutes=10)),
    )
    proof.code_digest = hashlib.sha256(proof_code(proof).encode()).hexdigest()
    proof.save()
    audit(
        proof,
        user,
        "company_work_contact_proof_requested",
        metadata={
            "company_id": str(provisioning.staff.company.id),
            "provisioning_id": str(provisioning.id),
        },
    )
    return proof


def verify(user, identity, code):
    """Return a failed attempt normally so the surrounding transaction commits it."""
    require_actor(user)
    with transaction.atomic():
        initial = get_object_or_404(CompanyWorkContactProof, id=identity, user=user)
        Company.objects.select_for_update().get(
            pk=initial.provisioning.staff.company_id
        )
        proof = CompanyWorkContactProof.objects.select_for_update().get(pk=initial.pk)
        validate_proposal(proof.provisioning)
        if proof.revoked_at or proof.expires_at <= timezone.now():
            return None
        if proof.verified_at:
            return proof
        if proof.attempts >= 5:
            return None
        proof.attempts += 1
        matches = constant_time_compare(
            proof.code_digest, hashlib.sha256(code.encode()).hexdigest()
        )
        if matches:
            proof.verified_at = timezone.now()
            proof.revision += 1
        proof.save()
        if matches:
            audit(
                proof,
                user,
                "company_work_contact_verified",
                metadata={"company_id": str(proof.provisioning.staff.company.id)},
            )
            return proof
    return None


def payload(proof):
    return {
        "id": str(proof.id),
        "revision": proof.revision,
        "provisioning_id": str(proof.provisioning.id),
        "company_id": str(proof.provisioning.staff.company.id),
        "verified": bool(
            proof.verified_at
            and not proof.revoked_at
            and proof.expires_at > timezone.now()
        ),
        "delivery_status": proof.delivery_status,
        "expires_at": proof.expires_at.isoformat(),
    }

"""Separate work contact proof, using synthetic addresses and local email only."""

from datetime import timedelta
import pytest
from django.core import mail
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core_apps.features.company_models import CompanyMembership
from core_apps.features.company_staff_models import CompanyWorkContactProof
from core_apps.features.services.company import (
    staff,
    contact_proof,
    activation_delivery,
)
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.features.tests.test_company_staff import (
    company_setup,
    rental_participants,
    policy,
    authenticated,
    command,
    API,
    prepare,
)


@pytest.mark.django_db
def test_existing_personal_login_proves_work_contact_before_membership(
    company_setup, settings
):
    person, provision, recipient = prepare(company_setup, settings)
    original_email = recipient.email
    recipient.email = "personal@example.invalid"
    recipient.save(update_fields=["email"])
    token = staff.activation_token(provision)
    client = authenticated(recipient)
    preview = staff.preview(recipient, token)
    assert not preview["can_accept"] and preview["can_verify_work_contact"]
    accept = command(token=token, expected_revision=1, proposal_revision=1)
    assert (
        client.post(API + "company-access/accept/", accept, format="json").status_code
        == 403
    )
    body = command(token=token)
    endpoint = API + "company-access/contact-proof/"
    first = client.post(endpoint, body, format="json")
    assert first.status_code == 201, first.data
    assert client.post(endpoint, body, format="json").json() == first.json()
    proof = CompanyWorkContactProof.objects.get()
    assert "code" not in first.json()["data"]["resource"]
    assert not CompanyMembership.objects.filter(user=recipient).exists()
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    assert activation_delivery.deliver_contact_proof(proof.pk)
    assert mail.outbox[-1].to == [original_email]
    assert contact_proof.proof_code(proof) in mail.outbox[-1].body
    assert not activation_delivery.deliver_contact_proof(proof.pk)
    verify_endpoint = f"{endpoint}{proof.id}/"
    other = authenticated(company_setup[2])
    assert other.get(verify_endpoint).status_code == 404
    assert (
        other.post(
            verify_endpoint, {"code": contact_proof.proof_code(proof)}, format="json"
        ).status_code
        == 404
    )
    response = client.post(
        verify_endpoint, {"code": contact_proof.proof_code(proof)}, format="json"
    )
    assert response.status_code == 200 and response.json()["data"]["verified"]
    assert not CompanyMembership.objects.filter(user=recipient).exists()
    assert staff.preview(recipient, token)["can_accept"]
    assert (
        client.post(API + "company-access/accept/", accept, format="json").status_code
        == 200
    )
    person.refresh_from_db()
    recipient.refresh_from_db()
    assert person.membership.user == recipient
    assert recipient.email == "personal@example.invalid" and recipient.check_password(
        "synthetic-only"
    )


@pytest.mark.django_db
def test_proof_attempts_persist_on_api_failure_and_are_bounded(company_setup, settings):
    _, provision, user = prepare(company_setup, settings)
    proof = contact_proof.request_proof(user, staff.activation_token(provision))
    valid_code = contact_proof.proof_code(proof)
    invalid = "00000000" if valid_code != "00000000" else "00000001"
    endpoint = f"{API}company-access/contact-proof/{proof.id}/"
    client = authenticated(user)
    for _ in range(5):
        assert (
            client.post(endpoint, {"code": invalid}, format="json").status_code == 400
        )
    proof.refresh_from_db()
    assert proof.attempts == 5 and not proof.verified_at
    assert client.post(endpoint, {"code": valid_code}, format="json").status_code == 400
    with pytest.raises(RentalConflict):
        contact_proof.request_proof(company_setup[2], staff.activation_token(provision))


@pytest.mark.django_db
def test_work_proof_is_scoped_to_current_provision_and_expires(company_setup, settings):
    person, provision, user = prepare(company_setup, settings)
    user.email = "another-personal@example.invalid"
    user.save(update_fields=["email"])
    token = staff.activation_token(provision)
    proof = contact_proof.request_proof(user, token)
    assert contact_proof.verify(user, proof.id, contact_proof.proof_code(proof))
    assert contact_proof.verify(user, proof.id, contact_proof.proof_code(proof))
    proof.refresh_from_db()
    assert proof.attempts == 1
    proof.expires_at = timezone.now() - timedelta(seconds=1)
    proof.save()
    assert not staff.preview(user, token)["can_accept"]
    assert contact_proof.verify(user, proof.id, contact_proof.proof_code(proof)) is None
    with pytest.raises(PermissionDenied):
        staff.respond(
            user, {"token": token, "expected_revision": 1, "proposal_revision": 1}
        )
    proof.expires_at = timezone.now() + timedelta(minutes=2)
    proof.save()
    staff.revoke_activation(
        company_setup[1],
        company_setup[3].id,
        person.id,
        {"expected_revision": person.revision},
    )
    with pytest.raises(RentalConflict):
        contact_proof.verify(user, proof.id, contact_proof.proof_code(proof))
    assert not activation_delivery.deliver_contact_proof(proof.pk)


@pytest.mark.django_db
def test_unknown_work_email_delivery_is_not_blindly_retried(
    company_setup, settings, monkeypatch
):
    _, provision, user = prepare(company_setup, settings)
    proof = contact_proof.request_proof(user, staff.activation_token(provision))

    def uncertain(**kwargs):
        raise TimeoutError("Synthetic delivery timeout")

    monkeypatch.setattr(activation_delivery, "send_mail", uncertain)
    assert not activation_delivery.deliver_contact_proof(proof.pk)
    proof.refresh_from_db()
    assert proof.delivery_status == "unknown"
    assert not activation_delivery.deliver_contact_proof(proof.pk)

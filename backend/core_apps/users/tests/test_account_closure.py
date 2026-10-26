"""Local lifecycle and concurrency evidence; no deployed delivery claim."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import patch
import pytest
from django.db import close_old_connections, connection, transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient
from core_apps.admin_api.models import StaffProfile
from core_apps.users.models import (
    User,
    AccountClosureRequest,
    AccountClosureDecision,
    AuthSession,
)
from core_apps.users.services import account_closure as service
from core_apps.users.services.sessions import issue_refresh, validate_session
from core_apps.users.services.new_business import require_new_business
from core_apps.features.services.rental_phase2 import RentalConflict
from core_apps.common.idempotency import IdempotencyConflict, resolve_or_close
from core_apps.properties.models import Property
from core_apps.properties.services.public_access import public_properties

pytestmark = pytest.mark.django_db


def request(user, key=None):
    return SimpleNamespace(
        user=user,
        auth=issue_refresh(user).access_token,
        headers={"Idempotency-Key": key or str(uuid4())},
    )


@pytest.fixture
def reviewer():
    user = User.objects.create_user(
        email="closure-reviewer@example.invalid", password="local-test", is_staff=True
    )
    StaffProfile.objects.create(user=user, role_name="account_closure_reviewer")
    return user


@pytest.fixture
def listing(user):
    from core_apps.properties.models import PropertyType, Governorate, City

    apartment_type, _ = PropertyType.objects.get_or_create(
        slug="apartment", defaults={"name": "Apartment"}
    )
    cairo_governorate = Governorate.objects.create(name="Cairo")
    cairo_city = City.objects.create(name="Cairo City", governorate=cairo_governorate)
    return Property.objects.create(
        owner=user,
        title="Closure test listing",
        price=3000,
        property_type=apartment_type,
        governorate=cairo_governorate,
        city=cairo_city,
        status="verified",
        is_verified=True,
    )


def submit(user):
    return service.submit(
        request(user), {"expected_revision": 0, "reason": "No longer needed"}
    )[0]["request"]


def decision(reviewer, item, action="complete"):
    return service.decide(
        request(reviewer),
        item["id"],
        {
            "expected_revision": item["revision"],
            "decision": action,
            "reason": "Current records reviewed",
        },
    )[0]


def test_two_device_requests_share_one_request_and_account_notice(user):
    first = submit(user)
    second = submit(user)
    assert first["id"] == second["id"]
    assert (
        AccountClosureRequest.objects.count()
        == AccountClosureDecision.objects.count()
        == 1
    )
    from core_apps.notifications.models import Notification

    notice = Notification.objects.get(user=user)
    assert notice.data["scope"] == "account"
    assert notice.data["action_type"] == "open_account_closure"


def test_submission_replay_rejects_changed_payload_and_cannot_resurrect_withdrawn(user):
    req = request(user)
    body = {"expected_revision": 0, "reason": "Close"}
    result = service.submit(req, body)
    item = result[0]["request"]
    service.withdraw(request(user), item["id"], {"expected_revision": item["revision"]})
    assert service.submit(req, body)[2] is True
    assert not AccountClosureRequest.objects.filter(active=True).exists()
    with pytest.raises(IdempotencyConflict):
        service.submit(req, {**body, "reason": "Different"})


def test_fence_prevents_late_submission(user):
    req = request(user)
    resolve_or_close(
        user=user,
        operation="account.closure.submit",
        key=req.headers["Idempotency-Key"],
    )
    with pytest.raises(IdempotencyConflict):
        service.submit(req, {"expected_revision": 0, "reason": "Close"})
    assert not AccountClosureRequest.objects.exists()


def test_pending_account_cannot_receive_new_business_but_can_withdraw(user, listing):
    item = submit(user)
    assert not public_properties().filter(pk=listing.pk).exists()
    with transaction.atomic(), pytest.raises(PermissionDenied):
        require_new_business(user.pk)
    # Existing content remains readable; no property or history was erased.
    assert Property.objects.get(pk=listing.pk).title == "Closure test listing"
    service.withdraw(request(user), item["id"], {"expected_revision": item["revision"]})
    with transaction.atomic():
        require_new_business(user.pk)
    assert public_properties().filter(pk=listing.pk).exists()


def test_new_listing_is_guarded_at_persistence(user, listing):
    submit(user)
    listing.pk = None
    listing.id = uuid4()
    listing._state.adding = True
    with pytest.raises(PermissionDenied):
        listing.save()
    assert Property.objects.count() == 1


def test_previous_request_history_remains_visible_after_new_request(user):
    first = submit(user)
    service.withdraw(request(user), first["id"], {"expected_revision": 1})
    result = service.submit(
        request(user), {"expected_revision": 2, "reason": "Request again"}
    )[0]
    assert result["request"]["id"] != first["id"]
    assert [e["action"] for e in result["history"]] == [
        "requested",
        "withdrawn",
        "requested",
    ]
    assert result["history"][0]["request_id"] == first["id"]


def test_invoice_barrier_rechecked_then_completed_without_erasing_history(
    user, reviewer
):
    from core_apps.features.models import RentInvoice

    invoice = RentInvoice.objects.create(
        payer=user,
        purpose="subscription",
        business_reference="closure-invoice",
        reference="CLOSE-001",
        due_date=timezone.localdate(),
        amount_minor=1000,
    )
    item = submit(user)
    assert "invoice" in {b["code"] for b in item["blockers"]}
    with pytest.raises(RentalConflict):
        decision(reviewer, item)
    waiting = decision(reviewer, item, "wait")
    assert waiting["status"] == "awaiting_settlement"
    # Existing financial settlement is allowed while new work is restricted.
    invoice.status = "paid"
    invoice.save(update_fields=["status"])
    result = decision(reviewer, waiting)
    assert result["status"] == "completed"
    invoice.refresh_from_db()
    assert invoice.status == "paid" and invoice.amount_minor == 1000


def test_completion_revokes_sessions_and_erases_profile_without_private_push(
    user, reviewer
):
    from core_apps.notifications.models import Notification
    from core_apps.profiles.models import Profile
    from core_apps.features.decision_models import (
        DecisionNotebook,
        DecisionNotebookVersion,
        DecisionNotebookConflict,
    )

    notebook = DecisionNotebook.objects.create(user=user, workspace="individual")
    DecisionNotebookVersion.objects.create(
        notebook=notebook, revision=1, content={"note": "private"}
    )
    DecisionNotebookConflict.objects.create(
        notebook=notebook,
        record_key="private",
        revision=1,
        incoming={"note": "also private"},
    )

    profile = Profile.objects.get(user=user)
    profile.phone_number = "+201000000001"
    profile.save(update_fields=["phone_number"])
    login = request(user)
    item = submit(user)
    result = decision(reviewer, item)
    user.refresh_from_db()
    profile.refresh_from_db()
    assert result["account_name"] == "حساب محذوف"
    assert user.closed_at and not user.is_active and not user.has_usable_password()
    assert not str(profile.phone_number) and profile.gender is None
    assert not DecisionNotebook.objects.filter(user=user).exists()
    assert not DecisionNotebookVersion.objects.filter(notebook_id=notebook.pk).exists()
    assert not DecisionNotebookConflict.objects.filter(notebook_id=notebook.pk).exists()
    assert not AuthSession.objects.filter(user=user, revoked_at__isnull=True).exists()
    assert Notification.objects.filter(user=user).count() == 1
    with pytest.raises(Exception) as error:
        validate_session(user, login.auth)
    assert getattr(error.value, "status_code", None) == 401


@pytest.mark.parametrize(
    "role", ["support", "support_supervisor", "financial_approver", "main_admin"]
)
def test_support_and_finance_roles_cannot_review_deletion(user, reviewer, role):
    item = submit(user)
    StaffProfile.objects.filter(user=reviewer).update(role_name=role)
    with pytest.raises(PermissionDenied):
        decision(reviewer, item, "reject")


def test_revoked_reviewer_cannot_decide(user, reviewer):
    item = submit(user)
    req = request(reviewer)
    StaffProfile.objects.filter(user=reviewer).update(is_active=False)
    with pytest.raises(PermissionDenied):
        service.decide(
            req,
            item["id"],
            {"expected_revision": 1, "decision": "reject", "reason": "No"},
        )


def test_self_review_forbidden_even_superuser(user):
    item = submit(user)
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    with pytest.raises(PermissionDenied):
        decision(user, item, "reject")


def test_decision_lost_response_replays_once(user, reviewer):
    item = submit(user)
    req = request(reviewer)
    body = {"expected_revision": 1, "decision": "reject", "reason": "Reviewed"}
    first = service.decide(req, item["id"], body)
    assert service.decide(req, item["id"], body)[2]
    assert first[0]["status"] == "rejected"
    assert AccountClosureDecision.objects.count() == 2


def test_old_delete_aliases_cannot_erase_accounts(user):
    client = APIClient()
    client.force_authenticate(user)
    for url in ["/api/v1/auth/delete-account/", "/api/v1/profiles/delete-account/"]:
        result = client.delete(url)
        assert result.status_code == 409
    assert User.objects.filter(pk=user.pk).exists()


def test_final_notice_delivery_failure_only_retries_email(user, reviewer, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    from core_apps.users.services.closure_delivery import deliver

    item = submit(user)
    decision(reviewer, item)
    with patch(
        "core_apps.users.services.closure_delivery.send_mail",
        side_effect=OSError("offline"),
    ):
        assert deliver() == 0
    assert deliver() == 2
    assert deliver() == 0
    assert AccountClosureDecision.objects.count() == 2


def test_pending_account_blocks_other_tenant_interest(user, another_user, listing):
    from core_apps.features.models import RentalInterest

    submit(user)
    with pytest.raises(PermissionDenied):
        RentalInterest.objects.create(
            property=listing,
            tenant=another_user,
            offer_id="exact-unit",
            offer_revision=1,
            offer_snapshot={},
            desired_start=timezone.localdate() + timedelta(days=1),
            months=1,
        )
    assert not RentalInterest.objects.exists()


def test_closed_profile_cannot_be_restored_by_an_inflight_edit(user, reviewer):
    from core_apps.profiles.services import ProfileService

    stale_user = User.objects.get(pk=user.pk)
    decision(reviewer, submit(user))
    with pytest.raises(PermissionDenied):
        ProfileService.update_user_profile(stale_user, {"first_name": "Restored name"})
    user.refresh_from_db()
    assert user.get_full_name == "حساب محذوف"


def test_django_admin_cannot_reactivate_deleted_account_from_old_form(
    user, reviewer, superuser
):
    from django.contrib import admin
    from django.core.exceptions import PermissionDenied as AdminDenied
    from core_apps.users.admin import UserAdmin

    stale = User.objects.get(pk=user.pk)
    decision(reviewer, submit(user))
    model_admin = UserAdmin(User, admin.site)
    req = SimpleNamespace(user=superuser)
    assert not model_admin.has_delete_permission(req, stale)
    with pytest.raises(AdminDenied):
        model_admin.save_model(req, stale, None, True)
    user.refresh_from_db()
    assert user.closed_at and not user.is_active


def test_avatar_cleanup_retries_without_erasing_contract_evidence(user, reviewer):
    from core_apps.profiles.models import Profile
    from core_apps.users.models import AccountProfileErasureFile
    from core_apps.users.services.closure_delivery import erase_files

    Profile.objects.filter(user=user).update(
        avatar="image/upload/v1/profiles/avatar.jpg",
        id_face="image/authenticated/v1/identity/protected.jpg",
    )
    from core_apps.admin_api.models import KYCSubmission
    from core_apps.users.services.identity_submission import evidence_snapshot

    profile = Profile.objects.get(user=user)
    evidence = evidence_snapshot(profile)
    KYCSubmission.objects.create(
        profile=profile, status="approved", evidence_snapshot=evidence
    )
    # A newer URL for the same provider asset must not delete retained evidence.
    Profile.objects.filter(user=user).update(
        id_face="image/authenticated/v2/identity/protected.jpg"
    )
    item = decision(reviewer, submit(user))
    assert item["erasure_pending"] is True
    with patch("cloudinary.uploader.destroy", side_effect=OSError("offline")):
        assert erase_files() == 0
    with patch("cloudinary.uploader.destroy", return_value={"result": "ok"}) as destroy:
        assert erase_files() == 1
        assert erase_files() == 0
        assert destroy.call_count == 1
        assert "avatar" in destroy.call_args.args[0]
    assert AccountProfileErasureFile.objects.get().public_id == ""
    assert not Profile.objects.get(user=user).id_face
    assert KYCSubmission.objects.get(profile=profile).evidence_snapshot == evidence


def test_real_email_otp_is_bound_to_request_and_real_staff_totp_to_decision(
    user, reviewer, settings
):
    from core_apps.features.models import PolicyDecision
    from core_apps.users.models import TotpFactor, SensitiveAuthorization
    from core_apps.users.services import sensitive_actions, totp

    settings.SECURITY_TEST_BYPASS = False
    settings.SECURITY_ASSURANCE_PROVIDER = (
        "core_apps.users.services.assurance.AccountAssuranceProvider"
    )
    PolicyDecision.objects.create(
        code="D26",
        version="closure-local-only",
        status="approved",
        owner="test",
        approver=reviewer,
        source="local test",
        evidence_reference="synthetic",
        scope=sorted(sensitive_actions.ACTIONS),
        effective_at=timezone.now() - timedelta(seconds=1),
        evidence_requirements={"fixture": "local"},
        actions_and_consequences={"fixture": "local"},
        historical_treatment="Local only",
        audit_reason="R11 closure test",
        disclosure="Synthetic",
        rules={
            "provider": settings.SECURITY_ASSURANCE_PROVIDER,
            "proof_lifetime_seconds": 300,
            "assurance": "email_otp_or_totp",
        },
    )
    user.is_email_verified = True
    user.save(update_fields=["is_email_verified"])
    req = request(user)
    body = {"expected_revision": 0, "reason": "Close"}
    with pytest.raises(PermissionDenied):
        service.submit(req, body)
    with patch(
        "core_apps.users.services.assurance.generate_otp", return_value="739251"
    ):
        challenge = sensitive_actions.begin(
            req,
            {
                "action": "account.closure.request",
                "resource_id": user.id,
                "resource_revision": 0,
                "payload": body,
            },
        )
    proof = sensitive_actions.verify(req, challenge["id"], "739251")
    req.headers["X-Sokoun-Authorization"] = proof["proof"]
    with pytest.raises(PermissionDenied):
        service.submit(req, {**body, "reason": "Changed"})
    item = service.submit(req, body)[0]["request"]
    factor = TotpFactor.objects.create(
        user=reviewer,
        secret_ciphertext=totp.seal(totp.new_secret()),
        confirmed_at=timezone.now(),
    )
    staff = request(reviewer)
    decision_body = {
        "expected_revision": item["revision"],
        "decision": "complete",
        "reason": "Independent records reviewed",
    }
    with pytest.raises(PermissionDenied):
        service.decide(staff, item["id"], decision_body)
    challenge = sensitive_actions.begin(
        staff,
        {
            "action": "account.closure.review",
            "resource_id": item["id"],
            "resource_revision": item["revision"],
            "payload": decision_body,
        },
    )
    code = totp.code_at(
        totp.unseal(factor.secret_ciphertext), int(timezone.now().timestamp()) // 30
    )
    staff.headers["X-Sokoun-Authorization"] = sensitive_actions.verify(
        staff, challenge["id"], code
    )["proof"]
    result = service.decide(staff, item["id"], decision_body)[0]
    assert result["status"] == "completed"
    assert SensitiveAuthorization.objects.filter(consumed_at__isnull=False).count() == 2


@pytest.mark.django_db(transaction=True)
def test_concurrent_request_and_withdraw_finalization_have_one_winner(reviewer):
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL row locks")
    user = User.objects.create_user(
        email="concurrent-close@example.invalid", password="local"
    )
    barrier = Barrier(2)
    requests = [request(user), request(user)]

    def create(req):
        close_old_connections()
        try:
            barrier.wait()
            return service.submit(req, {"expected_revision": 0, "reason": "Close"})[0][
                "request"
            ]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(create, requests))
    assert first["id"] == second["id"]
    assert AccountClosureRequest.objects.count() == 1
    barrier = Barrier(2)
    applicant, staff = request(user), request(reviewer)

    def finish(action):
        close_old_connections()
        try:
            barrier.wait()
            if action == "withdraw":
                service.withdraw(applicant, first["id"], {"expected_revision": 1})
            else:
                service.decide(
                    staff,
                    first["id"],
                    {
                        "expected_revision": 1,
                        "decision": "complete",
                        "reason": "Reviewed",
                    },
                )
            return True
        except Exception as error:
            assert getattr(error, "status_code", None) in {401, 409}
            return False
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(finish, ["withdraw", "complete"]))
    assert sorted(results) == [False, True]
    assert AccountClosureDecision.objects.count() == 2

from uuid import uuid4

import pytest
from django.urls import reverse
from django.utils import timezone

from core_apps.admin_api.models import KYCSubmission, StaffProfile
from core_apps.admin_api.tests.test_analytics_periods import home  # noqa: F401
from core_apps.properties.models import Property
from core_apps.support.models import Ticket
from core_apps.users.models import AccountClosureRequest

pytestmark = pytest.mark.django_db


def request_as(client, actor, role):
    StaffProfile.objects.update_or_create(
        user=actor, defaults={"role_name": role, "is_active": True}
    )
    client.force_authenticate(actor)
    result = client.get(reverse("admin-followups"))
    assert result.status_code == 200
    assert result["Cache-Control"] == "private, no-store"
    return {row["id"]: row for row in result.data["results"]}


@pytest.mark.parametrize(
    "role,expected",
    [
        (
            "system_owner",
            {"kyc", "properties", "support", "escalations", "account_closure"},
        ),
        ("main_admin", {"kyc", "properties"}),
        ("kyc_reviewer", {"kyc"}),
        ("property_reviewer", {"properties"}),
        ("support", {"support"}),
        ("support_supervisor", {"support", "escalations"}),
        ("account_closure_reviewer", {"account_closure"}),
        ("financial_approver", set()),
        ("payout_operator", set()),
        ("security_recovery_reviewer", set()),
    ],
)
def test_roles_see_only_their_existing_queues_and_no_invented_work(
    api_client, user, role, expected
):
    rows = request_as(api_client, user, role)
    assert rows.keys() == expected
    assert all(row["count"] == 0 for row in rows.values())


def test_designated_recovery_superuser_cannot_gain_general_queues(
    api_client, superuser
):
    assert request_as(api_client, superuser, "security_recovery_reviewer") == {}


def test_current_profile_and_account_state_checked_again(api_client, user):
    request_as(api_client, user, "main_admin")
    StaffProfile.objects.filter(user=user).update(is_active=False)
    assert api_client.get(reverse("admin-followups")).status_code == 403
    StaffProfile.objects.filter(user=user).update(is_active=True)
    type(user).objects.filter(pk=user.pk).update(is_active=False)
    assert api_client.get(reverse("admin-followups")).status_code == 403


def test_pending_kyc_excludes_self_superseded_and_completed(
    api_client, user, another_user
):
    KYCSubmission.objects.create(profile=another_user.profile, status="pending")
    KYCSubmission.objects.create(
        profile=another_user.profile, status="pending", superseded_at=timezone.now()
    )
    KYCSubmission.objects.create(profile=user.profile, status="pending")
    rows = request_as(api_client, user, "kyc_reviewer")
    assert rows["kyc"]["count"] == 1
    assert rows["kyc"]["href"] == "/admin/kyc"
    KYCSubmission.objects.filter(profile=another_user.profile).update(status="approved")
    assert api_client.get(reverse("admin-followups")).data["results"][0]["count"] == 0


def test_property_review_counts_current_queue_without_own_listing(
    api_client, home, another_user  # noqa: F811 - imported pytest fixture
):
    own = Property.objects.create(
        owner=another_user,
        title="Own pending listing",
        property_type=home.property_type,
        governorate=home.governorate,
        city=home.city,
    )
    rows = request_as(api_client, another_user, "property_reviewer")
    assert rows["properties"]["count"] == 1
    Property.objects.filter(pk=home.pk).update(status="verified")
    assert api_client.get(reverse("admin-followups")).data["results"][0]["count"] == 0
    own.refresh_from_db()
    assert own.status == "under_review"  # Reading never approves the queue.


def ticket(user, **data):
    return Ticket.objects.create(
        user=user,
        reference=f"QA-{uuid4().hex[:12]}",
        subject="Private support context",
        **data,
    )


def test_support_counts_assignment_and_escalation_without_side_effects(
    api_client, user, another_user, superuser
):
    mine = ticket(another_user, assigned_to=user)
    free = ticket(another_user)
    ticket(another_user, assigned_to=superuser)
    escalated = ticket(another_user, escalated=True)
    ticket(another_user, status="resolved")
    ticket(user)  # Cannot independently service own inquiry.
    rows = request_as(api_client, user, "support")
    assert rows["support"]["count"] == 2 and "escalations" not in rows
    rows = request_as(api_client, user, "support_supervisor")
    assert rows["support"]["count"] == 3 and rows["escalations"]["count"] == 1
    for item in (mine, free, escalated):
        item.refresh_from_db()
        assert item.status == "open" and item.revision == 1
    assert free.assigned_to_id is None
    assert "Private support context" not in str(rows)


def test_closure_count_excludes_self_and_history_but_keeps_waiting(
    api_client, user, another_user
):
    AccountClosureRequest.objects.create(user=user)
    active = AccountClosureRequest.objects.create(
        user=another_user, status="awaiting_settlement"
    )
    AccountClosureRequest.objects.create(
        user=another_user, active=False, status="rejected"
    )
    rows = request_as(api_client, user, "account_closure_reviewer")
    assert rows["account_closure"]["count"] == 1
    AccountClosureRequest.objects.filter(pk=active.pk).update(
        active=False, status="withdrawn"
    )
    assert api_client.get(reverse("admin-followups")).data["results"][0]["count"] == 0


def test_ordinary_account_and_anonymous_cannot_read_followups(api_client, user):
    assert api_client.get(reverse("admin-followups")).status_code == 401
    api_client.force_authenticate(user)
    assert api_client.get(reverse("admin-followups")).status_code == 403

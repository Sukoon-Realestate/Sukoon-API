"""Administrative succession keeps canonical consent without contract disclosure."""

import pytest
from core_apps.users.models import User
from core_apps.features.models import CompanyMembership
from .test_company_tenancy import (
    active_agreement,
    signed_agreement,
    agreement,
    cycle,
    company_setup,
    rental_participants,
    policy,
    person,
    command,
    act,
    API,
)
from .test_company_role_contexts import client


@pytest.mark.django_db
def test_admin_succession_is_minimal_independent_and_revocation_safe(active_agreement):
    actors, item = active_agreement
    company = actors["company"]
    admin = client(actors["coordinator"], company, "admin")
    reviewer = company.memberships.get(user=actors["reviewer"])
    incoming = person("replacement-role-coordinator")
    member = CompanyMembership.objects.create(
        company=company, user=incoming, is_coordinator=True
    )
    endpoint = API + f"companies/{company.id}/responsibility-assignments/{item.id}/"
    detail = admin.get(endpoint)
    assert detail.status_code == 200, detail.data
    assert (
        not {
            "lease_id",
            "terms",
            "invoices",
            "rent_amount_minor",
            "package",
            "signing_document",
        }
        & detail.data.keys()
    )
    assert admin.get(API + f"company-tenancies/{item.id}/").status_code == 404
    assert client(actors["payer"], company, "payer").get(endpoint).status_code == 403
    body = command(
        expected_revision=item.revision,
        signer_mandate_id=str(item.signer_mandate.id),
        payer_mandate_id=str(item.payer_mandate.id),
        coordinator_membership_id=str(member.id),
        reviewer_membership_id=str(
            company.memberships.get(user=actors["coordinator"]).id
        ),
        reason="Synthetic independent assignment review",
    )
    denied = admin.post(endpoint + "replace_authority/", body, format="json")
    assert denied.status_code == 403, denied.data
    body["reviewer_membership_id"] = str(reviewer.id)
    result = admin.post(endpoint + "replace_authority/", body, format="json")
    assert result.status_code == 200, result.data
    assert set(result.data["resource"]) == {"id", "revision"}
    receipt = admin.get(
        API + f"rental-operations/{body['request_key']}/", {"subject_id": str(item.id)}
    )
    assert receipt.status_code == 200, receipt.data
    assert receipt.data["status"] == "confirmed"
    assert receipt.data["operation_receipt"] == result.data["operation_receipt"]
    from core_apps.features.planning_models import PlanningEvent
    from core_apps.features.services.planning_notifications_parts.event_copy import (
        event_copy,
    )

    notification = PlanningEvent.objects.filter(
        recipient=actors["reviewer"],
        destination__event_kind="company_responsibility_updated",
    ).latest("created_at")
    assert notification.destination["company_role"] == "admin"
    assert notification.destination["target_id"] == str(item.id)
    assert "lease_id" not in notification.destination
    assert event_copy(notification)
    change = item.changes.get(kind="authority")
    assert change.decisions == {}
    decision = command(
        expected_revision=item.lease.revision,
        change_id=str(change.id),
        digest=change.snapshot_digest,
        role="administrator",
        decision="accept",
    )
    denied = admin.post(endpoint + "respond_change/", decision, format="json")
    assert denied.status_code == 403
    reviewer_client = client(actors["reviewer"], company, "admin")
    item.lease.refresh_from_db()
    decision["expected_revision"] = item.lease.revision
    accepted = reviewer_client.post(
        endpoint + "respond_change/", decision, format="json"
    )
    assert accepted.status_code == 200, accepted.data
    for role, identity in change.snapshot["required"].items():
        if role == "administrator":
            continue
        actor = User.objects.get(id=identity)
        selected = {
            "new_signer": "signer",
            "new_payer": "payer",
            "new_coordinator": "coordinator",
        }[role]
        view = client(actor, company, selected).get(
            API + f"company-tenancies/{item.id}/"
        )
        assert view.status_code == 200, view.data
        task = next(c for c in view.data["changes"] if c["id"] == str(change.id))
        assert task["roles_to_decide"] == [role]
        assert set(task["content"]) <= {selected + "_name"}
        response = act(
            item,
            actor,
            "respond_change",
            change_id=str(change.id),
            digest=change.snapshot_digest,
            role=role,
            decision="accept",
        )
        assert response.status_code == 200, response.data
    item.refresh_from_db()
    change.refresh_from_db()
    assert change.state == "applied" and item.coordinator_id == incoming.pk
    assert (
        client(actors["coordinator"], company, "coordinator")
        .get(API + f"company-tenancies/{item.id}/")
        .status_code
        == 404
    )
    assert admin.get(API + f"company-tenancies/{item.id}/").status_code == 404
    reviewer.is_active = False
    reviewer.save()
    assert reviewer_client.get(endpoint).status_code == 404
    from rest_framework.exceptions import NotFound

    with pytest.raises(NotFound):
        event_copy(notification)

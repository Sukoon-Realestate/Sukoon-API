from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.features.models import ReputationAccessGrant, RentalSummaryGrant, ReviewAuditEvent
from .test_reputation import actors, stay, BASE
from .test_rental_phase2 import authenticated
from .test_student_housing import student_capabilities

pytestmark = pytest.mark.django_db


def grant(owner, recipient, **kw):
    return ReputationAccessGrant.objects.create(owner=owner, recipient=recipient,
        subject_kind="person_tenant", purpose="Application review",
        expires_at=timezone.now()+timedelta(days=3), **kw)


def rows(response):
    assert response.status_code == 200, response.data
    return response.data["results"] if "results" in response.data else response.data["data"]["results"]


def test_reputation_owner_preview_matches_recipient_without_mutating_audit(actors):
    owner, tenant, peer, outsider, *_ = actors
    item = grant(tenant, owner)
    recipient = authenticated(owner).get(BASE+f"reputation-grants/{item.id}/summary/")
    before = ReviewAuditEvent.objects.count()
    preview = authenticated(tenant).get(BASE+f"reputation-grants/{item.id}/preview/")
    assert preview.status_code == 200, preview.data
    assert preview["Cache-Control"] == "private, no-store"
    for key in ["subject_kind", "average", "review_count", "distribution", "criteria"]:
        assert preview.data[key] == recipient.data[key]
    assert preview.data["grant_revision"] == item.revision
    assert ReviewAuditEvent.objects.count() == before
    assert authenticated(outsider).get(BASE+f"reputation-grants/{item.id}/preview/").status_code == 404
    assert authenticated(owner).get(BASE+f"reputation-grants/{item.id}/preview/").status_code == 404


@pytest.mark.parametrize("expired", [False, True])
def test_inactive_grant_removes_preview_and_actions(actors, expired):
    owner, tenant, *_ = actors
    item = grant(tenant, owner)
    if expired:
        item.expires_at = timezone.now()-timedelta(seconds=1)
    else:
        item.revoked_at = timezone.now()
    item.save()
    result = rows(authenticated(tenant).get(BASE+"reputation-grants/?direction=sent"))[0]
    assert result["status"] == ("expired" if expired else "revoked")
    assert not result["can_read"] and not result["can_preview"] and not result["can_revoke"]
    assert result["allowed_actions"] == []
    assert authenticated(tenant).get(BASE+f"reputation-grants/{item.id}/preview/").status_code >= 400


def test_sent_grants_are_account_scoped_and_reject_company_context(actors):
    owner, tenant, peer, outsider, *_ = actors
    own = grant(tenant, owner)
    grant(peer, tenant)
    assert [r["id"] for r in rows(authenticated(tenant).get(BASE+"reputation-grants/?direction=sent"))] == [str(own.id)]
    assert rows(authenticated(outsider).get(BASE+"reputation-grants/?direction=sent")) == []
    assert authenticated(tenant).get(BASE+"reputation-grants/?direction=sent", HTTP_X_SUKOON_COMPANY_ROLE="payer").status_code == 403


def test_outgoing_family_shares_across_leases_remain_private(actors, student_capabilities):
    owner, tenant, peer, outsider, *_ = actors
    lease = stay(actors)
    grant = RentalSummaryGrant.objects.create(lease=lease, granted_by=tenant, recipient=peer,
        scopes=["booking"], expires_at=timezone.now()+timedelta(days=2))
    url = BASE+"shared-rental-summaries/?direction=sent"
    result = rows(authenticated(tenant).get(url))
    assert [r["id"] for r in result] == [str(grant.id)]
    assert result[0]["allowed_actions"] == ["revoke"]
    assert result[0]["booking"]["monthly_rent"]["amount_minor"] == lease.rent_amount_minor
    assert rows(authenticated(outsider).get(url)) == []
    assert rows(authenticated(peer).get(url)) == []
    assert authenticated(tenant).get(url, HTTP_X_SUKOON_COMPANY_ROLE="payer").status_code == 403
    grant.revoked_at = timezone.now()
    grant.save()
    revoked = rows(authenticated(tenant).get(url))[0]
    assert revoked["status"] == "revoked" and "booking" not in revoked

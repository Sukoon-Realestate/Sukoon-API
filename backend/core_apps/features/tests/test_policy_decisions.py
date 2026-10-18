import pytest
from django.core.exceptions import ValidationError
from core_apps.features.models import PolicyDecision
from core_apps.users.tests.test_security_recovery import assurance

pytestmark = pytest.mark.django_db


def test_draft_is_not_approved_and_approval_requires_complete_evidence(user):
    draft = PolicyDecision.objects.create(
        code="D28",
        version="synthetic-draft",
        owner="security",
        source="unapproved proposal",
    )
    assert draft.status == "draft"
    draft.status = "approved"
    draft.approver = user
    with pytest.raises(ValidationError):
        draft.save()
    draft.refresh_from_db()
    assert draft.status == "draft"


def test_approved_evidence_cannot_be_reinterpreted_or_revived(assurance):
    assurance.rules = {"proof_lifetime_seconds": 99999}
    with pytest.raises(ValidationError):
        assurance.save()
    assurance.refresh_from_db()
    assurance.status = "retired"
    assurance.save()
    assurance.status = "approved"
    with pytest.raises(ValidationError):
        assurance.save()

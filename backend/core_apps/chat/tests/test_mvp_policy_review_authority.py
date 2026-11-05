"""Independent decisions for the active direct-chat policy; no provider calls."""
import uuid

import pytest
from rest_framework.exceptions import PermissionDenied

from core_apps.chat.models import ChatModerationCase
from core_apps.chat.moderation.decisions import review
from core_apps.users.totp_models import StaffSecurityIdentity
from .test_rental_moderation import rental_chat, run, send  # noqa: F401

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('participant_index', [1, 2])
@pytest.mark.parametrize('second_account', [False, True])
def test_policy_decision_requires_independence_from_both_participants(
    rental_chat, superuser, participant_index, second_account
):
    chat, sender, _ = rental_chat
    send(chat, sender)
    run()
    case = ChatModerationCase.objects.get()
    participant = rental_chat[participant_index]
    if second_account:
        actor = superuser
        for account in (actor, participant):
            StaffSecurityIdentity.objects.create(
                user=account, person_reference='synthetic-shared-person',
                evidence_reference='synthetic-identity',
                known_channel_reference='synthetic-channel',
            )
    else:
        actor = participant
        actor.is_staff = actor.is_superuser = True
        actor.save(update_fields=['is_staff', 'is_superuser'])
    with pytest.raises(PermissionDenied, match='independent reviewer'):
        review(actor, case.id, uuid.uuid4(), case.revision, 'dismiss', 'Fixture decision')
    case.refresh_from_db()
    assert case.state == 'warning' and case.revision == 1
    assert not case.actions.exists() and case.report.reviewed_by_id is None


def test_policy_receipt_recovery_rechecks_current_independence(rental_chat, superuser):
    chat, sender, _ = rental_chat
    send(chat, sender)
    run()
    case = ChatModerationCase.objects.get()
    key = uuid.uuid4()
    result = review(superuser, case.id, key, 1, 'dismiss', 'Independent fixture decision')
    assert result['state'] == 'dismissed'
    assert review(superuser, case.id, key, 1, 'dismiss', 'Independent fixture decision') == result
    for account in (superuser, sender):
        StaffSecurityIdentity.objects.create(
            user=account, person_reference='synthetic-shared-person',
            evidence_reference='synthetic-identity', known_channel_reference='synthetic-channel',
        )
    with pytest.raises(PermissionDenied, match='independent reviewer'):
        review(superuser, case.id, key, 1, 'dismiss', 'Independent fixture decision')
    assert case.actions.count() == 1


def test_policy_release_preserves_other_case_and_administrative_block(rental_chat, superuser):
    from core_apps.admin_api.models import UserReport
    from core_apps.chat.models import AccountRestriction
    from core_apps.chat.moderation.policy import restricted

    chat, sender, _ = rental_chat
    send(chat, sender)
    run()
    case = ChatModerationCase.objects.get()
    AccountRestriction.objects.create(case=case, user=sender)
    other = ChatModerationCase.objects.create(
        report=UserReport.objects.create(reported_user=sender, reason='Independent fixture case'),
        conversation=chat, subject=sender, batch=case.batch,
        dedupe_key='independent-fixture-case', state='pending_review',
        policy_version=case.policy_version, evidence_ciphertext=case.evidence_ciphertext,
    )
    AccountRestriction.objects.create(case=other, user=sender)
    sender.is_active = False
    sender.save(update_fields=['is_active'])
    review(superuser, case.id, uuid.uuid4(), 1, 'release', 'Release only this exact case')
    sender.refresh_from_db()
    other.refresh_from_db()
    assert not sender.is_active and restricted(sender)
    assert other.state == 'pending_review' and other.revision == 1
    assert other.restriction.state == 'pending_review' and not other.actions.exists()
    assert AccountRestriction.objects.get(case=case).state == 'released'

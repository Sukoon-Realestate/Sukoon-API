import uuid
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
import pytest
from django.utils import timezone
from django.db import IntegrityError, transaction, connection
from django.core.management import call_command
from rest_framework.test import APIClient
from core_apps.features.models import (
    Lease,
    RentalHandover,
    ReviewCase,
    ReviewOpportunity,
    ReviewSection,
    ReviewSubmission,
    ReviewAuditEvent,
    IdempotencyRecord,
    Company,
    CompanyMembership,
)
from core_apps.properties.models import (
    Property,
    PropertyType,
    City,
    Governorate,
    PropertyVisit,
    PropertyVisitDecision,
)
from core_apps.users.models import User
from core_apps.features.services.reputation import (
    generation,
    submission,
    visibility,
    moderation,
    grants,
)
from core_apps.features.services.reputation.policy import ReviewError
from core_apps.features.services.reputation.tasks import reconcile

BASE = "/api/v1/features/v1/"


@pytest.fixture
def actors(db, settings):
    settings.REVIEWS_ENABLED = True
    owner, tenant, peer, outsider, moderator, second = [
        User.objects.create_user(
            email=f"rating-{name}@example.test",
            password="test",
            is_verified=True,
            is_staff=name in ["mod", "second"],
            is_superuser=name in ["mod", "second"],
        )
        for name in ["owner", "tenant", "peer", "outsider", "mod", "second"]
    ]
    g = Governorate.objects.create(name="Rating Cairo")
    c = City.objects.create(name="Rating city", governorate=g)
    t = PropertyType.objects.create(name="Rating apartment", slug="rating-apartment")
    prop = Property.objects.create(
        owner=owner,
        title="Rating home",
        price=1000,
        property_type=t,
        governorate=g,
        city=c,
        district="District",
        status="verified",
        is_verified=True,
    )
    return owner, tenant, peer, outsider, moderator, second, prop


def stay(actors, *, tenant=None, nights=10, end=True, start=True, root=None):
    owner, person, *_, prop = actors
    now = timezone.now()
    person = tenant or person
    lease = Lease.objects.create(
        property=prop,
        owner=owner,
        tenant=person,
        template_id="test",
        template_version="1",
        start_date=now.date() - timedelta(days=nights),
        end_date=now.date(),
        rent_amount_minor=1000,
        status="ended",
        occupancy_status="returned" if end else "occupied",
        legacy_read_only=False,
        offer_id=str(uuid.uuid4()),
        offer_snapshot={"rental_scope": "room", "room_ids": [str(uuid.uuid4())]},
        **({"tenancy_root_id": root} if root else {}),
    )
    for kind, day, timestamp, enabled in [
        ("move_in", lease.start_date, now - timedelta(days=nights), start),
        ("move_out", lease.end_date, now, end),
    ]:
        if enabled:
            RentalHandover.objects.create(
                lease=lease,
                kind=kind,
                possession_on=day,
                status="accepted",
                accepted_at=timestamp,
                approvals=[str(owner.id), str(person.id)],
            )
    return lease


def body(opp, score=4, target=None, **extra):
    return {
        "request_key": str(uuid.uuid4()),
        "expected_revision": opp.revision,
        "policy_version": opp.case.policy_version,
        "criteria_schema_version": opp.case.criteria_schema_version,
        "sections": [
            {
                "target_key": target or opp.allowed_targets[0]["key"],
                "overall_score": score,
                "criteria": {},
                "comment": "تجربة هادئة",
                "tag_codes": [],
            }
        ],
        **extra,
    }


def send_pair(actors):
    case = generation.generate_tenancy(stay(actors))
    a, b = [case.opportunities.get(reviewer=u) for u in actors[:2]]
    ra = submission.submit(actors[0], a.id, body(a))
    rb = submission.submit(actors[1], b.id, body(b))
    return case, a, b, ra, rb


def approve(actors, section):
    return moderation.moderate(
        actors[4],
        section.id,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": section.revision,
            "action": "approve",
            "reason": "Checked relevance and privacy",
        },
    )


def client(user=None):
    c = APIClient()
    if user:
        c.force_authenticate(user)
    return c


def test_actual_exit_opportunities_and_no_financial_condition(actors):
    lease = stay(actors, nights=1)
    case = generation.generate_tenancy(lease)
    assert case.opportunities.count() == 2
    assert len(case.opportunities.get(reviewer=actors[1]).allowed_targets) == 2
    assert generation.generate_tenancy(lease).id == case.id
    assert ReviewCase.objects.count() == 1


@pytest.mark.parametrize(
    "start,end,code",
    [(False, False, "experience_not_confirmed"), (True, False, "occupancy_not_ended")],
)
def test_payment_or_movein_not_enough(actors, start, end, code):
    with pytest.raises(ReviewError) as err:
        generation.generate_tenancy(stay(actors, start=start, end=end))
    assert err.value.get_codes() == code


def test_one_side_is_sealed_everywhere(actors):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    result = submission.submit(actors[1], opp.id, body(opp))
    section = ReviewSection.objects.get(id=result["section_ids"][0])
    approve(actors, section)
    section.refresh_from_db()
    assert not visibility.visible(section, actors[0])
    assert visibility.summary("person_landlord", actors[0].id)["review_count"] == 0
    assert client(actors[0]).get(BASE + "reviews/received/").json()["data"] == []
    assert client(actors[0]).get(BASE + f"reviews/{section.id}/").status_code == 404
    assert (
        client(actors[1])
        .get(BASE + f"reviews/{section.id}/")
        .json()["data"]["gate_state"]
        == "waiting"
    )


def test_mutual_gate_does_not_approve_content(actors):
    case, a, b, ra, rb = send_pair(actors)
    case.refresh_from_db()
    assert case.gate_released_at
    assert visibility.summary("person_landlord", actors[0].id)["average"] is None
    s = ReviewSection.objects.get(id=rb["section_ids"][0])
    approve(actors, s)
    assert visibility.summary("person_landlord", actors[0].id)["average"] == 4
    assert (
        visibility.summary("person_tenant", actors[1].id, actors[1])["average"] is None
    )


def test_boundary_and_worker_independent_read_release(actors, monkeypatch):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    submission.submit(actors[1], opp.id, body(opp))
    s = ReviewSection.objects.get()
    approve(actors, s)
    other = case.opportunities.get(reviewer=actors[0])
    monkeypatch.setattr(timezone, "now", lambda: case.closes_at)
    with pytest.raises(ReviewError) as err:
        submission.submit(actors[0], other.id, body(other))
    assert err.value.get_codes() == "review_window_closed"
    assert visibility.summary("person_landlord", actors[0].id)["review_count"] == 1
    reconcile()
    reconcile()
    case.refresh_from_db()
    assert case.gate_released_at


@pytest.mark.parametrize("score", [0, 6, 2.5, True, False, "5", None])
def test_strict_scores_rollback(actors, score):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    with pytest.raises(ReviewError):
        submission.submit(actors[1], opp.id, body(opp, score))
    assert not ReviewSubmission.objects.exists()


@pytest.mark.parametrize(
    "field,value",
    [
        ("reviewer_id", "forged"),
        ("company_id", "forged"),
        ("visibility", "public"),
        ("published_at", "now"),
    ],
)
def test_forged_subjects_rejected(actors, field, value):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    with pytest.raises(ReviewError):
        submission.submit(actors[1], opp.id, body(opp, **{field: value}))
    assert not ReviewSubmission.objects.exists()


def test_replay_unknown_and_kill_switch(actors, settings):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    data = body(opp)
    receipt = submission.submit(actors[1], opp.id, data)
    settings.REVIEWS_ENABLED = False
    assert submission.submit(actors[1], opp.id, data) == receipt
    assert submission.lookup(actors[1], data["request_key"])["receipt"] == receipt
    assert submission.lookup(actors[3], data["request_key"])["state"] == "unknown"
    altered = {**data, "sections": [{**data["sections"][0], "overall_score": 1}]}
    with pytest.raises(ReviewError) as err:
        submission.submit(actors[1], opp.id, altered)
    assert err.value.get_codes() == "idempotency_payload_mismatch"
    assert ReviewSubmission.objects.count() == 1


def test_null_criteria_optional_section_and_private_summary(actors):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    data = body(opp, target="property")
    data["sections"][0]["criteria"] = {"utilities": None, "quietness": 5}
    receipt = submission.submit(actors[1], opp.id, data)
    other = case.opportunities.get(reviewer=actors[0])
    submission.submit(actors[0], other.id, body(other))
    section = ReviewSection.objects.get(id=receipt["section_ids"][0])
    approve(actors, section)
    result = visibility.summary("property_stay", actors[-1].id)
    assert result["criteria"] == {
        "quietness": {"average": 5.0, "answered_count": 1, "label": "Quietness"}
    }
    assert result["review_count"] == sum(result["distribution"].values()) == 1
    assert visibility.summary("person_landlord", actors[0].id)["average"] is None
    assert (
        client(actors[0])
        .get(BASE + f"reviews/subjects/person_tenant/{actors[1].id}/summary/")
        .status_code
        == 404
    )


@pytest.mark.parametrize(
    "comment",
    [
        "<b>bad</b>",
        "https://example.com",
        "me@example.com",
        "010 1234 5678",
        "a" * 1501,
    ],
)
def test_plain_text_privacy_validation(actors, comment):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    data = body(opp)
    data["sections"][0]["comment"] = comment
    with pytest.raises(ReviewError):
        submission.submit(actors[1], opp.id, data)


def test_reply_withdrawal_report_and_appeal(actors):
    case, a, b, ra, rb = send_pair(actors)
    s = ReviewSection.objects.get(id=rb["section_ids"][0])
    decision = approve(actors, s)
    s.refresh_from_db()
    reply = moderation.section_action(
        actors[0],
        s.id,
        "reply",
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": s.revision,
            "comment": "شكرًا",
        },
    )
    for _ in range(2):
        moderation.section_action(
            actors[0],
            s.id,
            "reports",
            {
                "request_key": str(uuid.uuid4()),
                "expected_revision": s.revision,
                "reason_code": "outside_experience",
            },
        )
    from core_apps.features.models import ReviewReport

    assert ReviewReport.objects.count() == 1
    assert visibility.summary("person_landlord", actors[0].id)["review_count"] == 1
    appeal = moderation.appeal_decision(
        actors[1],
        decision["id"],
        {"request_key": str(uuid.uuid4()), "detail": "Please review"},
    )
    with pytest.raises(ReviewError):
        moderation.resolve_appeal(
            actors[4],
            appeal["id"],
            {
                "request_key": str(uuid.uuid4()),
                "expected_revision": 1,
                "reason": "Confirmed",
            },
        )
    moderation.resolve_appeal(
        actors[5],
        appeal["id"],
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": 1,
            "reason": "Confirmed",
        },
    )
    moderation.section_action(
        actors[1],
        s.id,
        "withdraw",
        {"request_key": str(uuid.uuid4()), "expected_revision": s.revision},
    )
    assert visibility.summary("person_landlord", actors[0].id)["review_count"] == 0
    assert submission.submit(actors[1], b.id, body(b))["id"] == rb["id"]


def test_grants_are_recipient_scoped_and_no_text(actors):
    case, a, b, ra, rb = send_pair(actors)
    s = ReviewSection.objects.get(id=ra["section_ids"][0])
    approve(actors, s)
    grant = grants.create(
        actors[1],
        {
            "request_key": str(uuid.uuid4()),
            "subject_kind": "person_tenant",
            "recipient_id": str(actors[3].id),
            "purpose": "Housing application",
        },
    )
    result = grants.read(actors[3], grant["id"])
    assert result["review_count"] == 1
    assert "comment" not in str(result)
    with pytest.raises(Exception):
        grants.read(actors[0], grant["id"])
    grants.revoke(
        actors[1],
        grant["id"],
        {"request_key": str(uuid.uuid4()), "expected_revision": 1},
    )
    with pytest.raises(ReviewError):
        grants.read(actors[3], grant["id"])


@pytest.mark.parametrize("nights,allowed", [(6, False), (7, True)])
def test_housemates_exact_overlap(actors, nights, allowed):
    a = stay(actors, nights=nights)
    b = stay(actors, tenant=actors[2], nights=nights)
    if allowed:
        case = generation.generate_housemates(a, b)
        assert generation.generate_housemates(b, a).id == case.id
        assert all(
            t["visibility"] == "private"
            for o in case.opportunities.all()
            for t in o.allowed_targets
        )
    else:
        with pytest.raises(ReviewError):
            generation.generate_housemates(a, b)


def test_company_rows_do_not_grant_personal_or_corporate_review(actors):
    co = Company.objects.create(
        name="Synthetic company",
        registration_number="TEST",
        contact_email="company@example.test",
    )
    CompanyMembership.objects.create(
        company=co, user=actors[1], is_admin=True, is_employee=True
    )
    response = client(actors[1]).get(
        BASE + "reviews/opportunities/", {"company_id": str(co.id)}
    )
    assert response.status_code == 200
    assert response.data["results"] == []
    assert not ReviewCase.objects.exists()
    assert (
        client(actors[1])
        .get(BASE + "reviews/capabilities/")
        .json()["data"]["capabilities"]["review_company_relationships"]
        is True
    )


def test_attendance_not_elapsed_time(actors):
    now = timezone.now()
    visit = PropertyVisit.objects.create(
        property=actors[-1],
        tenant=actors[1],
        visit_date=now.date() - timedelta(days=1),
        visit_time=now.time(),
        status="confirmed",
    )
    with pytest.raises(ReviewError):
        generation.generate_viewing(visit)
    PropertyVisitDecision.objects.create(
        visit=visit,
        tenant=actors[1],
        owner=actors[0],
        value="proceed",
        attested_at=now,
        visit_revision=visit.revision,
        request_key=uuid.uuid4(),
        property_id_snapshot=visit.property.id,
        scheduled_at=now - timedelta(days=1),
    )
    case = generation.generate_viewing(visit)
    opp = case.opportunities.get()
    submission.submit(actors[1], opp.id, body(opp))
    approve(actors, ReviewSection.objects.get())
    assert visibility.summary("property_visit", actors[-1].id)["review_count"] == 1
    assert visibility.summary("property_stay", actors[-1].id)["review_count"] == 0
    assert visibility.summary("person_landlord", actors[0].id)["review_count"] == 0


def test_api_envelope_private_cache_and_no_target_ids(actors):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    response = client(actors[1]).get(BASE + f"reviews/opportunities/{opp.id}/")
    assert response.status_code == 200
    assert set(response.json()) == {"message", "data"}
    assert "no-store" in response["Cache-Control"]
    assert "id" not in response.json()["data"]["allowed_targets"][0]
    assert (
        client(actors[3]).get(BASE + f"reviews/opportunities/{opp.id}/").status_code
        == 404
    )
    assert (
        client(actors[1])
        .post(BASE + f"leases/{case.lease.id}/reviews/", body(opp), format="json")
        .status_code
        == 409
    )


def test_removed_source_invalidates_summary_without_worker(actors):
    case, a, b, ra, rb = send_pair(actors)
    s = ReviewSection.objects.get(id=rb["section_ids"][0])
    approve(actors, s)
    assert visibility.summary("person_landlord", actors[0].id)["review_count"] == 1
    RentalHandover.objects.filter(lease=case.lease, kind="move_out").update(
        status="disputed"
    )
    assert visibility.summary("person_landlord", actors[0].id)["average"] is None


def test_changed_owner_does_not_receive_previous_personal_score(actors):
    case, a, b, ra, rb = send_pair(actors)
    s = ReviewSection.objects.get(id=rb["section_ids"][0])
    approve(actors, s)
    prop = actors[-1]
    prop.owner = actors[3]
    prop.save()
    assert visibility.summary("person_landlord", actors[0].id)["review_count"] == 1
    assert visibility.summary("person_landlord", actors[3].id)["average"] is None
    assert (
        client(actors[3])
        .post(
            BASE + f"reviews/{s.id}/reply/",
            {"request_key": str(uuid.uuid4()), "expected_revision": 2, "comment": "No"},
            format="json",
        )
        .status_code
        == 404
    )


def test_legacy_import_idempotent_and_never_promotes_to_verified(actors):
    from core_apps.features.models import RentalReview
    from core_apps.features.services.reputation.legacy import migrate_legacy

    lease = stay(actors)
    RentalReview.objects.create(
        lease=lease, author=actors[1], rating=5, comment="Historical"
    )
    assert migrate_legacy()["imported"] == 1
    assert migrate_legacy()["imported"] == 0
    assert ReviewSection.objects.count() == 1
    assert visibility.summary("person_landlord", actors[0].id)["average"] is None
    assert (
        client(actors[3])
        .get(BASE + f"reviews/{ReviewSection.objects.get().id}/")
        .status_code
        == 404
    )
    case = generation.generate_tenancy(lease)
    assert case.opportunities.get(reviewer=actors[1]).state == "revoked"


def test_direct_database_score_constraint(actors):
    case, a, b, ra, rb = send_pair(actors)
    with pytest.raises(IntegrityError), transaction.atomic():
        ReviewSection.objects.filter(id=ra["section_ids"][0]).update(overall_score=0)


def test_moderation_redaction_cannot_rewrite_opinion_or_score(actors):
    case, a, b, ra, rb = send_pair(actors)
    s = ReviewSection.objects.get(id=rb["section_ids"][0])
    approve(actors, s)
    s.refresh_from_db()
    with pytest.raises(ReviewError):
        moderation.moderate(
            actors[4],
            s.id,
            {
                "request_key": str(uuid.uuid4()),
                "expected_revision": s.revision,
                "action": "redact",
                "reason": "privacy",
                "redacted_comment": "A rewritten opinion",
            },
        )
    assert s.overall_score == 4


@pytest.mark.django_db(transaction=True)
def test_postgres_simultaneous_submission_and_pair_release(actors):
    if connection.vendor != "postgresql":
        pytest.skip("Row-lock concurrency requires PostgreSQL")
    from django.db import close_old_connections

    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    data = body(opp)
    user_id = actors[1].id

    def run():
        close_old_connections()
        try:
            return submission.submit(User.objects.get(id=user_id), opp.id, data)["id"]
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(lambda _: run(), range(2)))
    assert ids[0] == ids[1]
    assert ReviewSubmission.objects.count() == 1


def test_notifications_never_expose_submitted_opposite_content(actors):
    from core_apps.features.planning_models import PlanningEvent

    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    submission.submit(actors[1], opp.id, body(opp))
    approve(actors, ReviewSection.objects.get())
    events = list(
        PlanningEvent.objects.filter(recipient=actors[0]).values_list(
            "destination", flat=True
        )
    )
    assert len(events) == 1
    assert events[0]["review_event"] == "review_opportunity_opened"
    assert "score" not in str(events) and "comment" not in str(events)


def test_removed_target_receives_decision_metadata_without_hidden_content(actors):
    case, a, b, ra, rb = send_pair(actors)
    section = ReviewSection.objects.get(id=rb["section_ids"][0])
    moderation.moderate(
        actors[4],
        section.id,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": 1,
            "action": "reject",
            "reason": "Outside the confirmed experience",
        },
    )
    response = client(actors[0]).get(BASE + f"reviews/{section.id}/")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["content_state"] == "rejected" and data["decisions"][0]["can_appeal"]
    assert not {"overall_score", "comment", "criteria", "tag_codes"} & set(data)
    assert client(actors[3]).get(BASE + f"reviews/{section.id}/").status_code == 404


def test_appeal_window_starts_per_recipient_at_actual_notice(actors, monkeypatch):
    from core_apps.features.models import ReviewModerationDecision, ReviewDecisionNotice

    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    submission.submit(actors[1], opp.id, body(opp))
    section = ReviewSection.objects.get()
    decision = approve(actors, section)
    record = ReviewModerationDecision.objects.get(id=decision["id"])
    assert not ReviewDecisionNotice.objects.exists()
    visibility.section_payload(visibility.section_for(actors[1], section.id), actors[1])
    initial = timezone.now()
    monkeypatch.setattr(timezone, "now", lambda: initial + timedelta(days=31))
    # Target only receives the decision after the publication barrier opens.
    projection = visibility.section_payload(
        visibility.section_for(actors[0], section.id), actors[0]
    )
    assert projection["decisions"][0]["can_appeal"]
    assert not visibility.section_payload(
        visibility.section_for(actors[1], section.id), actors[1]
    )["decisions"][0]["can_appeal"]
    assert record.notices.count() == 2


def test_second_device_receives_canonical_receipt_without_second_vote(actors):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    first = submission.submit(actors[1], opp.id, body(opp, 1))
    second = submission.submit(actors[1], opp.id, body(opp, 5))
    assert first["id"] == second["id"] and second["already_submitted"]
    assert (
        ReviewSection.objects.get().overall_score == 1
        and ReviewSubmission.objects.count() == 1
    )


def test_invalid_nested_target_is_400_and_atomic(actors):
    case = generation.generate_tenancy(stay(actors))
    opp = case.opportunities.get(reviewer=actors[1])
    payload = body(opp)
    payload["sections"][0]["target_key"] = {"id": "injection"}
    assert (
        client(actors[1])
        .post(BASE + f"reviews/opportunities/{opp.id}/submit/", payload, format="json")
        .status_code
        == 400
    )
    assert ReviewSubmission.objects.count() == 0


def test_grant_boundary_expiry_and_invalid_duration(actors, monkeypatch):
    from core_apps.features.models import ReputationAccessGrant

    payload = {
        "request_key": str(uuid.uuid4()),
        "subject_kind": "person_tenant",
        "recipient_id": str(actors[3].id),
        "purpose": "Housing application",
        "days": 31,
    }
    with pytest.raises(ReviewError):
        grants.create(actors[1], payload)
    payload["days"] = 7
    result = grants.create(actors[1], payload)
    record = ReputationAccessGrant.objects.get(id=result["id"])
    monkeypatch.setattr(timezone, "now", lambda: record.expires_at)
    with pytest.raises(ReviewError) as error:
        grants.read(actors[3], record.id)
    assert error.value.get_codes() == "grant_expired"


def test_independent_appeal_restores_without_changing_score(actors):
    case, a, b, ra, rb = send_pair(actors)
    section = ReviewSection.objects.get(id=rb["section_ids"][0])
    decision = moderation.moderate(
        actors[4],
        section.id,
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": 1,
            "action": "reject",
            "reason": "Needs investigation",
        },
    )
    appeal = moderation.appeal_decision(
        actors[1],
        decision["id"],
        {"request_key": str(uuid.uuid4()), "detail": "Please investigate the evidence"},
    )
    moderation.resolve_appeal(
        actors[5],
        appeal["id"],
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": 1,
            "reason": "Confirmed relevant experience",
            "outcome": "restore",
        },
    )
    section.refresh_from_db()
    assert section.overall_score == 4 and section.content_state == "approved"


def test_disabled_staff_permission_and_conflict(actors):
    case, a, b, ra, rb = send_pair(actors)
    section = ReviewSection.objects.get(id=rb["section_ids"][0])
    actors[0].is_superuser = True
    actors[0].save()
    with pytest.raises(ReviewError) as error:
        moderation.moderate(
            actors[0],
            section.id,
            {
                "request_key": str(uuid.uuid4()),
                "expected_revision": 1,
                "action": "approve",
                "reason": "Own profile",
            },
        )
    assert error.value.get_codes() == "conflict_of_interest"
    response = client(actors[3]).get(
        "/api/v1/admin/reviews/", {"reason": "Review queue"}
    )
    assert response.status_code in {403, 404}


def test_demo_seed_is_local_and_repeatable(actors, settings):
    from django.core.management.base import CommandError

    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("seed_review_demo")
    settings.DEBUG = True
    call_command("seed_review_demo", confirm_local=True)
    count = ReviewCase.objects.count()
    call_command("seed_review_demo", confirm_local=True)
    assert ReviewCase.objects.count() == count


def test_grant_recipient_picker_has_only_known_counterparts(actors):
    stay(actors)
    result = client(actors[1]).get(BASE + "reputation-grants/recipients/")
    assert result.status_code == 200
    assert [row["id"] for row in result.json()["data"]] == [str(actors[0].id)]
    assert all(set(row) == {"id", "name"} for row in result.json()["data"])


def test_pending_reply_is_private_to_reply_author_and_can_be_withdrawn(actors):
    case, a, b, ra, rb = send_pair(actors)
    section = ReviewSection.objects.get(id=rb["section_ids"][0])
    approve(actors, section)
    section.refresh_from_db()
    reply = moderation.section_action(
        actors[0],
        section.id,
        "reply",
        {
            "request_key": str(uuid.uuid4()),
            "expected_revision": section.revision,
            "comment": "Thanks for the feedback",
        },
    )
    section = visibility.sections().get(pk=section.pk)
    own = visibility.section_payload(section, actors[0])
    assert own["reply"]["content_state"] == "pending" and own["reply"]["can_withdraw"]
    assert "reply" not in visibility.section_payload(section, actors[1])
    moderation.withdraw_reply(
        actors[0],
        reply["id"],
        {"request_key": str(uuid.uuid4()), "expected_revision": 1},
    )
    assert visibility.summary("person_landlord", actors[0].id)["review_count"] == 1

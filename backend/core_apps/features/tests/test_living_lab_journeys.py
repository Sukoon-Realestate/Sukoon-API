import copy
from datetime import timedelta
import pytest
from django.utils import timezone
from core_apps.features.models import GroupMembership, IdempotencyRecord, Lease
from core_apps.features.living_lab_models import (
    SharedLivingLab,
    SharedArrangementSnapshot,
)
from core_apps.features.planning_models import HousingRequest
from core_apps.features.services.living_lab.retention import purge_lab
from .test_living_lab import (
    API,
    command,
    create_lab,
    lab_capability,
    post,
    read,
    ready,
    requirements,
    respond,
)
from . import test_living_lab as test_living_lab_fixtures
from .test_rental_phase2 import authenticated, rental_participants

context = test_living_lab_fixtures.context


def configure(admin, lab, **values):
    return post(
        admin,
        f"living-labs/{lab['id']}/configuration/",
        command(lab["revision"], **values),
    ).data["resource"]


def submit_v2(user, lab, **values):
    raw = {
        "rent_max_minor": 100000,
        "deposit_max_minor": 100000,
        "accepted_start_on": lab["starts_on"],
        "accepted_end_on": lab["ends_on_exclusive"],
        "private_room": False,
        "required_room_id": "",
        "preferred_room_id": "",
        **values,
    }
    return post(
        user,
        f"living-labs/{lab['id']}/my-requirements/",
        command(
            lab["revision"],
            public_revision=lab["public_revision"],
            status="provided",
            purpose_version="living-lab-private-v1",
            purpose_accepted=True,
            values=raw,
        ),
    ).data["resource"]


def calculate(admin, lab):
    return post(admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"])).data[
        "resource"
    ]


@pytest.mark.django_db
def test_unequal_policy_requires_fresh_personal_purpose_and_enforces_exact_household_constraints(
    context, settings
):
    _, admin, member, _, _, _ = context
    settings.LIVING_LAB_MAX_RUNS_PER_LAB = 6
    lab = ready(context)
    weights = {str(admin.id): 2, str(member.id): 1}
    post(
        admin,
        f"living-labs/{lab['id']}/configuration/",
        command(
            lab["revision"],
            allocation_policy={
                "kind": "weighted",
                "weights": {str(admin.id): 5, str(member.id): 1},
            },
        ),
        400,
    )
    quiet = {"weekday": 1, "start_minute": 1200, "end_minute": 1440}
    chore = {
        "id": "clean",
        "title": "Shared cleaning",
        "user_id": str(member.id),
        "weekday": 2,
        "start_minute": 600,
        "duration_minutes": 30,
    }
    lab = configure(
        admin,
        lab,
        allocation_policy={"kind": "weighted", "weights": weights},
        household_plan={
            "quiet_windows": [quiet],
            "chores": [chore],
            "expense_minor": 301,
        },
    )
    lab = calculate(admin, lab)
    assert lab["latest_run"]["outcome"] == "invalid_input"
    lab = submit_v2(admin, lab, expense_max_minor=1000, quiet_windows=[quiet])
    lab = submit_v2(
        member,
        lab,
        expense_max_minor=1000,
        accepted_chore_ids=["clean"],
        unavailable_windows=[{"weekday": 2, "start_minute": 590, "end_minute": 640}],
    )
    lab = calculate(admin, lab)
    assert lab["latest_run"]["outcome"] == "infeasible"
    lab = submit_v2(member, lab, expense_max_minor=1000, accepted_chore_ids=["clean"])
    lab = calculate(admin, lab)
    candidate = lab["latest_run"]["candidates"][0]
    assert sum(v["rent_minor"] for v in candidate["shares"]) == 10001
    assert sum(v["deposit_minor"] for v in candidate["shares"]) == 5001
    assert sum(v["expense_minor"] for v in candidate["shares"]) == 301
    assert {v["user_id"]: v["rent_minor"] for v in candidate["shares"]} == {
        str(admin.id): 6667,
        str(member.id): 3334,
    }
    assert {v["user_id"]: v["expense_minor"] for v in candidate["shares"]} == {
        str(admin.id): 201,
        str(member.id): 100,
    }
    assert "expense_max_minor" not in str(candidate)
    assert candidate["household_plan"]["chores"] == [chore]
    lab = respond(admin, lab)
    lab = respond(member, lab)
    assert lab["agreements"][0]["snapshot"]["household_plan"]["quiet_windows"] == [
        quiet
    ]


@pytest.mark.django_db
def test_negotiated_amounts_do_not_use_private_maxima_and_disclosure_is_exact_and_revocable(
    context,
):
    _, admin, member, _, _, rooms = context
    lab = create_lab(context)
    allocation = {
        "kind": "negotiated",
        "rent_shares": {str(admin.id): 6000, str(member.id): 4001},
        "deposit_shares": {str(admin.id): 3000, str(member.id): 2001},
    }
    lab = configure(admin, lab, allocation_policy=allocation)
    lab = submit_v2(admin, lab, preferred_room_id=rooms[0]["id"])
    mine = (
        authenticated(admin).get(API + f"living-labs/{lab['id']}/my-requirements/").data
    )
    body = command(
        lab["revision"],
        public_revision=lab["public_revision"],
        requirement_revision=mine["requirement_revision"],
        fields=["preferred_room_id"],
        consent=True,
    )
    lab = post(admin, f"living-labs/{lab['id']}/disclosures/", body).data["resource"]
    assert read(member, lab)["disclosures"][0]["values"] == {
        "preferred_room_id": rooms[0]["id"]
    }
    post(
        admin,
        f"living-labs/{lab['id']}/disclosures/",
        command(
            lab["revision"],
            public_revision=lab["public_revision"],
            requirement_revision=mine["requirement_revision"],
            fields=["rent_max_minor"],
            consent=True,
        ),
        400,
    )
    lab = submit_v2(admin, lab, rent_max_minor=6000)
    assert read(member, lab)["disclosures"] == []
    replay = post(admin, f"living-labs/{lab['id']}/disclosures/", body).data
    assert replay["resource"]["disclosures"] == []
    assert replay["resource"]["my_disclosure_fields"] == []
    assert replay["operation_receipt"]["request_key"] == body["request_key"]
    lab = submit_v2(member, lab, rent_max_minor=4001)
    lab = calculate(admin, lab)
    assert lab["latest_run"]["candidates"][0]["policy"] == "negotiated"
    assert {
        v["user_id"]: v["rent_minor"]
        for v in lab["latest_run"]["candidates"][0]["shares"]
    } == allocation["rent_shares"]


@pytest.mark.django_db
def test_scenario_is_separate_no_copied_inputs_or_consents_and_counterfactual_cannot_handoff(
    context,
):
    _, admin, member, _, group, _ = context
    original = respond(member, respond(admin, ready(context)))
    snapshot = copy.deepcopy(original["agreements"][0]["snapshot"])
    body = command(
        original["revision"],
        kind="departure",
        expected_group_revision=group.revision,
        agreement_id=original["agreements"][0]["id"],
        departing_user_id=str(member.id),
    )
    path = f"living-labs/{original['id']}/scenario-runs/"
    child = post(admin, path, body).data["resource"]
    assert child["id"] != original["id"] and child["ready_count"] == 0
    assert post(admin, path, body).data["resource"]["id"] == child["id"]
    child = submit_v2(admin, child)
    child = calculate(admin, child)
    candidate = child["latest_run"]["candidates"][0]
    assert (
        len(candidate["shares"]) == 1 and candidate["shares"][0]["rent_minor"] == 10001
    )
    assert candidate["obligations_unchanged"] is True
    child = respond(admin, child)
    assert child["agreements"] == []
    child = respond(member, child)
    assert "prepare_cost_proposal" not in child["allowed_actions"]
    post(
        admin,
        f"living-labs/{child['id']}/prepare-cost-proposal/",
        command(
            child["revision"],
            expected_group_revision=group.revision,
            agreement_id=child["agreements"][0]["id"],
        ),
        403,
    )
    assert (
        SharedArrangementSnapshot.objects.get(
            id=original["agreements"][0]["id"]
        ).snapshot
        == snapshot
    )
    assert Lease.objects.count() == 0


@pytest.mark.django_db
def test_retention_purges_private_and_uncommitted_copies_but_preserves_agreements_receipts_and_withdrawal(
    context, settings
):
    _, admin, member, _, _, _ = context
    lab = ready(context)
    lab = respond(member, respond(admin, lab))
    accepted = copy.deepcopy(lab["agreements"][0]["snapshot"])
    model = SharedLivingLab.objects.get(id=lab["id"])
    consents = list(
        model.requirements.order_by("pkid").values_list(
            "purpose_version", "consented_at"
        )
    )
    future = timezone.now() + timedelta(days=60)
    assert purge_lab(model.pk, now=future)
    model.refresh_from_db()
    assert all(row.private_values == {} for row in model.requirements.all())
    assert (
        list(
            model.requirements.order_by("pkid").values_list(
                "purpose_version", "consented_at"
            )
        )
        == consents
    )
    assert model.agreements.get().snapshot == accepted
    assert model.runs.get().input_digest == ""
    assert not purge_lab(model.pk, now=future)
    for record in IdempotencyRecord.objects.filter(result_subject_id=model.id):
        assert (
            record.recovery_status == "confirmed"
            and record.response_data["operation_receipt"]["id"]
        )
        assert (
            len(
                (record.response_data["resource"].get("latest_run") or {}).get(
                    "candidates", []
                )
            )
            <= 1
        )
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = []
    fresh = read(admin, lab)
    post(admin, f"living-labs/{lab['id']}/withdraw/", command(fresh["revision"]))


@pytest.mark.django_db
def test_application_handoff_starts_canonical_individual_consent_and_tender_preserves_lineage(
    context, settings
):
    _, admin, member, _, group, _ = context
    settings.PLANNING_ENABLED_SERVICES = ["housing_groups", "group_applications"]
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = [
        "shared_living_lab",
        "collective_tender_planning",
    ]
    lab = respond(member, respond(admin, ready(context)))
    lab = post(
        admin,
        f"living-labs/{lab['id']}/prepare-cost-proposal/",
        command(
            lab["revision"],
            expected_group_revision=lab["group_revision"],
            agreement_id=lab["agreements"][0]["id"],
        ),
    ).data["resource"]
    post(
        admin,
        f"living-labs/{lab['id']}/prepare-application/",
        command(
            lab["revision"],
            expected_group_revision=lab["group_revision"],
            agreement_id=lab["agreements"][0]["id"],
        ),
        409,
    )
    group.refresh_from_db()
    for person in [admin, member]:
        proposal = group.proposals[-1]
        post(
            person,
            f"housing-groups/{group.id}/approve_costs/",
            command(
                group.revision,
                action="approve_costs",
                roster_revision=group.roster_revision,
                item_id=proposal["id"],
                item_revision=proposal["revision"],
                consent=True,
            ),
        )
        group.refresh_from_db()
    lab = read(admin, lab)
    lab = post(
        admin,
        f"living-labs/{lab['id']}/prepare-application/",
        command(
            lab["revision"],
            expected_group_revision=lab["group_revision"],
            agreement_id=lab["agreements"][0]["id"],
        ),
    ).data["resource"]
    process = group.processes.get()
    assert (
        str(process.id) == lab["handoff_application_id"]
        and process.consented_ids == []
        and process.status == "collecting_consent"
    )
    source = HousingRequest.objects.create(
        user=admin,
        title="Reviewed demand",
        expires_at=timezone.now() + timedelta(days=10),
        criteria={},
    )
    lab = post(
        admin,
        f"living-labs/{lab['id']}/prepare-tender/",
        command(
            lab["revision"],
            expected_group_revision=lab["group_revision"],
            agreement_id=lab["agreements"][0]["id"],
            request_id=str(source.id),
            request_revision=source.revision,
            closes_at=(timezone.now() + timedelta(days=7)).isoformat(),
        ),
    ).data["resource"]
    from core_apps.features.advanced_tender_models import HousingTender

    tender = HousingTender.objects.get(id=lab["handoff_tender_id"])
    assert tender.source_context["agreement_id"] == lab["agreements"][0]["id"]
    assert tender.requirements.count() == 0
    assert Lease.objects.count() == 0


@pytest.mark.django_db
def test_privacy_withdrawal_capability_is_scoped_to_the_exact_historical_resource(
    context, settings
):
    owner, admin, _, _, _, _ = context
    lab = create_lab(context)
    settings.ADVANCED_HOUSING_ENABLED_SERVICES = []
    query = f"planning-capabilities/?capability=shared_living_lab&action=withdraw&subject_id={lab['id']}"
    response = authenticated(admin).get(API + query)
    assert response.status_code == 200, response.data
    assert response.data["privacy_actions"] == ["withdraw"]
    assert response.data["privacy_subject_id"] == lab["id"]
    assert "shared_living_lab" not in response.data["enabled_capabilities"]
    outsider = authenticated(owner).get(API + query)
    assert outsider.data["privacy_actions"] == []
    other = authenticated(admin).get(
        API + query.replace("action=withdraw", "action=run")
    )
    assert other.data["privacy_actions"] == []
    post(admin, f"living-labs/{lab['id']}/runs/", command(lab["revision"]), 403)


@pytest.mark.django_db
def test_private_retention_scrubs_disclosure_receipts_before_output_expiry_and_preserves_closed_state(
    context, settings
):
    _, admin, _, _, _, rooms = context
    settings.LIVING_LAB_PRIVATE_RETENTION_DAYS = 1
    lab = calculate(
        admin, submit_v2(admin, create_lab(context), preferred_room_id=rooms[0]["id"])
    )
    mine = (
        authenticated(admin).get(API + f"living-labs/{lab['id']}/my-requirements/").data
    )
    body = command(
        lab["revision"],
        public_revision=lab["public_revision"],
        requirement_revision=mine["requirement_revision"],
        fields=["preferred_room_id"],
        consent=True,
    )
    lab = post(admin, f"living-labs/{lab['id']}/disclosures/", body).data["resource"]
    model = SharedLivingLab.objects.get(id=lab["id"])
    assert model.runs.get().input_digest
    model.status = "closed"
    model.save()
    model.requirements.update(updated_at=timezone.now() - timedelta(days=2))
    assert purge_lab(model.pk)
    model.refresh_from_db()
    assert model.status == "closed"
    assert model.runs.get().input_digest == ""
    row = model.requirements.get()
    assert row.private_values == {} and row.purpose_version == "living-lab-private-v1"
    assert row.consented_at is not None
    record = IdempotencyRecord.objects.get(user=admin, request_key=body["request_key"])
    assert record.response_data["resource"]["disclosures"] == []
    assert record.response_data["resource"]["my_disclosure_fields"] == []
    assert record.recovery_status == "confirmed"


@pytest.mark.django_db
def test_changed_quote_requires_fresh_exact_selection_and_preserves_previous_agreement(
    context,
):
    _, admin, member, prop, group, _ = context
    original = respond(member, respond(admin, ready(context)))
    snapshot = copy.deepcopy(original["agreements"][0]["snapshot"])
    prop.rental_inventory["offers"][0]["revision"] += 1
    prop.rental_inventory["offers"][0]["terms"]["price"] = "120.03"
    prop.save()
    changed = read(admin, original)
    assert changed["current_selection"]["offer_revision"] == 3
    path = f"living-labs/{original['id']}/scenario-runs/"
    body = command(
        original["revision"],
        kind="quote_change",
        expected_group_revision=group.revision,
        agreement_id=original["agreements"][0]["id"],
    )
    post(admin, path, {**body, "selection": original["selection"]}, 409)
    child = post(admin, path, {**body, "selection": changed["current_selection"]}).data[
        "resource"
    ]
    assert child["selection"]["terms"]["price"] == "120.03"
    assert child["ready_count"] == 0 and child["agreements"] == []
    child = calculate(admin, submit_v2(member, submit_v2(admin, child)))
    assert child["latest_run"]["candidates"][0]["rent_total"]["amount_minor"] == 12003
    assert child["previous_arrangement"] == snapshot
    assert (
        SharedArrangementSnapshot.objects.get(
            id=original["agreements"][0]["id"]
        ).snapshot
        == snapshot
    )


@pytest.mark.django_db
def test_changed_roster_scenario_never_copies_older_private_group_context(context):
    owner, admin, member, prop, group, _ = context
    prop.rental_inventory["offers"][0]["capacity"] = 3
    prop.save()
    group.shortlist[0]["selection"]["capacity"] = 3
    group.save()
    original = respond(member, respond(admin, ready(context)))
    group.capacity = 3
    group.revision += 1
    group.roster_revision += 1
    group.save()
    GroupMembership.objects.create(
        group=group, user=owner, joined_revision=group.revision
    )
    # A coordinator cannot evade new-member isolation by choosing a different label.
    child = post(
        admin,
        f"living-labs/{original['id']}/scenario-runs/",
        command(
            original["revision"],
            kind="amendment",
            expected_group_revision=group.revision,
            agreement_id=original["agreements"][0]["id"],
        ),
    ).data["resource"]
    visible = read(owner, child)
    assert visible["previous_arrangement"] is None
    assert visible["household_plan"] == {} and visible["house_rules"] == []
    assert visible["ready_count"] == 0 and visible["disclosures"] == []
    assert visible["title"] == group.name
    assert (
        authenticated(owner).get(API + f"living-labs/{original['id']}/").status_code
        == 404
    )


@pytest.mark.django_db
def test_vacancy_uses_exact_room_identity_and_expiry_never_creates_obligations(context):
    _, admin, member, _, group, rooms = context
    original = ready(context)
    child = post(
        admin,
        f"living-labs/{original['id']}/scenario-runs/",
        command(
            original["revision"],
            kind="room_unavailable",
            expected_group_revision=group.revision,
            unavailable_room_ids=[rooms[0]["id"]],
        ),
    ).data["resource"]
    child = calculate(admin, submit_v2(member, submit_v2(admin, child)))
    assert child["latest_run"]["outcome"] == "infeasible"
    assert child["scenario"]["unavailable_room_ids"] == [rooms[0]["id"]]
    SharedLivingLab.objects.filter(id=child["id"]).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    expired = read(admin, child)
    assert expired["status"] == "expired"
    assert "run" not in expired["allowed_actions"]
    post(admin, f"living-labs/{child['id']}/runs/", command(child["revision"]), 403)
    post(admin, f"living-labs/{child['id']}/withdraw/", command(child["revision"]))
    assert Lease.objects.count() == 0

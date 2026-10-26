import copy
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections

from core_apps.features.decision_models import (
    DecisionNotebook, DecisionNotebookConflict, DecisionNotebookVersion,
)
from core_apps.features.services.decision_notebooks import empty
from .test_rental_phase2 import authenticated, rental_participants
from .test_company_housing import company_setup
from .test_rental_lifecycle import policy

API = "/api/v1/features/v1/decision-notebook/"


def note(text="first", **fields):
    return {"property_id": "property-a", "offer_id": "bed-a", "title": "A",
            "note": text, "list": "", "checked_items": [], **fields}


def content(*notes):
    return {**empty(), "properties": list(notes)}


def sync(user, value, revision=0, key=None, workspace="individual", company=""):
    query = f"?workspace={workspace}" + (f"&company_id={company}" if company else "")
    return authenticated(user).post(API + query, {
        "operation_id": key or str(uuid.uuid4()), "base_revision": revision, "content": value,
    }, format="json")


@pytest.mark.django_db
def test_independent_changes_merge_and_conflicting_text_keeps_both(rental_participants):
    user = rental_participants[1]
    assert sync(user, content(note())).status_code == 200
    assert sync(user, content(note("device A")), 1).status_code == 200
    value = sync(user, content(note(list="shortlist")), 1).json()["data"]
    assert value["content"]["properties"][0]["note"] == "device A"
    assert value["content"]["properties"][0]["list"] == "shortlist"
    assert not value["conflicts"]
    value = sync(user, content(note("device B")), 1).json()["data"]
    assert value["content"]["properties"][0]["note"] == "device A"
    conflict = value["conflicts"][0]
    assert conflict["current"]["note"] == "device A"
    assert conflict["incoming"]["note"] == "device B"
    assert conflict["base"]["note"] == "first"
    assert conflict["fields"] == ["note"]


@pytest.mark.django_db
def test_offline_additions_and_exact_bed_identity_merge(rental_participants):
    user = rental_participants[1]
    sync(user, content(note("one")))
    value = sync(user, content(note("two", offer_id="bed-b"))).json()["data"]
    assert {row["offer_id"] for row in value["content"]["properties"]} == {"bed-a", "bed-b"}
    assert not value["conflicts"]


@pytest.mark.django_db
@pytest.mark.parametrize("base", [0, 1])
def test_old_sync_cannot_revive_deleted_note_even_without_old_record(base, rental_participants):
    user = rental_participants[1]
    sync(user, content(note()))
    sync(user, empty(), 1)
    value = sync(user, content(note("offline edit")), base).json()["data"]
    assert value["content"]["properties"] == []
    assert value["conflicts"][0]["incoming"]["note"] == "offline edit"
    assert value["conflicts"][0]["fields"] == ["deleted"]


@pytest.mark.django_db
def test_delete_wins_over_concurrent_edit_and_preserves_edit_copy(rental_participants):
    user = rental_participants[1]
    sync(user, content(note()))
    sync(user, content(note("changed")), 1)
    value = sync(user, empty(), 1).json()["data"]
    assert not value["content"]["properties"]
    assert value["conflicts"][0]["current"]["note"] == "changed"


@pytest.mark.django_db
def test_operation_recovery_does_not_duplicate_and_payload_change_is_rejected(rental_participants):
    user = rental_participants[1]
    key = str(uuid.uuid4())
    first = sync(user, content(note()), key=key).json()["data"]
    recovered = sync(user, content(note()), key=key).json()["data"]
    assert recovered == first
    assert DecisionNotebookVersion.objects.count() == 1
    assert sync(user, content(note("different")), key=key).status_code == 409


@pytest.mark.django_db
def test_private_account_and_workspace_and_staff_cannot_read_another_account(rental_participants):
    owner, user, other, *_ = rental_participants
    sync(user, content(note("private")))
    sync(user, content(note("student")), workspace="student")
    owner.is_superuser = owner.is_staff = True
    owner.save(update_fields=["is_superuser", "is_staff"])
    for actor in (owner, other):
        response = authenticated(actor).get(API, {"workspace": "individual", "user_id": str(user.pk)})
        assert response.json()["data"]["content"] == empty()
        assert response["Cache-Control"] == "private, no-store"
    assert authenticated(user).get(API, {"workspace": "student"}).json()["data"]["content"]["properties"][0]["note"] == "student"
    assert sync(user, content(note()), workspace="company", company=uuid.uuid4()).status_code == 404


@pytest.mark.django_db
def test_conflict_resolution_is_versioned_and_old_copies_remain(rental_participants):
    user = rental_participants[1]
    sync(user, content(note()))
    sync(user, content(note("A")), 1)
    value = sync(user, content(note("B")), 1).json()["data"]
    body = {"operation_id": str(uuid.uuid4()), "base_revision": 2,
            "conflict_id": value["conflicts"][0]["id"], "resolution": "incoming"}
    client = authenticated(user)
    assert client.post(API + "resolve/?workspace=individual", body, format="json").status_code == 409
    body["base_revision"] = value["revision"]
    response = client.post(API + "resolve/?workspace=individual", body, format="json")
    assert response.status_code == 200
    result = response.json()["data"]
    assert result["content"]["properties"][0]["note"] == "B"
    assert result["conflicts"][0]["resolved"]
    assert result["conflicts"][0]["current"]["note"] == "A"
    assert client.post(API + "resolve/?workspace=individual", body, format="json").json()["data"] == result


@pytest.mark.django_db
def test_unknown_revision_invalid_shape_and_suspension(rental_participants):
    user = rental_participants[1]
    assert sync(user, content(note()), revision=100).status_code == 409
    assert sync(user, {**empty(), "properties": [note(3)]}).status_code == 400
    assert sync(user, content(note(), note())).status_code == 400
    user.is_active = False
    user.save(update_fields=["is_active"])
    assert sync(user, content(note())).status_code == 403
    assert not DecisionNotebook.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_two_devices_sync_concurrently_without_losing_either_entry(rental_participants):
    user = rental_participants[1]
    gate = Barrier(2)

    def device(offer):
        close_old_connections()
        try:
            gate.wait(timeout=10)
            return sync(user, content(note(offer_id=offer))).status_code
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(device, ["bed-a", "bed-b"])) == [200, 200]
    notebook = DecisionNotebook.objects.get(user=user)
    assert notebook.revision == 2
    assert len(notebook.content["properties"]) == 2
    assert not DecisionNotebookConflict.objects.exists()


@pytest.mark.django_db
def test_company_context_is_private_even_to_other_members_and_revocation_is_current(company_setup):
    from core_apps.features.company_models import CompanyMembership
    _, user, other, company, *_ = company_setup
    assert sync(user, content(note("private company thought")), workspace="company", company=company.id).status_code == 200
    query = {"workspace": "company", "company_id": str(company.id)}
    assert authenticated(other).get(API, query).json()["data"]["content"] == empty()
    CompanyMembership.objects.filter(company=company, user=user).update(is_active=False)
    assert authenticated(user).get(API, query).status_code == 404
    assert sync(user, content(note()), workspace="company", company=company.id).status_code == 404


@pytest.mark.django_db
def test_resolution_preserves_independent_fields_and_cannot_revive_later_deletion(rental_participants):
    user = rental_participants[1]
    sync(user, content(note()))
    sync(user, content(note("A", list="keep this list")), 1)
    value = sync(user, content(note("B")), 1).json()["data"]
    conflict_id = value["conflicts"][0]["id"]
    client = authenticated(user)
    response = client.post(API + "resolve/?workspace=individual", {
        "operation_id": str(uuid.uuid4()), "base_revision": value["revision"],
        "conflict_id": conflict_id, "resolution": "incoming",
    }, format="json")
    assert response.status_code == 200
    row = response.json()["data"]["content"]["properties"][0]
    assert row["note"] == "B" and row["list"] == "keep this list"
    value = sync(user, content(note("C")), 1).json()["data"]
    conflict_id = value["conflicts"][-1]["id"]
    deleted = sync(user, empty(), value["revision"]).json()["data"]
    assert client.post(API + "resolve/?workspace=individual", {
        "operation_id": str(uuid.uuid4()), "base_revision": deleted["revision"],
        "conflict_id": conflict_id, "resolution": "incoming",
    }, format="json").status_code == 409
    assert not DecisionNotebook.objects.get(user=user).content["properties"]


def test_staff_admin_has_no_notebook_or_conflict_reader():
    from django.contrib import admin
    assert not admin.site.is_registered(DecisionNotebook)
    assert not admin.site.is_registered(DecisionNotebookConflict)

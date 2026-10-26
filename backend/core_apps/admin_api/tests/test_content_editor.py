import uuid
from concurrent.futures import ThreadPoolExecutor
import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from django.urls import reverse
from rest_framework.test import APIClient
from core_apps.admin_api.models import StaffProfile
from core_apps.common.content_models import ContentEditAudit, ReleaseNote
from core_apps.support.models import HelpArticle, HelpContact

pytestmark = pytest.mark.django_db
ROOT = "/api/v1/admin/content/"


def operator(name="editor"):
    user = get_user_model().objects.create_user(
        email=f"{name}@example.test", password="local-only"
    )
    StaffProfile.objects.create(user=user, role_name="system_owner")
    return user


def client(user):
    result = APIClient()
    result.force_authenticate(user)
    return result


def article(slug="content-proof", **changes):
    return dict(
        slug=slug,
        workspace="student",
        question_ar="سؤال خاص بالطلاب",
        question_en="Student question",
        answer_ar="إجابة محفوظة",
        answer_en="Stored answer",
        sort_order=2,
        active=True,
        **changes,
    )


def save(api, kind, values, revision=0, identity=None, key=None):
    key = key or str(uuid.uuid4())
    body = dict(
        expected_revision=revision, reason="Verified content update", values=values
    )
    url = ROOT + kind + "/" + (f"{identity}/" if identity else "")
    return api.post(url, body, format="json", HTTP_IDEMPOTENCY_KEY=key), key


def test_shared_content_edit_revision_audit_and_public_workspace(api_client):
    editor = operator()
    api = client(editor)
    response, key = save(api, "articles", article())
    assert response.status_code == 201, response.data
    value = response.data
    assert value["revision"] == 1 and value["id"] == "content-proof"
    assert ContentEditAudit.objects.get().after == value
    repeated, _ = save(api, "articles", article(), key=key)
    assert repeated.status_code == 201 and repeated.data == value
    recovery = api.post(
        ROOT + f"articles/receipts/{key}/", {"identity": None}, format="json"
    )
    assert recovery.data["status"] == "confirmed" and recovery.data["receipt"] == value
    public = reverse("support-help-center")
    for workspace in ["tenant", "individual", "owner", "company"]:
        response = api_client.get(public, {"workspace": workspace, "lang": "ar"})
        assert response.status_code == 200, response.data
        assert "content-proof" not in [row["id"] for row in response.data["faqs"]]
    assert (
        api_client.get(public, {"workspace": "student", "lang": "ar"}).data["faqs"][0][
            "answer"
        ]
        == "إجابة محفوظة"
    )
    updated, _ = save(api, "articles", {"answer_ar": "إجابة محدثة"}, 1, "content-proof")
    assert updated.status_code == 200 and updated.data["revision"] == 2
    stale, _ = save(api, "articles", {"answer_ar": "نص قديم"}, 1, "content-proof")
    assert stale.status_code == 409
    detail = api.get(ROOT + "articles/content-proof/").data
    assert len(detail["history"]) == 2
    assert detail["history"][0]["before"]["values"]["answer_ar"] == "إجابة محفوظة"
    assert (
        api_client.get(public, {"workspace": "student", "lang": "ar"}).data["faqs"][0][
            "answer"
        ]
        == "إجابة محدثة"
    )
    inactive, _ = save(api, "articles", {"active": False}, 2, "content-proof")
    assert inactive.status_code == 200
    assert "content-proof" not in [
        row["id"]
        for row in api_client.get(public, {"workspace": "student"}).data["faqs"]
    ]
    active, _ = save(api, "articles", {"active": True}, 3, "content-proof")
    assert (
        active.status_code == 200
        and HelpArticle.objects.get(pk="content-proof").revision == 4
    )


def test_content_recovery_absence_fences_delayed_writes_and_role_revocation():
    editor = operator()
    api = client(editor)
    key = str(uuid.uuid4())
    assert (
        api.post(
            ROOT + f"articles/receipts/{key}/", {"identity": None}, format="json"
        ).data["status"]
        == "absent_final"
    )
    late, _ = save(api, "articles", article(), key=key)
    assert (
        late.status_code == 409
        and not HelpArticle.objects.filter(pk="content-proof").exists()
    )
    response, key = save(api, "articles", article())
    assert response.status_code == 201
    StaffProfile.objects.filter(user=editor).update(is_active=False)
    assert api.get(ROOT).status_code == 403
    assert (
        api.post(
            ROOT + f"articles/receipts/{key}/", {"identity": None}, format="json"
        ).status_code
        == 403
    )
    assert save(api, "articles", article(), key=key)[0].status_code == 403


def test_content_allowlist_fixed_identity_and_validation(user):
    assert client(user).get(ROOT).status_code == 403
    api = client(operator())
    assert api.post(ROOT, {}, format="json").status_code == 405
    assert api.get(ROOT + "releases/not-an-id/").status_code == 404
    assert (
        api.post(
            ROOT + f"articles/receipts/{uuid.uuid4()}/", [], format="json"
        ).status_code
        == 400
    )
    assert api.get(ROOT + "permissions/").status_code == 404
    assert api.get(ROOT + "articles/?page=not-a-page").status_code == 404
    invalid = article()
    invalid["financial_approver"] = True
    assert save(api, "articles", invalid)[0].status_code == 400
    invalid = article()
    invalid["workspace"] = "community"
    assert save(api, "articles", invalid)[0].status_code == 400
    assert save(api, "articles", article())[0].status_code == 201
    assert (
        save(api, "articles", {"slug": "another-id"}, 1, "content-proof")[0].status_code
        == 400
    )
    assert (
        save(api, "articles", {"answer_ar": "  "}, 1, "content-proof")[0].status_code
        == 400
    )
    assert api.delete(ROOT + "articles/content-proof/").status_code == 405
    assert HelpArticle.objects.get(pk="content-proof").revision == 1


def test_restricted_staff_can_read_and_recover_but_cannot_edit():
    editor = operator()
    api = client(editor)
    created, key = save(api, "articles", article())
    assert created.status_code == 201
    editor.sensitive_actions_frozen = True
    editor.save(update_fields=["sensitive_actions_frozen"])
    response = api.get(ROOT)
    assert response.status_code == 200 and response.data["can_edit"] is False
    assert response.data["blocking_reason"]
    assert api.get(ROOT + "articles/content-proof/").status_code == 200
    assert (
        api.post(
            ROOT + f"articles/receipts/{key}/", {"identity": None}, format="json"
        ).data["status"]
        == "confirmed"
    )
    assert (
        save(api, "articles", {"active": False}, 1, "content-proof")[0].status_code
        == 403
    )
    assert HelpArticle.objects.get(pk="content-proof").active


def test_contact_and_release_audience_is_current_and_not_legacy_both(api_client):
    api = client(operator())
    values = dict(
        workspace="company",
        email="company@example.test",
        hours_ar="ساعات الشركة",
        hours_en="Company hours",
        active=True,
    )
    assert save(api, "contacts", values)[0].status_code == 201
    public = reverse("support-help-center")
    assert (
        api_client.get(public, {"workspace": "company", "lang": "en"}).data["email"]
        == values["email"]
    )
    assert api_client.get(public, {"workspace": "student"}).data["email"] == ""
    assert api_client.get(public, {"workspace": "community"}).status_code == 400
    for workspace in ["both", "student", "company"]:
        result, _ = save(
            api,
            "releases",
            dict(
                version="9.8.7",
                workspace=workspace,
                items_ar=workspace,
                items_en=workspace,
                publish_at=None,
                active=True,
            ),
        )
        assert result.status_code == 201, result.data
    for workspace, expected in [
        ("tenant", "both"),
        ("individual", "both"),
        ("owner", "both"),
        ("student", "student"),
        ("company", "company"),
    ]:
        response = api_client.get(
            reverse("release-notes"), {"version": "9.8.7", "workspace": workspace}
        )
        assert response.status_code == 200 and response.data["items"] == [expected]
        assert response.data["workspace"] == workspace
    ReleaseNote.objects.filter(version="9.8.7", workspace="student").delete()
    assert (
        api_client.get(
            reverse("release-notes"), {"version": "9.8.7", "workspace": "student"}
        ).data["items"]
        == []
    )


@pytest.mark.django_db(transaction=True)
def test_two_editors_cannot_overwrite_one_revision():
    first, second = operator("first-content"), operator("second-content")
    HelpArticle.objects.create(**article())

    def run(user):
        connections.close_all()
        try:
            return save(
                client(user),
                "articles",
                {"answer_ar": str(user.id)},
                1,
                "content-proof",
            )[0].status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(run, [first, second])) == [200, 409]
    assert HelpArticle.objects.get(pk="content-proof").revision == 2
    assert ContentEditAudit.objects.count() == 1

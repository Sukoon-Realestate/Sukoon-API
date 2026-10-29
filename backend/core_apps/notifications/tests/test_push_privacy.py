import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from core_apps.features.services.company.role_notifications import push_content
from core_apps.notifications.services.fcm_service import FCMService
from core_apps.notifications.services.push_privacy import PUSH_TITLE, PUSH_BODY


def test_native_payload_excludes_private_copy_and_arbitrary_metadata():
    credentials = MagicMock(valid=True, token="synthetic-token")
    with patch("requests.post", return_value=MagicMock(status_code=200)) as post:
        assert FCMService.send_push_to_device(
            token="synthetic-device",
            title="Private tenant name",
            body="Private dispute detail",
            data={
                "action_type": "open_support_ticket",
                "target_id": "ticket-id",
                "workspace": "tenant",
                "body": "Private dispute detail",
                "sender_name": "Private tenant name",
                "evidence_url": "https://private.invalid/?token=secret",
                "financial_limits": {"amount": 99},
            },
            credentials=credentials,
            project_id="synthetic-project",
        )
    payload = post.call_args.kwargs["json"]["message"]
    assert payload["notification"] == {
        "title": "سكون",
        "body": "لديك تحديث جديد. افتح التطبيق لعرضه.",
    }
    assert payload["data"] == {
        "action_type": "open_support_ticket",
        "target_id": "ticket-id",
        "workspace": "tenant",
        "presentation_workspace": "individual",
    }
    assert "Private" not in str(payload) and "secret" not in str(payload)


def test_explicit_recipient_workspace_precedes_company_action_name():
    from core_apps.notifications.services.push_privacy import presentation_context

    assert (
        presentation_context(
            {"action_type": "open_company_booking", "workspace": "owner"}
        )["presentation_workspace"]
        == "owner"
    )
    assert (
        presentation_context(
            {"action_type": "open_company_booking", "workspace": "student"}
        )["presentation_workspace"]
        == "student"
    )


def test_account_event_cannot_switch_workspace():
    from core_apps.notifications.services.push_privacy import routing_data

    data = routing_data(
        {
            "scope": "account",
            "workspace": "company",
            "presentation_workspace": "owner",
            "action_type": "open_account_security",
        }
    )
    assert data["scope"] == "account"
    assert "workspace" not in data and "presentation_workspace" not in data


@pytest.mark.parametrize(
    "role", ["admin", "coordinator", "approver", "signer", "payer", "employee"]
)
@pytest.mark.parametrize("language", ["ar", "en"])
@pytest.mark.parametrize("device_type", ["android", "ios"])
def test_company_role_reaches_final_fcm_payload_without_private_content(
    role, language, device_type
):
    notice = SimpleNamespace(
        scope="company",
        title="Private company employee name",
        body="Private contract requires payment of 892117",
        data={
            "action_type": "open_company_tenancy",
            "target_id": "synthetic-tenancy-id",
            "company_id": "synthetic-company-id",
            "company_role": role,
            "schema_version": 1,
            "workspace": "company",
            "notification_id": "synthetic-notification-id",
            "event_id": "synthetic-event-id",
            "amount_minor": 892117,
            "financial_limits": {"amount_minor": 892117},
            "contract": "Private contract terms",
            "contract_token": "private-contract-token",
            "document_url": "https://private.invalid/?token=private-contract-token",
            "employee_name": "Private company employee name",
        },
    )
    # Exercise both production privacy boundaries, including the final FCM
    # serialization that previously removed the role preserved by push_content.
    title, body, data = push_content(notice)
    credentials = MagicMock(valid=True, token="synthetic-token")
    with patch(
        "core_apps.notifications.services.fcm_service.requests.post",
        return_value=MagicMock(status_code=200),
    ) as post:
        assert FCMService.send_push_to_device(
            token="synthetic-device",
            title=title,
            body=body,
            data=data,
            credentials=credentials,
            project_id="synthetic-project",
            language=language,
            device_type=device_type,
        )

    post.assert_called_once()
    credentials.refresh.assert_not_called()
    payload = post.call_args.kwargs["json"]["message"]
    assert payload["data"] == {
        "action_type": "open_company_tenancy",
        "target_id": "synthetic-tenancy-id",
        "company_id": "synthetic-company-id",
        "company_role": role,
        "schema_version": "1",
        "workspace": "company",
        "presentation_workspace": "company",
        "notification_id": "synthetic-notification-id",
        "event_id": "synthetic-event-id",
    }
    assert payload["notification"] == {
        "title": "سكون" if language == "ar" else "Sokoun",
        "body": (
            "لديك تحديث جديد. افتح التطبيق لعرضه."
            if language == "ar"
            else "Open Sokoun to view your update."
        ),
    }
    serialized = json.dumps(payload)
    assert all(
        private not in serialized
        for private in (
            "Private",
            "892117",
            "private-contract-token",
            "private.invalid",
        )
    )
    assert notice.data["company_role"] == role
    assert notice.data["amount_minor"] == 892117


@pytest.mark.parametrize(
    "role_metadata", [{"contract_token": "private-token"}, ["private-token"]]
)
def test_company_role_cannot_carry_structured_private_metadata(role_metadata):
    with patch(
        "core_apps.notifications.services.fcm_service.requests.post",
        return_value=MagicMock(status_code=200),
    ) as post:
        assert FCMService.send_push_to_device(
            token="synthetic-device",
            title="Private title",
            body="Private contract",
            data={"company_id": "synthetic-company-id", "company_role": role_metadata},
            credentials=MagicMock(valid=True, token="synthetic-token"),
            project_id="synthetic-project",
        )
    payload = post.call_args.kwargs["json"]["message"]
    assert payload["data"] == {"company_id": "synthetic-company-id"}
    assert "private-token" not in json.dumps(payload)


@pytest.mark.parametrize(
    "scope,data,expected,title",
    [
        (
            "owner",
            {
                "action_type": "open_company_tenancy",
                "workspace": "owner",
                "company_id": "company-id",
            },
            {
                "action_type": "open_company_tenancy",
                "workspace": "owner",
                "company_id": "company-id",
                "presentation_workspace": "owner",
            },
            "Sokoun",
        ),
        (
            "student",
            {
                "action_type": "open_student_plan",
                "student_plan_id": "plan-id",
                "target_id": "plan-id",
            },
            {
                "action_type": "open_student_plan",
                "target_id": "plan-id",
                "presentation_workspace": "student",
            },
            "Sokoun",
        ),
        (
            "account",
            {
                "scope": "account",
                "action_type": "open_account_security",
                "workspace": "company",
                "presentation_workspace": "owner",
            },
            {"scope": "account", "action_type": "open_account_security"},
            "Sokoun — Account update",
        ),
        (
            "company",
            {
                "action_type": "open_company_tenancy",
                "workspace": "company",
                "company_id": "company-id",
            },
            {
                "action_type": "open_company_tenancy",
                "workspace": "company",
                "company_id": "company-id",
                "presentation_workspace": "company",
            },
            "Sokoun",
        ),
    ],
    ids=[
        "owner-authority",
        "student-workspace",
        "account-scope",
        "legacy-company-no-role",
    ],
)
def test_other_fcm_routes_preserve_scope_without_inventing_a_company_role(
    scope, data, expected, title
):
    private_data = {
        **data,
        "contract_token": "private-contract-token",
        "amount_minor": 892117,
    }
    push_title, push_body, push_data = push_content(
        SimpleNamespace(
            scope=scope, title="Private title", body="Private body", data=private_data
        )
    )
    with patch(
        "core_apps.notifications.services.fcm_service.requests.post",
        return_value=MagicMock(status_code=200),
    ) as post:
        assert FCMService.send_push_to_device(
            token="synthetic-device",
            title=push_title,
            body=push_body,
            data=push_data,
            credentials=MagicMock(valid=True, token="synthetic-token"),
            project_id="synthetic-project",
            language="en",
        )
    payload = post.call_args.kwargs["json"]["message"]
    assert payload["data"] == expected
    assert payload["notification"] == {
        "title": title,
        "body": "Open Sokoun to view your update.",
    }
    assert "company_role" not in payload["data"]
    assert all(
        private not in json.dumps(payload)
        for private in ("Private", "private-contract-token", "892117")
    )

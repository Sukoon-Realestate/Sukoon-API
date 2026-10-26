from unittest.mock import MagicMock, patch
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

import pytest
from django.test import override_settings
from django.urls import reverse


@pytest.mark.django_db
def test_app_associations_are_unavailable_without_release_identities(api_client):
    android = api_client.get(reverse("android-asset-links"))
    apple = api_client.get(reverse("apple-app-site-association"))

    assert android.status_code == 503
    assert apple.status_code == 503
    assert android.headers["Cache-Control"] == "no-store"


@pytest.mark.django_db
@override_settings(
    SOKOUN_ANDROID_APP_LINKS={
        "com.app.sokoon.real.estate": ["AA:BB"],
        "com.app.sokoon.real.estate.dev": ["CC:DD"],
    },
    SOKOUN_APPLE_TEAM_ID="TEAM123456",
    SOKOUN_APPLE_BUNDLE_IDS=[
        "com.app.sokoon.real.estate",
        "com.app.sokoon.real.estate.dev",
    ],
)
def test_app_associations_use_configured_release_identities(api_client):
    android = api_client.get(reverse("android-asset-links"))
    apple = api_client.get(reverse("apple-app-site-association"))

    assert android.status_code == 200
    assert android.json()[0]["relation"] == [
        "delegate_permission/common.handle_all_urls"
    ]
    assert {
        item["target"]["package_name"] for item in android.json()
    } == {
        "com.app.sokoon.real.estate",
        "com.app.sokoon.real.estate.dev",
    }
    assert apple.status_code == 200
    assert apple.json()["applinks"]["details"] == [
        {
            "appID": "TEAM123456.com.app.sokoon.real.estate",
            "paths": ["/properties/*"],
        },
        {
            "appID": "TEAM123456.com.app.sokoon.real.estate.dev",
            "paths": ["/properties/*"],
        },
    ]

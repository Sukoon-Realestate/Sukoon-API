import base64
import io
from unittest.mock import Mock, patch
import pytest
from PIL import Image
from cloudinary import CloudinaryResource
from django.urls import reverse
from rest_framework.test import APIClient
from core_apps.admin_api.models import KYCSubmission, StaffProfile
from core_apps.common.idempotency import fingerprint
from core_apps.profiles.identity_media import version
from core_apps.profiles.models import Profile
from core_apps.users.models import User
from core_apps.users.services.identity_submission import evidence_snapshot

pytestmark = pytest.mark.django_db


def actor(name, **values):
    user = User.objects.create_user(
        email=name + "@example.invalid", password="LocalOnly123!", **values
    )
    client = APIClient()
    client.force_authenticate(user)
    return user, client


def protected(user):
    profile = user.profile
    profile.id_face = CloudinaryResource(
        public_id="qa-proof",
        type="authenticated",
        resource_type="image",
        format="png",
        version=1,
    )
    profile.save()
    return profile


def test_identity_urls_are_private_and_account_bound():
    owner, client = actor("proof-owner")
    _, stranger = actor("proof-stranger")
    profile = protected(owner)
    response = client.get(reverse("profile-detail"))
    url = response.json()["data"]["id_face"]
    assert "/identity-media/id_face/?version=" in url
    assert "cloudinary" not in url
    with patch("core_apps.profiles.identity_media.requests.get") as provider:
        assert APIClient().get(url).status_code == 401
        assert stranger.get(url).status_code == 404
        assert (
            client.get(
                reverse("identity-media", kwargs={"field": "avatar"})
            ).status_code
            == 404
        )
        assert (
            client.get(url.replace(version(profile.id_face), "0" * 64)).status_code
            == 404
        )
        provider.assert_not_called()


def test_authorized_proxy_never_returns_provider_url_and_disables_cache():
    owner, client = actor("proof-reader")
    profile = protected(owner)
    response = Mock(status_code=200, headers={"Content-Type": "image/png"})
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.iter_content.return_value = [b"protected-test-bytes"]
    with patch(
        "core_apps.profiles.identity_media.private_download_url",
        return_value="https://provider.invalid/private",
    ) as signed, patch(
        "core_apps.profiles.identity_media.requests.get", return_value=response
    ) as provider:
        result = client.get(
            reverse("identity-media", kwargs={"field": "id_face"}),
            {"version": version(profile.id_face)},
        )
    assert result.status_code == 200 and result.content == b"protected-test-bytes"
    assert (
        "private" in result["Cache-Control"] and "no-store" in result["Cache-Control"]
    )
    assert "Location" not in result
    assert signed.call_args.kwargs["type"] == "authenticated"
    assert provider.call_args.kwargs["allow_redirects"] is False


def test_public_legacy_assets_are_not_served_or_redisclosed():
    owner, client = actor("legacy-proof")
    profile = owner.profile
    profile.id_face = CloudinaryResource(
        public_id="legacy", type="upload", resource_type="image", format="png"
    )
    profile.save()
    assert client.get(reverse("profile-detail")).json()["data"]["id_face"] is None
    assert client.get(reverse("profile-update")).json()["data"]["id_face"] is None
    with patch("core_apps.profiles.identity_media.requests.get") as provider:
        assert (
            client.get(
                reverse("identity-media", kwargs={"field": "id_face"}),
                {"version": version(profile.id_face)},
            ).status_code
            == 404
        )
        provider.assert_not_called()


def test_kyc_media_requires_current_identity_reviewer_role():
    owner, _ = actor("evidence-subject")
    profile = protected(owner)
    snapshot = evidence_snapshot(profile)
    submission = KYCSubmission.objects.create(
        profile=profile,
        evidence_snapshot=snapshot,
        evidence_digest=fingerprint(snapshot),
    )
    reviewer, client = actor("evidence-reviewer")
    staff = StaffProfile.objects.create(
        user=reviewer, role_name="kyc_reviewer", is_active=True
    )
    url = reverse(
        "admin-kyc-media", kwargs={"submission_id": submission.id, "field": "id_face"}
    )
    detail = client.get(
        reverse("admin-kyc-detail", kwargs={"submission_id": submission.id})
    ).json()["data"]
    assert detail["idFaceUrl"] == url
    staff.is_active = False
    staff.save()
    with patch("core_apps.profiles.identity_media.requests.get") as provider:
        assert client.get(url).status_code == 403
        provider.assert_not_called()
    submission.refresh_from_db()
    assert submission.evidence_snapshot == snapshot


@pytest.mark.parametrize(
    "value", ["https://example.invalid/proof.jpg", "image/upload/v1/borrowed.jpg"]
)
def test_identity_submission_rejects_urls_and_borrowed_asset_ids(value):
    _, client = actor("upload-" + str(len(value)))
    result = client.post(
        reverse("complete-register"), {"front_id_image": value}, format="json"
    )
    assert result.status_code == 400


def test_new_upload_uses_authenticated_provider_type_and_immutable_reference():
    owner, client = actor("new-proof")
    image = io.BytesIO()
    Image.new("RGB", (2, 2), "white").save(image, format="PNG")
    resource = CloudinaryResource(
        public_id="new-proof",
        type="authenticated",
        resource_type="image",
        format="png",
        version=1,
    )
    with patch(
        "cloudinary.models.uploader.upload_resource", return_value=resource
    ) as upload:
        result = client.post(
            reverse("complete-register"),
            {
                "front_id_image": "data:image/png;base64,"
                + base64.b64encode(image.getvalue()).decode()
            },
            format="json",
        )
    assert result.status_code == 200, result.data
    assert upload.call_args.kwargs["type"] == "authenticated"
    owner.profile.refresh_from_db()
    assert (
        evidence_snapshot(owner.profile)["id_face"]
        == "image/authenticated/v1/new-proof.png"
    )
    assert all(
        Profile._meta.get_field(field).type == "authenticated"
        for field in ("id_face", "id_back", "confirmation_selfi")
    )


def test_conversion_reconciles_provider_success_after_lost_response(tmp_path):
    from django.core.management import call_command
    import cloudinary.api
    import json

    owner, _ = actor("conversion")
    profile = owner.profile
    profile.id_face = CloudinaryResource(
        public_id="legacy-proof",
        type="upload",
        resource_type="image",
        format="png",
        version=1,
    )
    profile.save()
    manifest = tmp_path / "conversion.json"
    call_command("protect_identity_media", manifest=str(manifest))
    source = {
        "asset_id": "same-provider-asset",
        "public_id": "legacy-proof",
        "resource_type": "image",
        "type": "upload",
        "format": "png",
        "version": 1,
    }
    target = {**source, "type": "authenticated", "version": 2}
    with patch(
        "cloudinary.api.resource",
        side_effect=[source, cloudinary.api.NotFound("absent")],
    ), patch(
        "cloudinary.uploader.rename", side_effect=TimeoutError("Response lost")
    ) as rename:
        with pytest.raises(TimeoutError):
            call_command("protect_identity_media", manifest=str(manifest), apply=True)
        assert rename.call_count == 1
    profile.refresh_from_db()
    assert profile.id_face.type == "upload"
    with patch("cloudinary.api.resource", return_value=target), patch(
        "cloudinary.uploader.rename"
    ) as rename:
        call_command("protect_identity_media", manifest=str(manifest), apply=True)
        call_command("protect_identity_media", manifest=str(manifest), apply=True)
        rename.assert_not_called()
    profile.refresh_from_db()
    assert profile.id_face.type == "authenticated"
    assert (
        not profile.user.is_verified
    )  # The conversion cannot grant identity approval.
    assert (
        next(iter(json.loads(manifest.read_text())["assets"].values()))["state"]
        == "complete"
    )


def test_conversion_does_not_change_asset_shared_with_public_avatar(tmp_path):
    from django.core.management import call_command
    import json

    owner, _ = actor("shared-proof")
    profile = owner.profile
    asset = CloudinaryResource(
        public_id="shared-public",
        type="upload",
        resource_type="image",
        format="png",
        version=1,
    )
    profile.id_face = asset
    profile.avatar = asset
    profile.save()
    manifest = tmp_path / "conversion.json"
    with patch("cloudinary.uploader.rename") as rename:
        call_command("protect_identity_media", manifest=str(manifest))
        call_command("protect_identity_media", manifest=str(manifest), apply=True)
        rename.assert_not_called()
    assert (
        "also_referenced_outside_identity"
        in next(iter(json.loads(manifest.read_text())["assets"].values()))["blocked"]
    )


def test_deletion_uses_authenticated_provider_namespace():
    from core_apps.users.services.user_service import delete_user_account

    owner, _ = actor("deleted-proof")
    protected(owner)
    with patch("cloudinary.uploader.destroy") as destroy:
        delete_user_account(owner)
    destroy.assert_called_once_with(
        "qa-proof", type="authenticated", resource_type="image", invalidate=True
    )

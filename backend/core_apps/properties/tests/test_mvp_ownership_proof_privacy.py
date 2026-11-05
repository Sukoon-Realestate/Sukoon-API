"""Ownership images are provider-private and read through current resource access."""
import io
from unittest.mock import Mock, patch
from urllib.parse import urlsplit

import cloudinary
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image

from core_apps.admin_api.models import StaffProfile
from core_apps.properties.ownership_proof import proof_url
from .test_parallel_media import owner  # noqa: F401
from .test_discovery_fixes import listing  # noqa: F401

pytestmark = pytest.mark.django_db


def protected(prop):
    prop.ownership_proof = cloudinary.CloudinaryResource(public_id='properties/ownership_proofs/synthetic',
        format='jpg', version=1, type='authenticated', resource_type='image')
    prop.save(update_fields=['ownership_proof'])


def test_ownership_upload_uses_authenticated_storage_and_exposes_no_provider_url(auth_client, owner, listing):
    content = io.BytesIO()
    Image.new('RGB', (100, 100), 'blue').save(content, 'JPEG')
    asset = cloudinary.CloudinaryResource(public_id='properties/ownership_proofs/synthetic',
        format='jpg', version=1, type='authenticated', resource_type='image')
    with patch('cloudinary.uploader.upload_resource', return_value=asset) as upload:
        response = auth_client.patch(reverse('property-detail', kwargs={'id': listing.id}), {
            'ownership_proof': SimpleUploadedFile('proof.jpg', content.getvalue(), content_type='image/jpeg'),
        }, format='multipart')
    assert response.status_code == 200, response.data
    assert upload.call_args.kwargs['type'] == 'authenticated'
    assert upload.call_args.kwargs['resource_type'] == 'image'
    data = response.json()['data']
    assert '/ownership-proof/?version=' in data['ownership_proof']
    assert 'cloudinary' not in data['ownership_proof']
    listing.refresh_from_db()
    assert not listing.is_ownership_verified and listing.status == 'under_review'


def test_ownership_proxy_rechecks_owner_current_staff_role_and_revision(api_client, owner, listing, another_user, superuser):
    protected(listing)
    path = proof_url(listing, owner)
    assert path and not urlsplit(path).netloc
    # The owner and the current property reviewer may read; a generic staff flag cannot.
    assert proof_url(listing, another_user) is None
    another_user.is_staff = True
    another_user.save(update_fields=['is_staff'])
    assert proof_url(listing, another_user) is None
    role = StaffProfile.objects.create(user=another_user, role_name='property_reviewer')
    assert proof_url(listing, another_user)
    role.is_active = False
    role.save(update_fields=['is_active'])
    assert proof_url(listing, another_user) is None
    with patch('core_apps.profiles.identity_media.requests.get') as get:
        api_client.force_authenticate(another_user)
        assert api_client.get(path).status_code == 404
        api_client.force_authenticate(owner)
        assert api_client.get(path.replace('version=', 'version=stale-')).status_code == 404
        get.assert_not_called()


def test_ownership_proxy_returns_private_bytes_instead_of_redirect(api_client, owner, listing):
    protected(listing)
    response = Mock(status_code=200, headers={'Content-Type': 'image/jpeg'})
    response.iter_content.return_value = [b'synthetic-image-content']
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    with patch('core_apps.profiles.identity_media.private_download_url', return_value='https://provider.invalid/private') as signed, patch(
        'core_apps.profiles.identity_media.requests.get', return_value=response,
    ) as get:
        api_client.force_authenticate(owner)
        result = api_client.get(proof_url(listing, owner))
    assert result.status_code == 200 and result.content == b'synthetic-image-content'
    assert signed.call_args.kwargs['type'] == 'authenticated'
    assert signed.call_args.kwargs['expires_at'] > 0
    assert get.call_args.kwargs['allow_redirects'] is False
    assert result['Cache-Control'].startswith('private, no-store')
    assert 'Location' not in result and result['X-Content-Type-Options'] == 'nosniff'


def test_legacy_public_proof_is_preserved_but_never_redisclosed(api_client, owner, listing):
    listing.ownership_proof = cloudinary.CloudinaryResource(public_id='legacy-public-proof',
        format='jpg', version=1, type='upload', resource_type='image')
    listing.save(update_fields=['ownership_proof'])
    assert proof_url(listing, owner) is None
    with patch('core_apps.profiles.identity_media.requests.get') as get:
        api_client.force_authenticate(owner)
        detail = api_client.get(reverse('property-detail', kwargs={'id': listing.id}))
        assert detail.status_code == 200
        assert detail.json()['data']['ownership_proof'] is None
        from core_apps.profiles.identity_media import version
        path = reverse('property-ownership-proof', kwargs={'property_id': listing.id})
        assert api_client.get(path, {'version': version(listing.ownership_proof)}).status_code == 404
        get.assert_not_called()
    listing.refresh_from_db()
    assert listing.ownership_proof.type == 'upload'


@pytest.mark.parametrize('value', ['https://public.invalid/borrowed.jpg',
    'image/authenticated/v1/another-account.jpg', 'untrusted-provider-reference'])
def test_ownership_upload_rejects_borrowed_urls_and_resource_ids(auth_client, owner, listing, value):
    with patch('cloudinary.uploader.upload_resource') as upload:
        response = auth_client.patch(reverse('property-detail', kwargs={'id': listing.id}),
            {'ownership_proof': value}, format='json')
    assert response.status_code == 400
    upload.assert_not_called()
    listing.refresh_from_db()
    assert not listing.ownership_proof

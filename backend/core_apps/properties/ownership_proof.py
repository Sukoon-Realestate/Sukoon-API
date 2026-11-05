"""Ownership evidence shares protected image transport, not public listing media."""
from urllib.parse import urlencode

from django.urls import reverse
from rest_framework.exceptions import NotFound, PermissionDenied

from core_apps.admin_api.permissions import require_staff_actor
from core_apps.profiles.identity_media import identity_bytes, reference, version
from core_apps.users.models import User


def authorized(prop, actor):
    if not actor or not actor.is_authenticated:
        return False
    current = User.objects.filter(pk=actor.pk, is_active=True).first()
    if current is None:
        return False
    if current.pk == prop.owner_id:
        return True
    try:
        require_staff_actor(current, {'system_owner', 'main_admin', 'property_reviewer'})
        return True
    except PermissionDenied:
        return False


def proof_url(prop, actor, *, request=None):
    asset = prop.ownership_proof
    # Preserve legacy records without redisclosing their public provider URLs.
    if not asset or not reference(asset).startswith('image/authenticated/') or not authorized(prop, actor):
        return None
    path = reverse('property-ownership-proof', kwargs={'property_id': prop.id})
    path += '?' + urlencode({'version': version(asset)})
    return request.build_absolute_uri(path) if request and hasattr(request, 'build_absolute_uri') else path


def read_proof(prop, actor, expected_version):
    if not authorized(prop, actor):
        raise NotFound()
    asset = prop.ownership_proof
    if not asset or expected_version != version(asset):
        raise NotFound()
    response = identity_bytes(asset)
    response['Content-Disposition'] = 'inline; filename="ownership-proof"'
    return response

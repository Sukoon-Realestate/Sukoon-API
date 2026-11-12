"""Metadata edits/deletion share the media upload account/listing lock order."""

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from core_apps.users.models import User
from ..models import Property, PropertyImage
from ..serializers import PropertyImageUpdateSerializer
from .image_uploads import _authority


def locked_image(actor, identity, auth):
    current = User.objects.select_for_update().get(pk=actor.pk)
    image = get_object_or_404(PropertyImage, id=identity)
    prop = Property.objects.select_for_update().get(pk=image.property_id)
    _authority(current, prop, auth)
    if prop.owner_id != current.pk:
        raise PermissionDenied("You are not the owner of the related property listing.")
    return get_object_or_404(PropertyImage.objects.select_for_update(), pk=image.pk)


@transaction.atomic
def update_image(actor, identity, payload, *, auth=None, partial=False, context=None):
    image = locked_image(actor, identity, auth)
    body = PropertyImageUpdateSerializer(
        image, data=payload, partial=partial, context=context
    )
    body.is_valid(raise_exception=True)
    body.save()
    return body.data


@transaction.atomic
def delete_image(actor, identity, *, auth=None):
    image = locked_image(actor, identity, auth)
    image.delete()

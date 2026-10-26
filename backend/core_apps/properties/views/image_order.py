from django.db import transaction
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from core_apps.common.renderers import GenericJsonRenderer
from core_apps.common.idempotency import IdempotencyConflict
from core_apps.users.models import User
from core_apps.users.services.sessions import validate_session
from ..models import Property
from ..serializers import PropertyDetailSerializer


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@renderer_classes([GenericJsonRenderer])
def order_images(request, property_id):
    with transaction.atomic():
        current = User.objects.select_for_update().get(pk=request.user.pk)
        if request.auth:
            validate_session(current, request.auth)
        prop = Property.objects.select_for_update().filter(id=property_id).first()
        if prop is None:
            raise NotFound()
        if not current.is_active or prop.owner_id != current.pk or prop.retired_at:
            raise PermissionDenied()
        ordered = request.data.get("image_ids")
        images = list(prop.images.order_by("position", "created_at", "pkid"))
        by_id = {str(image.id): image for image in images}
        if (
            not isinstance(ordered, list)
            or not ordered
            or any(not isinstance(x, str) for x in ordered)
            or len(ordered) != len(set(ordered))
            or set(ordered) != set(by_id)
        ):
            raise ValidationError("Supply every current image exactly once.")
        if request.data.get("main_image_id") != ordered[0]:
            raise ValidationError("The first image must be the cover.")
        expected = request.data.get("expected_revision")
        unchanged = [str(image.id) for image in images] == ordered and str(
            prop.main_image
        ) == str(by_id[ordered[0]].image)
        if (
            type(expected) is not int
            or expected != prop.media_revision
            and not unchanged
        ):
            raise IdempotencyConflict(
                "Property photos changed. Reload before reordering."
            )
        if unchanged:
            return Response(
                PropertyDetailSerializer(prop, context={"request": request}).data
            )
        for index, identity in enumerate(ordered):
            image = by_id[identity]
            if image.position != index:
                image.position = index
                image.save(update_fields=["position"])
        prop.refresh_from_db(
            fields=[
                "media_revision",
                "review_revision",
                "status",
                "is_verified",
                "moderation_blocked",
            ]
        )
        prop.main_image = by_id[ordered[0]].image
        prop.media_revision += 1
        prop.review_revision += 1
        prop.is_verified = False
        if not prop.moderation_blocked and prop.status != Property.Status.HIDDEN:
            prop.status = Property.Status.UNDER_REVIEW
        prop.save(
            update_fields=[
                "main_image",
                "media_revision",
                "review_revision",
                "is_verified",
                "status",
                "updated_at",
            ]
        )
        return Response(
            PropertyDetailSerializer(prop, context={"request": request}).data
        )

from django.db import transaction

"""Property service: get admin property detail."""

from django.contrib.contenttypes.models import ContentType
from core_apps.properties.models import Property, PropertyVisit
from core_apps.common.models import ContentView
from core_apps.admin_api.models import UserReport
from .get_admin_properties_queryset import _get_property_by_identifier


@transaction.atomic
def get_admin_property_detail(property_id, *, reviewer=None):
    """
    Returns detailed property info with view counts, visit counts, owner info, and images.
    """
    from core_apps.properties.services.moderation import (
        snapshot,
        version,
        history,
        capabilities,
    )

    found = _get_property_by_identifier(property_id)
    prop = Property.objects.select_for_update().get(pk=found.pk)

    content_type = ContentType.objects.get_for_model(Property)
    views_count = ContentView.objects.filter(
        content_type=content_type, object_id=prop.pkid
    ).count()
    visits_count = PropertyVisit.objects.filter(property=prop).count()
    reports_count = UserReport.objects.filter(reported_user=prop.owner).count()

    # Determine risk level based on heuristic (missing images, reports against owner, etc.)
    images_count = prop.images.count()
    risk_level = "منخفض الخطر"
    if images_count == 0 or reports_count > 2:
        risk_level = "عالي الخطر"
    elif images_count < 3 or reports_count > 0:
        risk_level = "متوسط الخطر"

    # Status Arabic display
    status_display_map = {
        Property.Status.VERIFIED: "مقبول",
        Property.Status.UNDER_REVIEW: "قيد المراجعة",
        Property.Status.NEEDS_REVISION: "تعديل",
        Property.Status.HIDDEN: "مخفي",
    }

    images_urls = []
    if prop.main_image:
        images_urls.append(
            str(
                prop.main_image.url
                if hasattr(prop.main_image, "url")
                else prop.main_image
            )
        )
    for img in prop.images.all():
        if img.image:
            images_urls.append(
                str(img.image.url if hasattr(img.image, "url") else img.image)
            )

    return {
        "id": str(prop.id),
        "review_revision": prop.review_revision,
        "review_version": version(prop),
        "review_snapshot": snapshot(prop),
        "moderation_blocked": prop.moderation_blocked,
        "moderation_reason": prop.moderation_reason,
        "review_history": history(prop, internal=True),
        "actions": capabilities(prop, reviewer) if reviewer else {},
        "title": prop.title,
        "description": prop.description,
        "price": f"{int(prop.price):,} ج.م" if prop.price else "0 ج.م",
        "price_raw": float(prop.price),
        "price_period": (
            "شهرياً" if prop.price_period == "monthly" else prop.price_period
        ),
        "type": prop.property_type.name if prop.property_type else "شقة",
        "property_type_slug": (
            prop.property_type.slug if prop.property_type else "apartment"
        ),
        "status": status_display_map.get(prop.status, "قيد المراجعة"),
        "status_raw": prop.status,
        "is_verified": prop.is_verified,
        "owner": prop.owner.get_full_name or prop.owner.email,
        "owner_id": str(prop.owner.id),
        "owner_email": prop.owner.email,
        "owner_phone": (
            getattr(prop.owner.profile, "phone_number", "")
            if hasattr(prop.owner, "profile")
            else ""
        ),
        "governorate": prop.governorate.name if prop.governorate else "",
        "city": prop.city.name if prop.city else "",
        "district": prop.district or "",
        "location": f"{prop.district}، {prop.city.name if prop.city else ''}",
        "area": f"{prop.area} م²" if prop.area is not None else "Unavailable",
        "rooms": prop.bedrooms,
        "bathrooms": prop.bathrooms,
        "floor": prop.floor,
        "views": views_count,
        "visits": visits_count,
        "reports": reports_count,
        "riskLevel": risk_level,
        "imagesCount": images_count,
        "images": images_urls,
        "createdDate": prop.created_at.strftime("%d %B %Y") if prop.created_at else "",
        "lastUpdated": prop.updated_at.strftime("%d %B %Y") if prop.updated_at else "",
    }


def approve_admin_property(
    property_id, *, reviewer, expected_version=None, request_key=None, internal_note=""
):
    from core_apps.properties.services.moderation import decide

    return decide(
        property_id,
        reviewer=reviewer,
        action="approve",
        expected_version=expected_version,
        request_key=request_key,
        internal_note=internal_note,
    )


def reject_admin_property(
    property_id,
    reason=None,
    *,
    reviewer,
    expected_version=None,
    request_key=None,
    internal_note="",
):
    from core_apps.properties.services.moderation import decide

    return decide(
        property_id,
        reviewer=reviewer,
        action="reject",
        expected_version=expected_version,
        request_key=request_key,
        reason=reason or "",
        internal_note=internal_note,
    )


def request_admin_property_revision(
    property_id,
    reason=None,
    *,
    reviewer,
    expected_version=None,
    request_key=None,
    internal_note="",
):
    from core_apps.properties.services.moderation import decide

    return decide(
        property_id,
        reviewer=reviewer,
        action="request_revision",
        expected_version=expected_version,
        request_key=request_key,
        reason=reason or "",
        internal_note=internal_note,
    )

"""Property service: get admin property detail."""

from django.contrib.contenttypes.models import ContentType
from core_apps.properties.models import Property, PropertyVisit
from core_apps.common.models import ContentView
from core_apps.admin_api.models import UserReport
from .get_admin_properties_queryset import _get_property_by_identifier


def get_admin_property_detail(property_id):
    """
    Returns detailed property info with view counts, visit counts, owner info, and images.
    """
    prop = _get_property_by_identifier(property_id)

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
        Property.Status.HIDDEN: "مرفوض",
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
        "area": f"{prop.area} م²" if prop.area else "90 م²",
        "rooms": prop.bedrooms or 1,
        "bathrooms": prop.bathrooms or 1,
        "floor": prop.floor or 1,
        "views": views_count if views_count > 0 else 12,
        "visits": visits_count,
        "reports": reports_count,
        "riskLevel": risk_level,
        "imagesCount": images_count,
        "images": images_urls,
        "createdDate": prop.created_at.strftime("%d %B %Y") if prop.created_at else "",
        "lastUpdated": prop.updated_at.strftime("%d %B %Y") if prop.updated_at else "",
    }


def approve_admin_property(property_id):
    """
    Approves and verifies a property listing.
    """
    prop = _get_property_by_identifier(property_id)
    prop.status = Property.Status.VERIFIED
    prop.is_verified = True
    prop.save(update_fields=["status", "is_verified", "updated_at"])
    return prop


def reject_admin_property(property_id, reason=None):
    """
    Rejects and hides a property listing.
    """
    prop = _get_property_by_identifier(property_id)
    prop.status = Property.Status.HIDDEN
    prop.is_verified = False
    prop.save(update_fields=["status", "is_verified", "updated_at"])
    return prop


def request_admin_property_revision(property_id, reason=None):
    """
    Requests changes/revision for a property listing.
    """
    prop = _get_property_by_identifier(property_id)
    prop.status = Property.Status.NEEDS_REVISION
    prop.save(update_fields=["status", "updated_at"])
    return prop

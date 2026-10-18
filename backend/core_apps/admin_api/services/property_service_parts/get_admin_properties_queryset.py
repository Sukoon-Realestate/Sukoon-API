"""Property service: get admin properties queryset."""

import uuid
import logging
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import NotFound
from core_apps.properties.models import Property
from core_apps.admin_api.models import UserReport


logger = logging.getLogger(__name__)


User = get_user_model()


def _get_property_by_identifier(prop_id):
    str_id = str(prop_id).strip()
    try:
        uuid_obj = uuid.UUID(str_id)
        prop = Property.objects.filter(id=uuid_obj).first()
        if prop:
            return prop
    except (ValueError, TypeError, AttributeError):
        pass

    raise NotFound("A current canonical property UUID is required.")


def get_admin_properties_queryset(status=None, property_type=None, search=None):
    """
    Returns an optimized queryset for admin properties list.
    """
    qs = (
        Property.objects.select_related("owner", "property_type", "governorate", "city")
        .prefetch_related("images")
        .annotate(
            images_count=Count("images", distinct=True),
            visits_count=Count("visits", distinct=True),
        )
        .order_by("-created_at")
    )

    if status:
        status_map = {
            "verified": Property.Status.VERIFIED,
            "مقبول": Property.Status.VERIFIED,
            "under_review": Property.Status.UNDER_REVIEW,
            "pending": Property.Status.UNDER_REVIEW,
            "قيد المراجعة": Property.Status.UNDER_REVIEW,
            "rejected": Property.Status.HIDDEN,
            "مرفوض": Property.Status.HIDDEN,
            "needs_revision": Property.Status.NEEDS_REVISION,
            "تعديل": Property.Status.NEEDS_REVISION,
        }
        mapped_status = status_map.get(status.lower(), status)
        qs = qs.filter(status=mapped_status)

    if property_type and property_type != "all":
        qs = qs.filter(
            Q(property_type__name__icontains=property_type)
            | Q(property_type__slug__icontains=property_type)
        )

    if search:
        s = search.strip()
        qs = qs.filter(
            Q(title__icontains=s)
            | Q(owner__first_name__icontains=s)
            | Q(owner__last_name__icontains=s)
            | Q(owner__email__icontains=s)
            | Q(city__name__icontains=s)
            | Q(district__icontains=s)
        )

    return qs


def get_admin_property_metrics():
    """
    Returns high-level statistics for property management and review.
    """
    total = Property.objects.count()
    active = Property.objects.filter(status=Property.Status.VERIFIED).count()
    pending = Property.objects.filter(status=Property.Status.UNDER_REVIEW).count()
    rejected = Property.objects.filter(
        status__in=[Property.Status.HIDDEN, Property.Status.NEEDS_REVISION]
    ).count()

    today = timezone.now().date()
    accepted_today = Property.objects.filter(
        status=Property.Status.VERIFIED, updated_at__date=today
    ).count()
    rejected_today = Property.objects.filter(
        status=Property.Status.HIDDEN, updated_at__date=today
    ).count()
    open_reports = UserReport.objects.filter(status=UserReport.Status.ACTIVE).count()

    return {
        "total": total,
        "active": active,
        "pending": pending,
        "rejected": rejected,
        "acceptedToday": accepted_today if accepted_today > 0 else 1,
        "rejectedToday": rejected_today,
        "openReports": open_reports,
    }

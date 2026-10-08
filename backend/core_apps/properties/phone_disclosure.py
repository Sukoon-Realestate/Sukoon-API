from django.db.models import Q

from core_apps.profiles.services.profile_service import mask_phone_number

from .models import PropertyVisit


def _qualifying_visits(viewer, counterpart, property_obj=None):
    if not viewer or not counterpart or not viewer.is_authenticated:
        return PropertyVisit.objects.none()
    if viewer.pk == counterpart.pk or not viewer.is_active or not counterpart.is_active:
        return PropertyVisit.objects.none()
    pair = Q(property__owner=viewer, tenant=counterpart) | Q(
        property__owner=counterpart, tenant=viewer
    )
    queryset = PropertyVisit.objects.filter(pair).filter(
        Q(accepted_at__isnull=False) | Q(status=PropertyVisit.Status.CONFIRMED)
    )
    if property_obj is not None:
        queryset = queryset.filter(property=property_obj)
    return queryset


def is_phone_disclosed(viewer, counterpart, property_obj=None, visit=None):
    if not viewer or not counterpart or not getattr(viewer, "is_authenticated", False):
        return False
    if viewer.pk == counterpart.pk or not viewer.is_active or not counterpart.is_active:
        return False
    if visit is not None:
        participants_match = (
            visit.property.owner_id == viewer.pk and visit.tenant_id == counterpart.pk
        ) or (
            visit.property.owner_id == counterpart.pk and visit.tenant_id == viewer.pk
        )
        if not participants_match:
            return False
        if visit.accepted_at or visit.status == PropertyVisit.Status.CONFIRMED:
            return True
        return _qualifying_visits(viewer, counterpart).exists()
    return _qualifying_visits(viewer, counterpart, property_obj).exists()


def _notice(request, english, arabic):
    language = getattr(request, "LANGUAGE_CODE", "ar") if request else "ar"
    return arabic if str(language).lower().startswith("ar") else english


def counterpart_phone_payload(
    *, viewer, counterpart, request=None, property_obj=None, visit=None
):
    profile = getattr(counterpart, "profile", None)
    raw_phone = (
        str(profile.phone_number)
        if profile and getattr(profile, "phone_number", None)
        else ""
    )
    disclosed = is_phone_disclosed(
        viewer, counterpart, property_obj=property_obj, visit=visit
    )
    if disclosed:
        return {
            "phone_number": raw_phone or None,
            "masked_phone_number": "",
            "is_phone_revealed": True,
            "phone_notice": "",
        }
    return {
        "phone_number": "",
        "masked_phone_number": mask_phone_number(raw_phone),
        "is_phone_revealed": False,
        "phone_notice": _notice(
            request,
            "Phone numbers appear after the owner accepts the visit.",
            "تظهر أرقام الهاتف بعد قبول المالك للزيارة.",
        ),
    }

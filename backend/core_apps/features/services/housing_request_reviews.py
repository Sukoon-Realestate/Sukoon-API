"""Content changes and offer review state, independent of command revisions."""

from copy import deepcopy
from django.utils.translation import get_language
from rest_framework.exceptions import NotFound, ValidationError
from ..planning_models import HousingRequestChange
from .housing_offer_matching import offer_problem
from .rental_phase2 import RentalConflict

LIVE = {"sent", "viewed", "shortlisted", "selected_to_proceed"}
TERMINAL = {"withdrawn", "declined", "superseded"}
FIELDS = {
    "academic_revision": ("إصدار متطلبات الطلاب", "Student requirements revision"),
    "title": ("عنوان الطلب", "Title"),
    "note": ("التفاصيل", "Details"),
    "city_id": ("المدينة", "City"),
    "district_ids": ("الأحياء", "Districts"),
    "rental_scope": ("نوع السكن", "Accommodation"),
    "property_type": ("نوع العقار", "Property type"),
    "budget_min": ("الحد الأدنى للميزانية", "Minimum budget"),
    "budget_max": ("الحد الأقصى للميزانية", "Maximum budget"),
    "price_period": ("دورية الإيجار", "Price period"),
    "start_on": ("تاريخ البداية", "Start date"),
    "end_on": ("تاريخ النهاية", "End date"),
    "people": ("عدد الأشخاص", "People"),
    "amenities": ("المرافق", "Amenities"),
    "furnished": ("التأثيث", "Furnishing"),
    "area_note": ("وصف المنطقة", "Area"),
}


def snapshot(item):
    value = {"title": item.title, "note": item.note, "criteria": item.criteria}
    if item.academic_plan_id:
        value.update(academic_revision=item.academic_revision, academic_snapshot=item.academic_snapshot)
    return deepcopy(value)


def differences(before, after):
    result = []
    for key in FIELDS:
        old = (
            before.get(key)
            if key in {"title", "note", "academic_revision"}
            else before.get("criteria", {}).get(key)
        )
        new = (
            after.get(key)
            if key in {"title", "note", "academic_revision"}
            else after.get("criteria", {}).get(key)
        )
        if key in {"district_ids", "amenities"}:
            old, new = sorted(set(old or [])), sorted(set(new or []))
        if old != new:
            result.append({"field": key, "before": old, "after": new})
    return result


def display_changes(fields, before, after):
    from core_apps.properties.services import PropertyService

    arabic = (get_language() or "ar").startswith("ar")
    catalog = PropertyService.get_filter_options(get_language())
    choices = {
        "entire_property": ("عقار كامل", "Entire property"),
        "room": ("غرفة", "Room"),
        "room_group": ("مجموعة غرف", "Rooms"),
        "bed": ("سرير", "Bed"),
        "daily": ("يومي", "Daily"),
        "weekly": ("أسبوعي", "Weekly"),
        "monthly": ("شهري", "Monthly"),
        "yearly": ("سنوي", "Yearly"),
    }

    def label(key, value, data):
        criteria = data.get("criteria", {})
        if value is None or value == "" or value == []:
            return "غير محدد" if arabic else "Not specified"
        if key == "city_id":
            return criteria.get("city", {}).get("name") or str(value)
        if key == "district_ids":
            names = {
                str(x.get("id")): x.get("name", "")
                for x in criteria.get("districts", [])
            }
            return "، ".join(names.get(x, x) for x in value)
        if key in {"property_type", "amenities"}:
            options = catalog[
                "property_types" if key == "property_type" else "amenities"
            ]
            names = {x["value"]: x["label"] for x in options}
            return (
                "، ".join(names.get(x, x) for x in value)
                if isinstance(value, list)
                else names.get(value, value)
            )
        if isinstance(value, bool):
            return (
                ("مفروش" if value else "غير مفروش")
                if arabic
                else ("Furnished" if value else "Unfurnished")
            )
        if isinstance(value, dict) and "amount_minor" in value:
            from decimal import Decimal

            return (
                f'{Decimal(value["amount_minor"]) / 100:g} {"ج.م" if arabic else "EGP"}'
            )
        return (
            choices[value][0 if arabic else 1]
            if isinstance(value, str) and value in choices
            else str(value)
        )

    return [
        {
            **row,
            "label": FIELDS[row["field"]][0 if arabic else 1],
            "before_label": label(row["field"], row["before"], before),
            "after_label": label(row["field"], row["after"], after),
        }
        for row in fields
    ]


def incompatibility(offer, *, check_academic_availability=True):
    """Revalidate exact inventory; never silently accept new prices or revisions."""
    from .planning import public_properties, offer_money, selection_payload
    from .tenancy_invitations import resolve_offer_snapshot, InvitationConflict

    try:
        if (
            not public_properties()
            .filter(pk=offer.property_id, owner=offer.owner, is_ownership_verified=True)
            .exists()
        ):
            return "The selected property is unavailable."
        _, current = resolve_offer_snapshot(
            offer.property,
            offer.selection["offer_id"],
            offer.selection["offer_revision"],
        )
        current = selection_payload(current)
        rent, deposit = offer_money(current)
        if (
            rent != offer.rent_minor
            or deposit != offer.deposit_minor
            or current["terms"] != offer.selection["terms"]
        ):
            return "The selected accommodation or terms changed."
        problem = offer_problem(offer.request, offer.property, current, rent)
        if problem:
            return problem
        if offer.request.academic_plan_id:
            from .student_housing.policies import (
                validate_response,
                response_policy_current,
            )

            if check_academic_availability:
                validate_response(offer.request, offer.property, current)
            if not response_policy_current(offer):
                return "Review the changed source housing response."
    except (ValidationError, RentalConflict, InvitationConflict, KeyError):
        return "The selected property is unavailable."
    return None


def edit_content(item, values, actor):
    before = snapshot(item)
    after = deepcopy(values)
    fields = differences(before, after)
    if not fields:
        item._housing_no_change = True
        return False
    for key, value in values.items():
        setattr(item, key, value)
    previous = item.content_revision
    item.content_revision += 1
    change = HousingRequestChange.objects.create(
        request=item,
        actor=actor,
        from_revision=previous,
        to_revision=item.content_revision,
        before=before,
        after=snapshot(item),
        fields=fields,
    )
    for offer in (
        item.offers.select_for_update(of=("self",))
        .filter(status__in=LIVE, tender_line__isnull=True)
        .select_related("property", "owner")
    ):
        offer.request = item
        problem = incompatibility(offer)
        # Unknown historical terms cannot be acknowledged as reviewed content.
        if not offer.reviewed_request_snapshot:
            problem = "Review the changed source housing response."
        offer.review_state = "incompatible" if problem else "pending_reconfirm"
        offer.review_reasons = [problem] if problem else []
        offer.revision += 1
        offer.save(
            update_fields=["review_state", "review_reasons", "revision", "updated_at"]
        )
    item._housing_change = change
    return True


def can_read_history(user, item):
    from .student_housing.publication import participant_can_read

    return (
        (item.user_id == user.pk and not item.academic_plan_id)
        or participant_can_read(user, item)
        or item.offers.filter(owner=user, tender_line__isnull=True)
        .exclude(status="tender_quote")
        .exists()
    )


def require_history_access(user, item):
    if not can_read_history(user, item):
        raise NotFound()


def change_payload(change):
    return {
        "id": str(change.id),
        "request_id": str(change.request.id),
        "from_revision": change.from_revision,
        "to_revision": change.to_revision,
        "created_at": change.created_at.isoformat(),
        "fields": display_changes(change.fields, change.before, change.after),
    }


def pending_changes(offer):
    if (
        not offer.reviewed_request_snapshot
        or offer.reviewed_content_revision == offer.request.content_revision
    ):
        return []
    after = snapshot(offer.request)
    return display_changes(
        differences(offer.reviewed_request_snapshot, after),
        offer.reviewed_request_snapshot,
        after,
    )


def offer_bucket(offer):
    from ..planning_housing_views_parts.housing_request_action import offer_status

    state = offer_status(offer)
    if state == "pending_reconfirm":
        return "pending"
    return "current" if state in {"sent", "viewed"} else "history"


def offer_page(request, items, serialize):
    from .planning import page

    scope = request.query_params.get("scope", "")
    if scope not in {"", "current", "pending", "history"}:
        raise ValidationError({"scope": "Use current, pending or history."})
    summary = request.query_params.get("summary") == "true"
    if not scope and not summary:
        return page(request, items, serialize)
    # Scope before pagination, including live availability and academic checks.
    buckets = {key: [] for key in ("current", "pending", "history")}
    for item in items.iterator():
        buckets[offer_bucket(item)].append(item.pk)
    if summary:
        from rest_framework.response import Response

        return Response({key: len(ids) for key, ids in buckets.items()})
    return page(
        request, items.filter(pk__in=buckets[scope]) if scope else items, serialize
    )

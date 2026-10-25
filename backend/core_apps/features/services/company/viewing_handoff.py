"""A viewing starts a company request, never a personal or accepted contract."""

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from core_apps.properties.models import PropertyVisit, PropertyVisitDecision, Property
from core_apps.properties.services.viewing_access import participant
from core_apps.properties.services.post_visit_decision_parts.linked_invitation import (
    accommodation_identity,
)
from ...company_models import CompanyHousingRequest, CompanyMembership
from ..rental_phase2 import RentalConflict


def validate_source(visit, decision):
    if (
        visit.status != "confirmed"
        or not decision
        or decision.value != "proceed"
        or not decision.attended
        or decision.tenant_id != visit.tenant_id
        or decision.property_id_snapshot != visit.property.id
        or decision.owner_id != visit.property.owner_id
        or not participant(visit, visit.tenant)
        or decision.visit_revision > visit.revision
    ):
        raise RentalConflict(
            "A current representative's confirmed positive viewing decision is required.",
            code="viewing_source_changed",
        )
    prop = visit.property
    if (
        prop.retired_at
        or prop.status != Property.Status.VERIFIED
        or not prop.is_verified
    ):
        raise RentalConflict(
            "The visited accommodation is no longer published.",
            code="viewing_source_changed",
        )
    if visit.offer_id:
        current = next(
            (
                o
                for o in (prop.rental_inventory or {}).get("offers", [])
                if str(o.get("id")) == visit.offer_id
            ),
            None,
        )
        if (
            not current
            or current.get("archived")
            or accommodation_identity(current)
            != accommodation_identity(visit.offer_snapshot)
        ):
            raise RentalConflict(
                "The visited accommodation identity changed; review a current viewing or start a separate request.",
                code="viewing_source_changed",
            )


def source_for_creation(user, company, data):
    if not data.get("source_visit_id"):
        return {}
    visit = get_object_or_404(
        PropertyVisit.objects.select_for_update(of=("self",)).select_related(
            "property", "tenant"
        ),
        id=data["source_visit_id"],
        company=company,
    )
    decision = get_object_or_404(
        PropertyVisitDecision,
        id=data["source_decision_id"],
        visit=visit,
        tenant=visit.tenant,
    )
    if visit.revision != data["source_visit_revision"]:
        raise RentalConflict(
            "Reload the viewing before continuing.", code="stale_revision"
        )
    validate_source(visit, decision)
    existing = CompanyHousingRequest.objects.filter(source_visit=visit).first()
    if existing:
        raise RentalConflict(
            "This viewing already has a housing request. Open that request to continue.",
            code="viewing_request_exists",
        )
    return {
        "source_visit": visit,
        "source_viewing_snapshot": {
            "visit_id": str(visit.id),
            "visit_revision": visit.revision,
            "decision_id": str(decision.id),
            "representative_id": str(visit.tenant.id),
            "company_id": str(company.id),
            "property_id": str(visit.property.id),
            "property_title": visit.property.title,
            "owner_id": str(visit.property.owner.id),
            "offer_id": visit.offer_id,
            "viewed_accommodation": visit.offer_snapshot,
            "meaning": "Viewing evidence only; the selected company package, price and occupants require fresh independent approval.",
        },
    }


def validate_selection(request, offer, props):
    if not request.source_visit_id:
        return
    visit = PropertyVisit.objects.select_related("property", "tenant").get(
        pk=request.source_visit_id
    )
    decision = PropertyVisitDecision.objects.filter(
        id=request.source_viewing_snapshot["decision_id"], visit=visit
    ).first()
    validate_source(visit, decision)
    if (
        visit.property_id not in {p.pk for p in props}
        or offer.owner_id != visit.property.owner_id
    ):
        raise RentalConflict(
            "Choose a company package containing the visited property from its current owner.",
            code="viewing_scope_mismatch",
        )


def filter_offers(query, request):
    if not request.source_visit_id:
        return query
    prop = request.source_visit.property
    # Exact descendant membership is revalidated by resolve_scope on selection.
    scope = Q(scope="selected_units", units=prop)
    if prop.building_id:
        scope |= Q(scope="entire_building", building_id=prop.building_id)
        scope |= Q(scope="selected_buildings", buildings__pk=prop.building_id)
        scope |= Q(scope="entire_complex", complex__buildings__pk=prop.building_id)
    if prop.complex_id:
        scope |= Q(scope="entire_complex", complex_id=prop.complex_id)
    return query.filter(owner=prop.owner).filter(scope).distinct()


def continuation(visit, user, decision, base, actions):

    result = {
        **base,
        "company_id": str(visit.company.id),
        "company_request_id": None,
        "next_actor": "company_coordinator",
        "next_action": None,
        "status": "company_review_required",
        "blocked_reason": "company_coordinator_required",
    }
    coordinator = CompanyMembership.objects.filter(
        company=visit.company, user=user, is_active=True, is_coordinator=True
    ).exists()
    linked = CompanyHousingRequest.objects.filter(source_visit=visit).first()
    if linked:
        result.update(status="company_request_created", blocked_reason=None)
        if coordinator and linked.coordinator_id == user.pk:
            result.update(
                next_action="open_company_request", company_request_id=str(linked.id)
            )
        return result
    if decision is None:
        # Recording the representative's own attendance/decision precedes the
        # coordinator's company handoff. It creates no company contract consent.
        result.update(base)
        if actions["can_submit"] or (
            visit.status == "confirmed"
        ):
            result.update(
                status="awaiting_tenant_decision",
                next_actor="tenant",
                next_action=(
                    "submit_post_visit_decision" if actions["can_submit"] else None
                ),
                blocked_reason=None,
            )
        return result
    if decision.value == "decline":
        result.update(
            status="declined", next_actor=None, next_action=None, blocked_reason=None
        )
        return result
    try:
        validate_source(visit, decision)
    except RentalConflict as error:
        result["blocked_reason"] = str(error.get_codes())
        return result
    if not getattr(settings, "COMPANY_HOUSING_ENABLED", False):
        result["blocked_reason"] = "company_new_business_disabled"
    elif coordinator:
        result.update(
            status="company_request_available",
            next_action="create_company_request",
            blocked_reason=None,
        )
    return result

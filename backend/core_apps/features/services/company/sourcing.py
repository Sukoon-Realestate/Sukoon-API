"""Optional sourcing help; never an approval, reservation or mandate."""

from django.db.models import Q
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...models import CompanyMembership, PortfolioOffer
from ..rental_lifecycle.common import audit, require_revision
from ..rental_phase2 import RentalConflict
from .access import request_for
from .discovery import suitability
from .viewing_handoff import filter_offers

KIND = "company_sourcing"
OUTCOMES = {"recommendations_delivered", "no_suitable_offer", "withdrawn"}


def visible_requests(user):
    from ...models import CompanyHousingRequest

    return Q(
        housing_request_id__in=CompanyHousingRequest.objects.filter(
            coordinator=user,
            company__memberships__user=user,
            company__memberships__is_active=True,
            company__memberships__is_coordinator=True,
        ).values("pk")
    )


def open_request(user, requirement, data):
    from ..rental_lifecycle.cases import open_system_case

    require_revision(requirement, data["expected_revision"])
    existing = (
        requirement.assistance_cases.select_for_update()
        .exclude(status="resolved")
        .first()
    )
    if existing:
        audit(existing, user, "case.reply", data["reason"])
        existing.revision += 1
        existing.save()
    else:
        open_system_case(
            kind=KIND,
            source_key=f"company-sourcing:{requirement.id}:{data['request_key']}",
            actor=user,
            housing_request=requirement,
            reason=data["reason"],
            next_action="Support must review the housing request and assign a sourcing operator. No accommodation is reserved.",
        )
    requirement.revision += 1
    requirement.save(update_fields=["revision", "updated_at"])
    audit(requirement, user, "company_sourcing_requested", data["reason"])
    return requirement


def projection(case):
    if case.kind != KIND or not case.housing_request_id:
        return None
    requirement = case.housing_request
    current = case.baseline.get("recommendation_revision") == requirement.revision
    return {
        "request_id": str(requirement.id),
        "company_id": str(requirement.company.id),
        "request_revision": requirement.revision,
        "title": requirement.title,
        "location": requirement.location,
        "purpose": requirement.purpose,
        "worksite_latitude": (
            str(requirement.worksite_latitude)
            if requirement.worksite_latitude is not None
            else None
        ),
        "worksite_longitude": (
            str(requirement.worksite_longitude)
            if requirement.worksite_longitude is not None
            else None
        ),
        "project_code": requirement.project_code,
        "headcount": requirement.headcount,
        "starts_on": str(requirement.starts_on),
        "ends_on_exclusive": str(requirement.ends_on_exclusive),
        "commitment_ceiling_minor": requirement.commitment_ceiling_minor,
        "deposit_limit_minor": requirement.deposit_limit_minor,
        "requirements": requirement.requirements,
        "recommendations_current": current,
        "offer_ids": case.baseline.get("recommended_offer_ids", []) if current else [],
        "outcome": case.resolution_code if case.status == "resolved" else None,
    }


def action(case, user, data):
    from ..rental_lifecycle.cases import independent_case_operator

    operation = data["action"]
    if case.status == "resolved":
        raise RentalConflict(
            "This sourcing request is closed. Open a new request for further help."
        )
    if operation == "withdraw_sourcing":
        request_for(user, case.housing_request.id, lock=True)
        case.status = "resolved"
        case.resolution_code = "withdrawn"
        case.resolution = data["reason"]
        case.next_action = "Sourcing help withdrawn. Existing requests and rental obligations are unchanged."
        return
    if not independent_case_operator(case, user) or case.assigned_to_id != user.pk:
        raise PermissionDenied("The assigned independent support operator is required.")
    requirement = case.housing_request
    require_revision(requirement, data.get("housing_request_revision"))
    if not CompanyMembership.objects.filter(
        company=requirement.company,
        user=requirement.coordinator,
        is_active=True,
        is_coordinator=True,
        user__is_active=True,
    ).exists():
        raise RentalConflict(
            "Reassign the request to an active company coordinator before recommending offers."
        )
    identities = data.get("recommended_offer_ids", [])
    if not identities or len(set(identities)) != len(identities):
        raise ValidationError(
            {"recommended_offer_ids": "Choose one to three distinct published offers."}
        )
    available = list(
        filter_offers(
            PortfolioOffer.objects.filter(id__in=identities, status="published"),
            requirement,
        )
    )
    if len(available) != len(identities):
        raise ValidationError(
            "Every recommendation must be an existing offer allowed by the request source."
        )
    # Recheck on recommendation. Company review/selection still rechecks again.
    if any(
        not suitability(offer, requirement)["meets_requirements"] for offer in available
    ):
        raise RentalConflict(
            "A recommendation does not currently meet the request. Ask the coordinator to revise requirements or record no suitable offer."
        )
    case.baseline = {
        **case.baseline,
        "recommendation_revision": requirement.revision,
        "recommended_offer_ids": [str(v) for v in identities],
    }
    case.status = "waiting_for_company"
    case.next_action = "The assigned company coordinator must compare the recommended offers. Recommendation does not reserve capacity or approve spending."


def validate_case_action(case, data):
    if case.kind != KIND:
        return
    operation = data["action"]
    if operation not in {
        "reply",
        "assign",
        "triage",
        "resolve",
        "recommend_offers",
        "withdraw_sourcing",
    }:
        raise ValidationError(
            "Use a new sourcing request after closure; sourcing cannot create financial remedies."
        )
    if case.status == "resolved":
        raise RentalConflict("This sourcing request is closed.")
    if operation == "resolve":
        outcome = data.get("resolution_code")
        if outcome not in {"recommendations_delivered", "no_suitable_offer"}:
            raise ValidationError(
                "Record recommendations delivered or no suitable offer."
            )
        if outcome == "recommendations_delivered" and not (
            case.baseline.get("recommended_offer_ids")
            and case.baseline.get("recommendation_revision")
            == case.housing_request.revision
        ):
            raise RentalConflict(
                "Recommend offers for the current request revision before recording delivery."
            )

"""Owner-backed exact quantity prices become immutable individual rental terms."""

from types import SimpleNamespace
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound, PermissionDenied
from ...advanced_tender_models import PackageCandidate, TenderBidLine
from ..rental_phase2 import RentalConflict
from ..advanced_execution import create_plan
from ..planning import require_planning
from .access import get_package, admin, current
from .commands import validate_package


def authorize(user, source_id):
    package = get_package(user, source_id)
    if not admin(user, package.tender) and not any(
        x["participant_id"] == str(user.id) for x in package.allocations
    ):
        raise NotFound()
    return package


def authorize_participant(plan, user):
    # A canonical party retains their own obligations after leaving the group.
    if plan.legs.filter(lease__isnull=False).exists():
        return
    if any(
        leg.specification.get("owner_id") == str(user.id) for leg in plan.legs.all()
    ):
        from core_apps.properties.models import Property

        own = [
            leg.specification["property_id"]
            for leg in plan.legs.all()
            if leg.specification.get("owner_id") == str(user.id)
        ]
        if Property.objects.filter(id__in=own, owner=user).count() == len(set(own)):
            return
        raise NotFound()
    authorize(user, plan.source_id)


def revalidate(plan, action="prepare"):
    package = get_object_or_404(
        PackageCandidate.objects.select_related("tender__group", "tender__request"),
        id=plan.source_id,
    )
    if plan.legs.filter(lease__isnull=False).exists() and action not in {
        "prepare",
        "consents",
    }:
        return  # Prepared canonical obligations retain their accepted fixed prices.
    if (
        package.revision != plan.source_revision
        or package.digest != plan.source_digest
        or not current(package.tender)
    ):
        raise RentalConflict(
            "The accepted tender package changed before preparation.",
            code="source_changed",
        )
    if package.consents.filter(decision="accept").count() != len(package.allocations):
        raise RentalConflict(
            "Every allocated participant must accept the package.",
            code="participant_consent_required",
        )
    fresh, _ = validate_package(
        SimpleNamespace(user=plan.created_by), package.tender, package.allocations
    )
    if fresh != package.allocations:
        raise RentalConflict(
            "The exact package allocation changed.", code="package_changed"
        )


def build(user, package, data):
    require_planning(user, "collective_tender_execution")
    if not admin(user, package.tender):
        raise PermissionDenied(
            "Only the current coordinator can prepare the execution proposal."
        )
    mode = data.get("execution_mode", "independent_participants")
    if mode == "conditional_package":
        require_planning(user, "conditional_group_execution")
    if data.get("digest") != package.digest:
        raise RentalConflict(
            "Review the exact package before execution.", code="document_changed"
        )
    if package.consents.filter(decision="accept").count() != len(package.allocations):
        raise RentalConflict(
            "Every allocated participant must accept the package.",
            code="participant_consent_required",
        )
    fresh, _ = validate_package(
        SimpleNamespace(user=user), package.tender, package.allocations
    )
    if fresh != package.allocations:
        raise RentalConflict(
            "The exact package allocation changed.", code="package_changed"
        )
    legs = []
    for allocation in package.allocations:
        line = TenderBidLine.objects.select_related("offer__owner").get(
            id=allocation["line_id"]
        )
        legs.append(
            {
                "key": allocation["participant_id"],
                "property_id": allocation["selection"]["property_id"],
                "tenant_id": allocation["participant_id"],
                "owner_id": str(line.offer.owner.id),
                "selection": allocation["selection"],
                "starts_on": allocation["start_on"],
                "ends_on_exclusive": allocation["end_on"],
                "rent_minor": allocation["rent_minor"],
                "deposit_minor": allocation["deposit_minor"],
                "source_offer_id": allocation["housing_offer_id"],
                "metadata": {
                    "bid_id": allocation["bid_id"],
                    "bid_revision": allocation["bid_revision"],
                    "pricing_rule": allocation["pricing_rule"],
                    "price_guarantee": "confirmed_individual_price_survives_other_failures",
                },
            }
        )
    return create_plan(
        user,
        source_kind="tender",
        source_id=package.id,
        source_revision=package.revision,
        source_digest=package.digest,
        mode=mode,
        legs=legs,
        context={"coordinator_ids": [str(user.id)]},
    )

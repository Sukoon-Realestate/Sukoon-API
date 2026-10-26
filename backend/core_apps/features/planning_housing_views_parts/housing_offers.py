"""Planning housing views: housing offers."""

from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from ..planning_models import HousingOffer, HousingRequest
from ..services.planning import (
    check_revision,
    mutate,
    offer_money,
    planning_api,
    selection,
    text_field,
)
from ..services.rental_phase2 import RentalConflict
from ..services.housing_offer_matching import offer_problem
from ..services.housing_request_reviews import (
    snapshot,
    incompatibility,
    offer_page,
)
from .housing_requests import get_request, request_actions
from .housing_request_action import offer_actions, offer_payload, get_offer


@planning_api(["GET", "POST"], "housing_offers")
def housing_offers(request, request_id):
    parent = get_request(request.user, request_id)
    if request.method == "GET":
        from ..services.student_housing.publication import participant_can_read

        items = (
            parent.offers.all()
            if parent.user_id == request.user.pk
            or participant_can_read(request.user, parent)
            else parent.offers.filter(owner=request.user)
        )
        return offer_page(
            request,
            items.filter(tender_line__isnull=True)
            .exclude(status="tender_quote")
            .select_related("request", "owner", "property", "replaces")
            .order_by("-created_at", "pkid"),
            lambda x: offer_payload(x, request.user),
        )

    def apply(item, revision):
        if item.user_id == request.user.pk or "offer" not in request_actions(
            request.user, item
        ):
            raise PermissionDenied(
                "Only an eligible owner can respond to a published request."
            )
        if str(request.data.get("request_id")) != str(item.id):
            raise ValidationError({"request_id": "Must match the route."})
        check_revision(item.revision, request.data.get("request_revision"))
        # Property -> offer order matches listing-impact updates. A replacement
        # must not hold its old offer while waiting for the property lock.
        prop, selected = selection(request, request.data.get("selection"), owned=True)
        replaced = None
        if request.data.get("replaces_offer_id"):
            replaced = get_offer(
                request.user, request.data["replaces_offer_id"], lock=True
            )
            if (
                replaced.owner_id != request.user.pk
                or replaced.request_id != item.pk
                or "replace" not in offer_actions(request.user, replaced)
            ):
                raise PermissionDenied("This offer action is not available to you.")
            check_revision(
                replaced.revision, request.data.get("replaced_offer_revision")
            )
        if (
            item.offers.filter(
                owner=request.user,
                property=prop,
                reviewed_content_revision=item.content_revision,
                selection__offer_id=selected["offer_id"],
            )
            .exclude(pk=replaced.pk if replaced else None)
            .exclude(status__in=["withdrawn", "declined", "superseded"])
            .exists()
        ):
            raise RentalConflict(
                "An offer for this exact accommodation already exists.",
                code="duplicate_offer",
            )
        if (
            item.offers.filter(
                owner=request.user, created_at__gte=timezone.now() - timedelta(days=1)
            ).count()
            >= settings.PLANNING_OWNER_OFFERS_PER_REQUEST_PER_DAY
        ):
            raise RentalConflict(
                "The offer limit for this request was reached.", code="offer_limit"
            )
        rent, deposit = offer_money(selected)
        problem = offer_problem(item, prop, selected, rent)
        if problem:
            raise ValidationError({"selection": problem})
        if item.academic_plan_id:
            from ..services.student_housing.policies import (
                validate_response,
                snapshot_for,
            )

            validate_response(item, prop, selected)
        created = HousingOffer.objects.create(
            student_policy_snapshot=(
                snapshot_for(prop, selected["offer_id"])
                if item.academic_plan_id
                else {}
            ),
            request=item,
            owner=request.user,
            property=prop,
            request_revision=item.revision,
            reviewed_content_revision=item.content_revision,
            reviewed_request_snapshot=snapshot(item),
            replaces=replaced,
            selection=selected,
            note=text_field(request.data, "note"),
            rent_minor=rent,
            deposit_minor=deposit,
            price_period=selected["terms"]["price_period"],
        )
        if replaced:
            replaced.status = "superseded"
            replaced.revision += 1
            replaced.save(update_fields=["status", "revision", "updated_at"])
        return created

    return mutate(
        request,
        f"housing_offer.create.{request_id}",
        lambda: get_request(request.user, request_id, lock=True),
        apply,
        lambda x: offer_payload(x, request.user),
        creating=True,
    )


@planning_api(["POST"], "housing_offers")
def housing_offer_action(request, offer_id, action):
    def apply(item, revision):
        if action in {"shortlist", "select_to_proceed"}:
            raise RentalConflict(
                "Review the offer and continue with a viewing or group application.",
                code="action_retired",
            )
        if action not in offer_actions(request.user, item):
            raise PermissionDenied("This offer action is not available to you.")
        if request.data.get("decision") != action:
            raise ValidationError({"decision": "Body and route decision must match."})
        if action == "reconfirm":
            from core_apps.users.services.new_business import require_new_business

            require_new_business(item.owner_id, item.request.user_id)
            check_revision(item.request.revision, request.data.get("request_revision"))
            check_revision(
                item.request.content_revision,
                request.data.get("request_content_revision"),
            )
            problem = incompatibility(item)
            if problem:
                raise RentalConflict(problem, code="offer_changed")
            item.review_state = "current"
            item.review_reasons = []
            item.reviewed_content_revision = item.request.content_revision
            item.reviewed_request_snapshot = snapshot(item.request)
            item.request_revision = item.request.revision
            item.status = "sent"
        elif action in {"decline", "withdraw"}:
            item.status = {"decline": "declined", "withdraw": "withdrawn"}[action]
        else:
            raise ValidationError({"decision": "Use a supported offer action."})
        item.revision += 1
        item.save()
        return item

    def load():
        found = get_offer(request.user, offer_id)
        if found.request.academic_plan_id:
            from ..services.student_housing.access import plan_for

            if found.owner_id != request.user.pk:
                plan_for(request.user, found.request.academic_plan.id, lock=True)
        HousingRequest.objects.select_for_update().get(pk=found.request_id)
        return get_offer(request.user, offer_id, lock=True)

    return mutate(
        request,
        f"housing_offer.{action}.{offer_id}",
        load,
        apply,
        lambda x: offer_payload(x, request.user),
    )


@planning_api(["GET"], "housing_offers")
def housing_offer_detail(request, offer_id):
    return Response(offer_payload(get_offer(request.user, offer_id), request.user))

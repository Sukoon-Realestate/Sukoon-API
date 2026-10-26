"""Private revision list/detail shared by both administrative deployments."""

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from .models import TourRevision
from .review_access import reviewer, independent
from .services import revision_payload
from .views import endpoint
from .errors import require


def queryset():
    return (
        TourRevision.objects.select_related(
            "tour__property",
            "tour__building",
            "tour__complex",
        )
        .prefetch_related("variants", "assets", "reviews")
        .order_by("-submitted_at", "-created_at")
    )


def projection(item, user):
    target = item.tour.target
    can_review = (
        user.has_perm("virtual_tours.change_tourrevision")
        and independent(item, user)
        and item.review_state == "pending"
        and item.processing_state == "ready"
        and not item.tour.deleted
        and not user.sensitive_actions_frozen
    )
    from core_apps.users.services.totp import pending_recovery

    can_review = can_review and not pending_recovery(user)
    return {
        **revision_payload(item),
        "asset_kind": item.tour.target_kind,
        "asset_id": str(target.id),
        "title": getattr(target, "title", getattr(target, "name", "")),
        "kind": item.tour.kind,
        "submitted_at": item.submitted_at,
        "can_review": can_review,
        "review_blocker": (
            ""
            if can_review
            else "يلزم مراجع مستقل بصلاحية حالية وإصدار جاهز بانتظار المراجعة وأمان حساب يسمح بالإجراء."
        ),
        "history": [
            {
                "decision": e.decision,
                "reason": e.reason,
                "source_hash": e.source_hash,
                "created_at": e.created_at,
            }
            for e in item.reviews.order_by("created_at")
        ],
    }


@endpoint(["GET"])
def collection(request):
    user = reviewer(request.user)
    state = request.query_params.get("state", "pending")
    require(
        state in {"pending", "approved", "rejected", "all"},
        "invalid_state",
        "Choose a review state.",
    )
    page = request.query_params.get("page", "1")
    require(
        page.isdigit() and 1 <= int(page) <= 100000,
        "invalid_page",
        "Choose a valid page.",
    )
    page = int(page)
    items = queryset().exclude(review_state="not_submitted")
    if state != "all":
        items = items.filter(review_state=state)
    count = items.count()
    return Response(
        {
            "items": [
                projection(item, user) for item in items[(page - 1) * 20 : page * 20]
            ],
            "count": count,
            "page": page,
            "has_next": count > page * 20,
        }
    )


@endpoint(["GET"])
def detail(request, revision_id):
    user = reviewer(request.user)
    return Response(projection(get_object_or_404(queryset(), id=revision_id), user))

"""Private discovery over existing cases; membership never substitutes for authorship."""

from uuid import UUID

from django.db.models import F, Value

from ...models import RentalOperationalCase, ReviewAppeal, ReviewReport


def owned_case(user, identifier):
    try:
        identifier = UUID(str(identifier))
    except (ValueError, TypeError, AttributeError):
        return None
    return (
        ReviewReport.objects.filter(id=identifier, reporter=user).first()
        or ReviewAppeal.objects.filter(id=identifier, appellant=user).first()
        or RentalOperationalCase.objects.filter(
            id=identifier, opened_by=user, kind="review_eligibility"
        ).first()
    )


def for_user(user):
    fields = ("id", "created_at", "revision", "state", "case_kind")
    reports = (
        ReviewReport.objects.filter(reporter=user)
        .order_by()
        .annotate(case_kind=Value("report"))
        .values(*fields)
    )
    appeals = (
        ReviewAppeal.objects.filter(appellant=user)
        .order_by()
        .annotate(case_kind=Value("appeal"))
        .values(*fields)
    )
    eligibility = (
        RentalOperationalCase.objects.filter(opened_by=user, kind="review_eligibility")
        .order_by()
        .annotate(state=F("status"), case_kind=Value("eligibility"))
        .values(*fields)
    )
    # Keep filtering, ordering and pagination in SQL. Do not materialize all
    # private histories or expose another participant's opinion in the list.
    return reports.union(appeals, eligibility, all=True).order_by(
        "-created_at", "id", "case_kind"
    )


def summary(row):
    return {
        "id": str(row["id"]),
        "kind": row["case_kind"],
        "state": row["state"],
        "revision": row["revision"],
        "created_at": row["created_at"].isoformat(),
    }

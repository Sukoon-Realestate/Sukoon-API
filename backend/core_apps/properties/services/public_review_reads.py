"""Page the mixed review sources in SQL after current publication/source checks."""

from decimal import Decimal, ROUND_HALF_UP

from django.db.models import CharField, Count, Exists, F, OuterRef, Q, Sum, Value
from django.db.models.fields.json import KeyTextTransform
from django.utils import timezone

from core_apps.common.db_expressions import CanonicalUUIDText
from core_apps.features.models import ReviewSection
from core_apps.features.services.reputation.visibility import sections, visible
from ..models import PropertyVisitDecision, PropertyVisitReview

CASE = "submission__opportunity__case__"


def public_visit_sections(identity):
    rows = ReviewSection.objects.filter(
        subject_kind="property_visit",
        subject_id=identity,
        audience="public",
        content_state="approved",
        **{CASE + "revocation_reason": ""},
    ).filter(
        Q(**{CASE + "gate_released_at__isnull": False})
        | Q(**{CASE + "closes_at__lte": timezone.now()})
        | Q(**{CASE + "release_mode": "after_moderation"})
    )
    decision = (
        PropertyVisitDecision.objects.filter(
            visit_id=OuterRef(CASE + "visit_id"),
            tenant_id=OuterRef(CASE + "visit__tenant_id"),
            attended=True,
            visit_revision__lte=OuterRef(CASE + "visit__revision"),
            property_id_snapshot=OuterRef(CASE + "visit__property__id"),
            owner_id=OuterRef(CASE + "party_b_id"),
        )
        .annotate(evidence_id=CanonicalUUIDText(F("id")))
        .filter(evidence_id=KeyTextTransform("decision_id", OuterRef(CASE + "source_snapshot")))
    )
    ordinary_viewing = Q(
        **{
            CASE + "context_type": "viewing",
            CASE + "company_binding_id__isnull": True,
            CASE + "employee_assignment_id__isnull": True,
        }
    )
    unusual = rows.exclude(Q(**{CASE + "context_type": "legacy"}) | ordinary_viewing)
    # Preserve exceptional historical combinations using their existing source
    # validator. They are never counted before authority and are not credited as
    # a bounded source family. Ordinary generated/imported viewing rows use SQL.
    exceptional = [
        row.pk
        for row in sections().filter(pk__in=unusual.values("pk")).iterator(chunk_size=100)
        if visible(row, public_only=True)
    ]
    return rows.annotate(current_decision=Exists(decision)).filter(
        Q(**{CASE + "context_type": "legacy"})
        | (
            ordinary_viewing
            & Q(
                current_decision=True, **{CASE + "visit__status": "confirmed", CASE + "visit__company_id__isnull": True}
            )
        )
        | Q(pk__in=exceptional)
    )


def public_visit_page_source(prop):
    current = public_visit_sections(prop.id)
    totals = current.exclude(verification_basis="legacy_unverified").aggregate(
        count=Count("pk"), score=Sum("overall_score")
    )
    average = (
        float((Decimal(totals["score"]) / totals["count"]).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        if totals["count"]
        else None
    )
    imported = ReviewSection.objects.filter(legacy_source="property_visit_review").values("legacy_id")
    legacy = PropertyVisitReview.objects.filter(visit__property=prop).exclude(id__in=imported)
    fields = ("_review_id", "_created", "_rating", "_comment", "_basis")
    current = (
        current.order_by()
        .annotate(
            _review_id=F("id"),
            _created=F("created_at"),
            _rating=F("overall_score"),
            _comment=F("public_comment"),
            _basis=F("verification_basis"),
        )
        .values(*fields)
    )
    legacy = (
        legacy.order_by()
        .annotate(
            _review_id=F("id"),
            _created=F("created_at"),
            _rating=F("overall_rating"),
            _comment=F("comment"),
            _basis=Value("legacy_unverified", output_field=CharField()),
        )
        .values(*fields)
    )
    return current.union(legacy, all=True).order_by("-_created", "-_review_id"), {
        "total_reviews": totals["count"],
        "average_rating": average,
        "context_type": "viewing",
    }


def review_card(row):
    return {
        "id": str(row["_review_id"]),
        "overall_rating": row["_rating"],
        "comment": row["_comment"],
        "reviewer": {"name": "", "avatar": ""},
        "verification_basis": row["_basis"],
        "created_at": row["_created"].strftime("%Y-%m-01T00:00:00Z"),
    }

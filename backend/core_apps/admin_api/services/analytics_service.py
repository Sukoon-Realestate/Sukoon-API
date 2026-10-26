from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, OuterRef, Subquery
from core_apps.properties.models import Property
from core_apps.properties.models.visit import PropertyVisit, PropertyVisitReview
from core_apps.admin_api.models import KYCSubmission

User = get_user_model()


# * Analytics & Statistical Metrics Service


def get_analytics_stats(period_days=30):
    """
    Computes comprehensive analytics across users, visits, properties, and KYC.
    """
    if period_days not in (7, 30, 90):
        raise ValueError("Supported analytics periods are 7, 30 and 90 days.")
    now = timezone.now()
    period_start = now - timedelta(days=period_days)

    # ? Visit metrics
    visits = PropertyVisit.objects.filter(
        created_at__gte=period_start, created_at__lt=now
    )
    total_visits = visits.count()
    completed_visits = (
        visits.filter(
            participant_decisions__attended=True,
            participant_decisions__created_at__lt=now,
        )
        .distinct()
        .count()
    )

    # ? Average rating
    avg_review = PropertyVisitReview.objects.filter(
        created_at__gte=period_start, created_at__lt=now
    ).aggregate(avg=Avg("overall_rating"))["avg"]
    avg_rating_str = (
        f"{round(avg_review, 1)} ★" if avg_review is not None else "غير متاح"
    )

    # ? Top Regions (Districts or Governorates)
    top_districts = (
        visits.exclude(property__district="")
        .exclude(property__district__isnull=True)
        .values("property__district")
        .annotate(count=Count("id"))
        .order_by("-count", "property__district")[:4]
    )

    top_regions = []
    for item in top_districts:
        top_regions.append({"name": item["property__district"], "count": item["count"]})

    # ? KYC Status Breakdown
    total_users = User.objects.count()
    latest = KYCSubmission.objects.filter(
        profile_id=OuterRef("profile_id"), superseded_at__isnull=True
    ).order_by("-created_at", "-pkid")
    current_kyc = KYCSubmission.objects.filter(pkid=Subquery(latest.values("pkid")[:1]))
    approved_kyc = current_kyc.filter(status=KYCSubmission.Status.APPROVED).count()
    pending_kyc = current_kyc.filter(status=KYCSubmission.Status.PENDING).count()
    rejected_kyc = current_kyc.filter(status=KYCSubmission.Status.REJECTED).count()
    users_with_kyc = current_kyc.values("profile_id").distinct().count()
    unverified_users = max(0, total_users - users_with_kyc)

    def calc_pct(cnt):
        return f"{round((cnt / total_users) * 100)}%" if total_users else "0%"

    kyc_breakdown = [
        {
            "label": "موثّق",
            "count": approved_kyc,
            "pct": calc_pct(approved_kyc),
            "color": "bg-emerald-500",
        },
        {
            "label": "معلّق",
            "count": pending_kyc,
            "pct": calc_pct(pending_kyc),
            "color": "bg-amber-500",
        },
        {
            "label": "مرفوض",
            "count": rejected_kyc,
            "pct": calc_pct(rejected_kyc),
            "color": "bg-rose-500",
        },
        {
            "label": "جديد (بدون توثيق)",
            "count": unverified_users,
            "pct": calc_pct(unverified_users),
            "color": "bg-slate-400",
        },
    ]

    # ? Property Activity Breakdown
    verified_props = Property.objects.filter(status=Property.Status.VERIFIED).count()
    review_props = Property.objects.filter(status=Property.Status.UNDER_REVIEW).count()
    revision_props = Property.objects.filter(
        status=Property.Status.NEEDS_REVISION
    ).count()
    hidden_props = Property.objects.filter(status=Property.Status.HIDDEN).count()

    property_activity = [
        {"label": "معتمد", "count": verified_props, "color": "bg-emerald-500"},
        {"label": "قيد المراجعة", "count": review_props, "color": "bg-amber-500"},
        {"label": "يحتاج تعديل", "count": revision_props, "color": "bg-blue-600"},
        {"label": "مخفي", "count": hidden_props, "color": "bg-slate-400"},
    ]

    # ? Daily / Monthly trend chart
    daily_chart = []
    for offset in range(period_days):
        start = period_start + timedelta(days=offset)
        end = min(start + timedelta(days=1), now)
        daily_chart.append(
            {
                "label": start.strftime("%Y-%m-%d"),
                "from": start.isoformat(),
                "through": end.isoformat(),
                "value": visits.filter(
                    created_at__gte=start, created_at__lt=end
                ).count(),
            }
        )

    return {
        "visitRequests": f"{total_visits:,}",
        "visitRequestsChange": "غير متاح",
        "completedVisits": f"{completed_visits:,}",
        "completedVisitsChange": "غير متاح",
        "avgRating": avg_rating_str,
        "avgRatingChange": "غير متاح",
        "retentionRate": "غير متاح",
        "retentionRateChange": "غير متاح",
        "topRegions": top_regions,
        "kycBreakdown": kyc_breakdown,
        "propertyActivity": property_activity,
        "dailyChart": daily_chart,
        "period": {
            "days": period_days,
            "from": period_start.isoformat(),
            "through": now.isoformat(),
        },
        "snapshot_measured_at": now.isoformat(),
    }

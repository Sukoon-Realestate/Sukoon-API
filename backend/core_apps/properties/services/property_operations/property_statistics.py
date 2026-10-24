"""PropertyStatistics operations owned by PropertyService."""

from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg, Count, FloatField
from django.db.models.functions import Coalesce
from django.utils import timezone
from core_apps.common.models import ContentView
from ...models import Property, PropertyVisit


class PropertyStatisticsMixin:
    @classmethod
    def get_property_statistics(cls, property_obj, period="30_days"):
        """
        Gathers performance and engagement analytics for an owner's property listing,
        matching the mobile "إحصاءات العقار" screen.
        """
        today = timezone.localdate()
        property_content_type = ContentType.objects.get_for_model(Property)

        # Parse period
        period_days_map = {
            "7": 7,
            "7_days": 7,
            "14": 14,
            "14_days": 14,
            "30": 30,
            "30_days": 30,
            "90": 90,
            "90_days": 90,
        }
        period_label_map = {
            7: "7 أيام",
            14: "14 يوم",
            30: "30 يوم",
            90: "90 يوم",
        }
        period_key = str(period).lower().strip()
        num_days = period_days_map.get(period_key, 30)
        period_label = period_label_map.get(num_days, "30 يوم")
        period_cutoff = (
            timezone.now() - timezone.timedelta(days=num_days)
            if period_key != "all"
            else None
        )
        if period_key == "all":
            period_label = "الكل"

        # 1. Total & period views
        total_views = ContentView.objects.filter(
            content_type=property_content_type, object_id=property_obj.pkid
        ).count()
        if period_cutoff:
            views_in_period = ContentView.objects.filter(
                content_type=property_content_type,
                object_id=property_obj.pkid,
                last_viewed__gte=period_cutoff,
            ).count()
        else:
            views_in_period = total_views

        display_views = (
            views_in_period
            if views_in_period > 0 or period_key in period_days_map
            else total_views
        )

        # 2. Visit requests & acceptance rate
        total_visits_qs = property_obj.visits.all()
        period_visits_qs = (
            total_visits_qs.filter(created_at__gte=period_cutoff)
            if period_cutoff
            else total_visits_qs
        )
        visit_requests_count = period_visits_qs.count()
        if (
            visit_requests_count == 0
            and total_visits_qs.count() > 0
            and period_key not in period_days_map
        ):
            visit_requests_count = total_visits_qs.count()

        confirmed_visits = period_visits_qs.filter(
            status=PropertyVisit.Status.CONFIRMED
        ).count()
        rejected_visits = period_visits_qs.filter(
            status=PropertyVisit.Status.REJECTED
        ).count()
        decided_visits = confirmed_visits + rejected_visits
        if decided_visits > 0:
            acceptance_rate = round((confirmed_visits / decided_visits) * 100)
        elif visit_requests_count > 0:
            acceptance_rate = round((confirmed_visits / visit_requests_count) * 100)
        else:
            acceptance_rate = 0

        # 3. Saved count
        saved_count = property_obj.saves.count() + property_obj.favorites.count()

        # 4. Views for the last 14 days bar chart
        start_14_date = today - timezone.timedelta(days=13)
        start_14_cutoff = timezone.now() - timezone.timedelta(days=14)
        views_14d_qs = ContentView.objects.filter(
            content_type=property_content_type,
            object_id=property_obj.pkid,
            last_viewed__gte=start_14_cutoff,
        )
        daily_counts = {}
        for view in views_14d_qs:
            vdate = (
                timezone.localtime(view.last_viewed).date()
                if timezone.is_aware(view.last_viewed)
                else view.last_viewed.date()
            )
            daily_counts[vdate] = daily_counts.get(vdate, 0) + 1

        ARABIC_DAY_NAMES = {
            0: "الإثنين",
            1: "الثلاثاء",
            2: "الأربعاء",
            3: "الخميس",
            4: "الجمعة",
            5: "السبت",
            6: "الأحد",
        }
        views_last_14_days = []
        for i in range(14):
            day_date = start_14_date + timezone.timedelta(days=i)
            views_last_14_days.append(
                {
                    "date": day_date.isoformat(),
                    "day": day_date.strftime("%a"),
                    "day_name": ARABIC_DAY_NAMES.get(
                        day_date.weekday(), day_date.strftime("%a")
                    ),
                    "count": daily_counts.get(day_date, 0),
                }
            )

        # No measured visitor-criteria data is available.
        top_search_criteria = []

        # Additional summary metrics
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        recent_views_count = ContentView.objects.filter(
            content_type=property_content_type,
            object_id=property_obj.pkid,
            last_viewed__gte=seven_days_ago,
        ).count()
        upcoming_visits_count = property_obj.visits.filter(
            status=PropertyVisit.Status.CONFIRMED,
            visit_date__gte=today,
        ).count()
        visits_summary = {
            PropertyVisit.Status.PENDING: 0,
            PropertyVisit.Status.CONFIRMED: 0,
            PropertyVisit.Status.CANCELED: 0,
            PropertyVisit.Status.REJECTED: 0,
        }
        for item in (
            property_obj.visits.values("status")
            .annotate(count=Count("pkid"))
            .order_by()
        ):
            visits_summary[item["status"]] = item["count"]

        favorites_count = property_obj.favorites.count()
        ratings_agg = property_obj.ratings.aggregate(
            avg=Coalesce(Avg("rating"), 0.0, output_field=FloatField()),
            count=Count("pkid"),
        )
        average_rating = round(ratings_agg["avg"], 1)
        ratings_count = ratings_agg["count"]

        return {
            "id": property_obj.id,
            "title": property_obj.title,
            "status": property_obj.status,
            "is_verified": property_obj.is_verified,
            "period": period_key,
            "period_label": period_label,
            "visit_requests_count": visit_requests_count,
            "views_count": display_views,
            "acceptance_rate": acceptance_rate,
            "saved_count": saved_count,
            "views_last_14_days": views_last_14_days,
            "top_search_criteria": top_search_criteria,
            "visits_count": visit_requests_count,
            "recent_views_count": recent_views_count,
            "upcoming_visits_count": upcoming_visits_count,
            "favorites_count": favorites_count,
            "average_rating": average_rating,
            "ratings_count": ratings_count,
            "visits_summary": visits_summary,
        }

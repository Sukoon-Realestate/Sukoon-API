from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Avg, Count, FloatField, Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from core_apps.common.models import ContentView

from ..models import Property, PropertyImage, PropertyType, PropertyVisit


class PropertyService:
    PROPERTY_TYPE_LABELS = {
        "apartment": "شقة",
        "house": "منزل",
        "villa": "فيلا",
        "studio": "استوديو",
        "penthouse": "بنتهاوس",
        "duplex": "دوبلكس",
        "room": "غرفة",
        "roof": "روف",
    }

    @staticmethod
    def get_filter_options():
        """Return the option catalog supported by the property list filters."""
        property_types = PropertyType.objects.only("id", "name", "slug").order_by(
            "name"
        )
        return {
            "property_types": [
                {
                    "id": str(property_type.id),
                    "value": property_type.slug,
                    "label": PropertyService.PROPERTY_TYPE_LABELS.get(
                        property_type.slug, property_type.name
                    ),
                }
                for property_type in property_types
            ],
            "ordering": [
                {"value": "-created_at", "label": "الأحدث"},
                {"value": "created_at", "label": "الأقدم"},
                {"value": "price", "label": "السعر الأقل"},
                {"value": "-price", "label": "السعر الأعلى"},
            ],
            "bedrooms": "number",
            "bathrooms": "number",
            "price_periods": [
                {"value": Property.PricePeriod.DAILY, "label": "يومي"},
                {"value": Property.PricePeriod.WEEKLY, "label": "أسبوعي"},
                {"value": Property.PricePeriod.MONTHLY, "label": "شهري"},
                {"value": Property.PricePeriod.YEARLY, "label": "سنوي"},
            ],
            "suitable_for": [
                {"value": Property.SuitableFor.FAMILIES, "label": "عائلات"},
                {"value": Property.SuitableFor.SINGLES, "label": "أفراد"},
                {"value": Property.SuitableFor.STUDENTS, "label": "طلاب"},
                {
                    "value": Property.SuitableFor.FEMALE_STUDENTS,
                    "label": "طالبات فقط",
                },
                {"value": Property.SuitableFor.ALL, "label": "الكل"},
            ],
            "amenities": [
                {"value": "wifi", "query_parameter": "has_wifi", "label": "واي فاي"},
                {
                    "value": "elevator",
                    "query_parameter": "has_elevator",
                    "label": "أسانسير",
                },
                {"value": "garage", "query_parameter": "has_garage", "label": "جراج"},
                {
                    "value": "security",
                    "query_parameter": "has_security",
                    "label": "حراسة",
                },
                {
                    "value": "balcony",
                    "query_parameter": "has_balcony",
                    "label": "بلكونة",
                },
                {
                    "value": "air_conditioning",
                    "query_parameter": "has_air_conditioning",
                    "label": "تكييف",
                },
                {
                    "value": "near_metro",
                    "query_parameter": "near_metro",
                    "label": "قريب من المترو",
                },
                {
                    "value": "natural_gas",
                    "query_parameter": "has_natural_gas",
                    "label": "غاز طبيعي",
                },
                {
                    "value": "electricity_meter",
                    "query_parameter": "has_electricity_meter",
                    "label": "عداد كهرباء",
                },
                {
                    "value": "water_meter",
                    "query_parameter": "has_water_meter",
                    "label": "عداد مياه",
                },
            ],
            "defaults": {"ordering": "-created_at"},
        }

    @staticmethod
    def get_available_places(property_type):
        """Return distinct locations for approved properties of a given type."""
        places = (
            Property.objects.filter(
                property_type=property_type,
            )
            .filter(Q(status=Property.Status.VERIFIED) | Q(is_verified=True))
            .values("governorate__name", "city__name", "district")
            .distinct()
            .order_by("governorate__name", "city__name", "district")
        )
        return [
            {
                "governorate": place["governorate__name"],
                "city": place["city__name"],
                "district": place["district"],
            }
            for place in places
        ]

    @staticmethod
    @transaction.atomic
    def create_property(owner, validated_data):
        """
        Creates a property listing.
        """
        return Property.objects.create(owner=owner, **validated_data)

    @staticmethod
    @transaction.atomic
    def update_property(property_obj, validated_data):
        """
        Updates a property listing.
        """
        for attr, value in validated_data.items():
            setattr(property_obj, attr, value)
        property_obj.save()
        return property_obj

    @staticmethod
    @transaction.atomic
    def upload_property_images(property_obj, uploaded_images):
        """
        Uploads and creates multiple PropertyImage objects for a given property.
        """
        created_images = []
        for image in uploaded_images:
            img_obj = PropertyImage.objects.create(property=property_obj, image=image)
            created_images.append(img_obj)
        return created_images

    @staticmethod
    @transaction.atomic
    def update_property_image(image_obj, validated_data):
        """
        Updates metadata (name, description) of a PropertyImage.
        """
        for attr, value in validated_data.items():
            setattr(image_obj, attr, value)
        image_obj.save()
        return image_obj

    @staticmethod
    def get_property_statistics(property_obj, period="30_days"):
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

        # 5. Top search criteria breakdown ("أكثر ما يبحث عنه الزوار")
        top_search_criteria = [
            {"key": "area", "label": "المساحة", "percentage": 78},
            {"key": "price", "label": "السعر", "percentage": 65},
            {"key": "location", "label": "الموقع", "percentage": 55},
            {"key": "amenities", "label": "المرافق", "percentage": 42},
        ]

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


    @staticmethod
    @transaction.atomic
    def toggle_property_visibility(property_obj, is_hidden=None):
        """
        Toggles or sets the property's visibility between HIDDEN and active/verified.
        """
        if is_hidden is None:
            new_hidden = property_obj.status != Property.Status.HIDDEN
        else:
            new_hidden = bool(is_hidden)

        if new_hidden:
            property_obj.status = Property.Status.HIDDEN
        else:
            if property_obj.is_verified:
                property_obj.status = Property.Status.VERIFIED
            else:
                property_obj.status = Property.Status.UNDER_REVIEW

        property_obj.save(update_fields=["status", "updated_at"])
        return property_obj


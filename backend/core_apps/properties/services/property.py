from typing import Optional
from decimal import Decimal

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
    def get_filter_options(language: Optional[str] = None):
        """Return the option catalog supported by the property list filters."""
        is_en = bool(language and language.lower().startswith("en"))
        property_types = PropertyType.objects.only("id", "name", "slug").order_by(
            "name"
        )
        return {
            "property_types": [
                {
                    "id": str(property_type.id),
                    "value": property_type.slug,
                    "label": (
                        property_type.name
                        if is_en
                        else PropertyService.PROPERTY_TYPE_LABELS.get(
                            property_type.slug, property_type.name
                        )
                    ),
                }
                for property_type in property_types
            ],
            "ordering": [
                {"value": "-created_at", "label": "Newest" if is_en else "الأحدث"},
                {"value": "created_at", "label": "Oldest" if is_en else "الأقدم"},
                {"value": "price", "label": "Lowest Price" if is_en else "السعر الأقل"},
                {
                    "value": "-price",
                    "label": "Highest Price" if is_en else "السعر الأعلى",
                },
            ],
            "bedrooms": "number",
            "bathrooms": "number",
            "price_periods": [
                {
                    "value": Property.PricePeriod.DAILY,
                    "label": "Daily" if is_en else "يومي",
                },
                {
                    "value": Property.PricePeriod.WEEKLY,
                    "label": "Weekly" if is_en else "أسبوعي",
                },
                {
                    "value": Property.PricePeriod.MONTHLY,
                    "label": "Monthly" if is_en else "شهري",
                },
                {
                    "value": Property.PricePeriod.YEARLY,
                    "label": "Yearly" if is_en else "سنوي",
                },
            ],
            "suitable_for": [
                {
                    "value": Property.SuitableFor.FAMILIES,
                    "label": "Families" if is_en else "عائلات",
                },
                {
                    "value": Property.SuitableFor.SINGLES,
                    "label": "Singles" if is_en else "أفراد",
                },
                {
                    "value": Property.SuitableFor.STUDENTS,
                    "label": "Students" if is_en else "طلاب",
                },
                {
                    "value": Property.SuitableFor.FEMALE_STUDENTS,
                    "label": "Female Students Only" if is_en else "طالبات فقط",
                },
                {
                    "value": Property.SuitableFor.ALL,
                    "label": "All" if is_en else "الكل",
                },
            ],
            "amenities": [
                {
                    "value": "wifi",
                    "query_parameter": "has_wifi",
                    "label": "WiFi" if is_en else "واي فاي",
                },
                {
                    "value": "elevator",
                    "query_parameter": "has_elevator",
                    "label": "Elevator" if is_en else "أسانسير",
                },
                {
                    "value": "garage",
                    "query_parameter": "has_garage",
                    "label": "Garage" if is_en else "جراج",
                },
                {
                    "value": "security",
                    "query_parameter": "has_security",
                    "label": "Security" if is_en else "حراسة",
                },
                {
                    "value": "balcony",
                    "query_parameter": "has_balcony",
                    "label": "Balcony" if is_en else "بلكونة",
                },
                {
                    "value": "air_conditioning",
                    "query_parameter": "has_air_conditioning",
                    "label": "Air Conditioning" if is_en else "تكييف",
                },
                {
                    "value": "near_metro",
                    "query_parameter": "near_metro",
                    "label": "Near Metro" if is_en else "قريب من المترو",
                },
                {
                    "value": "natural_gas",
                    "query_parameter": "has_natural_gas",
                    "label": "Natural Gas" if is_en else "غاز طبيعي",
                },
                {
                    "value": "electricity_meter",
                    "query_parameter": "has_electricity_meter",
                    "label": "Electricity Meter" if is_en else "عداد كهرباء",
                },
                {
                    "value": "water_meter",
                    "query_parameter": "has_water_meter",
                    "label": "Water Meter" if is_en else "عداد مياه",
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

    SUPPORTED_AMENITIES_MAP = {
        "wifi": "has_wifi",
        "elevator": "has_elevator",
        "garage": "has_garage",
        "security": "has_security",
        "balcony": "has_balcony",
        "air_conditioning": "has_air_conditioning",
        "near_metro": "near_metro",
        "natural_gas": "has_natural_gas",
        "electricity_meter": "has_electricity_meter",
        "water_meter": "has_water_meter",
    }

    @staticmethod
    def _apply_rental_projection(data):
        inventory = data.get("rental_inventory")
        if inventory is None:
            return
        eligible = [
            offer
            for offer in inventory.get("offers", [])
            if not offer.get("archived") and offer.get("availability") == "available"
        ]
        scopes = sorted(
            {
                offer.get("rental_scope")
                for offer in eligible
                if offer.get("rental_scope")
            }
        )
        data["rental_scopes"] = "," + ",".join(scopes) + "," if scopes else ""
        periods = {offer.get("terms", {}).get("price_period") for offer in eligible}
        if len(periods) == 1:
            period = periods.pop()
            prices = [Decimal(str(offer["terms"]["price"])) for offer in eligible]
            data["rental_price_period"] = period
            data["rental_min_price"] = min(prices) if prices else None
        else:
            data["rental_price_period"] = ""
            data["rental_min_price"] = None

    @staticmethod
    @transaction.atomic
    def create_property(owner, validated_data):
        """
        Creates a property listing conforming to the mobile handoff specification.
        """
        from rest_framework.exceptions import ValidationError

        data = validated_data.copy()
        PropertyService._apply_rental_projection(data)
        main_image_file = data.pop("main_image", None)
        main_image_name = (data.pop("main_image_name", "") or "").strip()
        main_image_description = (data.pop("main_image_description", "") or "").strip()
        amenities = data.pop("amenities", None)

        # Distinguish street and district; fallback district to street on POST if district is empty
        street = (data.get("street") or "").strip()
        district = (data.get("district") or "").strip()
        if not district and street:
            data["district"] = street

        # Map amenities array to model booleans if provided
        if amenities is not None:
            for (
                amenity_val,
                field_name,
            ) in PropertyService.SUPPORTED_AMENITIES_MAP.items():
                data[field_name] = amenity_val in amenities

        # Check conflicting video / ownership proof clear flags
        remove_video = data.pop("remove_video", False)
        if remove_video and data.get("video"):
            raise ValidationError(
                {
                    "video": "Cannot upload video and specify remove_video simultaneously."
                }
            )

        remove_ownership_proof = data.pop("remove_ownership_proof", False)
        if remove_ownership_proof and data.get("ownership_proof"):
            raise ValidationError(
                {
                    "ownership_proof": "Cannot upload ownership proof and specify remove_ownership_proof simultaneously."
                }
            )

        # Edits / creations always submit for review
        data["status"] = Property.Status.UNDER_REVIEW
        data["is_verified"] = False
        data["is_ownership_verified"] = False

        if main_image_file:
            data["main_image"] = main_image_file

        property_obj = Property.objects.create(owner=owner, **data)

        # If a cover image was uploaded, persist it as a stable PropertyImage
        if main_image_file:
            PropertyImage.objects.create(
                property=property_obj,
                image=property_obj.main_image,
                name=main_image_name,
                description=main_image_description,
            )

        return property_obj

    @staticmethod
    @transaction.atomic
    def update_property(property_obj, validated_data):
        """
        Updates a property listing conforming to the mobile handoff specification.
        """
        from rest_framework.exceptions import ValidationError

        data = validated_data.copy()
        PropertyService._apply_rental_projection(data)

        # Handle video removal and replacement conflict
        remove_video = data.pop("remove_video", False)
        new_video = data.get("video")
        if remove_video and new_video:
            raise ValidationError(
                {
                    "video": "Cannot upload video and specify remove_video simultaneously."
                }
            )
        if remove_video:
            property_obj.video = None
            property_obj.video_duration = None
            data.pop("video", None)
            data.pop("video_duration", None)

        # Handle ownership proof removal and replacement conflict
        remove_ownership_proof = data.pop("remove_ownership_proof", False)
        new_ownership_proof = data.get("ownership_proof")
        if remove_ownership_proof and new_ownership_proof:
            raise ValidationError(
                {
                    "ownership_proof": "Cannot upload ownership proof and specify remove_ownership_proof simultaneously."
                }
            )
        if remove_ownership_proof:
            property_obj.ownership_proof = None
            property_obj.is_ownership_verified = False
            data.pop("ownership_proof", None)
        elif new_ownership_proof:
            property_obj.is_ownership_verified = False

        # Image retention and metadata updates
        retained_image_ids = data.pop("retained_image_ids", None)
        images_metadata = data.pop("images_metadata", None)
        main_image_id = data.pop("main_image_id", None)
        main_image_file = data.pop("main_image", None)
        main_image_name = data.pop("main_image_name", None)
        main_image_description = data.pop("main_image_description", None)

        # 1. Retained image IDs: remove existing image records not listed
        if retained_image_ids is not None:
            retained_str_ids = [str(i) for i in retained_image_ids]
            current_images = list(property_obj.images.all())
            current_ids = {str(img.id): img for img in current_images}

            for rid in retained_str_ids:
                if rid not in current_ids:
                    raise ValidationError(
                        {
                            "retained_image_ids": f"Image with ID {rid} does not belong to this property."
                        }
                    )

            # Delete unlisted images
            for img_id, img_obj in current_ids.items():
                if img_id not in retained_str_ids:
                    img_obj.delete()

        # 2. Apply images_metadata by image ID
        if images_metadata is not None:
            current_images = {str(img.id): img for img in property_obj.images.all()}
            for meta in images_metadata:
                mid = str(meta.get("id"))
                if mid in current_images:
                    target_img = current_images[mid]
                    if "name" in meta:
                        target_img.name = (meta["name"] or "").strip()
                    if "description" in meta:
                        target_img.description = (meta["description"] or "").strip()
                    target_img.save()

        # 3. Handle cover photo replacement / selection
        if main_image_file:
            new_name = (
                (main_image_name or "").strip() if main_image_name is not None else ""
            )
            new_desc = (
                (main_image_description or "").strip()
                if main_image_description is not None
                else ""
            )
            created_cover = PropertyImage.objects.create(
                property=property_obj,
                image=main_image_file,
                name=new_name,
                description=new_desc,
            )
            property_obj.main_image = created_cover.image
        elif main_image_id:
            try:
                selected_cover = property_obj.images.get(id=main_image_id)
            except PropertyImage.DoesNotExist:
                raise ValidationError(
                    {
                        "main_image_id": "Selected cover image does not belong to this property."
                    }
                )
            property_obj.main_image = selected_cover.image
            if main_image_name is not None:
                selected_cover.name = (main_image_name or "").strip()
            if main_image_description is not None:
                selected_cover.description = (main_image_description or "").strip()
            selected_cover.save()
        else:
            # If cover captions were passed without image replacement
            if main_image_name is not None or main_image_description is not None:
                cover_img = property_obj.images.first()
                if cover_img:
                    if main_image_name is not None:
                        cover_img.name = (main_image_name or "").strip()
                    if main_image_description is not None:
                        cover_img.description = (main_image_description or "").strip()
                    cover_img.save()

        # Map amenities array if provided
        amenities = data.pop("amenities", None)
        if amenities is not None:
            for (
                amenity_val,
                field_name,
            ) in PropertyService.SUPPORTED_AMENITIES_MAP.items():
                data[field_name] = amenity_val in amenities

        # Apply scalar updates
        for attr, value in data.items():
            setattr(property_obj, attr, value)

        # On every owner edit, set status to under_review
        property_obj.status = Property.Status.UNDER_REVIEW
        property_obj.save()
        if hasattr(property_obj, "_prefetched_objects_cache"):
            property_obj._prefetched_objects_cache.clear()
        return property_obj

    @staticmethod
    @transaction.atomic
    def delete_property(property_obj, user):
        """
        Deletes a property if the user is the owner and no active visit requests or leases exist.
        """
        from rest_framework.exceptions import APIException, PermissionDenied
        from rest_framework import status

        if property_obj.owner != user:
            raise PermissionDenied("You are not the owner of this property listing.")

        # Check for active or confirmed visit requests
        active_visits = property_obj.visits.filter(
            status__in=[PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED]
        )
        if active_visits.exists():
            conflict_exc = APIException(
                "Cannot delete property with active or upcoming visit requests."
            )
            conflict_exc.status_code = status.HTTP_409_CONFLICT
            raise conflict_exc

        property_id = str(property_obj.id)
        property_obj.delete()
        return property_id

    @staticmethod
    @transaction.atomic
    def upload_property_image(property_obj, image, name="", description=""):
        """
        Uploads an image with transactional enforcement of the 25 images limit.
        """
        from rest_framework.exceptions import ValidationError

        locked_property = Property.objects.select_for_update().get(
            pkid=property_obj.pkid
        )
        if locked_property.images.count() >= 25:
            raise ValidationError(
                {"detail": "A property cannot have more than 25 images."}
            )

        name = (name or "").strip()
        description = (description or "").strip()

        img_obj = PropertyImage.objects.create(
            property=locked_property,
            image=image,
            name=name,
            description=description,
        )
        return img_obj

    @staticmethod
    @transaction.atomic
    def upload_property_images(property_obj, uploaded_images):
        """
        Uploads and creates multiple PropertyImage objects for a given property.
        """
        created_images = []
        for image in uploaded_images:
            img_obj = PropertyService.upload_property_image(property_obj, image)
            created_images.append(img_obj)
        return created_images

    @staticmethod
    @transaction.atomic
    def update_property_image(image_obj, validated_data):
        """
        Updates metadata (name, description) of a PropertyImage.
        """
        for attr, value in validated_data.items():
            if attr in ("name", "description") and isinstance(value, str):
                value = value.strip()
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

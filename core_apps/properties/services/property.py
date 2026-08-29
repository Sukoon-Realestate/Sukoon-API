from django.db import transaction
from django.db.models import Q

from ..models import Property, PropertyImage, PropertyType


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

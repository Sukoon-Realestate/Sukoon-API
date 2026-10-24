"""PropertyCatalog operations owned by PropertyService."""

from typing import Optional
from django.db.models import Q
from ...models import Property, PropertyType


class PropertyCatalogMixin:
    @classmethod
    def get_filter_options(cls, language: Optional[str] = None):
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
                        else cls.PROPERTY_TYPE_LABELS.get(
                            property_type.slug, property_type.name
                        )
                    ),
                }
                for property_type in property_types
            ],
            "ordering": [
                {"value": "relevance", "label": "Most relevant" if is_en else "الأكثر صلة"},
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

    @classmethod
    def get_available_places(cls, property_type):
        """Return distinct locations for approved properties of a given type."""
        places = (
            Property.objects.filter(
                property_type=property_type,
                retired_at=None,
            )
            .filter(status=Property.Status.VERIFIED)
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

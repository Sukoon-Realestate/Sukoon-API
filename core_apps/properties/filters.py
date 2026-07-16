import django_filters

from .models import Property


class PropertyFilter(django_filters.FilterSet):
    """
    Filter class for Property listings.

    Supported filters:
    - property_type (e.g. ?property_type=apartment)
    - price_period (e.g. ?price_period=monthly)
    - is_furnished (e.g. ?is_furnished=true)
    - is_verified (e.g. ?is_verified=true)
    - bedrooms (e.g. ?bedrooms=3)
    - bathrooms (e.g. ?bathrooms=2)
    - suitable_for (e.g. ?suitable_for=families)
    - smoking_allowed (e.g. ?smoking_allowed=false)
    - has_wifi (e.g. ?has_wifi=true)
    - has_elevator (e.g. ?has_elevator=true)
    - has_garage (e.g. ?has_garage=true)
    - has_security (e.g. ?has_security=true)
    - has_balcony (e.g. ?has_balcony=true)
    - has_air_conditioning (e.g. ?has_air_conditioning=true)
    - near_metro (e.g. ?near_metro=true)
    - has_natural_gas (e.g. ?has_natural_gas=true)
    - price_min (e.g. ?price_min=1000)
    - price_max (e.g. ?price_max=10000)
    """

    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    class Meta:
        model = Property
        fields = [
            "property_type",
            "price_period",
            "is_furnished",
            "is_verified",
            "bedrooms",
            "bathrooms",
            "suitable_for",
            "smoking_allowed",
            "has_wifi",
            "has_elevator",
            "has_garage",
            "has_security",
            "has_balcony",
            "has_air_conditioning",
            "near_metro",
            "has_natural_gas",
        ]

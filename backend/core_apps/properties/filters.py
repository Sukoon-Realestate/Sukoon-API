import django_filters
from rest_framework.filters import OrderingFilter

from .models import Property, PropertyVisit, PropertyType


class DistrictIdsFilter(django_filters.BaseInFilter, django_filters.UUIDFilter):
    pass


class PropertyFilter(django_filters.FilterSet):
    """
    Filter class for Property listings.

    Supported filters:
    - property_type (e.g. ?property_type=apartment) — filters by PropertyType slug
    - price_period (e.g. ?price_period=monthly)
    - is_furnished (e.g. ?is_furnished=true)
    - is_verified (e.g. ?is_verified=true)
    - bedrooms (e.g. ?bedrooms=3)
    - bedrooms_min (e.g. ?bedrooms_min=4) — useful for the "4+" option
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

    property_type = django_filters.CharFilter(field_name="property_type__slug")
    governorate = django_filters.UUIDFilter(field_name="governorate__id")
    city = django_filters.UUIDFilter(field_name="city__id")
    district_ids = DistrictIdsFilter(
        field_name="district_catalog__id", lookup_expr="in"
    )
    price_min = django_filters.NumberFilter(method="filter_price_min")
    price_max = django_filters.NumberFilter(method="filter_price_max")
    price_period = django_filters.CharFilter(method="filter_price_period")
    bedrooms_min = django_filters.NumberFilter(field_name="bedrooms", lookup_expr="gte")
    rental_scope = django_filters.CharFilter(method="filter_rental_scope")

    @property
    def student_search(self):
        return (
            self.data.get("student_search") == "true"
            or "rental_search_version" in self.data
        )

    def filter_price_min(self, queryset, name, value):
        return queryset if self.student_search else queryset.filter(price__gte=value)

    def filter_price_max(self, queryset, name, value):
        return queryset if self.student_search else queryset.filter(price__lte=value)

    def filter_price_period(self, queryset, name, value):
        return queryset if self.student_search else queryset.filter(price_period=value)

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        if self.student_search:
            from core_apps.features.services.student_housing.discovery import (
                filter_properties,
            )

            queryset = filter_properties(queryset, self.data, self.request)
        return queryset

    def filter_rental_scope(self, queryset, name, value):
        if value not in {"entire_property", "room", "room_group", "bed"}:
            return queryset.none()
        return (
            queryset
            if self.student_search
            else queryset.filter(rental_scopes__contains=f",{value},")
        )

    class Meta:
        model = Property
        fields = [
            "property_type",
            "governorate",
            "city",
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


class PropertyVisitFilter(django_filters.FilterSet):
    """
    Filter class for PropertyVisit listings.

    Supported filters:
    - status (e.g. ?status=pending) — one of: pending, confirmed, canceled, rejected
    """

    class Meta:
        model = PropertyVisit
        fields = ["status"]


class PropertyOrderingFilter(OrderingFilter):
    """Student budgets and ordering use the same matched-offer price basis."""

    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        if (
            request.query_params.get("student_search") == "true"
            or "rental_search_version" in request.query_params
        ) and ordering:
            return [
                (
                    "student_comparison_price"
                    if key == "price"
                    else "-student_comparison_price" if key == "-price" else key
                )
                for key in ordering
            ] + ["pk"]
        return ordering

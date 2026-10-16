"""Bounded, typed asset facts and explicitly inheritable unit defaults."""

from rest_framework import serializers
from decimal import Decimal


class Fields(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError("Unsupported fields.")
        return super().to_internal_value(data)


class UnitDefaults(Fields):
    is_furnished = serializers.BooleanField(required=False)
    smoking_allowed = serializers.BooleanField(required=False, allow_null=True)
    has_wifi = serializers.BooleanField(required=False)
    has_elevator = serializers.BooleanField(required=False)
    has_garage = serializers.BooleanField(required=False)
    has_security = serializers.BooleanField(required=False)
    has_air_conditioning = serializers.BooleanField(required=False)
    has_natural_gas = serializers.BooleanField(required=False)
    has_electricity_meter = serializers.BooleanField(required=False)
    has_water_meter = serializers.BooleanField(required=False)
    district = serializers.CharField(max_length=100, required=False)
    street = serializers.CharField(max_length=255, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False)


class UnitChanges(UnitDefaults):
    bedrooms = serializers.IntegerField(min_value=0, max_value=100, required=False)
    bathrooms = serializers.IntegerField(min_value=0, max_value=100, required=False)
    area = serializers.IntegerField(min_value=1, max_value=100000, required=False)
    floor = serializers.IntegerField(
        min_value=-20, max_value=200, required=False, allow_null=True
    )
    occupancy_capacity = serializers.IntegerField(
        min_value=1, max_value=1000, required=False, allow_null=True
    )


class UtilityArrangements(Fields):
    water = serializers.CharField(max_length=500, required=False, allow_blank=True)
    electricity = serializers.CharField(
        max_length=500, required=False, allow_blank=True
    )
    internet = serializers.CharField(max_length=500, required=False, allow_blank=True)
    laundry = serializers.CharField(max_length=500, required=False, allow_blank=True)


class AssetFacts(Fields):
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-90"),
        max_value=Decimal("90"),
        allow_null=True,
        required=False,
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        min_value=Decimal("-180"),
        max_value=Decimal("180"),
        allow_null=True,
        required=False,
    )
    elevators = serializers.IntegerField(
        min_value=0, max_value=100, allow_null=True, required=False
    )
    parking_spaces = serializers.IntegerField(
        min_value=0, max_value=10000, allow_null=True, required=False
    )
    accessibility = serializers.CharField(
        max_length=2000, allow_blank=True, required=False
    )
    utilities = UtilityArrangements(required=False)
    included_services = serializers.ListField(
        child=serializers.CharField(max_length=300), max_length=30, required=False
    )
    public_access = serializers.CharField(
        max_length=2000, allow_blank=True, required=False
    )
    private_access = serializers.CharField(
        max_length=2000, allow_blank=True, required=False
    )
    contact_name = serializers.CharField(
        max_length=200, allow_blank=True, required=False
    )
    contact_phone = serializers.CharField(
        max_length=40, allow_blank=True, required=False
    )
    unit_defaults = UnitDefaults(required=False)

    def validate(self, data):
        if (data.get("latitude") is None) != (data.get("longitude") is None):
            raise serializers.ValidationError(
                "Provide both map coordinates or clear both."
            )
        return data

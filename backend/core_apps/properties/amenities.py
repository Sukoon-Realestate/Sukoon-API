"""Public amenity names and their persisted property fields."""

AMENITY_FIELDS = {
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


def property_amenities(prop):
    return sorted(name for name, field in AMENITY_FIELDS.items() if getattr(prop, field, False))

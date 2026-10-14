from typing import Optional
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.models import Avg, Count, FloatField, Q
from django.db.models.functions import Coalesce
from django.utils import timezone

from core_apps.common.models import ContentView

from ..models import Property, PropertyImage, PropertyType, PropertyVisit


from .property_operations.property_catalog import PropertyCatalogMixin
from .property_operations.property_creation import PropertyCreationMixin
from .property_operations.property_update import PropertyUpdateMixin
from .property_operations.property_media import PropertyMediaMixin
from .property_operations.property_lifecycle import PropertyLifecycleMixin
from .property_operations.property_statistics import PropertyStatisticsMixin


class PropertyService(
    PropertyCatalogMixin,
    PropertyCreationMixin,
    PropertyUpdateMixin,
    PropertyMediaMixin,
    PropertyLifecycleMixin,
    PropertyStatisticsMixin,
):
    """Public service dispatch with domain-specific responsibilities."""

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

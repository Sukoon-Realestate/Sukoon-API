"""Stable public imports for property.

Implementation modules separate domain responsibilities without changing routes.
"""

import json
from typing import Optional
from django.utils import timezone
from rest_framework import serializers
from core_apps.profiles.serializers import CloudinarySerializerField
from ..models import City, Governorate, Property, PropertyImage, PropertyType
from ..phone_disclosure import counterpart_phone_payload
from .location import CitySerializer, GovernorateSerializer, PublicUUIDRelatedField
from ..services import PropertyService
from ..rental_inventory import normalize_inventory

from .property_parts.property_list_serializer import (
    CloudinaryMediaField,
    PropertyTypeSerializer,
    PropertyImageSerializer,
    PropertyImageUploadSerializer,
    PropertyImageUpdateSerializer,
    build_rental_summary,
    PropertyListSerializer,
)
from .property_parts.property_new_list_serializer import (
    PropertyNewListSerializer,
    MyPropertyListSerializer,
    PropertyDetailOwnerSerializer,
)
from .property_parts.property_detail_serializer import (
    PropertyDetailSerializer,
)
from .property_parts.property_serializer import (
    PropertySerializer,
)
from .property_parts.property_statistics_serializer import (
    AvailablePlacesQuerySerializer,
    DailyViewSerializer,
    TopSearchCriterionSerializer,
    PropertyStatisticsSerializer,
    PropertyVisibilitySerializer,
)

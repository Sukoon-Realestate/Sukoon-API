from ..amenities import AMENITY_FIELDS
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

    SUPPORTED_AMENITIES_MAP = AMENITY_FIELDS

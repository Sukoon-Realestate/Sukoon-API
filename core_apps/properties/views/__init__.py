from .owner_dashboard import OwnerDashboardAPIView
from .property import (
    AvailablePlacesAPIView,
    MyPropertyListAPIView,
    PropertyCreateAPIView,
    PropertyDeleteAPIView,
    PropertyDetailAPIView,
    PropertyImageDetailAPIView,
    PropertyImageUploadAPIView,
    PropertyListAPIView,
    PropertyNewListAPIView,
    PropertyTypeListAPIView,
    PropertyUpdateAPIView,
)
from .visit import (
    PropertyAvailableDatesAPIView,
    PropertyVisitCreateAPIView,
    TenantPropertyVisitListAPIView,
    OwnerPropertyVisitListAPIView,
    PropertyVisitDetailAPIView,
    PropertyVisitUpdateAPIView,
)

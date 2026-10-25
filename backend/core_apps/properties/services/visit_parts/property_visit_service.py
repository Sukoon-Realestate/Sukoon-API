"""Visit: property visit service."""

from datetime import date, datetime, time, timedelta
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied, ValidationError
from ...models import (
    OwnerAvailabilitySlot,
    PropertyRating,
    PropertyVisit,
    PropertyVisitReview,
)
from .logger import logger


from .property_visit_service_operations.visit_booking import VisitBookingMixin
from .property_visit_service_operations.visit_decision import VisitDecisionMixin
from .property_visit_service_operations.visit_review import VisitReviewMixin


class PropertyVisitService(
    VisitBookingMixin,
    VisitDecisionMixin,
    VisitReviewMixin,
):
    """Public service dispatch with domain-specific responsibilities."""

    BOOKED_STATUSES = (PropertyVisit.Status.PENDING, PropertyVisit.Status.CONFIRMED)

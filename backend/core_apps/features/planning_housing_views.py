"""Stable public imports for planning housing views.

Implementation modules separate domain responsibilities without changing routes.
"""

from datetime import timedelta
from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from .planning_models import HousingOffer, HousingRequest
from .services.planning import (
    check_revision,
    criteria,
    criteria_payload,
    eligible_owner,
    money,
    mutate,
    offer_money,
    page,
    planning_api,
    public_properties,
    selection,
    text_field,
)
from .services.rental_phase2 import RentalConflict

from .planning_housing_views_parts.housing_requests import (
    request_status,
    can_read_request,
    get_request,
    request_actions,
    request_payload,
    _request_values,
    housing_requests,
    housing_demand,
    housing_request_detail,
    housing_request_changes,
)
from .planning_housing_views_parts.housing_request_action import (
    housing_request_action,
    offer_status,
    offer_actions,
    offer_payload,
    get_offer,
)
from .planning_housing_views_parts.housing_offers import (
    housing_offers,
    housing_offer_action,
    housing_offer_detail,
)
from .planning_housing_views_parts.owner_housing_offers import (
    owner_housing_offers,
)

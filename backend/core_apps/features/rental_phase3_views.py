"""Stable public imports for rental phase3 views.

Implementation modules separate domain responsibilities without changing routes.
"""

import hashlib
import json
import secrets
import uuid
from datetime import timedelta
from urllib.parse import urlparse
from django.conf import settings
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    renderer_classes,
    throttle_classes,
)
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from .models import (
    CheckoutSession,
    Lease,
    IdempotencyRecord,
    OwnerPayable,
    PaymentAttempt,
    PaymentQuote,
    ProviderWebhookEvent,
    RentInvoice,
)
from .providers import (
    mock_completion_metadata,
    checkout_available,
    fake_provider_available,
    get_rental_provider,
    verify_fake_webhook,
)
from .renderers import FeatureJsonRenderer
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase3 import (
    invoice_balance_minor,
    invoice_payment_allowed,
    payment_attempt_payload,
    process_provider_event,
    quote_fingerprint,
)

from .rental_phase3_views_parts.rent_invoice_quote import (
    PaymentReconcileThrottle,
    _money,
    _invoice,
    _attempt,
    _active_session,
    quote_payload,
    rent_invoice_quote,
)
from .rental_phase3_views_parts.owner_payables import (
    _validated_navigation,
    payment_attempts,
    payment_attempt_detail,
    payment_attempt_reconcile,
    owner_payables,
    apply_fake_payment_event,
)
from .rental_phase3_views_parts.rent_invoice_checkout import (
    rent_invoice_checkout,
    fake_payment_webhook,
)

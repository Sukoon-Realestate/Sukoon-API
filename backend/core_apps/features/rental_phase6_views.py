"""Stable public imports for rental phase6 views.

Implementation modules separate domain responsibilities without changing routes.
"""

import uuid
from datetime import timedelta
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from core_apps.admin_api.models import StaffProfile
from .models import (
    DepositAgreement,
    FinalSettlement,
    Lease,
    MaintenanceRequest,
    PaymentAttempt,
    PrivateAccessRevocation,
    RefundRequest,
    RentalChange,
    RentalDispute,
    RentalDocument,
    RentalEvidence,
    RentalHandover,
    RentalPayout,
    RentalReview,
    RentInvoice,
)
from .providers import (
    fake_provider_available,
    get_rental_provider,
    require_rental_provider,
)
from .renderers import FeatureJsonRenderer
from .services.cycle_permissions import cycle_actions
from .services.commands import command_identity, money_minor
from .services.refunds import validate_allocations
from .services.settlements import (
    LINE_TYPES,
    execute_settlement,
    financial_snapshot,
    prepare_settlement,
)
from .services.rental_phase2 import RentalConflict, remember_mutation, replay_operation
from .services.rental_phase6 import (
    closure_blocking_reasons,
    evaluate_financial_closure,
    refundable_balance_minor,
    settlement_balances,
)

from .rental_phase6_views_parts.final_settlement_propose import (
    _money,
    _lease,
    settlement_payload,
    _settlement,
    final_settlement_detail,
    final_settlement_propose,
)
from .rental_phase6_views_parts.final_settlement_respond import (
    final_settlement_respond,
    refund_payload,
    _refund,
)
from .rental_phase6_views_parts.refund_requests import (
    refund_requests,
    refund_detail,
    refund_respond,
)
from .rental_phase6_views_parts.refund_execute import (
    SUBJECT_MODELS,
    refund_execute,
    dispute_payload,
    _dispute,
)
from .rental_phase6_views_parts.disputes import (
    disputes,
    dispute_detail,
    dispute_respond,
    document_payload,
)
from .rental_phase6_views_parts.lease_reviews import (
    lease_documents,
    document_download,
    rental_statement_create,
    review_payload,
    lease_reviews,
)
from .rental_phase6_views_parts.rental_center import (
    rental_center,
)

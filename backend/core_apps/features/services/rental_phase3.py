"""Stable public imports for rental phase3.

Implementation modules separate domain responsibilities without changing routes.
"""

import hashlib
import json
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from ..models import (
    BillingPeriod,
    DepositAgreement,
    InvoiceLine,
    InvoicePaymentAllocation,
    LedgerEntry,
    LedgerTransaction,
    Lease,
    OwnerPayable,
    PaymentAttempt,
    PaymentReceipt,
    ProviderWebhookEvent,
    RentInvoice,
    RefundRequest,
    RentalChange,
    RentalTimelineEvent,
)
from .rental_phase2 import (
    RentalConflict,
    activate_inventory,
    add_months,
    assert_owner_ready,
)

from .rental_phase3_parts.issue_invoice import (
    CAIRO,
    cairo_instant,
    post_ledger_transaction,
    issue_invoice,
    generate_billing_schedule,
)
from .rental_phase3_parts.payment_attempt_payload import (
    invoice_balance_minor,
    invoice_payment_allowed,
    quote_fingerprint,
    payment_attempt_payload,
)
# Supported private imports stay outside the public star-import surface.
from .rental_phase3_parts.payment_attempt_payload import (  # noqa: F401
    _activate_after_initial_capture,
)
# Supported private imports stay outside the public star-import surface.
from .rental_phase3_parts.capture_attempt import (  # noqa: F401
    _capture_attempt,
)
from .rental_phase3_parts.process_provider_event import (
    process_provider_event,
)
# Supported private imports stay outside the public star-import surface.
from .rental_phase3_parts.process_provider_event import (  # noqa: F401
    _settle_attempt,
)

# Preserve the existing public import surface, including compatibility seams.
__all__ = [
    'hashlib',
    'json',
    'datetime',
    'time',
    'timedelta',
    'ZoneInfo',
    'transaction',
    'Sum',
    'timezone',
    'ValidationError',
    'BillingPeriod',
    'DepositAgreement',
    'InvoiceLine',
    'InvoicePaymentAllocation',
    'LedgerEntry',
    'LedgerTransaction',
    'Lease',
    'OwnerPayable',
    'PaymentAttempt',
    'PaymentReceipt',
    'ProviderWebhookEvent',
    'RentInvoice',
    'RefundRequest',
    'RentalChange',
    'RentalTimelineEvent',
    'RentalConflict',
    'activate_inventory',
    'add_months',
    'assert_owner_ready',
    'CAIRO',
    'cairo_instant',
    'post_ledger_transaction',
    'issue_invoice',
    'generate_billing_schedule',
    'invoice_balance_minor',
    'invoice_payment_allowed',
    'quote_fingerprint',
    'payment_attempt_payload',
    'process_provider_event',
]

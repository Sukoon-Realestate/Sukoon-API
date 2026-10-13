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
    _activate_after_initial_capture,
)
from .rental_phase3_parts.capture_attempt import (
    _capture_attempt,
)
from .rental_phase3_parts.process_provider_event import (
    _settle_attempt,
    process_provider_event,
)

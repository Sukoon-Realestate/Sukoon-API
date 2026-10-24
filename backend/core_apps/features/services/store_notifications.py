"""Verified store events maintain recurring invoices and current entitlements.

The configured adapter authenticates the notification and queries the provider's
current state before returning this value. An arbitrary webhook body grants nothing.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from rest_framework.exceptions import APIException
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from ..models import (
    AccountSubscription,
    InvoiceLine,
    PaymentAttempt,
    PaymentQuote,
    RentInvoice,
    StoreAccount,
    StoreNotification,
    StoreProduct,
    StorePurchaseIntent,
    StoreSubscriptionHead,
    StoreTransaction,
)
from .store_payments import (
    VerifiedPurchase,
    StoreUnavailable,
    adapter,
    environment,
    record_purchase,
    review_purchase,
)
from .rental_phase2 import RentalConflict


@dataclass(frozen=True)
class VerifiedStoreEvent:
    event_id: str
    purchase: VerifiedPurchase
    # Provider's trusted current-state timestamp, not client/event arrival time.
    observed_at: datetime
    status: str
    grace_ends_at: datetime | None = None


def handle_notification(platform, payload, headers):
    verifier = adapter(platform)
    if not hasattr(verifier, "verify_notification"):
        raise StoreUnavailable()
    try:
        event = verifier.verify_notification(payload, headers=headers)
    except APIException:
        raise
    except Exception:
        raise StoreUnavailable() from None
    if (
        not isinstance(event, VerifiedStoreEvent)
        or event.status
        not in {"active", "grace", "billing_retry", "hold", "expired", "revoked"}
        or not event.event_id
    ):
        raise StoreUnavailable()
    digest = hashlib.sha256(payload).hexdigest()
    try:
        return record_notification(platform, digest, event)
    except APIException as exc:
        account = (
            StoreAccount.objects.select_related("user")
            .filter(
                platform=platform,
                environment=environment(),
                app_account_token=event.purchase.app_account_token,
            )
            .first()
        )
        if account:
            review_purchase(account.user, event.purchase, digest, str(exc.get_codes()))
        raise


@transaction.atomic
def record_notification(platform, digest, event):
    purchase = event.purchase
    account = (
        StoreAccount.objects.select_related("user")
        .filter(
            platform=platform,
            environment=environment(),
            app_account_token=purchase.app_account_token,
        )
        .first()
    )
    if not account or purchase.environment != account.environment:
        raise RentalConflict(
            "The store account requires investigation.", code="store_account_mismatch"
        )
    get_user_model().objects.select_for_update().get(pk=account.user_id)
    existing = StoreNotification.objects.filter(
        platform=platform, environment=account.environment, event_id=event.event_id
    ).first()
    if existing:
        if existing.account_id != account.pk or existing.payload_digest != digest:
            raise RentalConflict(
                "Store event identity conflict.", code="idempotency_conflict"
            )
        return {"recorded": True}
    head = (
        StoreSubscriptionHead.objects.select_for_update()
        .filter(
            account=account, original_transaction_id=purchase.original_transaction_id
        )
        .first()
    )
    notification = StoreNotification.objects.create(
        platform=platform,
        environment=account.environment,
        event_id=event.event_id,
        account=account,
        payload_digest=digest,
    )
    if head and event.observed_at <= head.observed_at:
        notification.processed_at = timezone.now()
        notification.save(update_fields=["processed_at", "updated_at"])
        return {"recorded": True}
    original = (
        StoreTransaction.objects.filter(
            platform=platform,
            environment=account.environment,
            original_transaction_id=purchase.original_transaction_id,
        )
        .select_related("intent__account", "intent__attempt__invoice")
        .order_by("created_at")
        .first()
    )
    if original and original.intent.account_id != account.pk:
        raise RentalConflict(
            "The original purchase belongs to another account.",
            code="store_account_mismatch",
        )
    current = (
        StoreTransaction.objects.filter(
            platform=platform,
            environment=account.environment,
            transaction_id=purchase.transaction_id,
        )
        .select_related("intent__attempt__invoice")
        .first()
    )
    if current and (
        current.intent.account_id != account.pk
        or current.original_transaction_id != purchase.original_transaction_id
        or current.intent.route_snapshot["product_id"] != purchase.product_id
    ):
        raise RentalConflict(
            "The transaction belongs to another account.", code="store_account_mismatch"
        )
    if current is None:
        if original is None:
            # A notification can complete the first original pending checkout.
            record_purchase(
                account.user,
                {"platform": platform, "product_id": purchase.product_id},
                digest,
                purchase,
            )
            current = StoreTransaction.objects.select_related(
                "intent__attempt__invoice"
            ).get(
                platform=platform,
                environment=account.environment,
                transaction_id=purchase.transaction_id,
            )
        else:
            current = record_renewal(account, original, purchase, digest)
    subscription = AccountSubscription.objects.select_for_update().get(
        invoice=current.intent.attempt.invoice
    )
    subscription.store_status = event.status
    subscription.auto_renew = purchase.auto_renew
    subscription.grace_ends_at = (
        event.grace_ends_at if event.status == "grace" else None
    )
    subscription.save(
        update_fields=["store_status", "auto_renew", "grace_ends_at", "updated_at"]
    )
    if head:
        head.observed_at = event.observed_at
        head.save(update_fields=["observed_at", "updated_at"])
    else:
        StoreSubscriptionHead.objects.create(
            account=account,
            original_transaction_id=purchase.original_transaction_id,
            observed_at=event.observed_at,
        )
    notification.processed_at = timezone.now()
    notification.save(update_fields=["processed_at", "updated_at"])
    return {"recorded": True}


def record_renewal(account, original, purchase, digest):
    """Provider-created obligation; it never needs a new open mobile checkout."""
    if purchase.state != "purchased" or purchase.expires_at <= purchase.purchased_at:
        raise RentalConflict(
            "The recurring purchase is unresolved.", code="outcome_unknown"
        )
    old_invoice = original.intent.attempt.invoice
    product = (
        StoreProduct.objects.select_related("plan")
        .filter(
            platform=account.platform,
            environment=account.environment,
            product_id=purchase.product_id,
        )
        .first()
    )
    if not product or (product.plan.audience == "organization") != bool(
        old_invoice.organization_id
    ):
        raise RentalConflict(
            "The recurring product requires investigation.",
            code="purchase_route_unavailable",
        )
    if (purchase.amount_minor, purchase.currency, purchase.exponent) != (
        product.amount_minor,
        product.currency,
        product.exponent,
    ) or (product.plan.amount_minor, product.plan.currency, product.plan.exponent) != (
        purchase.amount_minor,
        purchase.currency,
        purchase.exponent,
    ):
        raise RentalConflict(
            "The recurring price requires reconciliation.", code="store_price_mismatch"
        )
    from .billing_catalog import plan_snapshot
    from .billing_settlement import settle_purchase
    from .rental_phase3 import quote_fingerprint

    snapshot = plan_snapshot(product.plan)
    # Membership changes do not transfer an organization's existing subscription.
    # Store-originated renewal follows the original agreement, never a new employee.
    if old_invoice.organization_id:
        from ..models import Company

        Company.objects.select_for_update().get(pk=old_invoice.organization_id)
    subscriptions = AccountSubscription.objects.filter(
        **(
            {"organization_id": old_invoice.organization_id}
            if old_invoice.organization_id
            else {"user": account.user, "organization__isnull": True}
        ),
        workspace__in=[old_invoice.workspace, "both"],
        store_status__in=["", "active", "grace"],
        ends_at__gt=timezone.now(),
    )
    for previous in subscriptions:
        if previous.ends_at > purchase.purchased_at:
            raise RentalConflict(
                "Overlapping subscription periods require reconciliation.",
                code="outcome_unknown",
            )
        previous.store_status = "expired"
        previous.save(update_fields=["store_status", "updated_at"])
    invoice = RentInvoice.objects.create(
        purpose="subscription",
        payer=account.user,
        organization_id=old_invoice.organization_id,
        workspace=old_invoice.workspace,
        reference=f"INV-{uuid.uuid4().hex[:20].upper()}",
        business_reference=f"store-renewal:{uuid.uuid5(uuid.NAMESPACE_URL, account.platform + ':' + account.environment + ':' + purchase.transaction_id)}",
        amount_minor=purchase.amount_minor,
        charges_minor=purchase.amount_minor,
        currency=purchase.currency,
        exponent=purchase.exponent,
        due_date=purchase.purchased_at.date(),
        purchase_snapshot=snapshot,
    )
    InvoiceLine.objects.create(
        invoice=invoice,
        line_type="subscription",
        description=snapshot["name_en"],
        amount_minor=invoice.amount_minor,
        currency=invoice.currency,
        exponent=invoice.exponent,
        source={"description_ar": snapshot["name_ar"], "quantity": 1},
    )
    key = uuid.uuid5(invoice.id, purchase.transaction_id)
    mode = "storekit" if account.platform == "ios" else "play_billing"
    route = {
        "contract_version": 1,
        "route": mode,
        "product_type": "subscription",
        "product_id": purchase.product_id,
        "enabled": True,
        "message": "",
    }
    quote = PaymentQuote.objects.create(
        invoice=invoice,
        request_key=key,
        invoice_revision=1,
        payer_amount_minor=invoice.amount_minor,
        currency=invoice.currency,
        exponent=invoice.exponent,
        policy_version="store-renewal-v1",
        purchase_route=route,
        fingerprint=quote_fingerprint(
            invoice, key, invoice.amount_minor, purchase.expires_at
        ),
        expires_at=purchase.expires_at,
    )
    attempt = PaymentAttempt.objects.create(
        invoice=invoice,
        payer=account.user,
        quote=quote,
        request_key=key,
        invoice_revision=1,
        amount_minor=invoice.amount_minor,
        currency=invoice.currency,
        exponent=invoice.exponent,
        policy_version=quote.policy_version,
        quote_fingerprint=quote.fingerprint,
    )
    intent = StorePurchaseIntent.objects.create(
        account=account,
        product=product,
        attempt=attempt,
        route_snapshot=route,
        expires_at=purchase.expires_at,
    )
    result = StoreTransaction.objects.create(
        intent=intent,
        platform=account.platform,
        environment=account.environment,
        transaction_id=purchase.transaction_id,
        original_transaction_id=purchase.original_transaction_id,
        proof_digest=digest,
        verified_at=timezone.now(),
    )
    settle_purchase(
        invoice, attempt, purchase.transaction_id, provider_mode=mode, verified=purchase
    )
    intent.fulfilled_at = timezone.now()
    intent.save(update_fields=["fulfilled_at", "updated_at"])
    return result

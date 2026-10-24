"""Store boundary: only a configured server-to-server verifier can confirm money.

Adapters must verify signatures/source, bundle/package, environment, account binding
and current store state. Never return a result derived solely from the client proof.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.module_loading import import_string
from rest_framework.exceptions import APIException, ValidationError
from ..models import (
    StoreAccount,
    StoreProduct,
    StorePurchaseIntent,
    StoreTransaction,
    PaymentAttempt,
)
from .rental_phase2 import RentalConflict


class StoreUnavailable(APIException):
    status_code = 503
    default_detail = "Store verification is unavailable."
    default_code = "provider_unavailable"


@dataclass(frozen=True)
class VerifiedPurchase:
    transaction_id: str
    original_transaction_id: str
    product_id: str
    app_account_token: str
    environment: str
    amount_minor: int
    currency: str
    exponent: int
    purchased_at: datetime
    expires_at: datetime
    state: str = "purchased"
    auto_renew: bool = True


def environment():
    value = getattr(settings, "COMMERCE_STORE_ENVIRONMENT", "sandbox")
    if value not in {"sandbox", "live"}:
        raise StoreUnavailable()
    return value


def adapter(platform):
    path = getattr(settings, "COMMERCE_STORE_ADAPTERS", {}).get(platform)
    if not path:
        raise StoreUnavailable()
    return import_string(path)()


def product_route(plan, platform):
    mode = "storekit" if platform == "ios" else "play_billing"
    product = StoreProduct.objects.filter(
        plan=plan, platform=platform, environment=environment(), active=True
    ).first()
    configured = bool(
        getattr(settings, "COMMERCE_STORE_PURCHASES_ENABLED", False)
        and getattr(settings, "COMMERCE_STORE_ADAPTERS", {}).get(platform)
    )
    matching = product and (
        product.amount_minor,
        product.currency,
        product.exponent,
        product.period_months,
    ) == (plan.amount_minor, plan.currency, plan.exponent, plan.period_months)
    enabled = bool(
        plan.active
        and plan.audience == "personal"
        and plan.period_months in {1, 12}
        and configured
        and matching
    )
    return {
        "contract_version": 1,
        "category": "digital_purchase",
        "route": mode if enabled else "disabled",
        "required_route": mode,
        "enabled": enabled,
        "product_id": product.product_id if product else "",
        "product_type": "subscription",
        "external_checkout_allowed": False,
        "reason": (
            ""
            if enabled
            else (
                "organization_commerce_policy_not_configured"
                if plan.audience == "organization"
                else (
                    "store_price_mismatch"
                    if product and not matching
                    else "store_product_and_receipt_verification_not_configured"
                )
            )
        ),
        "message": "" if enabled else "Store purchases are unavailable.",
    }


@transaction.atomic
def account_context(user, platform):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    account, _ = StoreAccount.objects.get_or_create(
        user=user, platform=platform, environment=environment()
    )
    enabled = bool(
        getattr(settings, "COMMERCE_STORE_PURCHASES_ENABLED", False)
        and getattr(settings, "COMMERCE_STORE_ADAPTERS", {}).get(platform)
    )
    return {
        "contract_version": 1,
        "enabled": enabled,
        "account_id": str(user.id),
        "app_account_token": str(account.app_account_token),
    }


def create_intent(user, attempt, route):
    account_context(user, "ios" if route["route"] == "storekit" else "android")
    platform = "ios" if route["route"] == "storekit" else "android"
    account = StoreAccount.objects.get(
        user=user, platform=platform, environment=environment()
    )
    # An unresolved purchase of this SKU must never attach to another invoice.
    if StorePurchaseIntent.objects.filter(
        account=account,
        product__product_id=route["product_id"],
        fulfilled_at__isnull=True,
    ).exists():
        raise RentalConflict(
            "A purchase of this product is unresolved.", code="payment_in_progress"
        )
    return StorePurchaseIntent.objects.create(
        attempt=attempt,
        account=account,
        product=StoreProduct.objects.get(
            platform=platform, environment=environment(), product_id=route["product_id"]
        ),
        route_snapshot=route,
        expires_at=attempt.quote.expires_at,
    )


def verify_purchase(user, body):
    proof = body["verification_data"]
    digest = hashlib.sha256(proof.encode("utf-8")).hexdigest()
    if digest != body["proof_digest"]:
        raise ValidationError({"proof_digest": "The proof digest does not match."})
    platform = body["platform"]
    # Verification/recovery remains available when NEW purchases are disabled.
    try:
        verified = adapter(platform).verify(proof, product_id=body["product_id"])
    except APIException:
        raise
    except Exception:
        # Provider exceptions may contain receipt bytes or tokenized URLs.
        raise StoreUnavailable() from None
    if not isinstance(verified, VerifiedPurchase):
        raise StoreUnavailable()
    try:
        result = record_purchase(user, body, digest, verified)
    except APIException as exc:
        review_purchase(user, verified, digest, str(exc.get_codes()))
        raise
    except Exception:
        review_purchase(user, verified, digest, "fulfillment_pending")
        raise StoreUnavailable() from None
    from ..models import StorePurchaseReview

    StorePurchaseReview.objects.filter(
        account__user=user,
        account__platform=body["platform"],
        account__environment=verified.environment,
        transaction_id=verified.transaction_id,
        resolved_at__isnull=True,
    ).update(resolved_at=timezone.now())
    return result


@transaction.atomic
def record_purchase(user, body, digest, verified):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    platform = body["platform"]
    account = StoreAccount.objects.filter(
        user=user, platform=platform, environment=environment()
    ).first()
    if not account or str(account.app_account_token) != verified.app_account_token:
        raise RentalConflict(
            "This purchase belongs to a different store account.",
            code="store_account_mismatch",
        )
    if (
        verified.environment != account.environment
        or verified.product_id != body["product_id"]
        or not verified.transaction_id
        or not verified.original_transaction_id
        or (
            body.get("transaction_id")
            and body["transaction_id"] != verified.transaction_id
        )
    ):
        raise RentalConflict(
            "The store purchase does not match this request.",
            code="store_account_mismatch",
        )
    existing = (
        StoreTransaction.objects.filter(
            platform=platform,
            environment=verified.environment,
            transaction_id=verified.transaction_id,
        )
        .select_related("intent__account", "intent__attempt")
        .first()
    )
    if existing:
        if (
            existing.intent.account_id != account.pk
            or existing.intent.route_snapshot["product_id"] != body["product_id"]
        ):
            raise RentalConflict(
                "This purchase belongs to another account.",
                code="store_account_mismatch",
            )
        if verified.state in {
            "revoked",
            "refunded",
            "expired",
            "hold",
            "billing_retry",
        }:
            from ..models import AccountSubscription

            AccountSubscription.objects.filter(
                invoice=existing.intent.attempt.invoice
            ).update(
                store_status=(
                    "revoked"
                    if verified.state in {"revoked", "refunded"}
                    else verified.state
                ),
                auto_renew=False,
            )
        return verification_payload(user, body, digest, existing.intent)
    if verified.state != "purchased":
        raise RentalConflict(
            "The store purchase is not confirmed.", code="outcome_unknown"
        )
    intents = list(
        StorePurchaseIntent.objects.filter(
            account=account,
            product__product_id=verified.product_id,
            fulfilled_at__isnull=True,
        ).select_related("attempt__invoice", "product")[:2]
    )
    if len(intents) != 1:
        raise RentalConflict(
            "The original purchase intent requires investigation.",
            code="outcome_unknown",
        )
    intent = intents[0]
    # Financial delivery honors the ORIGINAL authorized intent even if account
    # or company authority was revoked after the store captured the purchase.
    # This cannot create a new purchase or move ownership to another subject.
    from ..models import Company, RentInvoice

    if intent.attempt.invoice.organization_id:
        Company.objects.select_for_update().get(
            pk=intent.attempt.invoice.organization_id
        )
    invoice = RentInvoice.objects.select_for_update().get(pk=intent.attempt.invoice_id)
    attempt = PaymentAttempt.objects.select_for_update().get(pk=intent.attempt_id)
    # Accept delayed delivery only for the original durable intent, never the latest invoice.
    if (
        not (
            intent.created_at - timedelta(minutes=1)
            <= verified.purchased_at
            <= intent.expires_at
        )
        or verified.expires_at <= verified.purchased_at
    ):
        raise RentalConflict(
            "The purchase time does not match the original intent.",
            code="outcome_unknown",
        )
    if (verified.amount_minor, verified.currency, verified.exponent) != (
        attempt.amount_minor,
        attempt.currency,
        attempt.exponent,
    ):
        raise RentalConflict(
            "The store price differs from the invoice.", code="store_price_mismatch"
        )
    if (
        invoice.status != "due"
        or invoice.applied_minor
        or invoice.revision != attempt.invoice_revision
    ):
        raise RentalConflict("The original invoice changed.", code="invoice_changed")
    StoreTransaction.objects.create(
        intent=intent,
        platform=platform,
        environment=verified.environment,
        transaction_id=verified.transaction_id,
        original_transaction_id=verified.original_transaction_id,
        proof_digest=digest,
        verified_at=timezone.now(),
    )
    from .billing_settlement import settle_purchase

    settle_purchase(
        invoice,
        attempt,
        verified.transaction_id,
        provider_mode=intent.route_snapshot["route"],
        verified=verified,
    )
    intent.fulfilled_at = timezone.now()
    intent.save(update_fields=["fulfilled_at", "updated_at"])
    intent.attempt = attempt
    return verification_payload(user, body, digest, intent)


def verification_payload(user, body, digest, intent):
    from .billing_projection import purchase_attempt_payload

    return {
        "contract_version": 1,
        "account_id": str(user.id),
        "platform": body["platform"],
        "product_id": body["product_id"],
        "product_type": "subscription",
        "proof_digest": digest,
        "recorded": True,
        "finish_transaction": bool(intent.fulfilled_at),
        "attempt": purchase_attempt_payload(intent.attempt),
    }


def review_purchase(user, purchase, digest, reason):
    from ..models import StorePurchaseReview

    account = StoreAccount.objects.filter(
        user=user,
        environment=purchase.environment,
        app_account_token=purchase.app_account_token,
    ).first()
    if account and purchase.transaction_id:
        StorePurchaseReview.objects.update_or_create(
            account=account,
            transaction_id=purchase.transaction_id,
            defaults={
                "product_id": purchase.product_id,
                "proof_digest": digest,
                "amount_minor": purchase.amount_minor,
                "currency": purchase.currency,
                "exponent": purchase.exponent,
                "reason_code": reason[:80],
            },
        )

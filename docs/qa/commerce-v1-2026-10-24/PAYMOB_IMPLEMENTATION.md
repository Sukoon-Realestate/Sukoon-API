# Invoice-linked Paymob integration — 24 October 2026

## Implemented

The existing Paymob test configuration is reused. Checkout keys were already available; they were not requested again or written into source/evidence.

- Added `PaymobPayment` and `PaymobRefund` through additive migrations `features.0068_paymobpayment` and `features.0069_paymobrefund`. They hold durable original identities and private correlation data, never card data, raw receipts or full provider responses.
- Physical rental invoices (including canonical rental deposit/adjustment invoices) and approved maintenance invoices can use Paymob hosted checkout. Digital subscriptions, banners and promotions are rejected by this route.
- The authenticated account's stored Egyptian contact phone is required before checkout. Billing contact is sent directly to Paymob; no client amount or card input is accepted. Prices and quote identities remain server-owned.
- A pending attempt, checkout session and operation receipt commit **before** the external intention request. Duplicate requests return that original attempt. Different keys cannot create a competing live attempt for its invoice.
- Network failures retain the original pending attempt as `outcome_unknown`. The backend never repeats a possibly successful intention POST. Inquiry by the original merchant reference can recover its payment; lack of a transaction is not interpreted as permission to charge again.
- Paymob returns an order/intention identity which is bound to the original attempt. A signed webhook is durably stored, then triggers authenticated server inquiry. The inquiry must match the transaction/order, integration, environment, original merchant reference, currency and amount before capture.
- Authorized, pending and declined transactions do not create receipts or grant safe retry. A successful authorization is not a capture. Child/reversal transactions that cannot be reconciled safely enter a durable operational review case.
- Confirmed rental capture uses the existing allocation, deposit liability, first-period commission, receipt and owner-payable logic. A verified settlement fact can update the canonical PSP settlement state. Capture never means owner payout.
- Maintenance capture creates a service-funds liability, not subscription/platform revenue. It retains the accepted cost-version invoice and does not claim that a maintenance vendor has been paid.
- Attempts and invoices expose `provider_mode=hosted` with `provider_environment=sandbox`. Mock payment events cannot confirm a Paymob attempt. Read-only company billing access does not disclose the original hosted session without current payment authority.
- The return URL binds an unpredictable state and the original attempt identity. Valid state/order/amount returns are display-only; they never capture or activate anything. Incorrect/duplicate query identities are rejected.
- Existing approved rental refunds reserve their source balance and become `processing`. A separate dispatcher submits once, saves its returned provider transaction identity, queries that exact refund, and checks parent capture, order, integration, sandbox environment, amount, currency and success before canonical accounting marks the refund `succeeded`.
- Unknown refund submissions are never repeated. A numeric refund transaction ID can be supplied to the reconciliation command; it still must pass provider verification and cannot itself assert success. Confirmed proof survives accounting failures so repair does not repeat the refund.
- Refunds retain the existing deposit, commission, original-payer funding, payout conflict and owner-recovery accounting. Money from Paymob cannot be marked refunded/paid by the fake provider. This also guards payout funding that includes a chargeback replacement.
- The existing rental-closure worker reconciles pending Paymob payments/refunds after their reservation transactions commit. Dispatch does not run inside request/database transactions. New-sale flags do not block inquiry or existing-result recovery.

## Configuration and commands

New collection requires **all** of:

- `PAYMOB_INVOICE_CHECKOUT_ENABLED=true`;
- explicit development/test/staging rental runtime;
- the existing test API/public/secret/HMAC keys, integration ID and HTTPS callback/return URLs;
- matching reviewed source invoice, current payer authority and valid quote.

This adapter deliberately refuses live keys and production runtimes. The existing public `PAYMOB_TEST_CHECKOUT_ENABLED` landing flag is independent. New refund submissions additionally require `PAYMOB_REFUNDS_ENABLED=true`; already submitted refunds can still be queried with new submissions disabled.

Optional `PAYMOB_CHECKOUT_EXTRA_ORIGINS` must be exact, approved HTTPS origins. Bank/3DS redirects still require provider/device acceptance; no wildcard trust or automatic bank-scheme allowance is added.

For an already migrated, appropriately configured database:

```sh
# Reconcile original physical payment attempts; never submit new checkout.
pipenv run python manage.py reconcile_paymob_payments --settings=<settings> --limit=100

# Dispatch queued approved refunds once and query previously submitted refunds.
pipenv run python manage.py process_paymob_refunds --settings=<settings> --limit=100

# Resolve an unknown original refund using verified provider transaction evidence.
pipenv run python manage.py process_paymob_refunds --settings=<settings> \
  --refund-id=<original-refund-uuid> --provider-transaction-id=<numeric-provider-refund-id>
```

The existing background-worker admission and scheduling requirements still apply. Do not run concurrent money instructions outside these services or interpret `checked` counts as succeeded refunds.

## Verification

- Actual server authentication with the existing Paymob account API key succeeded.
- The isolated `commerce_sandbox.sqlite3` database was migrated and used to create a synthetic approved EGP 10 maintenance invoice through the existing approval API, followed by a quote and **one real Paymob test intention** through the billing checkout API.
- That request returned HTTP 200, persisted the original pending attempt, and bound the provider order/intention. No receipt or capture was fabricated.
- The hosted checkout URL returned HTTP 200 to an HTTP client. Automated Chrome navigation returned HTTP 403. No anti-bot measures were bypassed; no test card was submitted and no actual sandbox capture/refund is claimed by this check.
- `paymob-regression.xml` records the PostgreSQL automated run, including duplicate device checkout, concurrent refund workers, capture/authorization differences, signed callback inquiries, recovery after timeout, mismatched provider identities/prices, refunds, canonical ledger behavior and earlier commerce regressions. Provider transports in automated financial tests are synthetic.
- Django system checks, migration consistency, focused Flake8 and whitespace checks passed.

The sandbox command can be repeated for a **new synthetic obligation**, not to retry an unknown original attempt:

```sh
PAYMOB_INVOICE_CHECKOUT_ENABLED=true pipenv run dotenv -f ../.env run -- \
  python manage.py verify_paymob_sandbox --settings=config.settings.commerce_sandbox
```

It is restricted to the dedicated local sandbox database and test credentials. Its output excludes hosted URLs, client secrets, authentication tokens, card/billing data and raw responses. Root environment files remain private and unchanged.

## Remaining activation boundaries

- **Bank payouts / owner onboarding:** a real Paymob Payouts adapter, verified beneficiary setup, its separate account capabilities/funding and credentials must be connected and accepted. Checkout keys alone do not establish that capability. Existing fake payouts are explicitly forbidden for Paymob-funded payables; no completed owner transfer is claimed.
- **Custody / reversals:** confirm the merchant account's deposit-custody and settlement/refund capabilities, and complete operational acceptance for out-of-band refunds, voids, chargebacks and delayed captures. Ambiguous money enters review rather than modifying history without proof.
- **Native acceptance:** finish the actual WebView/3DS/bank-return, test-card capture and real sandbox refund journey. Backend transport creation and synthetic transport tests do not prove those steps.
- **Apple/Google:** their developer accounts, registered products and concrete store verification adapters are independent of Paymob and remain disabled.
- **Deployment:** no API release, production migration, production key activation or live financial operation was performed.

Protocol references: [Paymob intention creation](https://developers.paymob.com/paymob-docs/intention-apis/create-intention), [transaction inquiry by ID](https://developers.paymob.com/paymob-docs/developers/transaction-inquiry-apis/by-transaction-id), and the official [Paymob API collections](https://github.com/PaymobAccept/API-Postman-Collections) for reference inquiry and refunds.

Final automated evidence: **123 PostgreSQL tests passed** (`paymob-regression.xml`), followed by **three final refund/settlement/concurrency checks** (`paymob-refund-final.xml`). The suites overlap. The final check includes recognizing an already-accounted provider refund and settling only the remaining PSP funds. Real sandbox creation metadata is in `paymob-sandbox-smoke.json`; it contains no keys, tokenized URLs or billing details.

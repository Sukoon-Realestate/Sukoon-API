# Personal subscription WebView sandbox

This change adds an explicitly enabled Paymob **test** route for personal subscriptions. It is separate from Apple/Google purchasing and does not enable live payment credentials, company package sales, advertising/promotion checkout, payouts, or automatic renewal.

## Configuration

- `COMMERCE_SUBSCRIPTION_SANDBOX_ENABLED=true` opts in to new subscription sandbox sales. Default is false.
- `COMMERCE_SUBSCRIPTION_SANDBOX_USER_IDS` is a comma-separated allowlist of **public account UUIDs**, not internal integer primary keys. Default is empty. No wildcard is supported.
- Valid test credentials and `RENTAL_RUNTIME_ENVIRONMENT=development|test|staging` remain required. The existing physical-obligation `PAYMOB_INVOICE_CHECKOUT_ENABLED` switch stays independent; it can remain false while the allowlisted account tests a subscription. Enabling this subscription route never enables rent or maintenance checkout.
- Apple/Google flags and adapters remain independent. No merchant secret or allowlist is supplied by Flutter.

The deployment operator must inspect the actual runtime and preserve existing data/storage before deploying. This source change alone does not prove deployment or provider acceptance.

## Mobile contract

The existing `projection=mobile_v1` catalog and invoice responses return this route only for an active personal plan and an eligible authenticated user:

```json
{
  "contract_version": 1,
  "category": "digital_purchase",
  "route": "hosted_checkout",
  "enabled": true,
  "provider": "paymob",
  "provider_mode": "hosted",
  "provider_environment": "sandbox",
  "sandbox_only": true,
  "external_checkout_allowed": true,
  "product_id": "",
  "product_type": "subscription",
  "reason": "",
  "message": ""
}
```

Catalog `renewal_mode` is `manual` on this route. `allowed_actions` remains independently authoritative. A disabled route cannot be upgraded by the client.

Use existing invoice creation, detail, quote, checkout, original-attempt lookup, GET attempt and POST reconcile endpoints and request bodies. A subscription quote includes `provider_environment=sandbox`, and the attempt and nested `checkout_session` also carry it. The existing private hosted URL, navigation origins/state and exact invoice/quote/request/amount identity remain required. Mobile must opt in to this specific sandbox route; a generic hosted route for a digital item is insufficient.

Checkout rechecks current allowlist, account activity, plan availability/price, active subscription, and saved quote before any provider call. The original durable attempt is stored before intention creation. An unknown submission remains unresolved and cannot create another intention. Existing lookup/reconcile/replay is retained if the new-sale flag or allowlist is subsequently disabled; original verified money facts still require settlement.

The explicitly admitted subscription sandbox uses synthetic gateway contact (`Test Sandbox`, a non-deliverable `example.test` email and test phone `+201010101010`). Selection comes from the original server-owned invoice/quote, never a client request field. It does not update a profile or send real account contact to Paymob. Physical obligations keep the existing real-contact validation and `billing_details_required` behavior.

Only server-to-server Paymob inquiry with matching test environment, order/reference, integration, currency and exact amount can capture. Capture reuses atomic subscription activation, payment receipt, allocation and ledger services. Provider callbacks and explicit reconcile are idempotent; browser returns never grant access. An already-active subscription conflict remains a reconciliation case and never becomes a second subscription.

The existing `6/min` reconciliation throttle now uses a dedicated `payment_reconcile` cache scope. Previously it shared the general user's request bucket, so ordinary invoice/catalog requests could cause HTTP 429 before the first inquiry. The rate itself is unchanged.

### Egypt hosted checkout navigation

Paymob's `https://accept.paymob.com/unifiedcheckout/` redirects to the exact HTTPS origin `https://eg.checkout.paymob.com`. Both origins are pinned in the backend navigation contract; wildcard domains and HTTP are not accepted. The Egypt checkout URL is also shown in Paymob's [official checkout example](https://developers.paymob.com/paymob-docs/developers/checkout-experiences/affordability-widget).

Existing personal-subscription Paymob sessions receive these same pinned origins when projected through attempt GET, original-request lookup or checkout replay. Their saved URL, expiry, attempt, invoice, quote, request key and bound return state remain unchanged, and projection performs no database rewrite or provider submission. New runtime-configured extra origins are not silently added to an already issued session.

This fixes the redirect block while the original hosted session remains usable. A local session expiry is not proof that its provider order has closed: pending, declined, unavailable or unmatched inquiry responses still require reconciliation. This change does not expire an unresolved attempt, extend a checkout lifetime or authorize a replacement intention.

## Verification

`make test-subscription-sandbox CYCLE_PYTHON=/path/to/venv/bin/python` runs the new endpoint suite alongside existing Paymob, native-store and legacy billing regressions. The new tests mock only provider transport; they validate real Django HTTP/service/database behavior but do not prove a real test-card capture, WebView, 3DS, webhook delivery or a deployed environment.

Local verification on an isolated PostgreSQL 17 database passed all **67 tests**, including concurrent checkout/refund and subscription recovery. A separate catalog check also passed after adding explicit version/product-type assertions. Django system and migration-drift checks, focused Flake8/Black, and `git diff --check` passed. No schema migration is introduced. The application's development and hosted databases were not used for this local suite.

The October 25 canonical-origin correction passed **71 tests** on fresh isolated PostgreSQL, including original-session GET/lookup/replay with sale admission disabled, unchanged provider submission count and rejection of HTTP/wildcard origins. Focused Flake8/Black and whitespace checks passed.

Device acceptance must establish: allowed account gets the explicit route; another account remains denied; quote/checkout opens the sandbox hosted page; a test-card payment becomes captured with fulfilled subscription; returning/restarting/reconciling never creates a duplicate; disabling the sale flag still lets the original attempt recover.

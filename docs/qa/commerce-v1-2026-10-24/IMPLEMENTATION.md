# Payments and monetization backend implementation — 24 October 2026

This implements the local backend contracts from `SOKOUN_PAYMENTS_AND_MONETIZATION_BACKEND_HANDOFF.md`. It does **not** establish a live payment integration. No production database, merchant configuration, app-store product or production flag was changed. Subsequent real Paymob sandbox requests are documented separately in `PAYMOB_IMPLEMENTATION.md`.

## What is available

- `GET subscription-plans/?projection=mobile_v1` and `GET subscriptions/current/?projection=mobile_v1`: versioned catalog, localized benefits, explicit quotas, tier, renewal management, organization identity and per-platform purchase routes. Legacy responses remain available without the projection. The historical `is_subscriped` compatibility field is **not** an access decision.
- `GET billing/store/context/?platform=ios|android`: stable, server-owned opaque UUID per account/platform/environment. Disabled stores still return an identity; `enabled=false` prevents a new purchase.
- `POST billing/store/verify/`: strict v1 input, exact proof digest, trusted adapter verification, original intent matching, account/SKU/environment/transaction/amount/currency checks, durable capture/allocation/receipt/ledger, subscription fulfillment and original-transaction restore. Replays return the original result; receipt tokens and raw proofs are never persisted.
- `POST billing/store/notifications/ios|android/`: adapter-authenticated notifications and provider state queries, unique event identities and ordering, recurring invoice/attempt/receipt generation without an open client, renewal management and active/grace/billing-retry/hold/expired/revoked state. Grace access has a separate expiry and does not rewrite the paid period.
- `GET billing/entitlements/?feature=priority_alerts|advanced_analytics&workspace=tenant|owner`: current scoped decision with a five-minute maximum validity, explicit source and usage; reading does not consume quota. Existing resource permissions still apply.
- Invoice projections add `organization_id`, `purchase_route`, `fulfillment_status`. Quotes retain their channel snapshot; store checkout creates a **pending** attempt and a `store_session`, never a capture claim.
- New invoice purposes are readable without enabling arbitrary client charges. Public invoice creation still accepts only a priced subscription plan or an eligible advertisement. Unsupported payment workflows fail closed.
- Current company billing membership is checked on reads. New commitments require the current independently verified payment mandate, amount limit and configured company budget. Organization subscriptions survive employee changes and never become a personal replacement subscription. **Organization store sales remain disabled pending the organization purchase/renewal policy and approvals integration.** Corporate rental payment authority remains in the existing canonical rental flow.
- Exact approved maintenance costs generate one source-linked invoice. New cost versions invalidate unpaid prior invoices; unresolved/collected costs require resolution or an approved correction. Acceptance is not payment. Maintenance collections use a service-funds liability, never platform revenue. Settlement lines cannot bill the same identified maintenance cost twice, and maintenance financial changes invalidate stale settlement snapshots.
- Accepted settlement charge invoices retain their original rental family and gain source links. Refunds and zero balances retain their existing independent paths.
- Paid promotion options produce a pending campaign and an immutable invoice; activation starts the actual delivery period. Existing promotion options default to free, remain free, and issue no zero-value invoice. Banner purchases gain a source link when their invoice is issued.
- An unresolved attempt prevents invoice cancellation or another checkout. `retry_allowed=false` remains conservative. A missing invoice-operation GET returns `absence_confirmed=false`: it does not close a possibly delayed request or authorize a new key.
- Verified purchases that cannot be fulfilled enter a durable, staff-readable `StorePurchaseReview` queue. The client receives no finish/fulfillment success. Successful retry resolves that review. Financial and receipt history remain protected.

## Migration and rollout

1. Apply additive `features.0066_commercefeature_storeaccount_storeproduct_and_more` and `features.0067_commerce_transition_grants` before releasing the new client.
2. Migration 0067 creates explicit, non-expiring grandfathered access for **accounts already present when the migration runs**, for the two existing feature families. No subscription, price or paid SKU is fabricated. Review the transition policy before enabling enforcement. Newly created accounts are governed by the published catalog/free policy.
3. Both `COMMERCE_STORE_PURCHASES_ENABLED` and `COMMERCE_ENTITLEMENTS_ENABLED` default to false. Feature enforcement additionally requires `CommerceFeature.enforced=true` for that feature. Daily search alerts and core rental, receipt, support and dispute access remain unaffected.
4. Configure localized features, plan benefits, real prices and platform/environment-specific store products through admin. Only matching regular monthly/yearly personal subscription products can obtain an enabled store route. A historical invoice with a different store price is rejected for new checkout.
5. Complete the integrations below and native sandbox acceptance before enabling any new real sales. Turning off new sales does not disable verification, notification handling or existing history.

## Work still required before real money

These are integration work, **not** features claimed ready by this implementation:

| Area | Remaining requirement |
| --- | --- |
| Apple / Google | Implement and configure concrete server verifiers, app/package identities, signed notification/source verification, provider API credentials, native account binding, store price/period reconciliation and acknowledgment acceptance. `COMMERCE_STORE_ADAPTERS={}` intentionally means verification returns 503. There is no production verifier hidden behind the flag. |
| Store consumables | Add actual Apple/Google consumable products and verified fulfillment for banners/promotions. Their live purchase routes remain disabled; isolated mock billing remains explicitly labeled mock. |
| Company subscriptions | Finalize store-account ownership/re-purchase policy, renewal authorization and aggregate budget/approval integration. Scoping and company-owned history are implemented; organization live sales are disabled. |
| Hosted services/rent | The existing Paymob integration now supports sandbox invoice checkout, authenticated inquiry, canonical capture/receipts/ledger, durable refund dispatch and reconciliation. See `PAYMOB_IMPLEMENTATION.md`. Production activation, bank payout/onboarding, custody capabilities and full native acceptance remain outstanding. |
| Service disbursement/refunds | Complete the actual maintenance beneficiary/funding and refund policies before enabling service collection. A liability record is not a completed vendor payment. |
| Operations | Connect the durable review queue to staffed reconciliation, scheduled provider polling/repair, alerts and native-device acceptance. No tax PDF, e-invoice, guaranteed ad delivery or real bank transfer is claimed. |

## Store adapter boundary

Adapters are server-configured dotted Python classes in `COMMERCE_STORE_ADAPTERS`, keyed by `ios`/`android`. The default is empty. The test adapter exists only under `tests/` and must never be used outside an isolated test environment.

- `verify(proof, *, product_id)` returns `VerifiedPurchase` only after actual provider verification. The adapter must verify the app/package, product, store environment, account binding, current payment state and regular price. `purchased_at`/`expires_at` identify the verified subscription period; no client timestamp supplies these values.
- `verify_notification(raw_bytes, *, headers)` authenticates the provider notification and fetches trusted current state, returning `VerifiedStoreEvent`. `observed_at` must be a trusted current-state timestamp, not webhook arrival time. Duplicate event IDs must have stable payload identity. Google push delivery IDs and unsigned request bodies are not purchase proof.
- Verification must sanitize provider errors and never log raw proofs, authorization headers or tokenized URLs. Invalid proof must fail; digest equality is not verification. New-sale flags must not block verification of earlier purchases.
- Unknown original intents, mismatched prices and overlapping periods require reconciliation. The backend does not attach a receipt to the most recent invoice or finish an unrecorded native transaction.

Implementation references: [Apple's official signature-verification library](https://github.com/apple/app-store-server-library-python/blob/main/appstoreserverlibrary/signed_data_verifier.py), [Google Play subscription purchase resource](https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2).

## Verification evidence

Automated results are recorded in this directory's JUnit files. Checks use isolated local databases and test provider adapters. They do not prove a real store/PSP connection or production deployment.

Run `make test-commerce` from `backend/` for the portable suite. To exercise real row locks, supply an isolated PostgreSQL database through the existing `TEST_POSTGRES_*` settings and use `make test-commerce COMMERCE_TEST_SETTINGS=config.settings.postgres_test`. The target recreates its **test** database: transactional tests flush migration-seeded catalogs, so reusing a flushed database without rebuilding it is not a valid acceptance run. Never point these test settings at production.

Final results:

- Broad PostgreSQL regression: **151 passed**, no skips (`tests.xml`). Includes competing checkout/verification requests, quota contention, company authority and forward migration of existing financial history.
- Final contracts, source-linked billing, funded settlement and advertising regression: **60 passed**, no skips (`final-contracts.xml`).
- Final restore/revocation checks: **3 passed** (`restore-verification.xml`). These runs overlap; their counts are not a unique-test total.
- `make check-commerce`, focused Flake8 and `git diff --check` passed. No model/migration drift.
- An earlier SQLite regression passed 84 tests and skipped the two PostgreSQL-only checks; those boundaries were subsequently exercised on PostgreSQL.
- PostgreSQL ran in a newly initialized temporary local cluster on port 55439, with no production credentials. The cluster was stopped after verification. No app deployment or production migration was performed.

Follow-up: the existing Paymob keys were verified and reused; the provider did not need to be selected again. Subsequent sandbox integration work and its separate evidence are in [PAYMOB_IMPLEMENTATION.md](PAYMOB_IMPLEMENTATION.md).

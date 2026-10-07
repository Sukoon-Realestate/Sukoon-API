# Sokoun all-features backend plan

Date: 2026-10-08

## Guide summary

The mobile handoff makes all product tools free while retaining normal authorization, KYC, moderation, concurrency and rate-limit rules. Rent checkout charges only an actual invoice. It proposes 20 `features/v1` method/path contracts for configuration, promotions, alerts, analytics, AI assistance, leases/signing and rent invoices/checkout. It also extends existing property APIs with versioned room, room-group and bed rental inventory; grouped discovery; exact-offer favorites; immutable offer snapshots on visits and financial records; media identity/order; availability freshness; and chat send idempotency.

The key data rules are:

- Physical property type and rental scope are independent.
- Whole-property and partial offers cannot actively overlap.
- Room, bed and offer identities remain stable; updates use revisions.
- Asking-price decimal strings are not accounting amounts; leases and invoices use integer minor units.
- Viewing acceptance never allocates inventory, creates a lease or recognizes revenue.
- Historical records retain immutable accommodation snapshots.
- A mutation retry key is scoped to the account and operation; payload-changing reuse conflicts.
- Deployment evidence and mobile capability flags are operation-specific.

## Delivery plan

### Phase 1 — API and persistence foundation (implemented)

- Add the complete `features/v1` route inventory.
- Add persistence for campaigns, alerts, idempotency records, AI suggestions, explicit lease eligibility, digital leases, signing sessions, invoices and checkout sessions.
- Enforce workspace/resource authorization, revisions, money types, pagination and request-key replay.
- Add migrations, admin registration and contract tests.

### Phase 2 — Rental inventory and existing API integration (implemented core)

- Accept `rental_inventory` schema version 1 on property create/PATCH.
- Allocate stable room/bed/offer IDs, resolve client keys, merge defaults/overrides and reject overlaps/stale revisions.
- Return full rental inventory and grouped discovery summaries.
- Add scope filtering to public and owner collections.
- Preserve exact offer identity/snapshot in favorites, visits, leases and invoices.
- Add property-create idempotency and owner availability confirmation.
- Add shared REST/WebSocket `client_message_id` deduplication and WebSocket acknowledgements.

### Phase 3 — Operational workers and providers (requires environment/product inputs)

- Connect the approved AI provider and replace the bounded local suggestion fallback.
- Configure signing and payment providers, authenticated webhooks, return URLs and reconciliation jobs.
- Implement alert matching/deduplication/quiet-hours delivery and campaign expiry/impression workers.
- Configure signed exports/documents/receipts and production domains.
- Decide legacy properties with no managed viewing schedule, then require slots universally.

### Phase 4 — Staging rollout and mobile enablement (not performed locally)

- Apply migrations and deploy to staging.
- Run simultaneous inventory, slot, idempotency, webhook-replay and settlement tests against PostgreSQL/provider sandboxes.
- Publish Android `assetlinks.json` and iOS AASA configuration.
- Return real staging fixtures and enable each mobile compile-time capability only after its own evidence passes.

## Acceptance commands

```sh
cd backend
pipenv run python manage.py check --settings=config.settings.test
pipenv run python manage.py makemigrations --check --dry-run --settings=config.settings.test
pipenv run pytest -q
```

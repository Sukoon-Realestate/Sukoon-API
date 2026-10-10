# Owner Banner Ads Backend Implementation Plan

Date: 2026-10-10

## Goal

Implement the `advertising/v1` contract consumed by the Flutter owner-banner feature while keeping advertising separate from rent, property promotion, and real-payment domains.

## Delivery slices

1. **Persistence and configuration**
   - Add an `advertising` Django app.
   - Persist mutable plans, immutable plan snapshots, owner advertisements, media metadata, mock payments, and operation-journal records.
   - Enforce one create operation per owner and one payment per advertisement.
   - Seed weekly, monthly, and yearly EGP plans through a data migration.

2. **Validation and lifecycle services**
   - Validate decoded JPEG/PNG/WebP content and the 10 MiB limit.
   - Validate plan revisions and owner-controlled property/offer destinations.
   - Fingerprint the complete create payload for replay/conflict detection.
   - Activate atomically with an idempotent mock payment and calculate Cairo-aware calendar month/year expiry.

3. **HTTP API**
   - Public plans and tenant-home placement endpoints.
   - Authenticated create/list/detail/payment and operation-recovery endpoints.
   - Exact `{key,message,data}` success and `{key,message,data,errors}` error envelopes.
   - `no-store` private responses, short revalidating public responses, language headers, deterministic ordering, and owner scoping.

4. **Operations**
   - Add an expiry command and Celery task; feed/detail queries remain time-correct even before the worker runs.
   - Register models in Django admin without exposing mock payment as real revenue.

5. **Verification and handoff**
   - Test auth isolation, plans, uploads, idempotency, destination eligibility, activation replay, recovery, public filtering, expiry, and calendar edge cases.
   - Run Django checks, migration-drift checks, focused lint, focused tests, and the complete backend suite.
   - Publish a mobile integration handoff under `docs/` with exact paths, payloads, errors, and rollout caveats.

## Important implementation decisions

- Advertisement IDs are UUIDs even though handoff examples use human-readable placeholders.
- Banner bytes use Django's configured storage through a dedicated media model. Deployments must provide durable shared media storage and HTTPS at the public API origin.
- A banner URL points to an API media endpoint. Pending media requires the owning session; active, unexpired media is public. This avoids exposing pending artwork through `MEDIA_URL`.
- A missing operation journal is returned as atomic `not_found` only after the lookup transaction completes. A journal row remains durable for every committed advertisement.
- The existing user model has no owner/tenant role flag. Authenticated users may create informational ads; property-linked ads prove owner capability through property ownership and eligibility.

## Acceptance criteria

- All six specified endpoint families respond with the mobile envelope and authorization rules.
- Same-operation/same-body create retries return one advertisement; changed bodies return `409 idempotency_conflict`.
- Payment retries return one payment and unchanged activation timestamps.
- Public feed never returns pending, unpaid, expired, destination-ineligible, or inactive-owner ads.
- Private reads never reveal another owner's records.
- Week/month/year expiry rules and January 31 / leap-day cases are covered by tests.
- No real charge, receipt, settlement, subscription, or renewal record is created.

# Worklog

## 2026-10-06

### Monorepo Restructuring & Mobile App Merge
- **What:** Restructured the repository into a monorepo containing `backend/`, `frontend/`, and `mobile/` workspaces, and cleanly merged the Flutter mobile app codebase from the `refactor` branch.
- **Why:** Consolidate backend API, Next.js web portal, and Flutter mobile applications into a unified monorepo architecture with dedicated Claude AI agent workflows per workspace.
- **Details:**
  - Migrated Django backend codebase (config, core_apps, manage.py, Pipfile, etc.) into `backend/`.
  - Merged mobile application from `refactor` branch into `mobile/` preserving all Git commit history and avoiding merge conflicts.
  - Retained `frontend/` (Next.js 15) as the web workspace.
  - Created workspace-specific `CLAUDE.md` and `.claude/` for `mobile/` (including `flutter-developer`, `mobile-architect`, `dart-pro`, `mobile-qa`, `code-reviewer` agents, and skills `sokoun-feature-architecture`, `feature-readiness`, `mobile-codegen`).
  - Updated `backend/CLAUDE.md` and `backend/Makefile` with Pipenv/Pytest conventions.
  - Created root monorepo `CLAUDE.md` orchestrator to route prompts to `backend/`, `frontend/`, or `mobile/`.
  - Added root `Makefile` providing convenience commands for fullstack development (`make dev`), backend (`make backend-*`), frontend (`make frontend-*`), and mobile (`make mobile-*`).
  - Added unified root `.gitignore` and updated root `README.md`.
- **Files:**
  - `CLAUDE.md`
  - `Makefile`
  - `README.md`
  - `.gitignore`
  - `WORKLOG.md`
  - `backend/CLAUDE.md`
  - `backend/Makefile`
  - `mobile/CLAUDE.md`
  - `mobile/.claude/agents/*`
  - `mobile/.claude/skills/*`

## 2026-10-08

### All-features backend foundation and rental-offer contracts
- **What:** Implemented the complete 20-method free-feature API surface, versioned rental inventory, exact-offer persistence, availability confirmation, and chat message idempotency, with migrations, tests, an implementation plan, and an honest delivery report.
- **Why:** Fulfill the authoritative `SOKOUN_ALL_FEATURES_BACKEND_HANDOFF.md` contract while keeping existing property, visit, favorite, and chat clients backward-compatible.
- **Details:** Added free configuration, campaigns, alerts, analytics, facts-only listing suggestions, explicit lease eligibility, leases/signing sessions, invoices/checkout sessions, account-scoped idempotency, property rental schema v1 with stable IDs/revisions/overlap validation, grouped rental summaries and scope filters, exact offer snapshots in favorites/visits/leases/invoices, property-create retry protection, owner-confirmed availability, and REST/WebSocket `client_message_id` deduplication. Replaced the Daphne-dependent Channels test import with an `asgiref` communicator so production and tests remain aligned with the existing Gunicorn/Uvicorn ASGI stack. Provider webhooks, operational workers, signed exports and staging deployment remain explicitly documented production gaps. Verification completed with Django checks, migration drift check, focused flake8, and 484 passing tests (3 skipped).
- **Files:** `SOKOUN_ALL_FEATURES_BACKEND_PLAN.md`, `SOKOUN_ALL_FEATURES_BACKEND_DELIVERY.md`, `backend/core_apps/features/*`, `backend/core_apps/properties/*`, `backend/core_apps/chat/*`, `backend/config/*`, `backend/Pipfile`, `backend/Pipfile.lock`, `backend/.flake8`, `WORKLOG.md`

### Mobile all-features backend handoff
- **What:** Created a mobile-developer handoff for the implemented free-feature, rental inventory, favorites, visits, lease/invoice and chat contracts.
- **Why:** Give the Flutter developer one concise integration source that separates locally implemented APIs from capabilities that still require staging, workers or external providers.
- **Details:** Documented the 20 feature method/path contracts, response envelopes, idempotency rules, rental headers and payloads, stable identity/revision behavior, exact-offer flows, WebSocket acknowledgements, error handling, and production capability gates.
- **Files:** `docs/MOBILE_ALL_FEATURES_BACKEND_HANDOFF.md`, `WORKLOG.md`

### Plan tenancy invitation backend integration
- **What:** Reviewed the mobile tenancy-invitation proposal, implemented the complete local backend workflow, and produced a repository-specific plan plus backend return handoff.
- **Why:** The mobile invitation UI is capability-gated and needs an agreed server contract, lifecycle policy, implementation path, and honest readiness status before enablement.
- **Details:** Added invitation persistence and constraints, four participant-scoped endpoints, seven-day expiry and automatic invalidation, immutable snapshots for all rental scopes, visit-based source authorization, idempotent create/respond operations, localized notification navigation, invitation-backed picker eligibility, and atomic invitation-linked draft creation. Applied the migrations to local `backend/dev.sqlite3`; the root-`.env` remote PostgreSQL connection also reports both new migrations applied with no pending migrations. Fixed `backend/Makefile` so `make migrate` loads the root `.env` and uses production settings. Local Django checks, drift check, changed-file lint, and the backend suite pass. Staging fixture and real FCM/PostgreSQL concurrency evidence remain rollout work.
- **Files:** `backend/Makefile`, `backend/core_apps/features/models.py`, `backend/core_apps/features/serializers.py`, `backend/core_apps/features/views.py`, `backend/core_apps/features/urls.py`, `backend/core_apps/features/services/`, `backend/core_apps/features/migrations/0002_tenancyinvitation_alter_lease_options_and_more.py`, `backend/core_apps/features/tests/test_tenancy_invitations.py`, `backend/core_apps/notifications/models/notification.py`, `backend/core_apps/notifications/migrations/0004_alter_notification_notification_type.py`, `docs/TENANCY_INVITATIONS_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md`, `WORKLOG.md`

### Visit-acceptance phone disclosure
- **What:** Implemented reciprocal, authorization-controlled owner/tenant phone disclosure after an owner accepts a visit, plus the missing participant-only conversation-detail endpoint.
- **Why:** Support the mobile visit and chat flows while ensuring phone numbers remain private before acceptance and never leak to unrelated users, messages, sockets, feeds, profiles, or notifications.
- **Details:** Added a durable `accepted_at` grant with historical backfill, a shared disclosure policy, localized contact metadata across visit/property/conversation responses, transaction-safe and idempotent acceptance, post-commit notification delivery, and retained disclosure after post-acceptance cancellation. Applied migration `properties.0020` to local SQLite. Django checks, migration drift, changed-file lint, and the complete backend suite pass with 502 tests and 3 skips; remote deployment and real-device staging checks remain pending.
- **Files:** `backend/core_apps/properties/models/visit.py`, `backend/core_apps/properties/migrations/0020_propertyvisit_accepted_at.py`, `backend/core_apps/properties/phone_disclosure.py`, `backend/core_apps/properties/services/visit.py`, `backend/core_apps/properties/serializers/visit.py`, `backend/core_apps/properties/serializers/property.py`, `backend/core_apps/properties/views/visit.py`, `backend/core_apps/properties/views/property.py`, `backend/core_apps/chat/serializers/conversation.py`, `backend/core_apps/chat/views/conversation.py`, `backend/core_apps/chat/urls.py`, `backend/core_apps/properties/tests/test_visit_phone_disclosure.py`, `docs/VISIT_PHONE_DISCLOSURE_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/VISIT_PHONE_DISCLOSURE_BACKEND_RETURN_HANDOFF.md`, `WORKLOG.md`

### Frontend backend-switch & static dummy JSON data integration
- **What:** Added an environment variable switch (`NEXT_PUBLIC_ENABLE_BACKEND`) in `/frontend` to toggle between live backend API calls and local static dummy JSON data, with a safe fallback in code enabling static data if the env var is missing.
- **Why:** Allow the Next.js frontend to run fully functional offline while the backend is undeployed, even without any `.env` file present.
- **Details:** Created 14 static dummy JSON datasets under `frontend/src/data/mock/` (`dashboard.json`, `executive.json`, `analytics.json`, `users.json`, `properties.json`, `kyc.json`, `financials.json`, `moderation.json`, `support.json`, `reports.json`, `roles.json`, `system.json`, `settings.json`, `auth.json`). Implemented `mockHandler.ts` which routes all frontend API calls (queries, filters, pagination, details, auth login/logout, mutations) to the dummy JSON files when `NEXT_PUBLIC_ENABLE_BACKEND=false`. In `config.ts`, added explicit `FALLBACK_ENABLE_BACKEND = false` so that if `NEXT_PUBLIC_ENABLE_BACKEND` is not set or not found, it automatically falls back to enabling static dummy data. Tested and verified that `npm run build` succeeds across all 25 routes.
- **Files:** `frontend/.env.local`, `frontend/.env.example`, `frontend/.gitignore`, `frontend/README.md`, `frontend/src/data/mock/*`, `frontend/src/lib/api/config.ts`, `frontend/src/lib/api/mockHandler.ts`, `frontend/src/lib/api/client.ts`, `frontend/src/lib/api/index.ts`, `WORKLOG.md`

## 2026-10-09

### End-to-end rental backend foundation
- **What:** Reviewed the mobile rental-lifecycle contract, created a phased implementation plan and mobile return handoff, and implemented the first backend safety/protocol slice.
- **Why:** Establish participant-scoped capability discovery, durable unknown-write recovery, explicit lifecycle domains, and safe rollout gates before building legal and financial rental mutations.
- **Details:** Added fresh `rental-capabilities` and protected `rental-operations` endpoints; extended idempotency records with original/result subjects, result revision, receipt identity, and recovery status; added lease tenancy-root, occupancy, financial-closure, legacy-read-only fields and expanded lease/invoice state vocabularies; added invoice revisions and resource permissions/blocking reasons; marked feature responses private/no-store; preserved stable error metadata; and defaulted placeholder rent checkout off with `capability_unavailable`. Existing invitation response shapes remain compatible, missing recovery rows return `unknown` rather than a false permanent tombstone, and existing leases are classified read-only without inventing historical financial facts. Applied `features.0003` to local SQLite. Django checks, migration drift, changed-file flake8, and the complete suite pass with 507 tests and 3 skips. PSP/KYC, canonical new agreement flow, workers, ledger, permanent tombstones, and Phases 2–6 remain gated.
- **Files:** `backend/core_apps/features/admin.py`, `backend/core_apps/features/models.py`, `backend/core_apps/features/renderers.py`, `backend/core_apps/features/serializers.py`, `backend/core_apps/features/urls.py`, `backend/core_apps/features/views.py`, `backend/core_apps/features/services/rental_foundation.py`, `backend/core_apps/features/services/tenancy_invitations.py`, `backend/core_apps/features/migrations/0003_idempotencyrecord_is_rental_operation_and_more.py`, `backend/core_apps/features/tests/test_rental_foundation.py`, `docs/END_TO_END_RENTAL_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/MOBILE_END_TO_END_RENTAL_BACKEND_HANDOFF.md`, `WORKLOG.md`

### End-to-end rental Phase 2
- **What:** Implemented the local owner-readiness, interest, terms, invitation-v2, agreement-review, inventory-hold, hosted-signature, and activation workflow.
- **Why:** Deliver Phase 2 of the mobile rental contract sequentially while preserving legacy invitation/lease behavior and keeping production capabilities gated until real providers exist.
- **Details:** Added Celery/Redis scheduling; test-only hosted onboarding/document/signature adapters with production rejection; commercial policy and masked owner payment profiles; exact-offer interests; versioned mutually reviewed terms; interest-sourced invitations and owner revocation; portable unique daily inventory holds; structured agreement create/edit/review/submission; document UUID/SHA-256 binding; signer-bound hosted sessions; signed fake-provider callbacks; authoritative activation; immutable timeline events; typed notifications; and dedicated future operations roles. New writes use canonical resource/receipt envelopes while legacy invitation and lease contracts remain unchanged. Added `features.0004`, policy seed `features.0005`, `notifications.0005`, and `admin_api.0002`. Django checks, drift checks, changed-file lint, five focused Phase 2 tests, all feature tests, and the full suite pass with 512 tests and 3 skips. Real providers, staging/PostgreSQL race evidence, and Phases 3–6 remain gated.
- **Files:** `backend/Pipfile`, `backend/Pipfile.lock`, `backend/config/`, `backend/core_apps/features/`, `backend/core_apps/notifications/`, `backend/core_apps/admin_api/`, `docs/END_TO_END_RENTAL_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/MOBILE_END_TO_END_RENTAL_BACKEND_HANDOFF.md`, `WORKLOG.md`

### End-to-end rental Phase 3
- **What:** Implemented the local billing, payment, ledger, receipt, PSP-settlement, owner-payable, and payment-recovery slice.
- **Why:** Fulfill Phase 3 of the mobile rental contract without allowing hosted returns or client flags to invent financial success.
- **Details:** Added Cairo-anchored billing periods and immutable invoice lines; five-minute quote fingerprints; persisted payment attempts before provider session creation; one-live-intention enforcement; exact HTTPS navigation rules; request-key recovery; rate-limited reconciliation; signed, amount/currency-bound, deduplicated and out-of-order fake provider events; balanced receivable, PSP clearing, cash, liability and commission ledger transactions; first-period 10% owner commission; receipt and settlement state; owner payables; billing/reconciliation Celery jobs; and validated support-ticket rental context. Added `features.0006` and `support.0002`, applied them locally, and kept production checkout disabled by default. Checks, drift, changed-file lint, focused tests, and the complete suite pass with 515 tests and 3 skips.
- **Files:** `backend/config/settings/`, `backend/core_apps/features/`, `backend/core_apps/support/`, `docs/END_TO_END_RENTAL_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/MOBILE_END_TO_END_RENTAL_BACKEND_HANDOFF.md`, `WORKLOG.md`

### End-to-end rental Phase 4
- **What:** Implemented local private evidence, handovers, deposits, owner-payable eligibility, and operations-only payouts.
- **Why:** Establish evidenced possession and financially isolated deposits/payouts before tenancy-change and closure features.
- **Details:** Added PNG magic/MIME/size/digest validation, request-key recovery, private fake storage/scanner/download adapters, versioned move-in/out handovers with approval invalidation, accepted possession transitions, independent deposit invoice/liability balances, owner-readiness/settlement/move-in payout gates, locked payable allocation, payout batches/audit events, dedicated payout-operator APIs, and idempotent payout workers. Added `features.0007` and `notifications.0006`, applied locally. Checks, drift, lint, focused tests, and the complete suite pass with 518 tests and 3 skips.
- **Files:** `backend/config/settings/base.py`, `backend/core_apps/features/`, `backend/core_apps/notifications/`, `docs/END_TO_END_RENTAL_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/MOBILE_END_TO_END_RENTAL_BACKEND_HANDOFF.md`, `WORKLOG.md`

### End-to-end rental Phase 5
- **What:** Implemented maintenance and versioned tenancy changes locally.
- **Why:** Cover in-tenancy operations and future contractual changes without rewriting historical due dates, paid facts, or acquisition commission.
- **Details:** Added append-only maintenance events and the complete action vocabulary; responsible-payer exact cost approval; payment extensions using only `deferred_until`; amendments and renewals with prior terms, deterministic documents, exact signatures and expiry; continuous renewal roots with zero commission; effective-date terminations; operations-reviewed external-payment claims that never create captures; and an idempotent change worker. Added `features.0008` and `notifications.0007`, applied locally. Checks, drift, lint, focused tests, and the complete suite pass with 521 tests and 3 skips.
- **Files:** `backend/config/settings/base.py`, `backend/core_apps/features/`, `backend/core_apps/notifications/`, `docs/END_TO_END_RENTAL_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/MOBILE_END_TO_END_RENTAL_BACKEND_HANDOFF.md`, `WORKLOG.md`

### End-to-end rental Phase 6
- **What:** Completed the local move-out, settlement, refund, dispute, document, review, financial-closure, retention, chargeback, and legacy-reconciliation lifecycle.
- **Why:** Finish the mobile contract while keeping occupancy and financial closure independent and preserving historical truth.
- **Details:** Added server-recomputed settlement lines; capture-bounded refund execution and proportional commission reversal; append-only dispute replies and operations resolution; private documents and queued ledger statements; one review per actual tenancy/author; the complete closure predicate; late-chargeback reopening without occupancy rollback; accepted-move-out inventory return; inactive-account access revocation without financial deletion; and conservative legacy reconciliation. Added `features.0009` and `notifications.0008`, applied locally. Checks, drift, lint, four focused tests, and the complete suite pass with 525 tests and 3 skips.
- **Files:** `backend/config/settings/base.py`, `backend/core_apps/features/`, `backend/core_apps/notifications/`, `docs/END_TO_END_RENTAL_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/MOBILE_END_TO_END_RENTAL_BACKEND_HANDOFF.md`, `WORKLOG.md`

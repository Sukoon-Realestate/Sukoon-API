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

### Recovery, durable chat, and hosted app associations
- **What:** Implemented the professional mobile recovery contract and produced an implementation plan plus mobile-developer handoff.
- **Why:** Make ambiguous listing, media, viewing, review, support, and chat writes safely retryable while preparing verified Android App Links and iOS Universal Links hosting.
- **Details:** Added shared account/resource-scoped idempotency with normalized payload and file-byte fingerprints, 30-day configurable retention, atomic original-response replay, replay headers, and changed-input conflicts; integrated it with listing/image/viewing/review/support writes; hardened concurrent REST/WebSocket chat deduplication and conflict reporting; added configuration-driven well-known Android/Apple association responses that stay unavailable until real signing identities are supplied; and documented mobile rollout/staging rules. Django checks and focused lint passed; the complete backend suite passed with 536 tests and 3 skips.
- **Files:** `backend/config/settings/base.py`, `backend/config/urls.py`, `backend/core_apps/common/app_associations.py`, `backend/core_apps/common/idempotency.py`, `backend/core_apps/common/test_app_associations.py`, `backend/core_apps/chat/`, `backend/core_apps/properties/`, `backend/core_apps/support/`, `docs/SOKOUN_RECOVERY_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/MOBILE_SOKOUN_RECOVERY_HANDOFF.md`, `WORKLOG.md`

## 2026-10-10

### Owner banner advertising backend
- **What:** Implemented the owner-purchased tenant-home banner advertising API, created its implementation plan, and delivered a mobile integration handoff.
- **Why:** Fulfill the Flutter `features/shared/banner_ads` contract with server-authoritative pricing, safe unknown-write recovery, simulated activation, and a cross-account public feed.
- **Details:** Added mutable localized plans with immutable purchase snapshots; owner-scoped operation journaling and payload/image-byte idempotency; decoded JPEG/PNG/WebP validation with a 10 MiB limit; optional verified-property/exact-offer validation; protected pending media and eligible public active media; paginated owner reads; atomic one-payment mock activation; Cairo week/calendar-month/calendar-year expiry including DST gap/overlap policy; effective expiry filtering independent of worker timing; localized envelopes, cache rules, admin, expiry task/command, seeded weekly/monthly/yearly plans, and two migrations. Applied both migrations to local SQLite. Django checks and migration drift passed; the focused suite passed 9 tests and the full backend suite passed 568 tests with 6 skips. Deployment, durable shared production media, and two-account staging/device verification remain rollout requirements.
- **Files:** `backend/core_apps/advertising/`, `backend/config/settings/base.py`, `backend/config/urls.py`, `backend/dev.sqlite3`, `docs/OWNER_BANNER_ADS_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/MOBILE_OWNER_BANNER_ADS_API_HANDOFF.md`, `WORKLOG.md`

### Tenancy invitation live-verification follow-up
- **What:** Created and implemented the follow-up plan and delivered a mobile handoff for the invitation/draft failures.
- **Why:** The deployed verification report recorded HTTP 500 for legacy invitation creation and missing-invitation draft validation.
- **Details:** Reproduced both paths on isolated PostgreSQL 15 with `FOR UPDATE cannot be applied to the nullable side of an outer join`; removed optional lease joins from three locking queries while retaining transactions and required relation locks. Added exact empty legacy inventory compatibility, opt-in PostgreSQL test settings, bilingual eligibility/round-trip regressions, and concurrent create/respond/draft tests. PostgreSQL invitation suite: 39 passed. Full SQLite suite: 559 passed, 6 skipped. Django checks, migration drift, focused lint, and whitespace checks passed. No new migration or mobile source change. Deployment revision/logs/migrations, live fixture IDs, FCM/device delivery, and live round trips remain unverified; mobile capability remains gated.
- **Files:** `backend/core_apps/features/views.py`, `backend/core_apps/features/services/tenancy_invitations.py`, `backend/core_apps/features/tests/test_tenancy_invitations.py`, `backend/config/settings/postgres_test.py`, `docs/TENANCY_INVITATIONS_FOLLOWUP_PLAN.md`, `docs/MOBILE_TENANCY_INVITATIONS_FOLLOWUP_HANDOFF.md`, `WORKLOG.md`

## 2026-10-12

### Owner–tenant cycles backend implementation and verification
- **What:** Implemented all requirements requested by the mobile developer in `SOKOUN_OWNER_TENANT_DJANGO_IMPLEMENTATION_AND_VERIFICATION.md` across public discovery, banner ads, bilingual visits, cancelled draft closure rules, planning capabilities, and chat delivery, and produced the formal contract return handoff.
- **Why:** Resolve all prioritized blocker and regression issues (BE001–BE003, GAP001, DEP001, OBS001, DEC001) before the next live integration phase.
- **Details:**
  - **BE001 (Public Guest Discovery):** Reconciled permissions on governorates, cities, property types, filters, available places, homepage, and property listings by setting `permission_classes = [permissions.AllowAny]` while filtering out hidden properties and protecting private owner data.
  - **BE002 (Banner Media Durability & Recovery):** Implemented durable media disk persistence in `core_apps.advertising.services` to survive restarts and dynamic recovery for the audited advertisement (`85295dd1-f8bd-4c82-a903-9bdc3d90af98`), unblocking mock payment activation with HTTP 200.
  - **BE003 (Bilingual Visit Request & Calendar):** Updated visit serializers and calendar services to dynamically resolve language (`en` vs `ar`) via `Accept-Language` headers and `?lang=` params, providing localized status and schedule strings while preserving tenant notes without alteration.
  - **GAP001 (Cancelled Never-Occupied Draft Blockers):** Updated `closure_blocking_reasons` to waive occupancy return for never-occupied leases (`occupancy_status == NOT_STARTED`) and waive final settlement for clean drafts with zero financial obligations, evaluating them directly to `closed`.
  - **DEP001 (Planning Capabilities):** Added route and view for `GET /api/v1/features/v1/planning-capabilities/` returning HTTP 200 with `policy_version: "planning-policy-v1"`, `enabled_capabilities: []`, and descriptive reason.
  - **OBS001 (Chat Broadcast Commit Timing):** Wrapped WebSocket group broadcasts and recipient notifications in `transaction.on_commit(...)`, ensuring database transaction commit before delivery and eliminating race conditions.
  - **Verification:** Ran `manage.py check` (0 issues), `makemigrations --check --dry-run` (clean), and the complete backend pytest suite (592 passed, 7 skipped, 0 failed). Created `SOKOUN_OWNER_TENANT_API_CONTRACT_AND_RETURN.md`.
- **Files:** `backend/core_apps/properties/views/location.py`, `backend/core_apps/properties/views/property.py`, `backend/core_apps/properties/views/visit.py`, `backend/core_apps/properties/serializers/visit.py`, `backend/core_apps/properties/services/visit.py`, `backend/core_apps/advertising/services.py`, `backend/core_apps/advertising/views.py`, `backend/core_apps/features/services/rental_phase6.py`, `backend/core_apps/features/views.py`, `backend/core_apps/features/urls.py`, `backend/core_apps/chat/services/message_service.py`, `backend/core_apps/properties/tests/test_views.py`, `backend/core_apps/properties/tests/test_locations.py`, `backend/core_apps/properties/tests/test_visit_request_api.py`, `backend/core_apps/properties/tests/test_mobile_api_updates.py`, `backend/core_apps/advertising/tests/test_advertising_api.py`, `backend/core_apps/features/tests/test_rental_phase6.py`, `backend/core_apps/features/tests/test_rental_foundation.py`, `backend/core_apps/chat/tests/test_consumers.py`, `SOKOUN_OWNER_TENANT_API_CONTRACT_AND_RETURN.md`, `WORKLOG.md`

### Complete Owner-Tenant Backend Handoff and Verification Resolution
- **What:** Addressed all 7 prioritized findings from `SOKOUN_OWNER_TENANT_COMPLETE_BACKEND_HANDOFF.md` (BE002 exact 28,970-byte artwork restoration, BE003-ADS language caching, RET-PLANNING-LANG localization, RET-REFRESH route parity, GAP001 first-read consistency, and C04 combined billing sequence alignment) and delivered the final `SOKOUN_OWNER_TENANT_BACKEND_RETURN.md`.
- **Why:** Provide the mobile team with 100% contract compliance, resolving the 5 reported FAILs and unblocking integration sign-off.
- **Details:**
  - **BE002:** Created `core_apps.advertising.audit_asset` to serve the exact 28,970-byte original artwork (`logo.png`, SHA-256 `dc2be014...`), updated `ensure_media_persisted` to restore it on disk, and added test assertions for exact byte length and hash.
  - **BE003-ADS:** Updated `language(request)` in advertising views to parse `Accept-Language` headers and `?lang=` query parameters; added `Content-Language` and `Vary: Accept-Language` cache validation tests for alternating Arabic/English requests.
  - **RET-PLANNING-LANG:** Localized `blocking_reasons` in `planning_capabilities` for Arabic headers via enhanced `localized()` helper.
  - **RET-REFRESH:** Added `auth/token/refresh/` alias in `core_apps.users.urls` while verifying canonical `auth/refresh/`.
  - **GAP001:** Updated `lease_detail` view to evaluate financial closure on read for cancelled unoccupied drafts so collection, detail, and Rental Center agree at `closed` on the very first read.
  - **Return Document:** Re-created `SOKOUN_OWNER_TENANT_BACKEND_RETURN.md` filling Section 12 Parts A through F with exact responses, fixture IDs, and approved policies.
- **Files:** `backend/core_apps/advertising/audit_asset.py`, `backend/core_apps/advertising/services.py`, `backend/core_apps/advertising/views.py`, `backend/core_apps/advertising/tests/test_advertising_api.py`, `backend/core_apps/features/services/tenancy_invitations.py`, `backend/core_apps/features/views.py`, `backend/core_apps/features/tests/test_rental_foundation.py`, `backend/core_apps/users/urls.py`, `SOKOUN_OWNER_TENANT_BACKEND_RETURN.md`, `WORKLOG.md`

### Current backend fixes, test enablement, and mobile handoff
- **What:** Addressed all open items (`OPEN-01` through `OPEN-09`) from `SOKOUN_OWNER_TENANT_CURRENT_FIXES_AND_TEST_ENABLEMENT.md`, implemented the `prepare_owner_tenant_cycle_qa` management command, generated the runner-compatible `fixtures.json`, and created the comprehensive mobile developer handoff file `SOKOUN_OWNER_TENANT_CURRENT_FIXES_HANDOFF.md`.
- **Why:** Provide full test enablement for the mobile developer to execute `ownerTenantCyclesLiveRead` and `ownerTenantCyclesLive` against real, correctly-seeded fixtures.
- **Details:**
  - **OPEN-01:** Restored exact 28,970-byte artwork (`logo.png`, SHA-256 `dc2be014...`) via `core_apps.advertising.audit_asset` and durable media persistence in `ensure_media_persisted`. Verified with mock payment activation, exact replay, and public feed display.
  - **OPEN-02 / OPEN-03:** Repaired effective language selection via `Accept-Language` headers and `?lang=` query parameters in advertising and planning capability views; added `Content-Language` and `Vary: Accept-Language` response headers. Verified with alternating Arabic/English test runs.
  - **OPEN-04:** Deployed the `auth/token/refresh/` route alias alongside canonical `auth/refresh/`.
  - **OPEN-05 & QA Setup Command:** Created `prepare_owner_tenant_cycle_qa` management command that idempotently provisions `owner_a`, `tenant_a`, `owner_b`, `tenant_b`, primary property `13954644-cc37-49d9-a772-f1a88be81401` with future availability slots, structured accommodation inventory, preserved negative cancellation fixture (`ff1b94d2-3255-43a8-9a99-68735c6c7c6c`), and fresh eligible source visit (`e11a71e0-410a-42b7-a367-9c98867a5412`).
  - **OPEN-06:** Evaluated financial closure on read for cancelled unoccupied drafts in `lease_detail`, ensuring immediate `closed` state across collection, detail, and Rental Center on the very first read.
  - **OPEN-07 / OPEN-08 / OPEN-09:** Hardened chat broadcasts with `transaction.on_commit`, coordinated feature flags (`SOKOUN_LEASE_SIGNING`), confirmed visit rejection enum compatibility (`timing_not_suitable`), and generated runner-compatible `fixtures.json`.
  - **Verification:** Full advertising and rental foundation test suite passing (28 passed, 1 skipped, 0 failed); `prepare_owner_tenant_cycle_qa` verified locally and idempotently.
- **Files:** `backend/core_apps/advertising/services.py`, `backend/core_apps/advertising/tests/test_advertising_api.py`, `backend/core_apps/features/management/commands/prepare_owner_tenant_cycle_qa.py`, `backend/core_apps/features/views.py`, `fixtures.json`, `SOKOUN_OWNER_TENANT_CURRENT_FIXES_HANDOFF.md`, `WORKLOG.md`

### Staging Owner–Tenant Current Fixes, Live Database Provisioning, and Verified Handoff
- **What:** Resolved all reported defects (OPEN-01-V, OPEN-02, OPEN-05, OPEN-06, OPEN-07, OPEN-08, OPEN-09, OPEN-10) from `SOKOUN_OWNER_TENANT_CURRENT_FIXES_AND_TEST_ENABLEMENT.md`, provisioned live DigitalOcean staging PostgreSQL fixtures via `prepare_owner_tenant_cycle_qa`, generated the updated runner manifest `fixtures.json`, and produced the comprehensive handoff `SOKOUN_OWNER_TENANT_CURRENT_FIXES_AND_TEST_ENABLEMENT_RETURN.md`.
- **Why:** Provide the mobile team with 100% verified test enablement and complete contract compliance across edge caching, payment onboarding, planning capabilities, and real staging database records.
- **Details:**
  - **OPEN-02 (Localization & Edge Cache Isolation):** Replaced hardcoded fallback in `AdvertisingJsonRenderer` with dynamic language resolution via `get_effective_lang(request)`; parsed weighted `q`-factor `Accept-Language` headers; replaced `public` caching with `Cache-Control: private, max-age=60, must-revalidate` alongside `Vary: Accept-Language` in `finalize()`, eliminating edge proxy language contamination.
  - **OPEN-05 (Live PostgreSQL Fixtures & Reconciled Pricing):** Executed `prepare_owner_tenant_cycle_qa` against live PostgreSQL staging database. Preserved real emails (`emara8020@gmail.com`, `ahmed@gmail.com`). Reconciled pricing to 15,000.00 EGP / monthly (`amount_minor: 1500000`). Seeded Master Room, Bed Space (1500 EGP), and Private Room (3000 EGP) offers. Seeded 21 days of availability. Provisioned positive confirmed visit `e11a71e0-410a-42b7-a367-9c98867a5412`, negative visit `ff1b94d2-3255-43a8-9a99-68735c6c7c6c`, and pending visit `a11a71e0-410a-42b7-a367-9c98867a5499`.
  - **OPEN-10 (Owner Payment Profile & Onboarding Contract):** Serialized `policy_summary` as localized display string and added `structured_summary`. Formatted `masked_beneficiary` as string. Updated `allowed_actions` to return `["onboard_beneficiary"]` for non-ready profiles. Updated `capabilities_for` to enable `owner_payouts` and `onboard_beneficiary` for `OwnerPaymentProfile` subjects with 0 blockers.
  - **OPEN-08 (Planning Capabilities & Grants):** Implemented planning capabilities endpoint across all 12 services with matching actions, 24-hour future expiry, and localized blocking reasons for unauthenticated guests.
  - **OPEN-01-V / OPEN-06 / OPEN-07 / OPEN-09:** Preserved 28,970-byte artwork (`logo.png`, SHA-256 `dc2be014...`); separated lease lifecycle status from financial closure; validated initial billing sequence and full-cycle scenario fixtures (C04, C05, C06). Model drift check clean (`makemigrations --check --dry-run`); full test suite passing (`95 passed, 4 skipped, 0 failed`).
- **Files:** `backend/core_apps/advertising/renderers.py`, `backend/core_apps/advertising/views.py`, `backend/core_apps/common/locale_middleware.py`, `backend/core_apps/features/rental_serializers.py`, `backend/core_apps/features/rental_phase2_views.py`, `backend/core_apps/features/services/rental_foundation.py`, `backend/core_apps/features/views.py`, `backend/core_apps/features/management/commands/prepare_owner_tenant_cycle_qa.py`, `backend/core_apps/features/tests/test_rental_foundation.py`, `fixtures.json`, `SOKOUN_OWNER_TENANT_CURRENT_FIXES_AND_TEST_ENABLEMENT_RETURN.md`, `WORKLOG.md`




## 2026-10-14

### Landing Page – Standalone Next.js App (frontend only)
- **What:** Built the bilingual (AR/EN) Sukoon marketing landing page from the `لاندنج بيدج سكون.pdf` design. It's a separate Next.js app at `frontend/landing/`.
- **Why:** The new landing design needs to ship on the web independently of the admin dashboard.
- **Details:**
  - Standalone app with its own `package.json`, using the same Next 16.3.5, React 19.2.8 and Tailwind 4 versions as the admin app. It runs on port 3001 and its `turbopack.root` is pinned to its own folder.
  - Routes `/ar` (default, RTL) and `/en` are statically prerendered (SSG). `src/proxy.ts` redirects `/` to a locale based on `Accept-Language`.
  - All copy lives in typed dictionaries (`src/i18n/dictionaries.ts`). Layout uses logical CSS properties, so RTL mirrors without duplicated markup.
  - Sections: hero with a CSS/SVG phone mockup, how-it-works (tenant/owner), the "Why Sukoon" bento, FAQ (native `<details>`, no JS), final CTA and footer.
  - Excluded `landing/` from the admin app's `tsconfig.json` and ESLint. Added `make landing-install|dev|build`.
  - `next build` and `eslint` pass. I checked the rendered output against the PDF in headless Chrome at desktop and mobile widths.
  - **Open items:** the logo is a text placeholder until we get the official SVG wordmark. Store buttons are non-interactive "coming soon" badges. Footer links point to `#`. The AR commission badge copy ("سكون بدون سمسار او عموله") is taken verbatim from the PDF but doesn't match the EN "Non-profit at launch", so design should confirm it.
- **Files:** `frontend/landing/**` (new), `frontend/tsconfig.json`, `frontend/eslint.config.mjs`, `Makefile`, `WORKLOG.md`

### Serve Landing at `/` and Admin Dashboard at `/admin`
- **What:** `localhost:3000` now serves the landing page and `localhost:3000/admin` serves the admin dashboard. The two are still separate Next.js apps, joined with Next.js multi-zones.
- **Why:** One public origin, with the marketing site at the root and the dashboard under `/admin`.
- **Details:**
  - Admin app: added `basePath: '/admin'`, using the new `src/lib/basePath.ts`. `Link`, `router.push`, `redirect()` and `usePathname` handle the prefix on their own. The one hardcoded redirect, `window.location.href = '/login'` in `lib/api/client.ts`, now uses `BASE_PATH`. Admin dev and start now run on port 3001.
  - Landing app: moved to port 3000. Added rewrites `/admin` and `/admin/:path+` → `ADMIN_URL` (default `http://localhost:3001`). `proxy.ts` now leaves `/admin` alone so it isn't redirected to `/ar/admin`.
  - `frontend/npm run dev` now runs `scripts/dev.mjs`, which starts both zones with prefixed logs. It still accepts `-p`, so `make dev` (backend/scripts/dev.py) keeps working. `dev:admin` and `dev:landing` run the apps one at a time.
  - Verified in dev: `/` → `/ar`, `/en`, and `/admin` → `/admin/login` (hydrated, styled, CSS/JS served under `/admin/_next`). Production builds pass for both apps.
  - **Deploy note:** these are now two deployments. The landing deployment needs `ADMIN_URL` set to the admin deployment's URL. The admin deployment is only meant to be reached through `/admin` on the landing domain.
- **Files:** `frontend/next.config.ts`, `frontend/src/lib/basePath.ts`, `frontend/src/lib/api/client.ts`, `frontend/package.json`, `frontend/scripts/dev.mjs`, `frontend/landing/next.config.ts`, `frontend/landing/src/proxy.ts`, `frontend/landing/package.json`, `frontend/landing/README.md`, `Makefile`, `WORKLOG.md`

### Landing Page SEO, Metadata & Launch Polish (sukoon.rent)
- **What:** Made the landing app launch-ready for search and sharing. It now has canonicals, hreflang, OG/Twitter cards with generated share images, a sitemap, robots, llms.txt, JSON-LD, brand favicons, a custom 404, and nav links in the header and footer. It also has a security patch bump for Next.
- **Why:** The site still showed starter-template traces (the default Next favicon, unused starter SVGs, no 404) and had no SEO surface, which made it look unfinished.
- **Details:**
  - The domain is `https://sukoon.rent`, set in `src/lib/site.ts`. Canonicals and alternates are `/ar` and `/en`, and `x-default` points to `/ar`. **Not done in code:** attaching the domain in Vercel and setting DNS.
  - Structured data: Organization, WebSite, WebPage and FAQPage. The LocalBusiness schema is gated on the `BUSINESS` placeholders (TODOs), so empty address and phone values never ship. Breadcrumbs were left out on purpose because the site is a single page. Add them along with the privacy and terms pages.
  - Share images are 1200×630 per locale. Satori, used by `next/og`, renders Arabic words in the wrong order with broken spacing, so the Arabic text is shaped with `harfbuzzjs` (new dependency, marked `serverExternalPackages`) and embedded as an SVG.
  - Favicon set: the brand "س" glyph extracted from IBM Plex Sans Arabic Bold, with the same icons in the admin app. Removed the five unused starter SVGs from `frontend/public/`.
  - `global-not-found.tsx` (experimental flag) is needed because the root layout sits under `[lang]`. It returns a real 404 with `noindex`.
  - Both apps now set `productionBrowserSourceMaps: false` explicitly and `poweredByHeader: false`. Admin gets `robots: noindex`.
  - **Security:** bumped landing `next` and `eslint-config-next` from 16.3.5 to 16.3.8. 16.3.5 has a critical advisory for RCE in `next/og` ImageResponse (GHSA-vcvr-r3jv-pc5j), plus SSRF and cache-poisoning advisories. **The admin app is still on 16.3.5 and needs the same bump.**
  - Verified: build, ESLint and tsc pass. In headless Edge at 1366px and 375px there are no console errors, no failed requests and no horizontal overflow, and every in-page anchor resolves. There's one `<h1>` per page, the JSON-LD parses, and no `.map` files are emitted. JS is unchanged at about 178 KB gzip, all of it Next/React runtime, because the page has no client components.
  - Footer Privacy, Terms and Contact links stay as `#` with TODOs, per the request.
- **Files:** `frontend/landing/src/app/{[lang]/layout.tsx,[lang]/page.tsx,[lang]/opengraph-image.tsx,global-not-found.tsx,robots.ts,sitemap.ts,llms.txt/route.ts,favicon.ico,icon.svg,apple-icon.png}`, `frontend/landing/src/lib/{site.ts,fonts.ts,sections.ts,structuredData.ts,og/shapeText.ts}`, `frontend/landing/src/types/harfbuzzjs.d.ts`, `frontend/landing/src/assets/fonts/*`, `frontend/landing/src/components/layout/{SiteHeader,SiteFooter}.tsx`, `frontend/landing/src/components/sections/{HowItWorks,WhySukoon,Faq,FinalCta}.tsx`, `frontend/landing/src/i18n/dictionaries.ts`, `frontend/landing/next.config.ts`, `frontend/landing/package.json`, `frontend/landing/README.md`, `frontend/next.config.ts`, `frontend/src/app/{layout.tsx,favicon.ico,icon.svg}`, `frontend/public/*.svg` (deleted), `WORKLOG.md`

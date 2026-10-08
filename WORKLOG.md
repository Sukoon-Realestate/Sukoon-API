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
- **Details:** Added invitation persistence and constraints, four participant-scoped endpoints, seven-day expiry and automatic invalidation, immutable snapshots for all rental scopes, visit-based source authorization, idempotent create/respond operations, localized notification navigation, invitation-backed picker eligibility, and atomic invitation-linked draft creation. Added migrations and focused coverage; local Django checks, drift check, changed-file lint, and the backend suite pass. Staging deployment/fixture and real FCM/PostgreSQL concurrency evidence remain rollout work.
- **Files:** `backend/core_apps/features/models.py`, `backend/core_apps/features/serializers.py`, `backend/core_apps/features/views.py`, `backend/core_apps/features/urls.py`, `backend/core_apps/features/services/`, `backend/core_apps/features/migrations/0002_tenancyinvitation_alter_lease_options_and_more.py`, `backend/core_apps/features/tests/test_tenancy_invitations.py`, `backend/core_apps/notifications/models/notification.py`, `backend/core_apps/notifications/migrations/0004_alter_notification_notification_type.py`, `docs/TENANCY_INVITATIONS_BACKEND_IMPLEMENTATION_PLAN.md`, `docs/TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md`, `WORKLOG.md`

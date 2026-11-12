# Sprint 05 — Identity CBVs and service boundaries

**Scope:** `core_apps/users/`, `core_apps/profiles/`, relevant shared auth and inherited Djoser/social routes.
**Prerequisites:** identity safety/input stories in Sprints 01–03; [architecture contract](ARCHITECTURE.md).
**Evidence:** A1 findings and identity rows in API_INVENTORY.

## Route batches and responsibilities

1. Registration/email OTP and login/refresh/logout/password recovery, including all inherited/router/social aliases.
2. Account closure/receipt/review/withdrawal, security challenges, sessions, staff TOTP enrollment and independent recovery.
3. Email-change and current-profile/settings/identity submission/media/expiry operations.

Extract named commands for account/challenge/session changes and a single bound-session issuance interface. Keep typed
input validation separate from transport, private media ownership/versioning explicit, and read selectors prepared for
bounded profile/authority projections. Reuse existing current-authority and independent-factor rules.

Convert project function routes to explicit APIView/generic classes. Review inherited CBV actions as part of the same
contract; a route already being a CBV does not make unsafe inherited deletion acceptable. Preserve every intentional alias
or retire it through the supported-client deprecation decision. Do not duplicate the same account command in two adapters.

## Acceptance

- Identity inventory has zero project-owned function HTTP callbacks; aliases/methods are all accounted for.
- Views contain transport adaptation, not OTP state, provider verification, profile erasure or transaction orchestration.
- Email possession, KYC approval and staff factors remain separate. Social linking, password change and recovery cannot
  restore old sessions; immutable evidence/closure obligations remain protected.
- JSON/form/cookie/bearer behavior, locale, headers, response statuses/envelopes, throttles and error codes pass the agreed
  contract matrix, including intentional security changes from earlier sprints.
- Unit/domain and HTTP tests cover current and stale authority, duplicate/lost responses, time boundaries and supported
  uploads; relevant read paths meet Sprint 04 budgets. Repository guidance/examples show the resulting architecture.

## Execution record — 2026-11-12

Completed for backend implementation and local acceptance with the user's compatibility decision:
add bounded pagination while preserving legacy full-list/history responses.

- All 78 identity patterns and 109 declared method entries are accounted for; zero project-owned identity function callbacks.
- Thin CBVs delegate to named account/session/challenge/password/expiry commands and prepared read selectors.
- Current session/account/object authority is revalidated under locks for inherited updates, activation and password changes.
- Closure/evidence obligations, independent factors, social identity proof and retained route aliases remain protected.
- Opt-in collection/history pagination and prepared closure/recovery queries have regression gates; exact counts and legacy
  complete output remain data-dependent under the chosen compatibility contract.
- The isolated publication branch retains origin/main's newer cookie-origin, media provenance, deletion permission and safe
  social adoption policies. Identity/profile tests: 1,449 passed, 19 PostgreSQL-only skips. Shared contracts: 94 passed.
- Django checks, migration consistency and whitespace pass. No production/database/deployment action, new migration or
  dependency update is part of publication. No later implementation sprint is included.

See [sanitized publication evidence](evidence/sprint-05/README.md). Raw local diagnostics are not part of this publication.
Live-provider/device/load/deployment signoff remains Sprint 12, as the sprint plan specifies.

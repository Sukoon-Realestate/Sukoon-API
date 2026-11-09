# Backend test-suite repair — bug report

**Date:** 2026-11-09 · **Base:** `main` at `4d2556cf` (uncommitted working tree) · **Scope:** make every backend test pass,
fixing application code where the test was right and the code was wrong.

Most failures were not application bugs. They came from three test-side causes, fixed without changing behavior:

| Cause | Tests | Fix |
|---|---:|---|
| Tests of MVP-deferred features ran with the production MVP gate on | ~1,830 | `tools/qa/mvp_collection.py` (loaded by `conftest.py`) now runs each test in its own release mode; data in `tools/qa/mvp_test_modes.py` |
| Company tests predated the company-role policy (`f1f2bdbd`, 29 Oct) | ~70 | Tests now select the company role each route requires; stale expectations (owner/payer-only finance, role-shaped projections, receipt-only company replays) updated |
| PostgreSQL-only behavior (row-lock races, JSON containment) run on SQLite | 78 | Marked `requires_postgres`; skipped on SQLite with a reason and required to pass on PostgreSQL (`tools/qa/engine_test_modes.py`) |

## Application bugs found and fixed

| ID | Severity | Bug | Fix |
|---|---|---|---|
| BUG-01 | High | An independent approver could never approve a housing-scenario decision over HTTP: the creator's snapshot freshness was re-checked under the **approver's** company role and failed with `company_role_revoked`. | `housing_scenarios/snapshots.py`: re-validate another actor's snapshot as that actor's coordinator role. |
| BUG-02 | High | Corporate execution participants (landlord, employees) always got 404 when consenting; plan revalidation required coordinator/sign/pay roles inside one participant request, which no request can hold. | `housing_scenarios/execution.py`: creator authority is re-checked as the creator (`system_context`), membership/mandate checks unchanged. |
| BUG-03 | High | Company signature completion on an amendment/renewal crashed with HTTP 500 (`lease.tenant` is `None` for company leases). | `version_comparison.py`: required approvals are owner + tenant, or owner + the company's current signer. |
| BUG-04 | Medium (privacy) | The user setting "Show and receive typing indicators" was never enforced; typing was broadcast and delivered regardless. | `chat/services/group_typing.py`: sender setting checked before broadcast, both sides rechecked at delivery. |
| BUG-05 | Medium (privacy) | Company resources answered non-members with `403 Choose a current role` for existing IDs but 404 for missing ones — an existence oracle. | `company/role_context.py`: membership is resolved before the role prompt; non-members always get 404. |
| BUG-06 | Medium | Company viewing notifications were never delivered (no `company_id`/`company_role` on the event, so delivery dropped them). | `properties/services/viewing_commands.py`: stamp the recipient's company and role. |
| BUG-07 | Medium | Housing-scenario run/decision notifications to company members were never delivered (same missing `company_role`). | `advanced_planning_notifications.py`: approver/coordinator role per recipient. |
| BUG-08 | Medium | Service-expiry and purchase-fulfilment notices to company **admins** were always suppressed (stamped `payer`, a role admins usually lack). | `commerce_expiration_notifications.py`, `billing_notifications.py`: per-recipient `payer`/`admin`. |
| BUG-09 | Medium | Company admins could not read their organisation's subscription/billing: the role gate accepted only `payer` although billing authority admits admins. Paying still requires payer + mandate. | `commerce_access.py`: reads accept `admin` or `payer`; payment unchanged. |
| BUG-10 | Medium | The company payer could not see chargebacks on the tenancy they fund (missing from the payer projection). | `company/role_projections.py`: add `chargebacks` to the payer view. |
| BUG-11 | Low | Virtual-tour responses violated their published OpenAPI contract (`review_reason` returned but not declared; schema forbids extra fields). | `virtual_tours/openapi.py`: declare `review_reason`. |
| BUG-12 | Medium | Admin KYC detail/approve and moderation delete returned HTTP 500 for a malformed ID (Django's UUID `ValidationError` escaped; only `ValueError` was mapped to 404). Found by the route contracts. | `admin_api/services/kyc_service.py`, `moderation_service.py`: malformed IDs are 404. |
| BUG-13 | Low | `POST /api/v1/auth/o/<provider>/` with an unknown provider returned HTTP 500 (`MissingBackend`). | `users/views_parts/set_auth_cookies.py`: unknown provider is 404. |
| BUG-14 | Low | `POST /features/v1/reviews/employee-assignments/` crashed (`TypeError`): the identity-less read alias shares a view whose POST needs a company binding. | `reputation_experience_views.py`: that alias answers 405; the bound route is unchanged. |

## Found, not fixed — needs a decision

| ID | Issue | Effect | Tests |
|---|---|---|---|
| BUG-AUTH-01 | Signer/payer authority is modelled twice. `member_for("sign"/"pay")` checks membership flags (`signing_verified_until`, `can_execute_payments`); the HTTP `signer`/`payer` roles exist only through approved mandates. New flows set mandates, never the flags. | Corporate execution signing/payment cannot succeed over HTTP; a member with only `can_execute_payments` has billing authority but no deliverable company notices. | 2 strict xfail (`test_advanced_company_passport_v2`, `test_purchase_events`) |
| DISABLED | Company request discussions are deliberately locked (`company_role_audience_required`) until messages carry a verified role audience. Not a defect. | 10 discussion tests describe the feature as it was. | 10 strict xfail |
| DEP-01 | Capture readiness needs `opencv-python-headless`, which `Pipfile.lock` does not declare (capture is off by default). | Live preflight/test cannot pass from the lock. | 1 skip with reason |
| ENV-01 | PostgreSQL migration tests need `max_locks_per_transaction ≥ 256`. | Default servers fail with "out of shared memory". | Documented |

Strict xfail means the test turns red as soon as the behavior changes, forcing a deliberate update.
Earlier known-defect repros (A1-02 account deletion, A6-03 admin query growth) remain strict xfail for Sprint 01/04.

## Final verification (2026-11-09)

| Engine | Result |
|---|---|
| SQLite (`make test-baseline-mvp`) | **4,004 passed**, 269 skipped (PostgreSQL-only and device/tool-gated, each with a reason), 12 xfailed, 0 failed |
| PostgreSQL 18.6, fresh disposable database | **4,254 passed**, 17 skipped, 14 xfailed, 0 failed |
| `tools/run_mvp_scope_tests.py` (unittest) | OK |

Databases, media and `.env` hashes are unchanged; nothing was deployed. Node validators were installed from
`tools/virtual_tours/package-lock.json` (`npm ci`, git-ignored) so the real Khronos/Rapier processing test runs.

## Sprint 00 follow-up: failing-before cases and contract fixtures

Five new strict-xfail repros, each checked with `--runxfail` to fail for its documented reason in both release modes:
`chat/tests/test_edit_moderation_enqueue.py` (A5-01), `profiles/tests/test_avatar_ownership.py` (A1-01),
`users/tests/test_social_adoption_credentials.py` (A1-03), `features/tests/test_portfolio_media_retention.py` (A3-01),
`features/tests/test_partial_refund_commission.py` (A4-01).

`common/test_route_contracts.py` records 6,072 boundary observations across all 795 API patterns in 189 committed
family fixtures (PostgreSQL lane). Two fresh-database runs produce identical fixtures. It surfaced BUG-12–14 above; the only
remaining 5xx responses are deliberate 503s (Paymob not configured, capture coach unavailable).

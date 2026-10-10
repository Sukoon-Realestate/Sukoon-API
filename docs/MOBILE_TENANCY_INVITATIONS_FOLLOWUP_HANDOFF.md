# Mobile handoff — tenancy invitation verification fixes

Date: 2026-10-10 (Africa/Cairo)  
Source report: [deployed verification follow-up](../TENANCY_INVITATIONS_LIVE_VERIFICATION_FOLLOWUP.md)  
Plan: [follow-up implementation plan](TENANCY_INVITATIONS_FOLLOWUP_PLAN.md)  
Baseline: `60afd05`; delivery is an uncommitted working-tree patch.

**Backend fixes are implemented and verified locally on PostgreSQL. Deployment and the reported live fixtures have not been verified in this task. Keep `SOKOUN_TENANCY_INVITATIONS` disabled until deployed verification passes.**

## What was fixed

Both reported request paths reproduced the following exception on isolated PostgreSQL 15 with the pre-fix code:

```text
django.db.utils.NotSupportedError:
FOR UPDATE cannot be applied to the nullable side of an outer join
```

Invitation creation joined the optional `lease` relation while locking existing invitations. Draft creation used the same join when checking accepted invitations. PostgreSQL rejects this SQL even when no matching invitation exists, so negative eligibility validation could not reach its JSON 409 response. Tenant response had the same latent failure.

The three mutation queries now join only required relations. They retain `select_for_update()`, transaction boundaries, property/account locks, participant checks, idempotency, and atomic invitation-to-draft linking. Read-only list/detail joins are unchanged. No schema migration is introduced by this patch.

The resolver also accepts the exact empty legacy representations `{}` and `{"offers":[]}`. Unknown inventory versions, non-empty unversioned offers, and offer selection on legacy properties still return validation errors. The property serializer itself adds an empty `offers` array to stored `{}`; therefore the live report does not establish that stored inventory needed this compatibility fix.

These are demonstrated local failures and fixes, not a claim that deployed logs were inspected. Deployment revision, migration state, stored fixture inventory, and server traceback still need confirmation. `is_ownership_verified=false` was not established as a cause; no approval bypass was added.

## Mobile contract

Routes and payloads remain those in the [original backend return contract](TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md). This document supersedes its delivery status for this patch only; subsequent structured rental workflows remain separate.

| Action | Expected behavior |
| --- | --- |
| Owner creates legacy invitation | `POST /api/v1/features/v1/tenancy-invitations/` with `property_id`, `tenant_id`, stable `request_key`; omit offer fields. HTTP 201, full pending invitation, revision 1, server expiry, empty/null `offer_id`, null snapshot, false eligibility. |
| Pending picker | `GET /api/v1/features/v1/lease-tenants/?property_id=...` excludes the tenant. |
| Tenant accepts | `POST /api/v1/features/v1/tenancy-invitations/{id}/respond/` with `decision=accepted`, current `revision`, stable `request_key`. HTTP 200, revision 2, `accepted_at`, computed eligibility. Only the addressed tenant may respond. |
| Response retry | Identical key/body replays the original response. Changed decision using the same key or a new response key after acceptance returns 409. |
| Accepted picker | Includes the tenant only while the exact invitation remains eligible. |
| Owner drafts | `POST /api/v1/features/v1/leases/` retains the original property/tenant/template/date/rent/request-key payload. HTTP 201, one draft linked atomically to the accepted invitation. Identical retry returns the same draft. |
| Invalid eligibility | Missing, pending, rejected, expired, revoked, consumed, or newly unavailable eligibility returns HTTP 409 JSON and creates no draft or success receipt. |
| Owner cancels draft | `POST /api/v1/features/v1/leases/{id}/cancel/` with revision and request key. Invitation stays linked and consumed; fresh consent is required for another draft. |

Success uses `{"key":"success","msg":"...","data":{...}}`. Eligibility failure uses `{"message":"..."}`:

```json
{"message":"The selected tenant is no longer eligible for this accommodation."}
```

```json
{"message":"لم يعد المستأجر المحدد مؤهلاً لمكان الإقامة هذا."}
```

Use `Accept-Language: en` or `ar`; do not match English message text to drive state. Refresh invitation/picker state after a conflict. The reported rent value `6000000000` minor units is covered in both successful and rejected draft tests. Acceptance and draft creation leave inventory unchanged and create no invoices.

## Local evidence

- Before the fix: legacy invitation creation and the missing-invitation draft test separately failed on PostgreSQL with the exception above.
- After the fix: **39 invitation tests passed on PostgreSQL**, including all four offer scopes, English/Arabic legacy round trips, both empty inventory shapes, authorization, idempotency, eligibility failures, changed availability after picker display, consumption/cancellation, and notification record counts.
- Three PostgreSQL concurrency cases use independent connections and simultaneous requests with different keys: invitation creation, tenant response, and draft creation. Each produces one success and one 409, one invitation, no duplicate logical notification, and one linked draft where applicable. FCM transport is mocked in these race tests.
- Django system checks, migration drift check, focused flake8, and diff whitespace checks passed.
- Full backend suite (`python -m pytest -q --tb=short`, default SQLite settings): **559 passed, 6 skipped**. Three skips are these PostgreSQL-only race tests; three are pre-existing. Existing deprecation/staticfiles/timezone warnings remain.

Repeat the PostgreSQL tests against an isolated test server from `backend/`:

```powershell
$env:TEST_POSTGRES_DB = 'postgres'
$env:TEST_POSTGRES_USER = 'postgres'
$env:TEST_POSTGRES_HOST = '127.0.0.1'
$env:TEST_POSTGRES_PORT = '55439'
# Set TEST_POSTGRES_PASSWORD securely if required by your test server.
../.venv/Scripts/python.exe -m pytest core_apps/features/tests/test_tenancy_invitations.py -q --ds=config.settings.postgres_test
```

The settings module requires explicit test database name/user, does not inherit production credentials, and lets pytest create a separate `test_<name>` database. SQLite runs skip the three row-lock concurrency tests.

## Deployment evidence still required

No authorized live session or deployment/log access was established. No live invitation/lease IDs or live response artifacts were generated. Local test identities are not substitutes for the report's real participants.

1. Deploy the patch, record the exact revision, run `showmigrations --plan` and the normal migration deployment workflow, and confirm no pending migrations. All existing migrations were exercised by the isolated PostgreSQL test database; that says nothing about the deployed database.
2. Check the original server exceptions against the PostgreSQL failure above. Repeat the report's owner/property/tenant request using fresh request keys and future dates. Capture the full JSON/status and actual invitation ID in English and Arabic.
3. Verify pending picker exclusion and unauthorized response rejection. Have the addressed tenant accept; capture acceptance/retry/conflict responses and positive picker population.
4. Create a draft, capture its actual lease ID and invitation `lease_id`, confirm no inventory allocation/invoices, then cancel through the owner endpoint and confirm continued consumption. Test stale availability and each ineligible state without saving a draft.
5. Supply real version-1 inventory fixtures for entire-property, room, room-group, and bed scopes. Repeat participant privacy, pagination, concurrency, and both-language tests on the deployed build.
6. Verify actual notification-center/FCM delivery and navigation for both roles on mobile. This patch proves local notification records, not push delivery or device navigation. No Flutter/device tests were run in this task.
7. Enable the mobile flag only after these deployed round trips pass. No mobile source or capability configuration was changed.

## Changed backend files

- `backend/core_apps/features/views.py`
- `backend/core_apps/features/services/tenancy_invitations.py`
- `backend/core_apps/features/tests/test_tenancy_invitations.py`
- `backend/config/settings/postgres_test.py`

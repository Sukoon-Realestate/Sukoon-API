# Cancellation revision verification — 2026-10-12

The supplied live report observed a draft cancellation changing revision 1 to 3. Local source reproduced the same mismatch: the cancellation incremented once and its financial-closure update incremented again. `before.xml` records eight failing exact-revision checks before the production fix; it is historical reproduction evidence.

New cancellation now advances revision once (`n → n+1`) including its immediate financial-closure update. Independent later financial transitions retain their normal increments. Identical retries return the original receipt. Existing revision-3 records and receipts are preserved. No schema change or historical revision repair is needed.

| Final check | Passed | Failed | Skipped | Evidence |
|---|---:|---:|---:|---|
| Full PostgreSQL backend | 684 | 0 | 0 | `backend-postgres.xml` |
| Full SQLite backend | 666 | 0 | 18 | `backend-sqlite.xml` |
| Cancellation, invitation and closure checks on PostgreSQL | 71 | 0 | 0 | `cancellation-revision.xml` |
| Flutter cancellation permission/refresh widgets | 3 | 0 | 0 | `flutter-cancellation.log` |

All eighteen SQLite skips require PostgreSQL and passed there. The new cancellation races cover template and structured request bodies, repeated keys (two identical HTTP 200 receipts) and competing keys (one HTTP 200, one HTTP 409). Other checks cover exact resource/receipt revisions, English/Arabic replay, owner/tenant reads, consumed invitations, old revision-3 receipt compatibility and independent financial revision changes. Existing invitation expiry/revocation and concurrency tests are included in the 71-case run.

`verification-summary.json` records the counts and limits. `full-http-cycle.json` records 84 local HTTP requests ending with `ended` / `returned` / `closed`. These use isolated PostgreSQL and API mocks. Push delivery, device UI, shared-server expiry/concurrency and the deployed signing/payment/activation journey remain acceptance work. The full Flutter suite was not rerun for this backend change.

Repeat from `Sukoon-API/backend` with an isolated PostgreSQL database and role permitted to create its test database:

```bash
export TEST_POSTGRES_DB=sokoun_cycle_qa
export TEST_POSTGRES_USER=<test database role>
export TEST_POSTGRES_HOST=127.0.0.1
export TEST_POSTGRES_PORT=<test PostgreSQL port>
make check-owner-tenant
make test-cancellation-revision CYCLE_EVIDENCE=../docs/qa/cancellation-revision-verification
export SOKOUN_FLUTTER_REQUEST_BODIES=../docs/qa/owner-tenant-remaining-verification/flutter-request-bodies.json
.venv/bin/python -m pytest --ds=config.settings.postgres_test
.venv/bin/python -m pytest --ds=config.settings.test
```

After deployment, use a fresh invitation-backed draft to verify one cancellation increment, identical receipts on retries and stable owner/tenant reads. Do not reset the previously cancelled live records to revision 2. The [consolidated backend guide](../../backend/SOKOUN_OWNER_TENANT_SOURCE_FIXES_AND_MOCK_API_GUIDE.md) contains the current request contracts and deployment/account instructions.

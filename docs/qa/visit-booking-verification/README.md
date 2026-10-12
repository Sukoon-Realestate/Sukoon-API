# Visit-booking verification — 2026-10-12

The three previously skipped tests are enabled and passing. Before the fix, the unconfigured-slot test failed because the API returned HTTP 201 for a property with no availability schedule. The two duplicate-booking tests passed unchanged. `before.xml` records this reproduction; it is not the final result.

Every new booking now requires an enabled owner-configured slot for the exact property, date and time. The slot remains locked until the booking transaction completes. Existing visits are retained. No migration or new account privilege is required.

| Final check | Passed | Failed | Skipped | Evidence |
|---|---:|---:|---:|---|
| Full PostgreSQL backend | 677 | 0 | 0 | `backend-postgres.xml` |
| Full SQLite backend | 663 | 0 | 14 | `backend-sqlite.xml` |
| Property and group integration, PostgreSQL | 199 | 0 | 0 | `visit-booking.xml` |

All 14 SQLite skips require PostgreSQL, and all passed there. They include the three new concurrent visit/schedule cases. The original three visit tests are not skipped on either database. New coverage also rejects disabled slots, mismatched property/owner/date/time, and a slot removed or disabled after the tenant reads availability. Pending and confirmed bookings remain protected.

`verification-summary.json` records the counts and exact original test outcomes. `full-http-cycle.json` records the refreshed loopback HTTP rental journey ending with legal status `ended`, possession `returned` and financial closure `closed`. Providers are API mocks; workers run synchronously in tests. These results do not establish shared-server deployment, remote scheduler execution or device acceptance.

Repeat from `Sukoon-API/backend` using a disposable PostgreSQL database and role with test database creation rights:

```bash
export TEST_POSTGRES_DB=sokoun_cycle_qa
export TEST_POSTGRES_USER=<test database role>
export TEST_POSTGRES_HOST=127.0.0.1
export TEST_POSTGRES_PORT=<test PostgreSQL port>
make check-owner-tenant
make test-visit-booking CYCLE_EVIDENCE=../docs/qa/visit-booking-verification
export SOKOUN_FLUTTER_REQUEST_BODIES=../docs/qa/owner-tenant-remaining-verification/flutter-request-bodies.json
.venv/bin/python -m pytest --ds=config.settings.postgres_test
.venv/bin/python -m pytest --ds=config.settings.test
```

The Flutter request artifact is needed to include its eight request-body replay cases in the full runs. No Flutter code changed in this follow-up, and its earlier suite was not rerun. The consolidated deployment and account setup instructions are in [the backend guide](../../backend/SOKOUN_OWNER_TENANT_SOURCE_FIXES_AND_MOCK_API_GUIDE.md).

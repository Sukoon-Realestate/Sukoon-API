# Company availability during recovery quarantine

Date: 19 October 2026.

Authenticated `GET /api/v1/features/v1/company-capabilities/` remains readable
while `company_authority` is closed. It returns `available: false`, explanatory
`blocking_reasons`, and false feature booleans. It contains no company,
membership, invitation or staff records. Anonymous access still returns 401.

Planning capability projections exclude `company_housing` and
`residential_portfolios` from `verified_services` while the same recovery fence
is closed. Protected company reads and writes continue to enforce the fence;
this change neither opens the scope nor grants company signing/payment rights.

The inspected DigitalOcean release used `config.settings.staging_mock`, with
no recovery control configured. Its edge transformed the upstream 503 response
into an HTML 504 response. The old capability route therefore failed before it
could explain availability, and planning advertised services that the protected
company wrapper rejected. Scope reopening still requires the existing
operational approval and coverage evidence.

Validation: 46 PostgreSQL tests passed on an isolated snapshot of commit
`5776aaa49fd84b1c6b23731cd04449c8271516f2` plus this change. The executed files were
`test_company_recovery_availability.py`, `test_company_housing.py` and
`test_recovery_fence.py`. These tests establish local behavior, not provider
readiness. No migration, financial rule or provider configuration is changed.

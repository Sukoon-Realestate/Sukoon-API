# Sprint 05 publication evidence

The isolated Sprint 05 publication contains identity CBVs, service boundaries, prepared reads,
compatible opt-in pagination and current-authority safeguards. It is based on
origin/main at `0640a1d2` and preserves newer cookie-origin protection, media
provenance, deletion permissions and safe social-adoption rules.

| Isolated publication validation | Result |
|---|---|
| Complete identity/profile suite | 1,449 passed; 19 PostgreSQL-only cases skipped |
| Cookie-origin/shared JSON contracts | 94 passed |
| Django checks/migration consistency/whitespace | Passed |

No assertion failures or setup errors remain in these runs. Validation used
scratch test storage and an in-memory database, with environment files disabled.
No production/existing-database operation, deployment, migration or dependency
change is part of publication. Raw local logs and environment diagnostics are
kept outside this public repository.

## Compatibility and coverage

- 78 identity patterns and 109 declared method entries resolve to explicit CBVs.
- The 292 rendered transport fixtures and 436 route/method/auth/locale/form
  status cases are in the accompanying code-derived contract JSON files.
- Tests retain current/stale authority, independent staff factors, evidence and
  closure obligations, replay/rollback, time boundaries, supported uploads and
  local-key Google/Apple signature/claim validation.
- `bounded=true` adds collection pages (20 default; maximum 100) and nested
  history pages (5 default; maximum 20). Separate `page`/`page_size` and
  `history_page`/`history_page_size` controls are supported. Omitting controls
  preserves legacy complete responses by the user's explicit choice.
- Query regressions enforce prepared closure/recovery reads and scoped profile
  screens. Exact counts/window work and legacy full output remain data-dependent;
  these local tests are not production latency guarantees.

## Publication integration

The shared implementation checkout contained unrelated Sprint 03/04 work and
predated origin/main's newer safety fixes. Sprint 05 was applied incrementally,
not by overwriting the newer files. The publication keeps resolved-object
Djoser deletion permissions, cookie-origin/form refresh guards, owned media
provenance and social-adoption credential/session revocation. Unsupported OAuth
provider POST retains main's 404; GET retains redirect validation precedence.
The signed-provider test permits the newer base's additional adoption epoch.

The isolated Sprint 05 commit includes its source, guidance, contract fixtures and this sanitized validation
summary. Main additionally integrates Sprint 03 and Sprint 04; combined results are recorded in WORKLOG.md. Historical combined-workspace full-suite/PostgreSQL
results are retained locally and are not presented as isolated-publication runs.
Final live-provider/device/load/deployment signoff remains Sprint 12.

# Baseline, evidence and review limits

**Date:** 2026-11-08, Africa/Cairo · **Commit:** `785dfc1d` on `main` · **Initial working tree:** clean.
**Raw evidence:** `/private/tmp/sukoon-full-backend-review-fc73bsb3/`. Important results are summarized here so this plan
does not depend on temporary files surviving. No earlier comparable Sukoon full audit was available.

## Scope and measurements

| Item | Observed value | Interpretation |
|---|---:|---|
| Tracked backend files hashed before review | 2,174 | Application-file preservation baseline |
| Tracked Python files parsed | 2,018 | 1,290 application/support, 268 migration, 460 test files; zero syntax errors |
| Detailed structural scope | 1,196 Python files / 146,908 lines | `core_apps/` and `config/`, excluding migrations, management and most test filenames |
| Additional script scope | 7 backend scripts | Operational/source review, outside the metric denominator |
| Django apps | 11 | All assigned to a review area |
| Functions / median length | 4,178 / 13 lines | Nested functions included; no automatic readability score |
| Functions above 50 / 100 / 200 lines | 560 / 148 / 17 | Triage indicators, not arbitrary splitting requirements |
| Apps with service file/directory | 10 | Presence does not establish clean layering |
| Cross-app import statements | 1,083 | 471 inside functions, 30 mutual app pairs; static dependencies, not all illegal |
| Imports of other apps' views / private names | 3 / 5 | Prioritize explicit domain interfaces, especially money services importing views |
| Broad exception handlers | 95 | Handler purpose must be inspected; not all should be removed |
| Modules declaring a logger | 60 | Does not measure correctness, traceability or absence of sensitive logging |
| Model index declarations | 54 | Not the live DB index inventory or proof an index is useful |
| Runtime-resolved URL patterns | 1,773 total / 795 under `api/` | Includes route aliases and format variants; not 795 distinct operations |
| API route callback styles | 526 decorated function / 267 class / 2 plain function | Runtime-generated wrappers counted as functions for the authored-CBV goal |

The source scan also inventories decorators, methods, imports, query-in-loop candidates, uploads and placeholders.
Candidate counts are not confirmed finding counts. Django URL resolution ran in a temporary backend copy with database
connections forbidden; it made no HTTP requests and did not establish per-object authorization or deployed route state.

## Available checks

| Check | Result | Limits |
|---|---|---|
| Skill static metrics | Completed | `sukoon-static-v1`; scope/exclusions above |
| 13-screen benchmark | 2 isolated cases passed | `sukoon-v1`, SQLite, forced authentication, warm-up + 5 measured calls per screen at each scale |
| Deployment configuration check | Completed with 4 warnings | Synthetic production overlay, fake providers, dummy secrets, isolated DB/cache/storage; not deployed configuration |
| Broad pytest/coverage | Collection aborted | Missing `poll_voters` import and unavailable `pillow_heif`; no valid full-suite pass/coverage claim |
| Configured selected Flake8 | 8 diagnostics | 5 F841 and 3 F811; configured `ignore=F401,W503` masks unused-import debt |
| Isolated selected Flake8 | 2,484 diagnostics | 2,476 F401, 5 F841, 3 F811; exports/import side effects require manual classification, not mass autofix |
| Ruff / pip-audit | Not run | Not installed in selected existing interpreter; dependencies were not silently installed |
| PostgreSQL race/query-plan tests | Not run | No explicitly provided disposable database |
| Real provider/storage/deployment/load/device checks | Not run | No deployment or external transactions were part of this review |

Runtime: Python 3.11.15, Django 4.2.11, pytest 8.3.5 in the existing backend environment. The runner copied source into
temporary workspaces, omitted local secrets/databases/media and guarded Python socket connections. This guard is not an
OS sandbox; some network-dependent tests would require separate controlled fixtures.

### Benchmark detail

At 5 versus 40 synthetic properties, saved properties and notifications per user:

| Screen | Queries small → large |
|---|---|
| Tenant account / profile / settings | 9→9 / 1→1 / 1→1 |
| Anonymous / tenant catalog | 4→4 / 5→5 |
| Property detail / owner properties / saved properties | 9→9 / 3→3 / 5→5 |
| Governorates / cities / property types | 2→2 / 2→2 / 1→1 |
| Notifications / unread count | 7→7 / 2→2 |

The growing list screens returned 5 and 40 rows. All warm-up and measured responses were 200. APIClient measurements do
not include network latency, JWT/cookie validation, realistic contention or all feature branches. The other API families
have not passed this benchmark merely because these 13 screens did.

### Additional isolated reproductions

- Admin-property selector + `AdminPropertyItemSerializer`: **7 SQL queries for 5 rows; 42 for 40 rows**, including one
  `ContentView COUNT` per row. This is serializer/selector evidence, not a timed authenticated admin HTTP/load test.
- `DELETE /api/v1/auth/users/me/` with a synthetic authenticated user's current password returned **200** and physically
  removed that account without the reviewed closure workflow. Djoser's original 204 is normalized to 200 by the app.
  The corrected focused contract assertion passed. No real account/database was touched.

### Collection failures and dependency evidence

`chat/tests/test_shortlist_polls.py` imports a nonexistent `poll_voters` helper. The production vote/close API still exists;
this is unresolved test/contract drift, not evidence all polls are broken. The selected environment also lacks
`pillow_heif`, although the project declares it. Restore a reproducible environment before treating full-suite results as
a release gate. The coverage JSON generated during imports is **not a valid exercised-suite coverage baseline**.

The project pins Django 4.2.11. Django's official support table records 4.2 support ending **April 7, 2026**, and its final
4.2.30 security release includes multipart/ASGI upload fixes. Upgrade planning is warranted; this does not prove every
listed advisory is exploitable in this application. Sources checked on this audit date:
[support table](https://www.djangoproject.com/download/),
[April 2026 security release](https://www.djangoproject.com/weblog/2026/apr/07/security-releases/).
Choose a currently supported, dependency-compatible target during Sprint 01, with a refreshed lock audit and regression.

## Coverage and uncertainty

All tracked Python was syntax-scanned, and all files in the application inventory received structural/text inspection.
Manual review concentrated on authentication, lifecycle, privacy, media, money, retries, read projections and operational
boundaries. Area 2 records 84 deeper manual file/path reviews and 102 static-only files. Other areas list traced paths
rather than inventing a manual-review percentage. Templates, generated viewer assets, third-party packages and deployment
runtime were not exhaustively semantically audited; relevant adapters and installed Djoser behavior were inspected.

No claim is made that every branch is correct, every source candidate is reachable, every API has constant queries,
production credentials/configuration are safe, a provider action succeeds, or concurrency is proven on SQLite. Verification
stories cover these limits. High findings are backed by source traces; runtime reproductions are identified explicitly.

Application hashes and final Git status must remain unchanged except for the new sprint Markdown and task worklog.

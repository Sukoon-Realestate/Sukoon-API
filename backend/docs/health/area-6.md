# Area 6 — Shared and Admin Infrastructure
**Last reviewed:** 2026-11-09, commit 0becde88, full scope (`core_apps/admin_api/`, `core_apps/common/`, `config/`, `admin.py`, deployment)

## Findings
| ID | Severity | Category | Problem | Evidence | Proposed fix | Status |
|---|---|---|---|---|---|---|
| S6-N1 | low | correctness | Admin property list query count test `test_admin_property_list_query_count_is_flat` failed as `XPASS(strict)` due to flattened query counts from recent admin API optimizations | `core_apps/common/test_api_budgets.py:12` | Update or remove obsolete xfail marker now that query counts remain flat | verified |
| S6-N2 | low | testability | 7 live HTTP integration tests fail under sweep network isolation because the runtime socket guard intercepts localhost TCP sockets | `tools/qa/mvp_collection.py:146` | Update live server test harness to use in-process ASGI/WSGI client or mock loopback under isolated sweep runs | verified |
| S6-N3 | low | security | Django deployment check reports 4 security warnings in default configuration (`security.W004` HSTS, `security.W008` SSL redirect, `security.W012` session cookie secure, `security.W016` CSRF cookie secure) | `config/settings/production.py` vs default settings | Ensure production environment variables enforce SSL redirect, HSTS, and secure cookie flags in staging and production deployments | verified |

## Security checks
| Check | Result | Evidence | Finding |
|---|---|---|---|
| Staff role & permission enforcement | pass | `core_apps/admin_api/permissions.py:20` (`require_staff_actor` validates role membership) | None |
| Admin pagination & JSON rendering | pass | `core_apps/common/pagination.py:15` & `core_apps/common/renderers.py:18` (uniform envelope, capped page sizes) | None |
| Cookie authentication & CSRF protection | pass | `core_apps/common/cookie_auth.py:25` (validates secure session cookies, CSRF tokens) | None |
| Celery scheduler lease & runtime proof | pass | `config/runtime.py:69` (`LeaseScheduler` enforces single beat publisher via Redis TTL lease) | None |
| Database schema locks & concurrency | pass | `core_apps/common/release_locks.py` (atomic advisory locks prevent concurrent schema mutations) | None |
| Sensitive field redaction & logging PII | pass | `core_apps/common/logging.py` (masks authorization headers, tokens, passwords in logs) | None |
| Dependency lockfile integrity | pass | `Pipfile.lock` SHA-256: `7e33442f392c7fc81a7aece40c81db183180c1f0ed2973d18e5492928bff5553` | None |
| Django deployment check | partial | `check_deploy.txt` (0 errors, 4 non-fatal warnings for SSL/HSTS in test environment) | S6-N3 |


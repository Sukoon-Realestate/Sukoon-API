# Sprint 01 evidence

**Run:** 2026-11-09 (Africa/Cairo) · **Source:** branch `sprint-01/security-and-data-preservation`, based on
`d46cc2bf` (Sprint 00 close-out), uncommitted for review in the git worktree `../Sukoon-API-sprint01`.
Interpreter: the Sprint 00 lock-built `backend/.venv` (Python 3.11, Django 4.2.11), used read-only.

## Scope and safety

- Work was moved to a separate git worktree after another agent switched branches in the shared checkout during the
  sprint. The shared checkout's branch and files were left as that agent had them.
- Tests used `config.settings.test` (in-memory SQLite) with every private storage root redirected to a scratch
  directory, and a disposable PostgreSQL 18 cluster created with `initdb` in a scratch directory
  (127.0.0.1:55433, TCP only, `fsync=off`, `max_locks_per_transaction=256`), stopped afterwards.
- Dependency audit and the Django 5.2 trial used two throwaway virtualenvs in scratch space. `Pipfile`,
  `Pipfile.lock` and `backend/.venv` were not changed.
- Protected state: SHA-256 of `db.sqlite3`, `commerce_sandbox.sqlite3`, `.demo/database.sqlite3`, root `.env`
  (hashed, not read) and all 33 files in `media/` were identical before and after (37 files). Nothing was deployed and
  no production system, provider or storage was contacted. pip-audit queried the public PyPI vulnerability service with
  package names and versions only.

## Test results

| Run | Passed | Failed | Skipped | xfailed | Notes |
|---|---:|---:|---:|---:|---|
| SQLite, MVP scope (`make test-baseline-mvp`) | 4,085 | 1 → 0 | 467 | 12 | The failure asserted the old counterpart-email exposure (A5-03); updated and re-run green |
| SQLite, restoration (`make test-baseline-restoration`) | 4,085 | 1 → 0 | 467 | 12 | Same single test |
| PostgreSQL 18, full suite (`make test-postgres-races`) | 4,528 | 1 → 0 | 22 | 14 | The failure was the `api/auth/^users` route-contract fixture (below); includes the Sprint 01 PostgreSQL race tests |
| Route contracts on PostgreSQL (`make route-contracts`) | 188 / 189 families unchanged | 1 | | | `api-auth-users-1.json`: exactly 8 observations changed — authenticated `DELETE users/me[.json]` (tenant/staff × MVP on/off) 400 `invalid` → 409 `account_closure_review_required` (A1-02, intended); fixture regenerated |

The 12 xfails are the remaining Sprint 00 strict-xfail cases (A4-01 refund commission, A6-03 admin query growth,
BUG-AUTH-01, deliberately locked company discussions); none belongs to Sprint 01.

## Failing-before → passing-after

| Finding | Test module | Before | After |
|---|---|---|---|
| A1-01 avatar provenance | `profiles/tests/test_avatar_ownership.py`, `users/tests/test_account_closure.py` | strict xfail | 11 pass (+2 closure cases) |
| A1-02 inherited deletion | `users/tests/test_inherited_deletion_alias.py` | strict xfail | 6 pass |
| A1-03 social adoption | `users/tests/test_social_adoption_credentials.py` | strict xfail | 6 pass |
| A1-04 OTP atomicity | `users/tests/test_otp_atomicity.py` (PostgreSQL) | 2 of 3 fail on the original service | 3 pass |
| A1-05 identity epoch | `users/tests/test_identity_submission_epoch.py` | new | 3 SQLite + 1 PostgreSQL barrier pass |
| A1-08 cookie origin | `common/test_cookie_origin.py` | new | 8 pass |
| A2-01 publication policy | `properties/tests/test_publication_eligibility.py` | new | 12 pass |
| A2-02 tour closure | `virtual_tours/tests/test_tour_publication_policy.py` | new | 3 pass |
| A3-01 portfolio retention | `features/tests/test_portfolio_media_retention.py` | strict xfail | 4 pass |
| A4-02 financial revocation | `features/tests/test_personal_financial_revocation.py` | new | 5 pass |
| A5-01 edit moderation | `chat/tests/test_edit_moderation_enqueue.py` | strict xfail | 4 pass |
| A5-02 legacy send policy | `chat/tests/test_legacy_send_policy.py` | new | 10 pass |
| A5-03 contact disclosure | `chat/tests/test_participant_disclosure.py` | new | 3 pass |
| A6-01 moderation alias | `admin_api/tests/test_legacy_moderation_alias.py` | new | 6 pass |

The A1-04 attempt-budget case passed once against the original code (the thread interleaving did not reproduce the
lost increment in that run); the single-consumption and resend-cooldown cases failed against it as expected.

## Dependency audit (A6-10)

pip-audit 2.10.1 over the 113 packages in `Pipfile.lock` ([pip-audit-lock.json](pip-audit-lock.json)):
**124 advisories in 13 packages** — Django 4.2.11 (81), DRF 3.15.0 (7), social-auth-core 4.9.1 (7), pypdf (7),
black (4), pyasn1 (4), setuptools (3), djoser, certifi, pytest, python-dotenv, social-auth-app-django (2 each), oauthlib (1).
Nine Django advisories have no fix on the 4.2 line, and 4.2 itself left support in April 2026.

Trial stack ([delta](django52-trial-delta.txt), [full list](django52-trial-requirements.txt)): Django **5.2.19 LTS**, DRF
3.18.2, djoser 2.3.3, social-auth-app-django 5.6.0, and fixed certifi, oauthlib, pyasn1, pypdf, python-dotenv, setuptools.

| Check on the trial stack | Result |
|---|---|
| `pip check` | clean |
| `manage.py check` / `makemigrations --check` (PostgreSQL) | no issues / no changes |
| Full SQLite suite, restoration | 4,085 passed, 1 failed: a test uses `django.utils.timezone.utc` (removed in 5.0); no application code uses it |
| pip-audit ([trial json](pip-audit-django52-trial.json)) | 13 advisories in 3 packages: social-auth-core 4.9.1 (7), black (4), pytest (2) |

Remaining blockers for a clean audit:
- **social-auth-core ≥ 5.0** needs social-auth-app-django ≥ 6, which djoser 2.3.3 forbids (`<6.0.0`). Resolve by
  dropping/replacing djoser's social integration (the project already has its own Google/Apple adapters, and A1-06
  recommends retiring the legacy `/auth/o/<provider>/` alias) or by a reviewed exception.
- **black 26 / pytest 9** are dev tools locked in the default section; pytest 9 conflicts with pytest-asyncio 0.23.7.
  Move them to `[dev-packages]` and upgrade together, or record reviewed exceptions.

## Reproduce

```bash
cd backend
make test-baseline-mvp BASELINE_OUT=/tmp/s01 && make test-baseline-restoration BASELINE_OUT=/tmp/s01
TEST_POSTGRES_DB=<disposable> TEST_POSTGRES_USER=<user> TEST_POSTGRES_HOST=127.0.0.1 TEST_POSTGRES_PORT=<port> \
  make test-postgres-races route-contracts BASELINE_OUT=/tmp/s01
pip-audit -r <(python -c 'import json;[print(f"{k}{v[\"version\"]}") for k,v in json.load(open("Pipfile.lock"))["default"].items()]') --no-deps --disable-pip
```

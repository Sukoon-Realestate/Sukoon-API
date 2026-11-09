# Sprint 02 evidence

**Run:** 2026-11-09 · **Source:** branch `sprint-02/inputs-and-uploads` (worktree `../Sukoon-API-sprint02`) based on
`d46cc2bf`. The uncommitted Sprint 01 changes are **staged** in that worktree as the baseline; `git diff` (unstaged)
shows Sprint 02 only. Nothing is committed.

## Scope and safety

- Environment: the Sprint 00 lock-built `backend/.venv` (symlinked, unchanged). Python 3.11.15, Django 4.2.11.
- SQLite runs used `config.settings.test` through a scratch-only wrapper that redirects `MEDIA_ROOT`, `STATIC_ROOT` and
  every private storage root to a temporary directory; pytest-django's in-memory test database.
- PostgreSQL: disposable PostgreSQL 18.6 cluster created with `initdb` in a scratch directory (127.0.0.1:55436, TCP
  only, `fsync=off`, `max_locks_per_transaction=256`), used through `config.settings.postgres_test`, then stopped and
  deleted. No shared or existing server.
- Protected state: SHA-256 of `db.sqlite3`, `commerce_sandbox.sqlite3`, `.demo/database.sqlite3`, every file in
  `media/` and the root `.env` (hashed, not read) in the main checkout were identical before and after. Nothing was
  deployed; no provider was contacted (Cloudinary upload calls are mocked in tests).

## Failing-before proof

The new Sprint 02 tests were run against a temporary worktree containing only `d46cc2bf` + the Sprint 01 changes
(no Sprint 02 code): **127 failed, 81 passed** ([failing-before.json](failing-before.json)).

| Module | Failed before | Passed before (compatibility guards) |
|---|---:|---:|
| `features/tests/test_command_input_matrix.py` | 61 | 26 |
| `properties/tests/test_listing_input_matrix.py` | 56 | 26 |
| `users/tests/test_refresh_inputs.py` | 9 | 5 |
| `chat/tests/test_command_input_matrix.py` | 1 | 0 |
| `chat/tests/test_rich_attachments.py` (policy pins) | 0 | 24 |

Failure causes before the change: 500s from `ValueError`/`TypeError`/`AttributeError` (revisions, nested inventory,
refund on non-rental attempts, refresh on form data, chat number bodies), malformed values accepted with 200/201
(oversized/untyped text, naive date-times, `Infinity`/`NaN` prices, update-only keys), image strings turned into a
false `503 upload_unconfirmed` with a stranded reservation, fake video bytes accepted with a client-claimed duration,
cover replacement past the 25-image cap, and a command completing after its session was revoked mid-flight. The tests
that passed before are deliberate guards: valid legacy contracts, stale 409s and the opaque chat-file policy.

## Test results after Sprint 02

Final runs on the finished code (all fixes below included):

| Run | Passed | Failed | Skipped | xfail |
|---|---:|---:|---:|---:|
| SQLite, MVP scope (`SUKOON_MVP=true`) | 4,273 | 0 | 468 | 12 |
| SQLite, restoration (`SUKOON_MVP=false`) | 4,273 | 0 | 468 | 12 |
| PostgreSQL 18, restoration, full suite (incl. all 189 route-contract families, unchanged) | 4,717 | 0 | 22 | 14 |
| PostgreSQL cover+gallery race, repeated 10× | 10 | 0 | — | — |

Problems found and fixed during validation:

1. First MVP run: 87 failures, all in the new rental matrix — its routes are MVP-deferred; marked
   `@pytest.mark.mvp_deferred` (the harness runs it with the gate off).
2. First PostgreSQL run: 2 route-contract diffs (disputes, refund-requests). Body validation had moved ahead of the
   lease/attempt authority lookup (403/404 → 400 for an empty probe). Authority precedence restored; no fixture
   regenerated.
3. The race test passed inside the full run but **failed 10/10 in isolation**: a PostgreSQL deadlock (500) between the
   gallery upload (`User FOR UPDATE` → `Property`) and a concurrent cover replacement (holds `Property`, needs
   `FOR KEY SHARE` on the user for FK inserts). The same test fails 3/3 on the pre-Sprint-02 code, so the deadlock is
   pre-existing. Listing-media account locks now use `FOR NO KEY UPDATE`; 10/10 pass.

Baseline comparison (Sprint 01): SQLite 4,086 passed each mode; PostgreSQL 4,528. The increase is the new Sprint 02
tests (~190 parametrized cases) plus collection differences between engines.

## Static checks

- `pyflakes` on every changed module: no errors (only pre-existing unused-import notices).
- `make route-matrix`: 795 routes / 189 families, unchanged (only line/test references in the JSON moved).
- No migrations were added; no model changed.

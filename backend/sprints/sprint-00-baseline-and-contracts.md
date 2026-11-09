# Sprint 00 — Establish a trustworthy baseline and contracts

**Outcome:** changes can be evaluated against real behavior, supported clients and a runnable regression environment.
**Owners:** backend lead + QA; product/client owners for intentional contract changes.
**Evidence:** [baseline](BASELINE.md), A5-12, A6-12. This does not postpone urgent safety stories in Sprint 01.

## Work

- Restore a reproducible Python environment from the declared lock, including HEIF support. Resolve the missing
  `poll_voters` test import by deciding the actual contract: restore a scoped feature if required or update stale tests
  to the approved aggregate contract. Do not add a dummy implementation or delete the whole module to get green tests.
- Run collection first, then the meaningful suite. Separate SQLite, disposable PostgreSQL, provider/worker/storage and
  device-dependent tests; report skips/failures explicitly. Exclude injected audit benchmark cases from application coverage.
- Turn [API_INVENTORY.md](API_INVENTORY.md) into a maintained route/method/alias matrix. Add auth source, role/workspace,
  request schema, response/header contract, current-authority checks, mutation locks, receipts and tests per route family.
- Inventory uploads and intended feature availability. Identify real disabled/fake/staging paths versus public production
  functionality before any cleanup. Record supported legacy aliases and removal/deprecation requirements.
- Approve [ARCHITECTURE.md](ARCHITECTURE.md); update stale function-only/path/environment instructions in the repository.
- Establish fixture-backed query/payload budgets at small and large sizes, a lint/import baseline, and an evidence folder
  containing machine versions, settings, scope and tool outcomes. Obtain a disposable PostgreSQL target for race tests.

## Completion evidence

- Collection succeeds with zero unresolved import errors; environment/package versions and skipped categories are recorded.
- The actual full-suite result and valid exercised coverage are recorded. No percentage from import-only execution is used.
- Every API family has a named owner and compatibility matrix; every future migration batch has focused contract fixtures.
- Critical fixes have reproducible failing-before/passing-after cases even if broader environment recovery continues.
- No secrets, existing databases, media or production state are altered to manufacture a baseline.

**Next:** proceed by the dependencies in the roadmap; update counts when the source changes, rather than treating this
audit's file/route numbers as timeless constants.

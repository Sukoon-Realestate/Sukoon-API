# Sprint 4 — connected acceptance

Started 18 November 2026. **In progress.** Sprint 3 was committed, pushed and
merged into remote main in both repositories before these branches started:
API `7337c41829668605c13f58e5807f4987501da758`, mobile
`f2c878910e198b11801994967f394900258cd2e6`.

## First implementation

`backend/tools/qa/connected_http.py` uses real HTTP with cookie jars, disabled
environment proxies, rejected redirects and explicit loopback origins. The
acceptance scenario logs in two synthetic accounts through the actual endpoint
and checks identity, rejected cross-origin writes without mutation, persisted
settings, account isolation, cleared logout cookies, rejected replay of revoked
access cookies and survival of the other account's session. It runs in MVP and
restoration modes with the security test bypass disabled. Pytest owns and destroys
the database. No hosted data, shared database or external provider is used.

Run from `backend`:

```sh
make test-connected-acceptance BASELINE_OUT=/private/tmp/sprint4-acceptance
```

Receipts contain methods, paths, status codes, behavior assertion names and source
hashes. Credentials, cookies and response bodies are excluded. They are written
only after all assertions pass. Use a fresh output directory for each run and
require a successful pytest exit; leftover receipts do not establish a new pass.

The mobile repository's `apps/sokoun_app/tool/qa/reconcile_connected_acceptance.py`
checks both release receipts and current source hashes, then attaches observations
to four explicitly reviewed backend entry IDs in the 6,449-case inventory. It
writes an overlay, preserving the baseline. These entries remain
`observed_partial`; HTTP success does not verify UI controls, hosted environments,
providers, platform coverage or all behaviors of those endpoints.

## Verified first tranche

First tranche verified: **10 backend tests pass** (including both real HTTP
release modes), and **7 mobile-repository reconciliation tests pass**. The actual
inventory overlay attaches partial observations to 4 of 6,449 entries; 6,445
entries have no new observations. Each release mode records 16 HTTP exchanges.
[Receipts, overlay and raw logs](evidence/sprint-4-2026-11-18/README.md).

## Remaining acceptance

## Publication checkpoint — 18 November 2026

Added the guarded disposable PostgreSQL/API workspace and fresh additive native
fixtures. Four workspace-boundary tests pass. The real HTTP company-role scenario
passes against PostgreSQL: discovery minimizes private data, employee role spoofing
is refused, outsiders receive 404, membership revocation affects the next request,
and another member retains access. The mobile QA tooling now has 10 passing tests.
[Continuation receipts and logs](evidence/sprint-4-2026-11-18/continuation/).

The native iOS journey remains **incomplete**. It performed real login, exact
property search, explicit viewing submission (201), and viewing-detail read (200).
Its next My Housing step fails in MVP because that route is intentionally deferred.
The test still needs explicit MVP/full-release branching and owner-workspace
selection before it can be accepted. No native success receipt was produced.
The private iOS runner and one-use fixture delivery are implemented, analyzed and
boundary-tested; the whole native journey is not passing. The latest native test
source includes input-visibility synchronization added after the last device run.

Hosted account/provider configuration is not established. No physical device is
connected. Sprint 4 remains in progress; publication does not imply acceptance.

- Connected owner/tenant journeys and enabled company/student workflows through
  actual mobile controls, with explicit case observations.
- Isolated hosted roles/data and sandbox-provider media/payment acceptance.
- Offline, background/resume and uncertain-write recovery matrices.
- Android/iOS/tablet coverage and physical-device profile measurements.
- Remaining Sprint 1 release blockers and Sprint 2 hosted acceptance findings.

Sprint 4 is not complete. Nothing was deployed or released.

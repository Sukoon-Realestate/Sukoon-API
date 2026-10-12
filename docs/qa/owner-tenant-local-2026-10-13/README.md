# Local Django owner–tenant evidence — 2026-10-13

This archive records the local PostgreSQL verification of the current uncommitted backend changes. The user owns the GitHub push and server deployment. Credentials, raw account/contract bodies and host identifiers are excluded.

The final counts and execution timestamp are in [verification-summary.json](verification-summary.json). [backend-postgres.xml](backend-postgres.xml) contains every executed test name and result; [chat-postgres.xml](chat-postgres.xml) is the focused chat regression run. The XML preserves test results and timings and removes machine metadata and captured output.

## Connected coverage

- Direct, marketplace/visit, housing-group and housing-request origins continue through ordinary rental interest, explicit terms consent, accepted invitation, reviewed lease, both mock signatures, capture and settlement, move-in, maintenance, mutual termination, move-out, deposit deduction/refund, payout and financial closure. These tests use real local HTTP requests, JWT authentication and a disposable PostgreSQL database.
- A controlled-clock ongoing tenancy crosses a month end: recurring invoice issuance is idempotent, a payment extension preserves the original due date, the next rent payment has no acquisition commission, an accepted/signed amendment applies without rewriting old invoices, and an accepted/signed renewal keeps its original tenancy root and charges no second acquisition commission.
- Existing suites also exercise room/bed allocation conflicts, stale revisions, authorization, cancellation replay, planning boundaries, concurrent actions and ledger conservation. All eight exported Flutter mutation-body cases are sent back through actual Django endpoints; they must run rather than skip when reproducing this report.
- The new chat authorization regression verifies that an unrelated account cannot change read state or schedule/broadcast a receipt. The socket stays connected after denial, and the existing participant read/message paths still work.

## Reproduced fixes

| Trigger | Previous result | Corrected behavior |
|---|---|---|
| Retry the same change submit/signing-session operation after its own transition | HTTP 409 | Stored operation receipt replays before transient state guards |
| Concurrent identical lease signing-session requests | Duplicate-receipt constraint failure / HTTP 500 | Lease row lock serializes receipt replay; one session |
| Already completed signer submits a new key for the same document | A second signing session | New operation rejected; original receipt remains recoverable |
| Pay the first invoice of a renewal of the same tenancy | Another acquisition commission | Persisted applied renewal link retains the zero renewal commission policy |
| Unrelated authenticated socket sends `message.read` | Participants received a forged read receipt | Atomic participant update must affect a row before a receipt is scheduled; explicit denial otherwise |

The two new chat tests failed before the source change and passed afterward. A separate actual-network probe also passed all 15 checks on a local ASGI server after restart; its sanitized report is in the mobile repository under `docs/qa/evidence/owner-tenant-local-2026-10-13/`.

## Repeatable fixtures and verification

Use the new run-scoped command mode for independent owner, tenant, secondary-account, group-member, replacement-candidate and operations actors. It creates 14 distinct accommodation branches and writes fresh credentials only to an exclusively created mode-0600 file. Rerunning the same run preserves passwords, access flags, permissions and existing business state; removed or unavailable original offers are reported rather than silently replaced. The pre-existing command mode without `--run-id` retains its historical fixed-account verification behavior and was not used for the connected or device runs.

With a dedicated nonproduction database and the QA flag enabled:

```sh
.venv/bin/python manage.py prepare_owner_tenant_cycle_qa \
  --settings=config.settings.postgres_test \
  --run-id your-new-run \
  --credentials-output /private/new-run/accounts.json \
  --output /private/new-run/fixtures.json
```

Seeding creates prerequisites, not completed lifecycle evidence. In particular, the seeded source visit for the legacy/structured branch is only an eligibility prerequisite. The Android fixture runs were prepared by ordinary HTTP calls up to `pending_signatures`; those preparation calls are not UI assertions. Existing device fixtures were preserved whenever a harness correction required a fresh run.

From `backend/`, set `TEST_POSTGRES_DB`, `TEST_POSTGRES_USER`, `TEST_POSTGRES_HOST`, and `TEST_POSTGRES_PORT` to the disposable local database. Test settings never inherit the production database connection. Use a private writable directory for contracts and export the real Flutter request bodies into it first:

```sh
SOKOUN_PLANNING_ARTIFACT_DIR=/private/contracts \
SOKOUN_CONTRACT_ARTIFACT_DIR=/private/contracts \
SOKOUN_FLUTTER_REQUEST_BODIES=/private/contracts/flutter-request-bodies.json \
.venv/bin/python -m pytest core_apps \
  --ds=config.settings.postgres_test \
  --junitxml=/private/contracts/backend-postgres.xml

make check-owner-tenant CYCLE_SETTINGS=config.settings.postgres_test
```

`make test-connected-cycles CYCLE_EVIDENCE=/private/contracts` selects the joined HTTP paths, ongoing cycle, signing recovery and additive-fixture tests. `make test-cycle-contract CYCLE_EVIDENCE=/private/contracts` regenerates the current-time agreement contract; the controlled-clock test writes to a distinct filename so it cannot replace this fresh contract with expired sessions. Mock completion responses and capability grants are exported unchanged for onboarding, both signatures, capture/settlement and change signing.

## Evidence boundaries

Rental payments, beneficiary onboarding and signatures use the explicit mock provider. Full-cycle/ongoing tests use controlled clocks and direct task calls where required; these runs do not establish deployed scheduling or external provider behavior. See the independent [local Redis/Celery/beat evidence](../owner-tenant-runtime-verification/README.md) and [deployment/runtime guide](../../deployment/OWNER_TENANT_STAGING_RUNTIME.md) for that layer.

This archive does not claim remote deployment, original historical advertisement recovery, real Google sign-in, device push delivery, external payment/signature provider acceptance, or exhaustive elimination of every possible edge case. Android, actual-network socket and runner evidence is recorded separately in the mobile repository.

After the successful Android native cycle, [five fresh canonical readbacks](native-fixture-c-final-readback.json) confirmed both owner profiles ready, the same active lease/document for both actors, a paid zero-balance invoice, and its captured attempt with the matching receipt. Capture settlement remains pending because that native flow does not request settlement. The owned loopback API and disposable PostgreSQL cluster were then stopped; their database files and all private fixture journals were preserved.

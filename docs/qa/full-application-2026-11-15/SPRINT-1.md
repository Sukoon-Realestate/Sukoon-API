# Sprint 1 remediation — 16 November 2026

**Partial completion; local changes only. No deployment, release upload or production data change.** Work was performed in `Sukoon-API-sprint01` and the separate `sokoun` checkout. Concurrent unrelated edits in both checkouts were preserved. Original 15 November evidence remains unchanged; new evidence is under [sprint-1-2026-11-16](evidence/sprint-1-2026-11-16/).

## Fixes and reproductions

| Finding | Reproduction before change | Local result |
|---|---|---|
| MOB-001 | Four new transport cases rejected Accepted's `approved` request value, for visits/requests and populated/empty responses. | Explicit filter mapping now sends `confirmed`. All/Pending/Rejected and legacy response aliases remain supported. Four transport cases pass; eight real Django HTTP cases pass across both endpoints, Arabic/English and populated/empty collections. |
| PRIV-001 | New Arabic and English translation checks failed against the notices promising phone disclosure. Current backend source and tests establish that acceptance does **not** reveal account numbers. | Tenant pre-submit notice, owner acceptance notice and legacy phone labels now state that numbers remain private and communication uses Sokoun chat. Regenerated both locale assets; removed the banner's two-line cap so the notice can wrap. No disclosure/acceptance/notification behavior was changed. |
| ADM-001 | Rendered the existing page with new verified and unverified users and no reputation data. Both tests failed because the page invented 5.0/4.5. | The score card explicitly shows `غير متاح` and explains that authoritative evaluation data was not supplied. Removed the misleading rating star; verification, reports, property counts, activity and account actions remain intact. Both cases pass. |
| WEB-001 | Two new Arabic/English render checks failed: noninteractive badges lacked unavailable semantics and the hero/FAQ falsely promised store availability. | Both locales now explicitly say download links are unavailable. Badges carry a visible explanation and `aria-disabled`. No store listing, release date or prelaunch status was invented. Real public listing URLs remain a launch prerequisite. |
| SEC-001 | Fresh npm audits reproduced admin **1 critical / 3 high / 7 moderate**, merged **1 critical / 0 high / 7 moderate**. | Both lockfiles/manifests use Next.js and eslint-config-next **16.4.6**, with compatible sharp/source-map-js/zod patches. Fresh audits show **0 critical / 0 high / 7 moderate** each. Production webpack builds and regressions pass. |

The Accepted enum's Dart identity remains `approved`; only its explicit wire value changed. Existing cache keys and localized tab labels remain stable. Backend filters were preserved rather than extended with a second request spelling.

PRIV-001 corrects stale mobile copy to the current no-disclosure backend contract and published policy. The original finding's suggestion that acceptance discloses numbers does not describe the current source. PostgreSQL tests verify hidden numbers in pending, accepted, rejected/cancelled, property and chat reads, including repeated acceptance and localized notices. No legal-policy publication was performed.

## Verification

| Check | Result and evidence |
|---|---|
| Focused Flutter data, bilingual privacy assets and contact-refresh lifecycle | **15 passed** — [focused log](evidence/sprint-1-2026-11-16/mobile-focused.log). Covers legacy response aliases, request route/query, accepted/empty mapping, account replacement and notification refresh. |
| Broader tenant/owner visit regressions | **79 passed, 1 failed** — [log](evidence/sprint-1-2026-11-16/mobile-regression.log). The remaining `renders the O-REQ-ICON-B request card states` expects three chat icons but finds two; the exact failure already exists in the [original report](mobile-failures/owner_visit_requests_flow_test.dart.md). It was not weakened or reclassified as fixed. Three additional failures were obsolete Back-icon finders; they now use the app's shared `SokounIcons.back` and their navigation/state assertions pass. |
| MOB-002 bounded widget reproduction | **2 passed**, three validation → Back → mode selection → Back → inventory attempts per test, with normal and reduced motion — [log](evidence/sprint-1-2026-11-16/navigation-reproduction.log). Validation feedback was allowed to dismiss before tapping the toolbar; headers were scrolled into view. No create request was sent and no Flutter exception was captured. This is a negative reproduction, not closure of the intermittent finding. |
| PostgreSQL privacy, association and existing visit status-filter regressions | **9 passed** — [JUnit](evidence/sprint-1-2026-11-16/backend-postgres.xml), [log](evidence/sprint-1-2026-11-16/backend-postgres.log). Uses a disposable loopback QA database via the existing Make baseline target with an explicitly limited pytest selection. |
| New real HTTP Accepted matrix | **8 passed** — [JUnit](evidence/sprint-1-2026-11-16/filter-contract-postgres.xml). Both collections × Arabic/English × populated/empty; pending rows are excluded. This test requires PostgreSQL, like the existing collection projections. SQLite's unsupported JSON/read semantics are not treated as product regressions. |
| SQLite limited privacy/association selection | **3 passed, 4 skipped** for PostgreSQL-required cases. These four were subsequently covered by the nine-case PostgreSQL run. |
| Admin regressions, including store and reputation cases | **60 passed** — [log](evidence/sprint-1-2026-11-16/admin-tests.log). |
| Merged build-configuration tests | **3 passed** — [log](evidence/sprint-1-2026-11-16/landing-tests.log). |
| Production builds | Both **passed with `npm run build -- --webpack`**, including TypeScript/static generation — [admin](evidence/sprint-1-2026-11-16/admin-build-webpack.log), [merged](evidence/sprint-1-2026-11-16/landing-build-webpack.log). Default Turbopack builds hit a local CSS-worker `binding to a port / Operation not permitted` restriction, including an escalated retry. Default-bundler validation remains open; no build config was changed to hide it. |
| npm advisory repeat | **0 critical, 0 high, 7 moderate** per tree — [admin](evidence/sprint-1-2026-11-16/admin-audit-after.json), [merged](evidence/sprint-1-2026-11-16/landing-audit-after.json). |
| Lint | Full-tree gate remains red. Captured run had **103 errors / 7 warnings**, including 12 CommonJS-rule errors in the two new Node test harnesses. Those two files now document their CommonJS exception and both pass scoped ESLint. Other baseline lint issues remain open; no global lint rule was disabled. |
| Hosted read-only repeat | **54/56** met expectations; both association URLs again returned **504** — [JSON](evidence/sprint-1-2026-11-16/hosted.json). No authenticated business writes were made. |

The 17 PostgreSQL cases are separate from the Flutter and JavaScript counts. These selections are not a full backend or full mobile-suite rerun. Simulator/device, English runtime navigation, profile/release Back reproduction, accessibility layout and release signing acceptance were not established in this pass. Widget tests do not prove native/profile behavior or production readiness.

## Still unresolved

- **MOB-002:** preserve as intermittent. Capture a Flutter stack during the original English Owner → Accepted → Add property → Single unit → empty Next → Back → Back journey in a fresh dev app and a profile/release build. No speculative navigation or global error-handler patch was made.
- **HOST-001:** hosted 504s persist. Local handlers return explicit 503 when release identities are absent and correct JSON with configured test identities. Gateway/routing cause and actual release certificate/team/bundle configuration are unproven. Fix/verify deployment routing and real identities in a separately authorized release task; no signing identities were guessed or replaced.
- **WEB-001 launch acceptance:** messaging is truthful locally, but real listing destinations and installed/uninstalled-device checks remain open.
- **SEC-001 residual tooling:** minimatch 10.2.6 and six dependent TypeScript ESLint packages still produce seven moderate findings per tree. No forced cross-major minimatch override was applied. Deployed package versions were not established.
- **SEC-002:** Python lockfile remediation remains open. The retained audit has 124 advisory entries across 13 packages. black/pytest are tooling; framework, identity/social/OAuth, certificate, ASN.1 and PDF packages require compatible updates plus identity/authorization/media/lifecycle regressions. Neither lockfile nor shared Python environment was mutated. See [security triage](SECURITY-ADVISORIES.md).
- **QA-001/QA-002:** the full mobile baseline and frontend lint are still red. The one remaining targeted owner-card assertion is retained with its original evidence. No production-readiness sign-off is given.
- **ADM-003 and the remaining backlog:** audit failure feedback, CSV export, locale catalogs, framing hardening and broader connected acceptance were not changed in this Sprint 1 slice. Intentional company release gates remain in place.

## Repeating the focused checks

From `sokoun/apps/sokoun_app`:

```sh
flutter test --no-pub test/tenant_visits_data_test.dart test/visit_privacy_copy_test.dart test/visit_contact_refresh_test.dart
flutter test --no-pub test/owner_properties_flow_test.dart --plain-name 'empty single-unit validation returns'
flutter test --no-pub test/tenant_visits_flow_test.dart test/owner_visit_requests_flow_test.dart
```

From `Sukoon-API-sprint01/frontend`:

```sh
node --test tests/*.test.cjs
npx eslint tests/user-reputation.test.cjs tests/store-availability.test.cjs
npm run build -- --webpack
npm audit --json
cd landing
node --test scripts/vercel-build.test.mjs
npm run build -- --webpack
npm audit --json
```

Backend checks used the existing `make test-baseline-mvp` target with the shared lockfile-compatible Python, explicit private `BASELINE_OUT`, and a limited `BASELINE_PYTEST` selection containing `test_visit_filter_contract.py`, `test_visit_phone_disclosure.py`, `common/test_app_associations.py` and the two existing `TestPropertyVisitViews` status-filter cases. Set disposable `TEST_POSTGRES_*` values and `--ds=config.settings.postgres_test`; do not reuse production credentials. The local QA cluster started for this pass was stopped afterward.

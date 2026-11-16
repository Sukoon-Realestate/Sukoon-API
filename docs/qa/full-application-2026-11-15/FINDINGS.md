# Confirmed findings and security triage

Date: 2026-11-15, Africa/Cairo. No product fixes were applied. P1 means resolve or explicitly disposition before release; P2 means a normal prioritized fix. Scanner severity is kept separate from demonstrated application impact.

| ID | Priority | Finding | Evidence status |
|---|---|---|---|
| MOB-001 | P1 | Accepted Visits sends an unsupported status | Confirmed in the installed mobile app and both source contracts |
| MOB-002 | P1 | Back from listing creation leaves a screen without navigation | Intermittent: one failure, one successful repeat; underlying exception not captured |
| MOB-003 | P2 | Home category labels retain the previous language | Observed after switching Arabic→English and English→Arabic |
| PRIV-001 | P1 | Privacy policy contradicts viewing phone-disclosure behavior | Confirmed public policy and mobile notice; backend disclosure regression tests exist |
| ADM-001 | P1 | User behavior scores are fabricated from verification state | Confirmed local admin UI and source |
| ADM-002 | P2 | Audit CSV export button has no action | Clicked in local admin; confirmed missing handler |
| ADM-003 | P1 triage | Audit API errors can be displayed as an empty successful log | Source-confirmed; fault-injected browser reproduction pending |
| WEB-001 | P1 launch | Public download badges have no store destinations | Confirmed hosted UI and source; may be intentional before store launch |
| HOST-001 | P1 launch | Android/iOS association endpoints return 504 | Reproduced twice against the configured API origin |
| SEC-001 | P1 | Next.js dependency audit includes critical advisories | Affected lockfile versions detected; exploitability not tested |
| SEC-002 | P1 | Python lockfile contains published vulnerable versions | 124 advisory entries across 13 packages; includes development tools |
| SEC-003 | P2 hardening | Hosted admin lacks response-level framing restrictions | Neither X-Frame-Options nor CSP was present on sampled portal responses |
| QA-001 | P1 | Mobile regression baseline is red and can stall | 497 failed/error test records across 93 files; not 497 unique product bugs |
| QA-002 | P2 | Frontend lint baseline fails | 91 errors and 7 warnings |
| COPY-001 | P2 | Permissions page invites editing a read-only matrix | Confirmed local UI and read-only controls |
| KNOWN-001 | P1 if restored | Company signing/payment authority mismatch | Existing strict expected failures; deferred workflow |

## MOB-001 — Accepted Visits filter fails

Reproduce on the mobile app: open **Visit requests → Accepted** (Arabic: **طلبات الزيارة → مقبولة**). The screen replaces the list with `Status: ... approved ...` and an invalid-choice error. Pending, Rejected and All work; Rejected's empty-state reset returns to All correctly.

Expected: list accepted visits or show a successful empty state.

Cause: `TenantVisitFilter.approved.apiValue` returns the enum name `approved` in the separate mobile repository at `apps/sokoun_app/lib/features/tenant/visits/data/enums/visit_status.dart:62`. `tenant_visits_data.dart` sends it as the `status` parameter. `backend/core_apps/properties/filters.py:124` accepts `PropertyVisit.Status` values, including `confirmed`, and the legacy `completed` projection. It does not accept `approved`.

Fix direction: use an explicit wire-value mapping for Accepted and check both visit and visit-request collections. Preserve legacy response parsing separately from request values. Add an end-to-end test that uses the actual backend filter choices, in Arabic and English, with accepted records and an empty collection.

## MOB-002 — Listing Back flow reaches an unrecoverable screen

Observed sequence in the installed dev app (one failure; a fresh repeat after cold relaunch returned correctly): switch to English → Owner workspace → My properties → Accepted tab → Add property → Single residential unit → press Next photos with the form empty → Back to creation-mode selection → Back again.

Actual: the app displays only an information icon on a blank background. Its entire navigation shell, Back control and recovery actions disappear. Sending the app to the background and opening it again retained the same screen. A cold relaunch restored the owner inventory. Repeating the same validation/Back sequence then returned correctly, so treat this as intermittent. No property was submitted or published.

Expected: return to My properties with its tabs and navigation intact. If an unexpected exception occurs, provide an actionable recovery path and preserve the local draft safely.

The underlying Flutter stack was not captured. The simulator system-log query only returned an unrelated Photos/CoreData service error; do not attribute this failure to that message. The appearance is consistent with the debug fallback in `main.dart` and the icon-only `ExceptionView`, but that is an inference, not a proven root cause. Reproduce on a fresh dev run and a release/profile build before declaring its production scope.

## MOB-003 — Home categories retain the previous language

Reproduce: load Individual Home in Arabic, then change the app language to English in Account → Privacy and preferences → Change language. Return to Home. The surrounding app controls change to English, but property-type categories remain Arabic. After a cold relaunch in English, categories load as Apartment/House/etc. Switching back to Arabic updates the app controls but leaves those English category labels. This was observed in both directions.

Expected: language-dependent catalogs are refreshed or selected from the correct locale cache when the app language changes. Property titles authored in Arabic are not part of this finding. The underlying request/cache invalidation cause was not traced; check Home category state, filter-option caches and locale-aware request descriptors.

## PRIV-001 — Phone privacy statements disagree

The hosted Arabic privacy policy says that account phone numbers are not displayed as a communication method between users. The viewing-request form says that after acceptance the owner sees the requester's number and the requester sees the owner's number. These communicate different privacy behavior.

Reproduce: **Account → Privacy and preferences → Privacy policy**, then inspect the notice in **property details → Request a visit**. Public policy evidence: [hosted-privacy-policy.json](evidence/hosted-privacy-policy.json). Backend acceptance/disclosure behavior is exercised in `backend/core_apps/properties/tests/test_visit_phone_disclosure.py`.

Expected: policy, pre-submit notice, actual disclosure scope and revocation behavior agree. Decide the intended product behavior, then align policy and both participants' notices. This finding documents contradictory app behavior/copy; it is not a legal compliance conclusion.

## ADM-001 — Fabricated behavior rating

Reproduce in the Next.js portal: **Users → a newly created user**. The synthetic verified account, with no reputation history, shows **5.0** under **تقييم السلوك**.

Source: `frontend/src/components/admin/pages/users/[id]/page.tsx:247` renders `user.is_verified ? '5.0' : '4.5'`. Verification is not a behavior-rating calculation. Unverified users are assigned 4.5 without evidence.

Expected: show an authoritative rating and its basis/count, or an explicit unavailable state. Do not derive reputation from identity verification. Regression check: new verified and unverified accounts with zero reviews must not receive invented scores.

## ADM-002 — Audit CSV button is inert

Reproduce: **Platform administration → Activity logs → Export CSV**. Clicking changes nothing and initiates no export.

Source: `frontend/src/components/admin/pages/system/logs/page.tsx:120` renders the enabled button without `onClick`, a link, form action or download target. No export function exists in that component.

Expected: a real, correctly scoped export with CSV formula-injection handling, pagination/completeness semantics and error feedback, or a clearly unavailable action. Verify with a nonempty audit dataset as well as an empty result.

## ADM-003 — Audit read errors are hidden

Source: `frontend/src/components/admin/pages/system/logs/page.tsx:19` catches `fetchAuditLogs` failures and only writes to `console.error`. It then ends loading. `logs` remains empty on initial failure, or retains an earlier query's rows. The rendered empty state says **لا توجد سجلات مطابقة**. There is no visible failure state or retry action.

Browser fault-injection reproduction remains pending: keep a valid admin session, make the audit endpoint return 503, then change its search/type filter. Inspect whether the UI shows an error rather than an empty or stale successful result.

Expected: distinguish unavailable audit data from a successful empty collection; identify stale results and offer retry. This matters because administrators may interpret an empty audit log as absence of activity.

## WEB-001 — Download path ends at noninteractive badges

Reproduce on `https://www.sukoon.rent/ar`: click **حمّل التطبيق**. The page navigates to `#download`, where App Store and Google Play are noninteractive containers. The page and FAQ say the app is available on both stores, but provide no store URLs.

Source: `frontend/landing/src/components/ui/StoreButtons.tsx:18` explicitly postpones destinations; each badge is a `span`. This can be intentional during preparation, but is incomplete for a public launch claiming availability.

Expected: correct listing links and accessible link semantics, or truthful prelaunch availability text. Check English and Arabic, desktop and mobile, and installed/uninstalled app behavior.

## HOST-001 — Association endpoints unavailable

Both `https://api.sukoon.rent/.well-known/assetlinks.json` and `https://api.sukoon.rent/.well-known/apple-app-site-association` returned HTTP 504 in two separate bounded checks. See [first run](evidence/hosted.json) and [repeat](evidence/hosted-repeat.json). The health endpoint returned ready during these checks.

Impact: these endpoints cannot currently establish trusted Android App Links or iOS Universal Links for that origin. The production mobile signing identities, entitlements and configured link domains were not independently validated, so this does not establish failure on every configured domain.

Expected: direct HTTPS 200 JSON matching release certificate/package and team/bundle identities, without redirects or gateway failures. Recheck with `python3 docs/qa/full-application-2026-11-15/rerun.py --hosted`.

## SEC-001 — JavaScript dependency advisories

`npm audit --json` reports **1 critical, 3 high and 7 moderate affected packages** for the standalone admin lockfile, and **1 critical and 7 moderate** for the merged landing/admin lockfile. These counts overlap across dependency trees and are not unique exploits.

Standalone admin pins Next.js 16.3.5; merged app pins 16.3.8. The scanner reports affected Next.js versions for multiple RCE, cache, information-disclosure, SSRF and denial-of-service advisories. The standalone tree also flags sharp, source-map-js and zod at high severity. See [complete advisory ledger](SECURITY-ADVISORIES.md), [admin audit](evidence/frontend-audit.json), and [merged-app audit](evidence/landing-audit.json).

Expected: triage applicability against the actual deployed build, update compatible patched dependencies, and repeat audit, build and functional tests. No exploitability or successful compromise was demonstrated by this pass.

## SEC-002 — Python dependency advisories

The pinned default lockfile scan reports **124 advisory entries across 13 packages**. Django 4.2.11 accounts for 81 entries; affected packages also include DRF, Djoser, OAuth/social auth, certificate/parser tooling and development tools. Some findings may have platform, configuration or feature prerequisites. Developer tools must be separated from the production runtime inventory before exposure is scored.

Evidence: [machine-readable scan](evidence/backend-audit.json) and [advisory/fixed-version ledger](SECURITY-ADVISORIES.md). Scan input was extracted from `backend/Pipfile.lock`; the audit tool ran in a temporary virtual environment. It did not replace the app environment.

Expected: establish deployed package versions, prioritize reachable runtime advisories, update the lockfile deliberately, and run identity, authorization, media/document and lifecycle regressions. Scanner detection is not proof that any endpoint is exploitable.

## SEC-003 — Portal framing hardening absent

Sampled hosted admin responses, including `/admin/login`, had HSTS but neither `X-Frame-Options` nor a `Content-Security-Policy` header. The read-only probe retains selected response headers in [hosted-repeat.json](evidence/hosted-repeat.json).

Expected: define an intended framing policy and verify it in a browser. If embedding is not required, apply response-level restrictions such as CSP `frame-ancestors`. No authenticated clickjacking exploitation was performed; treat this as a hardening gap rather than a demonstrated takeover.

## QA-001 — Mobile regression baseline and hangs

The full app test run recorded **13,124 passed, 32 skipped, 425 error and 72 failure test cases**, across **93 failing files**. It stalled and was interrupted after approximately 61.5 minutes of recorded events; it has no successful terminal event. Hidden setup/teardown and loader events are separated by the summarizer. Shutdown errors remain in the raw evidence and are not automatically product defects.

An independent bounded rerun of `rental_mock_provider_test.dart`, `rental_listing_categories_test.dart` and `company_role_work_status_test.dart` produced **166 passed / 7 failed**. Those failures include company workspace selection, role-status widget finders and saved-price/category expectations. Each needs fixture/selector/contract/product classification; do not weaken assertions to obtain green results.

See [failure index](MOBILE-FAILURES.md), per-file reports and [independent rerun](evidence/mobile-targeted-rerun.log). The supplied [rerun tool](rerun.py) executes individual case IDs or failed files with a wall-clock timeout. Shared core separately passed all **345 tests**.

## QA-002 — Frontend lint baseline

`npm run lint` reports **91 errors and 7 warnings**. Some errors are CommonJS test/script imports being linted as production TypeScript; others require file-specific review. The production build and all 56 standalone admin tests pass, so this finding is a failing quality gate rather than proof of 98 runtime bugs. See [lint output](evidence/frontend-lint.log).

## COPY-001 — Read-only permissions matrix invites editing

The Roles page labels its matrix **مصفوفة الصلاحيات (انقر للتعديل المباشر)**, while every matrix cell describes a read-only server rule and role Edit buttons are disabled. Source: `frontend/src/components/admin/pages/roles/page.tsx`.

Expected: text accurately describes read-only policy and directs authorized changes through the existing staff-grant flow. Do not add direct matrix editing merely to satisfy the current label.

## KNOWN-001 — Existing company authority mismatch

Two existing strict expected failures reference `BUG-AUTH-01`. `test_advanced_company_passport_v2.py:295` describes signing/payment commands requiring membership flags while selectable signer/payer roles require approved mandates. `test_purchase_events.py:169` describes a payment-capable member's notification being suppressed without a selectable role.

This is an existing acknowledged domain inconsistency, not a newly proven hosted exploit. Preserve the current release gates; make the product decision on membership-versus-mandate authority and resolve both tests before restoring the affected company workflows.

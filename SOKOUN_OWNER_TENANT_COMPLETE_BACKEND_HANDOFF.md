# Sokoun owner–tenant: complete backend handoff

**Prepared: 2026-10-12 UTC. Audience: Django backend engineer, QA and release operator.**

This single file includes the complete verification report, Django implementation/deployment guide, API contract and backend return form, plus the integration-runner instructions. Send this file to the backend engineer; the three separate source guides do not need to be attached.

**Current outcome: Not ready for full integration sign-off.** This consolidation preserves the recorded 2026-10-12 results; it is not a new live test or deployment. Both replacement accounts passed login, session refresh and scoped app reads. Latest HTTP checks: **25 PASS / 5 FAIL / 12 BLOCKED**. Latest Flutter live checks: **7 passed / 1 failed / 2 skipped**. Local checks passed within their documented scope. Passing reads are not completed business cycles.

The approved billing sequence is: **final signatures → 48-hour inventory hold and one initial invoice containing rent plus deposit → successful required capture → active agreement**. Possession, financial settlement, refunds and owner payout remain separate states. Keep existing records and operation identities intact.

## Contents and reading order

1. [Part A — Latest findings and exact work required](#part-a)
2. [Part B — Django implementation, verification and deployment](#part-b)
3. [Part C — Exact requests, responses and compatibility rules](#part-c)
4. [Part C, section 12 — Backend return form to complete](#c-12-backend-return-form)
5. [Part D — Integration-runner setup and rerun procedure](#part-d)
6. [Optional repository references](#repository-references)

Each part retains its original section numbering. A section number without a named part refers to the current part. Part A contains the latest observed results; explicitly historical results later in this file retain their original timestamps and do not supersede Part A. Proposed or illustrative JSON remains labeled as such and must not be reported as a deployed response.

Repository references identify supporting source code, earlier reports and evidence artifacts. All instructions from the three source guides and the runner procedure are included below; these references are supplemental and may require the mobile repository to open. No account password, Google token, session cookie or private credential file is included.

## Backend work to address first

| Order | Required work | Acceptance evidence |
| --- | --- | --- |
| 1 | Restore the original banner artwork on its existing advertisement/operation | Original byte length and SHA-256 match before mock activation; same receipt/dates on replay; media/placement survive replica change and redeployment |
| 2 | Correct Arabic/English advertising caching and server-owned planning text | Alternating language requests to the same URL work on warm and cold caches; payload text, Content-Language and Vary agree |
| 3 | Supply an eligible pending/confirmed visit for the working owner/tenant and separate secondary actors | Complete C03 invite/accept/draft/cancel/replay and separate unrelated-account denial tests; cancelled sources remain ineligible |
| 4 | Resolve first-read financial-closure consistency | Both actors' collection/detail/Rental Center agree immediately after cancellation, without relying on a GET to finalize state; funded liabilities remain open until resolved |
| 5 | Correct the returned route/schema documentation | Preserve working auth/refresh/, actual public envelopes and required rental-capability subject_id; fill the endpoint return table with real sanitized requests/responses |
| 6 | Verify the approved billing flow and dependent services | Signed unpaid combined-invoice fixture, provider sandbox capture/signature/refund/payout, inventory-race and scheduled-job evidence; enable only independently verified capabilities |
| 7 | Supply deployment and integration evidence | Immutable API/worker/scheduler versions, applied migrations, exact schema hash, PostgreSQL concurrency results, storage durability, rollback/recovery and device results |

### Original banner identifiers for BE002

These are existing test-resource identifiers, not credentials. Preserve them during recovery.

| Field | Value |
| --- | --- |
| Approved nonproduction base URL | `https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/` |
| Advertisement ID | `85295dd1-f8bd-4c82-a903-9bdc3d90af98` |
| Original create operation ID | `74682688-4428-413c-a1ae-c4b87222c687` |
| Original mock payment operation ID | `74682688-4428-413c-a1ae-c4b87222c687-payment` |
| Original asset in mobile repository | `packages/core/assets/png/logo.png` |
| Original byte length | `28970` |
| Expected SHA-256 | `dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b` |
| Observed remote byte length on 2026-10-12 | `1213` |
| Observed remote SHA-256 | `303a95728f601403f468dd9abe1cd8618d1f9fee2ef68e7cb57a257337b5b370` |
| Latest observed status | `pending_payment`; activation stopped before dispatch because the original bytes did not match |

Only after restoring and verifying the original artwork, replay the original mock-payment intention at `POST advertising/v1/owner-advertisements/85295dd1-f8bd-4c82-a903-9bdc3d90af98/mock-payment/` with this exact body:

```json
{"operation_id":"74682688-4428-413c-a1ae-c4b87222c687-payment","payment_mode":"mock"}
```

This is the existing banner mock operation, not rental PSP capture. Complete the current-state and media checks in Parts A, B and D before replaying it.

---

<a id="part-a"></a>

## Part A — Latest verification, blockers and required backend return

Included source: `docs/backend/SOKOUN_OWNER_TENANT_BACKEND_REPLY_VERIFICATION.md`.

Date: **2026-10-12 UTC**. Audience: backend engineer, mobile engineer, QA and release operator.

**Outcome: Not ready for complete owner–tenant integration sign-off.** The replacement owner and tenant now authenticate, refresh their sessions and read their scoped data through the real app transport. The original banner returns different artwork bytes, advertising language caching still fails, and the supplied pair has no eligible source visit for a new invitation. Full business journeys, deployed signing/payment providers, workers and device flows remain unverified.

<a id="a-1-sources-and-evidence-boundaries"></a>

### 1. Sources and evidence boundaries

Reviewed the supplied root-level `SOKOUN_OWNER_TENANT_DJANGO_IMPLEMENTATION_AND_VERIFICATION.md` and `SOKOUN_OWNER_TENANT_BACKEND_RETURN.md`, the original cycle specification, current Flutter callers/models and the API contract. The supplied Django guide was byte-identical to the earlier canonical guide when received; the separate backend return contains the implementation claims. Original supplied files and historical audit results are preserved.

- [Updated Django implementation and verification instructions](#part-b)
- [Exact client contract, bodies/responses and remaining backend return fields](#part-c)
- Initial seed/public evidence and local verification[^repo-1]
- Replacement-account evidence and exact follow-up observations[^repo-2]
- Final verification summary and follow-up test counts[^repo-3]
- [Integration runner setup, fixtures, recovery and coverage](#part-d)

Target: `https://sukoon-app-y4j5r.ondigitalocean.app/api/v1/`, identified as nonproduction by the backend reply. The backend claims `Sukoon-Realestate/Sukoon-API` at `5c1aaa5` plus working-tree updates; the exact deployed SHA, image digest and schema artifact were not supplied. No Django checkout, deployed database, provider dashboard or scheduler control is available in this workspace.

New remote actions sent by the client are GET/OPTIONS and authentication/refresh exchanges only. **No business command, database reset, real charge, banner publication, production flag change or deployment was performed.** The final Python scenario run explicitly enabled eligible test commands, but source-visit and original-artwork checks stopped both scenarios before any business POST. Initial lease observations changed during readback; backend reconciliation/job causality needs server evidence, as described below.

<a id="a-2-backend-claims-compared-with-observed-behavior"></a>

### 2. Backend claims compared with observed behavior

| ID / priority | Claim / requirement | Current evidence | Required action and closure criterion |
| --- | --- | --- | --- |
| RET-AUTH / partial verification | Four pre-seeded verified accounts ready | Original four seeds returned **401**. Privately supplied replacements now pass Google owner/password tenant login, verified current-user checks and real Flutter scoped reads | Keep the original seed failure as historical evidence. Supply another distinct owner and tenant for unrelated-account denial cases. Do not alias the working pair as four actors. |
| RET-REFRESH / confirmed contract error | Refresh is `auth/token/refresh/` | OPTIONS there is **404**. Production `DioService.refreshSession()` at **`auth/refresh/`** succeeds for both replacements, followed by the same authoritative identity and scoped reads | Correct the return or deploy a deliberate compatible alias. Preserve the current client route. Rotation, old-token revocation and concurrent-expiry tests remain separate. |
| BE001 / verified public scope | Guest Home/properties/catalogs repaired | Home, properties, types, filters, governorates and cities return **200** in English and Arabic | Public permission regression is resolved within these checks. Private-resource authorization, property creation and full C01 remain separate. |
| RET-SHAPES / documentation correction | Home uses featured/recent arrays; catalogs use direct arrays | Actual Home is `data.results` with pagination/banner; several catalogs also wrap `results`; filters use named catalog fields | Keep existing app parsers and correct the returned wire examples. Do not rewrite the app to match descriptive pseudocode. |
| BE003-ADS / confirmed important issue | Locale headers and cache variation correct | Same plans/feed URL can return `Content-Language: en` to Arabic requests, or retain Arabic for a later English request. Plans payload labels also retain the cached language. `Vary` is present; query-language overrides work | Fix the effective language/cache key at the layer responsible. Warm/cold cache alternating-header tests must pass for both plans and public feed. Do not add per-screen query workarounds. |
| DEP001 / disabled contract verified | Planning discovery is safe empty 200 | Initial preflight lacked two fields. The later recorded response includes `verified_services:[]` and `expires_at:null`, with empty grants/services | Earlier missing-field observation is superseded by the recorded later response. Keep planning disabled; return verified service/expiry/account/action evidence before enabling. C08/C09 are still not deployed. |
| RET-PLANNING-LANG / important localization follow-up | Server-owned blocking text follows language | Recorded Arabic planning response still contains English blocking reasons | Localize server-owned reasons while preserving enum/capability IDs. Do not translate these messages on the client. |
| C03 / fixture blocker | Invitation consumption and cancellation replay pass | The pair's actual source visit is **`canceled`**; the owner's eligible-tenant picker is empty. Configuration allows creation, but this relationship cannot authorize it | Supply an actual pending/confirmed visit for this owner/property/tenant and valid terms, then execute consumption/cancel/replay. Keep the cancelled source ineligible; do not weaken consent checks. |
| GAP001 / partial verification, consistency follow-up | Never-occupied cancellation closes immediately | Three owner detail reads initially showed `open`, revision 2. Their next Rental Center reads showed `closed`, revision 3, zero balance and no next action. Later shared owner/tenant collection/detail/center reads agree at closed without further revision changes | Closure projection is verified for these historical examples, not funded cancellations. Investigate whether reconciliation happens during GET or a job. Make list/detail/center agree immediately after the authoritative transition; do not require opening Rental Center to repair state. |
| BE002 / confirmed original-artwork blocker | Original banner repaired and disk durable | Matching original owner/ad/create operation verified. Media now returns **200 image/png**, but **1,213 bytes** with a different digest from the original **28,970-byte** upload. Ad remains `pending_payment`; activation was not sent | Restore the original artwork for the same ad/operation and prove its digest before same-key mock activation/replay. Then verify public placement and redeploy/replica durability. HTTP 200 alone does not close BE002. |
| DEP002 / external verification incomplete | Rental phases 2–6 implemented with mock adapters | Queried closed legacy subjects grant only `rental_center`, with no actions. No signed/active fixture, provider event artifacts or job logs | Obtain subject/action grants for the actual signed/active fixtures and return sandbox capture/signature/refund/payout, scheduled-job and ledger evidence. Closed-lease capabilities alone do not establish global service availability. |
| RET-RELEASE / deployment evidence missing | `5c1aaa5 + working tree updates`, Django `5.0.x/5.1.x`, migrations clean | Exact immutable deployment/runtime identity absent; `makemigrations --check` cited as proof of applied migrations | Return SHA/image/runtime versions/schema hash and `migrate --check` output from deployed settings, plus compatible API/worker versions. |

The latest planning response proves only disabled discovery. No blanket capability enabling or relaxed expiry/verification checks were added to the app.

<a id="a-original-artwork-and-closure-evidence"></a>

#### Original artwork and closure evidence

The original uploaded file is logo.png[^repo-4], independently hashed again in this run. Expected SHA-256: `dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b`. Observed remote SHA-256: `303a95728f601403f468dd9abe1cd8618d1f9fee2ef68e7cb57a257337b5b370`. The earlier original-media handoff[^repo-5] identifies the same advertisement and create/payment operations. Backend must explain and correct the byte difference; this report does not infer the cause or image contents from the digest alone.

See initial detail[^repo-6], following center[^repo-7], and later paired checks[^repo-8]. No client mutation occurred between these reads. A background job and read-triggered reconciliation are both possible; only backend logs/database evidence can establish the cause.

<a id="a-3-implemented-flutter-changes"></a>

### 3. Implemented Flutter changes

The user explicitly selected the backend's latest billing policy: completed signing starts a 48-hour inventory hold; one initial invoice includes first-period rent and security deposit; successful required capture activates the agreement. This supersedes the earlier initial separate-deposit and activation-before-invoice wording.

- Structured signed agreements now link to the existing lease-scoped invoice screen before activation. The entry uses existing navigation and workspace guards. It does not authorize payment or change lease state.
- Existing invoice/deposit DTOs already represent the combined invoice: rent and deposit remain separate lines and the deposit projection points to that invoice. No unnecessary wire-model replacement or client amount calculation was introduced.
- Checkout remains `invoice_id`, `quote_id`, `expected_revision`, `request_key`. The app still requires the quote to match the full server balance, explicit permissions, current capability evidence and durable payment identity.
- Added tests for combined allocation parsing, deposit linkage, full versus rent-only quote totals, the unchanged checkout body, persisted key before checkout, no local activation, and Arabic/English invoice navigation at phone/tablet widths and larger text.
- Added executable Markdown examples for the combined invoice/deposit projection and the existing public Home envelope. They are illustrative contract fixtures tested by Dart DTOs; they are not fabricated live invoices.
- Corrected conflicting older billing handoff text while preserving original supplied replies and historical financial records.

The default production gates, working authentication route and public envelope parsers remain in place. Paid services were not made available by passing local tests.

<a id="a-4-verification-performed"></a>

### 4. Verification performed

The initial recorded HTTP run started at **2026-10-12 10:01:05 UTC**, completed at **10:01:14 UTC**, and returned **18 PASS, 8 FAIL, 10 BLOCKED**. These are individual checks, not 18 completed business cycles. The eight failures are four seed logins, three advertising language checks, and the refresh route stated in the backend reply. See the machine-readable report[^repo-9].

After the user supplied the replacement pair, the expanded HTTP scenario run at **10:26:24–10:26:42 UTC** returned **25 PASS, 5 FAIL, 12 BLOCKED**. The five failures are three advertising locale checks, the reply's refresh URL, and original-artwork mismatch. The twelve blocked entries cover missing secondary actors, the ineligible source visit, unrelated-account denial and remaining complete journeys. The current report[^repo-8] records the exact cases; passing reads are not completed rental cycles.

Commands, run from `apps/sokoun_app`:

```bash
make ownerTenantCyclesCheck FLUTTER=/Users/aait/Downloads/flutter_3.44_7/bin/flutter
python3 tool/audit/owner_tenant_cycles.py --private-dir /PRIVATE_DIRECTORY --evidence-dir /NEW_EVIDENCE_DIRECTORY
python3 tool/audit/owner_tenant_cycles.py --private-dir /PRIVATE_DIRECTORY --evidence-dir /NEW_SCENARIO_EVIDENCE_DIRECTORY --allow-mutations
SOKOUN_CYCLES_LIVE=true SOKOUN_CYCLES_PRIVATE_DIR=/PRIVATE_DIRECTORY SOKOUN_CYCLES_DART_REPORT=/NEW_REPORT.json /Users/aait/Downloads/flutter_3.44_7/bin/flutter test --no-pub --concurrency=1 --dart-define=SOKOUN_BYPASS_VERIFICATION=false test/owner_tenant_cycles_live_test.dart
```

Paths above deliberately omit the actual private credential directory. The runner's report refuses to overwrite previous evidence. Local tests have no live-service dependency; live tests are skipped unless explicitly enabled.

| Verification | Result / evidence boundary |
| --- | --- |
| New billing/navigation tests | **10 passed** locally, including both quote outcomes and Arabic/English navigation |
| Documentation contract examples | **12 passed**, including **28 parsed JSON blocks**; final focused analysis of all touched Dart verification files and the review widget is clean |
| Journal/audit safety tests | **23 passed** offline after replacement-account support: previous 14 cases plus Google wire/identity checks, failed-session cleanup, subject scoping, primary/secondary separation, ineligible source prevention, projection disagreement and wrong artwork stopping before activation |
| Existing cycle suites and focused analysis | **265 passed / 23 skipped** with default gates; **39 passed / 4 skipped** with planning enabled for fake transport only; two analysis invocations clean. Exact original command/results: local verification[^repo-10]. Counts overlap and are not distinct journeys. |
| Latest Python HTTP scenarios | **25 PASS / 5 FAIL / 12 BLOCKED**, exit 1; zero business commands dispatched |
| Latest real Flutter transport | **7 passed / 1 failed / 2 skipped**, exit 1. Both real actors pass authentication, refresh/current-user identity, invitation/lease/invoice helpers, lease/center DTOs and subject-scoped capabilities. Home, guest planning and English banner pass. Arabic banner language fails; secondary actors are skipped. See final report[^repo-11]. |
| Backend Django/PostgreSQL/job/provider tests | **Not run here**: backend checkout/runtime/provider access absent |
| Physical device / full Android or iOS journey | **Not run**; widget verification is not device/provider verification |

The first Flutter live test run incorrectly required the feature envelope's `key=success` on Home. Inspection of `TenantHomeData` and `BaseModel` confirmed that public Home intentionally permits a data-only envelope. The test was corrected to assert the actual collection schema/DTO and HTTP language behavior. This was a test expectation error, not an app Home defect; the initial observation file is preserved.

Discovery also tried a subjectless rental-capability request (400), an incorrect owner-list URL (404), and image-only Accept (406). These were probe mistakes, not backend defects. Corrected discovery used the app's `properties/owned/` path. The final runner uses an authorized capability `subject_id` and image MIME types plus `application/json` for media. Corrected media reads still fail the original-byte check. The initial seed Flutter result, **5 passed / 5 failed**, remains historical and is superseded for primary-account access by the replacement run.

<a id="a-5-per-cycle-acceptance-status"></a>

### 5. Per-cycle acceptance status

| Cycle | Status now | Remaining execution required |
| --- | --- | --- |
| C01 discovery → visit/chat/review | Public discovery and working primary actors verified; full cycle blocked | Owned/published exact-offer fixture with valid future availability, booking/decision readbacks, independent chat broadcast and eligible review |
| C02 rejection/cancellation | Blocked | Pending/accepted visits, documented reject enum, both projections, resubmission and accepted contact history |
| C03 invitation → legacy draft | Primary pair/scoped reads pass; new journey blocked before write | Pending/confirmed source visit; then consumption/cancel replay and fresh centers. Secondary actors required for separate denial tests |
| C04 signed agreement → initial payment → activation/handover | Client policy/navigation locally verified; live incomplete | Valid scoped capabilities, supported quote policy, sandbox signing/capture, hold expiry/race and handover |
| C05 recurring management | Live incomplete | Active lease, scheduled invoice job, maintenance/amendment/renewal/extension fixtures, no duplicate financial effects |
| C06 exit/settlement | Live incomplete | Funded/unfunded exit fixtures, handover, deposit/refund/dispute/payout ledger and participant readbacks; replacement remains gated |
| C07 banner | Original identity verified; original bytes mismatch | Restore expected artwork digest, same-ad mock activation/replay, visibility and media across redeployment |
| C08/C09 | Explicitly disabled, not deployed | Backend service implementation, real fixtures, capability grants and full consent/scope testing |
| S01 | Local identity/scope regressions available; full live chain blocked | Same exact offer snapshot through every persisted stage and both parties |
| S02 | Planning discovery disabled | Saved alert job evidence; routing/assistant providers and actual service gates |
| S03 | Client and runner safety locally tested | Live lost-response/restart/stale-revision/account-switch tests with authoritative lookup and no duplicated side effects |

The staging runner currently automates public/authentication/scoped reads and journaled C03/C07 regression scenarios. It explicitly reports the remaining full-cycle/provider/device work as blocked. A passed C03/C07 regression entry does not prove every scenario in the original cycle specification.

<a id="a-6-exact-next-backend-return"></a>

### 6. Exact next backend return

Return one evidence bundle containing:

1. Immutable API/worker/scheduler/WebSocket release identity, UTC deployment time, exact runtime versions and actual OpenAPI/schema artifact with hash.
2. Applied-migration evidence: `showmigrations --plan`, reviewed migration plan, **`migrate --check`**; separate model-drift result from `makemigrations --check --dry-run`.
3. Two additional distinct verified actors for unrelated-account tests, supplied privately; the replacement primary pair already works. Correct the original failed seed-account claim. Provide sanitized identity/relationship results; do not repeat passwords/tokens in Markdown.
4. Actual fixture IDs for property/offers/visits, pending and accepted invitations, cancellable legacy draft, signed unpaid combined-invoice agreement, active and ended leases, funded cancellation, invoice/payment/deposit/settlement, and original advertisement/operation/media digest. Include validity dates and approved reset/cleanup scope. Literal `uuid` is not a fixture.
5. Exact request/response JSON for the initial combined invoice, deposit projection, quote, checkout, capture lookup, signed/active lease and both Rental Centers. Include null/omitted field rules, supported policy version, late-capture policy and actual invoice/line type tokens.
6. Deployed C03 duplicate/consumption/cancellation replay evidence with an eligible source visit, consistent closure projections from the first read, and C07 restored original-byte digest plus same-operation mock activation/replay/public placement.
7. Advertising alternating-language cache regression output, including request/response language headers and localized labels on plans and feed.
8. PostgreSQL concurrency results, scheduled-job executions, outbox/realtime evidence, provider sandbox callbacks and ledger effects, storage proof across redeployment, and device/manual results where applicable.

After the remaining fixtures/media/cache issues are corrected, rerun `ownerTenantCyclesLiveRead` into a fresh evidence directory. Then run `ownerTenantCyclesLive` using the same private journal directory. Stop and reconcile uncertain operations before retrying. Keep undeployed/service-dependent scenarios blocked until their explicit prerequisites and acceptance cases pass.

<a id="a-7-device-and-external-service-test-sheet"></a>

### 7. Device and external-service test sheet

All rows below remain **not run**. Record device/OS/app build, backend release, actor aliases, timestamps, outcome and sanitized evidence for each row.

| Manual case | Steps and expected result |
| --- | --- |
| Owner/tenant navigation | Sign in with each role on Android and iOS; open invitations, lease detail, Rental Center and invoices through real entry points; switch accounts and verify no previous account data appears |
| Signed initial invoice | With a backend signed fixture, open the new invoice entry before activation; server combined balance and quote match; failed/pending checkout leaves the lease signed |
| Arabic/English and accessibility | Repeat at phone/tablet widths, RTL/LTR and enlarged text; invoice entry stays reachable, language changes refresh server text, no clipped controls |
| App restart and uncertain payment | In provider sandbox, lose the checkout response and restart; reconcile the same saved operation; no new key/charge or local success |
| Invitation and legacy cancellation | Fresh eligible visit → invite → tenant accepts → picker → draft → cancel → replay; verify both devices, consumed consent, closed unfunded center and no invoice |
| Original banner | After exact artwork restoration, recover the same original ad and operation; activate in mock mode; second device sees the same image; repeated activation preserves receipt/dates |
| External signing/payment/jobs | Backend and QA execute real sandbox callbacks, duplicate/out-of-order events, hold expiry race, recurring invoice jobs, refund/settlement/payout, storage replica/redeploy checks; attach provider and ledger evidence |

Deployment and Django implementation must be completed in the backend project. This report does not claim they were changed or deployed from the Flutter workspace.

---

<a id="part-b"></a>

## Part B — Django implementation, tests and deployment

Included source: `docs/backend/SOKOUN_OWNER_TENANT_DJANGO_IMPLEMENTATION_AND_VERIFICATION.md`.

Prepared: **2026-10-12**. Audience: backend engineer, QA, release operator, mobile integrator.

This guide translates the owner–tenant cycle specification[^repo-12] into backend work and acceptance criteria, checked against the Flutter implementation. Use it with [the API contract](#part-c) and [the backend reply verification](#part-a). The supplied reply has been reviewed; replacement actors now pass live authentication, refresh and scoped Flutter reads. Section 10 identifies the remaining implementation and verification work.

<a id="b-1-what-is-verified-and-what-still-needs-evidence"></a>

### 1. What is verified, and what still needs evidence

The repository contains the Flutter clients, typed API models, local tests, handoffs and earlier sanitized server observations. It does **not** contain the Django project, production database, worker configuration or provider dashboards. Backend implementation details below are requirements and recommended designs, not claims that those components already exist. Map the concepts to your actual Django apps and return the mapping; do not create a parallel rental subsystem merely to match these names.

Evidence levels used here:

| Label | Meaning |
| --- | --- |
| Client implemented | A reachable Flutter flow and typed request/response handling exist. Build/server/provider gates can still prevent use. |
| Locally verified | A test exercised client behavior using fixtures or fake transport. This does not prove deployed API behavior. |
| Historical server observation | A dated response in the previous audit; it must be rechecked against the release being delivered. |
| Backend required | A rule the Django service must implement and prove. Its current implementation is unknown without server evidence. |
| Policy decision | A business choice that code and tests cannot safely invent. Return the approved answer and version. |

The baseline mobile commit is `0e122774433b42e16a6643f33e886bdd29d897c9`; this guide and the companion client fixes are working-tree changes after it. The prior audit targeted **TEST-DO**, with observations on 2026-10-11 UTC (some reports dated October 12 local time). Its backend commit was not supplied. The original handoff performed no new remote operations. Reply verification subsequently performed public/participant reads, login and refresh exchanges. It sent no business commands or provider operations; see the dated verification report.

Historical sources: backend findings[^repo-13], audit report[^repo-14], flow matrix[^repo-15], captured evidence[^repo-16]. Preserve their timestamps and original outcomes when adding new evidence.

<a id="b-2-cycle-to-implementation-map"></a>

### 2. Cycle-to-implementation map

Paths below are relative to `apps/sokoun_app/lib/features/`. The linked folders contain the actual screens, Cubits and data helpers. The API companion lists wire contracts; do not infer endpoint availability from screen existence.

| Cycle | In-app entry and implementation chain | Server responsibilities / current boundary |
| --- | --- | --- |
| C01: listing → discovery → visit | Owner listing/draft screens → owner draft/inventory Cubits → owner/home[^repo-17] and rental_offers[^repo-18]; tenant Home/Search → property detail → `BookVisitCubit`; owner visit inbox → request detail/actions; tenant visits[^repo-19] / owner visits[^repo-20] | Listing ownership, moderation, publication, exact offer selection, schedule/slot availability, both inboxes, consent-based contact/chat, actual eligible review. Historical public discovery 401 and localization defects remain release checks. |
| C02: visit rejection/cancellation | Same visit detail/action Cubits; preserved note/date/offer and refreshed resource after conflicts | Authoritative allowed actions, reason requirements, permitted resubmission, contact disclosure history and notification consistency. Rejecting/accepting a visit does not allocate rental inventory. |
| C03: invitation → legacy draft | Owner eligible visit/tenant context → tenancy invitations[^repo-21] → tenant invitation response → `LeaseTenantPickerScreen` / `LeaseDraftCubit` → digital leases[^repo-22] | Pending/confirmed visit eligibility; seven-day invitation validity; atomic consent consumption; legacy body and raw response compatibility; owner draft cancellation. Latest historical tests resolved several older invitation/cancel defects. |
| C04: structured rental agreement | Property exact offer → rental interests[^repo-23] / terms proposal → structured invitation → `RentalAgreementCommandCubit` / `RentalAgreementData` → signing → rent management[^repo-24] → handover | Capabilities, versions, signatures, inventory holds/activation, invoice ledger, PSP capture and reconciliation. Client exists, but historical capabilities were empty; no deployed full-cycle proof. |
| C05: in-tenancy operations | My Rentals / rental center[^repo-25] → invoice, deposit, maintenance[^repo-26], changes[^repo-27], documents | Scheduled invoices, payment extensions, cost approvals, amendments, renewals, external payment claims, immutable documents and counterpart projections. Requires active-lease fixtures and jobs. |
| C06: move-out → closure | Rental Center → termination/change, handovers and condition reports[^repo-28], transition screens, settlement[^repo-29], disputes, refunds, payouts | Separate legal end, occupancy return, financial settlement, deposit, refund and owner payout states. Planning notice/replacement services historically missing. Cancelled unoccupied draft blocker text is historically contradictory. |
| C07: owner banner → tenant placement | Owner Home → banner ads[^repo-30] create/upload/recovery → tenant carousel | Independent advertising API, durable original artwork, same operation replay, **mock** activation, placement eligibility and expiry. Historical original media 404 and mock-payment failure block completion. |
| C08: roommates → group decisions | Tenant tools → lifestyle/roommates[^repo-31] → housing groups[^repo-32] → invite/shortlist/vote/costs/group visit/application | Private profile consent, member/roster versions, individual approvals, capacity and expiry, real qualifying visits. Planning routes historically 404; group membership does not establish a tenancy. |
| C09: housing request → owner offer | Tenant housing requests[^repo-33] → owner housing demand[^repo-34] → exact offer response → compare/shortlist/decline → explicit property/visit flow | Eligible owner feed, request and offer revisions, price/period snapshots, participant privacy, expiry. Planning routes historically missing. Comparison now permits at most three distinct response records. |
| S01: accommodation identity | Shared `RentalSelection`, inventory read/mutation helpers; offer-aware discovery/favorites/visits/leases | Preserve property + offer + offer revision + whole/room/group/bed identity. Lock overlapping inventory atoms. Never substitute the first available offer. |
| S02: decision support | Saved search/alerts, commute[^repo-35], tenant assistant[^repo-36] | Alert delivery workers, catalog validation, real routing coverage, grounded assistant replies with explicit user review. Local saved filters are not proof of an alert worker or AI/routing service. |
| S03: recovery and consistency | premium API helpers[^repo-37], recovery[^repo-38], `AccountSession`, receipt and operation lookup, payment attempt recovery | Scoped idempotency, durable operation status, authoritative absence, replay, account isolation, stale revision rejection, counterpart readback. Legacy endpoints do not all support the structured recovery protocol. |

<a id="b-3-prioritized-work-register"></a>

### 3. Prioritized work register

Each row must return an owner, backend ticket/PR, deployed commit, test names and sanitized evidence. “Implemented locally” is not a deployment result.

| ID | Priority | Evidence / problem | Required backend work and exit condition |
| --- | --- | --- | --- |
| BE001 | Regression gate; public-read issue resolved in tested scope | Historical guest 401; current guest Home/list/catalog checks return 200 | Retain public permission regressions. Private fields, property creation and the complete visit journey need separate evidence. |
| BE002 | P0 for banner completion | Historical media 404; now 200 but original artwork digest does not match | Restore the original uploaded bytes for the **existing** ad and operation. Replay the same activation only after its original digest matches; prove tenant placement, replica/redeploy persistence and expiry. Do not substitute artwork or a new advertisement. |
| BE003 | P1 | English visit request returned Arabic labels despite English headers | Translate server-owned tabs/status/display strings under the selected locale; test `ar` and `en`, `Content-Language`, cache variation and stored free text preservation. |
| GAP001 | P1 consistency follow-up | Centers now close historical never-occupied drafts, but initial details showed open/revision 2 before center closed/revision 3 | Investigate reconciliation timing; list/detail/center must agree after the transition. Funded cancellations retain obligations. Later shared-pair readbacks pass; first-read consistency still needs backend evidence. |
| DEP001 | P0 before planning rollout | `planning-capabilities` and planning collections historically 404 | Implement/version/migrate planning families C08/C09/S02 and condition/transition services; advertise only deployed, verified capability/action pairs. Missing services remain disabled. |
| DEP002 | P0 before structured rental rollout | Empty rental capabilities/actions; no active fixture/provider proof | Complete C04–C06 and owner finance, seed authorized fixtures, verify signature/PSP/worker integrations, then return granular capabilities. Do not enable all flags merely to render screens. |
| OBS001 | P1 investigation | Chat ACK + REST persistence observed; counterpart WebSocket broadcast inconsistent | Trace two authenticated connections, channel subscription, commit/outbox, reconnect and event IDs. This is an observation, not a proven channel-layer root cause. Prove counterpart delivery and REST recovery independently. |
| DEC001 | Release dependency | Unresolved policy choices | Return approved studio/zero-bedroom rules, commission refund/tax treatment, deletion/retention, activation ordering and pending financial closure semantics. Version the chosen policy and add boundary tests. |

Latest historical observations **already resolved**: `lease-configuration.can_create=true`; new invitation-created draft `legacy_read_only=false`; owner cancellation permitted, tenant cancellation denied; `can_sign=false`; repeated same cancellation returned revision 2 with HTTP 200; eligible picker changed pending → accepted → consumed/absent; draft/cancel created no invoices. Keep these as regressions rather than reporting them again as currently failing.

<a id="b-4-flutter-enhancements-delivered-with-this-guide"></a>

### 4. Flutter enhancements delivered with this guide

1. Structured agreement creation now confirms the returned owner, tenant, invitation, property, exact accommodation snapshot, draft state, editable classification and reviewed terms. A mismatched success payload remains an **unknown** outcome so recovery can retain the same intention.
2. Legacy draft creation now checks returned dates and rejects contradictory owner/tenant IDs when present. Older projections may still omit participant IDs. Existing property/offer/rent checks remain in place. This does not upgrade legacy transport to the structured operation-lookup protocol.
3. Planning pages now support per-record scope validation and reject late responses after a session change. Housing-offer pages must match the requested request ID; condition-report and transition pages must match the requested lease; transition pages must match the known collection kind. Invalid pages fail as a whole rather than quietly hiding a wrong record.
4. Housing comparison counts response records, not unique properties. Two to three offers can be compared even when several belong to the same property; a fourth requires deselecting one. Re-selecting the same record cannot create duplicates. Arabic/English help text reflects this rule.

These checks defend against accidental API mismatch. Django must still enforce authorization and invariants; a malicious client can bypass every UI check. Unknown transition kinds already lose actions in parsing; they are not evidence of a supported new business state.

<a id="b-5-django-implementation-structure-and-shared-invariants"></a>

### 5. Django implementation structure and shared invariants

<a id="b-51-before-coding"></a>

#### 5.1 Before coding

Inventory the installed Python/Django/DRF/database versions, auth classes, timezone settings, storage backend, task runner/scheduler, WebSocket service, signing/PSP/routing providers and release mechanism. Return exact versions and configuration **names**, never secret values. The framework references below use Django 6.0 for explanation; adapt to the supported version actually installed. This guide does not require a framework upgrade.

Keep transport serializers separate from business commands and actor-scoped read projections. Use explicit input fields and validation; do not expose writable model fields such as `owner_id`, `paid`, `accepted_by`, `occupancy_status`, `commission` or capability grants via a broad `ModelSerializer(fields='__all__')`. Resolve the actor from authenticated `request.user`. A `workspace=owner` query is a view selection, not proof of ownership.

Use the same policy/permission function to calculate `allowed_actions` and to recheck a command immediately before mutation. Querysets must scope both list and detail resources; object permissions alone are not a list filter. Child routes must join through the authorized parent. Validate cross-resource links: invoice→lease, evidence→lease, offer→property, invitation→both parties, candidate→consented source. Return no private resource before checking authorization.

<a id="b-52-transactions-revisions-and-operation-identity"></a>

#### 5.2 Transactions, revisions and operation identity

Apply the following command protocol to new structured mutations; preserve the legacy adapters described in the API guide:

1. Authenticate, validate request schema and classify action/subject. Authorize access to the command subject and any replayed resource before returning saved data. Canonicalize semantic body fields for a payload hash. Do not include transient authentication or locale in this hash.
2. Find or reserve a durable idempotency operation scoped to the actor and action namespace. Same key + same semantics replays the original outcome; same key + changed body conflicts. Check existing operation identity **before** rejecting a replay merely because its submitted revision is old.
3. In a short database transaction, lock the relevant aggregate and source rows in a consistent order; validate roles, revisions, expiry, current offer/capacity and permitted transition. A create usually has `expected_revision=0`; source revision fields still need independent checks.
4. Write the resource, new revision, immutable history, receipt, and durable outbox entry atomically. Use unique/check constraints as a second defense against concurrent workers/requests. Ensure two concurrent first uses of the same key converge on one operation.
5. Commit; return the saved canonical projection and receipt. Enqueue/deliver outbox work after commit, and let a periodic dispatcher retry committed-but-undelivered records.
6. Perform external provider calls outside long database locks, using the persisted operation identity as the provider idempotency key. Persist provider request/result transitions and reconcile uncertainty instead of creating a new operation.

`transaction.atomic()` groups database changes; `transaction.on_commit()` defers callbacks until commit, but a callback is not a durable queue. The outbox requirement above is Sokoun's proposed reliability design. Catch database exceptions at an appropriate transaction/savepoint boundary rather than querying inside a broken transaction. [Django transactions](https://docs.djangoproject.com/en/6.0/topics/db/transactions/)

Use `select_for_update()` where row locking is supported, and explicit constraints for uniqueness/overlap. Locking behavior is database-dependent; SQLite does not establish production row-lock correctness. Exercise races with `TransactionTestCase`/`APITransactionTestCase` and separate connections against the deployment database engine. Ordinary `TestCase` wraps tests in transactions and can conceal incorrect lock usage. [Django row locking](https://docs.djangoproject.com/en/6.0/ref/models/querysets/#select-for-update)

Recommended constraints (map to actual schema):

| Aggregate | Constraint / concurrency protection |
| --- | --- |
| Operations | Unique actor + action namespace + key; immutable canonical payload hash; unique receipt; durable final-absence tombstone if advertised |
| Invitations | No duplicate live invitation for the same authorized parties/exact selection under the approved policy; one consuming lease; expiry tested under lock |
| Allocation | No overlapping active hold/occupancy for the same underlying room/bed atoms and time interval; whole property overlaps all included atoms |
| Signatures | Unique provider event; document ID/hash/revision immutable once signing starts; signature belongs to authorized party |
| Billing | Unique tenancy root + billing period + invoice type; immutable original due date; journal source IDs unique |
| Payments/refunds/payouts | Unique provider event and idempotency key; one applicable capture posting; refund ≤ remaining refundable balance; no duplicate payable/payout posting |
| Groups | Unique active membership; unique actor vote/approval at item + item revision + roster revision; no admin-less active group |
| Reports | Stable item identity; one actor acknowledgment per report revision; final report immutable; lease/evidence/baseline scope enforced |

`absent_final` and `absence_confirmed=true` are strong promises: a delayed original operation can never later commit. Implement a tombstone/operation reservation protocol to enforce that, or return unresolved. A 404, timeout, temporarily empty read replica or empty list alone is not final absence. The current generic Flutter lookup rejects `absent_final`; enabling such a result requires a coordinated contract/client update even after a server tombstone is implemented.

<a id="b-53-separate-state-machines"></a>

#### 5.3 Separate state machines

Do not use a single `status` field to imply all of these facts:

| Domain | Independent facts |
| --- | --- |
| Visit | requested/accepted/rejected/cancelled/completed; granted contact/chat; slot occupancy |
| Invitation | pending/accepted/rejected/expired/revoked/consumed; eligible source; lease link |
| Agreement | draft/review/signature/legal lifecycle; exact revision/document; legacy classification |
| Inventory | available/future availability/held/allocated; hold expiry; atom overlap |
| Occupancy | never handed over / possession transferred / returned; accepted handover evidence |
| Finance | invoice due/partial/paid/credited; payment authorization/capture; PSP settlement; owner payout |
| Closure | accepted settlement; deposit allocation/return; refund execution; dispute resolution; final financial closure |

The above are conceptual states. Emit only wire tokens recognized by the linked Dart enums and return any proposed additions before changing them. Every read projection should derive from the same facts, including the counterparty's view. Avoid treating expiry/revision-dependent permissions as long-lived cached values.

<a id="b-6-implementation-and-acceptance-by-cycle"></a>

### 6. Implementation and acceptance by cycle

<a id="b-c01--c02--listing-discovery-and-visits"></a>

#### C01 / C02 — listing, discovery and visits

1. Validate owner listing fields, category and inventory mode; assign stable server IDs while echoing local `client_key` values. Preserve inventory/offer revisions. Persist uploads durably before declaring publication usable.
2. Apply moderation and publication to all discovery feeds and detail eligibility. Apply scope/price-period/availability filters **before** grouping and pagination. Never take the minimum of mixed monthly/yearly prices.
3. Return server-authored available dates/times with a documented timezone. Book against the actual slot and exact offer revision. Atomically enforce capacity, self-booking/ownership rules and duplicate policy.
4. Persist `offer_snapshot` at booking. Rejection, cancellation and resubmission use explicit allowed transitions and reason policy. Preserve the original record/history; do not manufacture completion from the passage of a date.
5. On acceptance, update both actor projections and granted contact/chat consistently. Preserve historical contact disclosure according to the existing accepted-visit policy even if the visit is later cancelled; do not accidentally expose contact for a never-accepted request.
6. Calendar export/reminders must reflect the current appointment, timezone and cancellation. Review eligibility must derive from the real visit policy, with one eligible author and no self-review.

**Proof:** guest discovery and authenticated detail; two tenant requests racing for the last slot; stale offer revision; owner A attempting owner B's action; rejection note persistence; allowed resubmission; cancel after acceptance; both inboxes/counters; Arabic/English labels; deduplicated notifications; review eligibility; no lease/invoice/inventory rental allocation caused by a visit action.

<a id="b-c03--consent-invitation-and-legacy-lease-draft"></a>

#### C03 — consent invitation and legacy lease draft

The agreed existing source is a pending/confirmed visit for the same owner/tenant/property; an exact offer must match when present. Do not expand to completed visits without accepting that policy and updating tests. Both actors must meet server verification requirements. Invitation lifetime is seven days including accepted but unconsumed invitations.

Owner creates → tenant reads/responds → accepted invitation becomes eligible in `lease-tenants` → owner submits a legacy draft → invitation is consumed in the same transaction. A pending/rejected/expired/revoked/consumed invitation must not appear as eligible. Prevent two simultaneous drafts consuming one consent. Cancellation never restores eligibility or reuses consent. The legacy body has no `invitation_id`, so resolve the unique eligible source under lock; reject ambiguity instead of guessing.

Create only a draft: no invoice, no occupancy, no automatic signing/payment/activation. Respect the distinction between old immutable legacy history and a newly created editable/cancellable legacy-shaped draft. Return truthful `can_cancel`, `can_sign`, `legacy_read_only` and actions for each actor.

**Proof:** pre/post picker reads; wrong owner/tenant/offer; pending acceptance; expiry before and after acceptance; duplicate create same key; changed-body same key; two distinct keys racing for the same invitation; owner cancel same key twice; tenant cancel denied; consumed invitation remains unavailable; exact dates/rent retained; no financial or possession side effects. Include historical cancelled drafts in migration/readback tests.

<a id="b-c04--structured-agreement-signing-first-payment-and-move-in"></a>

#### C04 — structured agreement, signing, first payment and move-in

1. Authorize the tenant's exact current offer interest, desired dates, occupants and duration. Owner proposals pin interest revision, offer revision and full approved terms. Editing terms invalidates prior acceptance/review.
2. Create an interest-sourced invitation only from an eligible source and accepted required proposal. Do not let a property ID alone authorize an unrelated tenant. Preserve both parties and exact offer snapshot through the agreement response.
3. Server validates the commercial/template policy, civil dates, occupancy capacity and handover/billing dates. Generate the versioned document and digest from the exact reviewed terms. Review/signing actions pin revision; hosted signing pins document ID/hash and expiry. A WebView return is not a signature event.
4. Verify signature provider callbacks, replay handling, signer identity and document digest. Keep provider pending/failure visible and reconcile. Define a bounded inventory hold and release policy; never sell the same room/bed through an overlapping whole-property offer.
5. **Apply the policy approved on 2026-10-12:** completed signing starts a 48-hour inventory hold, and successful capture of the combined initial rent/deposit invoice triggers activation. Expired unpaid holds release inventory. Enforce owner readiness and current inventory under one auditable server transition; test retries, concurrent allocation and capture arriving after hold expiry. Possession still requires the appropriate handover.
6. Issue the combined initial invoice at signing/hold creation, before activation. Keep rent and deposit allocations separate in the ledger. Quote the stored invoice, persist one payment attempt before contacting the PSP, bind checkout to quote/revision/amount, and reconcile by the same key after timeout. Validate signed provider events and ledger posting exactly once. Display capture, receipt, PSP settlement and owner payout independently.
7. Move-in handover requires the correct parties' acknowledgment of the current report/version. Transfer possession only at the defined acceptance boundary. A condition report submission or a visit acceptance cannot transfer possession.

**Proof:** stale proposal/review/signature; mismatched snapshot; expired signing session; repeated/out-of-order webhooks; hold expiry during signing/payment; two competing offers for overlapping atoms; tenant A paying tenant B's invoice denied; owner checkout denied; two checkout retries one attempt/charge; lost response then lookup; captured payment without receipt still captured with receipt pending; no payout until payout eligibility; both Rental Centers agree.

<a id="b-c05--recurring-stay-operations"></a>

#### C05 — recurring stay operations

Billing schedule uses civil dates, `ends_on_exclusive`, approved timezone and original billing anchor. Test January 31 → February → March without permanently shifting the anchor, leap years, DST, final partial periods and amount rounding. A repeated scheduler run issues the same invoice once. Deposit is a separate invoice/balance; do not treat it as rent revenue.

Maintenance: validate category/priority/access preferences and evidence ownership; record appointment and responses as history. A proposed tenant cost is not payable until that tenant approves the exact amount/version. A resolution report is not tenant confirmation. Reopen/cancel must honor current state and role.

Payment extension: preserve `original_due_at`; store `deferred_until` separately after approval. Amendment/renewal: preserve previous terms, invalidate old reviews, require new signatures where the policy requires, and apply effective dates without rewriting historical invoices. Renewal retains the tenancy root and does not repeat the first-period commission. An external payment claim is pending evidence until the authorized process confirms and posts the appropriate accounting adjustment.

**Proof:** repeated job; boundary dates; extension rejected/accepted; unauthorized cost approval; amendment during pending payment; renewal conflicting with future inventory; no double commission; external claim replay/rejection; private documents expire and cannot be downloaded by strangers; both parties read the same timeline and invoices.

<a id="b-c06--end-condition-settlement-refunds-and-replacement"></a>

#### C06 — end, condition, settlement, refunds and replacement

Keep legal termination, notice receipt, effective end, occupancy return, settlement acceptance and actual fund movement distinct. A notice `acknowledge` records receipt; it does not terminate a lease. A finalized condition report records agreed observations; it does not establish liability, accept a handover, charge damages or deduct a deposit.

Condition reports need stable item IDs, permitted spaces, `notInspected`/`unknown` distinctions, evidence bindings, exact revision acknowledgments, objection history and a final immutable baseline. For move-out comparison, use the authorized final move-in baseline of the same leased selection. Re-submission invalidates acknowledgments of the old version. Reject cross-lease media and invented baseline IDs.

Settlement totals come from the ledger and authorized item proposals. Owner/tenant acceptance or dispute references exact version/item IDs; operations resolves disputed responsibility under policy. Refund requests never directly execute PSP refunds. Enforce remaining refundable balance under lock, process callbacks idempotently and keep failure/retry history. Payout retry must reuse provider identity, not duplicate a transfer.

Replacement has three separate tracks: outgoing release, incoming agreement, and future availability. Candidate nomination is not candidate consent; group membership is not a signature; approving future availability does not release current possession. Coordinate the required contracts, consent, inventory and dates through a resumable journal/outbox. Keep the old occupant's obligations unchanged until the approved release becomes effective; retain pending recovery if any step is uncertain.

**Proof:** notice read/acknowledge/withdraw; report object/revise/finalize; stale baseline; one party's approval cannot stand for everyone; settlement dispute one item; partial/refused refund; refund/provider timeout; retained payout hold; replacement declined/withdrawn/stale candidate; double replacement race; no incoming occupancy before eligibility; never-occupied cancellation shows no move-out obligation.

<a id="b-c07--banner-advertising"></a>

#### C07 — banner advertising

Preserve the existing advertising API and `payment_mode=mock` semantics. This is not rental PSP payment and must not be described as a real captured charge. Server plan price/duration/revision are authoritative; a property link is optional and must be owned/eligible when supplied.

Create/upload stores the original artwork and operation journal durably. Verify content/size, authorization and media availability before accepting activation. Repeated same create/activation intention must return the same advertisement. Publication and tenant placement depend on actual status, moderation, start/end and property eligibility; expiry removes placement without deleting evidence required for recovery.

**Proof:** original blocked ad recovery, same operation after app/server restart, pending private artwork access, active public artwork access, wrong owner denied, bad/corrupt upload, plan revision conflict, tenant feed independent readback, expired/unpublished target removed, no accidental rental invoice/provider charge.

<a id="b-c08--lifestyle-roommates-and-housing-groups"></a>

#### C08 — lifestyle, roommates and housing groups

Lifestyle profile data requires explicit disclosure consent and purpose/retention policy. Match explanations must not expose private answers. Canonical user-pair connections prevent duplicates; blocking applies in both discovery and connection/chat authorization. Return the real `user_id` for a granted chat, not a connection resource ID.

Group creation atomically creates the admin membership. Membership/capacity, transfer/removal/leave, private token invites and revocation must survive simultaneous joins. Hash invite tokens at rest and omit raw tokens from logs/analytics/push. Preview is read-only and must not consume a token. Departed members lose future private reads according to the approved archive policy.

Shortlists pin exact offer versions. Votes and contributions bind to item, proposal, offer and roster versions. Contributions must cover exactly the active participants with nonnegative integer amounts summing to total; a planning proposal does not create payables. Changes invalidate approvals. Group visits/applications collect each participant's own consent and source eligibility; a coordinator cannot approve for everyone.

**Proof:** private profile access, withdrawal/block, duplicate connection, last slot invite race, revoked/expired token, preview no join, last-admin leave, roster change invalidates votes/cost approval, unauthorized history read, contribution total error, per-member visit/application consent and withdrawal, no automatic lease creation.

<a id="b-c09--demand-requests-and-owner-offers"></a>

#### C09 — demand requests and owner offers

Tenant request states and owner visibility must be explicit. Feed applies eligibility/block/expiry and prevents self-dealing. Criteria write and read schemas differ (see API guide); free-text neighborhood is not a district ID. Owner responses use owned published exact inventory, current request revision and server-authoritative rent/deposit/price period. Do not derive bed rent from whole-property rent.

Shortlist/decline/withdraw affects planning only. Communication requires a separate grant, and booking starts through the existing property/visit flow. Preserve response snapshots while requiring fresh eligibility at the next action. Editing/pausing/closing/expiring a request must prevent stale new offers. Offer list count and pagination must remain request-scoped.

**Proof:** two owners' offers and tenant view; owner cannot see another owner's private responses unless policy allows; stale request/offer; closed request; offer from unowned property; four offers on one property compare at most three; same response never duplicated; shortlist creates no lease/hold/invoice; selected offer survives navigation into property details.

<a id="b-s01--s02--s03--cross-cycle-requirements"></a>

#### S01 / S02 / S03 — cross-cycle requirements

S01: model allocation against underlying inventory atoms so whole/room/group/bed paths cannot double-book. Keep immutable historical snapshots even after archive/edit. Never replace the selected offer on deep-link resolution, favorites, visit, invitation, lease, handover or invoice.

S02: a saved search is local until an alert is created; prove real worker evaluation, deduplication and notification delivery before claiming alerts are operational. Commute must use an actual routing provider, all destinations and hard time limits before pagination, with explicit unknown/coverage states. The assistant must use authorized grounded property IDs/catalog filters and expose unresolved requirements; it proposes drafts/actions that the user reviews in the normal feature, never executes hidden rental commands.

S03: preserve input and operation identity after timeout, malformed success, app kill and account switch. Fresh success may replace cached content; fresh empty is authoritative. A read failure should retain valid scoped data and Retry, but stale cached permissions cannot authorize a mutation. Backend replies, jobs and callbacks must be replay-safe independently of the client.

<a id="b-7-test-plan-for-the-django-engineer"></a>

### 7. Test plan for the Django engineer

<a id="b-71-required-fixtures"></a>

#### 7.1 Required fixtures

Use isolated authorized test accounts: verified owner A, owner B, verified tenants A/B/C, unverified account, guest and a staff/operations actor with explicit permissions. Do not share a logged-in client across actors. Include whole-property, independent room, room group and bed offers with overlapping inventory; published, draft, rejected, archived, expired and unavailable variants.

Create visit variants; pending/accepted/expired/consumed invitations; editable legacy draft, historical read-only lease, structured draft/review/signature/active/ended/settlement-pending leases; unpaid/partial/paid/credited invoices; pending/captured/failed/unknown attempts; groups with changed rosters; request/offer/report/transition fixtures. Use deterministic clocks, approved templates/policy and synthetic media. Keep credentials outside reports.

<a id="b-72-test-layers-and-what-each-proves"></a>

#### 7.2 Test layers and what each proves

| Layer | Required assertions | Evidence |
| --- | --- | --- |
| Serializer/unit | Exact bodies/types/omissions, nested Money, civil dates, enum rejection, nested identity, approved policy, bilingual messages | Test names and fixture/schema version |
| Database/service | Atomic transitions, constraints, revision changes, consent consumption, ledger invariants, immutable audit | Database engine/version and postcondition queries |
| API permissions | Every actor for collection/detail/action/attachment/operation lookup; real authentication path, validation and conflict codes | Status + sanitized response + unchanged DB for forbidden writes |
| Concurrency | Same key race; distinct keys same source; last slot/member; overlapping allocation; duplicate webhook/refund/billing | Separate connections, controlled barrier, exactly one effect |
| Provider sandbox | Signing, payment capture, reconciliation, refund and payout events; invalid signatures, retries, out-of-order events | Provider environment, event IDs redacted, event→resource correlation |
| Worker/storage | Outbox survives restart, scheduler catch-up, expiry, artifact generation, durable media after deploy | Job execution and queue/object evidence |
| Staging HTTP | Real reverse proxy/auth/routing/database/storage/worker integration across actors | Requests/responses, release SHA, timestamps and actor readback |
| Flutter local / later integration | Parser/body compatibility and recovery first; then real in-app journeys after backend return | Local command results now; device/live evidence in next phase |

DRF's `APIClient` and `APITransactionTestCase` support API tests against the test application. Its `RequestsClient` uses an in-process adapter, so naming a test “live” does not prove a deployed request. Use an actual network client such as `requests.Session` against the returned staging base URL for release evidence. Test authentication without `force_authenticate` in at least the auth/permission layer. [DRF testing](https://www.django-rest-framework.org/api-guide/testing/)

<a id="b-73-mandatory-test-pattern-for-every-mutation"></a>

#### 7.3 Mandatory test pattern for every mutation

Run: success; forbidden actor; unverified/expired session; missing/invalid fields; stale target revision; stale source revision; expired source; duplicate same key/same body; same key/changed body; response lost after commit; replay after subsequent unrelated updates; simultaneous requests; linked resource from another lease/account; counterpart reads; outbox/ledger exactly once. For a failed command, assert **no partial** allocation, invoice, approval, membership or journal effect.

Add explicit parser mismatch fixtures: wrong owner/tenant/invitation/property, changed room/bed/offer revision/price, wrong dates, missing required receipt, wrong key/subject/revision and unexpected status. A 200 with wrong facts must fail contract validation.

For each C01–C09 and S01–S03, record a test set ID, preconditions, actor, request, expected response, database postconditions, counterpart projection, job/provider evidence and cleanup policy. Preserve failed cases until a rerun identifies the fixing commit.

<a id="b-8-configure-migrate-and-deploy-safely"></a>

### 8. Configure, migrate and deploy safely

<a id="b-81-preflight-commands"></a>

#### 8.1 Preflight commands

Run these from the **actual backend checkout**, with that project's isolated test configuration. They are standard Django commands, not commands for this Flutter repository. Replace settings/module/test labels with the returned real names. Pin and report the versions already supported by the backend.

```bash
python --version
python -m django --version
python -m pip check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations
python manage.py migrate --plan
python manage.py test <actual_cycle_test_package> --keepdb
python manage.py check --deploy --settings=<actual_production_settings_module>
```

If pytest is already installed/configured, use the project's existing pytest command instead of inventing a second test runner. Export machine-readable results through the project's configured reporter. Run race tests on the production database engine with separate connections. Never point destructive test setup at production data.

`check --deploy` checks deployment-sensitive settings; run it with the settings used by the deployed service. It does not test Sokoun cycles or prove providers/workers are healthy. Review HTTPS/proxy trust, hosts, `DEBUG`, secret handling, cookies, static/media separation, backups and logging in the context of the actual deployment. [Django deployment checklist](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/)

<a id="b-82-configuration-checklist"></a>

#### 8.2 Configuration checklist

| Area | Verify and return |
| --- | --- |
| Authentication | Installed auth/permission classes, access/refresh transport, expiry/rotation/revocation, cookie/CSRF behavior for the actual scheme. Do not assume Django means session auth or disable CSRF globally. |
| Locale/time | Default locale, `ar`/`en`, translation fallback, `Content-Language`, timezone/civil-date rules, DST behavior, aware instants |
| Database | Engine/version, transactions/isolation, constraints/indexes, connection limits, migration compatibility and tested restore |
| Jobs | Worker and scheduler commands, queues, retry/backoff/dead-letter policy, outbox dispatch, expiry, billing, provider reconciliation, alerts, document generation |
| Storage | Durable private evidence/documents, banner artwork lifetime, MIME/size/digest checks, signed URL TTL, object authorization, restart/deploy persistence |
| Providers | Sandbox/live identity, webhook endpoint ownership, signature verification, event dedup, timeouts, idempotency, reconciliation, secret manager configuration names |
| Feature gates | Build availability separately from server `enabled_capabilities`, `verified_services` and per-resource actions; verification bypass off for acceptance/release |
| Observability | Correlation/operation/resource IDs, actor-safe logs, status/revision, latency, queue lag, unresolved attempt age, overdue job, failed media and mismatch alerts; no tokens, raw private messages or payment credentials |

<a id="b-83-migration-and-rollout-sequence"></a>

#### 8.3 Migration and rollout sequence

1. Back up and verify restore on an isolated database. Inventory old rows and contradictions before backfilling. Preserve old financial/legal history.
2. Add backward-compatible fields/tables/indexes first; deploy code that tolerates old rows. Classify legacy records explicitly; do not infer signatures, possession or paid status from old generic flags.
3. Backfill in bounded resumable batches with audit counts. Detect duplicate invitations/allocations/payments and resolve them under approved policy before enabling stricter constraints. Never silently drop conflicting obligations.
4. Review `migrate --plan`, apply approved migrations through the deployment job, then run `migrate --check`. Verify all web/worker versions are schema-compatible. Perform static collection only as required by the project's deployment setup.
5. Deploy API/worker/scheduler/WebSocket components with capabilities still disabled for unverified families. Verify durable storage and job credentials from the deployed runtime.
6. Run real HTTP smoke and the backend cycle suite on isolated staging fixtures. Capture both actors and actual provider sandbox events. Confirm no duplicated effects on restart/retry.
7. Return the API contract, evidence and unresolved issues. Enable only independently passed capability families for a limited rollout; keep reconciliation/read access for existing pending operations available.
8. Monitor invariant violations and queue/provider/media failures. Define an operator and rollback trigger before rollout. Prefer disabling new writes and rolling forward schema-compatible code; do not reverse a migration that would erase operations, signatures or financial history. Reconcile existing pending work after rollback.

<a id="b-84-deployment-acceptance-criteria"></a>

#### 8.4 Deployment acceptance criteria

A successful deployment needs all of: correct release SHA exposed or otherwise correlated to requests; migrations applied; web and workers on compatible versions; real authenticated/guest endpoints resolve correctly; fresh scoped capabilities; counterpart reads agree; original media survives restart; outbox/jobs run; provider callbacks correlate; no unresolved P0 issues for enabled families; rollback/recovery procedure verified.

Do not mark C04–C06 complete from synthetic `paid=true`, seeded active rows, mocked webhooks alone or a checkout return page. Do not mark C08/C09 complete from route registration alone. An unsupported family is a documented disabled family, not a passed cycle.

<a id="b-9-local-mobile-verification-and-next-handoff"></a>

### 9. Local mobile verification and next handoff

Use `make ownerTenantCyclesCheck FLUTTER=/path/to/flutter` in `apps/sokoun_app` to run the focused local contract/behavior suite with default-disabled planning gates and with the relevant planning gates enabled **only for fake-transport tests**. See the command definition in the Makefile[^repo-39]. It performs no staging mutations and does not enable production services.

The focused suite covers agreement response identity/terms, legacy compatibility, planning parent scope/session changes, comparison selection, existing invitation/lease contracts, recovery and the documented sample payloads. The verification record is in the companion guide. This is not a claim that every backend cycle is deployed.

The backend reply has been received. Public reads and replacement-account login/refresh/scoped reads have run through the real Flutter transport and HTTP audit. Complete journeys still need eligible fixtures, secondary actors and provider/job evidence. The [verification report](#part-a) records exact outcomes and prerequisites; the [contract return form](#c-12-backend-return-form) still needs concrete payload/deployment evidence where the reply contains descriptions or placeholders.

<a id="b-10-actions-after-the-backend-reply"></a>

### 10. Actions after the backend reply

<a id="b-101-fix-the-integration-prerequisites-first"></a>

#### 10.1 Fix the integration prerequisites first

1. **Seed authentication:** the original four accounts returned 401. Replacement Google owner/password tenant accounts now pass login, verified identity and scoped reads. Supply distinct secondary actors for denial tests and correct the original seed claim. Verify seeds in the database used by the deployed API, using Django password hashing and actual account policy. Test the public URL and `GET auth/users/me/`; transfer credentials privately. Do not reset the shared database. `make seed` alone is not deployed-database evidence.
2. **Refresh route:** production `DioService.refreshSession()` at `auth/refresh/` now passes for both replacements, followed by the same identity and authorized feature reads. The reply's `auth/token/refresh/` still returns 404. Correct the reply or deploy a deliberate tested alias. Preserve the working route; separately test rotation, revocation, concurrent expired requests and account switching.
3. **Public envelopes:** Home/properties/catalogs use `{data: ...}`. Home/properties paginate under `data.results`; filter options use named catalog fields. Preserve these working projections. Do not replace them with the reply's `featured_properties/recent_properties` summary or blanket `data: []` shapes.
4. **Advertising language:** repeat requests to the exact plans/feed URL with `en → ar → en` and `ar → en → ar`, on both cold and warm caches. Current responses can retain the first language. The explicit `?lang=` variant working does not fix normal app requests. Determine whether the application cache or proxy cache misses language in its key; activate the effective locale before translation/serialization and cache lookup/write. Verify payload labels, `Content-Language` and `Vary`, then invalidate only affected cache namespaces. Django documents language variation through [Vary-aware caching](https://docs.djangoproject.com/en/5.1/topics/cache/#controlling-cache-using-vary-headers).
5. **Planning:** the initial read lacked `verified_services`/`expires_at`; the later recorded check includes both with empty services and null expiry. Preserve that safe disabled response. It is a successful disabled-capability contract, not deployment evidence for C08/C09/S02. Enable a family only with matching account, verification, policy, future expiry, verified service and scoped action.
6. **Invitation fixture:** the replacement pair's actual visit is `canceled`, the eligible-tenant picker is empty, and the queried current-week availability is empty. Supply an eligible pending/confirmed visit and valid future dates through the normal rules. Never make a cancelled source eligible just to pass the test. The runner validates owner-scoped visit detail before any invitation POST.
7. **Original media:** the original advertisement's media is now a 1,213-byte PNG with SHA-256 `303a95728f601403f468dd9abe1cd8618d1f9fee2ef68e7cb57a257337b5b370`; the uploaded 28,970-byte logo.png[^repo-4] hashes to `dc2be014d6db85c4e73572c11fe5f21eb10df6d84675a3cc1b3350097e2e212b`. Restore the exact original for the existing operation and explain the difference. Media tests must include `application/json` alongside accepted image types, matching the client; an image-only 406 is not a storage result. Activation remains stopped until original-byte verification passes.
8. **Closure consistency:** historical details first reported open/revision 2, followed by closed/revision 3 from Rental Center, without a client command. Later reads agree. Trace logs/SQL/job execution to identify the cause. Apply the correct unfunded closure in the authoritative cancellation/reconciliation transaction or explicit repair migration/job, and use one consistent read projection. Test collection → detail → center → detail for both actors immediately after cancellation; GETs must not be a required step to finalize business state. Do not apply this repair to records with captured funds or unresolved liabilities.

<a id="b-102-implement-and-verify-the-selected-billing-transition"></a>

#### 10.2 Implement and verify the selected billing transition

- Final signature processing and initial-invoice creation must be idempotent. Pin the signed document hash/revision and approved terms; create exactly one initial invoice per agreement/policy boundary and exactly one deposit obligation linked to it.
- In the transaction, lock the agreement, relevant overlapping inventory and financial aggregate in a consistent order. Make the operation receipt, invoice, rent/deposit allocations and transition agree before committing. Test races using independent PostgreSQL connections and `TransactionTestCase`; SQLite and ordinary transaction-wrapped test cases do not establish row-lock behavior. See [Django row-lock testing guidance](https://docs.djangoproject.com/en/5.1/ref/models/querysets/#select-for-update).
- Issue the invoice while lease status is `signed`; return `hold_expires_at`, server-calculated invoice amount, lines, balance, revision and tenant actions. Owner cannot checkout. A read/list request cannot create an invoice or activate the lease.
- Verify the provider event and one capture posting. Activate only when the required balance is satisfied and the hold/inventory is still valid. Do not activate on authorization, browser return, pending/failed payment, or payment of rent alone when a deposit is due.
- Serialize hold expiry against capture. A late capture after inventory release must enter documented reconciliation/refund handling; it must not double-allocate accommodation. Return the chosen late-event policy and test it with controlled clocks.
- Keep deposit liability separate from rent, platform revenue and owner payable. Compute the approved 10% commission on first-period base rent only. Never issue a second initial deposit charge. Preserve prior agreements/invoices and version any actual policy migration; the current mobile quote validator supports `rental-policy-v1` only.
- Record state changes before notifications. `transaction.on_commit()` prevents pre-commit publication, but does not make a callback durable after process failure. Verify outbox/job recovery where delivery is promised and exercise the gap between commit and dispatch. See [Django on-commit behavior](https://docs.djangoproject.com/en/5.1/topics/db/transactions/#performing-actions-after-commit).
- Clean never-occupied, unfunded drafts close without a move-out obligation. A funded cancellation retains refunds/deposit/chargeback obligations until resolved. Return owner and tenant Rental Center snapshots after both paths.

<a id="b-103-supply-actual-release-and-test-evidence"></a>

#### 10.3 Supply actual release and test evidence

The reply's `5c1aaa5 + working tree updates` is not an immutable deployment identity. Return the exact deployed Git SHA/container digest for API, worker and scheduler, exact Python/Django/DRF versions, deployment timestamp, migration evidence and the actual OpenAPI artifact/hash. `schema_version=1` alone is not an API schema. The stated Django 5.0/5.1 versions also need verification against the project's supported release target; the [5.1 documentation identifies that version as unsupported](https://docs.djangoproject.com/en/5.1/ref/django-admin/).

From the backend runtime/checkout, using its real settings, capture:

```bash
git rev-parse HEAD
git status --porcelain
python --version
python -m django --version
python -m pip check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py showmigrations --plan
python manage.py migrate --plan
python manage.py migrate --check
python manage.py check --deploy
```

Run deployment checks in the deployed configuration, and run business tests separately in the isolated PostgreSQL CI configuration. The return must name the exact test labels/settings used for `test_properties_views`, `test_visits`, `test_tenancy_invitations`, rental phase 1–6 tests and `test_advertising_api`; filenames without commands/results are insufficient. Use the existing configured Django/pytest runner; no unverified test package path is prescribed here.

`makemigrations --check --dry-run` detects model changes missing migrations. **`migrate --check` detects unapplied migrations.** These prove different facts; neither proves application workflows. See [Django management command reference](https://docs.djangoproject.com/en/5.1/ref/django-admin/#migrate).

For every claimed cycle provide a result artifact with deployment ID, database engine, test identifiers, exit status, timestamps, actor/resource correlations and sanitized request/response readbacks. Mark mock, provider sandbox, deployment smoke and device evidence separately.

<a id="b-104-required-operational-proofs"></a>

#### 10.4 Required operational proofs

| Component | Required proof and failure exercise |
| --- | --- |
| Original banner artwork | Repair the original ad/operation. Record digest and MIME, read through authenticated owner and eligible public media routes, restart and redeploy/replace a replica, then verify identical bytes. Process restart alone does not prove container-disk persistence. Use deployed persistent storage/object storage; prove shared visibility across replicas. |
| Banner mock activation | Same ad/operation/plan/media, `payment_mode=mock`, one receipt and unchanged dates on replay. Independent tenant/guest sees eligible placement. This is not rental PSP capture. |
| Worker/scheduler | Return exact worker/scheduler deployment and task names, queue/heartbeat evidence, scheduled due time, execution time and effect IDs. Repeat a billing/expiry job and verify no duplicate invoice/notification/allocation. Test retry after worker termination. |
| Signing/payment provider | Private environment configuration, valid/invalid signatures, duplicate/out-of-order callbacks, timeout then same-key lookup, capture/receipt/settlement/payout separation. Secrets stay outside artifacts. |
| Chat/notifications | Sender ACK, persisted message read by both actors, independent receiver broadcast, reconnect/dedup, post-commit delivery and recovery after dispatch failure. |
| Capability rollout | Keep families disabled until the corresponding proofs pass. Rollback disables new writes while retaining authorized status/recovery reads for existing operations. |

<a id="b-105-focused-acceptance-cases-for-the-return"></a>

#### 10.5 Focused acceptance cases for the return

| ID | Scenario | Required observable result |
| --- | --- | --- |
| AUTH-01 | Each supplied seed signs in and reads itself | Four distinct verified identities; then refresh succeeds at the documented route |
| LOC-01 | Same plans/feed URL, alternating `ar`/`en`, cache hit/miss | Correct labels and `Content-Language` on every response; `Vary` present |
| BILL-01 | Sign twice/replay provider callback | One 48-hour hold and one combined invoice; lease remains signed/unoccupied until required capture |
| BILL-02 | Quote first invoice and perform full sandbox capture | Quote matches combined balance; one capture; rent/deposit allocations correct; active lease read by both actors |
| BILL-03 | Wrong tenant/owner, stale invoice/quote, tampered amount | Denied/conflicted without charge or state change |
| BILL-04 | Capture timeout, repeated checkout, repeated/out-of-order callback | Original attempt reconciled, no second charge, receipt may remain pending |
| BILL-05 | Hold expires as capture arrives; another offer targets same bed | No double allocation; explicit late-event financial outcome and matching ledger |
| LEGACY-01 | Accepted consent → legacy draft → cancel twice | Same cancellation receipt/revision; consent stays consumed; no invoice/possession; both centers close cleanly |
| LEGACY-02 | Cancelled/completed source or wrong participant attempts invitation | Ineligible; no new invitation or draft; existing consent/history unchanged |
| CLOSE-02 | First collection/detail/center reads immediately after unfunded cancellation | All agree on closure and revision; reading does not repair the business state; inspect concurrent-job effects explicitly |
| CLOSE-01 | Cancel an unoccupied agreement with money captured | Refund/deposit obligations remain visible; no false immediate financial closure |
| MEDIA-01 | Verify original digest, then banner activation, repeat, redeploy, public read | Same identity/receipt/dates and exact original media survive; wrong bytes block activation testing |
| GATE-01 | Empty, incomplete, expired or wrong-account capabilities | Client/server prohibit creation; authorized recovery reads remain possible |

The mobile runner provides public/authentication checks and journaled legacy/banner regression scenarios. Full provider, scheduled-job, inventory-race and device scenarios require the backend fixtures/services above; they remain explicit blocked checks until executed.

---

<a id="part-c"></a>

## Part C — Exact API contracts, payloads and response examples

Included source: `docs/backend/SOKOUN_OWNER_TENANT_API_CONTRACT_AND_RETURN.md`.

Prepared **2026-10-12** against the Flutter working tree after baseline `0e122774433b42e16a6643f33e886bdd29d897c9`. Read alongside [the Django implementation/verification guide](#part-b) and the cycle specification[^repo-12].

This is the **client-compatible target contract**, not a declaration that all routes are deployed. Legacy/advertising contracts have earlier backend handoffs; structured rental has a local-backend return; planning remains a proposed client integration with historical 404 observations. The backend engineer must fill section 12 with the actual deployed contract, examples, deviations and evidence. “Correct” means demonstrated conformance for the tested version and cases; an unverified endpoint cannot be called 100% correct.

**Backend reply reviewed 2026-10-12:** see [claim-by-claim verification and remaining requirements](#part-a). The chosen billing policy is now the combined initial rent/deposit invoice and capture-before-activation policy in section 6. The original section 11 records the earlier local run; current checks and live failures are recorded separately in the verification report.

<a id="c-1-protocol-and-compatibility-boundaries"></a>

### 1. Protocol and compatibility boundaries

All paths are relative to `/api/v1/` unless a section explicitly says otherwise. Preserve trailing slashes, method, content type and query/body placement. URL-encode opaque resource IDs. Use actual server IDs from previous responses; sample aliases such as `lease-example` are explanatory and are not valid production UUIDs. Request-key examples are synthetic stable UUIDs; reuse a key only for the same logical intention.

| Family | Prefix / body convention | Success `data` shape | Compatibility rule |
| --- | --- | --- | --- |
| Property/visit/chat | Existing `properties/`, `homepage/`, `chat/`; some multipart; visit bodies have no generic revision/key | Existing resource/collection schema | Do not add a required `expected_revision`/`request_key` to these clients without a coordinated migration. |
| Legacy features/invitations | `features/v1/`; `request_key`, action-specific `revision` | Direct resource, not canonical wrapper | Invitation response and legacy draft/cancel must remain accepted. |
| Structured rental | `features/v1/`; `request_key`, `expected_revision` plus source revisions | `{resource,operation_receipt}` for most writes | Reads are direct resources; payment-attempt reconciliation is a direct resource exception. |
| Planning | `features/v1/`; typed action body with `request_key`, `expected_revision` | `{resource,operation_receipt}` for writes | Invite preview is a read-only POST returning a direct resource; no mutation receipt. |
| Banner advertising | `advertising/v1/`; `operation_id`, multipart create, mock activation | Advertising resource/receipt fields | Do not substitute rental request keys/quotes or claim real PSP capture. |

Headers: `Accept: application/json`, `Accept-Language: ar` or `en`, `Content-Type: application/json` for JSON. Multipart uploads must use the generated boundary and real bytes. Current transport persists access/refresh cookies and can derive `Authorization: Bearer …` from the access cookie; return the exact installed Django auth/refresh behavior. Do not publish tokens in this return document. Private responses must avoid shared/public caching; locale-dependent public responses need appropriate language variation.

`workspace=owner|tenant` controls presentation/filtering. The server must derive identity and permissions from authentication and database relationships, never from workspace or a supplied participant ID.

<a id="c-current-deployed-protocol-corrections"></a>

#### Current deployed protocol corrections

| Area | Verified wire behavior / required correction |
| --- | --- |
| Login | Password login is `POST auth/login/` with only `email,password`; Google is `POST auth/google/` with only `token`. Both then read `GET auth/users/me/`. The replacement pair passes both production Flutter paths and verified identity checks; the original four seeds returned 401. Auth secrets/cookies are withheld from evidence. |
| Refresh | App retains **`auth/refresh/`** and posts with its saved cookie/header session, without a JSON refresh body. Actual refresh and same-user readback pass for both replacements. The reply's `auth/token/refresh/` is 404. Rotation/revocation/concurrent-expiry behavior still needs separate evidence. |
| Home / property lists | Root `{data:{results,per_page,total_pages,...}}`; no required `key` or `status`. Home also includes `count,banner`. `HomePageModel` expects `results`; do not replace it with `featured_properties/recent_properties`. |
| Types / governorates / cities | Root `data` object contains `results` and pagination; the reply's broad `data:[]` summary is not this envelope. |
| Filter options | Root `data` object contains named catalogs including `property_types,ordering,bedrooms,bathrooms,price_periods,suitable_for,amenities,defaults`; preserve actual nested types from the recorded response. |
| Planning | Latest recorded 200 contains empty `enabled_capabilities`, `verified_services`, `allowed_actions` and null `expires_at`; guest account is unverified. Earlier missing fields are now present. Disabled discovery does not establish implemented planning services. |
| Advertising | `{key,message,data}` with `data.results` for plans/feed. Alternating language headers can return the previous language. Fix server/cache behavior; the app continues using its global language header. |
| Rental capabilities | `subject_id` is required by the deployed endpoint; a subjectless probe returns 400. An authorized lease subject returns account-bound grants. Queried closed legacy subjects grant only `rental_center`; this is not evidence about grants for a signed/active fixture. |
| Legacy projections | Historical initial detail was `financial_closure_status=open,revision=2`; subsequent center was `closed,revision=3`, without a client write. Later shared-pair reads agree. Backend must return first-read consistency evidence and explain reconciliation timing. Do not patch the client to invent a closed state. |
| Banner media | Send `Accept: image/jpeg, image/png, image/webp, application/json`. The original ad now returns 200 image/png but a different digest from the original upload; this fails recovery before any mock activation. See the verification report for exact byte lengths/hashes. |
| Visit reject | App sends `reason=timing_not_suitable` plus `custom_reason`; reply illustrates `unavailable`. Return the accepted enum/catalog and compatibility evidence before requiring a different token. |

Actual sanitized public responses are in the dated evidence directory[^repo-1]. The excerpt below illustrates the supported empty Home projection; it is not a claim that the live Home returned no listings.

Current authenticated observations and tested bodies are in the replacement-account evidence[^repo-40]. The final Flutter test uses `AuthSessionData`, `DioService.refreshSession`, `TenancyInvitationsData`, `DigitalLeasesData`, `RentManagementData`, `DigitalLeaseReadData`, `RentalCenterData` and `RentalApiData` with real HTTP. Original credentials, tokens, cookies and raw account identities stay outside the repository.

<!-- contract: public-home-envelope -->
```json
{"data":{"count":0,"per_page":20,"total_pages":1,"results":[],"banner":null}}
```

<a id="c-2-shared-json-shapes-and-types"></a>

### 2. Shared JSON shapes and types

<a id="c-21-envelope-pagination-and-canonical-receipt"></a>

#### 2.1 Envelope, pagination and canonical receipt

Feature successes use `key=success`, `msg` and `data`; advertising handoff uses `message`. Preserve the family's documented message field and HTTP status. An HTML proxy error, login page or malformed 200 is not a successful resource.

<!-- contract: empty-page -->
```json
{"key":"success","msg":"","data":{"results":[],"count":0,"per_page":20,"total_pages":1,"next":null,"previous":null}}
```

Collections request `page` (one-based) and, in shared feature pagination, `page_size=20`. Return stable deterministic ordering, correct filtered count/page metadata and no duplicate IDs across pages. Parent-scoped pages must not contain other requests' offers or other leases' reports/transitions. A fresh empty page is authoritative. Return an empty collection rather than a placeholder object with an empty ID.

<!-- contract: decision-request -->
```json
{"expected_revision":3,"request_key":"c2a15b57-1376-44e0-af2e-355086934ab1","decision":"accept_review","note":"Reviewed the current terms."}
```

`Decision` in later tables means exactly the above shape with the action's decision token. `effective_on`, `requested_date`, `item_ids` are included only when nonempty/applicable. `note` is emitted even when empty. The URL action is not always identical to the decision token: `/review/` receives `accept_review` or `request_changes`.

Canonical writes return an operation receipt **inside `data` alongside `resource`**. Receipt fields are `id`, `subject_id`, `request_key`, positive `revision`, `status=confirmed`. The receipt subject is the returned resource identity. A new resource can have a different subject than the source used for capability/recovery lookup. For an existing aggregate its revision must advance beyond the reviewed revision. For artifacts such as quotes, receipt revision belongs to the artifact; do not compare it to the source invoice's revision.

<a id="c-22-money-dates-nullability-and-permissions"></a>

#### 2.2 Money, dates, nullability and permissions

| Value | Exact convention |
| --- | --- |
| Accounting Money | `{amount_minor: integer, currency: "EGP", exponent: 2}`; no floating-point major-unit accounting. Unknown values must not become zero. Refund/deposit/fees stay separate. |
| Listing price | `RentalSelection.terms.price` is a decimal **string** in the listing contract, with `price_period`; it is not a Money object. Convert/validate on the server, never confuse it with accounting rent. |
| Revision | Integer; create target normally 0, saved resource positive. `offer_revision`, `invitation_revision`, `request_revision`, `lease_revision`, `roster_revision`, `item_revision` refer to different resources. |
| Civil dates | `YYYY-MM-DD`; `starts_on`/`ends_on_exclusive` are not UTC instants. Preserve inclusive/exclusive semantics and `Africa/Cairo` calendar policy. Legacy `start_date`/`end_date` must be returned exactly as accepted. |
| Instants | Timezone-aware ISO 8601; UTC `Z` recommended for responses. Expiry is server-authoritative; client-visible TTL is not authorization. |
| Permissions | Root `allowed_actions: string[]`, `blocking_reasons: string[]`; legacy invitation also uses `actions.can_respond`. Unknown status tokens must not enable actions. |
| Optional vs null | Follow each serializer. Example: empty legacy `offer_id` is omitted; housing `end_on` is null when unspecified; response `lease_id` may be null/empty before consumption. Do not replace all empty strings with null globally. |
| IDs | Opaque stable strings; never use display labels as IDs. Return `user_id` for chat participants, resource ID for an invitation/connection, and retain the distinction. |

<a id="c-23-exact-accommodation-snapshot"></a>

#### 2.3 Exact accommodation snapshot

<!-- contract: rental-selection -->
```json
{
  "property_id":"property-example","offer_id":"offer-example","offer_revision":7,
  "rental_scope":"bed","name":"Bed A1","room_ids":["room-a"],"room_names":["Room A"],
  "bed_id":"bed-a1","bed_name":"Bed A1",
  "terms":{"price":"10000","price_period":"monthly","rental_period":3,"deposit":"one_month","suitable_for":"students","description":"Shared accommodation close to campus.","smoking_allowed":false,"rules":["Keep shared spaces clean"]},
  "availability":"available","archived":false,"capacity":2,"bathroom_access":["shared"],
  "offer_link":"https://sokoun.app/properties/property-example/offers/offer-example"
}
```

`entire_property`, `room`, `room_group`, `bed` are distinct scopes. Room has one room ID; room group has at least two distinct room IDs; bed has one room and a bed ID/name, with shared-room capacity at least two. Supply matching room labels and resolved terms. Historical snapshots retain original terms after listing edits. Server must reconstruct/validate the canonical snapshot instead of trusting a submitted price. The client now compares structured creation against the accepted invitation snapshot, including names, room/bed identity, capacity, bathroom access and terms; locale-dependent labels must stay consistent through this round trip.

<a id="c-3-capabilities-and-operation-recovery"></a>

### 3. Capabilities and operation recovery

`GET features/v1/rental-capabilities/?subject_id={source_or_resource}&action={action}` returns account-bound `account_id`, `account_verified`, `enabled_capabilities`, `policy_version`, `allowed_actions`, `blocking_reasons`. Supported client capability names: `rental_center`, `rental_interests`, `rental_agreements`, `rent_checkout`, `rental_handovers`, `condition_reports`, `rental_deposits`, `rental_maintenance`, `rental_changes`, `rental_settlement`, `rental_disputes`, `owner_payouts`, `signed_documents`, `rental_reviews`.

`GET features/v1/planning-capabilities/?capability=housing_offers&action=read` optionally includes `subject_id` for scoped commands/reads. Collection authorization currently omits the subject; the actual collection route still must enforce its parent scope.

<!-- contract: planning-access -->
```json
{"key":"success","msg":"","data":{"account_id":"tenant-example","account_verified":true,"policy_version":"planning-policy-v1","enabled_capabilities":["housing_offers"],"verified_services":["housing_offers"],"allowed_actions":["read"],"expires_at":"2027-01-01T12:05:00Z"}}
```

This is a shape example, not a live/future permission grant. Return a short real expiry and only services verified in that environment. Planning names: `lifestyle`, `roommates`, `housing_groups`, `group_visits`, `group_applications`, `housing_requests`, `housing_offers`, `commute`, `tenant_assistant`, `condition_reports`, `move_out_notices`, `replacements`. Mobile build flags and server grants are both required. Empty capabilities/actions or 404 keep the service unavailable.

`GET features/v1/rental-operations/{request_key}/?subject_id={original_request_subject}` is a fresh authorized lookup, not a new command. Preserve the original request subject even if the operation created a new resource.

<!-- contract: operation-confirmed -->
```json
{"key":"success","msg":"","data":{"request_key":"161f3a2b-b1ee-4f73-8994-20e4abf35744","request_subject_id":"invitation-example","status":"confirmed","operation_receipt":{"id":"operation-example","subject_id":"lease-example","request_key":"161f3a2b-b1ee-4f73-8994-20e4abf35744","revision":1,"status":"confirmed"}}}
```

**Current generic client accepts only `confirmed`, `pending`, `unknown`. It rejects `absent_final` because the current backend has no agreed permanent tombstone guarantee.** Older proposal text mentioning final absence is a future requirement, not currently supported behavior. Do not unlock a replacement write with a 404. Any future final-absence support needs a durable server guarantee and coordinated mobile change. Payment lookup's separate `absence_confirmed` contract is described below; it also requires permanent absence, never a temporarily empty list.

Sources: rental API constants[^repo-41], rental capability enum[^repo-42], planning access[^repo-43], operation lookup[^repo-44].

<a id="c-4-c01c02s01--property-visits-and-communication"></a>

### 4. C01/C02/S01 — property, visits and communication

| Method / path | Current client input | Response and critical rule |
| --- | --- | --- |
| GET `homepage/`, `properties/` | Catalog search/scope/filter/paging query | Public published discovery with `rental_schema_version`, `rental_summary` count/scopes/labels/price/period/scope/starting_from; exact filters before pagination |
| GET `properties/types/`, `properties/filter-options/`, `properties/governorates/`, `properties/cities/` | Existing catalog query | Stable catalog IDs and localized labels; do not invent missing district IDs |
| POST `properties/create/`; GET/PATCH `properties/{id}/` | Existing property multipart fields, inventory JSON when enabled | Full saved property, stable room/bed/offer IDs, echoed client keys, revisions, moderation/actions |
| GET `properties/owned/` | Owner filters/pagination, optional `rental_scope` | Owned property inventory, `rental_scopes`, `manageable_offer_count`; no other owner's private drafts |
| POST `properties/{id}/confirm-availability/` | Existing action body | Authoritative `availability_confirmed_at`; `updated_at` is not equivalent |
| POST `properties/{id}/save/`; DELETE `properties/{id}/unsave/` | `{offer_id}` for exact offer; existing legacy property mode when no offer | Echo `offer_id`, `is_saved`; multiple offers under one property independent |
| GET `properties/{id}/available_dates/` | Existing date/availability query | Real selectable dates/slots, consistent with owner calendar |
| GET `properties/owner/properties/{id}/availability/` | `week_start=YYYY-MM-DD` | Owned weekly schedule, editable/locked slot states |
| PUT `properties/owner/properties/{id}/availability/` | `availability_date`, `slots:[{time,is_enabled}]` | Updated schedule; booked/locked slots cannot be silently cleared |
| GET `properties/owner/calendar/` | `year`, `month`, `date=YYYY-MM-DD` | Owner calendar days/visits for the selected month/date |
| POST `properties/{id}/visits/` | `BookVisitBody` below | Saved visit with exact `offer_id`/`offer_snapshot`; validate slot and current offer |
| GET `properties/visits/`, `properties/visits/requests/` | Tenant `page`, optional `status` | Tenant-scoped visits/requests with localized labels/actions and correct page metadata |
| GET `properties/owner/visits/requests/`, `properties/visits/received/` | Owner pagination | Owner-scoped request/received views, including tabs and status labels |
| GET `properties/visits/{id}/`, `properties/visits/requests/{id}/`, `properties/owner/visits/requests/{id}/` | Respective actor resource ID | Authorized detail, current actions, history and contact grant |
| POST `properties/owner/visits/requests/{id}/accept/` | No business fields in current accept command | Updated accepted request; no lease/allocation |
| POST `properties/owner/visits/requests/{id}/reject/` | `reason`, `custom_reason` | Rejected request; reason policy enforced |
| PATCH `properties/visits/{id}/update/` | `{status:"canceled"}` for current tenant cancel | Cancellation result; preserve accepted contact history according to policy |
| POST `properties/visits/{id}/review/` | `cleanliness_rating`, `listing_accuracy_rating`, `owner_interaction_rating`, `comment` | Authorized eligible review, ratings 1..5; no fabricated completion |
| GET `properties/{id}/reviews/` | Pagination | Published reviews with safe author projection |
| POST `chat/conversations/create/` | `{user_id}` of allowed counterparty | Canonical conversation; independent relationship authorization |
| GET `chat/conversations/`, `chat/conversations/{id}/`, `chat/conversations/{id}/messages/` | Actor pagination/cursor according to current chat DTO | Participant-scoped thread/messages, persisted IDs and ordering |
| POST `chat/conversations/{id}/messages/create/` | `{content,client_message_id}` | Canonical persisted message with same client ID; socket retry must not duplicate it |
| POST `chat/conversations/{id}/read/` | Existing read action | Authorized read/unread state; never another participant's thread |

Full listing fields and inventory nesting are in the current serializer matrix[^repo-45], owner draft implementation[^repo-46] and inventory handoff[^repo-47]. For inventory creation preserve `X-Rental-Offers-Version: 1` and `Idempotency-Key: <stable draft UUID>`; `rental_inventory` is a multipart JSON string with `schema_version`, `mode`, `expected_revision`, rooms/beds/shared defaults/media/offers. This is not the structured lease JSON body.

<!-- contract: visit-request -->
```json
{"offer_id":"offer-example","expected_offer_revision":7,"visit_date":"2027-01-15","visit_time":"11:00:00","note":"Please confirm the selected bed can be viewed."}
```

Legacy visit requests omit both offer fields. Current `BookVisitBody` does **not** emit a request key, target revision or timezone. Do not silently require those fields; return any proposed versioned upgrade. Available-date and owner-availability DTOs remain defined by visit models[^repo-48]. Socket send includes `conversation_id`, `content`, `client_message_id`; REST send omits `conversation_id` because it is in the path. ACK, persistence and counterpart broadcast are three independently tested facts.

<a id="c-5-c03--legacy-invitation-and-draft-contract"></a>

### 5. C03 — legacy invitation and draft contract

<a id="c-51-invitation-create-read-and-tenant-response"></a>

#### 5.1 Invitation create, read and tenant response

All routes here start `features/v1/`:

| Route | Input | Output |
| --- | --- | --- |
| POST `tenancy-invitations/` | Legacy body below | Direct `TenancyInvitation` in `data`; owner/source checked |
| GET `tenancy-invitations/` | `workspace`, optional `property_id`, paging | Participant-scoped paginated invitations |
| GET `tenancy-invitations/{id}/` | ID | Direct invitation |
| POST `tenancy-invitations/{id}/respond/` | `decision=accepted|rejected`, **`revision`**, `request_key` | Direct updated invitation |
| GET `lease-tenants/` | `property_id` | Eligible accepted unconsumed tenants as `id`, `display_name` |
| GET `lease-configuration/` | Actor | Approved templates/versions and `can_create`; structured policy extension if supported |

<!-- contract: legacy-invitation-request -->
```json
{"property_id":"property-example","tenant_id":"tenant-example","offer_id":"offer-example","expected_offer_revision":7,"request_key":"fb12f8a4-c4f6-423e-ae14-f8bcb6655dab"}
```

If no rental inventory is selected, omit `offer_id` **and** `expected_offer_revision`. The source visit is resolved by the backend; the current legacy body does not send a `visit_id`.

<!-- contract: legacy-invitation-response -->
```json
{"key":"success","msg":"Invitation created.","data":{"id":"invitation-legacy","property_id":"property-legacy","property_title":"Legacy apartment","owner_id":"owner-example","owner_name":"Owner","tenant_id":"tenant-example","tenant_name":"Tenant","offer_id":null,"offer_snapshot":null,"status":"pending","revision":1,"created_at":"2027-01-01T12:00:00Z","expires_at":"2027-01-08T12:00:00Z","accepted_at":null,"rejected_at":null,"revoked_at":null,"lease_id":null,"eligible_for_lease":false,"actions":{"can_respond":true},"allowed_actions":[],"blocking_reasons":[]}}
```

This example is a **tenant projection for a separate property without inventory**. For the offer-aware create example, return its same property/offer and the complete snapshot from §2.3. `actions.can_respond` is actor-specific: false for owner, true only for the intended tenant while eligible to respond. After accept, increment revision, set `accepted_at`, set `eligible_for_lease` according to current expiry/source/consumption, and remove respond permission. Seven-day validity still applies after acceptance. New draft consumes consent permanently; cancel never restores it.

<!-- contract: legacy-invitation-accept -->
```json
{"decision":"accepted","revision":1,"request_key":"eed8a613-a642-4bce-9a5b-d9c5658d9b98"}
```

<a id="c-52-legacy-draft-creation-and-cancellation"></a>

#### 5.2 Legacy draft creation and cancellation

`POST features/v1/leases/` accepts the existing `LeaseDraftBody`. This route also supports the structured body in §6; distinguish the schemas deliberately on the server.

<!-- contract: legacy-draft-request -->
```json
{"property_id":"property-legacy","tenant_id":"tenant-example","template_id":"eg-residential-v1","template_version":"1","start_date":"2027-01-15","end_date":"2027-07-15","rent":{"amount_minor":500000,"currency":"EGP","exponent":2},"request_key":"60c6c290-e532-4e7f-899a-b1dc1d0630a2"}
```

<!-- contract: legacy-draft-response -->
```json
{"key":"success","msg":"Draft created.","data":{"id":"lease-legacy","property_id":"property-legacy","property_title":"Legacy apartment","invitation_id":"invitation-legacy","owner_name":"Owner","tenant_name":"Tenant","start_date":"2027-01-15","end_date":"2027-07-15","rent":{"amount_minor":500000,"currency":"EGP","exponent":2},"offer_snapshot":null,"status":"draft","revision":1,"can_sign":false,"can_cancel":true,"legacy_read_only":false,"allowed_actions":[],"blocking_reasons":[]}}
```

This owner projection deliberately demonstrates existing compatibility when `owner_id`/`tenant_id` are omitted. If present, they must match the authenticated owner and selected tenant. Dates and rent must match the accepted body. Offer-aware draft adds **only** `offer_id` to this body and returns its exact stored `offer_snapshot`; the body does not send `invitation_id`, `expected_offer_revision`, `rentalSelection` or `hasRentalOffers`. Django must resolve and consume the unique accepted source atomically, validating current inventory; reject ambiguous/stale sources.

`POST features/v1/leases/{id}/cancel/` legacy body is `{revision,request_key}`; return the direct cancelled lease with advanced revision. Same-key replay must return the saved cancellation even though the original revision is now stale. New key on a stale revision must conflict. A cancelled draft has no possession to return and creates no rental invoice. Old read-only history and new cancellable drafts are separate classifications.

Legacy signing's historical body `{revision,request_key}` does not authorize structured signing. Keep signing disabled unless the appropriate service/contract is verified. The old checkout handoff likewise does not replace the current quote-based payment flow.

Sources: invitation backend return[^repo-49], legacy draft body[^repo-50], draft Cubit[^repo-51].

<a id="c-6-c04c06--structured-rental-endpoint-and-body-registry"></a>

### 6. C04–C06 — structured rental endpoint and body registry

All routes in this section start `features/v1/`. `Mutation<T>` means the canonical resource/receipt wrapper in §2. DTO fields, including request field inventories, are in §13 and linked directly to Dart. Do not send a field inventory as an object with every value null: use each serializer's actual types and omission rules.

<a id="c-readiness-interest-invitation-and-agreement"></a>

#### Readiness, interest, invitation and agreement

| Method and relative path | Input / query | Response / required behavior |
| --- | --- | --- |
| GET `rental-capabilities/` | `subject_id`, `action` | `RentalCapabilities`; fresh authenticated verification and scoped actions |
| GET `rental-operations/{request_key}/` | `subject_id` | `RentalOperationLookup`; current client accepts confirmed/pending/unknown only; see section 3 |
| GET `owner-payment-profile/` | Current owner | `OwnerPaymentProfile`; masked beneficiary, required policies, KYC requirements and actions |
| POST `owner-payment-profile/onboarding-session/` | `OwnerOnboardingBody` | `Mutation<OwnerOnboardingSession>`; hosted KYC URL with TTL, subject/revision/key and operation identity |
| GET `rental-interests/` | `workspace`, pagination | `RentalInterest[]`; participant-scoped offer snapshots |
| POST `rental-interests/` | `RentalInterestBody` | `Mutation<RentalInterest>`; verify available exact offer/revision, capacity, desired dates, duration and tenant |
| GET `rental-interests/{id}/` | Interest UUID | `RentalInterest`, including server-derived `source_eligible`, `tenant_id`, `proposal_id`, `invitation_id` |
| POST `rental-interests/{id}/respond/` | `Decision` | `Mutation<RentalInterest>`; reject/other explicitly allowed decisions |
| GET `terms-proposals/` | `workspace`, pagination | `TermsProposal[]` |
| POST `terms-proposals/` | `TermsProposalBody` | `Mutation<TermsProposal>`; source interest and offer revisions, full policy-bound terms |
| GET `terms-proposals/{id}/` | Proposal UUID | `TermsProposal`; immutable current/previous terms and exact offer snapshot |
| PATCH `terms-proposals/{id}/` | `TermsProposalBody` with current target revision | `Mutation<TermsProposal>`; editing invalidates prior approvals |
| POST `terms-proposals/{id}/respond/` | `Decision`: accept/reject/request_changes | `Mutation<TermsProposal>`; both parties act on the same revision |
| GET `tenancy-invitations/` | Existing workspace/property filters | Existing compatible invitation list; extend with scoped actions |
| POST `tenancy-invitations/` | Legacy `CreateTenancyInvitationBody` **or** new `RentalInvitationBody` | Preserve legacy response; use `Mutation<TenancyInvitation>` for interest-sourced body |
| GET `tenancy-invitations/{id}/` | Existing detail route | `TenancyInvitation` with owner/tenant/offer/revision, timestamps and eligibility |
| POST `tenancy-invitations/{id}/respond/` | Existing `{decision,revision,request_key}` | Preserve existing agreed raw invitation response; enforce expiry and current participant |
| POST `tenancy-invitations/{id}/revoke/` | `Decision`: revoke_invitation | `Mutation<TenancyInvitation>`; owner only, before consumption |
| GET `lease-configuration/` | Current actor | `RentalAgreementConfiguration`: approved templates, versions, policy, can_create and permissions |
| GET `leases/` | `workspace`, `period`, `search`, pagination | Extended `DigitalLease[]` for My Rentals; filters all/current/upcoming/ended/pending_settlement |
| POST `leases/` | `RentalAgreementDraftBody` | `Mutation<DigitalLease>`; consume accepted eligible invitation atomically |
| GET `leases/{id}/` | Lease UUID | Extended `DigitalLease`; agreement details, including `legacy_read_only` |
| GET `leases/{id}/rental-center/` | Lease UUID | Fresh participant-scoped `RentalCenter` aggregate; independent states, balances and next actions |
| PATCH `leases/{id}/` | Full draft body with current `expected_revision` | `Mutation<DigitalLease>`; permitted draft edit, same participants/accommodation; invalidate reviews/document signatures |
| POST `leases/{id}/review/` | `Decision`: accept_review/request_changes | `Mutation<DigitalLease>`; review the current exact document/terms revision |
| POST `leases/{id}/submit-for-signature/` | `Decision`: submit_for_signature | `Mutation<DigitalLease>`; readiness, mutual review and inventory hold checks |
| POST `leases/{id}/signing-session/` | `RentalSigningBody` | `Mutation<RentalSigningSession>`; exact document ID/hash, revision, request key and TTL |
| POST `leases/{id}/cancel/` | Existing legacy body or new Decision: cancel_draft | Legacy compatibility or `Mutation<DigitalLease>`; cancel permitted drafts only |
| GET `leases/{id}/timeline/` | `workspace`, pagination | `RentalTimelineEvent[]`; actual immutable events with dates/actors represented by authorized labels |
| GET `leases/{id}/billing-schedule/` | `workspace`, pagination | `BillingPeriod[]`; full server-calculated schedule, issued invoice IDs only when present |

Invitation eligibility: pending/confirmed visits for the same owner, tenant and property, or an eligible interest path. Completed visits remain unsupported until the backend eligibility change is explicitly accepted. Invitation lifetime is seven days, including accepted invitations. Creating a draft consumes an invitation once; cancelling the draft never restores it. Do not silently create a lease by property and tenant alone when an exact room/bed offer is selected.

Owner readiness includes verified identity, listing ownership, beneficiary/KYC, payout readiness and explicit acceptance of the **required** policy versions and complete policy summary. Do not infer acceptance from a previously accepted version. Collect full bank/KYC data through the hosted provider, not mobile fields or logs.

<a id="c-invoices-and-payment"></a>

#### Invoices and payment

| Method and relative path | Input / query | Response / required behavior |
| --- | --- | --- |
| GET `rent-invoices/` | Existing workspace/lease filters, pagination | Extended `RentInvoice[]`; real billing periods and independent balances |
| GET `rent-invoices/{id}/` | Invoice UUID | Extended `RentInvoice`; exact state/revision/balance/allowed_actions/active attempt |
| POST `rent-invoices/{id}/quote/` | `Decision` with current invoice revision and request key | `Mutation<PaymentQuote>`; short-lived SHA-256 fingerprint, payer total and zero tenant service fee |
| POST `rent-invoices/{id}/checkout/` | `RentCheckoutBody`: invoice_id, quote_id, expected_revision, request_key | `Mutation<RentalCheckoutSession>`; one server-recorded attempt before PSP session creation |
| GET `payment-attempts/` | **Required recovery mode:** invoice_id + request_key | `PaymentAttemptLookup`; at most one matching attempt, absence_confirmed, optional active_session |
| GET `payment-attempts/{id}/` | Attempt UUID | `PaymentAttempt`; exact invoice/key/amount, confirmed capture time, receipt, PSP settlement and owner payout states |
| POST `payment-attempts/{id}/reconcile/` | `Decision`: reconcile, current attempt revision and UUID | Direct authoritative `PaymentAttempt`; server-rate-limited PSP reconciliation; never create a charge |

The invoice response exposes `invoice_status`, `balance`, `revision`, `can_pay` and `allowed_actions` containing `quote` and `checkout` when currently permitted. `payment_attempt_id` identifies a live/existing attempt. Without the new quote/permission/revision contract, the app keeps a legacy invoice readable and disables checkout.

Quote DTO (`data.resource`; return the canonical receipt alongside it):

```json
{
  "quote_id":"quote-uuid","invoice_id":"invoice-uuid","invoice_revision":3,
  "payer_amount":{"amount_minor":1000000,"currency":"EGP","exponent":2},
  "tenant_service_fee":{"amount_minor":0,"currency":"EGP","exponent":2},
  "policy_version":"rental-policy-v1","fingerprint":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "expires_at":"2026-10-09T10:05:00Z"
}
```

The nested Money objects above are the implemented DTO. The illustrative fingerprint is a placeholder, not a calculated quote. Return the actual immutable lowercase SHA-256 fingerprint, `rental-policy-v1` and a five-minute expiry. Quote receipt revision belongs to the quote; `invoice_revision` still pins the invoice.

Checkout DTO (`data.resource`; return the canonical receipt alongside it):

```json
{
  "session_id":"session-uuid","payment_attempt_id":"attempt-uuid",
  "invoice_id":"invoice-uuid","quote_id":"quote-uuid","invoice_revision":3,
  "request_key":"request-uuid","status":"created",
  "amount":{"amount_minor":1000000,"currency":"EGP","exponent":2},
  "checkout_url":"https://approved-psp.example/checkout/opaque-session",
  "expires_at":"2026-10-09T10:15:00Z","operation_receipt_id":"operation-uuid",
  "navigation":{
    "allowed_origins":["https://approved-psp.example","https://approved-3ds.example"],
    "return_url":"https://sokoun.example/payments/return?invoice_id=invoice-uuid",
    "return_state":"unpredictable-attempt-bound-nonce",
    "external_schemes":["approved-bank-app"]
  }
}
```

These domains are documentation placeholders; backend configuration must supply real approved PSP/3DS origins. Allowlist exact HTTPS origins, not suffixes or arbitrary redirects. Return callbacks must echo one `state` and one `payment_attempt_id`, match the exact configured return path/query, and be bound to the authenticated attempt. The mobile app does not treat `success=true` as a financial outcome. Restrict native bank app schemes; omit them when unsupported. Never put card details or reusable PSP credentials in API responses.

Recovery lookup example:

```json
{"invoice_id":"invoice-uuid","request_key":"request-uuid","results":[{"payment_attempt_id":"attempt-uuid","lease_id":"lease-uuid","invoice_id":"invoice-uuid","revision":4,"request_key":"request-uuid","quote_id":"quote-uuid","invoice_revision":3,"policy_version":"rental-policy-v1","quote_fingerprint":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","payment_status":"pending","invoice_status":"due","amount":{"amount_minor":1000000,"currency":"EGP","exponent":2},"confirmed_at":null,"receipt_id":"","settlement_status":"pending","payout_status":"held"}],"absence_confirmed":false,"active_session":null}
```

Only expose a reusable `active_session` if it is still valid and matches the original invoice, quote, revision, request key and amount. An empty lookup does not unlock a second charge. `absence_confirmed=true` requires a permanent tombstone; generic `absent_final` is not currently accepted by the client. Captured success requires an authoritative `payment_status=captured` plus `confirmed_at`. Authorization, capture, PSP settlement and owner payout remain four separate facts. Receipt production may lag a confirmed capture; expose its pending state without inventing a receipt URL.

<a id="c-stay-operations-change-agreements-and-final-closure"></a>

#### Stay operations, change agreements and final closure

| Method and relative path | Input / query | Response / required behavior |
| --- | --- | --- |
| GET/POST `leases/{id}/handovers/` | workspace + pagination / `HandoverBody` | `RentalHandover[]` / `Mutation<RentalHandover>`; move_in or move_out |
| GET/PATCH `handovers/{id}/` | UUID / complete HandoverBody at current revision | `RentalHandover` / `Mutation<RentalHandover>`; edit invalidates approvals |
| POST `handovers/{id}/respond/` | Decision: accept/dispute | `Mutation<RentalHandover>`; mutual acceptance on exact condition, keys, meters, inventory and evidence |
| POST `rental-attachments/` | Multipart lease_id, file, mime_type, sha256, request_key | Canonical resource + operation receipt; `RentalEvidence` metadata only |
| GET `rental-attachments/{id}/` | Attachment UUID | Fresh participant-authorized `RentalEvidence` metadata, immutable digest and revision; needed to reconcile an unknown upload |
| GET `rental-attachments/{id}/download/` | Attachment UUID | `RentalEvidenceLink`: id, subject_id=lease UUID, URL, expires_at; participant authorization |
| GET `leases/{id}/deposit/` | Lease UUID | `RentalDeposit`; separate deposit balances and `invoice_id` referencing the combined initial invoice; preserve historical separate-invoice identities |
| GET/POST `leases/{id}/maintenance-requests/` | workspace + pagination / `MaintenanceBody` | List / `Mutation<MaintenanceRequest>`; category, priority, access preferences and evidence |
| GET `maintenance-requests/{id}/` | Request UUID | `MaintenanceRequest`; events, appointment, proposed cost and payer |
| POST `maintenance-requests/{id}/actions/` | `MaintenanceActionBody` | `Mutation<MaintenanceRequest>`; explicitly allowed response/work/cost actions |
| GET/POST `leases/{id}/payment-extension-requests/` | workspace + pagination / `RentalChangeBody` with invoice_id | List / `Mutation<RentalChange>`; original due date remains immutable |
| GET/POST `leases/{id}/amendments/` | workspace + pagination / RentalChangeBody | List / Mutation; effective date and full proposed terms |
| GET/POST `leases/{id}/renewals/` | workspace + pagination / RentalChangeBody | List / Mutation; same tenancy root, no repeated commission or automatic renewal |
| GET/POST `leases/{id}/termination-requests/` | workspace + pagination / RentalChangeBody | List / Mutation; reason and proposed exit date |
| POST `rent-invoices/{id}/external-payment-claims/` | RentalChangeBody with invoice_id, amount, method, evidence | Mutation; a claim is not a PSP capture or an automatic invoice adjustment |
| GET `leases/{id}/external-payment-claims/` | workspace + pagination | Related claim list for rental history |
| GET `payment-extension-requests/{id}/`, `amendments/{id}/`, `renewals/{id}/`, `termination-requests/{id}/`, `external-payment-claims/{id}/` | Change UUID | RentalChange; kind, previous/current terms, dates, permissions |
| POST each change detail's `respond/` | Decision: accept/reject/request_changes; propose_end includes effective_on | Mutation; exact reviewed version and role |
| POST `amendments/{id}/submit-for-signature/`, `renewals/{id}/submit-for-signature/` | Decision: submit_for_signature | Mutation<RentalChange>; freeze document version and validate both reviews |
| POST `amendments/{id}/signing-session/`, `renewals/{id}/signing-session/` | RentalSigningBody | Mutation<RentalSigningSession>; pins change ID, revision, document ID/hash |
| GET `leases/{id}/final-settlement/` | Lease UUID | FinalSettlement; server totals, item IDs/evidence, acceptance/dispute status |
| POST `leases/{id}/final-settlement/propose/` | SettlementBody | Mutation<FinalSettlement>; only permitted lines, validated evidence, server recomputes balances |
| POST `leases/{id}/final-settlement/respond/` | Decision: accept/dispute, optional disputed item_ids | Mutation<FinalSettlement>; neither acceptance nor submission directly returns money |
| GET/POST `refund-requests/` | workspace/lease filters + pagination / RefundBody | List / Mutation<RentalRefund>; request only, operations controls PSP execution |
| GET `refund-requests/{id}/` | Refund UUID | RentalRefund; requested amount, actual refundable balance, provider tracking state |
| POST `refund-requests/{id}/respond/` | Decision if explicitly allowed | Mutation; do not grant ordinary users financial execution/operations approval |
| GET/POST `disputes/` | workspace/lease filters + pagination / DisputeBody | List / Mutation<RentalDispute>; subject identity, reason and authorized evidence |
| GET `disputes/{id}/` | Dispute UUID | RentalDispute; responses and operations resolution |
| POST `disputes/{id}/respond/` | Decision: reply, note | Mutation<RentalDispute>; append-only party reply |
| GET `leases/{id}/documents/` | Pagination | RentalDocument[]; metadata/status only, including contracts, signed changes, receipts and statements |
| GET `rental-documents/{id}/download/` | Document UUID | PrivateDocumentLink: id, subject_id=lease UUID, URL and TTL |
| POST `rental-statements/` | RentalStatementBody: lease_id, starts_on, ends_on_exclusive, target revision/key | Mutation<RentalDocument>; queued statement resource with revision, type=statement and generation status |
| GET/POST `leases/{id}/reviews/` | Pagination / RentalReviewBody | List / Mutation<RentalReview>; one actual tenancy review per permitted author, rating 1..5 |

Maintenance actions currently exposed: `acknowledge`, `reply`, `propose_appointment`, `accept_appointment`, `start_work`, `report_resolved`, `confirm_resolved`, `reopen`, `cancel`, `propose_cost`, `approve_cost`, `reject_cost`. Cost payer is `owner` or `tenant`; unexpected responsibility values are invalid. A proposed cost must not create a charge until the responsible party approves the exact version and amount. Emergency reporting includes contextual support, not a promise of emergency service.

Attachments: V1 UI accepts up to five PNG images, each at most 5 MiB after normalization. The client re-encodes photos to remove metadata and deletes its temporary file after upload. Backend must still verify actual MIME/magic bytes, size, digest, participant/lease ownership, malware status, retention and download permissions. Scanning transitions `pending` to `ready` or `unsafe`; only ready evidence may be attached or downloaded. A parent draft stores approved attachment **metadata/IDs**, never bytes, raw paths or download URLs. Before transmission, the client protects an intent containing `lease_id`, `request_key` and `sha256`. After a confirmed pending response, it also protects the returned `resource_id` and `minimum_revision`; future checks read that ID without another upload. Unknown uploads use scoped operation lookup and then authorized metadata. A wrong digest/lease, regressed revision, unknown status or missing operation never unlocks a new transmission. Durable completion of a ready/unsafe scan clears its upload record; unsafe media never enters a parent form. Generic permanent tombstones are unsupported. Never require the client to retransmit an unknown file to discover its result. Revalidate restored IDs before attachment use. Physical-device camera/gallery permission and upload recovery remain integration checks.

<a id="c-owner-finance-and-contextual-support"></a>

#### Owner finance and contextual support

| Method and relative path | Input / query | Response / required behavior |
| --- | --- | --- |
| GET `owner-payables/` | workspace=owner, optional lease_id, pagination | OwnerPayable[]: gross, commission, processing_fee, net, settlement/payout states and blocking reasons |
| GET `payouts/` | workspace, optional lease_id, pagination | RentalPayout[]; authorized owner view only |
| GET `payouts/{id}/` | Payout UUID | RentalPayout; actual tracking state, masked beneficiary, payable IDs and failure/hold reason |

The mobile client has no endpoint to force payout execution. It never infers owner payout success from a paid invoice. Extend the existing support ticket body with optional `rental_context` containing `lease_id`, `invoice_id`, `payment_attempt_id`, `subject_kind`, `subject_id`. It is context for support routing, not financial permission; validate every supplied ID. Existing tickets without this field remain compatible. Lease responses may supply `chat_thread_id` for the existing authorized chat thread; do not create another messaging transport.

A payment-attempt detail must also include the original `quote_id`, `invoice_revision`, `policy_version` and `quote_fingerprint`. This binds recovery on another app session or device to the same intention. For an unfinished attempt, its lookup may include the existing unexpired `active_session`; return the same attempt/key and authorized checkout session, never create a second charge during a GET. If no active session can safely be resumed, keep status checking and support available.

<a id="c-complete-structured-agreement-example"></a>

#### Complete structured agreement example

POST `features/v1/leases/` (owner, accepted current invitation):

<!-- contract: structured-draft-request -->
```json
{
  "invitation_id": "invitation-example",
  "invitation_revision": 2,
  "property_id": "property-example",
  "offer_id": "offer-example",
  "offer_revision": 7,
  "tenant_id": "tenant-example",
  "terms": {
    "starts_on": "2027-01-31",
    "ends_on_exclusive": "2028-01-31",
    "handover_on": "2027-01-31",
    "monthly_rent": {
      "amount_minor": 1000000,
      "currency": "EGP",
      "exponent": 2
    },
    "deposit": {
      "amount_minor": 1000000,
      "currency": "EGP",
      "exponent": 2
    },
    "deposit_holder": "platform",
    "included_services": [],
    "excluded_services": [],
    "termination_policy": "notice-v1",
    "renewal_policy": "mutual-v1",
    "policy_version": "rental-policy-v1",
    "template_id": "eg-residential-v1",
    "template_version": "1",
    "timezone": "Africa/Cairo",
    "occupants": 1,
    "billing_anchor_day": 31,
    "commission_rate_bps": 1000,
    "commission_payer": "owner",
    "commission_basis": "first_period_base_rent",
    "processing_fee_payer": "platform",
    "renewal_commission_rate_bps": 0
  },
  "request_key": "161f3a2b-b1ee-4f73-8994-20e4abf35744",
  "expected_revision": 0
}
```

Canonical response, owner projection:

<!-- contract: structured-draft-response -->
```json
{
  "key": "success",
  "msg": "",
  "data": {
    "resource": {
      "id": "lease-example",
      "revision": 1,
      "owner_id": "owner-example",
      "tenant_id": "tenant-example",
      "invitation_id": "invitation-example",
      "property_id": "property-example",
      "property_title": "Example shared apartment",
      "owner_name": "Owner",
      "tenant_name": "Tenant",
      "status": "draft",
      "lease_status": "draft",
      "legacy_read_only": false,
      "can_sign": false,
      "can_cancel": false,
      "terms": {
        "starts_on": "2027-01-31",
        "ends_on_exclusive": "2028-01-31",
        "handover_on": "2027-01-31",
        "monthly_rent": {
          "amount_minor": 1000000,
          "currency": "EGP",
          "exponent": 2
        },
        "deposit": {
          "amount_minor": 1000000,
          "currency": "EGP",
          "exponent": 2
        },
        "deposit_holder": "platform",
        "included_services": [],
        "excluded_services": [],
        "termination_policy": "notice-v1",
        "renewal_policy": "mutual-v1",
        "policy_version": "rental-policy-v1",
        "template_id": "eg-residential-v1",
        "template_version": "1",
        "timezone": "Africa/Cairo",
        "occupants": 1,
        "billing_anchor_day": 31,
        "commission_rate_bps": 1000,
        "commission_payer": "owner",
        "commission_basis": "first_period_base_rent",
        "processing_fee_payer": "platform",
        "renewal_commission_rate_bps": 0
      },
      "offer_snapshot": {
        "property_id": "property-example",
        "offer_id": "offer-example",
        "offer_revision": 7,
        "rental_scope": "bed",
        "name": "Bed A1",
        "room_ids": [
          "room-a"
        ],
        "room_names": [
          "Room A"
        ],
        "bed_id": "bed-a1",
        "bed_name": "Bed A1",
        "terms": {
          "price": "10000",
          "price_period": "monthly",
          "rental_period": 3,
          "deposit": "one_month",
          "suitable_for": "students",
          "description": "Shared accommodation close to campus.",
          "smoking_allowed": false,
          "rules": [
            "Keep shared spaces clean"
          ]
        },
        "availability": "available",
        "archived": false,
        "capacity": 2,
        "bathroom_access": [
          "shared"
        ],
        "offer_link": "https://sokoun.app/properties/property-example/offers/offer-example"
      },
      "reviewed_by": [],
      "allowed_actions": [
        "edit_lease",
        "cancel_draft"
      ],
      "blocking_reasons": []
    },
    "operation_receipt": {
      "id": "operation-example",
      "subject_id": "lease-example",
      "request_key": "161f3a2b-b1ee-4f73-8994-20e4abf35744",
      "revision": 1,
      "status": "confirmed"
    }
  }
}
```

The create response must match the authenticated owner, tenant, invitation, property, accepted invitation snapshot and submitted terms, with `status=draft` and `legacy_read_only=false`. A server 200 with mismatched facts remains unresolved in the client. Do not “fix” this by echoing unvalidated request data; derive the response from saved authorized rows.

For edits, preserve participants/accommodation and use current target revision. A terms change invalidates prior reviews/signatures and generates a new document version. Return real `document_id`/`document_hash` only when the artifact exists. Terms policy currently expects owner-funded commission 1000 basis points once on first-period base rent, platform processing fees, renewal commission 0; taxes/refund treatment require an approved policy rather than invented defaults.

<a id="c-initial-invoice-and-activation-policy--approved-2026-10-12"></a>

#### Initial invoice and activation policy — approved 2026-10-12

The owner approved the latest backend reply's ordering: completed signing starts a **48-hour inventory hold**; the server issues **one first invoice containing rent and deposit**; successful capture of its required balance triggers activation. This replaces older wording requiring a separate initial deposit invoice and issuing first rent only after activation. Move-in/possession, payment settlement and owner payout remain independent facts.

The app already supports multiple `RentInvoice.lines` and a `RentalDeposit.invoice_id` pointing to that invoice. Structured signed agreements now expose the existing invoice-list entry before activation. Amounts, expiry, invoice creation and activation remain server-owned. There is no new client `/activate/` command and no client-supplied checkout amount.

The following are **illustrative contract fixtures, not captured deployed invoices**. `invoice_type=rent` uses an existing classification; the backend must confirm the actual deployed classification and line tokens in its schema. Do not invent a new required enum to implement combined billing. The app preserves invoice/line type strings and uses invoice status, permissions and quote evidence for payment eligibility. It currently requires `rental-policy-v1` for quotes: return the real supported policy version and coordinate any version change before rollout; do not weaken that check to accept arbitrary financial policies.

<!-- contract: initial-combined-invoice -->
```json
{"key":"success","msg":"","data":{"id":"invoice-initial-example","lease_id":"lease-example","property_title":"Apartment example","reference":"INITIAL-001","revision":3,"invoice_type":"rent","invoice_status":"due","status":"due","can_pay":true,"period_start":"2027-01-31","period_end_exclusive":"2027-02-28","due_at":"2027-01-30T12:00:00Z","amount":{"amount_minor":2000000,"currency":"EGP","exponent":2},"charges":{"amount_minor":2000000,"currency":"EGP","exponent":2},"credits":{"amount_minor":0,"currency":"EGP","exponent":2},"applied":{"amount_minor":0,"currency":"EGP","exponent":2},"balance":{"amount_minor":2000000,"currency":"EGP","exponent":2},"lines":[{"type":"rent","description":"First rental period","amount":{"amount_minor":1000000,"currency":"EGP","exponent":2}},{"type":"deposit","description":"Security deposit","amount":{"amount_minor":1000000,"currency":"EGP","exponent":2}}],"payment_attempt_id":"","receipt_id":"","allowed_actions":["quote","checkout"],"blocking_reasons":[]}}
```

<!-- contract: initial-deposit-projection -->
```json
{"key":"success","msg":"","data":{"id":"deposit-example","lease_id":"lease-example","invoice_id":"invoice-initial-example","revision":1,"holder":"platform","status":"due","agreed":{"amount_minor":1000000,"currency":"EGP","exponent":2},"due":{"amount_minor":1000000,"currency":"EGP","exponent":2},"collected":{"amount_minor":0,"currency":"EGP","exponent":2},"returned":{"amount_minor":0,"currency":"EGP","exponent":2},"applied":{"amount_minor":0,"currency":"EGP","exponent":2},"disputed":{"amount_minor":0,"currency":"EGP","exponent":2},"remaining":{"amount_minor":0,"currency":"EGP","exponent":2},"allowed_actions":[],"blocking_reasons":[]}}
```

The initial example intentionally has a known unpaid deposit, not a collected deposit. After capture, recompute deposit allocations from the ledger, return the paid invoice and authoritative active lease independently, and keep receipt/payout pending when appropriate. Do not count the full combined total as rent or commission basis. Current approved commission is 10% of first-period base rent, owner funded; deposit is excluded. Keep historic invoices unchanged and prevent a second deposit charge for this combined invoice.

The server must define and test late capture after hold expiry, failed/partial capture, cancellation with funds collected, and pending receipt generation. A clean unfunded never-occupied draft can close immediately; a cancellation with unresolved money must retain financial obligations.

<a id="c-payment-and-hosted-session-contract-cautions"></a>

#### Payment and hosted-session contract cautions

Quote request is a `Decision` with `decision=quote`, current invoice revision and a stable quote-operation key. Checkout request is **only** `invoice_id`, `quote_id`, `expected_revision`, `request_key`; client sends no amount or card details. The returned quote/checkout must match the invoice, quote, key, amount, fingerprint and expiry. Quote and checkout are separate intentions and keys.

<!-- contract: checkout-request -->
```json
{"invoice_id":"invoice-example","quote_id":"quote-example","expected_revision":3,"request_key":"d0a0f1d2-4053-4c67-945a-499b9cae2267"}
```

`GET payment-attempts/?invoice_id=...&request_key=...` is a lookup envelope with `results` (zero or one exact attempt), `absence_confirmed` and optional `active_session`, not an ordinary broad payment history page. Return `absence_confirmed=false` for unresolved absence. Only set true when the original operation is permanently prevented from committing. Reject contradictory true + nonempty results. Reconcile is a direct `PaymentAttempt` response and must never create a charge. Capture requires `payment_status=captured` and authoritative `confirmed_at`; receipt generation, PSP settlement and payout may still be pending.

Hosted checkout navigation contains exact HTTPS `allowed_origins`, `return_url`, unpredictable attempt-bound `return_state` and approved `external_schemes`. Examples using `.example` hosts are placeholders, never a production allowlist. Bind return state/attempt, verify provider signatures on the backend, and use fresh resource readback; URL success text is not financial confirmation. Signing likewise pins document ID/hash/revision with a private expiring session.

<a id="c-7-c08c09s02c06--planning-contracts"></a>

### 7. C08/C09/S02/C06 — planning contracts

Planning endpoints require fresh build + server capability + verified service + action grants. They are not proven deployed by this document. All paths below start `features/v1/`. Unless stated otherwise, POST writes return `Mutation<T>` and GET detail returns direct `T`; lists use §2 pagination.

<a id="c-71-lifestyle-roommates-and-groups"></a>

#### 7.1 Lifestyle, roommates and groups

| Method / route | Request body / response |
| --- | --- |
| GET/POST `lifestyle-profile/` | Read `LifestyleProfile`; save `discoverable`, `habits`, `preferences`, `disclosed`, `expected_revision`, `request_key`; no input `id` or `revision` |
| GET `roommate-candidates/`, `roommate-connections/` | Paged `RoommateRecord` |
| POST `roommate-candidates/{id}/{decision}/` | `decision`, `note`, `candidate_revision`, `expected_revision=0`, `request_key`; candidate operation can create a different relationship resource |
| POST `roommate-connections/{id}/{decision}/` | `decision`, `note`, current `expected_revision`, `request_key`; permitted actor only |
| GET/POST `housing-groups/`; GET `housing-groups/{id}/` | Group list/create/detail; create uses `GroupActionBody(action=create)` |
| POST `housing-groups/{id}/{action}/` | `GroupActionBody`, returning updated **HousingGroup** and receipt for group ID/revision |
| POST `housing-groups/{id}/invitations/` | `group_id`, `group_revision`, `expected_revision=0`, `request_key`; returns new `GroupInvite` receipt |
| GET `group-invitations/{id}/` | Admin-authorized `GroupInvite` |
| POST `group-invitations/preview/` | `{token}`; read-only direct `GroupInvite`, no receipt, no token consumption |
| POST `group-invitations/join/` | `token`, `group_id`, `group_revision`, `expected_revision=group_revision`, `request_key`; updated group + receipt |

Roommate decisions must be taken from current actions/UI (`request`, `accept`, `decline`, `withdraw`, `block` as applicable); `candidate` and connection IDs are distinct. `RoommateRecord` fields: `id`, `user_id`, `display_name`, `status`, `revision`, `reasons`, `disclosures`, `chat_granted`, `allowed_actions`, `blocking_reasons`. Match reasons/disclosures must not leak undisclosed profile answers. Lifestyle answer tokens come from the actual enums/models[^repo-52]; do not translate enum values.

`GroupActionBody` always sends `expected_revision`, `request_key`, `roster_revision`, `action`, `consent`. Create/edit additionally sends `name`, `visibility`, `capacity`, `criteria` (write schema). Nonempty `member_id`, `item_id` + `item_revision`, `note`, `appointment_at` are conditional. `selection` and `proposal` are sent when supplied. `request_visit`/`apply` send `participant_ids` from the current active roster. Do not use their presence as everyone else's consent.

Group actions: `edit`, `transfer_admin`, `remove_member`, `leave`, `archive`, `revoke_invites`, `add_shortlist`, `remove_shortlist`, `vote`, `comment`, `propose_costs`, `approve_costs`; `request_visit`, `consent_visit`, `withdraw_visit_consent` require `group_visits`; `apply`, `consent_application`, `withdraw_application_consent` require `group_applications`.

Group response: `id,name,status,visibility,revision,roster_revision,capacity,criteria,members,shortlist,proposals,visits,applications,allowed_actions,blocking_reasons`. Member: `user_id,name,role,status`. Proposal request: `id,revision,roster_revision,offer_id,offer_revision,start_on,end_on,period,total,contributions`; contributions map user IDs to integer minor amounts; `approved_by` is response-only. Process response: `id,revision,roster_revision,status,selection,participant_ids,consented_ids,appointment_at,qualifying_visit_id,allowed_actions`. All consent is versioned and actor-owned.

GroupInvite returns `id,group_id,group_name,status,link,revision,group_revision,member_count,capacity,expires_at`. Private join link format is `https://sokoun.app/housing-groups/join#<base64url-token>`; do not log/store raw tokens in analytics. Preview and join bodies remain private. Sources: group data and models[^repo-53].

<a id="c-72-housing-requests-and-owner-responses"></a>

#### 7.2 Housing requests and owner responses

| Method / route | Input | Resource |
| --- | --- | --- |
| GET `housing-requests/`; GET `housing-demand/` | Tenant own list / eligible owner feed, paging | `HousingRequest[]` |
| GET `housing-requests/{id}/` | Authorized actor | `HousingRequest` |
| POST `housing-requests/` | `HousingRequestBody(action=publish)` | New `HousingRequest` |
| POST `housing-requests/{id}/{action}/` | Same full body, current revision; `edit`, `pause`, `publish`, `close`, `fulfill` | Updated request |
| GET/POST `housing-requests/{id}/offers/` | Page / `HousingOfferBody` | Scoped offer list / new offer |
| POST `housing-offers/{id}/{decision}/` | `Decision`: `shortlist`, `decline`, `withdraw` | Updated offer |

Criteria **write** fields: `city_id`, `district_ids` (currently empty list), `rental_scope`, `property_type`, `budget_min`, `budget_max`, `price_period`, `start_on`, `end_on` nullable, `people`, `amenities`, `furnished` bool/null. Criteria **read** fields: `city` object, `filters` as `PropertySearchFilters`, `start_on`, `end_on`, `people`, `area_note`. Echoing the write shape as the read shape loses the client's editable city/filter state. `area_note` currently is not sent by `toRequest`; do not claim it is applied as a district filter.

<!-- contract: housing-request-create -->
```json
{
  "expected_revision": 0,
  "request_key": "04c372ed-f263-4dd2-83a8-1a4fa03b974e",
  "action": "publish",
  "title": "Bed close to campus",
  "note": "Move-in at the end of January.",
  "criteria": {
    "city_id": "city-example",
    "district_ids": [],
    "rental_scope": "bed",
    "property_type": "apartment",
    "budget_min": {
      "amount_minor": 500000,
      "currency": "EGP",
      "exponent": 2
    },
    "budget_max": {
      "amount_minor": 1200000,
      "currency": "EGP",
      "exponent": 2
    },
    "price_period": "monthly",
    "start_on": "2027-01-31",
    "end_on": null,
    "people": 1,
    "amenities": [],
    "furnished": true
  },
  "visibility": "eligible_owners"
}
```

Response reconstructs the read criteria (catalog values here are synthetic):

<!-- contract: housing-request-response -->
```json
{
  "key": "success",
  "msg": "",
  "data": {
    "resource": {
      "id": "request-example",
      "user_id": "tenant-example",
      "title": "Bed close to campus",
      "note": "Move-in at the end of January.",
      "status": "published",
      "revision": 1,
      "criteria": {
        "city": {
          "id": "city-example",
          "name": "Example City",
          "slug": "example-city"
        },
        "filters": {
          "search": "",
          "city": "city-example",
          "district": "",
          "ordering": "-created_at",
          "page": 1,
          "page_size": 20,
          "price_min": "5000",
          "price_max": "12000",
          "rental_scope": "bed",
          "property_type": "apartment",
          "price_period": "monthly",
          "suitable_for": "",
          "is_furnished": "true",
          "is_verified": "",
          "smoking_allowed": "",
          "bedrooms": "",
          "bathrooms": "",
          "amenities": []
        },
        "start_on": "2027-01-31",
        "end_on": "",
        "people": 1,
        "area_note": ""
      },
      "expires_at": "2027-02-01T00:00:00Z",
      "allowed_actions": [
        "edit",
        "pause",
        "close"
      ],
      "blocking_reasons": []
    },
    "operation_receipt": {
      "id": "operation-request",
      "subject_id": "request-example",
      "request_key": "04c372ed-f263-4dd2-83a8-1a4fa03b974e",
      "revision": 1,
      "status": "confirmed"
    }
  }
}
```

Owner offer POST body:

<!-- contract: housing-offer-request -->
```json
{
  "expected_revision": 0,
  "request_key": "78f8e5bc-2d9a-4a58-b317-d6f152de5b60",
  "request_id": "request-example",
  "request_revision": 1,
  "selection": {
    "property_id": "property-example",
    "offer_id": "offer-example",
    "offer_revision": 7,
    "rental_scope": "bed",
    "name": "Bed A1",
    "room_ids": [
      "room-a"
    ],
    "room_names": [
      "Room A"
    ],
    "bed_id": "bed-a1",
    "bed_name": "Bed A1",
    "terms": {
      "price": "10000",
      "price_period": "monthly",
      "rental_period": 3,
      "deposit": "one_month",
      "suitable_for": "students",
      "description": "Shared accommodation close to campus.",
      "smoking_allowed": false,
      "rules": [
        "Keep shared spaces clean"
      ]
    },
    "availability": "available",
    "archived": false,
    "capacity": 2,
    "bathroom_access": [
      "shared"
    ],
    "offer_link": "https://sokoun.app/properties/property-example/offers/offer-example"
  },
  "note": "This is the exact bed available for review."
}
```

Tenant detail/list item projection of the new offer (the immediate owner POST response must instead return owner actions such as `withdraw`):

<!-- contract: housing-offer-resource -->
```json
{
  "id": "response-example",
  "request_id": "request-example",
  "owner_user_id": "owner-example",
  "status": "sent",
  "note": "This is the exact bed available for review.",
  "revision": 1,
  "request_revision": 1,
  "selection": {
    "property_id": "property-example",
    "offer_id": "offer-example",
    "offer_revision": 7,
    "rental_scope": "bed",
    "name": "Bed A1",
    "room_ids": [
      "room-a"
    ],
    "room_names": [
      "Room A"
    ],
    "bed_id": "bed-a1",
    "bed_name": "Bed A1",
    "terms": {
      "price": "10000",
      "price_period": "monthly",
      "rental_period": 3,
      "deposit": "one_month",
      "suitable_for": "students",
      "description": "Shared accommodation close to campus.",
      "smoking_allowed": false,
      "rules": [
        "Keep shared spaces clean"
      ]
    },
    "availability": "available",
    "archived": false,
    "capacity": 2,
    "bathroom_access": [
      "shared"
    ],
    "offer_link": "https://sokoun.app/properties/property-example/offers/offer-example"
  },
  "rent": {
    "amount_minor": 1000000,
    "currency": "EGP",
    "exponent": 2
  },
  "deposit": {
    "amount_minor": 1000000,
    "currency": "EGP",
    "exponent": 2
  },
  "price_period": "monthly",
  "allowed_actions": [
    "shortlist",
    "decline"
  ],
  "blocking_reasons": []
}
```

`HousingRequest` returns `id,user_id,title,note,status,revision,criteria,expires_at,allowed_actions,blocking_reasons`. Known statuses: `draft,published,paused,closed,fulfilled,expired`.

`HousingOfferBody` sends `expected_revision=0`, `request_key`, `request_id`, `request_revision`, complete `selection`, `note`. Return `id,request_id,owner_user_id,status,note,revision,request_revision,selection,rent,deposit,price_period,allowed_actions,blocking_reasons`. `rent` and `deposit` are Money. Known statuses: `sent,viewed,shortlisted,declined,withdrawn,expired`. Every returned offer must belong to the parent request; this is now validated before the page is displayed. Two to three **offers** may be compared, including different offers on one property.

<a id="c-73-commute-assistant-and-alerts"></a>

#### 7.3 Commute, assistant and alerts

| Method / route | Request | Response |
| --- | --- | --- |
| POST `commute-searches/` | `destinations` 1..2, `local_time`, `time_kind=depart_at|arrive_by`, `timezone`, `balance`, `hard_limits=true`, `filters`, key/rev0 | `Mutation<CommuteSearch>` |
| GET `commute-searches/{id}/` | Own opaque search ID | `CommuteSearch` |
| GET `commute-searches/{id}/results/` | Paging; no private coordinates in query | `CommuteMatch[]` |
| POST `tenant-assistant/turns/` | `text`, `session_id`, `language`, `previous_turn_id` null when empty, `retain_history=false`, key/rev0 | `Mutation<TenantAssistantReply>` |
| GET `configuration/` | `workspace=tenant`, `lang` | Supported alert cadences/configuration |
| GET/POST `search-alerts/`; GET `search-alerts/{id}/` | Create `name,cadence,filters,request_key`; read own alerts | Legacy direct alert / paginated alerts |
| PATCH `search-alerts/{id}/` | `enabled,revision,request_key` | Direct updated alert |
| DELETE `search-alerts/{id}/` | JSON `revision,request_key` | Cancellation receipt under existing alert contract |

Destination has `label`, `location` using existing PropertyLocation JSON, `mode=driving|walking|transit|cycling`, `limit_minutes`. CommuteSearch: `id,revision,coverage,provider,resolved_at,expires_at,unknown_count`. CommuteMatch: `property_id,title,offer_ids,estimates`; estimate: `destination_label,duration_seconds` nullable, `limit_seconds,status,explanation`. Only `status=ok` and a nonnegative known duration prove a route. Provider timeout/uncovered route is not zero minutes. Apply hard limits and sorting to the full declared catalog before pagination.

Assistant reply: `id,revision,text,filters,unresolved_requirements,grounded_property_ids,actions,costs`. Action kinds: `search,requestDraft,commute,group,property,compare,messageDraft,visitReview`; fields include `title,property_id,offer_id,property_ids`. References must be authorized grounded IDs; unsupported filters belong in unresolved requirements. Cost fields: `label,kind=recurring|deposit|one_time,period,money`. The user reviews every action; do not return executable API paths. Local saved search has no server create endpoint and does not establish alert delivery.

Sources: commute models[^repo-54], assistant models[^repo-55], alert body[^repo-56].

<a id="c-74-condition-reports-move-out-notices-and-replacement"></a>

#### 7.4 Condition reports, move-out notices and replacement

| Method / route | Body / response |
| --- | --- |
| GET `leases/{lease_id}/condition-report-context/` | Direct unsaved ConditionReport template: empty ID, actual lease selection, stable items, permitted baseline; action `create` |
| GET/POST `leases/{lease_id}/condition-reports/` | Scoped list / `ConditionReportBody` → new report + receipt |
| GET `condition-reports/{id}/` | Authorized report |
| POST `condition-reports/{id}/{action}/` | Full `ConditionReportBody`; `submit`, `acknowledge`, `object`, `finalize` |
| GET/POST `leases/{lease_id}/move-out-notices/` | Scoped list / `TransitionBody(kind=moveOutNotice,action=submit)` |
| GET `move-out-notices/{id}/`; POST `move-out-notices/{id}/{action}/` | Read / `acknowledge`, `withdraw` using TransitionBody |
| GET/POST `leases/{lease_id}/replacement-requests/` | Scoped list / `TransitionBody(kind=replacement,action=submit)` |
| GET `replacement-requests/{id}/`; POST `replacement-requests/{id}/{action}/` | Read / `nominate`, `approve_availability`, `approve_candidate`, `withdraw`, `decline`, `cancel` as allowed |
| GET `leases/{lease_id}/replacement-candidates/` | Authorized candidates: `id,display_name,source,revision,consented` |

`ConditionReportBody` always emits `request_key,expected_revision,lease_id,action,kind,inspected_on,selection,items,evidence_ids,baseline_id,baseline_revision`; `baseline_id=null` if absent; `objection` only when nonempty. Kind is `move_in|move_out`. Item: `id,space,label,kind,condition,note,reading,unit,quantity,evidence_ids`; kind `surface|inventory|meter|key`, condition `notInspected|unknown|good|worn|damaged|missing`. Reading is decimal string/null, quantity integer/null. Evidence IDs refer to confirmed private uploads of that lease.

Response adds `id,status,revision,evidence,acknowledgements,baseline_items,history,allowed_actions,blocking_reasons`. Acknowledgment: `user_id,name,status,revision,note`. Known report statuses: `draft,submitted,changes_requested,acknowledged,final,superseded`. Report finalization does not accept handover or charge damage. These routes deliberately do not reuse `handovers/{id}/respond/`.

<!-- contract: move-out-request -->
```json
{"lease_id":"lease-example","kind":"moveOutNotice","action":"submit","request_key":"4bbd8cef-a3f1-4940-9d3e-9952a866ef59","expected_revision":0,"requested_on":"2027-07-31","reason":"Moving after the agreed notice period."}
```

<!-- contract: move-out-response -->
```json
{"key":"success","msg":"Notice received.","data":{"resource":{"id":"notice-example","lease_id":"lease-example","kind":"moveOutNotice","status":"submitted","revision":1,"requested_on":"2027-07-31","received_at":"2027-06-30T12:00:00Z","effective_on":"","reason":"Moving after the agreed notice period.","candidate_id":"","candidate_revision":0,"outgoing_release_status":"","incoming_agreement_status":"","future_availability_status":"","history":[],"allowed_actions":["withdraw"],"blocking_reasons":[]},"operation_receipt":{"id":"operation-notice","subject_id":"notice-example","request_key":"4bbd8cef-a3f1-4940-9d3e-9952a866ef59","revision":1,"status":"confirmed"}}}
```

`TransitionBody` emits the same fields for replacement, plus `candidate_id,candidate_revision` only when candidate ID is nonempty. Response fields are illustrated above. `received_at` is not `effective_on`; empty effective date is intentional until policy makes it effective. Known transition statuses: `draft,submitted,received,acknowledged,review_required,approved,candidate_pending,candidate_consented,signatures_pending,activation_pending,effective,withdrawn,declined,cancelled,expired`. Unknown kinds lose actions; never emit a new kind as if the app understands it.

Sources: ConditionReport and body[^repo-57], transition and body[^repo-58], planning handoff[^repo-59].

<a id="c-8-c07--banner-contract"></a>

### 8. C07 — banner contract

All paths below start `advertising/v1/`. Preserve the existing banner backend handoff[^repo-60] and current banner data/models[^repo-61].

| Method / path | Request | Response / access |
| --- | --- | --- |
| GET `plans/` | Locale | Public `results` with id/title/duration_unit/duration_count/revision/active/price Money |
| POST `owner-advertisements/` | Multipart fields below | Owner ad, server quote/status and durable original artwork reference |
| GET `owner-advertisements/`; GET `owner-advertisements/{id}/` | Own paging / ID | Actor-scoped ad list/detail |
| POST `owner-advertisements/{id}/mock-payment/` | Existing mock-payment body below | Same ad's activation and simulation receipt |
| GET `operations/{operation_id}/` | Original operation ID | Authoritative create/activation recovery, same advertisement |
| GET `placements/tenant-home/` | Locale | Public eligible active carousel, maximum 20 |
| GET `media/{advertisement_id}/` | Owner auth while pending | Original bytes; public only while active/eligible according to policy |

Create multipart fields: `operation_id` (stable ID, max128), `plan_id`, `plan_revision`, `title`, `description`, **`banner` bytes** (JPEG/PNG/WebP); optional `property_id`, optional `offer_id` requiring property. Do not submit a local path or base64 string as a replacement for the multipart file. Backend validates owned target and saved bytes before activation. Plans/revision/price/duration must come from GET, not these docs' historical seed values.

<!-- contract: banner-mock-request -->
```json
{
  "operation_id": "banner-example-payment",
  "payment_mode": "mock"
}
```

Activation response must retain the same advertisement ID and include `status=active`, server `starts_at`/`ends_at`, and `payment` with `id,advertisement_id,operation_id,payment_mode=mock,status=mock_succeeded`. Repeat activation returns the same dates/payment even after natural expiry. Week duration is elapsed time; calendar month/year use the agreed Cairo calendar/clamping/DST policy from the banner handoff.

Keep the original ad/operation on media failure or timeout. Historical pending media 404 is a blocker for the existing operation, not a reason to create a second ad. Return stable error codes, localized `message`, correct `Content-Language` and safe cache headers. Banner mock activation must remain distinct from rental payment capture and from provider sandbox/live evidence.

<a id="c-9-errors-replay-and-client-reaction"></a>

### 9. Errors, replay and client reaction

Return the documented HTTP status plus a readable localized message and machine-readable field/domain codes. Exact deployed error code names must be listed in the backend return; names below express required semantics rather than falsely claiming every server already emits them.

| Situation | Required HTTP/result semantics | Client/retest behavior |
| --- | --- | --- |
| Invalid field/type/catalog/date/MIME | 400 or the explicitly agreed 422; field errors | Preserve input; correct fields; changed intention uses a new key only after prior outcome is resolved |
| Missing/expired authentication | 401 under actual auth contract | Refresh/login through existing transport; no silent actor substitution |
| Authenticated but forbidden | 403, or documented non-disclosing 404 for private existence | No mutation; disable invalid action after fresh resource read |
| Missing resource | 404 | Not a successful empty resource and not proof an unknown operation never committed |
| Stale revision/source/offer/slot | 409 with domain code/current authorized context | Refresh and ask user to review changed facts; never silently resubmit new terms |
| Same key, different semantic payload | 409 idempotency conflict | Keep original operation; do not overwrite its payload |
| Expired invitation/session/token | Document 409/410 contract | New reviewed source/session only after original operation reconciled |
| Rate limit | 429 with `Retry-After` where supported | Preserve draft/key; bounded retry, no charge duplication |
| Service/provider unavailable | 503 or documented domain failure; capability unavailable | Read/reconcile existing work remains available as authorized |
| Timeout/connection lost/5xx after write | Outcome unknown until reconciled | Same identity lookup; do not show success or create replacement mutation |
| Malformed/mismatched 2xx resource/receipt | Contract failure, possibly committed | Preserve operation and investigate/reconcile; never infer rejection from parse failure |

Example **proposed** normalized error (backend must confirm its exact codes and exception adapter; do not emit a success envelope for this):

<!-- contract: revision-error -->
```json
{"key":"error","message":"This record changed. Refresh it before trying again.","code":"revision_conflict","errors":{"expected_revision":["stale_revision"]},"data":null}
```

Server replay must check a saved key/body match before ordinary stale-revision checks, return the same committed resource/receipt identity and avoid repeating outbox/ledger effects. Some reads may now reflect newer revisions; recovery must still prove the original operation. State which response is the immutable replay snapshot and which is current detail. Legacy draft cancellation's historical same-key replay is a required regression.

<a id="c-10-contract-conformance-checklist-for-each-endpoint"></a>

### 10. Contract conformance checklist for each endpoint

For every row in this file, backend must provide: implemented method/path; auth and object scope; schema with required/optional/nullable fields; enums; content type; normal/error statuses; request and response example; idempotency namespace/replay policy; target and source revisions; mutation side effects; counterpart read endpoint; worker/provider dependencies; deployed evidence.

Schema acceptance tests must compare the **actual Dart serialization**, not manually renamed equivalents. Required traps to test:

1. `revision` vs `expected_revision`; `expected_offer_revision` vs `offer_revision`; `terms_proposal_id` spelling; `ends_on_exclusive` vs legacy `end_date`.
2. Direct legacy `data` vs canonical `data.resource`; root-level `allowed_actions`; invitation `actions.can_respond`; artifact receipt revision vs invoice revision.
3. Accounting minor units vs listing decimal strings; unknown amounts vs zero; deposit vs recurring rent; price period compatibility.
4. Housing criteria write vs read; omission vs null; participant ID vs resource ID; typed body fields always emitted even for a decision-only action.
5. Same-key retries, pending lookup, malformed success, scope-mixed lists, account changes, unknown enum values and stale provider callbacks.
6. Owner and tenant views after every transition, plus a stranger/unverified actor. No private document/media/token exposure through collections, deep links or operation lookups.

Publish a versioned OpenAPI document (or equivalent exact schema) for the implemented deployment. Include multipart schemas and error responses, not just successful JSON. If current deployment differs, put each difference in the deviation table before changing mobile calls. Do not fill missing evidence with hypothetical payloads.

<a id="c-11-local-verification-record"></a>

### 11. Local verification record

The examples marked `contract:` are synthetic fixtures. Local tests parse every JSON fence and round-trip representative request DTOs and response/receipt relationships. They do not contact Django, validate real provider credentials or prove remote deployment.

Executed on 2026-10-12 with Flutter **3.44.7** / Dart **3.12.2**:

```bash
cd apps/sokoun_app
make ownerTenantCyclesCheck FLUTTER=/Users/aait/Downloads/flutter_3.44_7/bin/flutter
```

| Check | Result | Scope / limits |
| --- | --- | --- |
| Focused Flutter analysis | No issues found | Changed feature areas and new/affected tests listed in Makefile |
| Default build-gate suite | **263 passed, 23 skipped** | 17 test files; skipped cases require enabled planning gates |
| Enabled planning-gate suite | **39 passed, 4 skipped** | Four planning test files, including Arabic/English offer comparison; four skipped cases assert disabled-build behavior already exercised in the default run |
| Documentation samples | **10 tests passed** within the default suite | All **25 JSON blocks** parse; representative request serializers, legacy/structured responses, criteria mapping and receipts checked |
| Markdown local links / diff whitespace | Passed | Relative file/directory targets exist; `git diff --check` clean |
| Django tests / staging / signing / PSP / deployed workers / physical devices | **Not run in this phase** | Requires backend checkout/returned deployment and authorized integration fixtures |

The two suite counts are separate runs and include shared cases; they are not 302 distinct business journeys. Some existing pure-data fixtures emit localization-key warnings without a mounted localization host; the asserted test results pass. No warning is treated as backend or provider evidence.

These counts describe the original local handoff run, before the backend reply and new billing/Home examples. The reproducible target is ownerTenantCyclesCheck in the app Makefile[^repo-39]. Existing capability defaults remain unchanged; planning flags are enabled only in the fake-transport test invocation. The [reply verification report](#a-4-verification-performed) contains the later local rerun and actual live integration outcomes.

<a id="c-12-backend-return-form"></a>

### 12. Backend return form

Copy this section into **`SOKOUN_OWNER_TENANT_BACKEND_RETURN.md`** and send that file back with the schema/evidence bundle. Fill every row; use `not implemented`, `not deployed`, `not verified` or a concrete blocker instead of leaving ambiguous blanks. Keep credentials, personal data, private token links and raw payment/KYC data out of the bundle.

<a id="c-a-release-identity-and-environment"></a>

#### A. Release identity and environment

| Field | Backend answer |
| --- | --- |
| Backend repository / commit / PR | TO FILL |
| Deployment ID, UTC time, environment and HTTPS API base URL | TO FILL |
| Python / Django / DRF / database versions | TO FILL |
| Web / worker / scheduler / WebSocket release versions | TO FILL |
| Applied migration names; backfill counts; `migrate --check` result | TO FILL |
| Auth classes, access/refresh transport, CSRF/cookie behavior | TO FILL |
| OpenAPI/schema version and artifact path/hash | TO FILL |
| Approved rental/template/privacy policy versions | TO FILL |
| Provider environments and verified service families | TO FILL |
| Server capability/action grants by actor; mobile build requirements | TO FILL |
| Operator, rollback procedure, unresolved-operation recovery owner | TO FILL |

<a id="c-b-endpoint-contract-confirmation-one-row-per-endpointaction"></a>

#### B. Endpoint contract confirmation (one row per endpoint/action)

| Method / full path | Implemented and deployed SHA | Request schema/example | Response schema/example and HTTP status | Actor/object rules | Revision/key/replay behavior | Errors | Evidence artifact |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TO FILL | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |

For each JSON/multipart example, supply a sanitized **actual** request and response with UTC timestamp, locale and actor alias. Preserve field names, types and relationships while replacing identifiers consistently. Include a counterpart read, stale conflict, forbidden actor, duplicate replay and lost-response recovery for writes. Include receipt/operation lookup and linked source revisions. Do not return only endpoint names or Swagger screenshots.

<a id="c-c-cycle-acceptance"></a>

#### C. Cycle acceptance

| Cycle | Implemented / deployed / verified separately | Test IDs and command/result | Both-actor evidence | Provider/job/storage proof | Remaining blocker |
| --- | --- | --- | --- | --- | --- |
| C01 listing/discovery/visit | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C02 rejection/cancel/resubmit | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C03 invitation/legacy draft | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C04 structured agreement/payment/move-in | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C05 active stay/recurring operations | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C06 exit/settlement/replacement | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C07 banner/mock activation/placement | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C08 roommates/groups | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| C09 request/offer/compare/handoff | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| S01 exact accommodation | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| S02 alerts/commute/assistant | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |
| S03 recovery/account isolation | TO FILL | TO FILL | TO FILL | TO FILL | TO FILL |

<a id="c-d-conflict-resolution-and-approved-policy"></a>

#### D. Conflict resolution and approved policy

| Question | Approved answer / version / test |
| --- | --- |
| Public guest discovery permissions (BE001) | TO FILL |
| Original banner media/operation repair (BE002), no replacement ad | TO FILL |
| English visit labels and cache variation (BE003) | TO FILL |
| Cancelled never-occupied draft Rental Center applicability (GAP001) | TO FILL |
| Planning deployment and actual grants (DEP001) | TO FILL |
| Active fixture and signing/payment/payout readiness (DEP002) | TO FILL |
| Counterpart chat broadcast/persistence/reconnect (OBS001) | TO FILL |
| Activation ordering, inventory holds, payment/deposit requirements | TO FILL |
| Studio zero-bedroom rules, partial-period rounding, taxes, refund/commission policy | TO FILL |
| Invitation source eligibility, expiry, ambiguity handling and consumption | TO FILL |
| Financial closure vs legal end/possession; notice/replacement effective boundary | TO FILL |
| Deletion, retention, private group history and provider data retention | TO FILL |
| Generic operation statuses and permanent payment absence guarantees | TO FILL |

<a id="c-e-deviations-requiring-mobile-coordination"></a>

#### E. Deviations requiring mobile coordination

| Current Dart contract | Deployed/proposed difference | Reason and migration/version strategy | Affected cycles | Fixture/example and owner |
| --- | --- | --- | --- | --- |
| TO FILL (or explicitly “none”) | TO FILL | TO FILL | TO FILL | TO FILL |

<a id="c-f-next-integration-test-prerequisites"></a>

#### F. Next integration-test prerequisites

- Dedicated nonproduction environment, allowlisted test identities (owner A/B, tenant A/B/C, unverified, guest), reset/cleanup policy and authorization scope.
- Credentials delivered through the agreed private mechanism; account aliases and resource fixture IDs only in the Markdown.
- Published whole/room/group/bed fixtures, eligible visits/invitations, active lease/invoice/payment fixtures, groups/requests/reports/transitions, media and documents.
- Exact build flags and server capability grants for **passed** families; verification bypass disabled.
- Signing/PSP sandbox details, event delivery/reconciliation instructions, worker/scheduler/storage health evidence, stable operation journal and correlation IDs.
- Reproducible backend test commands/output, deployment and migration evidence, unresolved issue list and designated observer for logs during integration.

After each corrected return, rerun the deployed examples through the Dart models and exercise journeys with separate owner/tenant sessions. The first reply has been checked; public/authentication results and blocked journeys are recorded in the verification report. Local parsing, remote API, provider and device results remain separate.

<a id="c-13-structured-dto-field-appendix"></a>

### 13. Structured DTO field appendix

The following field inventory is synchronized from the existing rental handoff and links to actual Dart models. It is a navigation aid for exact serialization, not a generic all-fields-writable Django serializer. Resource permissions add root `allowed_actions` and `blocking_reasons`. Local recovery DTOs are explicitly not API request bodies. Inspect nested linked models for field types and conditional omissions.

| Client model | Purpose | Wire fields |
| --- | --- | --- |
| RentalAgreementConfiguration[^repo-62] | Resource/read DTO | `templates`, `policy`, `can_create` |
| RentalAgreementDraftBody[^repo-63] | Request | `invitation_id`, `invitation_revision`, `property_id`, `offer_id`, `offer_revision`, `tenant_id`, `terms`, `request_key`, `expected_revision` |
| RentalAgreementTerms[^repo-64] | Resource/read DTO | `starts_on`, `ends_on_exclusive`, `handover_on`, `monthly_rent`, `deposit`, `deposit_holder`, `included_services`, `excluded_services`, `termination_policy`, `renewal_policy`, `policy_version`, `template_id`, `template_version`, `timezone`, `occupants`, `billing_anchor_day`, `commission_rate_bps`, `commission_payer`, `commission_basis`, `processing_fee_payer`, `renewal_commission_rate_bps` |
| RentalCommercialPolicy[^repo-65] | Resource/read DTO | `version`, `commission_rate_bps`, `commission_payer`, `commission_basis`, `processing_fee_payer`, `renewal_commission_rate_bps`, `timezone`, `billing_cycle`, `currency`, `exponent` |
| RentalSigningBody[^repo-66] | Request | `document_id`, `document_hash`, `expected_revision`, `request_key` |
| RentalSigningSession[^repo-67] | Resource/read DTO | `session_id`, `subject_id`, `request_key`, `revision`, `document_id`, `document_hash`, `hosted_url`, `expires_at`, `operation_receipt_id` |
| RentalNotificationContext[^repo-68] | Resource/read DTO | `lease_id`, `invoice_id`, `payment_attempt_id`, `handover_id`, `maintenance_request_id`, `payout_id`, `dispute_id`, `rental_interest_id`, `terms_proposal_id`, `rental_change_id`, `rental_change_kind` |
| RentalDecisionBody[^repo-69] | Request | `expected_revision`, `request_key`, `decision`, `note`, `effective_on`, `requested_date`, `item_ids` |
| RentalCapabilities[^repo-70] | Resource/read DTO | `account_id`, `account_verified`, `enabled_capabilities`, `policy_version` |
| RentalOperationLookup[^repo-71] | Resource/read DTO | `request_key`, `request_subject_id`, `status`, `operation_receipt` |
| RentalOperationReceipt[^repo-72] | Resource/read DTO | `id`, `subject_id`, `request_key`, `revision`, `status` |
| RentalPermissions[^repo-73] | Resource/read DTO | `allowed_actions`, `blocking_reasons` |
| BillingPeriod[^repo-74] | Resource/read DTO | `id`, `start`, `end_exclusive`, `issue_at`, `due_at`, `invoice_id`, `amount`, `status` |
| CheckoutNavigationRules[^repo-75] | Resource/read DTO | `allowed_origins`, `return_url`, `return_state`, `external_schemes` |
| InvoiceLine[^repo-76] | Resource/read DTO | `id`, `type`, `description`, `amount` |
| PaymentAttempt[^repo-77] | Resource/read DTO | `refundable_balance`, `revision`, `lease_id`, `payment_attempt_id`, `invoice_id`, `request_key`, `quote_id`, `invoice_revision`, `policy_version`, `quote_fingerprint`, `payment_status`, `invoice_status`, `amount`, `confirmed_at`, `receipt_id`, `payout_status`, `settlement_status`, `updated_at` |
| PaymentAttemptLookup[^repo-78] | Resource/read DTO | `invoice_id`, `request_key`, `results`, `absence_confirmed`, `active_session` |
| PaymentQuote[^repo-79] | Resource/read DTO | `quote_id`, `invoice_id`, `invoice_revision`, `payer_amount`, `tenant_service_fee`, `policy_version`, `expires_at`, `fingerprint` |
| PaymentRecoveryIntent[^repo-80] | Local/query DTO; not a server resource | `invoice_id`, `request_key`, `quote_id`, `invoice_revision`, `quote_fingerprint`, `payment_attempt_id`, `created_at`, `policy_version`, `amount` |
| RentPaymentState[^repo-81] | Resource/read DTO |  |
| RentalCheckoutSession[^repo-82] | Resource/read DTO | `session_id`, `payment_attempt_id`, `invoice_id`, `quote_id`, `request_key`, `invoice_revision`, `status`, `amount`, `checkout_url`, `expires_at`, `operation_receipt_id`, `navigation` |
| MyRentalsFilter[^repo-83] | Local/query DTO; not a server resource | `period`, `search` |
| RentalCenter[^repo-84] | Resource/read DTO | `id`, `tenancy_root_id`, `revision`, `property_title`, `lease_status`, `status`, `occupancy_status`, `financial_closure_status`, `terms`, `balance`, `next_action`, `timeline`, `billing_schedule`, `chat_thread_id`, `last_updated_at`, `legacy_read_only`, `offer_snapshot` |
| RentalNextAction[^repo-85] | Resource/read DTO | `action`, `resource_id`, `description`, `kind` |
| RentalTimelineEvent[^repo-86] | Resource/read DTO | `id`, `label`, `description`, `occurred_at`, `kind`, `resource_id` |
| RentalChange[^repo-87] | Resource/read DTO | `document_hash`, `document_id`, `id`, `lease_id`, `invoice_id`, `revision`, `kind`, `status`, `reason`, `requested_date`, `original_due_at`, `deferred_until`, `effective_on`, `amount`, `terms`, `previous_terms`, `signature_document_id` |
| RentalChangeBody[^repo-88] | Request | `invoice_id`, `reason`, `requested_date`, `effective_on`, `method`, `amount`, `terms`, `evidence_ids`, `lease_revision`, `request_key`, `expected_revision` |
| RentalDeposit[^repo-89] | Resource/read DTO | `id`, `lease_id`, `revision`, `holder`, `invoice_id`, `status`, `agreed`, `due`, `collected`, `returned`, `applied`, `disputed`, `remaining` |
| DisputeBody[^repo-90] | Request | `lease_id`, `subject_kind`, `subject_id`, `reason`, `evidence_ids`, `request_key`, `expected_revision` |
| RentalDispute[^repo-91] | Resource/read DTO | `id`, `lease_id`, `subject_kind`, `subject_id`, `revision`, `status`, `reason`, `resolution`, `responses`, `evidence` |
| EvidenceUploadBody[^repo-92] | Request | `lease_id`, `file`, `mime_type`, `sha256`, `request_key` |
| HandoverBody[^repo-93] | Request | `kind`, `possession_on`, `condition`, `keys`, `meters`, `inventory`, `evidence_ids`, `request_key`, `expected_revision` |
| HandoverItem[^repo-94] | Resource/read DTO | `id`, `label`, `condition`, `reading`, `evidence_ids` |
| RentalEvidence[^repo-95] | Resource/read DTO | `id`, `lease_id`, `name`, `mime_type`, `size_bytes`, `status`, `sha256`, `revision` |
| RentalEvidenceLink[^repo-96] | Resource/read DTO | `id`, `subject_id`, `url`, `expires_at` |
| RentalHandover[^repo-97] | Resource/read DTO | `id`, `lease_id`, `revision`, `kind`, `status`, `possession_on`, `condition`, `keys`, `meters`, `inventory`, `evidence`, `accepted_by` |
| RentalInterest[^repo-98] | Resource/read DTO | `source_eligible`, `tenant_id`, `id`, `property_id`, `offer_id`, `revision`, `tenant_name`, `desired_start`, `months`, `occupants`, `message`, `status`, `proposal_id`, `invitation_id`, `offer_snapshot` |
| RentalInterestBody[^repo-99] | Request | `property_id`, `offer_id`, `offer_revision`, `desired_start`, `months`, `occupants`, `message`, `request_key`, `expected_revision` |
| TermsProposal[^repo-100] | Resource/read DTO | `id`, `interest_id`, `invitation_id`, `revision`, `status`, `terms`, `previous_terms`, `offer_snapshot` |
| TermsProposalBody[^repo-101] | Request | `interest_id`, `offer_id`, `terms`, `interest_revision`, `offer_revision`, `request_key`, `expected_revision` |
| MaintenanceActionBody[^repo-102] | Request | `action`, `note`, `appointment_at`, `cost`, `cost_payer`, `evidence_ids`, `request_key`, `expected_revision` |
| MaintenanceBody[^repo-103] | Request | `title`, `description`, `category`, `priority`, `access_times`, `evidence_ids`, `request_key`, `expected_revision` |
| MaintenanceEvent[^repo-104] | Resource/read DTO | `id`, `label`, `note`, `at`, `appointment_at`, `cost` |
| MaintenanceRequest[^repo-105] | Resource/read DTO | `id`, `lease_id`, `revision`, `title`, `description`, `category`, `priority`, `access_times`, `status`, `appointment_at`, `proposed_cost`, `cost_payer`, `events`, `evidence` |
| OwnerOnboardingBody[^repo-106] | Request | `expected_revision`, `request_key`, `accepted_policy_versions` |
| OwnerOnboardingSession[^repo-107] | Resource/read DTO | `session_id`, `subject_id`, `request_key`, `revision`, `hosted_url`, `expires_at`, `operation_receipt_id` |
| OwnerPayable[^repo-108] | Resource/read DTO | `id`, `lease_id`, `invoice_id`, `period`, `revision`, `gross`, `commission`, `net`, `processing_fee`, `settlement_status`, `payout_status`, `payout_id`, `blocking_reasons` |
| OwnerPaymentProfile[^repo-109] | Resource/read DTO | `policy_summary`, `required_policy_versions`, `id`, `revision`, `status`, `masked_beneficiary`, `provider`, `requirements`, `accepted_policy_versions` |
| RentalPayout[^repo-110] | Resource/read DTO | `id`, `lease_id`, `revision`, `status`, `amount`, `masked_beneficiary`, `reason`, `submitted_at`, `succeeded_at`, `payable_ids` |
| FinalSettlement[^repo-111] | Resource/read DTO | `id`, `lease_id`, `revision`, `status`, `lines`, `rent_balance`, `deposit_to_return`, `refund_due`, `total_due`, `accepted_by` |
| PrivateDocumentLink[^repo-112] | Resource/read DTO | `id`, `subject_id`, `url`, `expires_at` |
| RefundBody[^repo-113] | Request | `lease_id`, `payment_attempt_id`, `amount`, `reason`, `payment_revision`, `request_key`, `expected_revision` |
| RentalDocument[^repo-114] | Resource/read DTO | `id`, `lease_id`, `type`, `title`, `status`, `created_at`, `revision` |
| RentalRefund[^repo-115] | Resource/read DTO | `id`, `lease_id`, `payment_attempt_id`, `revision`, `status`, `amount`, `refundable_balance`, `reason`, `method` |
| RentalReview[^repo-116] | Resource/read DTO | `id`, `lease_id`, `revision`, `rating`, `comment`, `status` |
| RentalReviewBody[^repo-117] | Request | `rating`, `comment`, `request_key`, `expected_revision` |
| RentalStatementBody[^repo-118] | Request | `lease_id`, `starts_on`, `ends_on_exclusive`, `request_key`, `expected_revision` |
| SettlementBody[^repo-119] | Request | `lines`, `note`, `request_key`, `expected_revision` |
| SettlementLine[^repo-120] | Resource/read DTO | `id`, `type`, `description`, `amount`, `evidence_ids`, `disputed` |
| RentalSupportContext[^repo-121] | Resource/read DTO | `lease_id`, `invoice_id`, `payment_attempt_id`, `subject_kind`, `subject_id` |
| RentalInvitationBody[^repo-122] | Request | `interest_id`, `interest_revision`, `property_id`, `offer_id`, `offer_revision`, `tenant_id`, `terms_proposal_id`, `expected_revision`, `request_key` |
| DigitalLease[^repo-123] | Resource/read DTO | `owner_id`, `tenant_id`, `invitation_id`, `id`, `property_id`, `property_title`, `owner_name`, `tenant_name`, `start_date`, `end_date`, `rent`, `status`, `revision`, `document_url`, `can_sign`, `can_cancel`, `tenancy_root_id`, `lease_status`, `occupancy_status`, `financial_closure_status`, `legacy_read_only`, `terms`, `reviewed_by`, `document_id`, `document_hash`, `hold_expires_at`, `offer_snapshot` |
| RentInvoice[^repo-124] | Resource/read DTO | `id`, `lease_id`, `property_title`, `reference`, `due_date`, `amount`, `status`, `receipt_url`, `can_pay`, `revision`, `invoice_type` (legacy `type` read fallback), `billing_period_id`, `period_start`, `period_end_exclusive`, `due_at`, `deferred_until`, `charges`, `credits`, `applied`, `balance`, `lines`, `payment_attempt_id`, `receipt_id`, `invoice_status`, `offer_snapshot` |
| EvidenceUploadIntent[^repo-125] | Protected local recovery DTO; never submitted as a server resource | `lease_id`, `request_key`, `sha256`, optional confirmed `resource_id`, `minimum_revision`; no bytes, paths or URLs |
| RentCheckoutBody[^repo-126] | Request | `invoice_id`, `quote_id`, `expected_revision`, `request_key` |

---

<a id="part-d"></a>

## Part D — Integration runner, private fixtures and recovery procedure

Included source: `apps/sokoun_app/tool/audit/OWNER_TENANT_CYCLES.md`.

The local target validates app behavior with fixtures. The staging targets make real HTTP requests to the TEST-DO base URL declared in `live_api.py`; they do not switch the production app's feature flags.

<a id="d-commands"></a>

### Commands

From `apps/sokoun_app`:

```bash
make ownerTenantCyclesCheck FLUTTER=/path/to/flutter
make ownerTenantCyclesLiveRead FLUTTER=/path/to/flutter SOKOUN_CYCLES_PRIVATE_DIR=/absolute/private/directory
make ownerTenantCyclesLive FLUTTER=/path/to/flutter SOKOUN_CYCLES_PRIVATE_DIR=/absolute/private/directory
```

`LiveRead` performs public GET/OPTIONS, account login/current-user exchanges and actor-scoped reads. The Flutter companion also refreshes the saved session and verifies the same current user. It sends no business commands. `Live` additionally enables the journaled C03 legacy and C07 original-banner scenarios when fixtures and authenticated actors are available. Its Flutter companion remains read-only apart from authentication/refresh. Both targets attempt the HTTP audit and production Flutter transport checks even if one fails.

Use a new `CYCLES_EVIDENCE_DIR` for each run; default directories contain a UTC timestamp. Existing reports are never silently overwritten. Reuse the **same private directory** for the same business test intention: it holds account cookies, IDs and the operation journal. Keep it outside the repository and never attach it to reports. The code only supports the declared staging origin; there is no production override or database-reset command.

Python exit codes: `0` all selected checks passed, `1` at least one failed check, `2` incomplete/blocked verification. Make/Flutter also return nonzero when assertions fail. Do not suppress exit codes in CI or interpret blocked scenarios as successful coverage.

<a id="d-private-input"></a>

### Private input

Create `credentials.json` with distinct, active, verified accounts. Password and Google authentication use the production app's existing routes. These are placeholders, not real credentials:

```json
{
  "owner_a": {"email":"owner-a@example.test","google_id_token":"PRIVATE_GOOGLE_ID_TOKEN"},
  "owner_b": {"email":"owner-b@example.test","password":"PRIVATE_VALUE"},
  "tenant_a": {"email":"tenant-a@example.test","password":"PRIVATE_VALUE"},
  "tenant_b": {"email":"tenant-b@example.test","password":"PRIVATE_VALUE"}
}
```

Use either `password` or `google_id_token`, with the expected account `email` for identity verification. Google sends only `{"token":"..."}` to `auth/google/`; email is not added to that wire body. Restrict the directory to its owner and the file to mode 0600. Pass paths, never passwords/tokens, on the command line. Expired Google tokens need a fresh sign-in; never copy them into reports.

The originally supplied four seeds returned 401. The replacement owner/tenant supplied privately on 2026-10-12 both authenticated through Python and the real Flutter transport. A primary pair can run eligible positive scenarios. Omit unavailable secondary actors: their checks are BLOCKED (Flutter skips), not PASS. Full unrelated-account denial coverage still requires distinct owner B and tenant B; reusing account A under another alias is rejected.

Optional `fixtures.json`, supplied privately after backend verifies each relationship:

```json
{
  "legacy": {
    "property_id":"REAL_OWNER_A_PROPERTY_ID",
    "source_visit_id":"REAL_PENDING_OR_CONFIRMED_VISIT_ID",
    "draft": {
      "template_id":"CURRENT_SERVER_TEMPLATE_ID",
      "template_version":"CURRENT_SERVER_TEMPLATE_VERSION",
      "start_date":"2027-01-15",
      "end_date":"2027-07-15",
      "rent":{"amount_minor":500000,"currency":"EGP","exponent":2}
    }
  },
  "banner": {
    "advertisement_id":"ORIGINAL_ADVERTISEMENT_ID",
    "operation_id":"ORIGINAL_CREATE_OPERATION_ID",
    "mock_operation_id":"ORIGINAL_MOCK_PAYMENT_OPERATION_ID",
    "artwork_sha256":"ORIGINAL_ARTWORK_SHA256"
  }
}
```

The legacy fixture requires a currently eligible pending/confirmed visit relationship between owner A's property and tenant A. The runner reads the owner-scoped source detail before any invitation write; a cancelled/completed visit cannot authorize that write. `source_visit_id` is a fixture precondition, not an extra field in the invitation POST. For an offer-aware property add `offer_id` and `expected_offer_revision` to `legacy`, using fresh server inventory. Dates must be future-valid, template/version current, and rent approved for this test. The fixture never supplies a tenant identity override; login determines tenant A's actual ID.

The banner fixture must be owned by owner A and refer to the original saved advertisement. If the backend's repaired historical banner belongs to another account, supply that account privately under owner A for this isolated run or keep the scenario blocked. Never create a replacement advertisement to evade missing original media. Use the original mock operation; do not generate a new payment key. The digest must match original uploaded artwork, not a newly substituted placeholder.

<a id="d-journal-and-rerun-behavior"></a>

### Journal and rerun behavior

`cycle-journal.json` binds environment, actor, endpoint, semantic body and a stable request/operation key. It is written atomically and flushed before dispatch. A directory lock prevents concurrent Python runners from racing the same journal. Confirmed stages retain their saved responses and proceed through fresh scenario readbacks; deliberate replay assertions reuse the exact original body.

A timeout, malformed response or identity mismatch leaves the operation unresolved. Rerunning does **not** resend it or replace the key. Use the saved operation/resource lookup with the correct account and obtain authoritative receipt/readback evidence. A 404 is inconclusive. This runner intentionally does not automatically mark a legacy command confirmed from the structured operation endpoint, because that cross-family guarantee has not been supplied. Backend/operator reconciliation is required before resuming that unresolved stage. Do not delete the journal to bypass this stop.

<a id="d-actual-coverage"></a>

### Actual coverage

| Automated check | What it proves when it passes |
| --- | --- |
| Guest Home/catalogs and languages | HTTP reachability, expected envelope shape, language headers; Flutter also parses Home with the actual DTO/transport |
| Planning discovery | Required disabled-response fields; guest client cannot authorize a write |
| Seed authentication | Real login, current user and distinct verified identities; Flutter independently exercises app auth/cookie handling |
| Actor reads | Invitation/lease/invoice collection shapes and account-bound rental capabilities using an authorized `subject_id`; Flutter also uses the actual feature data helpers/DTOs |
| Existing paired lease projections | Shared owner/tenant lease collection, detail and Rental Center agree; revision changes between reads fail for backend investigation |
| C03 primary-pair scenario | Source scope/configuration, invitation/accept/draft/cancel, consent consumption, cancellation replay, both cancelled lease/center projections |
| C03 unrelated-actor denial scenario | Both distinct secondary actors receive 403/404 for the newly created invitation; separately blocked if secondary credentials are absent |
| C07 scenario | Original owner/operation/media digest, same-ad mock activation, unchanged content, replay identity/dates/payment, independent feed/media read |

C01/C02 complete listing/visit/chat/review journeys, C04–C06 provider and scheduled-job flows, C08/C09 undeployed services, comprehensive S01/S03 fault injection, and device runs remain explicit blocked coverage entries. The runner does not claim to automate those complete journeys. Use the detailed scenario matrix in the backend guide; add their executable scenarios against returned concrete fixtures/providers before declaring full integration complete. Existing app unit/widget suites test several of their failure boundaries locally.

<a id="d-evidence-handling"></a>

### Evidence handling

The HTTP audit records sanitized payloads, method/path/status, language/cache headers and timestamps. Authentication bodies/responses are withheld. Raw resource responses and operation identities remain in the private directory. Binary media evidence stores length and SHA-256, not image bytes. The Flutter report contains only request metadata and assertion outcomes; it never stores credentials, cookies or user profiles.

Public pagination shapes intentionally differ from feature envelopes. Home uses `{data:{results:...}}` and does not require `key=success`; feature tests must not impose the feature envelope on Home. Advertising language assertions remain strict even when the payload is otherwise parseable. Media GET includes `application/json` alongside image MIME types, matching the app's negotiated error handling; an image-only Accept header can be rejected by DRF before storage is checked. A 200 image with a different digest fails before activation.

---

<a id="repository-references"></a>

## Optional repository references

Paths below are relative to the mobile repository root. They identify supporting artifacts; the consolidated instructions above are the document to send.

[^repo-1]: `docs/qa/evidence/owner-tenant-reply-2026-10-12/`
[^repo-2]: `docs/qa/evidence/owner-tenant-reply-2026-10-12-verified-actors/followup-observations.json`
[^repo-3]: `docs/qa/evidence/owner-tenant-reply-2026-10-12-verified-actors/verification-summary.json`
[^repo-4]: `packages/core/assets/png/logo.png`
[^repo-5]: `docs/OWNER_BANNER_ADS_MEDIA_UNAVAILABLE_BACKEND_HANDOFF.md`
[^repo-6]: `docs/qa/evidence/owner-tenant-reply-2026-10-12-verified-actors/readbacks/owner_a-legacy-0-detail.json`
[^repo-7]: `docs/qa/evidence/owner-tenant-reply-2026-10-12-verified-actors/readbacks/owner_a-legacy-0-center.json`
[^repo-8]: `docs/qa/evidence/owner-tenant-reply-2026-10-12-verified-actors/scenarios/cycle-report.json`
[^repo-9]: `docs/qa/evidence/owner-tenant-reply-2026-10-12/cycle-report.json`
[^repo-10]: `docs/qa/evidence/owner-tenant-reply-2026-10-12/local-verification.json`
[^repo-11]: `docs/qa/evidence/owner-tenant-reply-2026-10-12-verified-actors/flutter-live-final.json`
[^repo-12]: `SOKOUN_OWNER_TENANT_CYCLES_EXPLAINED_EN.md`
[^repo-13]: `docs/backend/SOKOUN_BACKEND_REQUIRED_FIXES.md`
[^repo-14]: `docs/qa/SOKOUN_AUDIT_REPORT.md`
[^repo-15]: `docs/qa/SOKOUN_FLOW_TEST_MATRIX.md`
[^repo-16]: `docs/qa/evidence/run-2026-10-11/`
[^repo-17]: `apps/sokoun_app/lib/features/owner/home/`
[^repo-18]: `apps/sokoun_app/lib/features/shared/rental_offers/`
[^repo-19]: `apps/sokoun_app/lib/features/tenant/visits/`
[^repo-20]: `apps/sokoun_app/lib/features/owner/visits/`
[^repo-21]: `apps/sokoun_app/lib/features/shared/tenancy_invitations/`
[^repo-22]: `apps/sokoun_app/lib/features/shared/digital_leases/`
[^repo-23]: `apps/sokoun_app/lib/features/shared/rental_interests/`
[^repo-24]: `apps/sokoun_app/lib/features/shared/rent_management/`
[^repo-25]: `apps/sokoun_app/lib/features/shared/rental_center/`
[^repo-26]: `apps/sokoun_app/lib/features/shared/rental_maintenance/`
[^repo-27]: `apps/sokoun_app/lib/features/shared/rental_changes/`
[^repo-28]: `apps/sokoun_app/lib/features/shared/rental_handovers/`
[^repo-29]: `apps/sokoun_app/lib/features/shared/rental_settlement/`
[^repo-30]: `apps/sokoun_app/lib/features/shared/banner_ads/`
[^repo-31]: `apps/sokoun_app/lib/features/tenant/roommates/`
[^repo-32]: `apps/sokoun_app/lib/features/shared/housing_groups/`
[^repo-33]: `apps/sokoun_app/lib/features/shared/housing_requests/`
[^repo-34]: `apps/sokoun_app/lib/features/owner/housing_demand/`
[^repo-35]: `apps/sokoun_app/lib/features/tenant/commute/`
[^repo-36]: `apps/sokoun_app/lib/features/tenant/ai_assistant/`
[^repo-37]: `apps/sokoun_app/lib/features/shared/premium/data/`
[^repo-38]: `apps/sokoun_app/lib/features/shared/recovery/`
[^repo-39]: `apps/sokoun_app/Makefile`
[^repo-40]: `docs/qa/evidence/owner-tenant-reply-2026-10-12-verified-actors/`
[^repo-41]: `apps/sokoun_app/lib/features/shared/premium/data/rental_api_constants.dart`
[^repo-42]: `apps/sokoun_app/lib/features/shared/premium/data/enums/rental_capability.dart`
[^repo-43]: `apps/sokoun_app/lib/features/shared/premium/data/models/planning_access.dart`
[^repo-44]: `apps/sokoun_app/lib/features/shared/premium/data/rental_operation_data.dart`
[^repo-45]: `docs/qa/SOKOUN_SERIALIZER_MATRIX.md`
[^repo-46]: `apps/sokoun_app/lib/features/owner/home/data/owner_draft_data.dart`
[^repo-47]: `MOBILE_ALL_FEATURES_BACKEND_HANDOFF.md#4-rental-inventory-integration`
[^repo-48]: `apps/sokoun_app/lib/features/owner/visits/data/models/`
[^repo-49]: `TENANCY_INVITATIONS_BACKEND_RETURN_HANDOFF.md`
[^repo-50]: `apps/sokoun_app/lib/features/shared/digital_leases/data/models/lease_draft_body.dart`
[^repo-51]: `apps/sokoun_app/lib/features/shared/digital_leases/presentation/cubits/lease_draft_cubit.dart`
[^repo-52]: `apps/sokoun_app/lib/features/tenant/roommates/data/`
[^repo-53]: `apps/sokoun_app/lib/features/shared/housing_groups/data/`
[^repo-54]: `apps/sokoun_app/lib/features/tenant/commute/data/models/`
[^repo-55]: `apps/sokoun_app/lib/features/tenant/ai_assistant/data/models/`
[^repo-56]: `apps/sokoun_app/lib/features/tenant/premium_alerts/data/models/premium_alert_body.dart`
[^repo-57]: `apps/sokoun_app/lib/features/shared/rental_handovers/data/models/condition_report.dart`
[^repo-58]: `apps/sokoun_app/lib/features/shared/rental_changes/data/models/tenancy_transition.dart`
[^repo-59]: `docs/sokoun_new_features_backend_handoff.md`
[^repo-60]: `MOBILE_OWNER_BANNER_ADS_API_HANDOFF.md`
[^repo-61]: `apps/sokoun_app/lib/features/shared/banner_ads/data/`
[^repo-62]: `apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_agreement_configuration.dart`
[^repo-63]: `apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_agreement_draft_body.dart`
[^repo-64]: `apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_agreement_terms.dart`
[^repo-65]: `apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_commercial_policy.dart`
[^repo-66]: `apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_signing_body.dart`
[^repo-67]: `apps/sokoun_app/lib/features/shared/digital_leases/data/models/rental_signing_session.dart`
[^repo-68]: `apps/sokoun_app/lib/features/shared/notifications/data/models/rental_notification_context.dart`
[^repo-69]: `apps/sokoun_app/lib/features/shared/premium/data/models/rental_action_body.dart`
[^repo-70]: `apps/sokoun_app/lib/features/shared/premium/data/models/rental_capabilities.dart`
[^repo-71]: `apps/sokoun_app/lib/features/shared/premium/data/models/rental_operation_lookup.dart`
[^repo-72]: `apps/sokoun_app/lib/features/shared/premium/data/models/rental_operation_receipt.dart`
[^repo-73]: `apps/sokoun_app/lib/features/shared/premium/data/models/rental_permissions.dart`
[^repo-74]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/billing_period.dart`
[^repo-75]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/checkout_navigation_rules.dart`
[^repo-76]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/invoice_line.dart`
[^repo-77]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_attempt.dart`
[^repo-78]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_attempt_lookup.dart`
[^repo-79]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_quote.dart`
[^repo-80]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/payment_recovery_intent.dart`
[^repo-81]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/rent_payment_state.dart`
[^repo-82]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/rental_checkout_session.dart`
[^repo-83]: `apps/sokoun_app/lib/features/shared/rental_center/data/models/my_rentals_filter.dart`
[^repo-84]: `apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_center.dart`
[^repo-85]: `apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_next_action.dart`
[^repo-86]: `apps/sokoun_app/lib/features/shared/rental_center/data/models/rental_timeline_event.dart`
[^repo-87]: `apps/sokoun_app/lib/features/shared/rental_changes/data/models/rental_change.dart`
[^repo-88]: `apps/sokoun_app/lib/features/shared/rental_changes/data/models/rental_change_body.dart`
[^repo-89]: `apps/sokoun_app/lib/features/shared/rental_deposits/data/models/rental_deposit.dart`
[^repo-90]: `apps/sokoun_app/lib/features/shared/rental_disputes/data/models/dispute_body.dart`
[^repo-91]: `apps/sokoun_app/lib/features/shared/rental_disputes/data/models/rental_dispute.dart`
[^repo-92]: `apps/sokoun_app/lib/features/shared/rental_handovers/data/models/evidence_upload_body.dart`
[^repo-93]: `apps/sokoun_app/lib/features/shared/rental_handovers/data/models/handover_body.dart`
[^repo-94]: `apps/sokoun_app/lib/features/shared/rental_handovers/data/models/handover_item.dart`
[^repo-95]: `apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence.dart`
[^repo-96]: `apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_evidence_link.dart`
[^repo-97]: `apps/sokoun_app/lib/features/shared/rental_handovers/data/models/rental_handover.dart`
[^repo-98]: `apps/sokoun_app/lib/features/shared/rental_interests/data/models/rental_interest.dart`
[^repo-99]: `apps/sokoun_app/lib/features/shared/rental_interests/data/models/rental_interest_body.dart`
[^repo-100]: `apps/sokoun_app/lib/features/shared/rental_interests/data/models/terms_proposal.dart`
[^repo-101]: `apps/sokoun_app/lib/features/shared/rental_interests/data/models/terms_proposal_body.dart`
[^repo-102]: `apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_action_body.dart`
[^repo-103]: `apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_body.dart`
[^repo-104]: `apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_event.dart`
[^repo-105]: `apps/sokoun_app/lib/features/shared/rental_maintenance/data/models/maintenance_request.dart`
[^repo-106]: `apps/sokoun_app/lib/features/shared/rental_payouts/data/models/owner_onboarding_body.dart`
[^repo-107]: `apps/sokoun_app/lib/features/shared/rental_payouts/data/models/owner_onboarding_session.dart`
[^repo-108]: `apps/sokoun_app/lib/features/shared/rental_payouts/data/models/owner_payable.dart`
[^repo-109]: `apps/sokoun_app/lib/features/shared/rental_payouts/data/models/owner_payment_profile.dart`
[^repo-110]: `apps/sokoun_app/lib/features/shared/rental_payouts/data/models/rental_payout.dart`
[^repo-111]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/final_settlement.dart`
[^repo-112]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/private_document_link.dart`
[^repo-113]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/refund_body.dart`
[^repo-114]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_document.dart`
[^repo-115]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_refund.dart`
[^repo-116]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_review.dart`
[^repo-117]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_review_body.dart`
[^repo-118]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/rental_statement_body.dart`
[^repo-119]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_body.dart`
[^repo-120]: `apps/sokoun_app/lib/features/shared/rental_settlement/data/models/settlement_line.dart`
[^repo-121]: `apps/sokoun_app/lib/features/shared/support/data/models/rental_support_context.dart`
[^repo-122]: `apps/sokoun_app/lib/features/shared/tenancy_invitations/data/models/rental_invitation_body.dart`
[^repo-123]: `apps/sokoun_app/lib/features/shared/digital_leases/data/models/digital_lease.dart`
[^repo-124]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/rent_invoice.dart`
[^repo-125]: `apps/sokoun_app/lib/features/shared/rental_handovers/data/models/evidence_upload_intent.dart`
[^repo-126]: `apps/sokoun_app/lib/features/shared/rent_management/data/models/rent_checkout_body.dart`

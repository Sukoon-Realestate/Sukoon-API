# Coverage and remaining acceptance work

This is a substantial QA pass, not exhaustive release certification. A passing unit test, an HTTP 200 page shell, a discovered callback and a completed user journey are different evidence. No statement here means every button was clicked or every security threat was ruled out.

## Environments

- Hosted API: `https://api.sukoon.rent`; public web/admin: `https://www.sukoon.rent`.
- Installed mobile app: dev flavor, version 1.0.0 (7), iPhone 18 Pro simulator, iOS 27.0; an existing authenticated session. Real hosted-looking listing data was rendered, but the installed app's effective Remote Config origin and exact compiled revision were not independently extracted. Therefore native observations and direct hosted probes are retained separately.
- Authenticated Next.js checks: merged `frontend/landing` app on localhost:3037, connected to a new disposable SQLite backend on 127.0.0.1:8037. Synthetic admin, tenant, ticket and catalog data only. Test settings use the repository's security bypass; this does not prove production MFA behavior.
- Backend suites: fresh test database and private storage; additional HTTP rerun with socket access; PostgreSQL-dependent tests on a separately initialized password-protected cluster on 127.0.0.1:55447. No production database was migrated or reset.
- Source provenance is in [provenance.json](evidence/provenance.json). Neither the hosted backend revision nor the hosted portal revision was proven equal to this source checkout.

## Native mobile checks

| Area | Exercised | Remaining |
|---|---|---|
| Individual Home | Category/feed rendering, search entry, workspace switcher | Every category, feed pagination, offline freshness and personalization |
| Search/filter | Sort choice sheet, lowest price, required price-period feedback, monthly selection, apply and priced results | Exhaustive combinations, malformed numeric inputs, maps, geolocation and network interruption |
| Property | Result-to-detail navigation, price/terms, viewing-request form and phone notice | Photo/video/tour playback, full booking/acceptance/cancellation cycles across two hosted actors |
| Visits | All, Pending, Rejected, empty-state reset; Accepted failure in Arabic and English; day-agenda entry | Date/time proposals, arrival, completion, cancellation and concurrent changes on device |
| Saved | Properties/chat tabs, saved item rendering, filter entry and cancel | New folders, compare, move/remove, server paging and stale offers |
| Chat | Inbox/unread entry, media/storage screen, policy menu cancel, refresh and disabled empty-cache clear | Hosted message sends, attachments, recording, reconnect, receipts, search and moderation cycles |
| Account | Profile, preferences, security-session read, privacy policy, English language switch | Login/recovery/closure, email/password changes and full security challenge flows on device |
| Owner | Switch into workspace, Home, inventory tabs, single-unit creation form, empty validation and Back-flow failure | Publishing/editing/retirement, owner visit decisions and nonempty portfolio cycles |
| Student/company | Existing automated suites; only Individual/Owner were offered in current runtime switcher | Native deferred-workspace cycles require an explicitly enabled QA environment |
| Localization | Core native navigation in Arabic and English; Accepted bug in both; stale Home catalog labels after changing locale in both directions | Every screen, long strings, RTL/LTR forms, all accessible text scales and screen-reader interactions |

Account language/workspace are restored at the end of the UI pass. Existing customer messages, credentials and account identifiers are not copied into the report. Read navigation may update normal view/last-seen telemetry.

## Next.js portal and public web

| Area | Exercised | Remaining |
|---|---|---|
| Hosted admin login | Unauthenticated redirect; empty submit; password visibility; recovery section; nonexistent test-account rejection | Hosted staff login, MFA and role-by-role sessions |
| Local admin shell | Login, navigation groups, user/property/support/platform sections, account menu and successful sign-out back to Login | Every shortcut, mobile browser layout and full keyboard/screen-reader pass |
| Users | List/detail, suspended filter, nonexistent search, reset; fabricated rating confirmed | Suspend/reinstate a separate disposable account, KYC review with synthetic evidence |
| Property review/tours | Queue entry, status menu/all, empty states, disabled paging | Positive approval/rejection/revision and media/tour evidence review |
| Support | All/escalated/owner/individual scopes, refresh; synthetic ticket detail, empty reply validation, claim, reply, internal note, escalation, re-claim and resolve | Uploads, information requests/evidence review, reassignment to another role and competing operator revisions |
| Content | Property-type creation, edit, version 1→2, refresh persistence, change-history expansion | Every content kind, stale edit conflict, uncertain-response recovery in the browser |
| Roles | Role rules, invitation form, empty submit validation and cancel | Positive staff grants, independent identity review and revocation under production MFA policies |
| Audit/health | Audit filter/search, inert CSV button; health refresh and truthful unavailable telemetry | Nonempty complete history, fault-injected audit errors and real hosted worker telemetry |
| Financial workflows | Existing automated backend/frontend coverage; MVP excludes portal financial destinations | Full browser billing/payout/refund/chargeback/provider cycles in a designated enabled sandbox |
| Public web | Arabic page, feature select/next/previous/pause, FAQ expansion, download anchor; both locale/legal routes via HTTP | Real store destinations, complete English interactions, responsive menu, contact/deletion requests, sandbox checkout completion |

All 56 standalone admin regression tests and 3 merged-build configuration tests passed. Standalone and merged production builds passed. These checks do not substitute for every row action on a populated hosted portal.

## Backend and security

The full MVP-default suite collected 6,202 cases. Its per-test release-mode plugin also enables designated deferred-workflow tests; this is broader than testing only MVP endpoints. Original run: 5,691 passed, 489 skipped, 10 xfailed, 12 HTTP fixture setup errors. A socket-enabled rerun passed 40 cases and skipped 10 PostgreSQL-dependent cases; seven original setup errors passed, while five required PostgreSQL. The supplemental PostgreSQL run passed 477, skipped five independent-cluster recovery drills and recorded two known expected failures. Reconciled by exact case identity, the 6,202 cases finish at **6,168 passed, 22 skipped and 12 expected failures**, with no unexpected backend failure remaining. See [consolidated results](BACKEND-RESULTS.md).

Hosted probe repeat: 56 requests, 54 met the documented status expectations and two association URLs failed with 504. Private endpoints denied anonymous access; a malformed bearer token was denied; the untrusted-origin preflight returned no permissive allow-origin header. Selected configuration-disclosure paths returned denial/not-found without a Python traceback. Public malformed pagination/search requests were checked for bounded client errors or tolerated inputs, not full semantic correctness for every filter.

31 authenticated local admin HTTP checks passed across session, dashboard, user/KYC/property/reports/moderation/support/catalog/roles/settings/health/audit endpoints, with nonexistent search, out-of-range paging and invalid analytics period cases.

Dependency audits checked both JavaScript lockfiles and pinned Python default dependencies. They identify affected versions, not demonstrated exploitation. The following were not comprehensively assessed: all object-level cross-account IDOR combinations, credentialed CORS across every deployment origin, CSRF on every command, every upload parser, stored/reflected XSS, SSRF sinks, rate-limit bypass, infrastructure/IAM/secrets exposure, denial-of-service capacity, backup restoration, production worker/reconciliation correctness, penetration testing and independent security review.

## Source inventory and test gaps

[Inventory summary](evidence/inventory/control_inventory_summary.json): 79 feature areas, 884 action families, 4,583 mobile/web callback/control candidates, 1,334 backend entry candidates and 6,449 proposed case rows. These are source discoveries with pending reachability/case review. The ledger has zero automatically attached runtime observations; the separate manual observations above must not be mistaken for completion of those 6,449 rows.

Six Dart parse diagnostics came from the inventory collector; the actual Dart analyzer reported no compile errors. Treat collector diagnostics as inventory limitations until parser compatibility is checked. The app analyzer reported one async warning plus style notices. The full mobile suite is red and stalled, so complete native acceptance remains open.

Remaining backend skips include external native audio clips, externally generated Flutter request artifacts, independent recovery drill infrastructure, optional OpenCV and locked tour-validator dependencies. Company discussion restrictions are deliberate release gates. Two existing expected failures describe `BUG-AUTH-01`, a company signing/payment membership-versus-mandate mismatch; resolve that product/authority model before restoring those workflows. Do not convert intentional release gates into product bugs or silently enable deferred features.

## Suggested fix sprints

1. **Release blockers and dependency triage:** MOB-001, intermittent MOB-002, PRIV-001, ADM-001, HOST-001, store availability decision and runtime security advisories. Verify patched builds and real release signing identities.
2. **Admin reliability:** ADM-002/003, truthful permission labels, lint baseline, populated role-specific review/support/catalog cycles, failures/retries and stale revisions.
3. **Mobile regression recovery:** classify all 497 failed/error cases, repair obsolete fixtures/finders and product defects separately, remove hangs and obtain a successful complete run. Preserve Arabic/English/accessibility assertions.
4. **Connected acceptance:** reconcile the control ledger with executed cases; provision isolated hosted roles/data and sandbox providers; complete owner/tenant, enabled company/student, media, payments, offline/background and device matrices. Verify Android, iOS, tablet and production profile performance on physical devices.

No production-readiness sign-off is given by this report.

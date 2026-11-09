# Area 6 — Admin, shared code and operations

**Scope:** 178 assigned production/configuration/script files statically inventoried, plus selected dependency,
configuration, deployment and shared-policy sources. Manual paths below were verified in the current source. Runtime
observations and limits are in [BASELINE.md](../BASELINE.md). Application code was not changed.

<a id="a6-01"></a>
## A6-01 — High — Legacy moderation route bypasses canonical decision invariants

**Evidence:** `core_apps/admin_api/views/moderation.py:44-56` remains routed through `admin_api/urls.py`.
`services/moderation_service.py:57-77` checks the staff role and locks the property, then writes HIDDEN/is_verified=False.
It does not use `properties/services/moderation.py`'s independent-owner check, expected-version/idempotency decision,
review revision and persisted domain/audit events used by `views/property_views.py:68-85`.

**Impact:** an otherwise authorized reviewer can take the legacy command path without the canonical self-review,
stale-command, receipt and downstream event rules. This is alternate-path policy divergence; role checking is present.

**Task:** Sprint 01/10: route all moderation aliases through one command service or retire the alias explicitly.
**Acceptance:** same-owner reviewer, stale version, duplicate/conflicting key and visibility transitions behave identically
on every alias; decision/audit/planning events occur exactly once; no role or current-authority check is lost.

<a id="a6-02"></a>
## A6-02 — Medium — Admin KYC filters reference the wrong model relation

**Evidence:** `admin_api/filters.py:44-56` filters a User queryset using `kyc_submissions__status`; submissions belong to
`Profile`, with the user selector joining `profile` (`services/user_service.py:13-25`). The relation is
`profile__kyc_submissions`, not a reverse relation directly on User.

**Impact:** pending/rejected admin-user KYC filters raise FieldError/500 instead of producing the requested list.
**Task:** Sprint 03: use a correct current-submission selector/Exists predicate and clarify superseded/current status.
**Acceptance:** pending/rejected/verified, no-submission and mixed historical submissions return correct distinct users
without 500 or obsolete evidence being mistaken for current status.

<a id="a6-03"></a>
## A6-03 — Medium — Admin property list has measured per-row query growth

**Evidence:** `admin_api/serializers/property_serializers.py:73-78` issues `ContentView.count()` per property. The selector
`services/property_service_parts/get_admin_properties_queryset.py:39-46` joins relations and prefetches images but does not
prepare that count. Isolated selector/serializer probe: **5 rows → 7 queries; 40 rows → 42 queries**, with 5/40 content-view
count queries respectively. The image-count default expression is eager, but prefetched images already mitigate its SQL;
do not count it as another proven query per row.

**Task:** Sprint 04/10: annotate or bulk-map view counts and avoid unnecessary image row loading when only counts are
needed. **Acceptance:** valid 5/40/100-row pages retain data/permissions with a bounded query budget and no per-row COUNT.

<a id="a6-04"></a>
## A6-04 — Medium — KYC and report projections still query per list item

**Evidence:** `serializers/kyc_serializers.py` resolves owner properties and report existence per submission;
`services/kyc_service.py` joins profile/user but does not prepare all of these values. Report projections in
`serializers/report_serializers_parts/support_ticket_serializer.py` similarly resolve properties/chat-case context per row.

**Task:** Sprint 04: page-specific selectors with Exists/annotations and batch context, then pure projections.
**Acceptance:** 1/20/100-row KYC/report lists have recorded bounded queries; sensitive evidence/current reviewer authority
and current submission semantics are unchanged. This is source-proven query fan-out, not a measured latency claim.

<a id="a6-05"></a>
## A6-05 — Medium — Transaction/audit histories are truncated before filtering and pagination

**Evidence:** `services/financials_service_parts/get_transactions_list.py:9-11,35-36,54-65` takes at most 500 rows per
source before status/search filtering and sorting. `services/system_service_parts/get_audit_logs.py:28-81,100-112` takes
at most 100 rows per source before filtering. Views later paginate the already truncated Python lists.

**Impact:** older matching transactions/decisions disappear and totals describe the capped sample, not the full filtered
history. This is a correctness problem as well as inefficient read architecture.

**Task:** Sprint 03/04: query/filter/order before page selection using a unified read model or stable multi-source cursor;
define historical retention explicitly instead of silently capping. **Acceptance:** records beyond 500/100 remain reachable,
search/status/count/order are correct across sources, and first-page work/payload remains bounded.

<a id="a6-06"></a>
## A6-06 — Medium — Dashboard/analytics performs repeated daily and role queries

**Evidence:** `services/analytics_service.py:118-132` issues a COUNT per day up to 90. Executive dashboard
`dashboard_service_parts/get_executive_dashboard_stats.py:57-85` issues user/report counts per day, then obtains overview
activities. Overview `get_dashboard_overview_stats.py:43-48,57-65` also repeats interval counts and two properties.exists
calls per recent user.

**Task:** Sprint 04: grouped date/interval aggregates with Cairo-aware boundaries and precomputed role facts; reuse a bounded
activity selector instead of recomputing a complete dashboard. **Acceptance:** query count independent of date-window days,
correct empty days/DST boundaries/role totals, no private-row disclosure through aggregation.

<a id="a6-07"></a>
## A6-07 — Medium — Campaign history expands into per-campaign aggregate queries

**Evidence:** `services/system_service_parts/get_system_health.py:46-49` projects up to 100 campaigns individually;
`services/push_campaigns.py` payload calculates recipient/delivery state aggregates repeatedly per campaign.

**Task:** Sprint 04: grouped/annotated campaign summaries and bounded history. **Acceptance:** page query budget remains
bounded as campaign count grows, while delivery/retry/suppression totals preserve current semantics.

<a id="a6-08"></a>
## A6-08 — Medium — Campaign cap is applied before audience eligibility

**Evidence:** `services/workspace_campaigns.py:163-173` limits the broad opted-in candidate set to 5,001 before final
audience eligibility, consent and device work; exceeding the cap rejects the preview. Per-user eligibility/device queries
also run while the preview transaction is open.

**Impact:** once the broad candidate population exceeds 5,000, an otherwise small intended audience can be rejected;
preview cost and lock duration grow with the broad population.

**Task:** Sprint 03/04: express audience constraints before the approved cap, distinguish scan budget from actual recipient
limit, batch current eligibility and keep a versioned preview proof. **Acceptance:** large overall population/small eligible
audience works; genuinely oversized audiences remain bounded; role/consent/device changes invalidate or recheck delivery.

<a id="a6-09"></a>
## A6-09 — Medium — Content catalog projections lack their relation fetch plan

**Evidence:** `views/content.py:99` projects a page of catalog rows without a relation-specific select/prefetch plan;
`services/content_registry.py` projections access city/district/campus/plan/benefit relations.

**Task:** Sprint 04/10: declare a selector/fetch plan per registered content type instead of adding hidden queries to the
generic projection. **Acceptance:** 1/25-row pages for each relational catalog have bounded queries, correct labels and
unchanged editing/revision authority.

<a id="a6-10"></a>
## A6-10 — High maintenance priority — Unsupported framework pin and unmeasured dependency security

**Evidence:** `Pipfile` and lock pin Django 4.2.11; the selected runtime reports that version. Official Django support for
4.2 ended April 7, 2026. The final 4.2.30 release includes multipart and ASGI request-body security fixes.
[Official support table](https://www.djangoproject.com/download/) and
[security release](https://www.djangoproject.com/weblog/2026/apr/07/security-releases/), checked 2026-11-08.

**Task:** Sprint 01: select a supported dependency-compatible Django target, audit the complete production lock set, and
coordinate Python/DRF/Channels/auth/storage compatibility. **Acceptance:** supported locked runtime, clean agreed security
audit or documented reviewed exceptions, full invalid-upload/auth/admin/ASGI regression and staging acceptance. The missing
pip-audit tool was not silently installed, and this review does not invent a complete CVE count or deployed exploit proof.

<a id="a6-11"></a>
## A6-11 — Quality backlog — Broad unused-import suppression hides substantial cleanup candidates

**Evidence:** `.flake8` has `ignore=F401,W503`. Selected configured lint reports 8 diagnostics; isolated selected lint reports
2,476 F401 plus 5 unused variables and 3 redefinitions. Many F401s are intentional public facades or import/registration
side effects, so the warning total is not the count of safely deletable statements.

**Task:** Sprint 11: classify exports/registrations, use explicit supported public exports, remove proven unused plumbing
and narrow exceptions. **Acceptance:** no blanket F401 ignore; no accidental loss of models, tasks, signals, test monkeypatch
seams or migrations; selected lint/type/import checks pass for migrated scopes.

<a id="a6-12"></a>
## A6-12 — Documentation/architecture — Repository instructions conflict with the agreed target

**Evidence:** backend `CLAUDE.md` contains function-only views, `apps/`, `Project.settings` and obsolete environment paths,
while current code uses `core_apps/`, split `config/settings` and mixed views. The user's explicit instruction now requires CBVs.

**Task:** Sprint 00/10: align repository guidance and examples with the approved architecture and real commands.
**Acceptance:** one consistent route/service/validation/transaction policy; new work cannot accidentally reintroduce the
retired function-only convention.

## Existing controls and non-findings

Staff permissions re-read current account/profile authority, including disabled profiles and sensitive-action factors.
Cookie/JWT session revocation and socket guarded receive/send exist. Private media uses authorized resource gateways.
Support roles intentionally have broad ticket-service access; assigned financial reviewers are restricted separately, so
the general support adapter was not labeled a bypass. `settings_service.get_platform_settings()` deliberately returns an
empty compatibility result and refuses inert switches; it is not proof of a broken configurable rules engine. Runtime
workers, Redis, backups, real storage and deployment configuration still require operational acceptance.

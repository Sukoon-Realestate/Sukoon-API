# Planning features deployment — 2026-10-13

The mobile implementation lives in `/Users/aait/Desktop/StudioProjects/darak-app`; the API implementation lives in this repository's `backend/`. The `mobile/` copy in this repository was not synchronized. Deploy the API changes and distribute the updated app from the correct checkout.

Local database, contract, HTTP and widget tests do not establish live provider readiness. No server deployment, real payment, live signature, user outreach or paid Google request was performed for this change.

## Runtime configuration

All twelve implemented planning services are selected by default in normal settings. Deploy this source and restart **API, worker and beat** to apply the change. No `PLANNING_ENABLED_SERVICES` environment variable is required. Account verification, resource permissions and provider readiness still apply.

Optional overrides and provider configuration belong in the environment of **API, worker and beat**, before Django settings are imported. Keep keys server-side. Do not put keys in Dart defines, application logs, committed files or notification payloads.

```dotenv
# Optional: omitted or blank has the same effect as all.
PLANNING_ENABLED_SERVICES=all
PLANNING_ROUTES_API_KEY=<restricted-server-Google-Routes-key>
PLANNING_GEMINI_API_KEY=<server-Gemini-key>
PLANNING_GEMINI_MODEL=<supported-structured-output-model-id>
PLANNING_ROUTE_MODES=driving,walking,transit
PLANNING_PROVIDER_TIMEOUT_SECONDS=20
PLANNING_ROUTE_MAX_ORIGINS=1000
PLANNING_PROVIDER_REQUESTS_PER_MINUTE=10
PLANNING_REQUEST_TTL_DAYS=30
PLANNING_MAX_LIVE_REQUESTS=3
PLANNING_OWNER_OFFERS_PER_REQUEST_PER_DAY=5
PLANNING_LEASE_REMINDER_DAYS=30
```

`PLANNING_ENABLED_SERVICES` accepts:

| Value | Behavior |
|---|---|
| Unset, blank, whitespace or `all` | Select all twelve supported services. |
| Comma-separated service names | Select only the listed services; surrounding whitespace and duplicates are ignored. |
| `none` | Explicitly disable all planning services. |
| Unknown names or a mixed `all`/`none` list | Stop startup with a configuration error, instead of silently disabling features. |

**Blank no longer means disabled.** Use `none` for a deliberate shutdown. API permissions and settings use one shared service registry. Normal production and staging imports are covered by regression tests independently of the enabled test settings.

Ten services work without Google credentials: lifestyle, roommates, housing groups, group visits/applications, housing requests/offers, condition reports, move-out notices and replacements. Commute becomes available when `PLANNING_ROUTES_API_KEY` is configured; the assistant requires both `PLANNING_GEMINI_API_KEY` and `PLANNING_GEMINI_MODEL`. Missing or whitespace-only provider configuration removes only the corresponding `verified_services` entry. Capabilities return a localized setup message for that service, and other services remain usable.

`PLANNING_MOCK_DISCOVERY=False` in normal settings; test discovery additionally requires the explicitly permitted test rental provider. Never enable test settings, fake rental providers or QA endpoints in production.

Flutter planning flags now default to true so the fresh account-scoped API grant controls rollout. Explicit `--dart-define=SOKOUN_<FEATURE>=false` remains a build kill switch. Flags grant no permissions. Keep production account verification and the existing signing/payment readiness checks enabled.

The companion app's `RentalCapability` flags also default to true. Previously an ordinary build omitted these defines and refused every rental mutation locally before requesting server capabilities. An explicit false still disables that client capability. The app now preserves `blocking_reasons` from planning and rental capability responses; an unverified account, denied record action or invalid request is no longer mislabeled as a missing rental service. Rebuild the app for this correction. Deliberate server shutdowns using `PLANNING_ENABLED_SERVICES=none` report an environment-disabled reason.

Enable the Routes API, billing, server key restrictions and quota alerts in the Google project. Arrival-time searches use transit only; route matrix batches contain at most 100 origins per destination. The adapter requests status, indices, condition, duration and fallback information; fallback/missing routes never satisfy a time limit. These limits follow the [Google Routes matrix reference](https://developers.google.com/maps/documentation/routes/reference/rest/v2/TopLevel/computeRouteMatrix).

Configure a Gemini model supporting structured JSON output. The API validates the returned schema, catalog IDs and allowed filters again; generated text cannot execute an action or determine inventory/prices. See [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output). Assess the provider's account-specific retention and regional terms before accepting real user prompts.

The adapter uses `v1beta/models/{model}:generateContent` with `generationConfig.responseSchema`; schema types use the REST uppercase enum values (`OBJECT`, `STRING`, `ARRAY`, `BOOLEAN`). This request shape was checked against the [public Gemini REST discovery schema](https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta). That schema check is not a live model invocation.

## Migrations and processes

Use the existing release migration job before restarting workers:

```sh
python manage.py check --deploy --fail-level ERROR
python manage.py migrate --noinput
python manage.py migrate --check
```

The dependency chain includes:

- `features/0013_planning_completion`: profile extensions, joins, process snapshots, durable jobs/events.
- `properties/0021_planning_report_integrity` and `features/0014_planning_report_integrity`: additive report and visit-provenance fields. These include concurrent visit-decision work; keep the dependency chain together.
- `features/0015_post_visit_invitation_compatibility`: preserves historical invitation permissions.
- `features/0016_planning_snapshot_backfill`: captures the exact historical report baseline when available, labels missing history without inventing it, and preserves unknown deposits.
- `features/0017_renewal_effective_dates`: restores missing renewal activation dates from the reviewed `terms.starts_on`; invalid or unavailable historical dates remain unchanged for review.

Use the existing PostgreSQL and shared Redis configuration. LocMemCache is suitable only for isolated tests: provider rate limits and same-key assistant claims require a shared cache across production processes.

The repository's existing process commands remain:

```sh
celery -A config worker --loglevel=INFO --concurrency=2 --hostname=worker@%h
celery -A config beat --loglevel=INFO --scheduler=config.runtime.LeaseScheduler --max-interval=15 --pidfile=/tmp/sokoun-beat.pid
```

The new `process-planning-jobs` beat entry runs every 30 seconds. It drains queued commute jobs, records lease reminders, retries notifications, and marks interrupted jobs failed after five minutes without progress. Commute jobs also dispatch after commit. An unavailable broker cannot erase the persisted queued search; beat is its recovery path.

Keep the existing rental change, closure, billing, source-expiry, provider reconciliation and evidence scanning schedules. They own signatures, money, private evidence, expiry and replacement reconciliation. API changes alone are insufficient without workers and beat.

Notifications use a durable event and a single in-app record. Push retries may be delivered more than once after a crash; event IDs support client deduplication. Recipients and private-resource access are checked again at delivery and on opening. Do not claim exactly-once external push delivery.

## Product boundaries

- A group application stops at owner `approved_to_proceed`. It creates no individual RentalInterest, invitation or lease for the coordinator. `joint_leases=false`; group chat also remains unsupported.
- Housing offer selection is intent to continue; it reserves no accommodation.
- Condition report approval changes no possession, deposit, payment, liability or settlement.
- A notice acknowledges a requested departure date. Legal ending, possession return, incoming agreement and financial closure remain distinct.
- A replacement candidate receives a limited consent inbox, never the outgoing tenant's private report, balance or case history.
- Renewal and departure/replacement compete under the same lease lock. Applied renewals retain the existing single-tenant tenancy root and zero acquisition-commission policy.
- Existing live onboarding, e-signature, payment and private-storage providers are still required for their respective rental stages. This change does not configure provider accounts.

## Housing demand and group follow-up — 2026-10-14

Deploy/restart the API with the updated `planning_housing_views_parts/housing_requests.py`. No database migration is required for this follow-up. The mobile city-label fix is in the separate `darak-app` checkout and requires an updated app build.

`GET /api/v1/features/v1/housing-demand/` now returns published, unexpired requests from all cities to eligible owners, excluding the owner's own requests. Previously it silently restricted discovery to cities of the owner's verified listings. `?city=<UUID>` applies an explicit city filter. Detail permissions follow the same discovery rule. Sending an offer still requires verified inventory in the requested city and revalidates the exact selected unit against the request criteria.

The existing group fixes remain covered: `housing-groups/?status=active|archived`, administrator-only `unarchive`, invitation history, atomic leave with `member_id` for the successor, and `group_join_requests_count` in tenant unread counts. The common `planning-capabilities` URL authorizes access; it does not select a collection tab.

Local verification: four new demand-discovery tests, the existing complete housing request/offer/recovery cycle, and five group-management tests passed on isolated SQLite test databases. These checks cover other-account visibility across cities, city filtering/pagination, unpublished/expired/private/own-request exclusions, owner eligibility, offer permissions, group restore, succession, invitation history and counts. They do not verify the deployed service.

After deployment, publish a request from a designated tenant account in a different city from the test owner's listings. Confirm it appears in the owner's feed and detail, while no `offer` action is advertised without matching inventory. Verify the explicit city filter and a matching-city offer through the app.

## Post-deployment acceptance

Use designated test accounts and test-owned inventory:

1. With a verified test account, verify `GET /api/v1/features/v1/planning-capabilities/?capability=lifestyle&action=read` reports all twelve `enabled_capabilities`, at least the ten non-Google `verified_services`, and `read` in `allowed_actions`. Repeat for commute and assistant after configuring their respective providers. A deliberate service subset changes the expected list.
2. Submit one and two destination searches; observe queued/running/succeeded, independent times and hard limits. Verify cancellation, unavailable route, expired search and quota error.
3. Ask a Gemini question with reviewed filters and an exact offer; verify catalog-grounded IDs/prices, unknown costs, editable questions, refinement and same-key retry.
4. Exercise two-account consent, group capacity conflict, owner application review, report revision/addendum and competing renewal/departure.
5. Verify beat/worker runtime evidence for `process-planning-jobs`, notification delivery, reminder deduplication, evidence scanning and existing rental schedules.
6. On Android and iOS devices verify foreground/background polling, incoming links, workspace/login changes, voice permissions, private media and actual provider return paths.

Rollback by supplying the subset of services to retain in `PLANNING_ENABLED_SERVICES`, or use `PLANNING_ENABLED_SERVICES=none` to disable all planning, then restart API/worker/beat. An empty value enables the defaults. Keep additive data and operation receipts. Do not reverse migrations or discard pending financial/rental operations as a feature rollback.

## Local enablement verification — 2026-10-13

The enablement correction passed **154 distinct backend tests**: 104 planning/configuration tests on isolated PostgreSQL, plus 50 related capability, rental and runtime regressions on SQLite. The 56 new configuration tests import normal settings in fresh processes and exercise their resulting permissions through actual API views. They cover missing/blank/all/subset/none settings, invalid names, independent provider prerequisites, Arabic/English setup messages, private collection reads, profile save/replay/stale revision, and guest/unverified/inactive rejection. The existing planning suites cover provider adapters, consent, group/application cycles, report history, competing lease transitions and durable jobs.

Django system checks and migration consistency passed; this correction adds no migration. Provider HTTP remains mocked in local cycle tests. These results do not certify Google credentials, deployed worker/beat execution or enabled native app cycles. Earlier live Android evidence showed the old deployment disabled all planning; redeploy this source before repeating those checks.

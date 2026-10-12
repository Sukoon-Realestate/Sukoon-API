# Planning features deployment — 2026-10-13

The mobile implementation lives in `/Users/aait/Desktop/StudioProjects/darak-app`; the API implementation lives in this repository's `backend/`. The `mobile/` copy in this repository was not synchronized. Deploy the API changes and distribute the updated app from the correct checkout.

Local database, contract, HTTP and widget tests do not establish live provider readiness. No server deployment, real payment, live signature, user outreach or paid Google request was performed for this change.

## Runtime configuration

Set these values in the environment of **API, worker and beat**, before Django settings are imported. Keep keys server-side. Do not put keys in Dart defines, application logs, committed files or notification payloads.

```dotenv
PLANNING_ENABLED_SERVICES=lifestyle,roommates,housing_groups,group_visits,group_applications,housing_requests,housing_offers,condition_reports,move_out_notices,replacements,commute,tenant_assistant
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

`PLANNING_ENABLED_SERVICES` is empty by default. Missing Google credentials remove only the corresponding discovery capability. Other services remain independently configurable. `PLANNING_MOCK_DISCOVERY=False` in normal settings; test discovery additionally requires the explicitly permitted test rental provider. Never enable test settings, fake rental providers or QA endpoints in production.

Flutter planning flags now default to true so the fresh account-scoped API grant controls rollout. Explicit `--dart-define=SOKOUN_<FEATURE>=false` remains a build kill switch. Flags grant no permissions. Keep production account verification and the existing signing/payment readiness checks enabled.

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

## Post-deployment acceptance

Use designated test accounts and test-owned inventory:

1. Verify `GET /api/v1/features/v1/planning-capabilities/?capability=commute` reports the current account, enabled/verified services, expiry and configured modes; repeat for assistant and a non-provider feature.
2. Submit one and two destination searches; observe queued/running/succeeded, independent times and hard limits. Verify cancellation, unavailable route, expired search and quota error.
3. Ask a Gemini question with reviewed filters and an exact offer; verify catalog-grounded IDs/prices, unknown costs, editable questions, refinement and same-key retry.
4. Exercise two-account consent, group capacity conflict, owner application review, report revision/addendum and competing renewal/departure.
5. Verify beat/worker runtime evidence for `process-planning-jobs`, notification delivery, reminder deduplication, evidence scanning and existing rental schedules.
6. On Android and iOS devices verify foreground/background polling, incoming links, workspace/login changes, voice permissions, private media and actual provider return paths.

Rollback by disabling individual services in `PLANNING_ENABLED_SERVICES` and restarting API/worker/beat. Keep additive data and operation receipts. Do not reverse migrations or discard pending financial/rental operations as a feature rollback.

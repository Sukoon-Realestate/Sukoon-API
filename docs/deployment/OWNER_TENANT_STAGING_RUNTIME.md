# Owner–tenant simulated-provider deployment and runtime evidence

This setup updates the existing DigitalOcean app serving
`https://sukoon-app-y4j5r.ondigitalocean.app`. It does not create an app, database,
cache, domain or QA account. The user selected simulated providers and will push
the reviewed backend changes to GitHub `main`. This implementation performs local
fixes and tests only. The deployment and postdeployment commands below are for
the release operator; a successful local test is not deployed evidence.

## Required existing resources and private inputs

- The intended App Platform app, connected to `Sukoon-Realestate/Sukoon-API`.
- Its existing PostgreSQL database and a reachable Redis/Valkey service. The
  patch preserves the existing database/domain/network specification. Redis
  must support Celery, Channels and Lua scripts for the scheduler lease.
- `SECRET_KEY`, `RENTAL_PROVIDER_WEBHOOK_SECRET`, `REDIS_URL`, `POSTGRES_DB`,
  `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, and
  explicit `ALLOWED_HOSTS` in runtime scope. Reuse encrypted values or DigitalOcean
  bindable references already present in the app. No placeholder secrets are supplied.
- Existing provider/storage/Google/Firebase configuration remains in place.
  Mock rental providers do not replace image storage, Google login or push delivery.
- A private DigitalOcean API token with the permissions needed to read/update
  this app. Store it in an owner-only file outside Git; never paste it into shell
  arguments or a report. The tooling refuses group/world-readable input files.

`REDIS_URL` is also the default Celery broker/result backend when explicit values
are absent. For `rediss://`, Celery verifies certificates. Retain the existing
trusted connection/certificate configuration; do not disable certificate checking.
PostgreSQL uses `sslmode=require` on the remote deployment.

## Review the actual app before applying

Run from the repository root with Python 3.11+:

```sh
backend/.venv/bin/python backend/scripts/digitalocean_runtime.py \
  --token-file /private/path/digitalocean-token
```

This command makes read-only DigitalOcean requests and prints the redacted diff,
blocking prerequisites and a `plan_hash`. It finds the app by the exact existing
domain. If needed, select the known app UUID with `--app-id` and its Django service
with `--api-component`. Existing unrelated components, domains, databases,
encrypted environment values, API sizing and routes remain intact.

Missing secrets can be supplied via `--private-env-file /private/path/runtime-env.json`.
That owner-only file contains a JSON object of approved environment keys and real
values. It is read only in memory; neither it nor the full candidate spec is saved.
The allowlist is in `SECRET_INPUT_KEYS` in the script. Populate the existing
database/Redis credentials; the script does not provision cloud resources.

New worker and migration-job sizes default to the existing API instance size.
Select the approved size explicitly with `--worker-size` if needed. The diff shows
the two added worker components and deployment job, which affect App Platform
usage. Existing additional scheduler commands block application until reconciled.

After reviewing the concrete plan and passing source checks, apply that exact plan:

```sh
backend/.venv/bin/python backend/scripts/digitalocean_runtime.py \
  --token-file /private/path/digitalocean-token \
  --apply --expect-plan-hash <reviewed-plan-hash>
```

Use the same component, size and private-env arguments as the plan. The script
fetches the latest app specification again and refuses an outdated plan hash.
It submits one update to the existing app; it does not push Git commits or retry
an uncertain update. After a network error, read status/current plan before retrying.

An exported current JSON spec can be reviewed offline with `--spec-file` instead
of a token. It must also be private. Offline input cannot be applied.

## Resulting processes

All four components use `source_dir=backend`, the same repository and `main`.
API and workers expose their actual component `${_self.COMMIT_HASH}` as
`SOKOUN_RELEASE_SHA`; compare the migration job's source through the deployment API.

| Process | Behavior |
|---|---|
| Existing API service | Gunicorn/ASGI on `${PORT:-8080}`; `/health/` probes PostgreSQL and Redis without exposing connection details |
| `sukoon-worker` | Celery worker, concurrency 2, one instance |
| `sukoon-beat` | Celery beat, one instance; a Redis lease also prevents overlapping rollout instances from publishing concurrently |
| `sukoon-migrate` | `PRE_DEPLOY` job: Django deployment checks, forward migrations, migration completeness check |

Each runtime uses `config.settings.staging_mock`, `DEBUG=False`, Redis Channels,
and the same business secrets/database. This explicitly enables API-only rental
provider simulations and planning services; it does not enable fake providers in
production settings. Static assets are collected at build time with
`config.settings.build`, which needs no database, broker or runtime secret.

Keep migrations forward compatible with an older process during rolling deploys.
Before a release requiring destructive schema changes, use a separate reviewed
migration sequence. Roll back application code only to a version compatible with
the applied schema; retain financial records and idempotency receipts.

## Verify deployment and real scheduled execution

Inspect safe deployment metadata:

```sh
backend/.venv/bin/python backend/scripts/digitalocean_runtime.py \
  --token-file /private/path/digitalocean-token --status
```

Wait for an active deployment with the intended SHA for the API, worker, beat and
migration job, and no failed/in-progress deployment. Confirm `GET /health/` returns
200. Record the completed deployment's UTC time as the verification boundary.

From the **API component console**, after at least one five-minute schedule interval:

```sh
python manage.py runtime_readiness \
  --expected-sha <deployed-40-character-commit-sha> \
  --since <deployment-completed-UTC-ISO-timestamp>
```

The equivalent Make target is `make runtime-readiness CYCLE_PYTHON=python
RUNTIME_SHA=<sha> RUNTIME_SINCE=<timestamp>`. A nonzero exit means incomplete
readiness. The command only reads; it never invokes financial tasks or fabricates
a successful scheduler record.

The sanitized JSON must show:

- Correct API release/settings, PostgreSQL, no pending migrations, Redis, and
  actual worker execution enabled (no eager Celery test mode).
- A recent scheduler heartbeat whose owner still holds the Redis lease.
- A successful real worker completion for **each configured scheduled task**,
  dispatched after the requested boundary, with matching worker/scheduler SHA.
  Worker, scheduler and API settings/provider mode and database fingerprints must
  also agree; matching code pointed at a different database cannot pass.
  Missing, failed, retrying, stale or older-release evidence fails the check.

Required jobs currently cover advertisement expiry, invitation/hold expiry,
provider-session expiry, recurring invoice issuance/overdue updates, ambiguous
payment reconciliation, evidence scanning, approved payouts, rental changes, and
legal/financial closure. Most run every 300 seconds; evidence scanning runs every
60 seconds. The report follows the configured schedule rather than a second list.

Execution records retain UTC epoch times, task/scheduler IDs, worker identity,
release hashes, state and integer result counts for one hour. They exclude task
arguments, credentials, documents, provider URLs and exception text. Direct `.run()`
calls, eager tests and manual task publications do not count as beat evidence.
An observability write failure does not retry a completed financial operation.

**A successful task with zero affected rows proves execution, not a business
transition.** Use dedicated run-owned due fixtures to verify expiry, billing,
reconciliation and closure effects through fresh owner/tenant reads. Keep the
fixture IDs and before/after state in the cycle runner's private journal, then
export only sanitized assertions. Do not backdate shared real leases or reset
existing financial records to manufacture evidence.

## Local verification

```sh
cd backend
make test-runtime CYCLE_SETTINGS=config.settings.test
.venv/bin/python manage.py check --settings=config.settings.test
.venv/bin/python manage.py collectstatic --dry-run --noinput \
  --settings=config.settings.build --verbosity=0
```

The runtime/spec tests cover secret redaction, unchanged database/domain/route
configuration, repeatable spec updates, explicit missing prerequisites, private
file permissions, stale-plan protection, lease loss, direct/eager execution
rejection, wrong/stale release evidence, and dependency health failure handling.
They do not claim that DigitalOcean is configured or that a deployed task ran.

Official schema references: [App Specification](https://docs.digitalocean.com/products/app-platform/reference/app-spec/),
[workers](https://docs.digitalocean.com/products/app-platform/how-to/manage-workers/),
[bindable variables and encrypted environment values](https://docs.digitalocean.com/products/app-platform/how-to/use-environment-variables/).

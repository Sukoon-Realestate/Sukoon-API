# Local runtime verification — 2026-10-13 Cairo

This evidence covers local runtime preparation. **No DigitalOcean app was read or
changed, and no commit was pushed.** The user owns the push/deployment step.

| Check | Result | Evidence |
|---|---|---|
| Focused runtime/spec tests | 30 passed, 0 failed, 0 skipped | `make test-runtime CYCLE_SETTINGS=config.settings.test`; [focused-tests.txt](focused-tests.txt) |
| Django system/migration checks | Passed; no model changes detected | `manage.py check` and `makemigrations --check --dry-run` under test settings |
| Static build without runtime services | Passed dry run | `collectstatic --dry-run --noinput --settings=config.settings.build` |
| Real PostgreSQL, Redis, Celery worker and beat | All nine normal scheduled jobs completed successfully | [local-runtime.json](local-runtime.json) |
| API dependency health | HTTP 200, `ready=true` | [local-runtime.json](local-runtime.json) |
| Actual due-row expiry | Due advertisement/onboarding expired; future controls unchanged | [due-fixtures.json](due-fixtures.json) |
| Single scheduler lease | 50 rounds with two competing schedulers produced exactly one owner; old owner could not delete its replacement's lease | [scheduler-lease.json](scheduler-lease.json) |

The worker and beat were separate actual Celery processes using a temporary Redis
7.4.2 instance, a unique disposable PostgreSQL database, and
`config.settings.staging_mock`. Schedules retained their normal 60/300-second
intervals. The local API health check was served over HTTP by a separate Django
process. The readiness report required a successful task dispatched after the
run began, matching API/worker/beat configuration and database fingerprints, and
matching synthetic local release identifiers. `f` repeated 40 times is explicitly
a local protocol fixture, **not a deployed Git commit**.

The due/future fixtures were inserted directly into that disposable database to
make time-based checks deterministic. Neither the setup nor the observation
called the expiry task directly; the scheduled worker performed the changes.
Other jobs with zero affected rows prove scheduler/broker/worker execution.
Their business behavior is covered separately by the owner–tenant cycle tests.

All local runtime processes were stopped and the disposable database was removed.
Existing test databases, remote records, cloud resources and credentials were
untouched. The temporary harness/build logs remain under
`/tmp/sokoun-runtime-redis-20261013/` for this local session; no credential values
were persisted there.

For the reviewed runtime patch, exact release commands and postdeployment
acceptance, use [the deployment guide](../../deployment/OWNER_TENANT_STAGING_RUNTIME.md).
Pushing source alone does not add cloud worker components, configure Redis, or
change DigitalOcean environment variables. Those runtime prerequisites and the
same scheduled proof must be verified after deployment.

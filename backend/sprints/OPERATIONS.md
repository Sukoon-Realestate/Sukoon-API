# Runtime and recovery boundaries

Sprint 10 operational instructions, verified against source on 2026-11-14. No deployment, production read/write,
remote storage mutation or backup restoration was performed for this sprint. Sprint 12 owns controlled environment
acceptance; a local `check --deploy` result is not proof of TLS, Redis, workers, storage or recovery.

## Paths and isolated source checks

Run from `Sukoon-API/backend/`. `Pipfile`/`Pipfile.lock` are here; settings are `config/settings/` and apps are
`core_apps/`. Use `pipenv sync --dev` for the locked environment or the existing hash-checked `.venv/bin/python`.
There is no `Venv/` or `Project.settings`. `make` supports `CYCLE_PYTHON`, `CYCLE_SETTINGS` and `BASELINE_OUT`.

```sh
DOTENV_DISABLED=1 make sprint10-coverage
PYTHONPATH=<scratch-settings-directory>:. DOTENV_DISABLED=1 \
  make test-sprint10-admin-shared CYCLE_SETTINGS=<scratch-module> BASELINE_OUT=<scratch-root>
DOTENV_DISABLED=1 .venv/bin/python manage.py check --settings=config.settings.test
```

The scratch module must explicitly replace the default database and every media/static/private-storage root. Ordinary
`config.settings.test` pytest uses an in-memory SQLite test database, but **management commands** using that module can
open repository `db.sqlite3`. Do not use it for migrations, seeds or recovery commands against existing files. PostgreSQL
checks require new disposable `TEST_POSTGRES_*` or equivalent scratch settings, with unique test database names for
concurrent processes. The schema-heavy full suites need sufficient scratch lock capacity (the Sprint 10 cluster uses
`max_locks_per_transaction=1024`). Do not change production capacity to match synthetic tests.

`config.settings.base` loads the repository `.env` unless `DOTENV_DISABLED=1`; production also conditionally loads
`.envs/.env.local`. Tests must not read/edit those files. Pass scratch environment explicitly. The source release entry
point is `scripts/run_api.py`; it runs `manage.py migrate_release` before starting ASGI, so **never run it against an
existing database just for validation**. Build-only static collection uses `config.settings.build`.

## Dependency and release gates

- `config.celery` defaults to local settings unless `DJANGO_SETTINGS_MODULE` is explicit. The broker and result backend
  default to `REDIS_URL`; configured `rediss://` uses certificate verification. Production cache uses Redis, Channels
  uses its configured layer, and the leased scheduler requires Redis/Lua. In-memory/eager tests are not deployed proof.
- `config.background` controls admitted general-worker tasks/queues. `SOKOUN_GENERAL_BACKGROUND_ENABLED` selects the
  combined `manage.py run_general_worker` path (solo worker and leased scheduler); otherwise `run_api.py` starts policy
  maintenance. Do not add a second beat publisher alongside that process. `run_general_worker` refuses disabled mode.
  Separate staging worker/beat/migration components are described in
  [the deployment runbook](../../docs/deployment/OWNER_TENANT_STAGING_RUNTIME.md); inspect the actual deployment profile
  before choosing its process topology. Neither topology was launched against production here.
- In the selected controlled environment, compare the API, worker, scheduler and migration-job source SHA and settings/
  database identity. `SOKOUN_RELEASE_SHA` must be the actual source version, not an invented value. The read-only command
  `manage.py runtime_readiness --expected-sha <actual-sha> --since <UTC-ISO-time> --profile <staging_mock|general|probe>`
  checks dependency/schema and actual scheduled completion evidence. The `probe` profile certifies only isolated transport.
  `make runtime-readiness RUNTIME_SHA=<sha> RUNTIME_SINCE=<time>` uses the default staging profile.
- Require fresh scheduled completions, not only a worker heartbeat, eager call, manual `.run()` or a 200 health response.
  Zero affected rows proves execution only. Real transition evidence needs owned synthetic fixtures, fresh reads and cleanup.
- Storage/scanner/provider/voice/signing gates remain separate. Check `CHAT_PRIVATE_STORAGE_PROVIDER`,
  `SUPPORT_PRIVATE_STORAGE_PROVIDER`, `EVIDENCE_STORAGE_PROVIDER` and `VIRTUAL_TOUR_PRIVATE_ROOT` plus each provider's
  actual configured mode and dependencies. Never serve private local directories directly. Do not substitute a fake
  provider or disabled scanner for production readiness.

## Backups and supported recovery commands

A database dump does not include Cloudinary/private media, process configuration, signing material or independent delivery
facts. The release operator must demonstrate encrypted durable copies, database/media consistency, digest verification,
restricted restore access, retention and approved RPO/RTO using a new isolated restore target. Retain original files until
fresh remote download verification succeeds. Do not restore over an existing database to obtain acceptance evidence.

Source-supported commands (documentation only here; confirm the selected environment before execution):

| Command | Effect / limit |
|---|---|
| `manage.py migrate_release` | Forward migration with PostgreSQL release lock; not a rollback tool. Never fake migration history to recover data. |
| `manage.py backfill_support_private_storage` | Reports references by default; `--apply --attachment-id <uuid>` copies/verifies durable originals and binds their digest. It retains originals and fails honestly on missing/mismatched bytes. |
| `manage.py backfill_private_chat_media [--watch-seconds <n>]` | **Writes remote storage** and verifies active originals; requires configured private chat provider. This command has no dry-run switch. |
| `manage.py reconcile_paymob_payments` | Financial inquiry/reconciliation, not read-only diagnostics; retain original payment/instruction identities and inspect `--help` for selection. Never retry an unknown send under a new key. |
| `manage.py rental_closure_status` | Use its documented arguments/`--help` to inspect the selected closure; it does not authorize physical deletion of retained history. |
| `scripts/run_local_recovery_drill.py --port <owned-local-port> --user <scratch-role> --pg-bin <installed-bin> --output <scratch-report>` | Creates its own synthetic UUID database and uses real local pg_dump/pg_restore on loopback. Requires its own suitable disposable TCP cluster; the Sprint 10 Unix-only cluster is deliberately not suitable. Local drill evidence is not a production RPO/RTO claim. |
| `manage.py recovery_journal_readiness` | Explicitly retired by product policy; returns an error and grants no independent recovery/reopening approval. Do not interpret this as a functioning disaster-recovery gate. |

Account, receipt, upload and provider reconciliation recovery remain their respective domain workflows. A deployment
rollback must remain compatible with forward-applied schema and retained receipts/audit/money records. Controlled
TLS, real Redis/worker/storage delivery and a production-like restore drill remain Sprint 12 acceptance work.

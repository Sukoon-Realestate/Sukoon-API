# Local release checks — 2026-11-12

This records local evidence, not final release or deployment approval. Existing databases and production were not used.

| Check | Evidence |
|---|---|
| Real worker and scheduler | Passed: queued jobs consumed; planning inbox delivered; interrupted job recovered once; scheduled probe executed |
| Two ASGI processes and Redis | Passed: lost-ack recovery returns the original message; changed replay conflicts; peer read receipts cross processes; outsiders denied; suspension closes sockets and old sessions stay revoked |
| Scoped controlled loopback load | 120 requests, concurrency 4, three warmups, one-message fixture: 108 expected 200s and 12 expected 403s; zero unexpected outcomes; p50 20.9 ms, p95 25.7 ms, about 164.7 requests/s, maximum response 478 bytes |
| Mobile identity contracts | 28 existing Flutter tests passed, including login, Google adapter, OTP/registration/reset, cookie sessions, recovery and identity expiry |
| Scratch PostgreSQL backup/restore | 366 table row counts matched in a separate restored database; does not prove production backups |
| Environment-file isolation | 12 subprocess cases verify explicit DOTENV_DISABLED support with the pinned dotenv package |
| Opt-in HTTPS acceptance settings | 11 subprocess cases verify host/origin validation, HTTPS redirects, secure cookies, HSTS and explicit proxy trust |

The owned Redis, ASGI, worker and scheduler processes were stopped by the QA helpers on completion; their cloned databases were dropped. Redis 8.8.4 was compiled only in scratch storage after checking its source archive against the official published hash. No global software installation, dependency update or provider transaction was performed.

## HTTPS test profile

`config.settings.staging_acceptance` is a new opt-in profile; existing production/staging defaults are preserved. It requires explicit ALLOWED_HOSTS and HTTPS COOKIE_TRUSTED_ORIGINS, an operator-selected STAGING_HSTS_SECONDS value after verifying that isolated host's HTTPS, and optional STAGING_TRUST_HTTPS_PROXY=true only when trusted ingress strips client forwarding headers. Auth/session/CSRF cookies are secure; HTTP redirects to HTTPS.

Django's deployment checks have two explicit policy warnings in this profile: security.W005 and security.W021, because HSTS does not include subdomains and preload is disabled. The tests require precisely those warnings and reject additional warnings/errors. This avoids asserting TLS control over other hosts or requesting preload enrollment. The original staging profile's W004/W008/W012/W016 findings are not represented as fixed on a deployed server; the new profile must be selected and verified there.

## Reproduction and external gates

Use freshly created disposable PostgreSQL settings/template and private storage roots. The template name must start with test_sokoun_. QA tools accept --postgres-host for a private Unix socket and --postgres-port/--postgres-user for that owned cluster. Do not point them at a shared or production service.

- `make test-sprint04-performance CYCLE_SETTINGS=<scratch_settings> BASELINE_OUT=<scratch_output>` runs the focused query/authority/migration gates.
- `make test-sprint12-local-contracts CYCLE_SETTINGS=<scratch_settings> BASELINE_OUT=<scratch_output>` checks environment isolation and the opt-in HTTPS profile offline.
- `python tools/qa/verify_cycle_workers.py --template <owned_template> --postgres-host <private_socket> --postgres-port <port> --postgres-user <test_role>` starts/stops its own Redis/worker/scheduler and drops only its cloned database.
- `python tools/qa/verify_chat_network.py --template <owned_template> --postgres-host <private_socket> --postgres-port <port> --postgres-user <test_role> --multi-worker --load-requests 120` exercises two owned ASGI processes, shared Redis and bounded HTTP load.

Still needed for real signoff: a separate HTTPS staging server with sandbox Google/Apple/email/storage/payment/signing configuration, test accounts and physical devices; native capture/media tests; storage persistence/failure recovery against the chosen real service; all-family representative load; actual ingress/TLS/cookie/origin observations; dependency/security and client compatibility review; controlled migration rollout, observation and recovery evidence. No credentials should be pasted into this report. Nothing in these scripts deploys the API or grants acceptance to untested providers/devices.

## Final read-schema recheck

After the saved-search read migrations, the real local worker/scheduler/interruption and two-process shared-Redis/ASGI checks passed again. A fresh final-schema backup/restore matched 367 table row counts. The saved-search format flag is part of the runtime configuration identity; activation/rollback must follow the [read-format rollout notes](../sprint-04/read-followup-2026-11-12.md). These checks remain local and do not grant external release acceptance.

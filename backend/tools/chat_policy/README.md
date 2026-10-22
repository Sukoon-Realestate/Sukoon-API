# Rental chat policy operations

Ship with CHAT_MODERATION_MODE=off, CHAT_MODERATION_PRIVATE_INPUTS_APPROVED=false and CAPTURE_COACH_PRIVATE_INPUTS_APPROVED=false. The currently inspected Gemini project uses Free Tier. Do not send private user data to it or activate billing as part of this deployment. Review the provider terms: https://ai.google.dev/gemini-api/terms .

The web Procfile starts scripts/run_api.py. This supervises Gunicorn and run_chat_policy_worker in the existing service. Off mode performs retention and existing notice/outbox maintenance only, with no Gemini calls. Verify the actual DigitalOcean run command and process after deploying; an override can bypass the Procfile.

Only apply the new chat 0012/0013 and virtual_tours 0003 migrations for this feature. Chat 0012 depends on admin_api schema 0005. Do not run the unrelated pending admin_api 0006 legacy identity reconciliation as part of this feature: it changes user verification. Inspect the migration plan before applying targets.

Use GET /api/v1/chat/admin/policy-status/ as an authorized reviewer for counters, provider configuration flags and failures. It exposes no message contents. A configured key is not proof of a healthy worker or an evaluated model.

The synthetic corpus contains 300 contextual variants from 45 semantic families: 180 legitimate, 80 explicit circumvention, 40 ambiguous. This is a seed corpus, not an independently human-reviewed held-out benchmark. evaluate_synthetic.py reads only the bundled corpus, reserves the existing daily quota, and journals each attempt atomically. Only a final grounded decision after the independent verifier counts as a completed case. Retries never inflate unique coverage; missing actor output and provider failures are unknown, not compliant. A disagreement between classifier and verifier yields review/uncertain, matching the server decision path. The sampled order interleaves categories and semantic families. Transient retries are bounded to 2 per case by default, stop after 3 consecutive failures, and are paced serially with at least 15 seconds between HTTP attempt starts (including extraction and verifier calls). No client auth/configuration errors are retried. Never replace it with private conversations under the synthetic override.

Rollout gates: verified provider data terms on an existing authorized account, model evaluation including image/voice, independent review of false positives, shadow measurement, warn mode, then separately approved enforcement. No automatic permanent ban. Temporary restrictions remain pending human review after the 48-hour escalation threshold. Reverting mode to off does not lift existing restrictions or erase appeal evidence.

Verify live worker health/resources and migration ledger, own-account endpoints, owner-only/case-only evidence access, and property visibility before reporting deployment ready. Retain the existing durable media configuration and existing tour viewer. Do not add subscriptions.

## Reproducible synthetic provider checks

Run from `backend/` using the existing isolated PostgreSQL `capture_dev` database:

```sh
PYTHONPATH=. DJANGO_SETTINGS_MODULE=config.settings.capture_dev .venv/bin/python tools/chat_policy/evaluate_synthetic.py --synthetic-provider-check --output /tmp/sokoun-text-evaluation-v2.json --limit 12 --max-requests 16
PYTHONPATH=. DJANGO_SETTINGS_MODULE=config.settings.capture_dev .venv/bin/python tools/chat_policy/evaluate_synthetic.py --synthetic-provider-check --media --output /tmp/sokoun-media-evaluation-v2.json --limit 8 --max-requests 24
```

The override refuses production/nonlocal databases. No production policy mode, private-input gate, billing configuration, account, message, or moderation case is changed. The per-run cap and daily reservation both apply, including retries and the second verifier. The production default remains100/day. A separately authorized synthetic run may pass `--evaluation-daily-limit 600 --max-requests 600` to raise only this isolated process's application guard; the parser caps this allowance at 600. This cannot raise or bypass the real provider quota. A complete 300-case run needs at least 380 calls including the 80 expected positive verifiers, before retries/media. Never switch billing, keys, projects or models to evade provider quotas. HTTP 429 quota metadata distinguishes a daily limit from a minute limit without retaining project IDs/provider bodies. Daily exhaustion stops immediately until the next documented Pacific-midnight reset; Retry-After/RetryInfo waits are honored. Requests delayed more than 60 seconds are checkpointed and stopped for a later explicit resume.

Reusing the same output resumes only unfinished cases. Changing corpus/model/rubric requires a new output. Legacy result arrays are deliberately not imported because they scored the first classification before verification. The v2 summary counts unique completed cases, observed non-violations, false positives and missed violations. A denominator of zero is reported as null. `accuracy` is agreement with this packaged synthetic expectation rubric, not production accuracy or independent human approval; `no_circumvention` permits compliant, off_topic or uncertain.

`--media` generates 8 fixed fixtures: shaped Arabic/English/Arabizi text cards and local computer speech (Arabic/English, reporting/refusal, one deterministic noise sample). The macOS renderer uses Swift/AppKit for Arabic shaping; speech uses installed `say` voices and ffmpeg PCM conversion. It accepts no external media/input path. The exact production extraction path and subsequent classifier/verifier run against these bytes. Normalized character/word errors and uncertainty are retained with the synthetic transcript. Clean cards and synthetic voices are baselines, not evidence of natural dialect, real microphone noise, every codec, or camera OCR performance. Independently reviewed samples remain a separate acceptance gate.

The provider omits custom sampling parameters. Current official documentation says Gemini 3.6+ ignores and deprecates these; removal avoids a future invalid-parameter error but does not establish that all 503/timeouts were caused by them. The durable moderation queue already owns bounded exponential retry; the HTTP client performs a single budgeted attempt so failures cannot multiply hidden retries.

References: [Google troubleshooting](https://ai.google.dev/gemini-api/docs/troubleshooting), [thinking model defaults](https://ai.google.dev/gemini-api/docs/thinking/).

Transport events contain only HTTP status/error code and elapsed milliseconds, measured around the actual request. A private gate or local-budget rejection produces no transport event. Reports distinguish recorded transport attempts from case durations (which include rendering, pacing, and verification). Earlier attempts without this instrumentation remain without transport measurements; they are never reconstructed from total case times.

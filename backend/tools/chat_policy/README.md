# Rental chat policy operations

Ship with CHAT_MODERATION_MODE=off, CHAT_MODERATION_PRIVATE_INPUTS_APPROVED=false and CAPTURE_COACH_PRIVATE_INPUTS_APPROVED=false. The currently inspected Gemini project uses Free Tier. Do not send private user data to it or activate billing as part of this deployment. Review the provider terms: https://ai.google.dev/gemini-api/terms .

The web Procfile starts scripts/run_api.py. This supervises Gunicorn and run_chat_policy_worker in the existing service. Off mode performs retention and existing notice/outbox maintenance only, with no Gemini calls. Verify the actual DigitalOcean run command and process after deploying; an override can bypass the Procfile.

Only apply the new chat 0012/0013 and virtual_tours 0003 migrations for this feature. Chat 0012 depends on admin_api schema 0005. Do not run the unrelated pending admin_api 0006 legacy identity reconciliation as part of this feature: it changes user verification. Inspect the migration plan before applying targets.

Use GET /api/v1/chat/admin/policy-status/ as an authorized reviewer for counters, provider configuration flags and failures. It exposes no message contents. A configured key is not proof of a healthy worker or an evaluated model.

The synthetic corpus contains 300 contextual variants from 45 semantic families: 180 legitimate, 80 explicit circumvention, 40 ambiguous. This is a seed corpus, not an independently human-reviewed held-out benchmark. evaluate_synthetic.py reads only the bundled corpus, preserves completed case IDs, reserves the existing daily quota, and stops on provider errors. Never replace it with private conversations under the synthetic override.

Rollout gates: verified provider data terms on an existing authorized account, model evaluation including image/voice, independent review of false positives, shadow measurement, warn mode, then separately approved enforcement. No automatic permanent ban. Temporary restrictions remain pending human review after the 48-hour escalation threshold. Reverting mode to off does not lift existing restrictions or erase appeal evidence.

Verify live worker health/resources and migration ledger, own-account endpoints, owner-only/case-only evidence access, and property visibility before reporting deployment ready. Retain the existing durable media configuration and existing tour viewer. Do not add subscriptions.

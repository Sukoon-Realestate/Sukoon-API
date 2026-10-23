# Pending backend features — integration and acceptance, 23 October 2026

The previously untracked chat discovery, private upload, and device-session files are now connected to their models, migrations, API routes, workers, and existing Flutter contracts. Local PostgreSQL runtime data is excluded by `backend/.gitignore`; it is not application source.

## Behavior

- Chat: `GET /api/v1/chat/messages/search/`, `GET /api/v1/chat/conversations/{id}/library/`, and the conversation list's `q` parameter support authorized discovery. Message search normalizes Arabic diacritics and alef variants, binds signed cursors to the user/query/workspace/snapshot, excludes tombstones, and checks current membership and visible history. Direct counterpart names are searched independently of the viewer's membership join. Housing groups belong to student/all inboxes and badges; stale direct-workspace hints cannot reclassify them.
- Device sessions: `PATCH /api/v1/auth/security/sessions/current/` records bounded display metadata for the authenticated session. The existing sessions endpoint lists it and accepts `revoke_session` / `revoke_others` with a stable `Idempotency-Key`. Refresh and revocation share the account lock; push targets and the selected live WebSocket are revoked without invalidating unrelated sessions. Account-wide recovery remains separate.
- Support: staged uploads have a stable client UUID, uploader/workspace/ticket-or-creation binding, inspection lease, expiry, and up to three attachments per message. Only inspected, durably stored uploads can bind to a ticket or reply. Reply receipts serialize acknowledged/absent outcomes against the original command. Downloads recheck current ticket access and content integrity. Operators use the existing Django console and browser-session authentication with CSRF protection.
- Private evidence: supported image formats, PDF, and video preserve their inspected bytes and metadata. Limits are 5 MiB/image, 25 MiB/PDF, 50 MiB/video and five minutes/video. Student evidence accepts images/PDF only. PDF inspection is isolated with resource/time limits and rejects encrypted or active-action documents; format inspection does not replace malware scanning.
- Storage retries reconcile one deterministic immutable object. Lost storage replies keep the original bytes and identity; late scanner completions do not delete a newer worker's result. Cancellation cleanup retains tombstones and retries storage outages, even when inspection is disabled.

## Migration and runtime prerequisites

New migrations: `chat.0015_search_document`, `users.0006_session_metadata`, `support.0009_staged_media`, and `features.0065_evidence_media_metadata`. New fields required by older writers remain nullable during rolling deployment.

The production preflight found PostgreSQL `pg_trgm` available but not installed, and the app role lacks database CREATE permission. The migration therefore creates a trigram index only when the extension is already installed. Search remains functional using the existing conversation/message indexes; this acceptance does not establish large-scale search performance.

Existing messages can be indexed with the resumable, derived-data-only command:

```sh
python manage.py backfill_chat_search --batch-size 200
```

New and edited messages maintain their search documents automatically. The command locks each bounded batch so it cannot replace a concurrent edit with an older index.

`maintain-support-uploads` joins the bounded general worker's maintenance schedules. It inspects at most two uploads per invocation and preserves ownership/lease checks. No payment, signing, or campaign queue is enabled by this change.

At the pre-deployment server check, evidence storage and the malware scanner were **disabled**, while support storage used the existing private Cloudinary backend. New staged uploads remain rejected in that configuration; `/api/v1/support/attachment-policy/` reports this explicitly. A configured real scanner is required for live typed-upload acceptance. Synthetic scanning is permitted only in the explicitly isolated test/development configuration. Gemini private-input processing remains off; no subscription or resource was added.

The `capture_dev` settings module is a local PostgreSQL workbench only. It reads its optional password from the existing ignored local settings directory and contains no credentials.

## Verification

- PostgreSQL regression: **499 passed, 2 skipped** across chat, users, support, bounded runtime, rolling-writer compatibility, private evidence, students, and rental phase 4. The skips require actual Android/iOS voice recordings; they are not native-device acceptance.
- After the server privilege check: six focused search/migration checks passed, including an actual PostgreSQL transaction without `pg_trgm`, Arabic/cursor discovery, and repeatable indexing of legacy rows without changing messages.
- Six focused upload recovery/policy checks passed, including lost storage responses, stale scanner completion, cancellation with unavailable storage, owner/context isolation, PDF annotation actions, and disabled inspection.
- Browser check executed the real operator attachment script against Django's hidden-row structure with a synthetic intercepted API: picker visible, submit blocked during inspection, correct workspace and ready attachment identity, one upload plus one status request, no JavaScript errors. Real backend upload/reply/download behavior is covered separately by PostgreSQL tests.
- `makemigrations --check --dry-run`, `pipenv verify`, and `git diff --check` passed. The PDF parser is pinned to the installed/tested [pypdf 6.21.2 distribution](https://pypi.org/project/pypdf/6.21.2/) with verified release hashes.

The initial broad run exposed tests for retired automatic identity migration/global restore gating, a missing MIME field in an evidence fixture, the newly extended maintenance allowlist, and help-center fixtures relying on migration seeds surviving transactional flushes. Tests now exercise the current contracts and create their own synthetic published help content; no production identity or public content was changed to make a test pass.

Local acceptance does not certify a real malware provider, production load, native recordings, or completion of the separate 24-hour runtime observation. Deployment and observation results are recorded separately in the workspace QA evidence.

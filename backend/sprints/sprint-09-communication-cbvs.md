# Sprint 09 — Communication commands and prepared read models

**Scope:** chat, notifications, support and shared WebSocket authorization. **Evidence:** A5 findings.

## Work

- Convert the 14 remaining routed productivity/forwarding/mentions/notification-action functions to small CBVs grouped by
  resource; keep existing notification/support CBVs, improving boundaries where needed rather than rewriting them blindly.
- Use one typed send/edit/delete/forward/read command service across legacy REST, rich REST and socket transports, with
  explicit protocol response adaptation. Centralize event names, original-command receipts and moderation revision flow.
- Prepare one current-authorized page context for inbox/history/replay/search, reader/poll/reply/attachment projections
  and contact disclosure. Keep authorization refresh at real boundaries; do not create a global stale permission cache.
- Bound forwarding candidate scans, read-receipt work, edit expansion, ticket messages/information/evidence and recovery
  responses. Preserve access to older history via explicit paging.
- Correct device-source digest selection and connection-scoped presence, retaining per-device/per-send current checks.

## Acceptance

- No routed area-5 HTTP function remains; Channels remain consumers and use the same domain commands where appropriate.
- Edit moderation, transport text/rate parity, original retry after edit/delete, multi-device digest and multi-tab presence
  cases pass. Message/edit/reaction/poll membership and eligible-reader visibility remain correct.
- Both socket receive **and send** still verify session/epoch/expiry. Late revocation/block/closed membership denies private
  history, events, fanout, attachment bytes and transcription results as required.
- File policy from Sprint 02 is enforced without weakening private download/nosniff and scan/ready gates.
- Inbox/history/support query and payload budgets pass at large histories; user replies/recovery do not echo an unbounded
  complete thread. Obsolete notify helpers are removed only after durable-outbox callers/registrations are verified.

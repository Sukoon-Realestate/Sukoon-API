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

## Results — 2026-11-14

Implementation and reproducible evidence are recorded in
[evidence/sprint-09/README.md](evidence/sprint-09/README.md), with machine-readable
[validation](evidence/sprint-09/validation.json), route coverage, JUnit results,
logs, query/payload/memory measurements and database-preservation hashes.
Acceptance is **partial**, with the remaining criteria explicitly retained.

| Work item | Result |
|---|---|
| Remaining 14 HTTP functions | Converted to explicit resource CBVs; 64 communication patterns and all 795 global route policies reconciled; 11 HTTP family contracts unchanged |
| Shared commands, receipts and moderation | One typed send transaction across legacy/rich REST/socket; committed event vocabulary centralized; existing edit/delete/read/forward domain implementations and original-command receipts retained. Full typed-family consolidation remains open |
| Prepared current read pages | Shared history/context/lookup/starred/replay/search preparation; current direct inbox page batches authority, blocks/restrictions, people, previews, reader facts, preferences and presence. No global permission cache; moderation/group/legacy boundaries retained |
| Forwarding/read/edit/support bounds | Bounded signed forwarding scans and explicit edit paging; PostgreSQL database-side receipt insertion; independently paged support relations plus compact reply/recovery with committed message identity. Compatible complete legacy modes remain available |
| Digest/presence/current security | Earlier fixes retained and regressed: any authorized digest source, per-device dispatch checks, renewable per-connection leases, original retries after edits/deletion, current membership/media/transcript authority; both ASGI receive and send tested for session/epoch/expiry changes |
| File policy/obsolete helpers | Existing Sprint 02 private opaque-file/ready/attachment/nosniff behavior retained; pending product sign-off remains open. Verified obsolete notify/broadcast helpers and unrouted duplicate preferences adapter removed; durable outbox/task registrations retained |

The final affected PostgreSQL gate completed with **724 passed, 2 native-clip
skips and 1 existing expected failure** (727 cases). All 11 communication HTTP
contract families passed unchanged. The three schema cleanup/migration cases
that exhausted scratch lock capacity passed after scratch-only tuning; original
full-suite outcomes remain recorded rather than relabeled green.

Prepared direct inbox queries are constant at 17 for 1/20/100 conversations
(initial measured counts were 24/385/1,905). History and edit-heavy pages use 13
queries for 1/30/100 messages; rich poll/reply event pages use 16. Compact support
reply/recovery costs stay independent of 1/100/1,000-message history. The local
10,000-message read-receipt probe uses one SQL statement and bounded Python memory.
See run/engine labels and exact assertions in the evidence rather than treating
these synthetic measurements as production guarantees.

**Unmet:** unconditional hard work/payload caps for compatible full histories;
full single typed command-family consolidation and exhaustive positive parity;
flat-query moderated/group inboxes and arbitrarily long unread lock-time budgets;
authentic native clips/provider/deployment acceptance; and the pending opaque-file
product decision. Existing direct historical-read access after blocking or
roommate withdrawal is preserved; a blanket historical-access denial would be
a separate policy/contract change. Both integrated runs completed; their failures/errors were exclusively scratch
PostgreSQL lock-table exhaustion during migration cleanup. All three affected
cases passed after increasing only the disposable cluster's lock capacity.
The original full-run outcomes and final focused results are distinguished in
the validation record; a repeated green final-tree full run remains unaccepted. No later sprint,
existing database, real provider or production operation is included.

# Area 5 communication — static audit evidence for sprint planning

> Audit notes and source evidence. The authoritative cross-domain sequence and finding-to-sprint assignment are in
> [the roadmap](../README.md) and [FINDINGS.md](../FINDINGS.md). Local suggested sprint numbers below describe phases,
> not an alternative implementation schedule. Companion scan manifests are summarized in [SOURCE_INVENTORY.md](../SOURCE_INVENTORY.md).


Backend: `/Users/demo23home/code/sukoon/Sukoon-API/backend`. Paths below are relative to it. Read-only review; no tests, management commands, application imports, DB/provider/network calls, servers, secrets, private media, or application/documentation edits were performed by this analyst. The isolated runner reported the test collection ImportError; that is distinguished below from static evidence.

## Coverage and limits

All **160 owned production files / 14,279 lines** were loaded, parsed with Python AST, inventoried for classes/functions/decorated views, and scanned for placeholder/fake/dummy markers. The companion `area-5-reviewed-files.txt` records every path, line count and content digest. This all-file static scan is not a claim that every branch received a deep manual trace. No application AST parse errors occurred. The placeholder scan found no demonstrated fake/dummy production implementation; occurrences of `pass` are exception handlers/classes.

Deep manual paths: REST and both WebSocket direct/rich send protocols; current direct/housing/company authorization; session middleware guarded send/receive; conversation creation/workspace classification; history/context/events and projections; edits/deletion/mentions/reactions/pins/polls/forwards; attachment upload/decode/private download/cleanup/remote-storage adapters; transcription enqueue/provider/access checks; moderation enqueue/claim/evidence/decision/review; notification recipient scope, preferences, per-device outbox, session rechecks and daily digest scheduling; support create/detail/reply/information/evidence/staff operations/upload scan/private download/recovery and staff payment-report authority. Model constraints and URL registrations were read as supporting evidence. Small import/export/app/serializer/task modules were statically scanned, with selected source reads, not independently exercised. Out-of-area reads were limited to relevant callers/shared authorization and the poll tests; they do not establish deployment health.

## Checklist

| Check | Result | Evidence / finding |
|---|---|---|
| Current chat membership and visibility boundaries | pass for traced read/send/media paths | `chat/services/group_access.py:11`, `direct_access.py:68`, `company_access.py:48`, `views/group_attachments.py:46`; company chat fails closed explicitly |
| WebSocket session revocation/expiry | pass for traced middleware path | `common/ws_auth.py:58` fresh checks wrap **both** receive and send; `users/services/sessions.py:11`; do not report connection-only authentication |
| WebSocket text/type/rate limits | fail | A5-02 |
| Moderation revision freshness | partial | old revisions cannot sanction (`moderation/queue.py:206`, `decisions.py:96`), but edits never enqueue A5-01 |
| Private participant fields | fail | A5-03 |
| Attachment scoping, private downloads and media decoding | pass for traced access; file-content policy partial | uploader/membership fencing, byte caps, Pillow/ffmpeg verification and `nosniff` present; A5-11 identifies deliberately opaque arbitrary files, not inline execution |
| Transcription privacy | pass for traced path | `services/transcription.py:39`, `:138`, `:177`; access before and after provider call, encrypted output, duration quota; no provider executed |
| Inbox/message/support query growth | fail | A5-04–A5-08; static ORM evidence, no query count benchmark |
| Durable notification retries / scoped counts | pass for traced safety checks | `notifications/services/push_delivery.py:29`, `:232`, `inbox_scope.py:54`, notification inbox mixin `:104`; device/user/session/scope/access rechecked |
| Digest device selection | fail | A5-09 |
| Idempotent direct retries after edits | fail | A5-10 |
| Support owner/staff/evidence authority | pass for traced policy | `support/services/payment_reports.py:32` deliberately grants all tickets to current support roles; assigned financial reviewers remain restricted. No support-adapter bypass finding |
| All views CBV | fail against requested architecture | 14 routed decorated function views, A5-13 |
| Proven obsolete helpers/test drift | partial | A5-12 and A5-14; migrations and rollout fields retained, no blanket dead-code claim |
| Presence correctness | fail | A5-15 |
| Operational/provider/performance verification | not checked | prohibited in analyst scope; static review does not establish passing tests or production configuration |

## Verified findings and sprint tasks

<a id="a5-01"></a>
### A5-01 — High — message edits bypass moderation enqueue

Evidence: `core_apps/chat/services/message_mutations.py:108` emits `record_event(..., "message.edited", ...)`; `services/group_events.py:25` enqueues only `{'message.new', 'message.edit'}`. `moderation/queue.py:26` snapshots a message revision, while `:206` makes older edited revisions `new=False`; `moderation/decisions.py:96` rechecks revision before sanctions.

Trigger/impact: in a moderation-enabled enrolled direct chat with consent, send harmless text and edit it into prohibited text. The original input is stale and the edited revision gets no input, so it cannot receive the intended review. This is verified source behavior; no provider experiment was performed.

Sprint task: centralize event names and enqueue each committed reviewable revision through the shared event/service path. Acceptance: send then edit produces exactly one moderation input per revision; retry does not duplicate it; edits during provider processing invalidate the old result and schedule the new revision; deleted content never creates a sanction.

<a id="a5-02"></a>
### A5-02 — High — legacy direct socket bypasses text validation and explicit send limits

Evidence: `core_apps/chat/consumers.py:66` falls back from rich handling for direct messages without `chat.v1`; `:87` calls `.strip()` on untyped `content`; `:126` calls `send_message`. The legacy service `services/message_service_parts/send_message.py:19` has no content length/type/null-character validation or rate enforcement. Rich protocol uses `group_consumer.py:83`/`services/group_send.py:43` and `:66` to enforce a 4,000-codepoint policy. Legacy REST instead caps 5,000 (`serializers/message.py:37`). DRF HTTP throttling in `config/settings/base.py:530` does not execute for Channels messages; shared socket middleware checks authority, not rate.

Trigger/impact: an authenticated conversation participant sends direct `message.send` without a rich protocol. Text beyond the rich policy reaches the DB/service/event pipeline; rapid frames bypass the explicit per-minute send limiter. `content: null` or a numeric/list value raises an uncaught attribute error before the consumer's exception handling. This is a bounded source claim: server/proxy frame limits were not operationally measured.

Sprint task: use a shared typed send command and rate limiter for both transports/protocols, retaining legacy response compatibility. Acceptance: identical text limit/newline/null policy across REST/socket; null/list/number/oversize gives a stable validation response and keeps the socket usable; both protocols consume the same send quota and cannot bypass it by omitting `protocol` or `kind`.

<a id="a5-03"></a>
### A5-03 — High — starting a chat discloses the counterpart's email

Evidence: `core_apps/chat/serializers/participant.py:11` includes `email = serializers.EmailField()`; `serializers/conversation.py:10` inherits it for `other_participant`, and `:110` serializes the counterpart. `views/conversation.py:119` fetches any supplied active target user and returns that serializer at `:133`. `services/message_service_parts/get_or_create_direct_conversation.py:49` blocks an existing nonaccepted roommate connection but returns false when no connection exists (`:61`); contextual creation (`services/conversation_preferences.py:70`) requires active/new-business eligibility, not an existing relationship or contact-disclosure consent. Legacy message responses also use ParticipantSerializer (`serializers/message.py:8`).

Trigger/impact: an authenticated user with a visible/known active counterpart UUID and no block/nonaccepted connection can create a direct conversation and obtain the counterpart's account email. Conversation membership is created by the requester, so the participant guard does not protect this field. This is private account-field exposure, not an object-authorization bypass into another person's existing thread. Product-approved email disclosure policy was not supplied.

Sprint task: introduce a minimal public chat-participant projection and explicitly authorize any contact fields. Acceptance: arbitrary counterpart creation/list/detail/history/acks return only the approved public identity; email is absent unless an explicit supported disclosure policy grants it; self-account/admin views keep their authorized data; phone masking remains intact.

<a id="a5-04"></a>
### A5-04 — Medium — conversation list prefetch is defeated by repeated per-row authorization/projection queries

Evidence: `views/conversation.py:90` prefetches participants and participant_set, but `serializers/conversation.py:55`, `:86` separately call `authorize` for the same row; `:60`/`:87` each fetch the latest message through `.filter().first()` at `:97`; `:129` adds `exists/count/exclude` participant/block queries. `services/direct_access.py:69`–`:104` issues fresh user/participant/other-person/block/restriction queries each call. `services/conversation_preferences.py:98` adds counterpart/block/workspace/list queries. Counterpart phone payload is recomputed by four serializer methods (`serializers/conversation.py:24`–`:34`).

Trigger/impact: listing 20/100 direct conversations performs repeated DB work per conversation despite the prefetch comment, growing linearly with rows and amplifying search results that reuse the serializer. No exact count is claimed.

Sprint task: build one request-scoped authorization/projection context per conversation; bulk-load relevant current grants, restrictions, blocks, workspace/list preferences, latest visible messages and contact payloads. Acceptance: representative 1/20/100-thread query budgets are recorded and avoid repeated per-field reads; current block/revocation and cleared-history semantics still hold; summaries reuse already-computed context only inside the same request/authority boundary.

<a id="a5-05"></a>
### A5-05 — Medium — rich message pages and event replay have per-message query growth

Evidence: `services/group_projection.py:55` constructs eligible readers for each message and calls two counts at `:148`; `:121` can lazily load sender profiles; `:105`/`:106` read reply attachments not prefetched by `views/group_history.py:38`; `services/polls.py:66` loads eligible membership periods for each poll. History prefetches attachments/edits/reactions (`views/group_history.py:38`) but cannot eliminate these counts. Event replay at `views/group_history.py:182` loads bare ChatEvent rows and calls `event_payload` individually (`:194`), whose `services/group_events.py:73` reauthorization/message projection lazily reads relations again. Search similarly calls projection and full ConversationSerializer per result (`services/search.py:170`, `:201`).

Trigger/impact: 30/100-message history pages and replay batches produce at least two reader-count queries per message plus relation/authorization/poll work. Edits additionally serialize all edit revisions per message (`group_projection.py:134`), with no per-message history cap. The same heavy projection also runs in synchronous post-commit fanout (`group_outbox.py:56`), under business-root locks.

Sprint task: add bulk reader/eligible-count annotations or in-memory roster computation, explicit nested prefetch plans and shared page/replay projection context; bound edit-history expansion or move it to a paginated detail resource. Acceptance: measured 1/30/100-message and event batches have documented bounded query budgets with no per-message count/profile/reply-attachment reads; late membership/deletion/hidden-history checks retain their behavior; edit-heavy messages cannot make every history/event response arbitrarily large.

<a id="a5-06"></a>
### A5-06 — Medium — forward destinations paginate after scanning every conversation

Evidence: `services/forwarding.py:46` iterates all candidate conversations, reauthorizes and builds a result for each. `views/forwarding.py:15` calls this function before applying a 20-item paginator at `:18`.

Trigger/impact: opening page one for an account with a large chat history performs authorization/title queries for every accessible thread and materializes the full list. UI pagination limits response size but not DB/CPU/memory work.

Sprint task: implement a bounded candidate cursor/scan with current authorization before returning results. Acceptance: page one and subsequent pages inspect a defined maximum number of candidates, preserve filtering/order, and never reveal unauthorized destinations or skip a usable cursor when candidates are rejected.

<a id="a5-07"></a>
### A5-07 — Medium — marking a long unread history read creates all receipts in memory under chat locks

Evidence: `services/group_operations.py:12` authorizes with locking and calls `record_reads` at `:37`; `services/message_tools.py:146` builds a Python list of a MessageReadReceipt for every unseen visible incoming message at `:155`–`:161`, then bulk_create with `batch_size=500`. The batch size bounds SQL statement size, not Python materialization or transaction duration. Legacy mark-all-read delegates to this path (`message_service_parts/send_message.py:173`).

Trigger/impact: marking a long-idle conversation read allocates O(unread-message-count) objects and inserts them in the request while holding the shared conversation/root lock; sends and other commands wait. This can grow independently of history page size.

Sprint task: preserve monotonic read authority while bounding receipt creation memory/work (database-side insert/select or checkpointed/chunked durable projection). Acceptance: a large synthetic unread history stays within a documented memory/latency budget; no duplicate receipt on retries; read timestamps retain their documented meaning and current membership/visible boundaries are enforced. Do not silently invent per-message exact times if moving work asynchronously.

<a id="a5-08"></a>
### A5-08 — Medium — support detail/reply/recovery return unbounded threads with nested evidence N+1 queries

Evidence: `services/ticket_service_parts/get_ticket_detail.py:22` prefetches the entire message/attachment history; `serializers/ticket.py:53` returns all messages. Reply returns complete detail (`views/ticket.py:174`), and receipt recovery also serializes complete detail (`views/recovery.py:66`, `reply_recovery.py:57`). `services/information.py:16` traverses every information request and issues per-request history/evidence queries; `services/information_evidence.py:61` performs a separate attachment `.exists()` for each version file. No thread/information/evidence paging or cap is present.

Trigger/impact: a ticket with many messages and repeated evidence corrections makes ordinary detail, reply and recovery work grow with the entire ticket history; nested queries grow with requests, versions and files. Existing top-level ticket pagination does not constrain this.

Sprint task: add cursor-based ticket messages/information history or bounded expansions, use a compact reply receipt, and bulk-resolve current evidence availability. Acceptance: old and new ticket data remain reachable through stable pagination; create/reply/recovery response cost is bounded; one file-availability query can cover a page of evidence; no private internal notes appear in consumer responses.

<a id="a5-09"></a>
### A5-09 — Medium — one expired device session can suppress a digest despite another authorized device

Evidence: `notifications/services/delivery_policy.py:181` selects `.first()` among active-device PushDelivery rows; `:183` permanently marks the entire hold suppressed if that single source fails `allowed`. `summary_authorized` repeats the same first-row shortcut at `:154`. `push_delivery.py:50` rejects expired/revoked bound sessions; natural session expiry need not flip DeviceToken.is_active.

Trigger/impact: a notice has two active registered devices; the first selected row's auth session has expired, and the other row is still authorized. The digest hold is suppressed without considering the valid source; an existing summary can likewise fail authorization. This is missed delivery, not excess disclosure.

Sprint task: select any currently authorized source across eligible devices or separate notification eligibility from per-device eligibility; retain per-device rechecks at dispatch. Acceptance: first device expired + second valid still creates/delivers one appropriate digest; all expired suppress it; changing device registration or source access never restores unauthorized content.

<a id="a5-10"></a>
### A5-10 — Medium — a legacy direct send retry conflicts after that message is edited

Evidence: legacy `services/message_service_parts/send_message.py:65` compares the retry content with mutable `existing.content`; creation at `:80` records no immutable payload fingerprint. Rich fallback for legacy messages (`services/group_send.py:124`) also compares the current content. `services/message_mutations.py:98` replaces content, while its `:103` comment promises a delayed original retry will return the same message through an immutable fingerprint.

Trigger/impact: send legacy text with a client_message_id, successfully edit it through chat.v1, then retry the original send with its original body. The service reports a conflicting identity although the original operation committed. The same happens after deletion clears content. Clients attempting recovery can misclassify the original send as rejected/conflicting.

Sprint task: persist canonical original-command fingerprints/receipts for legacy and rich sends and use them independently of mutable presentation state, with migration behavior defined for old rows. Acceptance: original retries after edit/deletion return the original ID/current authorized state without restoring content or creating a duplicate; altered original commands still conflict; cleared-history boundaries remain enforced.

<a id="a5-11"></a>
### A5-11 — Medium / policy gap — opaque chat files accept every byte format without content inspection

Evidence: `services/group_media_storage.py:121` dispatches `kind=file` to `rich_media.inspect_file`; `services/rich_media.py:120` only reads bytes and sets application/octet-stream. It does not check a file-type allowlist/signature, archive content or malware result. `views/group_attachments.py:146` safely forces download for file content, and `:145` sets nosniff; current private authorization and byte caps remain present. Moderation explicitly treats files as uninspected evidence (`moderation/provider.py:185`).

Trigger/impact: any nonempty executable/archive/document bytes within the file cap can be attached and sent as `kind=file`. The server does not execute them or render them inline, so this is **not** a verified server-code-execution/XSS vulnerability. It is a concrete gap to resolve against the user's requested file-type/security policy, particularly for recipients downloading files.

Sprint task: document approved chat file classes and enforce the corresponding signature/type/container policy or explicitly approve arbitrary opaque download behavior; if malware inspection is required, quarantine until durable inspection completes and fail closed when unavailable. Acceptance: policy is explicit, extension/MIME spoofing cannot bypass supported-type checks, opaque files never render inline, and rejected/quarantined files cannot be bound or downloaded as ready. Product choice determines the precise implementation; do not label arbitrary downloads automatically unsafe by MIME alone.

<a id="a5-12"></a>
### A5-12 — High for validation readiness — poll-voter tests import a nonexistent helper

Evidence: `core_apps/chat/tests/test_shortlist_polls.py:5` imports `poll_voters`; the production `services/polls.py` exports normalize/create/payload/change helpers only, ending at line 145. Existing `group_urls.py:39` and `:43` still register vote/close routes; `views/productivity.py:83`/`:89` call change_poll; poll sending, property-link validation and aggregate counts remain implemented. Repository-wide static search finds `poll_voters` only in this test file; no current production voter-list route or frontend reference was found in Sukoon-API. The isolated collection already observed the ImportError; this analyst did not rerun tests.

Trigger/impact: collecting this test module fails at import, blocking the module's valid property-link tests too. Source cannot establish whether voter identities were intentionally retired or a feature implementation was lost. Therefore classify this as **test/contract drift**, not proof that all polling is broken or that a required production route is missing.

Sprint task: settle the intended voter-list contract, restore the scoped helper/route if still required, or replace stale voter-identity tests with the approved aggregate contract while retaining link/vote/membership tests. Acceptance: full collection no longer fails for this import; link validation and active vote/close behavior remain covered; if identities are supported, current membership, eligibility and disclosure rules are tested explicitly. Do not fix by deleting the whole test file or exporting a dummy helper.

<a id="a5-13"></a>
### A5-13 — Medium / architecture — 14 routed function views remain against the requested CBV rule

Evidence: AST inventory identifies 9 decorated API functions in `views/productivity.py:19`–`:97`, 2 in `views/forwarding.py:14`/`:26`, 2 in `views/mentions.py:13`/`:22`, and 1 in `views/notification_actions.py:32`. `group_urls.py` imports/routes them. Notifications and support owned HTTP entry points use CBVs. Existing service extraction is substantial and worth preserving.

Sprint task: convert those 14 functions into small APIView/generic classes grouped by resource, retain reusable pagination/no-store helpers and domain services; keep transaction/auth order deliberate. Acceptance: every routed area-5 HTTP handler resolves to a CBV, URL names/methods/statuses/body/auth/headers remain compatible, and service/model logic is not copied into views. This is an explicit architecture requirement, not a claim FBVs are insecure.

<a id="a5-14"></a>
### A5-14 — Low / cleanup — unused pre-outbox send helpers and an unrouted preferences view remain

Evidence: `_notify_recipients` and `_broadcast_new_message` in `services/message_service_parts/get_or_create_direct_conversation.py:128`/`:173` have no repository call sites; they are merely imported/re-exported by `message_service.py:27` and imported unused by `message_service_parts/send_message.py:13`. Actual send uses durable `record_event` at `send_message.py:117`, with per-recipient reauthorization in group_outbox. `views/group_commands.py:25` defines GroupPreferencesAPIView but no route/import uses it; routed preferences use `views/preferences.py:11`. The underlying `set_preference` service still has tests, so it is not proven wholly unused.

Sprint task: remove obsolete private notify/broadcast definitions and stale reexports/imports, and retire or deliberately route the duplicate preferences class after checking compatibility consumers. Acceptance: production/static call graph and import checks establish no remaining caller; durable outbox delivery and current preferences contract stay intact; remove neither historical migrations nor rollout-compatibility fields (`workspace_archived`, `direct_pair_key`) as part of this small cleanup. No other fake/dead production subsystem is asserted.

<a id="a5-15"></a>
### A5-15 — Low — online presence expires during active sessions and one tab disconnect marks all tabs offline

Evidence: `consumers.py:46` sets one user-level key only on connect; `:55` deletes it on every disconnect. `services/message_service_parts/get_or_create_direct_conversation.py:20` sets a 300-second TTL, `:34` sets the key, `:36` deletes it. No heartbeat/refcount/refresh caller was found. ParticipantSerializer exposes this flag at `serializers/participant.py:31`.

Trigger/impact: a healthy socket open beyond five minutes appears offline; with two active sockets, closing one deletes the other's presence. This affects UI correctness, not authentication.

Sprint task: track connection-scoped heartbeat leases and derive user presence from live leases (or explicitly change API semantics). Acceptance: one of two sockets disconnecting leaves presence online; active sockets renew past five minutes; abandoned connections expire without permanently stuck online status.

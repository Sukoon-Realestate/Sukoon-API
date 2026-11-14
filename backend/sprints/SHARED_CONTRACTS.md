# Shared command and HTTP contracts

Sprint 10, 2026-11-14. These interfaces describe current code; they grant no authority by themselves.

| Concern | Interface and caller responsibility |
|---|---|
| Authentication | `common.cookie_auth` authenticates cookie/SimpleJWT sessions and applies origin policy. Preserve `request.auth` when calling commands. `common.command_authority.recheck_actor_session(actor, claims)` fences the original session after locks. Native admin uses Django session/CSRF and installed model permissions. |
| Current staff | `admin_api.permissions.require_staff_actor(actor, roles, lock=True)` reloads account/profile, locks them and enforces active role and sensitive-action access. Call inside the transaction **before receipt replay**. `roles=None` intentionally retains general staff/support scope; recovery reviewers have a separate restricted workflow. Read permissions do not authorize a later write. |
| Commands | Validate transport containers with named serializers (`admin_api.serializers.commands`, property/report/moderation serializers). Services own current authority, independence, transaction/lock order, revision, receipt and committed effects. `properties.services.moderation.decide` is the property moderation command for API, native and legacy adapters; pass original `auth_claims` from JWT transports. |
| Receipts | `common.idempotency.execute_idempotent` runs an action returning `(data, status, subject_id)` and returns `(data, status, replayed)`. Use stable actor/operation/key and fingerprinted original command. It is **not** an authorization policy: recheck domain authority before calling it. Original JWT claims fence recoverable operations. `resolve_or_close` supplies lost-response absence fencing. Never expire/rekey a recoverable command just to retry a side effect. |
| HTTP responses | `common.renderers.GenericJsonRenderer` and `response_policy` own the two-key JSON envelope and safe pagination/error headers. Return `Response` and preserve service status plus `idempotency.response_headers(replayed)`. Unknown errors have an opaque `X-Correlation-ID`; logs contain error class/correlation, never raw exception messages or credentials. Validation/permission errors retain their established classification and language. |
| Raw HTTP | Health, associations, signed payment callbacks/returns, native HTML and byte streams use Django `View` adapters. Do not apply the JSON envelope, consume/re-encode signed body bytes, or change supported methods, stream/file headers or error precedence. Health intentionally catches dependency failures broadly and returns only readiness; this fail-closed probe does not certify worker/storage readiness. |
| Private files | `common.private_storage.DurablePrivateStorage` provides immutable names, bounded files, verified remote materialization and no public URL. A name, digest or storage object is **not ownership**. Identity uses `profiles.identity_media`/recorded owned assets; chat uses `chat.services.attachment_access`; support uses its resource gateway; tours/portfolio use current grant/resource/reference checks. Authorize before opening bytes and recheck references/retention before deleting. Never accept a client Cloudinary reference as deletion authority. |
| Recovery failures | Missing private bytes become missing resources; known provider/filesystem failures become retryable storage errors. Programming errors propagate. `_save` deliberately catches/rethrows all failures only to remove the unpublished local cache file. Audit-source query failures propagate to the normal correlation-aware error boundary; an incomplete audit must never appear successful/empty. Provider uncertainty remains durable and is never automatic permission to resend. |
| Prepared reads | `HistoryPage` filters/orders/unions source identities before slicing and hydrates the selected page; legacy full service reads remain compatible. `campaign_audience` prepares 500-account preview batches with SQL membership constraints before scan/recipient limits. Its facts live only for that preview. Delivery reloads current eligibility, consent and device/session authority. Never reuse preview/read facts for later authorization. |

## Supported native admin differences

Native admin is a separately authenticated operator workflow with Django model permissions and CSRF. Framework-owned
`AdminSite`/`ModelAdmin` URLs, built-in actions and form internals remain Django-owned; custom project routes use explicit
Django classes under `admin_site.admin_view`. `sprint10-coverage` inventories both categories.

- Property/PropertyRequest forms are decision-only and call `moderation.decide`; they cannot save arbitrary listing fields.
  Legacy queue deletion is a canonical block with its original success message. Bodyless clients retain observed-version
  fallback and revision-derived keys; the second bodyless submission can conflict. Explicit version/key retries replay.
- Native KYC uses the same current, independent, evidence-bound approve/reject services. Model save/add/delete are disabled.
  Native KYC has no durable command key; retrying an already-reviewed submission returns the existing validation outcome.
- Native policy, chargeback, mandate, portfolio-media, reputation and tour review classes retain their installed typed
  forms/serializers and canonical domain commands, including independence and scoped evidence checks. There is no generic
  model-save approval fallback. Reputation generic change URLs redirect to reasoned inspection.
- Native managed public pages/release notes intentionally use ModelForms, model validation and a locked incrementing
  revision plus `ContentEditAudit`. They now require current system-owner authority and sensitive access. This workflow
  has no client-supplied expected revision or durable operation key; use the shared content API for those guarantees.
- Django user/group maintenance remains a separately permitted operator/bootstrap workflow with native `LogEntry` history;
  it is not a public self-service account-change alias. User verification flags are read-only, account deletion is disabled,
  closed accounts cannot be edited, and suspension revokes sessions. Catalog maintenance forms retain their existing
  validation/revision and installed Django permissions; operational model histories remain read-only where registered so.
- Native tour **disable viewing** is the existing emergency suppression action under Django tour-change permission. It only
  disables serving; it neither approves a revision nor republishes content. The hash-bound review service remains required
  for approval. Do not use the emergency action as a publication bypass.

All native admin entry points now check current disabled staff profiles. Unsafe native requests additionally check current
sensitive access. These are intentional security corrections, as are command-time report authority checks. General report
`dismiss`/`mark_active` retains broad active staff access, with independence from reporter/reported account; suspending/banning an account still requires user-manager scope.

# Sprint 03 intentional bug-contract corrections

These are correctness changes, separate from the mechanical CBV work in Sprints 05–10.
Existing route names, aliases, auth requirements, successful command identities and response
renderers are retained. No production deployment or database migration was performed.

- Listing detail PATCH and alternate PATCH/PUT now share optimistic checks and idempotency.
  A stale `If-Unmodified-Since` or conflicting request identity returns 409 consistently.
  PUT continues full-field validation. Validation uses the locked current listing.
- Owner visit acceptance is confirmed / (confirmed + rejected), with the denominator exposed
  as `handled_visits_count`. No decisions produces `null`, including the formatted value.
  Ratings come from the canonical eligible rental-review aggregate; no eligible reviews
  produces `null`, with a real review count. Clients should display an empty-history state.
- Malformed handover/maintenance revisions, dates and consumed containers return 400 before
  mutation. Existing bounded text command keys, legacy containers and canonical decimal-string revisions remain supported.
  Maintenance appointment timestamps require an explicit timezone. Empty inactive
  legacy controls remain compatible; receipts still fingerprint original input.
- The rental refund command authorizes the payer and selects supported rental payments before
  dereferencing a lease. Unsupported, foreign and malformed payment identities retain main’s 404 contract.
- An absent final-settlement GET returns the virtual initial draft with `id: null`, revision 1.
  Propose creates its durable identity. Reading documents or absent drafts creates nothing.
- Document lists retain `count`, `next`, `previous`, `results`, and add standard page metadata.
  Default page size is 20, maximum 100. Clients must follow page links for longer catalogs.
  Signing/capture transitions create catalog intents. Historical sources are repaired only
  with the explicit idempotent `backfill_rental_document_intents <lease UUID>...` command;
  it was tested on synthetic data and was not run on any existing database.
- Admin history uses complete filtered SQL sources, deterministic timestamp/public-ID ordering,
  authoritative counts and page-only hydration. Search includes persisted audit reasons/notes
  selected by the source query; a second inconsistent Python filter no longer discards them.
  No retention cutoff is silently imposed.
- Campaign previews cap actual eligible accounts (default 5,000), independently of the scan
  budget (default 100,000). `ADMIN_CAMPAIGN_RECIPIENT_LIMIT` and `ADMIN_CAMPAIGN_SCAN_LIMIT`
  distinguish these limits; exceeding the scan budget returns an explicit audience error.
  Existing preview receipts and delivery-time authorization/device/consent checks remain.
- Refresh accepts JSON, form and cookie commands without mutating parsed request data.
  Malformed bodies/tokens return defined errors. Cookie precedence and rotation are preserved.
  Djoser social adapters now use the same bound-session issuer as native social login.
- Original chat send receipts survive edits and deletion; replay returns the original ID and
  current authorized state. Cleared-history retries conflict. Historical tombstones without
  a receipt or retained original edit cannot be reconstructed and fail closed with 409.
- Presence is per socket, renewed automatically, and removed only for the disconnected or
  cancelled socket. `chat.0029_chatpresencelease` must be deployed before the changed sockets.
- Polls retain the Sprint 00 aggregate-only contract, including the viewer's own selection;
  voter identities remain intentionally undisclosed. Existing valid tests were retained.
- Current admin KYC status uses the latest non-superseded submission, ordered by creation and
  primary key. Multiple historical non-superseded rows cannot make the same account appear
  both pending and rejected. Verified account authority remains the existing verified flag.

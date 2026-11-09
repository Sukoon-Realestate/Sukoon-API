# Sprint 02 — Type every command and define upload content contracts

**Outcome:** invalid user data produces controlled field-level errors before mutation or provider work.
**Owners:** API/domain maintainers + storage/media maintainer. **Evidence:** [UPLOADS.md](UPLOADS.md), A1-01/A1-05/A1-07,
A2-04/A2-05/A2-06, A3-02, A4-03/A4-04, A5-02/A5-11.

## Stories

- Add complete create/update/action serializers for property inventory and metadata, maintenance, handovers, checkout,
  disputes, refund eligibility, chat commands and refresh. Remove raw request coercion from command implementations.
- Validate strict nonboolean revisions/counts, supported UUIDs, finite fixed-precision money, enum values, timezone-aware
  dates and bounded strings/lists/nesting. Detect duplicate room/bed/offer IDs. Define unknown-field behavior explicitly.
- Separate create-only, update-only, actual-upload and server-owned-reference inputs. Update-only image keys on property
  create must have defined semantics or return 400, not reach model constructor errors. Invalid image strings must not
  reserve a slot and masquerade as an uncertain provider upload.
- Unify cover/gallery capacity reservations under one listing lock, including pending reservations, intended replacement
  and retries. Complete decoded video signature/container/duration/size validation through bounded inspection.
- Document resource-specific allowed media and limits. Preserve stronger existing identity/evidence/tour decoders and
  metadata stripping. Decide opaque chat-file policy explicitly; implement quarantine/inspection only as required by that
  policy, preserving forced download/nosniff and private authorization.
- Preserve original authenticated epoch/claims across validation, locked writes, replay and upload completion.

## Acceptance

- The negative matrix in UPLOADS.md covers every write/upload family with controlled 400/409/413/415/422 outcomes as
  appropriate; no unexpected ValueError/TypeError/AttributeError or accepted Infinity/NaN reaches persistence.
- Rejected input causes no domain writes, ready artifact, provider submission or stranded reservation.
- Concurrent cover/gallery completion never exceeds the 25-image product cap; retries do not duplicate media.
- Signature/type/actual-byte/decoded-size mismatches fail; valid supported multipart/base64/native images still work.
- Schema/parser changes have explicit client compatibility notes. Valid stale commands continue to conflict rather than
  silently overwrite, and no field validation change weakens current authority or idempotency.

**Out of scope:** mechanical conversion of every view. Introduce reusable validation/services here, then migrate transport
adapters in Sprints 05–10 without copying those rules back into methods.

## Results (2026-11-09)

Implemented on branch `sprint-02/inputs-and-uploads` (worktree `../Sukoon-API-sprint02`, based on `d46cc2bf` with the
uncommitted Sprint 01 changes staged as its baseline); Sprint 02 changes are unstaged and uncommitted for review.
Evidence: [evidence/sprint-02](evidence/sprint-02/README.md). No existing database, media, secret or production system
was altered (hashes verified before/after). No migrations, no route changes, `Pipfile.lock` unchanged.

### Stories

| Story | Status | What changed |
|---|---|---|
| Typed create/update/action commands | **Done for the listed families** | `common/command_fields.py` (strict revisions, strict text, request keys, UUID lists, aware date-times, bounded JSON, finite money, object-body guard) and `features/rental_serializers_parts/command_serializers.py`. Maintenance create/action, handover create/update/respond, dispute create/respond, rent checkout, refund create/respond read only `validated_data`. Rental change create/respond/submit/signing use the shared strict revision and bounded key parsers. Property inventory (`inventory_schema.py`) and metadata/amenities/image-id fields are typed. Refresh builds its own command (A1-07). Chat send/read reject non-object bodies; a poison matrix over 18 chat write routes found no other 5xx |
| Strict values, duplicates, unknown-field policy | Done | Bool/null/float/list/object/junk revisions → 400; `Infinity`/`NaN`/overflow/over-precise money → 400 (exact stored text kept); naive date-times → 400; bounded strings/lists/nesting; duplicate persisted room/bed/offer IDs and repeated image IDs → 400. Unknown-field policy documented in [UPLOADS.md](UPLOADS.md#command-schema-policy-applies-to-every-sprint-02-typed-command) |
| Separate create/update/upload/reference inputs | Done | Edit-only image keys on create: empty values ignored, anything else 400 (was a model-constructor 500). Listing images accept only uploads/data URIs; URL/public-ID strings are 400 before any reservation or provider call (was a false 503 with a stranded `pending` slot) |
| One cover/gallery capacity policy; video validation | Done | `properties/services/listing_capacity.py`: stored + pending/unknown reservations under the listing row lock for cover replacement, gallery reservation and the legacy service. Listing video decoded by the shared bounded `inspect_video_path` (MP4/MOV signature, codec, ≤ 50 MiB, ≤ 60 s measured; stored duration is the measured value). **Pre-existing deadlock fixed:** gallery upload locked the account `FOR UPDATE` while a concurrent cover replacement needed `FOR KEY SHARE` on it → PostgreSQL deadlock (500). Account locks in listing media now use `FOR NO KEY UPDATE` (still serialized with revocation) |
| Resource media policy; chat files | Done; chat policy needs product sign-off | Per-resource table in [UPLOADS.md](UPLOADS.md#resource-media-contract-sprint-02-2026-11-09). Identity/evidence/tour/portfolio decoders unchanged (evidence video now shares the same inspector). Chat `kind=file` is an **explicit opaque-download policy** (private, octet-stream, attachment, nosniff, no-store, never inline); no quarantine because the policy requires no inspection |
| Preserve authenticated epoch/claims | Done for the typed commands | `common/command_authority.recheck_session` re-validates the original token claims after the domain lock in every typed rental command and in property create/update; listing uploads already did. Test: revoking during the lease lock → 401, no rows, no receipt |

### Acceptance

| Criterion | Met? | Notes |
|---|---|---|
| Negative matrix covers every write/upload family with controlled 400/409/413/415/422; no unexpected ValueError/TypeError/AttributeError or accepted Infinity/NaN reaches persistence | **Partly** | Covered with tests: listing (create/update/images/video/inventory), maintenance, handovers, disputes, checkout, refunds, rental-change revisions, refresh, chat writes (no-5xx matrix). **Not covered in Sprint 02:** the remaining ~770 routes (company, planning, commerce, advertising, admin, support, tours, identity) were not individually fuzzed; their typed-command migration is Sprints 05–10 per the sprint's "out of scope". Oversized media return 400, not 413/415 (existing envelope) |
| Rejected input causes no domain writes, ready artifact, provider submission or stranded reservation | **Yes** for the covered families | Asserted per case: row counts, idempotency receipts, provider mock call count |
| Concurrent cover/gallery completion never exceeds 25; retries do not duplicate media | **Yes (PostgreSQL)** | 4 concurrent writers at 23/25 → exactly 2 succeed, 2 get 400; 10/10 repeated runs (baseline code: deadlock 500, 3/3). Retries dedupe through the existing `Idempotency-Key` receipts; a PATCH retried *without* a key can add a cover again (bounded by the cap) |
| Signature/type/byte/decoded-size mismatches fail; valid multipart/base64/native images work | **Yes** | JPEG/PNG/WebP multipart, base64 PNG, native HEIC tested (HEIC listing upload previously failed with 400). Real provider (Cloudinary) behavior not exercised |
| Explicit client compatibility notes; stale commands still 409; no weakening of authority/idempotency | **Yes** | Notes below. Route-contract fixtures for all 189 families are unchanged (after restoring authority-before-validation order on disputes/refunds). Replay fingerprints still use the raw body |

### Client compatibility notes

- Revisions: `true`, `null`, floats, lists, objects, non-digit strings → 400 (previously 500 or silently 0). Digit strings still accepted.
- Text fields reject numbers/booleans (previously stringified). Maintenance `priority` ∈ `low|normal|high|urgent|emergency`; `category` is a lowercase code ≤ 40.
- Maintenance/handover/dispute/note text bounded (4,000); handover JSON fields bounded (16 KiB, depth 4).
- Appointment date-times must include an offset (previously naive values were also rejected, but after the lock; non-string values were 500).
- Refund requests for non-rental or malformed payment attempt IDs → 404 (non-rental previously 500).
- Disputes ignore soft-deleted evidence (as maintenance/handover already did).
- Listing images: URL/public-ID strings → 400 (previously 503 pending); BMP/TIFF → 400; HEIC now accepted. Limits 20 MiB / 50 MP.
- Listing video: must be a real MP4/MOV ≤ 50 MiB and ≤ 60 s; `video_duration` in responses is the measured value.
- Property create: non-empty `main_image_id`/`retained_image_ids`/`images_metadata` → 400; empty values ignored.
- Cover replacement at 25 images (including pending uploads) → 400 on `main_image` unless `retained_image_ids` frees a slot.
- `deposit: "nan"`/`"inf"` → 400.
- Chat send/read with a non-object JSON body → 400. Refresh with non-string token → 400; form/multipart refresh now works.
- Flutter request shapes (inventory extension keys, handover string/list fields, string request keys) were checked against `sokoun` sources and remain valid.

### Open items handed to the owners

1. Product: approve the chat opaque-file policy (or request an allowlist + scanning, which then needs quarantine).
2. Backend (Sprints 05–10): migrate the remaining write families onto `command_fields` while converting views; extend
   the no-5xx matrix per family. Consider a global object-body policy for JSON once array-accepting routes are listed.
3. Backend/product: listing photos are uploaded to the public CDN without EXIF/GPS stripping (unchanged; identity,
   portfolio and chat already strip). Decide whether to re-encode listing images.
4. Ops: ffmpeg/ffprobe must be present on every web dyno that accepts listing video (Aptfile already installs it);
   without it the endpoint fails closed with 503.
5. Real Cloudinary acceptance of measured videos/HEIC was not exercised (provider mocked).

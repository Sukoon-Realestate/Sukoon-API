# Input and upload policy worklist

The code already has meaningful private-media, tour and capture validation. Reuse it where the resource policy matches;
do not replace it with an extension check or assume every upload needs the same allowlist. Exact approved formats/limits
must be documented per resource and preserved for supported clients, including native image formats where implemented.

| Surface | Observed implementation | Required sprint result |
|---|---|---|
| Avatar and shared Cloudinary field | Image/base64 paths exist, but arbitrary strings are returned unchanged and can become provider references | Accept actual validated uploads or an owned server-recorded media identity; never trust an arbitrary public ID/URL for attachment or erasure |
| Identity images | Dedicated decode/normalize/private-media and versioned KYC paths exist; HEIF dependency declared | Preserve decoding, privacy and immutable evidence; bound encoded/decoded bytes and pixels; establish ownership and recheck session epoch after locking |
| Listing images | Recoverable upload expects a seekable image, while serializer accepts reference strings | Separate file and reference commands; reject bad types before reservations/I/O; use one locked 25-image capacity policy for cover and gallery |
| Listing video | Ordinary FileField and client duration checks; app-controlled decoded type/size/duration contract incomplete | Approved container/codec/signature, finite byte/pixel/frame/time limits and bounded inspection; verify actual duration rather than trusting the client |
| Portfolio media | JPEG/PNG decode and metadata stripping exist; shared blob ownership/retention graph incomplete | Preserve typed intent/hash/pixel rules; safe retry compensation and retention references across local/remote storage |
| Tour/capture parts | Bounded/checksummed uploads and explicit JPEG/panorama/GLB inspection exist | Preserve parser, checksums, resource/selection membership, fencing and byte gateways; test corrupt/container/path and quota limits |
| Rental/student private evidence | Shared policy supports JPEG/PNG/WebP, PDF, and permitted MP4/QuickTime paths with resource-specific restrictions | Preserve signature/decode checks, PDF inspection, size/duration/page limits and private authorization; fail closed on scanner/inspection failure |
| Chat image/audio/video | Bounded decoding/transcoding and private attachment access exist | One policy across REST/WS send/bind/download; preserve metadata stripping, quotas and current membership checks |
| Chat `kind=file` | Bounded opaque bytes, forced download and nosniff; no approved-type/content inspection policy | Product decision: supported file classes versus deliberately arbitrary opaque download. If inspection is required, quarantine until ready and prevent bind/download before approval |
| Support/evidence corrections | Scoped private storage and upload scanning exist; history expansion/query cost grows | Preserve owner/staff/version access, bounded content validation and scan lifecycle; bound history and batch evidence availability checks |
| Advertising banners | PIL verification/type/size rules exist; one-off fixture repair/fabricated banner code leaks into GET | Enforce stored bytes/hash/type consistency; remove automatic fixture repair and fabricated artwork from request serving |

Do not claim opaque attachments execute on the server: current file downloads force attachment and nosniff. Do not claim
all valid image references are owned merely because Cloudinary can parse them. Do not authorize provider deletion from
an untrusted client-controlled reference.

## Common command schema

For every write family, inventory and validate object/list/scalar shape, required/optional/unknown fields, UUID identity,
strict nonboolean revision/count integers, finite fixed-precision money, accepted enum values, timezone-aware dates,
bounded text/list depth/count, and duplicate nested IDs. Use `validated_data` through the service boundary. Raw
`int(request.data[...])`, `.strip()` on arbitrary values, or model-field coercion is not a complete input contract.

## Required invalid-upload and input cases

- Missing/empty/truncated content, oversized declared and actual bytes, oversized base64, mismatched extension/MIME/signature,
  unsupported container/codec, decompression bombs, huge dimensions/frame counts and nonfinite durations.
- Malformed filenames/path segments, borrowed media IDs, missing ownership, removed/replaced resource, expired intent,
  stale revision, duplicate retry and cover/gallery concurrency at capacity.
- Null/boolean/object/list in scalar fields; invalid UUID/revision/date; NaN/Infinity/overflow money; oversized nested arrays,
  duplicate room/bed/offer IDs and unsupported enum/unknown fields.
- Scanner/provider unavailable, response lost after upload, asset changed before binding, authorization revoked during I/O,
  cleanup concurrent with publication and remote retention. Rejected commands create no ready artifact or stray reservation.

Valid historical client requests keep their documented semantics, or get an explicit coordinated migration/error contract.
This matrix is Sprint 02's implementation checklist, not a claim all listed tests have already run.

## Resource media contract (Sprint 02, 2026-11-09)

Implemented limits as enforced by code. Rows marked *unchanged* were verified, not modified, by Sprint 02.

| Resource | Accepted input | Formats (decoded) | Limits | Rejects / notes |
|---|---|---|---|---|
| Listing cover + gallery (`properties.listing_media.ListingImageField`) | multipart file or `data:image/...;base64,` | JPEG/MPO, PNG, WebP, HEIF/HEIC, AVIF, GIF | 20 MiB encoded (and base64 length), 50 MP decoded, full decode | URL/public-ID strings → 400 before reservation/provider call; BMP/TIFF/HTML/truncated/bomb → 400. Bytes are not re-encoded (EXIF stripping for public listing photos remains a follow-up) |
| Listing capacity (`properties.services.listing_capacity`) | — | — | 25 = stored images + `pending`/`unknown` upload reservations, checked under the listing row lock by cover replacement, gallery reservation and the legacy service | At the cap a new cover is 400 unless `retained_image_ids` frees a slot; a granted reservation is honored on completion |
| Listing video (`ListingVideoField` → `common.private_media_policy.inspect_video_path`) | multipart MP4/QuickTime (`ftyp` signature) | H.264/HEVC/MPEG-4 in mp4/mov | 50 MiB, ≤ 60 s (+0.5 s encoder rounding) decoded by ffprobe + bounded ffmpeg decode, 20 MP frames | Stored `video_duration` is the measured value; inspection tool absent → 503 (fail closed) |
| Avatar | upload/data URI; current-avatar echo only | *unchanged (Sprint 01)* | — | Borrowed references 400 |
| Identity images | *unchanged*: `IdentityImageField` decode → metadata-free JPEG | JPEG/PNG/WebP/GIF/HEIF/AVIF/BMP/TIFF in | 10 MiB | Profile-edit route refuses identity keys (403) |
| Rental/student private evidence | *unchanged*: `private_media_policy.inspect` | JPEG/PNG/WebP, PDF, MP4/MOV (students: no video) | image 5 MiB/20 MP, PDF 25 MiB/500 pages, video 50 MiB/300 s | Video branch now shares `inspect_video_path` with listings (same checks) |
| Portfolio media | *unchanged* | JPEG/PNG, re-encoded | 5 MiB | — |
| Chat image/voice/video | *unchanged*: `group_limits` | JPEG/PNG/WebP; AAC/M4A; MP4 | image 10 MiB/20 MP/2560 edge; voice 10 MiB/1–120 s; video 50 MiB/300 s | — |
| Chat `kind=file` | multipart, checksummed | **any (opaque)** | 25 MiB | **Explicit policy (A5-11), product sign-off pending:** deliberately opaque download, stored privately, served only to current members as `application/octet-stream`, `Content-Disposition: attachment`, `nosniff`, `private, no-store`; never executed, rendered inline or inspected. No quarantine because no inspection is required by this policy. Spoofed `.html`/`.svg`/`.exe` cases are pinned in `chat/tests/test_rich_attachments.py` |
| Support attachments | *unchanged* | scanned private storage | 5 MiB each, 3 per ticket | — |
| Tour/capture parts | *unchanged* | JPEG/panorama/GLB | 1–8 MiB parts, 30 MiB capture asset, 250 MiB remote | — |
| Advertising banners | *unchanged* | PIL-verified | 10 MiB | Fixture repair/fabricated artwork removal is Sprint 11 |

### Command schema policy (applies to every Sprint 02 typed command)

Shared fields live in `core_apps/common/command_fields.py`; rental bodies in
`core_apps/features/rental_serializers_parts/command_serializers.py`; inventory in
`core_apps/properties/rental_inventory_parts/inventory_schema.py`.

- **Revisions/counts:** integers; canonical digit strings (`"3"`) stay accepted for historical form clients; `true`,
  `null`, floats, lists, objects, negatives → 400. Missing revision keeps its historical default where one existed
  (`0`), so stale commands still conflict with 409.
- **Text:** strings only (numbers/booleans no longer coerced), NUL rejected, bounded by the model column
  (notes/reasons/descriptions 4,000, titles 160/200/255).
- **Identifiers:** UUID text for object IDs; request keys are non-blank text ≤ 100 (the receipt column) — UUIDs are
  required only where they already were (checkout, refunds).
- **Money:** finite, non-negative, ≤ 10 whole digits and 2 decimals; stored text (`"5000.00"`) is kept verbatim.
- **Date-times:** ISO-8601 with an explicit offset; dates ISO `YYYY-MM-DD`.
- **Free JSON** (handover condition/keys/meters/inventory): declared top-level types only, depth ≤ 4, ≤ 200 members
  per container, ≤ 16 KiB encoded, finite numbers.
- **Inventory:** ≤ 50 rooms, 20 beds per room, 100 offers, 256 KiB; duplicate persisted room/bed/offer IDs → 400.
- **Unknown fields:** ignored by commands (DRF default) but still part of the stored replay fingerprint; inventory
  extension keys (`media_ids`, `shared_media_ids`, `bathroom_access`, …) are preserved, bounded.
- **Non-object bodies** (JSON array/string/number) → 400.
- **Session claims** are rechecked after the command's domain lock (`common/command_authority.recheck_session`), so
  a session revoked while a command waited cannot complete it (401, no writes).

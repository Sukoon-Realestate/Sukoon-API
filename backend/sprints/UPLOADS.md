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

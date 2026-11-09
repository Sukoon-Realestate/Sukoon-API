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

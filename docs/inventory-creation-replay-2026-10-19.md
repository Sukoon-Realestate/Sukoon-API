# Stable inventory creation retries

An identical property-creation request containing new rooms and offers previously returned HTTP 409 when retried with its original `Idempotency-Key`. Inventory validation generated new UUIDs before the operation fingerprint was compared. Those server-generated result identities made the same command appear different. Both JSON and multipart requests reproduced the failure.

The fingerprint now uses the validated input inventory command, before server-generated result identities, while retaining the existing normalization of the other property fields. The first successful operation still assigns canonical room/offer IDs. An identical retry returns that original HTTP 201 response and the same IDs; a changed price under the same key remains rejected. No migration or new financial behavior is introduced.

Validation: two regression cases failed before the correction. After the correction, 66 focused PostgreSQL tests passed, covering both encodings, one-property persistence, changed-payload rejection, existing inventory validation, property endpoints and visit-offer snapshots. Tests used an isolated copy of commit `61ac71a` plus this change, not the unrelated pending identity/document migrations in the working tree.

Existing receipts created under the old inventory fingerprint must be reconciled through `POST /api/v1/properties/operation-recovery/` with the original operation key. Do not create a replacement key merely because a historical replay conflicts. This release does not rewrite historical receipts.

This is source/local verification. Deployed results are recorded separately in the app repository's deployment and capability work log.

# Identity media storage and access

Identity front/back/selfie uploads use Cloudinary `authenticated` image delivery. Ordinary public listing and avatar media keep their existing behavior. The registration serializer accepts actual multipart images or bounded base64 image data; it rejects supplied URLs/public IDs. Maximum decoded size is 10 MiB; accepted formats are JPEG, PNG, WebP and GIF.

The current user's profile exposes an account-bound API resource with a canonical-reference version hash. The endpoint checks the active authenticated user, field and version before fetching bytes. KYC reviewers use `/api/v1/admin/kyc/{submission_id}/media/{field}/`, after current reviewer authorization. That endpoint reads the immutable submission snapshot, not a later profile replacement. Both byte paths use no-store responses and do not redirect to a provider URL. The React review screen fetches with the current session, aborts interrupted reads and revokes temporary object URLs. These controls cannot retract copies already downloaded before protection.

New submission snapshots contain the canonical provider reference, not a public URL. Existing snapshots/digests and verification decisions must not be rewritten to manufacture approval. Missing legacy protection is an unavailable document, never permission to fall back to public delivery.

## Historical conversion

1. Retain a verified encrypted database backup outside the running service. Restore it independently before conversion where feasible.
2. Create an owner-only persistent working directory and run `python manage.py protect_identity_media --manifest /private/path/identity-conversion.json`. This audits without provider mutation. Retain/review the private manifest outside the ephemeral deployment instance before applying.
3. Review blocked rows. Any existing versioned KYC snapshot or reuse in another Cloudinary model field blocks automatic conversion. Those cases require a separate evidence-preserving plan.
4. Run the same command with `--apply`. It checkpoints the original provider asset identity, converts delivery to `authenticated` with CDN invalidation, verifies the exact provider asset and transactionally updates unchanged profile references. It does not alter national IDs, verification flags, consent, contracts or money.
5. If a provider response is lost, retain the manifest and rerun the original command. It reconciles the authenticated target before issuing another rename. Never replace an unknown result with a new operation or public upload.
6. Recheck old original/versionless/derived URLs anonymously using HEAD and test account-bound/reviewer byte access. Record response/cache metadata without copying private image contents into reports. CDN invalidation may be delayed; a successful provider rename is not proof that every earlier cached URL is already inaccessible.
7. Retain the completed manifest privately. A rollback must preserve private delivery; it must not republish identity proofs.

Provider behavior: [Cloudinary access control](https://cloudinary.com/documentation/control_access_to_media) distinguishes authenticated originals/derivatives from private-original-only delivery. [The upload API reference](https://cloudinary.com/documentation/image_upload_api_reference) documents `rename`, `to_type` and `invalidate`.

## Administration connection

Both Next.js variants support a server-side `SOKOUN_API_PROXY_URL` origin, with `NEXT_PUBLIC_API_URL` empty for same-origin browser requests. API paths bypass locale redirects, preserve Django's trailing slash and never require weakening production CORS. `NEXT_PUBLIC_ENABLE_BACKEND=true` selects real responses; demo mode remains explicit. The proxy target must be an HTTP(S) origin without embedded credentials, path, query or fragment.

## Verification boundaries

`profiles/tests/test_identity_media.py` checks account/role separation, no-store proxy behavior, upload restrictions, protected provider namespace, interrupted conversion reconciliation, public-avatar reuse blocking and deletion namespace. Its provider calls are mocked component checks. Real provider conversion, anonymous CDN denial and authorized browser rendering require separate identified-environment evidence. Provider deletion remains best effort under the existing account-cleanup implementation; no retention/legal policy is introduced here.

# Sprint 01 — Close security and data-preservation gaps

**Outcome:** legacy aliases, account/media lifecycles and communication revisions cannot bypass canonical policies.
**Owners:** identity, property/tour, communication and admin maintainers; security reviewer.
**Evidence:** A1-01…A1-05, A1-08; A2-01/A2-02; A3-01; A4-02; A5-01/A5-02/A5-03; A6-01/A6-10.

## Stories

1. **Media provenance and erasure:** prevent arbitrary avatar references from becoming owned assets or deletion intents.
   Audit existing references non-destructively. Protect all live portfolio blob owners in local/remote cleanup; define
   retention for removed and historical evidence. Compensate losing concurrent upload writes without retaining all orphans.
2. **Account identity:** close all inherited Djoser deletion aliases; route deletion through reviewed closure. Prevent social
   preregistration/adoption from preserving attacker-controlled passwords/sessions. Make OTP attempts/consumption/cooldown
   atomic. Revalidate original session epoch after locked identity submission.
3. **One publication/moderation policy:** enforce it under visit-creation locks and on tour availability/session/manifest/
   byte paths. Preserve separately authorized historical/reviewer/owner previews. Route legacy moderation through the
   canonical independent-review, revision, receipt and event service.
4. **Financial privacy:** agree on retained-record rights after personal access revocation; apply one policy to invoice,
   payment and new checkout commands without blocking necessary original-operation reconciliation.
5. **Communication:** enqueue moderation for the actual edited event/revision; apply typed text/quota checks to legacy and
   rich REST/WS sends. Replace unnecessary participant email projection with the approved public identity contract.
6. **Runtime hardening:** assess cookie-origin/CSRF threat conditions and coordinate required browser proof with clients;
   preserve bearer clients and signed provider callbacks. Select a supported Django/dependency stack and audit the lock.
   Verify deployment HTTPS/HSTS/session/CSRF/origin settings rather than applying synthetic warnings blindly.

## Acceptance

- Borrowed-media closure with mocked providers cannot destroy another asset. Cleanup retains active portfolio assets
  older than seven days locally and remotely while still reclaiming true orphans.
- Every self/staff deletion alias, including router/format variants, preserves closure obligations. Social adoption revokes
  untrusted prior credentials. Parallel OTP and in-flight revoked identity submissions fail correctly.
- Hidden/retired/blocked/closure-pending properties cannot start visits or expose public tour bytes; existing grants are
  denied immediately. Withdrawing closure restores only otherwise eligible publication.
- All moderation aliases reject self-review/stale/conflicting commands and emit one canonical decision/event.
- Edited messages receive exactly one input per eligible revision; bad legacy socket inputs do not kill the connection or
  bypass quotas. Chat projections follow the agreed contact-disclosure policy.
- Financial revocation tests cover lists/details/new commands and necessary reconciliation separately.
- Supported framework/runtime audit and focused security tests pass; unresolved provider/deployed checks remain explicit.

**Delivery:** split independent fixes into small PRs with source-triggered regression cases. Do not combine the entire
dependency upgrade and mechanical CBV migration with these behavior changes.

# Visit Phone Disclosure — Backend Implementation Plan

Date: 2026-10-08

Status: Implemented and verified locally. See `VISIT_PHONE_DISCLOSURE_BACKEND_RETURN_HANDOFF.md` for the delivered API contract and rollout notes.

## Goal

Keep owner and tenant phone numbers private until the owner accepts a visit, then disclose the current stored counterpart number reciprocally and consistently across authorized visit, property-detail, and direct-conversation reads.

## Policy

- Persist `PropertyVisit.accepted_at` as the historical contact grant.
- Current `confirmed` visits also qualify for compatibility; the migration backfills their `accepted_at` value.
- Cancellation after acceptance retains disclosure. Cancellation/rejection before acceptance does not grant it.
- A qualifying visit is always between the property owner and that visit's tenant.
- Property detail requires a qualifying visit for that exact property.
- Direct chat requires any qualifying accepted visit between the two conversation participants.
- Guests, unrelated accounts, public feeds, message sender payloads, and push notifications never receive raw phone numbers.
- Account blocking is not currently modeled. Inactive accounts do not qualify; a future block policy must be added to the shared authorization helper rather than individual serializers.

## Implementation steps

1. Add and migrate `PropertyVisit.accepted_at`, backfilling existing confirmed visits.
2. Add a shared contact-disclosure module that computes authorization and returns consistent localized contact fields.
3. Make owner acceptance lock the visit, set status and `accepted_at` atomically, remain idempotent, and create one notification with push dispatched after commit.
4. Add `conversation_id` to the acceptance notification when the pair already has a direct conversation; never include phone numbers.
5. Apply the shared policy to owner and tenant visit list/detail serializers, legacy visit reads, and property detail.
6. Add phone metadata only to conversation-level `other_participant`; do not add it to generic participant/message serializers.
7. Add participant-only `GET /api/v1/chat/conversations/{id}/`.
8. Test pending/accepted/cancelled history, repeated acceptance, property scoping, conversation list/create/detail, third-party privacy, missing/updated phones, notification payloads, and Arabic/English notices.
9. Run migration checks, focused lint, focused tests, and the complete backend suite.

## Rollout

Apply the migration to the target PostgreSQL database, verify with three real accounts and cross-device push/contact refresh, then return the implementation handoff to mobile. Mobile should not treat fixture tests alone as deployed-server evidence.

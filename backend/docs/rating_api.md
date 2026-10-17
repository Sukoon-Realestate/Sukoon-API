# Sokoun rating API

Implemented routes are in `Sukoon-API/backend/core_apps/features/reputation_urls.py` and `core_apps/admin_api/urls.py`. Mobile base: **`/api/v1/features/v1/`**. Do not remove or repeat `features/v1`.

## Transport and authorization

Use the existing account authentication and `Accept-Language: ar` or `en`. UUIDs in routes/DTOs are public IDs, never the models’ internal integer primary keys. All new review responses prohibit HTTP caching (`Cache-Control: private, no-store`). Account and anonymous throttles remain active; mutation throttling also limits an account/resource/operation context to 120/hour.

All JSON responses have exactly two top-level keys: `message` and `data`. Successful collections put the item array directly in `data`; pagination uses `X-Page`, `X-Per-Page`, `X-Total-Count`, `X-Total-Pages`, `X-Next-Page`, `X-Previous-Page`. Request pagination is `page`/`page_size`. The shared Flutter envelope reader adapts these headers for `AppPagify`. The retained legacy property-review endpoint still has a `data.summary` plus `data.results` object.

Errors retain the existing HTTP status, localized message and **`X-App-Error-Code` header**; `data` is null. No new top-level `code` or `success` field is introduced. Unknown/unauthorized private IDs normally return 404. Eligibility and revision conflicts return 409; invalid scores/text/payloads return 400; unavailable permissions return 403. A 429 includes the existing retry policy.

## Routes

| Method and relative route | Access and result |
| --- | --- |
| GET `reviews/capabilities/` | Authenticated; server flag, policy/schema, freshness and capabilities. Corporate and portfolio review capabilities follow the server flag; source-specific authority remains mandatory. |
| GET `reviews/opportunities/` | Own opportunities; optional authorized `lease_id` or `visit_id` filter. Source-filtered reads reconcile that source when enabled. A `company_id` filter returns only opportunities covered by current explicit company review authority. |
| GET `reviews/opportunities/{id}/` | Reviewer only; frozen targets, audience, versions, deadline, state and allowed actions. |
| PATCH `reviews/opportunities/{id}/` | Reviewer; idempotent reminder preference, with `request_key`, `expected_revision`, `reminders_enabled`. Preference does not reopen/change the submission window. |
| GET/PUT/DELETE `reviews/opportunities/{id}/draft/` | Reviewer only; revisioned private server draft. PUT requires `request_key`, draft `expected_revision` (0 initially) and `payload`. DELETE requires request key and current draft revision. |
| POST `reviews/opportunities/{id}/submit/` | Reviewer and current source eligibility; atomic final submission of selected sections. Returns 201 and receipt. |
| GET `reviews/operations/by-key/{request_key}/` | Same actor only. Returns a confirmed receipt or `unknown`. Absence is not proof of final failure. |
| GET `reviews/mine/` | Current reviewer’s sections, including private content/gate status. |
| GET `reviews/received/` | Released visible sections about the current person and their historical property responsibility; suppressed content may expose only decision metadata after release. |
| GET `reviews/subjects/{kind}/{id}/summary/` | Public kinds allow anonymous reads; private kinds require the subject’s own account. No client-selected audience. |
| GET `reviews/subjects/{kind}/{id}/` | Same visibility rule, published collection, optional integer `rating=1..5`. |
| GET `reviews/{id}/` | Public or authorized participant projection. No access to the other party’s pre-release submission. |
| POST `reviews/{id}/reply/` | Visible section’s historical subject only; one immutable nonempty plain-text reply. |
| POST `reviews/{id}/withdraw/` | Section author; removes contribution without reopening eligibility. |
| POST `reviews/replies/{id}/withdraw/` | Reply author, including a pending reply. |
| POST `reviews/{id}/reports/` | Authenticated reader of visible content; deduplicated by section, reporter and reason. |
| POST `reviews/moderation-decisions/{id}/appeals/` | Authorized participant, within fourteen days of their notice. One open appeal per decision; subsequent information uses the open appeal revision. |
| GET `reviews/cases/{id}/` | Reporter, appellant or eligibility-request opener only; state/revision/resolution. |
| POST `reviews/eligibility-requests/` | Authorized personal visit/tenancy participant; investigation case without invented source evidence. |
| GET `reputation-grants/recipients/` | Known counterpart accounts from the caller’s leases or viewings; public ID/name only. |
| GET/POST `reputation-grants/` | Own outgoing and incoming grants / explicitly create a private role grant. |
| POST `reputation-grants/{id}/revoke/` | Grant owner with revision and operation key. |
| GET `reputation-grants/{id}/summary/` | Exact named recipient, unexpired and unrevoked. Aggregates only. |

Public kinds: `property_visit`, `property_stay`, `person_landlord`, `organization_landlord`. Private kinds: `person_tenant`, `person_housemate`, `organization_renter`. Company history is restricted per binding by explicit `can_view_reputation` authority; company membership alone grants no personal employee history.

## Example opportunity

Illustrative UUIDs below are placeholders, not live records. Server-derived target identities are intentionally absent from the client-facing target list.

```json
{
  "message": "Request completed successfully.",
  "data": {
    "id": "f02086fe-c3d2-4d73-a80d-000000000001",
    "context_type": "tenancy",
    "state": "open",
    "revision": 1,
    "policy_version": "rating-v1",
    "criteria_schema_version": "rating-criteria-v1",
    "opens_at": "2026-10-17T12:00:00+00:00",
    "closes_at": "2026-11-16T12:00:00+00:00",
    "release_mode": "mutual_or_deadline",
    "gate_state": "waiting",
    "reviewer": {"kind": "person", "role": "tenant"},
    "allowed_actions": ["save_draft", "submit"],
    "blocking_reason_codes": [],
    "reminders_enabled": true,
    "allowed_targets": [
      {
        "key": "landlord",
        "kind": "person_landlord",
        "visibility": "public_after_release",
        "label": "Landlord",
        "criteria": [{"code": "communication", "label": "Communication"}],
        "tag_codes": ["clear_communication"],
        "tags": [{"code": "clear_communication", "label": "Clear communication"}]
      }
    ]
  }
}
```

The real target schema contains the full applicable criteria. Fetch it; do not infer permissions from a role label, cached capability or displayed profile category.

## Final submission and recovery

```json
{
  "request_key": "eb355d7e-630a-4941-815b-000000000002",
  "expected_revision": 1,
  "policy_version": "rating-v1",
  "criteria_schema_version": "rating-criteria-v1",
  "sections": [
    {
      "target_key": "landlord",
      "overall_score": 4,
      "criteria": {"communication": 5, "maintenance_response": null},
      "comment": "Clear communication throughout the stay.",
      "tag_codes": ["clear_communication"]
    }
  ]
}
```

At least one selected section is required. Target keys must belong to this opportunity. Scores must be actual integers 1–5; booleans, floats, zero and unknown criteria/tags fail. Criteria are nullable and do not calculate the overall score. Omitted sections cannot be added later. Comments are normalized plain text, at most 1500 Unicode code points; links, HTML, phone/email contacts and control characters are rejected. Replies have a 1000-code-point limit.

A receipt contains `id`, `opportunity_id`, `request_key`, `section_ids`, `state: "succeeded"`, `content_state`, `gate_state`, `received_at` and `revision`. This confirms receipt, not moderation/publication. The same key/body returns the same receipt. A changed payload with that key returns `idempotency_payload_mismatch`. A different key on an already submitted opportunity returns its canonical receipt with `already_submitted: true` and `canonical_request_key`; it never changes the prior score.

Operation lookup returns either:

```json
{"message":"Request completed successfully.","data":{"state":"unknown","request_key":"eb355d7e-630a-4941-815b-000000000002"}}
```

or `data: {"state":"succeeded","request_key":"...","receipt":{...}}`. Keep the original key and exact body until a confirmed result. Do not generate another operation because of a timeout, backgrounding or connectivity return.

## Other command bodies

- Reply: `request_key`, section `expected_revision`, `comment`.
- Section/reply withdrawal and grant revocation: `request_key`, resource `expected_revision`.
- Report: `request_key`, section `expected_revision`, `reason_code`, optional `detail`.
- Appeal: `request_key`, `detail`; add `expected_revision` when adding information to an existing open appeal.
- Eligibility: `request_key`, `source_kind` (`viewing` or `tenancy`), authorized public `source_id`, optional `detail`.
- Grant: `request_key`, `subject_kind` (`person_tenant` or `person_housemate`), `recipient_id`, nonempty `purpose`, optional `days` (default 7; 1–30). No comments or complete private history are granted.

Report reasons: `personal_information`, `abuse_or_threat`, `discrimination`, `outside_experience`, `fake_experience`, `extortion`, `prohibited_content`. Reports return a case ID/state/revision; reporting does not remove the score.

## Summaries and projections

`average` is nullable when no eligible votes exist. `review_count` counts sections; `distinct_experience_count` counts canonical cases. `distribution` contains keys `"1"` through `"5"`. Each included criterion has `average`, `answered_count` and localized `label`. `limited_sample`, `aggregation_version` and `computed_at` accompany the summary. Unanswered criteria are excluded from their denominators; `legacy_unverified` rows are excluded from verified averages.

A public section exposes ID, subject kind/label, score, nullable criteria, safe text/tags, month, verification basis and audience. It does not expose reviewer identities, precise occupancy dates, room/contract references or a person’s private profile link. Participant data can additionally contain `content_state`, `gate_state`, own opportunity ID, allowed actions, decision reasons and appeal availability. If content is suppressed, its target receives metadata only after the gate; scores/text remain absent. A reply author may see and withdraw their own pending reply.

A granted summary uses the same aggregate shape and does not include the underlying section list. `grant_revoked` and `grant_expired` are checked on every read.

## Operator API

Existing admin namespace: **`/api/v1/admin/`**. These endpoints are not authorized merely by a mobile owner role.

| Route | Contract |
| --- | --- |
| GET `reviews/?reason=...` | Explicit `features.moderate_reviews`; pending/held sections or replies. Audits each projected item; rejects conflicts. |
| POST `reviews/{id}/decisions/` | `request_key`, `expected_revision`, `action`, nonempty `reason`; optional `reply_id` or deletion-only `redacted_comment`. |
| GET `review-cases/?kind=reports\|appeals\|eligibility&reason=...` | Audited open-case queue; eligibility permission is separate; parties/conflicted reviewers are excluded. |
| POST `review-cases/{id}/resolve/` | `request_key`, `expected_revision`, `reason`; records resolution without creating evidence or changing a score. |
| POST `review-appeals/{id}/resolve/` | Independent authorized moderator; `request_key`, `expected_revision`, `reason`, optional `outcome`: `uphold`, `restore`, `remove`, `reject`, `hold`. |

Moderation actions: `approve`, `keep`, `hold`, `reject`, `remove`, `restore`, `redact`, `revoke_eligibility`. Eligibility revocation additionally requires `features.review_eligibility`. Withdrawn content cannot be restored through moderation. Moderation decisions are immutable; scores are never rewritten.

## Errors and legacy compatibility

Examples of stable `X-App-Error-Code` values: `review_not_eligible`, `experience_not_confirmed`, `occupancy_not_ended`, `co_living_overlap_insufficient`, `review_window_closed`, `revision_conflict`, `idempotency_payload_mismatch`, `invalid_review_target`, `unsupported_criteria`, `invalid_review_text`, `self_review_forbidden`, `conflict_of_interest`, `capability_unavailable`, `client_update_required`, `grant_expired`, `grant_revoked`.

Example conflict:

```http
HTTP/1.1 409 Conflict
X-App-Error-Code: review_window_closed
Cache-Control: private, no-store
Content-Type: application/json
```

```json
{"message":"The review window has closed.","data":null}
```

`leases/{lease_id}/reviews/` keeps its historical authorized GET; its old POST requires a client update. The property visit-review POST similarly requires an update. The old public property-review list uses the safe viewing projection and preserves unimported legacy rows with `legacy_unverified`, without promoting their scores to verified stays or landlord reputation.


## Confirmed experience and portfolio routes

All mutations below require a durable `request_key`; updates/confirmations require the current `expected_revision`. Sources are selected by public UUIDs from authorized reads. No form supplies review subject IDs or eligibility outcomes.

| Method and route | Contract |
| --- | --- |
| GET/POST `reviews/company-bindings/` | Authorized bindings, optionally `company_id`; propose `lease_id`, renter/landlord company UUID and renter `booking_id`. Signed canonical document and approved booking must match. |
| GET/POST `reviews/company-bindings/{id}/` | Read current source/actions; confirm one `role`: `lease_owner`, `lease_tenant`, `renter_company`, `landlord_company`. All required roles must confirm; company roles need current verified signing authority. |
| GET/POST `reviews/company-bindings/{id}/authorities/` | Admin-scoped member list (`company_id`) and explicit grant/revoke: `membership_id`, `is_active`, `can_submit`, `can_view_reputation`. New authority starts at expected revision 0. |
| GET/POST `reviews/company-bindings/{id}/assignments/` | List authorized residents; create with `employee_id`, `starts_on`, `ends_on`. Assignment alone generates no review. |
| GET `reviews/employee-assignments/` | Current employee's linked occupancy records. |
| GET/POST `reviews/employee-assignments/{id}/` | Read evidence or propose `kind=arrival|departure`, `possession_on` and assignment revision. Dates are actual, never future. |
| POST `reviews/occupancy-confirmations/{id}/confirm/` | Confirm `role=employee|landlord` with confirmation revision. The landlord must be responsible at the recorded date; a lessor company uses a verified signer. |
| GET/POST `reviews/ownership-transitions/` | Participant list; propose `lease_id`, `effective_on`, `evidence_id`. Evidence must already be safe and linked to the lease, and the new current property owner verified. |
| GET/POST `reviews/ownership-transitions/{id}/` | Historical previous/new owner and tenant confirm independently. All three are required. |
| GET `reviews/experience-choices/` | Paginated authorized `kind=leases|bookings|employees|evidence`; company and lease filters required where applicable. |
| GET `reviews/portfolios/{building|complex}/{id}/summary/` | Public live aggregate from original occupancy ancestry, with `distinct_unit_count`, `distinct_experience_count`, `archived` and name. |
| GET `reviews/portfolios/{building|complex}/{id}/` | Paginated eligible published property-stay sections; optional rating filter. |
| GET `reviews/properties/{id}/portfolios/` | Public property links: kind, id, name and `historical`; no private portfolio fields. |

`reviews/mine/`, `reviews/received/` and `reviews/opportunities/` accept `company_id`. Corporate opportunity DTOs identify `reviewer.kind=company` with company id/name, while acting-user identity remains private. Shared draft PUTs use the draft revision, not opportunity revision. A delegate change does not reset either the draft or the ballot. Employee opportunities use `release_mode=deadline`.

Under the existing admin API:

- POST `review-recovery/`: `source_kind=viewing|tenancy|co_living|employee_occupancy`, `source_id`, `peer_lease_id` for co-living, `incident_reference`, `reason`, ISO-aware `outage_started_at`, `outage_ended_at`, `request_key`. The source's trusted eligibility timestamp must lie within the outage. Requires independent `features.review_eligibility` authority.
- POST `review-windows/{case_id}/extend/`: the same incident evidence, `expected_revision`, `extension_days` from 1 to 30. One extension applies to the complete case before disclosure. Expired or released windows are rejected.

The recovery CLI accepts the identical JSON contract through `recover_review_outage --operator <user UUID> --request-file <path>`. `backfill_review_ancestry` only copies original historical snapshots and reports sources that remain unknown.

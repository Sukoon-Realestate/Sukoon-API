# Student housing: contracts and operations

Local implementation, 16 October 2026. This is not deployment or live-provider
evidence. The companion Flutter implementation and acceptance report is
`darak-app/docs/STUDENT_HOUSING_IMPLEMENTATION.md`.

## Canonical resources

`AcademicHousingPlan` is an individual plan or an optional context on an existing
`HousingGroup`. It does not create another group, membership, invitation,
conversation, shortlist, voting system, cost proposal, viewing or application.
Academic group processes use the existing group endpoints and `GroupProcess` IDs.
Manual group archive/unarchive remains retired. A group can plan several periods
while its current tenancy continues.

Plans reference an explicit subset of the existing membership roster, including
membership-period identity. A coordinator organizes requirements; only each
participant can submit their requirements and consent. Social membership,
academic participation, application consent, signatures and tenancy participation
remain distinct. Leaving a group revokes its private academic reads and recovery
receipts under the same current-membership rules.

Membership periods use **group revision**, independently of roster revision.
`access_group_revision` records the actual group revision observed by a plan.
An older group can have many edits/votes before someone joins; that person is
eligible for new plans without accidentally restoring access to periods before
their current membership. A regression covers group revision 45 / roster revision 2
and subsequent leave/rejoin.

New records are StudentProfile, University, Campus, AcademicHousingPlan,
AcademicPlanParticipant, AcademicRequirementRevision, StudentOfferPolicy and
SharedLivingAgreement. Student verification uses existing private RentalEvidence,
RentalVerificationClaim, RentalOperationalCase and audit events. Shared/exam
arrangements use existing RentalConsentRecord. Family summaries use the common
RentalSummaryGrant; they do not create a payer, guarantor or representative role.

## Transport and command identity

All routes below are relative to `/api/v1/features/v1/`. Authenticated controlled
successes have exactly `message` (nonempty string) and `data`. Collections retain
the existing pagination transport headers. Sensitive responses are private,
`no-store`. HTTP tests assert the actual rendered envelope, not only DRF's internal
`.data` value. The shared error renderer and stable error codes are unchanged.

JSON commands include `request_key` (UUID) and `expected_revision` (integer).
Creates use revision 0. Reuse the **same** request key and unchanged payload when
recovering an uncertain result through `rental-operations/<request_key>/` with the
original subject. A confirmed command returns `data.resource` and
`data.operation_receipt`. Current object authorization still applies to replays.
Unknown results do not authorize another signature, charge, consent or upload.

`revision` serializes commands. `requirements_revision` identifies the immutable
requirements/roster snapshot. Recording one person's approval increments the
command revision without invalidating another person's approval of the same
requirements. A material requirements or roster change creates another immutable
version and requires review again. `digest` binds participant consent;
`publication_preview.preview_digest` binds publication to the anonymous projection
shown to owners. These are different digests.

Shortlist votes/comments remain on the same canonical item and endpoints. Optional
`academic_plan_id`/`academic_revision` scope them to one period and requirements
version. Group payloads expose redacted `academic_decisions` with counts, the
reader's vote, comments and current/history status; individual voter maps are not
exposed. Earlier votes never count toward a later plan. Removing an academic
shortlist association does not delete another period's decisions or an existing
application. Ordinary general-group votes remain separate and unchanged.

Accommodation dates use `YYYY-MM-DD`, inclusive start and exclusive end, using the
existing business-date/timezone helpers. Expiry and case deadlines are timestamps.
Period labels never generate dates. Supported structured agreements remain monthly
EGP; no new semester invoice, implicit proration or automatic multiplication of
per-person affordability is introduced.

## Routes

| Method and route | Behavior / authorization |
| --- | --- |
| GET/POST `student-profile/` | Own voluntary profile; account verification and enrollment are separate |
| GET `campuses/?search=...` | Active catalog; bilingual institution/campus, maintained source/check date; unknown coordinates remain null |
| GET/POST `academic-plans/` | Own/current accessible plans; optional `group_id` collection filter; group creation requires current administrator |
| GET `academic-plans/<id>/` | Actor-specific participant requirements, actions and blockers |
| GET `academic-plans/<id>/history/` | Immutable dates, budgets, digest and only the reader's historical private requirements |
| POST `academic-plans/<id>/edit/` | New requirements revision; never edits a submitted request/application/lease |
| POST `academic-plans/<id>/requirements/` | Only the actor's requirements, affordability and chosen owner disclosures |
| POST `academic-plans/<id>/review/` | Explicit individual consent with current digest |
| POST `academic-plans/<id>/withdraw/` | Withdraw academic participation; no group removal, cost transfer or tenancy termination |
| GET `academic-plans/<id>/publication-preview/` | Exact anonymous owner projection and publication digest |
| POST `academic-plans/<id>/publish/` | Creates the existing HousingRequest after every intended participant reviews |
| POST `academic-plans/<id>/complete/` | Complete this planning period; group and tenancy history remain |
| POST `academic-plans/<id>/link_lease/` | Link actor's own existing lease; no booking created |
| POST `academic-plans/<id>/check_in/` | Actionable existing operations case for actor's linked confirmed tenancy |
| GET/POST `academic-plans/<id>/arrangements/` | Versioned shared-living/exam proposal for intended residents |
| GET `student-arrangements/<id>/` | Current decisions and explicit social-only effect |
| POST `student-arrangements/<id>/decide/` | Actor accepts or requests discussion; no proxy approval |
| POST `student-arrangements/<id>/revise/` | New terms version; old individual approvals retained as history |
| GET/POST `properties/<id>/student-policies/` | Read published policies; owner saves immutable replacement for exact canonical offer/revision |
| GET `student-evidence/` | Own private evidence metadata |
| POST `student-evidence/upload/` | Own private evidence, stable UUID + SHA256 + PNG, maximum 5 MiB, same durable worker |
| GET `student-evidence/<id>/metadata/` | Own upload recovery; pending/safe/unsafe/failed distinguished |
| GET `student-evidence/<id>/` | Safe bytes only; subject or authorized KYC reviewer |
| GET `operations/student-verifications/` | KYC queue; private evidence and own operational case context |
| POST `operations/student-verifications/<profile_id>/review/` | KYC reviewer creates expiring admission/enrollment claim and records auditable case outcome |
| GET `leases/<id>/summary-sharing-options/` | Own exact eligible invoices and receipts |
| GET/POST `leases/<id>/summary-grants/` | Student grants explicit booking/invoice/receipt scopes to an existing registered recipient for at most 30 days |
| GET `shared-rental-summaries/` | Recipient's current, redacted grants only |
| POST `rental-summary-grants/<id>/revoke/` | Grantor revokes access, including after recipient previously read it |

Read the strict serializers in `backend/core_apps/features/student_serializers.py`
for optional-field limits. Unknown command fields are rejected. New commands use
the existing fresh capability checks, receipts and transactional mutation wrapper.
Group/plan locks use a deterministic order. Evidence provider I/O runs outside
the database transaction, with fresh state checks before recording the result.

## Plan example

Illustrative UUIDs below must be replaced with actual authorized IDs; these are
not seeded production data. Omitting `group_id` creates an individual plan.

```json
{
  "request_key": "c8799693-33dc-4eed-a552-4545ca936b13",
  "expected_revision": 0,
  "group_id": "da089ec4-ae8b-4256-84de-98719c339214",
  "label": "First semester 2027",
  "period_kind": "semester",
  "starts_on": "2027-09-01",
  "ends_on_exclusive": "2028-01-20",
  "budget_basis": "per_person",
  "criteria": {
    "city_id": "b74ea874-dcb2-4557-a650-a8840f6f9f9a",
    "rental_scope": "room_group",
    "price_period": "monthly",
    "budget_min": {"amount_minor": 150000, "currency": "EGP"},
    "budget_max": {"amount_minor": 350000, "currency": "EGP"}
  },
  "requirements": {
    "campus_ids": [],
    "commute_mode": "transit",
    "max_commute_minutes": 40,
    "study_space": "A desk for each intended occupant",
    "internet": "Disclose service and usage limits",
    "summer_intention": "undecided",
    "admission_contingency": false
  },
  "participant_ids": ["68fb5b26-89d7-4df0-8c43-c3327927a493"]
}
```

`period_kind`: semester, academic_year, year_and_summer, summer, internship, other.
`budget_basis`: per_person or whole_group. Both budget bounds remain required by
existing criteria. `participant_ids` is a chosen membership subset, not capacity.
`previous_plan_id` links continuity; `current_lease_id` references the actor's own
tenancy without changing it. Campus destinations and affordability remain per
participant; private internship/preferences do not appear in another person's
history. Conflicting disclosed campuses/budgets are discussion points, not a score.

Participant requirement commands contain `requirements`, `budget_min`,
`budget_max`, and explicit `owner_disclosures` chosen from campuses, affordability,
study_requirements. Review/publish/withdraw commands contain `consent` and `digest`.
Consent is never restored as checked from a draft. Shared coordinator requirements
are visible in the review and publication preview. Owner projections omit member
identities, documents, group conversation and detailed timetables.

## Existing demand, applications and tenancy progression

Publication writes HousingRequest.academic_plan/revision/snapshot. Owner demand
can use `student=true&matching_inventory=true`: the inventory filter means owned,
verified properties in the request's city, **not** a full fit/capacity/availability
guarantee. Creating HousingOffer still resolves real property/offer/room/bed
identity, checks dates/availability and snapshots the student policy. An obsolete
plan, policy or source response becomes `review_required`, with no acceptance
actions. Selecting a response never signs, charges or reserves.

Group selection links the exact HousingOffer ID/revision to the same group's
shortlist. Academic group proposal/application commands add `academic_plan_id`
and `academic_revision` to existing endpoints. Cost proposals contain only the
consenting intended subset; existing participant approvals remain mandatory.
Ordinary group behavior is unchanged. The board can filter linked shortlist and
process records by plan while keeping the original Members, Chat and other tabs.

Individual `rental-interests/` accepts optional `academic_plan_id`,
`academic_revision`, `source_housing_offer_id`, `source_housing_offer_revision`.
Server validation preserves exact plan dates and the selected response snapshot,
including `desired_end`. Owner proposal/lease review still controls actual legal
terms. Academic group applications may use exact end dates after the supported
minimum monthly term; a semester label cannot change the monthly billing policy.

Existing independent GroupBookingProposal completion is supported. Each person
gets their own exact allocation, lease, signature and invoice/payment operation.
One person's failure does not end another completed independent booking. The
proposal remains partial when only three of four complete. **Conditional bundles,
joint signing/payment and automatic compensation remain disabled.** They need
approved obligations/partial-failure policy and real provider compensation support;
an approved group application alone is not a booking.

Study facts extend PropertyDecisionFact (desk, seating, lighting, storage, room and
shared-facility occupancy, internet limits/measurements, quiet hours, shared study
space and utilities). Owners can report facts; existing authorized review claims
determine checked provenance and expiry. There is no unsupported Study-ready badge
or opaque score. Tours, comparisons and commute retain canonical selection IDs,
unknown values and existing access/provider rules.

Student check-in kinds: access, wrong_space, missing_facility, maintenance,
roommate_support, academic_transition, admission_request. These open owned cases
with deadlines and next actions. Staff then use the existing maintenance,
amendment/replacement/termination/settlement or support workflow. A case close does
not execute a refund or tenancy transition. Exam/shared-living arrangements cannot
amend a lease, create debt or authorize unrestricted maintenance entry.

## Rollout and operations

1. Apply migrations `features.0024` through `0029` using the normal deployment
   process. They add tables, nullable context links, private student evidence scope,
   selected-offer snapshots, summary grants and coordinate constraints. They do
   **not** infer enrollment, dates, participant consent or historical group plans.
   No production backfill is necessary or authorized. If staged catalog data
   predates 0028, correct partial/out-of-range coordinate pairs before applying its
   constraint; never invent missing coordinates.
   Migration 0029 preserves only membership periods already recorded on any
   staged student participants. It does not use the group's current revision to
   grant retrospective access. Those older staged plans require renewed review
   after refreshing their requirements; submitted snapshots are retained.
2. Default `STUDENT_ENABLED_SERVICES=none`. Enable individual service names only
   after their operational prerequisites are met. Unknown names fail startup.
   See `backend/config/student_housing.py` and the no-secret example alongside
   this document. Build availability alone never grants an operation.
3. Maintain real University/Campus entries in Django admin, including bilingual
   names, city, source and checked date. The catalog does not imply a university
   partnership. No fictional production catalog or default verified status ships.
4. Assign trained, active `kyc_reviewer` staff. Verification evidence opens an
   existing case assigned to the verification team; support/finance cannot read
   that team's queue. Review only safe-scanned evidence. Record admission versus
   enrollment with an expiry (maximum 400 days). Revocation/expiry changes future
   offer eligibility; it does not terminate existing leases. Request missing
   evidence or record rejection through the existing case workflow without creating
   a positive claim. Consequential student records are read-only in Django admin.
   Changes to institution/campus, study dates or declared enrollment revoke old
   student claims for future use and require a new review; preference-only edits
   do not. Profile saves and reviewer decisions lock the same profile row. No
   existing agreement, payment or submitted application is rewritten.
5. Run the existing outbox, provider reconciliation, evidence scanning, changes,
   closure and case deadline workers. Monitor pending/unsafe evidence and
   unresolved money outcomes. The only current rental provider adapter is the
   explicitly isolated fake provider. Production student verification remains
   unavailable until private storage/scanning and review integration are supported;
   signing/payment also require their real adapters. Enabling a feature flag does
   not substitute for provider readiness.
6. Operate a support queue for arrival, roommate and academic-transition cases.
   Owner policies offer **requests** for exam extensions, renewal or storage, not
   unconditional approval, a free retained room or paused tenancy. Admission
   contingency remains a planning preference/request until a complete approved
   cancellation/refund policy and provider execution exist.
7. Roll back rollout by disabling capabilities before reverting code. Preserve
   records/audit/receipts. Do not reverse the schema after collecting real consent,
   evidence or financial links merely to hide the feature.

Unsupported capabilities remain unavailable even with `all`:
conditional_student_booking, student_family_payments, student_ambassadors,
student_services, admission_refund_guarantee. Read-only family summary sharing is
separately implemented; recipient access requires an account and a scoped live
grant. No emails, invitation messages or automatic family notifications are sent.

## Verification sources

- `backend/core_apps/features/tests/test_student_housing.py`: canonical reuse,
  privacy, revision/roster consent, separate enrollment, evidence worker, mixed
  eligibility and PostgreSQL competing commands.
- `test_student_journeys.py`: solo full local lifecycle; existing-group planning,
  exact source response and independent partial completion; existing roommate
  connection; next-year continuity; read-only family summary and revocation.
- `test_student_boundaries.py`: immutable policies/history, completed plans,
  campus constraints, study provenance, family expiry and internship planning
  alongside an acknowledged formal departure request.
- `test_student_relocation.py`: full local internship relocation, effective formal
  termination, move-out, new owner's independent booking, old deposit repayment
  and payout, with no automatic transfer to the new deposit.
- `test_student_group_decisions.py`: period-specific canonical votes/comments,
  revision history, late membership, leave/rejoin and historical access revocation.
- Existing `test_cycle_concurrency.py`, `test_rental_lifecycle_safety.py`,
  `test_full_cycle_http.py`, planning, finance and chat suites remain the shared
  integrity checks. PostgreSQL is required for lock/concurrency evidence.

Fixtures emitted to Flutter are explicitly synthetic and contain no production
students, documents, signatures or receipts. Local fake-provider completion is
integration test evidence only. Exact results and remaining release blockers are
recorded in the companion implementation report.

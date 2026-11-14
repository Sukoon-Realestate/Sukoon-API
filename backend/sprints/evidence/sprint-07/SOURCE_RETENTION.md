# Sprint 07 source and retention ownership

This change creates service/transport modules, with **no new model, app registration or migration**. Stable model,
migration, task and supported callable imports remain in their existing locations. The source ledger includes every
Python source under `core_apps/features/` outside tests/migrations/cache, including experience and files that do not
contain a housing/planning keyword. It is an ownership inventory, not proof that every retention policy is complete.

| Family | Canonical source / retention owner | Sprint 07 responsibility |
|---|---|---|
| Interests, invitations, terms and personal agreements | `services/rental_phase2*`, `services/tenancy_invitations*`, `services/rental_application_records.py`, `services/rental_lifecycle/terms.py`; existing receipts, timeline, invitation and lease models | Explicit transports; complete workflow extraction remains open for legacy interest/agreement handlers |
| Applications, reservations, group bookings and operational cases | `services/rental_lifecycle/`; application versions/grants, hold locks, booking consents, audit events and receipts | Named command steps retain authorization-before-replay and root-lock orchestration |
| Handovers and personal maintenance | `services/handover_commands.py`, `handover_reads.py`, `personal_maintenance.py`, `maintenance_reads.py`; existing evidence, possession, consent, invoice-source, audit and receipt records | Services own state changes; supported helper facades remain available; complete legacy read histories are retained |
| Private rental evidence and signed documents | `services/evidence_storage.py`, `evidence_projection.py`, `signing_documents.py`, `signing_*`, existing private byte/document access services | Projection metadata does not confer byte access or deletion rights; signing execution/provider handlers retain further extraction debt |
| Company membership, contracts, tenancies, responsibilities, staff and work | `services/company/`; current membership/mandate/assignment authority, contracts, operation recovery and historical evidence | Stable resource/action role metadata; command steps and prepared tenancy read sections; current command authorization remains separate from prepared facts |
| Residential portfolio and media | `services/company/portfolio*`, `properties.models.portfolio.ResidentialMedia`, `virtual_tours.tasks.referenced_blobs` | Portfolio remains an explicit shared-tour-storage consumer. Ready **and removed** blobs remain referenced private evidence; actual orphans can be reclaimed. Existing local/remote reference and upload-compensation tests are retained |
| Groups, roommates, housing requests/offers and conditions | `services/planning*`, existing group/roommate/housing/condition source modules and consent/history models | Explicit method transports preserve capability/type/privacy policies; substantial workflow/helper extraction remains open |
| Students and shared housing | `services/student_housing/`, `services/shared_housing/`, verification evidence, current participants, allocation/consent and handoff records | Named student command steps; existing evidence, participant and academic-period authority retained |
| Scenarios, tenders and transition matching | `services/housing_scenarios/`, `services/housing_tenders/`, `services/transition_network/`, `advanced_execution*` | Existing bounded computation/snapshot/commit/recovery rules retained; named tender/scenario steps; remaining adapter orchestration is recorded |
| Living Lab | `services/living_lab/retention.py`, private-data purge management command and existing source/result snapshots | Retention owner remains the existing scrub service; explicit method policies do not change expiry or receipt scrubbing |
| Experience, preferences, preparation tasks and action center | `features.experience` models/services/jobs and current group/company/source authority | Included even though nested outside the legacy `*_views.py` convention. No new private store is introduced; complete command/read extraction and family-wide retention evidence remain open |
| Reputation | `services/reputation/`, generation/submission/visibility/moderation/grants and source ancestry | Existing authored classes and privacy-aware public/read projections retained; no invented cache or success result |
| Commerce/provider/catalog families | Existing commerce, billing, subscription, payout, refund, provider-simulator and catalog owners | Deferred to Sprint 08; shared source references remain in the ledger and their adjacent regression tests run |

New read contexts contain only in-memory facts for one response. They never authorize a later mutation, provider job,
receipt replay or private-byte access. New command modules continue writing the existing owning models and durable
receipts; moving a command does not establish a new retention policy.

`source-ownership.json` records the whole feature source surface, while `route-coverage.json` records the exact selected
route set and adapter state-write signals. Those signals are review pointers, not a claim that every remaining method
is a bug. API-wide retention and hard payload/lock-time acceptance remain open where the evidence README says so.

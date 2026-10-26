# Sprint 13 — S261–S280

This sprint belongs to the authorized final batch (11–14). Complete remaining source coverage and stop for design review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Primary screens and their relevant presentation/data dependencies were audited; the complete dependency index below was hash-checked from the sibling `sokoun` checkout. `../batch-11-14-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s261"></a>
### S261 — Tender clarification composer

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_clarification_edit_screen.dart`

Required comment, bid identity/revision and requestKey, capability and sealed context apply. Clarification is not a modified quote; only current bid context may receive response. Preserve pending draft/recovery.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_clarification.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/tender_clarification_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`.

<a id="s262"></a>
### S262 — Tender clarifications history

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_clarifications_screen.dart`

Bid-scoped paginated clarification records, author/text/date and current permitted reply state. Preserve bid revision/scope; refreshed quote and clarification text are separate authorities.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_clarifications_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_clarification.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_labels.dart`.

<a id="s263"></a>
### S263 — Tender package own consent

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_consent_screen.dart`

Package/digest/decision bind own allocation filtered by AccountSession.userId. Accept requires independentAck, decline not forced to accept. Other users financial/private allocation data not consented for. Revisions/expiry invalidate prior digest; recovery same original body.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed, expired.

Rendered review variants: decline-package, loading, error, saving, unknown-outcome, stale, revision-changed, expired, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`.

<a id="s264"></a>
### S264 — Tender package construction runs

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_construction_screen.dart`

Tender-scoped construction runs and statuses, bounded solver/snapshot and output package references. Queued/running/completed/failed distinct; never imply optimum or booking from a run label. Resume/read original job, not duplicate dispatch.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, processing, infeasible.

Rendered review variants: loading, error, stale, restricted, empty, processing, infeasible.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_construction_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_empty_state.dart`.

<a id="s265"></a>
### S265 — Tender construction start or dispatch

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_construction_start_screen.dart`

Create new run and dispatch existing run are distinct actions/subjects/recovery suffixes. Use current tender/run revisions, snapshot and requestKey; creation itself does not perform dispatch or create binding allocations.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: dispatch-run, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/tender_construction_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_run_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`.

<a id="s266"></a>
### S266 — Create housing tender

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_create_screen.dart`

Source/group typed IDs and revisions, title, future instant close date; draft entity scopes both. Confirmed resource ID before navigation. No automatic own requirement/disclosure/publication or group consent from creating tender.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/cubits/housing_tender_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/housing_tender_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/housing_tender_details.dart`.

<a id="s267"></a>
### S267 — Tender execution proposal

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_execution_screen.dart`

Only package.executionModes allowed; independent vs conditional mode not interchangeable. Explicit ack and package digest, collectiveTenderExecution capability. Prepare produces execution proposal then detail, never payment/signature/occupancy by itself.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`.

<a id="s268"></a>
### S268 — Tender inventory picker

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_inventory_screen.dart`

Fresh property details and eligible offer inventory return typed RentalSelection. Correct property/offer/terms/revision, capacity and scope; unsupported/stale inventory not silently synthesized. Selection is not reservation.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, inventory-changed.

Rendered review variants: loading, error, stale, restricted, empty, inventory-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/cubits/tender_inventory_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_inventory_picker.dart`.

<a id="s269"></a>
### S269 — Tender package allocation builder

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_package_builder_screen.dart`

Choices validate participant, bid and inventory snapshots/revisions; nonempty assignments from current tender participants only. Draft restore removes absent users. Allocation editor avoids conflicting inventory; building package does not imply participant acceptance.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed, inventory-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, inventory-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_allocation_choice.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/housing_tenders_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_allocation_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_command.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_package_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_bid.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_execution_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_package_details.dart`.

<a id="s270"></a>
### S270 — Tender package detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_package_screen.dart`

Package snapshot/digest, allocations, per-person consent and validity. Only current own allocation may be accepted; accepted count not universal binding authority. Stale bid/requirements/expiry cause new snapshot/review, execution readiness still separate.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed, expired.

Rendered review variants: loading, error, stale, restricted, revision-changed, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/cubits/housing_tender_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_package_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_labels.dart`.

<a id="s271"></a>
### S271 — Tender package list

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_packages_screen.dart`

TenderId scoped packages, snapshot validity/status and phase constraints. New package version does not retain old participant consent. List distinguishes candidate packages from existing reservations/contracts.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_packages_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/tender_package.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_labels.dart`.

<a id="s272"></a>
### S272 — Tender source chooser

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/screens/tender_source_screen.dart`

Eligible paginated sources respect optional groupId. Current typed source/group revisions feed create route; unavailable or obsolete source cannot start a tender. Picker does not publish private requirements.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_sources_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/data/models/housing_tender.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_tenders/presentation/widgets/tender_empty_state.dart`.

<a id="s273"></a>
### S273 — Shared living-lab action

Source: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_lab_action_screen.dart`

Session boundary protects private lab state. Actions run/respond/withdraw/prepare_cost_proposal/prepare_application differ; response requires valid decision and candidate identity. Expected lab/candidate revisions, bounded optimization and handoff intent cannot imply legal or group-wide agreement.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: run-lab, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/enums/living_lab_action.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_session_boundary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_action_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_arrangement_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_candidate_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab_bodies.dart`.

<a id="s274"></a>
### S274 — Create shared living lab

Source: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_lab_create_screen.dart`

Load current HousingGroup then create with eligible active members/group revision and selection context. Session-bound private data and purpose; lab creation does not request private requirements or fabricate consent automatically.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/cubits/living_lab_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_create_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab_bodies.dart`.

<a id="s275"></a>
### S275 — Shared living lab planning

Source: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_lab_planning_screen.dart`

configure/scenario/prepareTender native action switch. Validate money/room/weight/chores allocation and household policy. Counterfactual departure/new member/shift/exam/quote/vacancy/expense changes do not alter real members; tender handoff uses current source and explicit disclosure.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: living-scenario, living-tender, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/enums/living_lab_action.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_session_boundary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_arrangement_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_scenario_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_tender_handoff_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_arrangement_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_cost_policy_fields.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_household_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_household_fields.dart`.

<a id="s276"></a>
### S276 — Shared living lab detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_lab_screen.dart`

Fresh lab snapshot, session boundary, private/omitted inputs and purpose state. Tabs/configuration/candidates/response/handoff gated by permission and current lab/candidate revisions. Missing requirements must not become zeros or hidden assumptions; solver results bounded, not guaranteed fairness.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed, processing, infeasible.

Rendered review variants: living-candidate, loading, error, stale, restricted, revision-changed, processing, infeasible.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/cubits/living_lab_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_arrangement_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_scenario_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_candidate_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_household_summary.dart`.

<a id="s277"></a>
### S277 — Shared living labs list

Source: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_labs_screen.dart`

Session-bound group-specific paginated labs. Only authorized current group can create/read; archived/withdrawn snapshots read-only. Do not carry private inputs across groups/accounts or make optional lab a housing prerequisite.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_session_boundary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_labs_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_labs_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_lab_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_scenario_form.dart`.

<a id="s278"></a>
### S278 — Living requirements and disclosure

Source: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/screens/living_requirements_screen.dart`

Separate permission-based editor/readout and disclosure mode. Purpose consent before input; optional omission explicit, never zero-valued inference. Rent/deposit/expense bounds, room and quiet windows validate; disclosure field selection must be opted in with own consent and lab revision/session.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: omitted-inputs, living-disclosure, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/cubits/living_lab_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_requirement.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_disclosure_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_requirement_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_requirement_readout.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_arrangement_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_household_summary.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/data/models/living_lab_bodies.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_cost_policy_fields.dart`, `sokoun/apps/sokoun_app/lib/features/shared/living_lab/presentation/widgets/living_private_arrangement_fields.dart`.

<a id="s279"></a>
### S279 — Company housing scenario

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/housing_scenario_screen.dart`

Company-scoped immutable input/source snapshots and scenario run revisions. Poll calculating state, cancel/retry by original job; feasibility not global optimality. Unknown costs/commutes remain unknown, per-person effects and unallocated staff visible. Compare/duplicate/run/actions allowed server-side; stale sources require refresh.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, processing, source-changed, infeasible.

Rendered review variants: scenario-inputs, loading, error, stale, restricted, processing, source-changed, infeasible.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/cubits/housing_scenario_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/housing_scenario.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/scenario_location_rule.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/scenario_assumptions.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_run_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_review_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_plan_card.dart`.

<a id="s280"></a>
### S280 — Company housing scenario list

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/housing_scenarios_screen.dart`

CompanyId/canCreate gated paginated scenarios. Embedded creation form requires eligible staff/request/offers/location rules, dates/headcount/rent/deposit caps; private input snapshots. Duplicate creates new draft, never mutates approved snapshot or authorizes booking.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: scenario-create, loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/housing_scenario.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenarios_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_form.dart`.


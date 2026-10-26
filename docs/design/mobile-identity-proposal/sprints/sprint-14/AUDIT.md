# Sprint 14 — S281–S295

This sprint belongs to the authorized final batch (11–14). Complete remaining source coverage and stop for design review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Primary screens and their relevant presentation/data dependencies were audited; the complete dependency index below was hash-checked from the sibling `sokoun` checkout. `../batch-11-14-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s281"></a>
### S281 — Scenario decision inbox

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/scenario_decision_inbox_screen.dart`

Company-scoped private paginated ScenarioReview records. Status label, source scenario and review/comparison ID maintained; detail return refreshes. Pending/approved/rejected/changes/prepared cannot be conflated with live booking or payment.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/scenario_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/scenario_review_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/scenario_review_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/housing_scenario.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/scenario_review_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_review_details.dart`.

<a id="s282"></a>
### S282 — Scenario review and comparison

Source: `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/screens/scenario_review_screen.dart`

Decision vs comparison mode native route. Review binds immutable snapshot digest/source revisions and selected plan; compare own labelled snapshots. Approved decision then prepare_booking and mock execute are distinct permissions/actions; source stale/unknown costs remain. Real booking IDs shown only when authoritative.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, source-changed.

Rendered review variants: comparison, prepare-booking, loading, error, saving, unknown-outcome, stale, source-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/cubits/scenario_review_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/scenario_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_review_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/data/models/housing_scenario.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_review_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/housing_simulator/presentation/widgets/scenario_plan_card.dart`.

<a id="s283"></a>
### S283 — Move intent action

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_action_screen.dart`

publish requires matchingConsent, other actions pause/withdraw/match distinct. MoveIntent revision/requestKey, capability and scope authoritative; match creates/returns run ID, never executes move. Publishing private matching info explicit opt-in.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, revision-changed.

Rendered review variants: start-matching, loading, error, saving, unknown-outcome, stale, revision-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/cubits/move_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/transition_network_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_run_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_run_details.dart`.

<a id="s284"></a>
### S284 — Move candidate detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_candidate_screen.dart`

Candidate selection/period/rent/deposit, signed rent change, gap/turnover and open-chain/cycle labels. checkedAt/expiry and snapshot digest gate interest/create_execution; existing execution opens it instead. Interest is not owner approval or tenancy release.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, expired, source-changed.

Rendered review variants: loading, error, stale, restricted, expired, source-changed.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/cubits/move_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_candidate_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`.

<a id="s285"></a>
### S285 — Move candidates list

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_candidates_screen.dart`

Optional runId scopes paginated candidates. Bounded result set, source freshness and privacy maintained; no future occupancy guarantee. Infeasible/no candidates is valid and distinct from failed network read.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted, infeasible.

Rendered review variants: loading, error, stale, restricted, empty, infeasible.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_candidates_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`.

<a id="s286"></a>
### S286 — Create or edit move intent

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_create_screen.dart`

Load MoveContext by lease, require eligible selected source and valid interval/budgets/gap/turnover. Existing intent update binds original identity/revision; no arbitrary source from cache. Saving draft does not publish matching consent or release current lease.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, source-changed, no-source.

Rendered review variants: no-source, loading, error, saving, unknown-outcome, stale, source-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/cubits/move_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_intent_editor.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_source.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_requirements_fields.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`.

<a id="s287"></a>
### S287 — Move execution proposal

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_execution_screen.dart`

housingTransitionExecution capability and candidate expectedRevision/snapshotDigest bind prepare request. Result is ExecutionDetailScreen only after confirmed resource identity. Not immediate transfer, occupancy/signature/payment or release of outgoing tenancy.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, expired, source-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, expired, source-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/transition_network_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_context.dart`.

<a id="s288"></a>
### S288 — Move intent detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_intent_screen.dart`

Intent status/criteria/turnover/gap and current allowed actions. Freshness/expiry/withdrawn state distinguish read vs mutation; current lease and published consent separate. History references original runs; no silent unpublishing or resubmission.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, revision-changed, expired.

Rendered review variants: loading, error, stale, restricted, revision-changed, expired.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/cubits/move_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_intent_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`.

<a id="s289"></a>
### S289 — Move intents collection

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_intents_screen.dart`

Lease-scoped private paginated intents, create from current eligible source, refresh on changed return. Draft/published/paused/withdrawn/expired do not indicate concluded rental status.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_intents_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`.

<a id="s290"></a>
### S290 — Move candidate interest decision

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_interest_screen.dart`

Decision passed to revision/digest-bound interest endpoint; source candidate and expected current terms immutable. Interest confirmation separate from owner acceptance, matching execution or existing tenancy obligations. Retry original command receipt after unknown result.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, expired, source-changed.

Rendered review variants: loading, error, saving, unknown-outcome, stale, expired, source-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/cubits/move_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/transition_network_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_body.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_run.dart`.

<a id="s291"></a>
### S291 — Move matching run detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_run_screen.dart`

Run ID, queued/matching/results/infeasible/failed and poolLimited state with candidateCount. Bounded search not exhaustive optimality. Refresh original run, do not create another on polling error or unknown dispatch outcome.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, processing, infeasible.

Rendered review variants: loading, error, stale, restricted, processing, infeasible.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/cubits/move_cubits.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_run_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_context.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_intent.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_candidate.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`.

<a id="s292"></a>
### S292 — Move matching run history

Source: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/screens/move_runs_screen.dart`

IntentId-scoped private paginated run history, each own snapshot and status. Historical result must not become writable current candidate. No results and no runs distinct from failed read.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_runs_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/data/models/move_run.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/transition_network/presentation/widgets/move_labels.dart`.

<a id="s293"></a>
### S293 — Execution action review

Source: `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/screens/execution_action_screen.dart`

Parameterized consent/advance/reconcile/withdraw/resolve with plan/leg/step/decision and digest. Explicit mock outcomes confirmed/failed/unknown_before/unknown_after belong only to sandbox UI. Terms review includes document hash, canonical individual/company context and own placement; recover same intent, never duplicate payment or rollback confirmed legs.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, stale, restricted, source-changed.

Rendered review variants: reconcile-step, loading, error, saving, unknown-outcome, stale, source-changed, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/data/models/execution_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/cubits/execution_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/widgets/execution_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/widgets/execution_terms_review.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/data/execution_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/data/models/execution_body.dart`.

<a id="s294"></a>
### S294 — Execution plan detail

Source: `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/screens/execution_detail_screen.dart`

Plan mode independent/conditional, accepted/required and confirmed/leg counts, immutable journal and per-leg canonical state. Unknown leg requires reconcile; confirmed legs cannot be withdrawn/replayed. Outgoing occupancy/financial closure separate from incoming leases. No blind rollback on partial success.

Original visual references: S18, S19.

Required implementation states: loading, error, stale, restricted, partial-error, unknown-outcome.

Rendered review variants: partial-completion, loading, error, stale, restricted, partial-error, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/cubits/execution_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/data/models/execution_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/widgets/execution_details.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/widgets/execution_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/widgets/execution_leg_card.dart`.

<a id="s295"></a>
### S295 — Execution inbox

Source: `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/screens/execution_inbox_screen.dart`

Private paginated execution inbox resource-authorized across tender/scenario/move sources. Item title/source/current stage/status and open detail refresh. Completed/partial/manual/unknown states explicit; inbox never authorizes new payment or consent for another actor.

Original visual references: S18, S19.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/widgets/execution_inbox_list.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/data/models/execution_plan.dart`, `sokoun/apps/sokoun_app/lib/features/shared/advanced_execution/presentation/widgets/execution_labels.dart`.


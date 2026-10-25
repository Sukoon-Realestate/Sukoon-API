# Sprint 3 — S61–S80

This sprint belongs to the authorized five-sprint batch (3–7). Stop after Sprint 7 for user review. No Flutter or API behavior changes.

## Visual authority

Original S01–S20, Readex/Plex type, pine/paper tokens, original control/card proportions and selective signature headers. All data, dates, balances, model previews and messages are illustrative. Maps/capture/provider/signature prototypes never use real device services or external APIs.

## Source audit

Every primary file and dependency below was inspected from the sibling `sokoun` checkout. `../batch-03-07-source-audit.json` records source hashes, label keys, commands and guards. A screen count represents a distinct source destination; its data/permission/provider variants do not inflate the count.

## Common contract

Freshness, role/capability, source revision, command identity and uncertain-write recovery remain authoritative. Private data stays scoped to session/workspace. Prototype confirmations only demonstrate intent: they do not assert payment, publication, signatures, consent for other users, refunds, occupancy or liability. A readonly or stale variant must not contain a mutating control.

## Screen audit

<a id="s61"></a>
### S61 — Property pricing and final review

Source: `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_pricing_page.dart`

Third step: positive price/duration, catalog-backed amenities/suitability, description and additional details. Partial offerings use RentalOfferTermsEditor and supported inventory; unsupported/local-only data must not be submitted. Review precedes server submission, not immediate publish.

Original visual references: S17, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: partial-offering, loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_add_property_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/owner_pricing_options_data.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_pricing_page_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_property_inventory_selection.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_property_form_validation.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_property_form_labels.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_property_form_copy.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_property_form_encoding.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_property_form_api_values.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/property_location.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_add_property_content_owner_property_photo_draft.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_step_shell.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/property_selection_field.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/rental_offer_terms_editor.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_info_banner.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_pricing_page_price_section.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/property_pricing_catalog.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_pricing_page_description_section.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_additional_details.dart`.

<a id="s62"></a>
### S62 — Property submitted for review

Source: `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_submitted_page.dart`

Submitted status is pending review. Display server message and summary; property detail only with ID, tour manager only when callback available. Add-another resets the flow; do not claim publication.

Original visual references: S11, S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/home/data/models/owner_add_property_content_add_property_summary_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/widgets/owner_add_property/add_property_primary_button.dart`, `sokoun/apps/sokoun_app/lib/features/owner/home/presentation/screens/owner_listings_screen.dart`.

<a id="s63"></a>
### S63 — Property analytics

Source: `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_property_analytics_screen.dart`

Server analytics periods 7_days/30_days/90_days; supplied snapshot omits period selector. Preserve missing analytics/history empty state; no invented acceptance or revenue values.

Original visual references: S15, S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/properties/data/models/owner_property_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/data/models/owner_property_analytics_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/cubits/owner_property_analytics_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/analytics/owner_analytics_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/analytics/owner_analytics_unavailable_details.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/analytics/owner_analytics_metric_card.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/analytics/owner_analytics_bar_chart.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/analytics/owner_analytics_empty_state.dart`.

<a id="s64"></a>
### S64 — Rejected property and correction

Source: `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_property_rejection_screen.dart`

Read rejection reason, use unavailable-reason fallback. Load current full details before opening edit flow; if details load fails do not construct an empty edit draft. Return updated property after successful edit.

Original visual references: S04, S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/properties/data/models/owner_property_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/list/owner_property_status_badge.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/data/enums/owner_property_status.dart`.

<a id="s65"></a>
### S65 — Owner revenue overview

Source: `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/screens/owner_revenue_screen.dart`

OwnerRevenueContent properties/transactions and optional comparison text; empty collections are valid. Retain rental selection on transaction details and direction/credit sign; displayed sums are illustrative, not settled payout guarantees.

Original visual references: S15, S19.

Required implementation states: loading, error, stale, restricted.

Rendered review variants: loading, error, stale, restricted.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/cubits/owner_revenue_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/data/models/owner_revenue_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/revenue/owner_revenue_content_view.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/data/models/owner_revenue_content_owner_revenue_property_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/data/models/owner_revenue_content_owner_transaction_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/revenue/owner_revenue_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/revenue/owner_revenue_property_card.dart`, `sokoun/apps/sokoun_app/lib/features/owner/properties/presentation/widgets/revenue/owner_transaction_row.dart`.

<a id="s66"></a>
### S66 — Owner availability editor

Source: `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_availability_screen.dart`

Per-property/date slot drafts, Cairo time, booked/locked slots immutable. Preserve local draft, unsaved guard and uncertain-save recovery; respect availability start/date range and authoritative save result.

Original visual references: S10, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/cubits/owner_availability_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_availability_content_owner_availability_slot_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/presentation/widgets/text_draft_binding.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_availability_content_owner_availability_day_content.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/enums/recovery_flow.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/owner_availability_draft_data.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_visit_calendar_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/widgets/owner_availability_screen_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_availability_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_availability_content_owner_availability_save_body.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_visit_calendar_content_owner_calendar_day_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_visit_calendar_content_owner_calendar_visit_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/widgets/owner_availability/owner_availability_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/widgets/owner_availability/owner_availability_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_availability_content_owner_availability_slot_body.dart`.

<a id="s67"></a>
### S67 — Owner viewing calendar

Source: `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_requests_calendar_screen.dart`

Select date and show server visit count/details. Manage availability requires an identified property or property picker; refresh when availability returns changed. Do not fabricate appointments from availability slots.

Original visual references: S10, S18.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/cubits/owner_calendar_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/screens/owner_availability_screen.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_visit_calendar_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/widgets/owner_calendar/owner_calendar_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_availability_content_owner_availability_slot_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_availability_content_owner_availability_day_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/widgets/owner_availability_screen_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_visit_calendar_content_owner_calendar_day_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/data/models/owner_visit_calendar_content_owner_calendar_visit_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/widgets/owner_calendar/owner_calendar_day.dart`, `sokoun/apps/sokoun_app/lib/features/owner/visits/presentation/widgets/owner_calendar/owner_calendar_visit_card.dart`.

<a id="s68"></a>
### S68 — Capture output selection

Source: `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/screens/capture_selection_screen.dart`

Catalog verified/selectable outputs only; require selected outputs, scope and names. Existing revision resumes draft. Preview panorama/reconstruction separately; do not treat raw uploaded captures as published tours.

Original visual references: S04, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, no-selectable-output.

Rendered review variants: loading, error, saving, unknown-outcome, no-selectable-output.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/property_capture/data/capture_api.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/cubits/capture_selection_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/data/capture_selection_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/widgets/capture_selection_form.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/cubits/capture_selection_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/data/models/capture_models.dart`.

<a id="s69"></a>
### S69 — Property capture session

Source: `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/screens/property_capture_screen.dart`

Capability/device readiness, camera permission and explicit consent before starting. Pause on lifecycle changes; coach opt-in/voice and offline/local guidance distinct. Angular coverage/stations, verified uploads and recovery do not grant publishing authority.

Original visual references: S04, S08.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, permission-denied, unsupported, processing.

Rendered review variants: loading, error, saving, unknown-outcome, permission-denied, unsupported, processing.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/cubits/property_capture_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/data/capture_api.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/data/models/capture_models.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/widgets/capture_live_panel.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/widgets/capture_preparation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/widgets/capture_review_panel.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/screens/capture_selection_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/widgets/capture_target_overlay.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/widgets/capture_selection_form.dart`.

<a id="s70"></a>
### S70 — Tour revision editor

Source: `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/screens/owner_tour_editor_screen.dart`

Edit revision/context/hotspots with draft signatures and source-scene checks. Fresh revision ready/contexts gate preview and direction capture. Handle save conflicts/recovery; saving does not imply active publication.

Original visual references: S08, S17.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, conflict, processing.

Rendered review variants: loading, error, saving, unknown-outcome, conflict, processing.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/tour_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/models/tour_models.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/cubits/tour_editor_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/widgets/tour_form_dialog.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/screens/tour_viewer_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/tour_authoring.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/tour_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/cubits/tour_editor_state.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/widgets/owner_tour_editor_content.dart`.

<a id="s71"></a>
### S71 — Owner tour manager

Source: `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/screens/owner_tour_manager_screen.dart`

Capabilities decide writable kinds/create/clone/preview/publish-disable-delete availability. Processing/review/active revisions differ. Confirm disable/unpublish/delete and apply only after successful commands. Property/common-area source scope preserved.

Original visual references: S18, S08.

Required implementation states: loading, error, empty, stale, restricted, processing.

Rendered review variants: loading, error, stale, restricted, empty, processing.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/tour_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/cubits/tour_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/models/tour_models.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/screens/owner_tour_editor_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/property_capture/presentation/screens/property_capture_screen.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/tour_labels.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/widgets/tour_form_dialog.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/widgets/owner_tour_editor_content.dart`.

<a id="s72"></a>
### S72 — Immersive tour viewer

Source: `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/presentation/screens/tour_viewer_screen.dart`

Trusted session origin /tours/ path, navigation/bridge instance checks and session cleanup. Model requires WebGL2/WASM readiness; handle timeout/unavailable. Direction-selection return only when captureDirection and source scene match.

Original visual references: S08.

Required implementation states: loading, error, stale, restricted, unsupported, session-ended.

Rendered review variants: loading, error, stale, restricted, unsupported, session-ended.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/tour_data.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/models/tour_models.dart`, `sokoun/apps/sokoun_app/lib/features/shared/virtual_tours/data/tour_viewer_bridge.dart`, `sokoun/apps/sokoun_app/lib/features/shared/recovery/data/recovery_scope.dart`.

<a id="s73"></a>
### S73 — Commute results

Source: `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/screens/commute_results_screen.dart`

Asynchronous job polling pauses offscreen and reloads on resume. Pending progress/cancel, failed/cancelled/complete states; known estimates, unknown and partial coverage distinguished. Loaded-only/full-catalog scope labels retained.

Original visual references: S06, S19.

Required implementation states: loading, error, empty, stale, restricted, processing, cancelled.

Rendered review variants: loading, error, stale, restricted, empty, processing, cancelled.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/cubits/commute_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/cubits/commute_state.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/widgets/commute_results_list.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/commute/data/models/commute_plan.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/commute/data/models/commute_search.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/widgets/commute_results_empty_state.dart`.

<a id="s74"></a>
### S74 — Commute preferences

Source: `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/screens/commute_screen.dart`

CommuteEditor destination location, modes, arrive/depart supported modes, Cairo local time and duration/balance preferences. Preserve filters and privacy; validate location/limits before starting a server search.

Original visual references: S07, S10.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/commute/data/models/commute_plan.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/widgets/commute_editor.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/commute/data/models/commute_destination.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/commute/presentation/widgets/commute_destination_editor.dart`.

<a id="s75"></a>
### S75 — Private decision notebook

Source: `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/screens/decision_tools_screen.dart`

Account/environment scoped local notebook, historical snapshots, saved searches and private viewing checklist. Local persistence failures preserve edits. Compare two to three exact property/offer targets; do not mix offer identity or imply notes are public.

Original visual references: S09, S20.

Required implementation states: loading, error, empty, stale, restricted.

Rendered review variants: loading, error, stale, restricted, empty.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/cubits/decision_tools_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/data/models/decision_notebook.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/decision_notebook_view.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/data/models/decision_target.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/notebook_delete_dialog.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/decision_tools_empty.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/decision_editor.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/rename_saved_search_dialog.dart`.

<a id="s76"></a>
### S76 — Property comparison

Source: `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/screens/property_comparison_screen.dart`

Only notebook-selected exact targets; retain unavailable/read-error entries and retry per property. Assistant enabled only if all offer IDs empty and at least two available properties, max three. Remove updates persisted comparison, not favorites.

Original visual references: S08, S07.

Required implementation states: loading, error, stale, restricted, partial-error.

Rendered review variants: loading, error, stale, restricted, partial-error.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/data/models/decision_target.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/cubits/property_comparison_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/cubits/decision_tools_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/data/models/comparison_property.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/decision_tools_empty.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/comparison_table.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/data/models/decision_notebook.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/decision_tools/presentation/widgets/comparison_table_body.dart`.

<a id="s77"></a>
### S77 — Tenant assistant

Source: `sokoun/apps/sokoun_app/lib/features/tenant/ai_assistant/presentation/screens/tenant_assistant_screen.dart`

Nonblank prompt max4000, filters/property/offer/selected-property context preserved. Clear sent text only if unchanged after response. Dictation consent, language, lifecycle/session cancellation; unresolved costs not fabricated.

Original visual references: S14, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, permission-denied, unavailable.

Rendered review variants: loading, error, saving, unknown-outcome, permission-denied, unavailable.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/ai_assistant/presentation/cubits/tenant_assistant_cubit.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/ai_assistant/data/system_dictation.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/premium_confirm_sheet.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/ai_assistant/presentation/widgets/tenant_assistant_screen_content.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/ai_assistant/data/models/tenant_assistant_reply.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/ai_assistant/data/models/tenant_assistant_body.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/ai_assistant/presentation/widgets/tenant_assistant_body.dart`.

<a id="s78"></a>
### S78 — Listing description assistant

Source: `sokoun/apps/sokoun_app/lib/features/owner/ai_assistant/presentation/screens/listing_ai_screen.dart`

Owner feature guard, selected property/facts and explicit consent before generation. Suggestion editable, copy and canApply are separate; manual review before applying. Request key and unavailable feature states preserved.

Original visual references: S17, S14.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome.

Rendered review variants: loading, error, saving, unknown-outcome.

Dependencies: `sokoun/apps/sokoun_app/lib/features/owner/ai_assistant/data/models/listing_ai_facts.dart`, `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart`, `sokoun/apps/sokoun_app/lib/features/owner/ai_assistant/presentation/widgets/listing_ai_content.dart`, `sokoun/apps/sokoun_app/lib/features/owner/ai_assistant/data/models/listing_suggestion.dart`, `sokoun/apps/sokoun_app/lib/features/owner/ai_assistant/data/models/listing_ai_body.dart`, `sokoun/apps/sokoun_app/lib/features/owner/ai_assistant/presentation/widgets/listing_ai_facts_view.dart`, `sokoun/apps/sokoun_app/lib/features/owner/ai_assistant/presentation/widgets/listing_ai_review.dart`.

<a id="s79"></a>
### S79 — Priority alert detail

Source: `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/screens/premium_alert_detail_screen.dart`

Alert cadence/last match/district criteria and criteria_need_review preserved; delivery capability can be unavailable even when matches exist. Open results with saved filters; no guaranteed instant delivery.

Original visual references: S06, S19.

Required implementation states: loading, error, stale, restricted, criteria-review, delivery-unavailable.

Rendered review variants: loading, error, stale, restricted, criteria-review, delivery-unavailable.

Dependencies: `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/widgets/premium_alert_detail_content.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/data/models/premium_search_alert.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/widgets/premium_alerts_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/widgets/premium_alert_details_view.dart`.

<a id="s80"></a>
### S80 — Saved search alerts

Source: `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/screens/premium_alerts_screen.dart`

Tenant workspace/feature guard; create only with supplied filters. Fresh revision and canManage gate pause/resume/remove, confirm removal; cached read is labelled and not writable. Delivery availability separate from alert persistence.

Original visual references: S09, S20.

Required implementation states: loading, error, invalid, dirty, saving, unknown-outcome, delivery-unavailable.

Rendered review variants: loading, error, saving, unknown-outcome, delivery-unavailable.

Dependencies: `sokoun/apps/sokoun_app/lib/features/shared/premium/presentation/widgets/shared/feature_workspace_guard.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/widgets/premium_alerts_content.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/data/models/premium_search_alert.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/widgets/premium_alert_composer.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/widgets/premium_alerts_empty_state.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/presentation/widgets/premium_alert_card.dart`, `sokoun/apps/sokoun_app/lib/features/tenant/premium_alerts/data/models/premium_alert_toggle_body.dart`.


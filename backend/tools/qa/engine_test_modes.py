"""Tests that need PostgreSQL semantics and are skipped (with a reason) on SQLite.

Populated from full runs on both engines: listed tests fail on SQLite and pass on PostgreSQL
(row locks, JSONField containment, schema/migration behavior, UUID storage). They must still
pass in the PostgreSQL run (make test-postgres-races). Prefer @pytest.mark.requires_postgres
on new tests. Same format as mvp_test_modes.py.
"""

POSTGRES_ONLY_TESTS = {
    "core_apps/admin_api/tests/test_content_editor.py": {
        "test_two_editors_cannot_overwrite_one_revision",
    },
    "core_apps/chat/tests/test_all_mentions_navigation.py": {
        "test_existing_mentions_backfill_keeps_read_and_unread_progress",
    },
    "core_apps/chat/tests/test_forwarding.py": {
        "test_opposite_forwards_and_duplicate_retries_do_not_deadlock",
    },
    "core_apps/chat/tests/test_message_mutations.py": {
        "test_concurrent_edits_are_serialized",
    },
    "core_apps/chat/tests/test_productivity.py": {
        "test_batch_opposite_directions_duplicate_and_normal_send_do_not_deadlock",
    },
    "core_apps/common/test_company_probe.py": {
        "test_probe_executes_only_read_only_database_statement",
    },
    "core_apps/features/tests/test_audit_change_terms.py": {
        "test_invalid_signed_change_is_preserved_and_does_not_stop_other_work",
    },
    "core_apps/features/tests/test_beneficiary_confirmation.py": {
        "test_concurrent_confirmations_replay_one_revision",
    },
    "core_apps/features/tests/test_change_versions.py": {
        "test_edit_and_accept_cannot_approve_different_content",
    },
    "core_apps/features/tests/test_chargeback_resolution.py": {
        "test_replacement_capture_and_cash_restoration_serialize_without_overpayment",
    },
    "core_apps/features/tests/test_closure_continuation.py": {
        "test_company_continuation_requires_current_membership_and_assigned_authority",
        "test_device_without_local_key_finds_original_attempt_during_disable",
        "test_server_pagination_and_support_workspace_are_not_local_drafts",
    },
    "core_apps/features/tests/test_company_listing_changes.py": {
        "test_events_follow_current_coordinator_and_approver_authority",
        "test_existing_contract_keeps_signed_terms_and_budget",
        "test_source_history_blocks_old_approval_and_replacement_preserves_evidence",
    },
    "core_apps/features/tests/test_company_operation_recovery.py": {
        "test_resolution_serializes_with_delayed_original_command",
    },
    "core_apps/features/tests/test_company_property_agreements.py": {
        "test_old_agreements_leave_property_but_remain_in_history",
        "test_property_agreement_keeps_bundle_identity_price_and_current_role",
    },
    "core_apps/features/tests/test_company_rental_value_reports.py": {
        "test_management_snapshot_keeps_concurrent_updates_out_of_same_report",
    },
    "core_apps/features/tests/test_company_request_versions.py": {
        "test_two_edits_share_one_current_revision_and_history",
    },
    "core_apps/features/tests/test_company_role_contexts.py": {
        "test_company_viewing_assignment_and_counters_exclude_other_work",
    },
    "core_apps/features/tests/test_company_service_requests.py": {
        "test_concurrent_original_operator_command_creates_one_proposal",
    },
    "core_apps/features/tests/test_company_staff.py": {
        "test_pending_staff_can_be_planned_without_identity_or_acknowledgment",
    },
    "core_apps/features/tests/test_decision_notebooks.py": {
        "test_two_devices_sync_concurrently_without_losing_either_entry",
    },
    "core_apps/features/tests/test_fulfillment_cases.py": {
        "test_concurrent_activation_workers_do_not_duplicate_case_or_service",
    },
    "core_apps/features/tests/test_group_booking_listing_changes.py": {
        "test_exact_physical_change_blocks_only_affected_pending_consent",
        "test_existing_invitation_and_other_private_allocations_are_preserved",
        "test_private_history_delivery_checks_current_membership_and_physical_location",
    },
    "core_apps/features/tests/test_group_booking_negotiation.py": {
        "test_concurrent_accept_and_counter_have_one_winner",
    },
    "core_apps/features/tests/test_group_process_history.py": {
        "test_concurrent_review_and_withdrawal_cannot_restore_old_consent",
        "test_roster_change_cancels_same_visit_once_and_notifies_owner",
    },
    "core_apps/features/tests/test_housing_districts.py": {
        "test_matching_inventory_filter_uses_the_same_district_scope",
    },
    "core_apps/features/tests/test_housing_request_reviews.py": {
        "test_concurrent_edit_and_reconfirm_never_confirms_old_requirements",
    },
    "core_apps/features/tests/test_invitation_review_pause.py": {
        "test_visit_continuation_preserves_pending_invitation_during_review",
    },
    "core_apps/features/tests/test_mvp_owner_portfolio.py": {
        "test_existing_owner_contract_without_company",
    },
    "core_apps/features/tests/test_negotiation_versions.py": {
        "test_accept_and_edit_are_serialized",
    },
    "core_apps/features/tests/test_paymob_payouts.py": {
        "test_concurrent_retry_approvals_create_only_one_current_attempt",
        "test_concurrent_workers_claim_one_instruction",
    },
    "core_apps/features/tests/test_planning_push_outbox.py": {
        "test_two_workers_keep_one_receipt_and_device_job",
    },
    "core_apps/features/tests/test_planning_targeted_outbox.py": {
        "test_concurrent_targeted_workers_keep_one_notice_and_push",
    },
    "core_apps/features/tests/test_portfolio_owner_workflows.py": {
        "test_bulk_stale_unit_partial_results_and_idempotent_api",
    },
    "core_apps/features/tests/test_refund_execution_recovery.py": {
        "test_concurrent_retries_have_one_new_attempt",
        "test_same_command_concurrent_reauthorization_has_one_effect",
    },
    "core_apps/features/tests/test_reputation_integrations.py": {
        "test_concurrent_bindings_cannot_split_one_renewed_tenancy_between_companies",
        "test_two_delegates_concurrently_submit_only_one_company_ballot",
    },
    "core_apps/features/tests/test_student_events.py": {
        "test_two_workers_queue_only_one_inbox_receipt",
    },
    "core_apps/notifications/tests/test_delivery_policy.py": {
        "test_concurrent_digest_workers_and_timezone_change_never_duplicate_summary",
    },
    "core_apps/profiles/tests/test_identity_expiry.py": {
        "test_concurrent_metadata_edits_and_workers_are_serialized",
    },
    "core_apps/properties/tests/test_contextual_viewings.py": {
        "test_one_group_appointment_records_each_attendee_independently",
    },
    "core_apps/properties/tests/test_mobile_handoff_oct2026.py": {
        "TestCheck4_AllWritableFieldsAndReopen::test_all_writable_fields_persist_and_reopen",
    },
    "core_apps/properties/tests/test_unscheduled_visit_requests.py": {
        "test_request_notes_owner_decision_and_chat",
    },
    "core_apps/properties/tests/test_ux_convenience.py": {
        "test_agenda_day_filter_precedes_pagination_and_sorts_times",
    },
    "core_apps/properties/tests/test_viewing_event_history.py": {
        "test_old_queued_request_survives_accept_and_cancel_with_current_history",
    },
    "core_apps/properties/tests/test_viewing_listing_changes.py": {
        "test_different_bed_change_does_not_replace_the_visited_bed",
        "test_location_change_requires_a_new_viewing_and_preserves_old_identity",
        "test_price_edit_keeps_confirmed_visit_snapshot_and_notifies_both_parties",
    },
    "core_apps/properties/tests/test_viewing_times.py": {
        "test_acceptance_is_atomic_idempotent_and_changes_visit_revision",
        "test_closure_and_acceptance_race_preserves_the_winning_revision",
        "test_competing_alternatives_accept_exactly_one_and_supersede_the_other",
        "test_expired_closed_and_stale_proposals_keep_original_appointment",
        "test_only_current_parties_in_individual_context_can_propose_up_to_three",
        "test_same_owner_two_properties_cannot_accept_the_same_time",
    },
    "core_apps/properties/tests/test_views.py": {
        "TestPropertyVisitViews::test_list_tenant_visits",
        "TestPropertyVisitViews::test_list_tenant_visits_filter_by_status",
        "TestPropertyVisitViews::test_list_tenant_visits_invalid_status_returns_400",
    },
    "core_apps/properties/tests/test_visit_offer_snapshot.py": {
        "test_existing_thin_snapshot_is_never_backfilled_from_current_inventory",
        "test_public_booking_details_decision_and_invitation_share_complete_frozen_snapshot",
    },
    "core_apps/properties/tests/test_visit_phone_disclosure.py": {
        "test_acceptance_keeps_contacts_private_and_is_idempotent",
        "test_notices_localize_and_missing_granted_phone_stays_authorized",
        "test_pending_visit_hides_numbers_across_visit_property_and_chat_reads",
        "test_rejected_or_pre_acceptance_cancelled_visit_never_discloses",
    },
    "core_apps/properties/tests/test_visit_request_api.py": {
        "TestBilingualVisitLabels::test_tenant_visit_request_labels_in_english_and_arabic",
        "TestTenantVisitRequestScreens::test_detail_reveals_owner_phone_only_after_confirmation",
        "TestTenantVisitRequestScreens::test_list_returns_card_data_and_status_actions",
        "TestTenantVisitRequestScreens::test_other_tenant_cannot_read_or_cancel_visit",
    },
    "core_apps/properties/tests/test_workspace_account_handoff.py": {
        "TestWorkspaceAccountContract::test_single_account_can_access_tenant_and_owner_endpoints",
    },
    "core_apps/users/tests/test_audit_identity.py": {
        "test_identity_migration_preserves_assurance_until_explicit_legacy_review",
    },
}

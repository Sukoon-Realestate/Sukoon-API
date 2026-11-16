# Mobile regression failures

These are observed test failures, not independently proven production defects. A stale finder, missing fixture, release gate, contract mismatch, timeout or product bug may cause them. The broad app run was interrupted after stalling; shutdown errors are retained in the raw log.

Counts exclude hidden setup/teardown and report file-loader events separately.

```json
{
  "test_cases": {
    "error": 425,
    "success": 13124,
    "failure": 72,
    "skipped": 32
  },
  "loader_events": {
    "success": 1
  },
  "terminal_event": null,
  "active_at_end": [],
  "recorded_seconds": 3692.55,
  "failed_records": 497
}
```

| Test file | Failed records | Report |
|---|---:|---|
| `advanced_execution_test.dart` | 3 | [Details](mobile-failures/advanced_execution_test.dart.md) |
| `advanced_privacy_capability_test.dart` | 1 | [Details](mobile-failures/advanced_privacy_capability_test.dart.md) |
| `app_walkthrough_repairs_test.dart` | 4 | [Details](mobile-failures/app_walkthrough_repairs_test.dart.md) |
| `application_share_consent_test.dart` | 1 | [Details](mobile-failures/application_share_consent_test.dart.md) |
| `backend_handoff_test.dart` | 2 | [Details](mobile-failures/backend_handoff_test.dart.md) |
| `badge_counts_test.dart` | 1 | [Details](mobile-failures/badge_counts_test.dart.md) |
| `banner_ads_backend_contract_test.dart` | 1 | [Details](mobile-failures/banner_ads_backend_contract_test.dart.md) |
| `banner_ads_image_selection_test.dart` | 6 | [Details](mobile-failures/banner_ads_image_selection_test.dart.md) |
| `banner_ads_rollout_test.dart` | 3 | [Details](mobile-failures/banner_ads_rollout_test.dart.md) |
| `chat_property_sharing_test.dart` | 6 | [Details](mobile-failures/chat_property_sharing_test.dart.md) |
| `chat_property_sharing_widgets_test.dart` | 42 | [Details](mobile-failures/chat_property_sharing_widgets_test.dart.md) |
| `company_approver_navigation_test.dart` | 5 | [Details](mobile-failures/company_approver_navigation_test.dart.md) |
| `company_closure_events_test.dart` | 1 | [Details](mobile-failures/company_closure_events_test.dart.md) |
| `company_core_scope_test.dart` | 1 | [Details](mobile-failures/company_core_scope_test.dart.md) |
| `company_housing_test.dart` | 2 | [Details](mobile-failures/company_housing_test.dart.md) |
| `company_mandate_status_test.dart` | 2 | [Details](mobile-failures/company_mandate_status_test.dart.md) |
| `company_negotiation_test.dart` | 1 | [Details](mobile-failures/company_negotiation_test.dart.md) |
| `company_operation_recovery_test.dart` | 2 | [Details](mobile-failures/company_operation_recovery_test.dart.md) |
| `company_package_submit_recovery_test.dart` | 1 | [Details](mobile-failures/company_package_submit_recovery_test.dart.md) |
| `company_property_agreements_test.dart` | 10 | [Details](mobile-failures/company_property_agreements_test.dart.md) |
| `company_rental_value_test.dart` | 4 | [Details](mobile-failures/company_rental_value_test.dart.md) |
| `company_role_context_test.dart` | 5 | [Details](mobile-failures/company_role_context_test.dart.md) |
| `company_role_layout_test.dart` | 5 | [Details](mobile-failures/company_role_layout_test.dart.md) |
| `company_role_populated_layout_test.dart` | 6 | [Details](mobile-failures/company_role_populated_layout_test.dart.md) |
| `company_role_work_status_test.dart` | 2 | [Details](mobile-failures/company_role_work_status_test.dart.md) |
| `company_selection_account_closure_test.dart` | 2 | [Details](mobile-failures/company_selection_account_closure_test.dart.md) |
| `company_simpler_alternative_test.dart` | 1 | [Details](mobile-failures/company_simpler_alternative_test.dart.md) |
| `company_staff_test.dart` | 2 | [Details](mobile-failures/company_staff_test.dart.md) |
| `company_tenancy_confirmation_test.dart` | 12 | [Details](mobile-failures/company_tenancy_confirmation_test.dart.md) |
| `company_tenancy_list_context_test.dart` | 3 | [Details](mobile-failures/company_tenancy_list_context_test.dart.md) |
| `company_tenancy_test.dart` | 7 | [Details](mobile-failures/company_tenancy_test.dart.md) |
| `contextual_onboarding_widgets_test.dart` | 1 | [Details](mobile-failures/contextual_onboarding_widgets_test.dart.md) |
| `dashboard_consistency_test.dart` | 29 | [Details](mobile-failures/dashboard_consistency_test.dart.md) |
| `feature_architecture_test.dart` | 1 | [Details](mobile-failures/feature_architecture_test.dart.md) |
| `feature_completeness_widgets_test.dart` | 1 | [Details](mobile-failures/feature_completeness_widgets_test.dart.md) |
| `feature_tools_flows_test.dart` | 2 | [Details](mobile-failures/feature_tools_flows_test.dart.md) |
| `four_workspaces_test.dart` | 12 | [Details](mobile-failures/four_workspaces_test.dart.md) |
| `fulfillment_followup_test.dart` | 42 | [Details](mobile-failures/fulfillment_followup_test.dart.md) |
| `group_booking_listing_changes_test.dart` | 1 | [Details](mobile-failures/group_booking_listing_changes_test.dart.md) |
| `group_booking_negotiation_test.dart` | 1 | [Details](mobile-failures/group_booking_negotiation_test.dart.md) |
| `group_chat_capability_test.dart` | 1 | [Details](mobile-failures/group_chat_capability_test.dart.md) |
| `group_chat_entry_test.dart` | 4 | [Details](mobile-failures/group_chat_entry_test.dart.md) |
| `group_chat_recovery_audio_test.dart` | 5 | [Details](mobile-failures/group_chat_recovery_audio_test.dart.md) |
| `group_chat_thread_test.dart` | 31 | [Details](mobile-failures/group_chat_thread_test.dart.md) |
| `group_chat_upload_test.dart` | 5 | [Details](mobile-failures/group_chat_upload_test.dart.md) |
| `group_chat_widgets_test.dart` | 23 | [Details](mobile-failures/group_chat_widgets_test.dart.md) |
| `group_property_agreements_test.dart` | 2 | [Details](mobile-failures/group_property_agreements_test.dart.md) |
| `housing_group_create_form_test.dart` | 11 | [Details](mobile-failures/housing_group_create_form_test.dart.md) |
| `housing_group_list_flow_test.dart` | 1 | [Details](mobile-failures/housing_group_list_flow_test.dart.md) |
| `housing_group_navigation_test.dart` | 3 | [Details](mobile-failures/housing_group_navigation_test.dart.md) |
| `housing_groups_bugfix_test.dart` | 1 | [Details](mobile-failures/housing_groups_bugfix_test.dart.md) |
| `housing_offer_compose_test.dart` | 5 | [Details](mobile-failures/housing_offer_compose_test.dart.md) |
| `housing_offer_roles_test.dart` | 6 | [Details](mobile-failures/housing_offer_roles_test.dart.md) |
| `housing_offer_source_history_test.dart` | 2 | [Details](mobile-failures/housing_offer_source_history_test.dart.md) |
| `housing_request_reviews_test.dart` | 6 | [Details](mobile-failures/housing_request_reviews_test.dart.md) |
| `housing_requests_flow_test.dart` | 3 | [Details](mobile-failures/housing_requests_flow_test.dart.md) |
| `housing_tenders_test.dart` | 1 | [Details](mobile-failures/housing_tenders_test.dart.md) |
| `living_lab_test.dart` | 2 | [Details](mobile-failures/living_lab_test.dart.md) |
| `main_journey_features_test.dart` | 5 | [Details](mobile-failures/main_journey_features_test.dart.md) |
| `mobile_dev_handoff_integration_test.dart` | 2 | [Details](mobile-failures/mobile_dev_handoff_integration_test.dart.md) |
| `my_housing_locale_test.dart` | 2 | [Details](mobile-failures/my_housing_locale_test.dart.md) |
| `owner_banner_ads_flow_test.dart` | 5 | [Details](mobile-failures/owner_banner_ads_flow_test.dart.md) |
| `owner_banner_ads_ui_test.dart` | 14 | [Details](mobile-failures/owner_banner_ads_ui_test.dart.md) |
| `owner_home_locale_test.dart` | 4 | [Details](mobile-failures/owner_home_locale_test.dart.md) |
| `owner_visit_requests_flow_test.dart` | 1 | [Details](mobile-failures/owner_visit_requests_flow_test.dart.md) |
| `planning_completion_contract_test.dart` | 1 | [Details](mobile-failures/planning_completion_contract_test.dart.md) |
| `planning_scope_contract_test.dart` | 4 | [Details](mobile-failures/planning_scope_contract_test.dart.md) |
| `rental_availability_test.dart` | 5 | [Details](mobile-failures/rental_availability_test.dart.md) |
| `rental_home_sections_test.dart` | 1 | [Details](mobile-failures/rental_home_sections_test.dart.md) |
| `rental_interest_creation_test.dart` | 1 | [Details](mobile-failures/rental_interest_creation_test.dart.md) |
| `rental_listing_categories_test.dart` | 4 | [Details](mobile-failures/rental_listing_categories_test.dart.md) |
| `rental_mock_provider_test.dart` | 1 | [Details](mobile-failures/rental_mock_provider_test.dart.md) |
| `rental_mutation_recovery_test.dart` | 4 | [Details](mobile-failures/rental_mutation_recovery_test.dart.md) |
| `replacement_consent_flow_test.dart` | 3 | [Details](mobile-failures/replacement_consent_flow_test.dart.md) |
| `screen_audit_test.dart` | 24 | [Details](mobile-failures/screen_audit_test.dart.md) |
| `sokoun_date_field_test.dart` | 2 | [Details](mobile-failures/sokoun_date_field_test.dart.md) |
| `sokoun_refresh_indicator_test.dart` | 4 | [Details](mobile-failures/sokoun_refresh_indicator_test.dart.md) |
| `splash_startup_test.dart` | 5 | [Details](mobile-failures/splash_startup_test.dart.md) |
| `static_data_integration_test.dart` | 1 | [Details](mobile-failures/static_data_integration_test.dart.md) |
| `student_event_navigation_test.dart` | 5 | [Details](mobile-failures/student_event_navigation_test.dart.md) |
| `student_housing_test.dart` | 1 | [Details](mobile-failures/student_housing_test.dart.md) |
| `student_profile_contract_workspace_test.dart` | 6 | [Details](mobile-failures/student_profile_contract_workspace_test.dart.md) |
| `tenancy_invitations_flow_test.dart` | 2 | [Details](mobile-failures/tenancy_invitations_flow_test.dart.md) |
| `tenant_planning_locale_test.dart` | 1 | [Details](mobile-failures/tenant_planning_locale_test.dart.md) |
| `tenant_property_details_screen_test.dart` | 1 | [Details](mobile-failures/tenant_property_details_screen_test.dart.md) |
| `transition_network_test.dart` | 3 | [Details](mobile-failures/transition_network_test.dart.md) |
| `ui_refactor_remaining_ux_test.dart` | 4 | [Details](mobile-failures/ui_refactor_remaining_ux_test.dart.md) |
| `ux60_chat_suggested_draft_test.dart` | 1 | [Details](mobile-failures/ux60_chat_suggested_draft_test.dart.md) |
| `visit_collection_count_test.dart` | 7 | [Details](mobile-failures/visit_collection_count_test.dart.md) |
| `workspace_feature_access_test.dart` | 9 | [Details](mobile-failures/workspace_feature_access_test.dart.md) |
| `workspace_navigation_clearance_test.dart` | 11 | [Details](mobile-failures/workspace_navigation_clearance_test.dart.md) |
| `workspace_navigation_test.dart` | 2 | [Details](mobile-failures/workspace_navigation_test.dart.md) |
| `workspace_switcher_design_test.dart` | 5 | [Details](mobile-failures/workspace_switcher_design_test.dart.md) |

# Backend execution results

Results are reconciled by exact pytest classname and test name, including parameter IDs. A passing supplemental execution supersedes an earlier environmental setup error or engine skip.

```json
{
  "unique_cases": 6202,
  "counts": {
    "passed": 6168,
    "skipped": 22,
    "xfail": 12
  },
  "attempts": [
    {
      "file": "backend/mvp/junit.xml",
      "counts": {
        "passed": 5691,
        "skipped": 489,
        "xfail": 10,
        "error": 12
      }
    },
    {
      "file": "backend-http-rerun.xml",
      "counts": {
        "passed": 40,
        "skipped": 10
      }
    },
    {
      "file": "backend-postgres.xml",
      "counts": {
        "passed": 477,
        "skipped": 5,
        "xfail": 2
      }
    }
  ]
}
```

The 12 setup errors in the original full run were loopback socket restrictions. Seven passed in the HTTP rerun; the remaining five funded/ongoing cycles passed on PostgreSQL. No unexpected failure remains among the executed backend cases.

## Still skipped or expected to fail

| Test | Result | Reason |
|---|---|---|
| `core_apps.chat.tests.test_group_native_media::test_native_recording_upload_send_and_other_member_download[ANDROID]` | skipped | Provide CHAT_NATIVE_ANDROID_CLIP from the native voice spike |
| `core_apps.chat.tests.test_group_native_media::test_native_recording_upload_send_and_other_member_download[IOS]` | skipped | Provide CHAT_NATIVE_IOS_CLIP from the native voice spike |
| `core_apps.chat.tests.test_reactions_mentions::test_company_discussion_mentions_and_reactions_follow_case_membership` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.common.test_recovery_postgres::test_concurrent_dispatch_has_one_original_transport` | skipped | Independent PostgreSQL drill cluster not supplied |
| `core_apps.common.test_recovery_postgres::test_primary_cluster_and_privileged_role_are_rejected` | skipped | Independent PostgreSQL drill cluster not supplied |
| `core_apps.common.test_recovery_postgres::test_primary_rollback_does_not_erase_durable_external_fact` | skipped | Independent PostgreSQL drill cluster not supplied |
| `core_apps.common.test_recovery_postgres::test_runtime_role_cannot_mutate_or_delete_history` | skipped | Independent PostgreSQL drill cluster not supplied |
| `core_apps.common.test_recovery_postgres::test_unknown_outcome_survives_reconnection_and_never_resends` | skipped | Independent PostgreSQL drill cluster not supplied |
| `core_apps.features.tests.test_advanced_company_passport_v2::test_two_company_packages_mock_sign_payment_and_uncertain_reconciliation` | xfail | BUG-AUTH-01: company_sign/company_pay require member_for() membership flags while the HTTP signer/payer role exists only through approved mandates; no member can satisfy both. Needs a product decision on the signing/payment authority model. |
| `core_apps.features.tests.test_company_discussions::test_company_chat_tools_keep_coordinator_and_personal_boundaries` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_company_discussions::test_company_push_retry_rechecks_revoked_membership` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_company_discussions::test_company_retry_rejects_wrong_period_and_authority_revocation` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_company_discussions::test_company_role_loss_revokes_private_attachments_and_delayed_notifications` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_company_discussions::test_concurrent_case_send_uses_one_canonical_message` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_company_discussions::test_discussion_grants_case_access_and_never_approves_from_text` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_company_discussions::test_late_original_and_company_retry_commit_once` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_company_discussions::test_reassignment_revokes_old_actor_and_preserves_business_history` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_company_discussions::test_unknown_company_send_can_retry_exact_identity_with_membership_fence` | xfail | Company discussions are deliberately locked: role_routes refuses company_chat_views with company_role_audience_required until every message has a verified role audience. |
| `core_apps.features.tests.test_flutter_request_roundtrip::test_flutter_commute_and_assistant_bodies` | skipped | Generate fresh Flutter request bodies with the documented Make targets |
| `core_apps.features.tests.test_flutter_request_roundtrip::test_flutter_condition_create_and_acknowledgement_roundtrip` | skipped | Generate fresh Flutter request bodies with the documented Make targets |
| `core_apps.features.tests.test_flutter_request_roundtrip::test_flutter_cost_proposal_body` | skipped | Generate fresh Flutter request bodies with the documented Make targets |
| `core_apps.features.tests.test_flutter_request_roundtrip::test_flutter_housing_request_and_authoritative_offer_bodies` | skipped | Generate fresh Flutter request bodies with the documented Make targets |
| `core_apps.features.tests.test_flutter_request_roundtrip::test_flutter_incoming_replacement_consent_body` | skipped | Generate fresh Flutter request bodies with the documented Make targets |
| `core_apps.features.tests.test_flutter_request_roundtrip::test_flutter_invite_body` | skipped | Generate fresh Flutter request bodies with the documented Make targets |
| `core_apps.features.tests.test_flutter_request_roundtrip::test_flutter_notice_body` | skipped | Generate fresh Flutter request bodies with the documented Make targets |
| `core_apps.features.tests.test_flutter_request_roundtrip::test_flutter_refund_body_and_recovery_subject` | skipped | Generate fresh Flutter request bodies with the documented Make targets |
| `core_apps.features.tests.test_purchase_events::test_company_recipients_and_retries_require_current_read_authority[after_failed_push]` | xfail | BUG-AUTH-01: a member with can_execute_payments but no approved pay mandate has billing authority yet no selectable company role, so their company notice is suppressed at delivery. |
| `core_apps.profiles.tests.test_avatar_ownership::test_borrowed_reference_is_refused_on_every_avatar_input[https://res.cloudinary.com/test_cloud/image/upload/v1/someone-elses-avatar.jpg-image-profile-update]` | skipped | aliases exist only on the edit screen |
| `core_apps.profiles.tests.test_avatar_ownership::test_borrowed_reference_is_refused_on_every_avatar_input[https://res.cloudinary.com/test_cloud/image/upload/v1/someone-elses-avatar.jpg-profile_image-profile-update]` | skipped | aliases exist only on the edit screen |
| `core_apps.profiles.tests.test_avatar_ownership::test_borrowed_reference_is_refused_on_every_avatar_input[image/upload/v1700000000/someone-elses-avatar-image-profile-update]` | skipped | aliases exist only on the edit screen |
| `core_apps.profiles.tests.test_avatar_ownership::test_borrowed_reference_is_refused_on_every_avatar_input[image/upload/v1700000000/someone-elses-avatar-profile_image-profile-update]` | skipped | aliases exist only on the edit screen |
| `core_apps.virtual_tours.tests.test_capture::test_partial_panorama_does_not_become_full_tour` | skipped | could not import 'cv2': No module named 'cv2' |
| `core_apps.virtual_tours.tests.test_capture_config::test_strict_preflight_requires_successful_requested_provider_probe[live]` | skipped | Capture readiness needs OpenCV (not in Pipfile.lock) |
| `core_apps.virtual_tours.tests.test_models_and_boundaries::test_real_khronos_and_rapier_processing` | skipped | Run `npm ci` in tools/virtual_tours to install the locked Khronos/Rapier validators |

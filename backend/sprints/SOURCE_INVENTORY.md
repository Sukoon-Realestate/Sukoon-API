# Source scan inventory

Baseline `785dfc1d`, 2026-11-08. All 2,018 tracked Python files below parsed successfully. The structural scan covers
1,196 application/configuration files; seven backend scripts have an additional assigned review scope. Other tracked tools,
management commands, migrations and tests received syntax inventory and selected supporting traces, not exhaustive semantic review.

“Structural + selected trace” means every file in that scope was statically inventoried; manual depth varied. It does not mean
every file/branch was deeply read. Area reports describe the actual selected traces; Area 2 additionally records 84 deeper file/path reviews.

## Review ownership

| Area | Final assigned files | Scope |
|---|---:|---|
| [1](findings/area-1.md) | 86 | Identity/profiles |
| [2](findings/area-2.md) | 186 | Properties/visits/tours |
| [3](findings/area-3.md) | 467 | Rentals/housing/planning |
| [4](findings/area-4.md) | 126 | Commerce/providers/advertising |
| [5](findings/area-5.md) | 160 | Communication/support |
| [6](findings/area-6.md) | 178 | Admin/shared/config/scripts |

Store notification and fulfillment-case modules are owned by Area 4 after boundary review. Area 3 scanned them in its
initial 469-file list, so its original scope count and the final ownership count differ by two; no files were silently dropped.

## core_apps/users

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/users/__init__.py](../core_apps/users/__init__.py) | Structural + selected trace | 1 | 0 / 0 |
| [core_apps/users/admin.py](../core_apps/users/admin.py) | Structural + selected trace | 6 | 116 / 6 |
| [core_apps/users/apps.py](../core_apps/users/apps.py) | Structural + selected trace | 1 | 11 / 1 |
| [core_apps/users/closure_models.py](../core_apps/users/closure_models.py) | Structural + selected trace | 1 | 65 / 0 |
| [core_apps/users/closure_views.py](../core_apps/users/closure_views.py) | Structural + selected trace | 1 | 117 / 7 |
| [core_apps/users/email_change_views.py](../core_apps/users/email_change_views.py) | Structural + selected trace | 1 | 37 / 2 |
| [core_apps/users/emails.py](../core_apps/users/emails.py) | Structural + selected trace | 1 | 49 / 3 |
| [core_apps/users/forms.py](../core_apps/users/forms.py) | Structural + selected trace | 1 | 29 / 1 |
| [core_apps/users/journey.py](../core_apps/users/journey.py) | Structural + selected trace | 1 | 65 / 4 |
| [core_apps/users/managers.py](../core_apps/users/managers.py) | Structural + selected trace | 1 | 44 / 4 |
| [core_apps/users/migrations/0001_initial.py](../core_apps/users/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0002_socialaccount_socialaccount_uniq_provider_uid.py](../core_apps/users/migrations/0002_socialaccount_socialaccount_uniq_provider_uid.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0003_user_is_verified.py](../core_apps/users/migrations/0003_user_is_verified.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0004_authsession_user_security_epoch_and_more.py](../core_apps/users/migrations/0004_authsession_user_security_epoch_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0005_user_is_email_verified.py](../core_apps/users/migrations/0005_user_is_email_verified.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0006_session_metadata.py](../core_apps/users/migrations/0006_session_metadata.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0007_email_change.py](../core_apps/users/migrations/0007_email_change.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0008_unique_email.py](../core_apps/users/migrations/0008_unique_email.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0009_bound_email_session.py](../core_apps/users/migrations/0009_bound_email_session.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0010_staffsecurityidentity_and_more.py](../core_apps/users/migrations/0010_staffsecurityidentity_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0011_alter_totpenrollment_options_and_more.py](../core_apps/users/migrations/0011_alter_totpenrollment_options_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0012_accountclosuredecision_accountclosurerequest_and_more.py](../core_apps/users/migrations/0012_accountclosuredecision_accountclosurerequest_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0013_accountprofileerasurefile_storage_type.py](../core_apps/users/migrations/0013_accountprofileerasurefile_storage_type.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/0014_staff_setup_and_beneficiary_details.py](../core_apps/users/migrations/0014_staff_setup_and_beneficiary_details.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/migrations/__init__.py](../core_apps/users/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/users/models.py](../core_apps/users/models.py) | Structural + selected trace | 1 | 165 / 3 |
| [core_apps/users/rest_urls.py](../core_apps/users/rest_urls.py) | Structural + selected trace | 1 | 78 / 6 |
| [core_apps/users/security_views.py](../core_apps/users/security_views.py) | Structural + selected trace | 1 | 105 / 4 |
| [core_apps/users/serializers.py](../core_apps/users/serializers.py) | Structural + selected trace | 1 | 28 / 0 |
| [core_apps/users/serializers_parts/__init__.py](../core_apps/users/serializers_parts/__init__.py) | Structural + selected trace | 1 | 1 / 0 |
| [core_apps/users/serializers_parts/create_user_serializer.py](../core_apps/users/serializers_parts/create_user_serializer.py) | Structural + selected trace | 1 | 176 / 8 |
| [core_apps/users/serializers_parts/set_user_password_serializer.py](../core_apps/users/serializers_parts/set_user_password_serializer.py) | Structural + selected trace | 1 | 131 / 5 |
| [core_apps/users/services/__init__.py](../core_apps/users/services/__init__.py) | Structural + selected trace | 1 | 18 / 0 |
| [core_apps/users/services/account_closure.py](../core_apps/users/services/account_closure.py) | Structural + selected trace | 1 | 369 / 15 |
| [core_apps/users/services/apple_dev_key.py](../core_apps/users/services/apple_dev_key.py) | Structural + selected trace | 1 | 73 / 3 |
| [core_apps/users/services/assurance.py](../core_apps/users/services/assurance.py) | Structural + selected trace | 1 | 78 / 2 |
| [core_apps/users/services/closure_blockers.py](../core_apps/users/services/closure_blockers.py) | Structural + selected trace | 1 | 174 / 2 |
| [core_apps/users/services/closure_delivery.py](../core_apps/users/services/closure_delivery.py) | Structural + selected trace | 1 | 86 / 2 |
| [core_apps/users/services/email_change.py](../core_apps/users/services/email_change.py) | Structural + selected trace | 1 | 299 / 6 |
| [core_apps/users/services/identity_submission.py](../core_apps/users/services/identity_submission.py) | Structural + selected trace | 1 | 132 / 5 |
| [core_apps/users/services/new_business.py](../core_apps/users/services/new_business.py) | Structural + selected trace | 1 | 73 / 3 |
| [core_apps/users/services/otp_service.py](../core_apps/users/services/otp_service.py) | Structural + selected trace | 1 | 245 / 5 |
| [core_apps/users/services/recovery_tokens.py](../core_apps/users/services/recovery_tokens.py) | Structural + selected trace | 1 | 12 / 1 |
| [core_apps/users/services/security_notices.py](../core_apps/users/services/security_notices.py) | Structural + selected trace | 1 | 69 / 1 |
| [core_apps/users/services/sensitive_actions.py](../core_apps/users/services/sensitive_actions.py) | Structural + selected trace | 1 | 225 / 8 |
| [core_apps/users/services/session_management.py](../core_apps/users/services/session_management.py) | Structural + selected trace | 1 | 149 / 6 |
| [core_apps/users/services/sessions.py](../core_apps/users/services/sessions.py) | Structural + selected trace | 1 | 106 / 4 |
| [core_apps/users/services/social_auth_service.py](../core_apps/users/services/social_auth_service.py) | Structural + selected trace | 1 | 30 / 0 |
| [core_apps/users/services/social_auth_service_parts/__init__.py](../core_apps/users/services/social_auth_service_parts/__init__.py) | Structural + selected trace | 1 | 1 / 0 |
| [core_apps/users/services/social_auth_service_parts/authenticate_apple.py](../core_apps/users/services/social_auth_service_parts/authenticate_apple.py) | Structural + selected trace | 1 | 102 / 3 |
| [core_apps/users/services/social_auth_service_parts/get_or_create_social_user.py](../core_apps/users/services/social_auth_service_parts/get_or_create_social_user.py) | Structural + selected trace | 1 | 184 / 7 |
| [core_apps/users/services/staff_setup.py](../core_apps/users/services/staff_setup.py) | Structural + selected trace | 1 | 250 / 7 |
| [core_apps/users/services/totp.py](../core_apps/users/services/totp.py) | Structural + selected trace | 1 | 115 / 10 |
| [core_apps/users/services/totp_recovery.py](../core_apps/users/services/totp_recovery.py) | Structural + selected trace | 1 | 504 / 16 |
| [core_apps/users/services/user_service.py](../core_apps/users/services/user_service.py) | Structural + selected trace | 1 | 194 / 4 |
| [core_apps/users/signals.py](../core_apps/users/signals.py) | Structural + selected trace | 1 | 30 / 1 |
| [core_apps/users/tasks.py](../core_apps/users/tasks.py) | Structural + selected trace | 1 | 10 / 1 |
| [core_apps/users/tests/__init__.py](../core_apps/users/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_account_closure.py](../core_apps/users/tests/test_account_closure.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_admin_creation.py](../core_apps/users/tests/test_admin_creation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_admin_session_revocation.py](../core_apps/users/tests/test_admin_session_revocation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_administrative_suspension.py](../core_apps/users/tests/test_administrative_suspension.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_audit_identity.py](../core_apps/users/tests/test_audit_identity.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_complete_register.py](../core_apps/users/tests/test_complete_register.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_device_management.py](../core_apps/users/tests/test_device_management.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_email_change.py](../core_apps/users/tests/test_email_change.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_identity_delivery_fences.py](../core_apps/users/tests/test_identity_delivery_fences.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_mobile_user_contract.py](../core_apps/users/tests/test_mobile_user_contract.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_models.py](../core_apps/users/tests/test_models.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_mvp_account_authorization.py](../core_apps/users/tests/test_mvp_account_authorization.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_mvp_closure_authority.py](../core_apps/users/tests/test_mvp_closure_authority.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_mvp_closure_support.py](../core_apps/users/tests/test_mvp_closure_support.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_mvp_email_change_binding.py](../core_apps/users/tests/test_mvp_email_change_binding.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_new_business_locking.py](../core_apps/users/tests/test_new_business_locking.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_otp_action_expiry.py](../core_apps/users/tests/test_otp_action_expiry.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_otp_services.py](../core_apps/users/tests/test_otp_services.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_otp_views.py](../core_apps/users/tests/test_otp_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_security_recovery.py](../core_apps/users/tests/test_security_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_serializers.py](../core_apps/users/tests/test_serializers.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_services.py](../core_apps/users/tests/test_services.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_set_password.py](../core_apps/users/tests/test_set_password.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_social_views.py](../core_apps/users/tests/test_social_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_staff_initial_setup.py](../core_apps/users/tests/test_staff_initial_setup.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_totp_recovery.py](../core_apps/users/tests/test_totp_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/tests/test_views.py](../core_apps/users/tests/test_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/users/token_serializers.py](../core_apps/users/token_serializers.py) | Structural + selected trace | 1 | 48 / 3 |
| [core_apps/users/totp_models.py](../core_apps/users/totp_models.py) | Structural + selected trace | 1 | 118 / 0 |
| [core_apps/users/totp_views.py](../core_apps/users/totp_views.py) | Structural + selected trace | 1 | 129 / 11 |
| [core_apps/users/urls.py](../core_apps/users/urls.py) | Structural + selected trace | 1 | 71 / 0 |
| [core_apps/users/views.py](../core_apps/users/views.py) | Structural + selected trace | 1 | 74 / 0 |
| [core_apps/users/views_parts/__init__.py](../core_apps/users/views_parts/__init__.py) | Structural + selected trace | 1 | 1 / 0 |
| [core_apps/users/views_parts/set_auth_cookies.py](../core_apps/users/views_parts/set_auth_cookies.py) | Structural + selected trace | 1 | 172 / 7 |
| [core_apps/users/views_parts/user_delete_apiview.py](../core_apps/users/views_parts/user_delete_apiview.py) | Structural + selected trace | 1 | 151 / 5 |
| [core_apps/users/views_parts/verify_email_apiview.py](../core_apps/users/views_parts/verify_email_apiview.py) | Structural + selected trace | 1 | 190 / 5 |

## core_apps/profiles

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/profiles/__init__.py](../core_apps/profiles/__init__.py) | Structural + selected trace | 1 | 0 / 0 |
| [core_apps/profiles/admin.py](../core_apps/profiles/admin.py) | Structural + selected trace | 6 | 27 / 0 |
| [core_apps/profiles/apps.py](../core_apps/profiles/apps.py) | Structural + selected trace | 1 | 11 / 1 |
| [core_apps/profiles/identity_expiry.py](../core_apps/profiles/identity_expiry.py) | Structural + selected trace | 1 | 107 / 6 |
| [core_apps/profiles/identity_expiry_views.py](../core_apps/profiles/identity_expiry_views.py) | Structural + selected trace | 1 | 50 / 3 |
| [core_apps/profiles/identity_media.py](../core_apps/profiles/identity_media.py) | Structural + selected trace | 1 | 168 / 5 |
| [core_apps/profiles/identity_recovery.py](../core_apps/profiles/identity_recovery.py) | Structural + selected trace | 1 | 21 / 1 |
| [core_apps/profiles/identity_status.py](../core_apps/profiles/identity_status.py) | Structural + selected trace | 1 | 76 / 4 |
| [core_apps/profiles/identity_views.py](../core_apps/profiles/identity_views.py) | Structural + selected trace | 1 | 24 / 1 |
| [core_apps/profiles/management/__init__.py](../core_apps/profiles/management/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/profiles/management/commands/__init__.py](../core_apps/profiles/management/commands/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/profiles/management/commands/protect_identity_media.py](../core_apps/profiles/management/commands/protect_identity_media.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/profiles/management/commands/review_legacy_identity.py](../core_apps/profiles/management/commands/review_legacy_identity.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0001_initial.py](../core_apps/profiles/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0002_initial.py](../core_apps/profiles/migrations/0002_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0003_add_kyc_fields.py](../core_apps/profiles/migrations/0003_add_kyc_fields.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0004_profile_avatar_alter_profile_confirmation_selfi_and_more.py](../core_apps/profiles/migrations/0004_profile_avatar_alter_profile_confirmation_selfi_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0005_profile_phone_number.py](../core_apps/profiles/migrations/0005_profile_phone_number.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0006_usersettings.py](../core_apps/profiles/migrations/0006_usersettings.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0007_add_notification_settings_fields.py](../core_apps/profiles/migrations/0007_add_notification_settings_fields.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0008_profile_city.py](../core_apps/profiles/migrations/0008_profile_city.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0009_contract.py](../core_apps/profiles/migrations/0009_contract.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0010_usersettings_revision_notificationpreferencechange_and_more.py](../core_apps/profiles/migrations/0010_usersettings_revision_notificationpreferencechange_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0011_alter_profile_gender.py](../core_apps/profiles/migrations/0011_alter_profile_gender.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0012_usersettings_typing_indicator.py](../core_apps/profiles/migrations/0012_usersettings_typing_indicator.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/0013_identity_document_expiry.py](../core_apps/profiles/migrations/0013_identity_document_expiry.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/migrations/__init__.py](../core_apps/profiles/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/profiles/models.py](../core_apps/profiles/models.py) | Structural + selected trace | 1 | 210 / 3 |
| [core_apps/profiles/pipeline.py](../core_apps/profiles/pipeline.py) | Structural + selected trace | 1 | 5 / 1 |
| [core_apps/profiles/serializers.py](../core_apps/profiles/serializers.py) | Structural + selected trace | 1 | 46 / 0 |
| [core_apps/profiles/serializers_parts/__init__.py](../core_apps/profiles/serializers_parts/__init__.py) | Structural + selected trace | 1 | 1 / 0 |
| [core_apps/profiles/serializers_parts/profile_edit_serializer.py](../core_apps/profiles/serializers_parts/profile_edit_serializer.py) | Structural + selected trace | 1 | 119 / 5 |
| [core_apps/profiles/serializers_parts/tenant_my_rate_serializer.py](../core_apps/profiles/serializers_parts/tenant_my_rate_serializer.py) | Structural + selected trace | 1 | 84 / 2 |
| [core_apps/profiles/serializers_parts/update_profile_serializer.py](../core_apps/profiles/serializers_parts/update_profile_serializer.py) | Structural + selected trace | 1 | 224 / 9 |
| [core_apps/profiles/serializers_parts/user_settings_serializer.py](../core_apps/profiles/serializers_parts/user_settings_serializer.py) | Structural + selected trace | 1 | 175 / 3 |
| [core_apps/profiles/services/__init__.py](../core_apps/profiles/services/__init__.py) | Structural + selected trace | 1 | 3 / 0 |
| [core_apps/profiles/services/contract_projection.py](../core_apps/profiles/services/contract_projection.py) | Structural + selected trace | 1 | 139 / 6 |
| [core_apps/profiles/services/mvp_counts.py](../core_apps/profiles/services/mvp_counts.py) | Structural + selected trace | 1 | 26 / 1 |
| [core_apps/profiles/services/profile_service.py](../core_apps/profiles/services/profile_service.py) | Structural + selected trace | 1 | 23 / 0 |
| [core_apps/profiles/services/profile_service_parts/__init__.py](../core_apps/profiles/services/profile_service_parts/__init__.py) | Structural + selected trace | 1 | 1 / 0 |
| [core_apps/profiles/services/profile_service_parts/account_metadata.py](../core_apps/profiles/services/profile_service_parts/account_metadata.py) | Structural + selected trace | 1 | 32 / 3 |
| [core_apps/profiles/services/profile_service_parts/arabic_months.py](../core_apps/profiles/services/profile_service_parts/arabic_months.py) | Structural + selected trace | 1 | 63 / 4 |
| [core_apps/profiles/services/profile_service_parts/profile_service.py](../core_apps/profiles/services/profile_service_parts/profile_service.py) | Structural + selected trace | 1 | 22 / 0 |
| [core_apps/profiles/services/profile_service_parts/profile_service_operations/__init__.py](../core_apps/profiles/services/profile_service_parts/profile_service_operations/__init__.py) | Structural + selected trace | 1 | 1 / 0 |
| [core_apps/profiles/services/profile_service_parts/profile_service_operations/profile_account.py](../core_apps/profiles/services/profile_service_parts/profile_service_operations/profile_account.py) | Structural + selected trace | 1 | 134 / 2 |
| [core_apps/profiles/services/profile_service_parts/profile_service_operations/profile_edit.py](../core_apps/profiles/services/profile_service_parts/profile_service_operations/profile_edit.py) | Structural + selected trace | 1 | 166 / 4 |
| [core_apps/profiles/services/profile_service_parts/profile_service_operations/profile_status.py](../core_apps/profiles/services/profile_service_parts/profile_service_operations/profile_status.py) | Structural + selected trace | 1 | 143 / 2 |
| [core_apps/profiles/services/profile_service_parts/profile_service_operations/profile_unread.py](../core_apps/profiles/services/profile_service_parts/profile_service_operations/profile_unread.py) | Structural + selected trace | 1 | 116 / 2 |
| [core_apps/profiles/signals.py](../core_apps/profiles/signals.py) | Structural + selected trace | 1 | 23 / 1 |
| [core_apps/profiles/tasks.py](../core_apps/profiles/tasks.py) | Structural + selected trace | 1 | 7 / 1 |
| [core_apps/profiles/tests/__init__.py](../core_apps/profiles/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_audit_privacy.py](../core_apps/profiles/tests/test_audit_privacy.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_contract_projection.py](../core_apps/profiles/tests/test_contract_projection.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_identity_corrections.py](../core_apps/profiles/tests/test_identity_corrections.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_identity_expiry.py](../core_apps/profiles/tests/test_identity_expiry.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_identity_image_formats.py](../core_apps/profiles/tests/test_identity_image_formats.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_identity_media.py](../core_apps/profiles/tests/test_identity_media.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_legacy_identity_review.py](../core_apps/profiles/tests/test_legacy_identity_review.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_models.py](../core_apps/profiles/tests/test_models.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_mvp_profile_authority.py](../core_apps/profiles/tests/test_mvp_profile_authority.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_mvp_record_counts.py](../core_apps/profiles/tests/test_mvp_record_counts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_mvp_review_note_privacy.py](../core_apps/profiles/tests/test_mvp_review_note_privacy.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_my_account_locale.py](../core_apps/profiles/tests/test_my_account_locale.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_screen_views.py](../core_apps/profiles/tests/test_screen_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_services.py](../core_apps/profiles/tests/test_services.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_settings_api.py](../core_apps/profiles/tests/test_settings_api.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_unread_counts_and_my_rates.py](../core_apps/profiles/tests/test_unread_counts_and_my_rates.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_verification_and_contracts.py](../core_apps/profiles/tests/test_verification_and_contracts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/tests/test_views.py](../core_apps/profiles/tests/test_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/profiles/urls.py](../core_apps/profiles/urls.py) | Structural + selected trace | 1 | 58 / 0 |
| [core_apps/profiles/views.py](../core_apps/profiles/views.py) | Structural + selected trace | 1 | 54 / 0 |
| [core_apps/profiles/views_parts/__init__.py](../core_apps/profiles/views_parts/__init__.py) | Structural + selected trace | 1 | 1 / 0 |
| [core_apps/profiles/views_parts/profile_edit_apiview.py](../core_apps/profiles/views_parts/profile_edit_apiview.py) | Structural + selected trace | 1 | 165 / 11 |
| [core_apps/profiles/views_parts/user_settings_apiview.py](../core_apps/profiles/views_parts/user_settings_apiview.py) | Structural + selected trace | 1 | 189 / 8 |

## core_apps/properties

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/properties/__init__.py](../core_apps/properties/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/admin.py](../core_apps/properties/admin.py) | Structural + selected trace | 6 | 299 / 19 |
| [core_apps/properties/apps.py](../core_apps/properties/apps.py) | Structural + selected trace | 2 | 11 / 1 |
| [core_apps/properties/catalog_access.py](../core_apps/properties/catalog_access.py) | Structural + selected trace | 2 | 70 / 4 |
| [core_apps/properties/catalog_labels.py](../core_apps/properties/catalog_labels.py) | Structural + selected trace | 2 | 108 / 4 |
| [core_apps/properties/filters.py](../core_apps/properties/filters.py) | Structural + selected trace | 2 | 156 / 9 |
| [core_apps/properties/management/commands/rebuild_property_search.py](../core_apps/properties/management/commands/rebuild_property_search.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/properties/media_signals.py](../core_apps/properties/media_signals.py) | Structural + selected trace | 2 | 28 / 2 |
| [core_apps/properties/migrations/0001_initial.py](../core_apps/properties/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0002_alter_property_suitable_for.py](../core_apps/properties/migrations/0002_alter_property_suitable_for.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0003_propertyimage_description_propertyimage_name.py](../core_apps/properties/migrations/0003_propertyimage_description_propertyimage_name.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0004_property_property_location_idx_and_more.py](../core_apps/properties/migrations/0004_property_property_location_idx_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0005_property_main_image.py](../core_apps/properties/migrations/0005_property_main_image.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0006_property_space.py](../core_apps/properties/migrations/0006_property_space.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0007_propertyvisit_and_more.py](../core_apps/properties/migrations/0007_propertyvisit_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0008_property_status.py](../core_apps/properties/migrations/0008_property_status.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0009_property_type_dynamic.py](../core_apps/properties/migrations/0009_property_type_dynamic.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0010_property_engagement_and_availability.py](../core_apps/properties/migrations/0010_property_engagement_and_availability.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0011_governorate_city_property_locations.py](../core_apps/properties/migrations/0011_governorate_city_property_locations.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0012_alter_city_slug_alter_governorate_slug.py](../core_apps/properties/migrations/0012_alter_city_slug_alter_governorate_slug.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0013_remove_property_country.py](../core_apps/properties/migrations/0013_remove_property_country.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0014_propertyvisitreview.py](../core_apps/properties/migrations/0014_propertyvisitreview.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0015_owneravailabilityslot_property.py](../core_apps/properties/migrations/0015_owneravailabilityslot_property.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0016_alter_property_status.py](../core_apps/properties/migrations/0016_alter_property_status.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0017_property_video_property_video_duration.py](../core_apps/properties/migrations/0017_property_video_property_video_duration.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0018_property_mobile_handoff.py](../core_apps/properties/migrations/0018_property_mobile_handoff.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0019_remove_savedproperty_unique_saved_property_and_more.py](../core_apps/properties/migrations/0019_remove_savedproperty_unique_saved_property_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0020_propertyvisit_accepted_at.py](../core_apps/properties/migrations/0020_propertyvisit_accepted_at.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0021_planning_report_integrity.py](../core_apps/properties/migrations/0021_planning_report_integrity.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0022_company_portfolio_foundations.py](../core_apps/properties/migrations/0022_company_portfolio_foundations.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0023_portfolio_batch_recovery.py](../core_apps/properties/migrations/0023_portfolio_batch_recovery.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0024_portfoliochangeset_residentialmedia_and_more.py](../core_apps/properties/migrations/0024_portfoliochangeset_residentialmedia_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0025_residentialbuilding_commercial_revision_and_more.py](../core_apps/properties/migrations/0025_residentialbuilding_commercial_revision_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0026_alter_portfoliochangeset_options_and_more.py](../core_apps/properties/migrations/0026_alter_portfoliochangeset_options_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0027_district_property_district_catalog_and_more.py](../core_apps/properties/migrations/0027_district_property_district_catalog_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0028_propertyvisit_academic_plan_propertyvisit_company_and_more.py](../core_apps/properties/migrations/0028_propertyvisit_academic_plan_propertyvisit_company_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0029_propertyvisit_stay_preferences.py](../core_apps/properties/migrations/0029_propertyvisit_stay_preferences.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0030_propertyrequest.py](../core_apps/properties/migrations/0030_propertyrequest.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0030_propertyvisit_renter_workspace.py](../core_apps/properties/migrations/0030_propertyvisit_renter_workspace.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0031_merge_20261024_1458.py](../core_apps/properties/migrations/0031_merge_20261024_1458.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0032_image_order.py](../core_apps/properties/migrations/0032_image_order.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0033_discovery_and_push.py](../core_apps/properties/migrations/0033_discovery_and_push.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0034_search_backfill.py](../core_apps/properties/migrations/0034_search_backfill.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0035_visit_requests_without_schedule.py](../core_apps/properties/migrations/0035_visit_requests_without_schedule.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0036_property_review_versions.py](../core_apps/properties/migrations/0036_property_review_versions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0037_alter_city_options_alter_district_options_and_more.py](../core_apps/properties/migrations/0037_alter_city_options_alter_district_options_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0038_visit_change_history.py](../core_apps/properties/migrations/0038_visit_change_history.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0039_managed_property_types.py](../core_apps/properties/migrations/0039_managed_property_types.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0040_propertyimage_room_category.py](../core_apps/properties/migrations/0040_propertyimage_room_category.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0041_hidden_listing_preferences.py](../core_apps/properties/migrations/0041_hidden_listing_preferences.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0042_saved_search_read_watermarks.py](../core_apps/properties/migrations/0042_saved_search_read_watermarks.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0043_availability_closures.py](../core_apps/properties/migrations/0043_availability_closures.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0044_viewing_time_proposals.py](../core_apps/properties/migrations/0044_viewing_time_proposals.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/0045_viewing_arrival_cards.py](../core_apps/properties/migrations/0045_viewing_arrival_cards.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/migrations/__init__.py](../core_apps/properties/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/properties/models/__init__.py](../core_apps/properties/models/__init__.py) | Structural + selected trace | 2 | 24 / 0 |
| [core_apps/properties/models/availability_closure.py](../core_apps/properties/models/availability_closure.py) | Structural + selected trace | 2 | 16 / 0 |
| [core_apps/properties/models/engagement.py](../core_apps/properties/models/engagement.py) | Structural + selected trace | 2 | 100 / 3 |
| [core_apps/properties/models/hidden_listing.py](../core_apps/properties/models/hidden_listing.py) | Structural + selected trace | 2 | 21 / 0 |
| [core_apps/properties/models/location.py](../core_apps/properties/models/location.py) | Structural + selected trace | 2 | 166 / 7 |
| [core_apps/properties/models/moderation.py](../core_apps/properties/models/moderation.py) | Structural + selected trace | 2 | 18 / 0 |
| [core_apps/properties/models/portfolio.py](../core_apps/properties/models/portfolio.py) | Structural + selected trace | 2 | 169 / 0 |
| [core_apps/properties/models/property.py](../core_apps/properties/models/property.py) | Structural + selected trace | 2 | 291 / 5 |
| [core_apps/properties/models/property_type.py](../core_apps/properties/models/property_type.py) | Structural + selected trace | 2 | 27 / 1 |
| [core_apps/properties/models/saved_search_visit.py](../core_apps/properties/models/saved_search_visit.py) | Structural + selected trace | 2 | 36 / 0 |
| [core_apps/properties/models/viewing_arrival.py](../core_apps/properties/models/viewing_arrival.py) | Structural + selected trace | 2 | 13 / 0 |
| [core_apps/properties/models/viewing_time_proposal.py](../core_apps/properties/models/viewing_time_proposal.py) | Structural + selected trace | 2 | 15 / 0 |
| [core_apps/properties/models/visit.py](../core_apps/properties/models/visit.py) | Structural + selected trace | 2 | 20 / 0 |
| [core_apps/properties/models/visit_parts/__init__.py](../core_apps/properties/models/visit_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/models/visit_parts/property_visit.py](../core_apps/properties/models/visit_parts/property_visit.py) | Structural + selected trace | 2 | 271 / 6 |
| [core_apps/properties/models/visit_parts/property_visit_review.py](../core_apps/properties/models/visit_parts/property_visit_review.py) | Structural + selected trace | 2 | 58 / 1 |
| [core_apps/properties/ownership_proof.py](../core_apps/properties/ownership_proof.py) | Structural + selected trace | 2 | 45 / 3 |
| [core_apps/properties/permissions.py](../core_apps/properties/permissions.py) | Structural + selected trace | 2 | 33 / 3 |
| [core_apps/properties/phone_disclosure.py](../core_apps/properties/phone_disclosure.py) | Structural + selected trace | 2 | 13 / 2 |
| [core_apps/properties/rental_inventory.py](../core_apps/properties/rental_inventory.py) | Structural + selected trace | 2 | 20 / 0 |
| [core_apps/properties/rental_inventory_parts/__init__.py](../core_apps/properties/rental_inventory_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/rental_inventory_parts/inheritable.py](../core_apps/properties/rental_inventory_parts/inheritable.py) | Structural + selected trace | 2 | 42 / 2 |
| [core_apps/properties/rental_inventory_parts/normalize_inventory.py](../core_apps/properties/rental_inventory_parts/normalize_inventory.py) | Structural + selected trace | 2 | 200 / 1 |
| [core_apps/properties/rental_inventory_parts/offer_revision.py](../core_apps/properties/rental_inventory_parts/offer_revision.py) | Structural + selected trace | 2 | 43 / 1 |
| [core_apps/properties/search.py](../core_apps/properties/search.py) | Structural + selected trace | 2 | 117 / 2 |
| [core_apps/properties/serializers/__init__.py](../core_apps/properties/serializers/__init__.py) | Structural + selected trace | 2 | 36 / 0 |
| [core_apps/properties/serializers/engagement.py](../core_apps/properties/serializers/engagement.py) | Structural + selected trace | 2 | 83 / 4 |
| [core_apps/properties/serializers/location.py](../core_apps/properties/serializers/location.py) | Structural + selected trace | 2 | 63 / 4 |
| [core_apps/properties/serializers/owner_dashboard.py](../core_apps/properties/serializers/owner_dashboard.py) | Structural + selected trace | 2 | 31 / 0 |
| [core_apps/properties/serializers/owner_dashboard_parts/__init__.py](../core_apps/properties/serializers/owner_dashboard_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/serializers/owner_dashboard_parts/owner_dashboard_pending_visit_serializer.py](../core_apps/properties/serializers/owner_dashboard_parts/owner_dashboard_pending_visit_serializer.py) | Structural + selected trace | 2 | 172 / 2 |
| [core_apps/properties/serializers/owner_dashboard_parts/owner_profile_serializer.py](../core_apps/properties/serializers/owner_dashboard_parts/owner_profile_serializer.py) | Structural + selected trace | 2 | 29 / 0 |
| [core_apps/properties/serializers/property.py](../core_apps/properties/serializers/property.py) | Structural + selected trace | 2 | 43 / 0 |
| [core_apps/properties/serializers/property_parts/__init__.py](../core_apps/properties/serializers/property_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/serializers/property_parts/property_collection.py](../core_apps/properties/serializers/property_parts/property_collection.py) | Structural + selected trace | 2 | 51 / 2 |
| [core_apps/properties/serializers/property_parts/property_detail_serializer.py](../core_apps/properties/serializers/property_parts/property_detail_serializer.py) | Structural + selected trace | 2 | 184 / 9 |
| [core_apps/properties/serializers/property_parts/property_detail_serializer_operations/__init__.py](../core_apps/properties/serializers/property_parts/property_detail_serializer_operations/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/serializers/property_parts/property_detail_serializer_operations/property_detail_media.py](../core_apps/properties/serializers/property_parts/property_detail_serializer_operations/property_detail_media.py) | Structural + selected trace | 2 | 100 / 7 |
| [core_apps/properties/serializers/property_parts/property_list_serializer.py](../core_apps/properties/serializers/property_parts/property_list_serializer.py) | Structural + selected trace | 2 | 198 / 11 |
| [core_apps/properties/serializers/property_parts/property_new_list_serializer.py](../core_apps/properties/serializers/property_parts/property_new_list_serializer.py) | Structural + selected trace | 2 | 152 / 6 |
| [core_apps/properties/serializers/property_parts/property_serializer.py](../core_apps/properties/serializers/property_parts/property_serializer.py) | Structural + selected trace | 2 | 132 / 3 |
| [core_apps/properties/serializers/property_parts/property_serializer_operations/__init__.py](../core_apps/properties/serializers/property_parts/property_serializer_operations/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/serializers/property_parts/property_serializer_operations/property_validation.py](../core_apps/properties/serializers/property_parts/property_serializer_operations/property_validation.py) | Structural + selected trace | 2 | 141 / 6 |
| [core_apps/properties/serializers/property_parts/property_statistics_serializer.py](../core_apps/properties/serializers/property_parts/property_statistics_serializer.py) | Structural + selected trace | 2 | 76 / 0 |
| [core_apps/properties/serializers/visit.py](../core_apps/properties/serializers/visit.py) | Structural + selected trace | 2 | 69 / 0 |
| [core_apps/properties/serializers/visit_parts/__init__.py](../core_apps/properties/serializers/visit_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/serializers/visit_parts/owner_visit_request_card_serializer.py](../core_apps/properties/serializers/visit_parts/owner_visit_request_card_serializer.py) | Structural + selected trace | 2 | 141 / 7 |
| [core_apps/properties/serializers/visit_parts/owner_visit_request_detail_serializer.py](../core_apps/properties/serializers/visit_parts/owner_visit_request_detail_serializer.py) | Structural + selected trace | 2 | 122 / 5 |
| [core_apps/properties/serializers/visit_parts/property_visit_serializer.py](../core_apps/properties/serializers/visit_parts/property_visit_serializer.py) | Structural + selected trace | 2 | 174 / 3 |
| [core_apps/properties/serializers/visit_parts/tenant_visit_list_serializer.py](../core_apps/properties/serializers/visit_parts/tenant_visit_list_serializer.py) | Structural + selected trace | 2 | 113 / 9 |
| [core_apps/properties/serializers/visit_parts/tenant_visit_request_serializer.py](../core_apps/properties/serializers/visit_parts/tenant_visit_request_serializer.py) | Structural + selected trace | 2 | 178 / 10 |
| [core_apps/properties/serializers/visit_parts/visit_owner_serializer.py](../core_apps/properties/serializers/visit_parts/visit_owner_serializer.py) | Structural + selected trace | 2 | 102 / 6 |
| [core_apps/properties/serializers/visit_parts/visit_request_input_serializer.py](../core_apps/properties/serializers/visit_parts/visit_request_input_serializer.py) | Structural + selected trace | 2 | 100 / 4 |
| [core_apps/properties/services/__init__.py](../core_apps/properties/services/__init__.py) | Structural + selected trace | 2 | 4 / 0 |
| [core_apps/properties/services/availability_closures.py](../core_apps/properties/services/availability_closures.py) | Structural + selected trace | 2 | 47 / 3 |
| [core_apps/properties/services/engagement.py](../core_apps/properties/services/engagement.py) | Structural + selected trace | 2 | 24 / 2 |
| [core_apps/properties/services/hidden_listings.py](../core_apps/properties/services/hidden_listings.py) | Structural + selected trace | 2 | 74 / 3 |
| [core_apps/properties/services/image_uploads.py](../core_apps/properties/services/image_uploads.py) | Structural + selected trace | 2 | 188 / 5 |
| [core_apps/properties/services/listing_funnel.py](../core_apps/properties/services/listing_funnel.py) | Structural + selected trace | 2 | 22 / 1 |
| [core_apps/properties/services/listing_lock.py](../core_apps/properties/services/listing_lock.py) | Structural + selected trace | 2 | 35 / 1 |
| [core_apps/properties/services/moderation.py](../core_apps/properties/services/moderation.py) | Structural + selected trace | 2 | 267 / 7 |
| [core_apps/properties/services/owner_dashboard.py](../core_apps/properties/services/owner_dashboard.py) | Structural + selected trace | 2 | 17 / 0 |
| [core_apps/properties/services/owner_dashboard_operations/__init__.py](../core_apps/properties/services/owner_dashboard_operations/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/services/owner_dashboard_operations/owner_dashboard_overview.py](../core_apps/properties/services/owner_dashboard_operations/owner_dashboard_overview.py) | Structural + selected trace | 2 | 45 / 1 |
| [core_apps/properties/services/owner_dashboard_operations/owner_profile.py](../core_apps/properties/services/owner_dashboard_operations/owner_profile.py) | Structural + selected trace | 2 | 114 / 1 |
| [core_apps/properties/services/owner_dashboard_operations/owner_revenue.py](../core_apps/properties/services/owner_dashboard_operations/owner_revenue.py) | Structural + selected trace | 2 | 9 / 1 |
| [core_apps/properties/services/owner_revenues.py](../core_apps/properties/services/owner_revenues.py) | Structural + selected trace | 2 | 109 / 4 |
| [core_apps/properties/services/post_visit_decision.py](../core_apps/properties/services/post_visit_decision.py) | Structural + selected trace | 2 | 55 / 0 |
| [core_apps/properties/services/post_visit_decision_parts/__init__.py](../core_apps/properties/services/post_visit_decision_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/services/post_visit_decision_parts/continuation.py](../core_apps/properties/services/post_visit_decision_parts/continuation.py) | Structural + selected trace | 2 | 191 / 4 |
| [core_apps/properties/services/post_visit_decision_parts/linked_invitation.py](../core_apps/properties/services/post_visit_decision_parts/linked_invitation.py) | Structural + selected trace | 2 | 146 / 8 |
| [core_apps/properties/services/post_visit_decision_parts/submit_decision.py](../core_apps/properties/services/post_visit_decision_parts/submit_decision.py) | Structural + selected trace | 2 | 176 / 2 |
| [core_apps/properties/services/post_visit_decision_parts/validate_invitation_provenance.py](../core_apps/properties/services/post_visit_decision_parts/validate_invitation_provenance.py) | Structural + selected trace | 2 | 72 / 1 |
| [core_apps/properties/services/post_visit_decision_parts/visit_context.py](../core_apps/properties/services/post_visit_decision_parts/visit_context.py) | Structural + selected trace | 2 | 128 / 2 |
| [core_apps/properties/services/property.py](../core_apps/properties/services/property.py) | Structural + selected trace | 2 | 55 / 0 |
| [core_apps/properties/services/property_operations/__init__.py](../core_apps/properties/services/property_operations/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/services/property_operations/property_catalog.py](../core_apps/properties/services/property_operations/property_catalog.py) | Structural + selected trace | 2 | 161 / 2 |
| [core_apps/properties/services/property_operations/property_creation.py](../core_apps/properties/services/property_operations/property_creation.py) | Structural + selected trace | 2 | 107 / 2 |
| [core_apps/properties/services/property_operations/property_lifecycle.py](../core_apps/properties/services/property_operations/property_lifecycle.py) | Structural + selected trace | 2 | 90 / 2 |
| [core_apps/properties/services/property_operations/property_media.py](../core_apps/properties/services/property_operations/property_media.py) | Structural + selected trace | 2 | 58 / 3 |
| [core_apps/properties/services/property_operations/property_statistics.py](../core_apps/properties/services/property_operations/property_statistics.py) | Structural + selected trace | 2 | 196 / 1 |
| [core_apps/properties/services/property_operations/property_update.py](../core_apps/properties/services/property_operations/property_update.py) | Structural + selected trace | 2 | 216 / 1 |
| [core_apps/properties/services/public_access.py](../core_apps/properties/services/public_access.py) | Structural + selected trace | 2 | 16 / 1 |
| [core_apps/properties/services/saved_search_reads.py](../core_apps/properties/services/saved_search_reads.py) | Structural + selected trace | 2 | 209 / 5 |
| [core_apps/properties/services/search_document.py](../core_apps/properties/services/search_document.py) | Structural + selected trace | 2 | 103 / 3 |
| [core_apps/properties/services/search_suggestions.py](../core_apps/properties/services/search_suggestions.py) | Structural + selected trace | 2 | 60 / 1 |
| [core_apps/properties/services/viewing_access.py](../core_apps/properties/services/viewing_access.py) | Structural + selected trace | 2 | 266 / 6 |
| [core_apps/properties/services/viewing_arrival.py](../core_apps/properties/services/viewing_arrival.py) | Structural + selected trace | 2 | 25 / 2 |
| [core_apps/properties/services/viewing_commands.py](../core_apps/properties/services/viewing_commands.py) | Structural + selected trace | 2 | 133 / 2 |
| [core_apps/properties/services/viewing_day_plan.py](../core_apps/properties/services/viewing_day_plan.py) | Structural + selected trace | 2 | 89 / 5 |
| [core_apps/properties/services/viewing_listing_changes.py](../core_apps/properties/services/viewing_listing_changes.py) | Structural + selected trace | 2 | 190 / 5 |
| [core_apps/properties/services/viewing_notifications.py](../core_apps/properties/services/viewing_notifications.py) | Structural + selected trace | 2 | 38 / 2 |
| [core_apps/properties/services/viewing_times.py](../core_apps/properties/services/viewing_times.py) | Structural + selected trace | 2 | 132 / 7 |
| [core_apps/properties/services/visit.py](../core_apps/properties/services/visit.py) | Structural + selected trace | 2 | 24 / 0 |
| [core_apps/properties/services/visit_parts/__init__.py](../core_apps/properties/services/visit_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/services/visit_parts/logger.py](../core_apps/properties/services/visit_parts/logger.py) | Structural + selected trace | 2 | 6 / 0 |
| [core_apps/properties/services/visit_parts/property_visit_service.py](../core_apps/properties/services/visit_parts/property_visit_service.py) | Structural + selected trace | 2 | 29 / 0 |
| [core_apps/properties/services/visit_parts/property_visit_service_operations/__init__.py](../core_apps/properties/services/visit_parts/property_visit_service_operations/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/services/visit_parts/property_visit_service_operations/visit_booking.py](../core_apps/properties/services/visit_parts/property_visit_service_operations/visit_booking.py) | Structural + selected trace | 2 | 151 / 1 |
| [core_apps/properties/services/visit_parts/property_visit_service_operations/visit_decision.py](../core_apps/properties/services/visit_parts/property_visit_service_operations/visit_decision.py) | Structural + selected trace | 2 | 206 / 3 |
| [core_apps/properties/services/visit_parts/property_visit_service_operations/visit_review.py](../core_apps/properties/services/visit_parts/property_visit_service_operations/visit_review.py) | Structural + selected trace | 2 | 7 / 1 |
| [core_apps/properties/tasks.py](../core_apps/properties/tasks.py) | Structural + selected trace | 2 | 14 / 1 |
| [core_apps/properties/tests/__init__.py](../core_apps/properties/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/conftest.py](../core_apps/properties/tests/conftest.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_audit_visibility.py](../core_apps/properties/tests/test_audit_visibility.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_availability_closures.py](../core_apps/properties/tests/test_availability_closures.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_catalog_locale.py](../core_apps/properties/tests/test_catalog_locale.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_contextual_viewings.py](../core_apps/properties/tests/test_contextual_viewings.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_discovery_fixes.py](../core_apps/properties/tests/test_discovery_fixes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_hidden_listings.py](../core_apps/properties/tests/test_hidden_listings.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_home_visit_reminder.py](../core_apps/properties/tests/test_home_visit_reminder.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_inventory_creation_replay.py](../core_apps/properties/tests/test_inventory_creation_replay.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_listing_funnel.py](../core_apps/properties/tests/test_listing_funnel.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_locations.py](../core_apps/properties/tests/test_locations.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_mentor_handoff_sept28.py](../core_apps/properties/tests/test_mentor_handoff_sept28.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_mobile_api_updates.py](../core_apps/properties/tests/test_mobile_api_updates.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_mobile_handoff_oct2026.py](../core_apps/properties/tests/test_mobile_handoff_oct2026.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_models.py](../core_apps/properties/tests/test_models.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_mvp_complete_journey.py](../core_apps/properties/tests/test_mvp_complete_journey.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_mvp_dashboard_ordering.py](../core_apps/properties/tests/test_mvp_dashboard_ordering.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_mvp_ownership_proof_privacy.py](../core_apps/properties/tests/test_mvp_ownership_proof_privacy.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_mvp_search_suggestions_api.py](../core_apps/properties/tests/test_mvp_search_suggestions_api.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_owner_draft_review.py](../core_apps/properties/tests/test_owner_draft_review.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_owner_profile_locale.py](../core_apps/properties/tests/test_owner_profile_locale.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_owner_profile_screen.py](../core_apps/properties/tests/test_owner_profile_screen.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_owner_property_screen.py](../core_apps/properties/tests/test_owner_property_screen.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_owner_visit_list_filters.py](../core_apps/properties/tests/test_owner_visit_list_filters.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_owner_visit_screens.py](../core_apps/properties/tests/test_owner_visit_screens.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_parallel_media.py](../core_apps/properties/tests/test_parallel_media.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_post_visit_decision.py](../core_apps/properties/tests/test_post_visit_decision.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_property_admin_moderation.py](../core_apps/properties/tests/test_property_admin_moderation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_property_map_coordinates.py](../core_apps/properties/tests/test_property_map_coordinates.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_rental_inventory.py](../core_apps/properties/tests/test_rental_inventory.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_review_versions.py](../core_apps/properties/tests/test_review_versions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_saved_properties.py](../core_apps/properties/tests/test_saved_properties.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_saved_search_reads.py](../core_apps/properties/tests/test_saved_search_reads.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_search_suggestion_contract.py](../core_apps/properties/tests/test_search_suggestion_contract.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_services.py](../core_apps/properties/tests/test_services.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_unscheduled_visit_requests.py](../core_apps/properties/tests/test_unscheduled_visit_requests.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_ux_convenience.py](../core_apps/properties/tests/test_ux_convenience.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_viewing_arrival_day.py](../core_apps/properties/tests/test_viewing_arrival_day.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_viewing_event_history.py](../core_apps/properties/tests/test_viewing_event_history.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_viewing_listing_changes.py](../core_apps/properties/tests/test_viewing_listing_changes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_viewing_message_context.py](../core_apps/properties/tests/test_viewing_message_context.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_viewing_response_commands.py](../core_apps/properties/tests/test_viewing_response_commands.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_viewing_times.py](../core_apps/properties/tests/test_viewing_times.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_views.py](../core_apps/properties/tests/test_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_visit_booking_concurrency.py](../core_apps/properties/tests/test_visit_booking_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_visit_offer_snapshot.py](../core_apps/properties/tests/test_visit_offer_snapshot.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_visit_phone_disclosure.py](../core_apps/properties/tests/test_visit_phone_disclosure.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_visit_request_api.py](../core_apps/properties/tests/test_visit_request_api.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/test_workspace_account_handoff.py](../core_apps/properties/tests/test_workspace_account_handoff.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/tests/viewing_support.py](../core_apps/properties/tests/viewing_support.py) | test; syntax/support | Supporting scope | — |
| [core_apps/properties/urls.py](../core_apps/properties/urls.py) | Structural + selected trace | 2 | 233 / 0 |
| [core_apps/properties/views/__init__.py](../core_apps/properties/views/__init__.py) | Structural + selected trace | 2 | 47 / 0 |
| [core_apps/properties/views/availability_closures.py](../core_apps/properties/views/availability_closures.py) | Structural + selected trace | 2 | 77 / 3 |
| [core_apps/properties/views/districts.py](../core_apps/properties/views/districts.py) | Structural + selected trace | 2 | 38 / 2 |
| [core_apps/properties/views/engagement.py](../core_apps/properties/views/engagement.py) | Structural + selected trace | 2 | 171 / 6 |
| [core_apps/properties/views/hidden_listings.py](../core_apps/properties/views/hidden_listings.py) | Structural + selected trace | 2 | 211 / 3 |
| [core_apps/properties/views/home_visit_reminder.py](../core_apps/properties/views/home_visit_reminder.py) | Structural + selected trace | 2 | 14 / 1 |
| [core_apps/properties/views/image_order.py](../core_apps/properties/views/image_order.py) | Structural + selected trace | 2 | 94 / 1 |
| [core_apps/properties/views/location.py](../core_apps/properties/views/location.py) | Structural + selected trace | 2 | 45 / 0 |
| [core_apps/properties/views/operation_recovery.py](../core_apps/properties/views/operation_recovery.py) | Structural + selected trace | 2 | 62 / 2 |
| [core_apps/properties/views/owner_availability.py](../core_apps/properties/views/owner_availability.py) | Structural + selected trace | 2 | 88 / 3 |
| [core_apps/properties/views/owner_dashboard.py](../core_apps/properties/views/owner_dashboard.py) | Structural + selected trace | 2 | 82 / 3 |
| [core_apps/properties/views/owner_draft_review.py](../core_apps/properties/views/owner_draft_review.py) | Structural + selected trace | 2 | 25 / 1 |
| [core_apps/properties/views/ownership_proof.py](../core_apps/properties/views/ownership_proof.py) | Structural + selected trace | 2 | 17 / 1 |
| [core_apps/properties/views/post_visit_decision.py](../core_apps/properties/views/post_visit_decision.py) | Structural + selected trace | 2 | 160 / 4 |
| [core_apps/properties/views/property.py](../core_apps/properties/views/property.py) | Structural + selected trace | 2 | 89 / 0 |
| [core_apps/properties/views/property_parts/__init__.py](../core_apps/properties/views/property_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/views/property_parts/my_property_list_apiview.py](../core_apps/properties/views/property_parts/my_property_list_apiview.py) | Structural + selected trace | 2 | 189 / 5 |
| [core_apps/properties/views/property_parts/property_detail_apiview.py](../core_apps/properties/views/property_parts/property_detail_apiview.py) | Structural + selected trace | 2 | 268 / 8 |
| [core_apps/properties/views/property_parts/property_filter_options_apiview.py](../core_apps/properties/views/property_parts/property_filter_options_apiview.py) | Structural + selected trace | 2 | 104 / 6 |
| [core_apps/properties/views/property_parts/property_image_upload_apiview.py](../core_apps/properties/views/property_parts/property_image_upload_apiview.py) | Structural + selected trace | 2 | 201 / 12 |
| [core_apps/properties/views/property_parts/property_list_apiview.py](../core_apps/properties/views/property_parts/property_list_apiview.py) | Structural + selected trace | 2 | 205 / 7 |
| [core_apps/properties/views/public_owner.py](../core_apps/properties/views/public_owner.py) | Structural + selected trace | 2 | 53 / 2 |
| [core_apps/properties/views/saved_search_reads.py](../core_apps/properties/views/saved_search_reads.py) | Structural + selected trace | 2 | 15 / 1 |
| [core_apps/properties/views/viewing_arrival.py](../core_apps/properties/views/viewing_arrival.py) | Structural + selected trace | 2 | 69 / 3 |
| [core_apps/properties/views/viewing_commands.py](../core_apps/properties/views/viewing_commands.py) | Structural + selected trace | 2 | 196 / 8 |
| [core_apps/properties/views/viewing_day_plan.py](../core_apps/properties/views/viewing_day_plan.py) | Structural + selected trace | 2 | 59 / 3 |
| [core_apps/properties/views/viewing_message_context.py](../core_apps/properties/views/viewing_message_context.py) | Structural + selected trace | 2 | 35 / 1 |
| [core_apps/properties/views/viewing_representatives.py](../core_apps/properties/views/viewing_representatives.py) | Structural + selected trace | 2 | 32 / 1 |
| [core_apps/properties/views/viewing_times.py](../core_apps/properties/views/viewing_times.py) | Structural + selected trace | 2 | 51 / 3 |
| [core_apps/properties/views/visit.py](../core_apps/properties/views/visit.py) | Structural + selected trace | 2 | 67 / 0 |
| [core_apps/properties/views/visit_parts/__init__.py](../core_apps/properties/views/visit_parts/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/properties/views/visit_parts/owner_property_visit_list_apiview.py](../core_apps/properties/views/visit_parts/owner_property_visit_list_apiview.py) | Structural + selected trace | 2 | 175 / 7 |
| [core_apps/properties/views/visit_parts/owner_visit_request_reject_apiview.py](../core_apps/properties/views/visit_parts/owner_visit_request_reject_apiview.py) | Structural + selected trace | 2 | 60 / 2 |
| [core_apps/properties/views/visit_parts/property_review_list_apiview.py](../core_apps/properties/views/visit_parts/property_review_list_apiview.py) | Structural + selected trace | 2 | 140 / 7 |
| [core_apps/properties/views/visit_parts/property_visit_create_apiview.py](../core_apps/properties/views/visit_parts/property_visit_create_apiview.py) | Structural + selected trace | 2 | 98 / 3 |
| [core_apps/properties/views/visit_parts/property_visit_review_create_apiview.py](../core_apps/properties/views/visit_parts/property_visit_review_create_apiview.py) | Structural + selected trace | 2 | 113 / 4 |

## core_apps/virtual_tours

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/virtual_tours/__init__.py](../core_apps/virtual_tours/__init__.py) | Structural + selected trace | 2 | 1 / 0 |
| [core_apps/virtual_tours/admin.py](../core_apps/virtual_tours/admin.py) | Structural + selected trace | 6 | 162 / 7 |
| [core_apps/virtual_tours/apps.py](../core_apps/virtual_tours/apps.py) | Structural + selected trace | 2 | 6 / 0 |
| [core_apps/virtual_tours/capture_coach.py](../core_apps/virtual_tours/capture_coach.py) | Structural + selected trace | 2 | 133 / 2 |
| [core_apps/virtual_tours/capture_contracts.py](../core_apps/virtual_tours/capture_contracts.py) | Structural + selected trace | 2 | 47 / 0 |
| [core_apps/virtual_tours/capture_delivery.py](../core_apps/virtual_tours/capture_delivery.py) | Structural + selected trace | 2 | 202 / 8 |
| [core_apps/virtual_tours/capture_models.py](../core_apps/virtual_tours/capture_models.py) | Structural + selected trace | 2 | 120 / 0 |
| [core_apps/virtual_tours/capture_panorama.py](../core_apps/virtual_tours/capture_panorama.py) | Structural + selected trace | 2 | 242 / 5 |
| [core_apps/virtual_tours/capture_plan.py](../core_apps/virtual_tours/capture_plan.py) | Structural + selected trace | 2 | 43 / 2 |
| [core_apps/virtual_tours/capture_reconstruction.py](../core_apps/virtual_tours/capture_reconstruction.py) | Structural + selected trace | 2 | 179 / 5 |
| [core_apps/virtual_tours/capture_services.py](../core_apps/virtual_tours/capture_services.py) | Structural + selected trace | 2 | 355 / 11 |
| [core_apps/virtual_tours/capture_urls.py](../core_apps/virtual_tours/capture_urls.py) | Structural + selected trace | 2 | 32 / 0 |
| [core_apps/virtual_tours/capture_validation.py](../core_apps/virtual_tours/capture_validation.py) | Structural + selected trace | 2 | 275 / 5 |
| [core_apps/virtual_tours/capture_views.py](../core_apps/virtual_tours/capture_views.py) | Structural + selected trace | 2 | 520 / 25 |
| [core_apps/virtual_tours/capture_worker.py](../core_apps/virtual_tours/capture_worker.py) | Structural + selected trace | 2 | 194 / 5 |
| [core_apps/virtual_tours/cloudinary_storage.py](../core_apps/virtual_tours/cloudinary_storage.py) | Structural + selected trace | 2 | 266 / 7 |
| [core_apps/virtual_tours/contracts.py](../core_apps/virtual_tours/contracts.py) | Structural + selected trace | 2 | 116 / 0 |
| [core_apps/virtual_tours/errors.py](../core_apps/virtual_tours/errors.py) | Structural + selected trace | 2 | 13 / 2 |
| [core_apps/virtual_tours/management/__init__.py](../core_apps/virtual_tours/management/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/management/commands/__init__.py](../core_apps/virtual_tours/management/commands/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/management/commands/check_property_capture_config.py](../core_apps/virtual_tours/management/commands/check_property_capture_config.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/management/commands/export_virtual_tour_contracts.py](../core_apps/virtual_tours/management/commands/export_virtual_tour_contracts.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/management/commands/prepare_property_capture_demo.py](../core_apps/virtual_tours/management/commands/prepare_property_capture_demo.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/management/commands/run_property_capture_worker.py](../core_apps/virtual_tours/management/commands/run_property_capture_worker.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/management/commands/run_virtual_tour_worker.py](../core_apps/virtual_tours/management/commands/run_virtual_tour_worker.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/management/commands/virtual_tour_health.py](../core_apps/virtual_tours/management/commands/virtual_tour_health.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/migrations/0001_initial.py](../core_apps/virtual_tours/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/migrations/0002_propertyvirtualtour_building_and_more.py](../core_apps/virtual_tours/migrations/0002_propertyvirtualtour_building_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/migrations/0003_capturemanifestrevision_propertycapturesession_and_more.py](../core_apps/virtual_tours/migrations/0003_capturemanifestrevision_propertycapturesession_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/migrations/0004_tourrevision_capture_job.py](../core_apps/virtual_tours/migrations/0004_tourrevision_capture_job.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/migrations/0005_tourrevision_processing_token.py](../core_apps/virtual_tours/migrations/0005_tourrevision_processing_token.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/migrations/0006_capture_processing_retry.py](../core_apps/virtual_tours/migrations/0006_capture_processing_retry.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/migrations/0007_tourreviewevent_public_reason.py](../core_apps/virtual_tours/migrations/0007_tourreviewevent_public_reason.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/migrations/__init__.py](../core_apps/virtual_tours/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/models.py](../core_apps/virtual_tours/models.py) | Structural + selected trace | 2 | 205 / 2 |
| [core_apps/virtual_tours/notifications.py](../core_apps/virtual_tours/notifications.py) | Structural + selected trace | 2 | 172 / 6 |
| [core_apps/virtual_tours/openapi.py](../core_apps/virtual_tours/openapi.py) | Structural + selected trace | 2 | 496 / 3 |
| [core_apps/virtual_tours/operations.py](../core_apps/virtual_tours/operations.py) | Structural + selected trace | 2 | 72 / 1 |
| [core_apps/virtual_tours/panorama.py](../core_apps/virtual_tours/panorama.py) | Structural + selected trace | 2 | 122 / 4 |
| [core_apps/virtual_tours/place_offers.py](../core_apps/virtual_tours/place_offers.py) | Structural + selected trace | 2 | 60 / 3 |
| [core_apps/virtual_tours/policy.py](../core_apps/virtual_tours/policy.py) | Structural + selected trace | 2 | 250 / 9 |
| [core_apps/virtual_tours/processing.py](../core_apps/virtual_tours/processing.py) | Structural + selected trace | 2 | 250 / 2 |
| [core_apps/virtual_tours/processing_lease.py](../core_apps/virtual_tours/processing_lease.py) | Structural + selected trace | 2 | 33 / 2 |
| [core_apps/virtual_tours/processor_lock.py](../core_apps/virtual_tours/processor_lock.py) | Structural + selected trace | 2 | 23 / 1 |
| [core_apps/virtual_tours/remote_storage.py](../core_apps/virtual_tours/remote_storage.py) | Structural + selected trace | 2 | 155 / 7 |
| [core_apps/virtual_tours/review_access.py](../core_apps/virtual_tours/review_access.py) | Structural + selected trace | 2 | 30 / 2 |
| [core_apps/virtual_tours/review_views.py](../core_apps/virtual_tours/review_views.py) | Structural + selected trace | 2 | 98 / 4 |
| [core_apps/virtual_tours/runtime.py](../core_apps/virtual_tours/runtime.py) | Structural + selected trace | 2 | 91 / 2 |
| [core_apps/virtual_tours/schemas.py](../core_apps/virtual_tours/schemas.py) | Structural + selected trace | 2 | 208 / 6 |
| [core_apps/virtual_tours/services.py](../core_apps/virtual_tours/services.py) | Structural + selected trace | 2 | 367 / 9 |
| [core_apps/virtual_tours/sessions.py](../core_apps/virtual_tours/sessions.py) | Structural + selected trace | 2 | 263 / 7 |
| [core_apps/virtual_tours/storage.py](../core_apps/virtual_tours/storage.py) | Structural + selected trace | 2 | 90 / 6 |
| [core_apps/virtual_tours/tasks.py](../core_apps/virtual_tours/tasks.py) | Structural + selected trace | 2 | 153 / 5 |
| [core_apps/virtual_tours/tests/__init__.py](../core_apps/virtual_tours/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/conftest.py](../core_apps/virtual_tours/tests/conftest.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_capture.py](../core_apps/virtual_tours/tests/test_capture.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_capture_config.py](../core_apps/virtual_tours/tests/test_capture_config.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_capture_delivery.py](../core_apps/virtual_tours/tests/test_capture_delivery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_capture_plan.py](../core_apps/virtual_tours/tests/test_capture_plan.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_cloudinary_storage.py](../core_apps/virtual_tours/tests/test_cloudinary_storage.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_contract_export.py](../core_apps/virtual_tours/tests/test_contract_export.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_inline_runtime.py](../core_apps/virtual_tours/tests/test_inline_runtime.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_models_and_boundaries.py](../core_apps/virtual_tours/tests/test_models_and_boundaries.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_mvp_capture_resume.py](../core_apps/virtual_tours/tests/test_mvp_capture_resume.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_mvp_review_authority.py](../core_apps/virtual_tours/tests/test_mvp_review_authority.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_owner_updates.py](../core_apps/virtual_tours/tests/test_owner_updates.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_panorama_quality.py](../core_apps/virtual_tours/tests/test_panorama_quality.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_place_offers.py](../core_apps/virtual_tours/tests/test_place_offers.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_polling_worker.py](../core_apps/virtual_tours/tests/test_polling_worker.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_processing_lease.py](../core_apps/virtual_tours/tests/test_processing_lease.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_processor_lock.py](../core_apps/virtual_tours/tests/test_processor_lock.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_recovery_and_concurrency.py](../core_apps/virtual_tours/tests/test_recovery_and_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_remote_storage.py](../core_apps/virtual_tours/tests/test_remote_storage.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_tour_correction_reason.py](../core_apps/virtual_tours/tests/test_tour_correction_reason.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_tours.py](../core_apps/virtual_tours/tests/test_tours.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/tests/test_viewer_host.py](../core_apps/virtual_tours/tests/test_viewer_host.py) | test; syntax/support | Supporting scope | — |
| [core_apps/virtual_tours/uploads.py](../core_apps/virtual_tours/uploads.py) | Structural + selected trace | 2 | 167 / 7 |
| [core_apps/virtual_tours/urls.py](../core_apps/virtual_tours/urls.py) | Structural + selected trace | 2 | 72 / 0 |
| [core_apps/virtual_tours/validation.py](../core_apps/virtual_tours/validation.py) | Structural + selected trace | 2 | 386 / 8 |
| [core_apps/virtual_tours/viewer_views.py](../core_apps/virtual_tours/viewer_views.py) | Structural + selected trace | 2 | 39 / 1 |
| [core_apps/virtual_tours/views.py](../core_apps/virtual_tours/views.py) | Structural + selected trace | 2 | 541 / 40 |

## core_apps/features

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/features/__init__.py](../core_apps/features/__init__.py) | Structural + selected trace | 3 | 0 / 0 |
| [core_apps/features/admin.py](../core_apps/features/admin.py) | Structural + selected trace | 6 | 138 / 0 |
| [core_apps/features/advanced_execution_models.py](../core_apps/features/advanced_execution_models.py) | Structural + selected trace | 3 | 87 / 0 |
| [core_apps/features/advanced_execution_urls.py](../core_apps/features/advanced_execution_urls.py) | Structural + selected trace | 3 | 8 / 0 |
| [core_apps/features/advanced_execution_views.py](../core_apps/features/advanced_execution_views.py) | Structural + selected trace | 3 | 61 / 3 |
| [core_apps/features/advanced_tender_models.py](../core_apps/features/advanced_tender_models.py) | Structural + selected trace | 3 | 158 / 1 |
| [core_apps/features/advanced_tender_urls.py](../core_apps/features/advanced_tender_urls.py) | Structural + selected trace | 3 | 22 / 0 |
| [core_apps/features/advanced_tender_views.py](../core_apps/features/advanced_tender_views.py) | Structural + selected trace | 3 | 359 / 21 |
| [core_apps/features/apps.py](../core_apps/features/apps.py) | Structural + selected trace | 3 | 10 / 1 |
| [core_apps/features/beneficiary_views.py](../core_apps/features/beneficiary_views.py) | Structural + selected trace | 4 | 175 / 4 |
| [core_apps/features/billing_admin.py](../core_apps/features/billing_admin.py) | Structural + selected trace | 6 | 149 / 5 |
| [core_apps/features/billing_models.py](../core_apps/features/billing_models.py) | Structural + selected trace | 4 | 91 / 2 |
| [core_apps/features/billing_serializers.py](../core_apps/features/billing_serializers.py) | Structural + selected trace | 4 | 81 / 3 |
| [core_apps/features/billing_urls.py](../core_apps/features/billing_urls.py) | Structural + selected trace | 4 | 49 / 0 |
| [core_apps/features/billing_views.py](../core_apps/features/billing_views.py) | Structural + selected trace | 4 | 234 / 10 |
| [core_apps/features/business_policy_admin.py](../core_apps/features/business_policy_admin.py) | Structural + selected trace | 6 | 104 / 4 |
| [core_apps/features/business_policy_views.py](../core_apps/features/business_policy_views.py) | Structural + selected trace | 3 | 55 / 4 |
| [core_apps/features/case_admin.py](../core_apps/features/case_admin.py) | Structural + selected trace | 6 | 281 / 12 |
| [core_apps/features/catalog_admin.py](../core_apps/features/catalog_admin.py) | Structural + selected trace | 6 | 22 / 2 |
| [core_apps/features/catalog_models.py](../core_apps/features/catalog_models.py) | Structural + selected trace | 3 | 32 / 1 |
| [core_apps/features/chargeback_admin.py](../core_apps/features/chargeback_admin.py) | Structural + selected trace | 6 | 151 / 6 |
| [core_apps/features/chargeback_views.py](../core_apps/features/chargeback_views.py) | Structural + selected trace | 4 | 34 / 2 |
| [core_apps/features/commerce_models.py](../core_apps/features/commerce_models.py) | Structural + selected trace | 4 | 256 / 0 |
| [core_apps/features/commerce_views.py](../core_apps/features/commerce_views.py) | Structural + selected trace | 4 | 67 / 5 |
| [core_apps/features/company_admin.py](../core_apps/features/company_admin.py) | Structural + selected trace | 6 | 78 / 0 |
| [core_apps/features/company_admin_views.py](../core_apps/features/company_admin_views.py) | Structural + selected trace | 3 | 98 / 6 |
| [core_apps/features/company_chat_views.py](../core_apps/features/company_chat_views.py) | Structural + selected trace | 3 | 19 / 1 |
| [core_apps/features/company_contract_models.py](../core_apps/features/company_contract_models.py) | Structural + selected trace | 3 | 160 / 1 |
| [core_apps/features/company_contract_serializers.py](../core_apps/features/company_contract_serializers.py) | Structural + selected trace | 3 | 48 / 2 |
| [core_apps/features/company_contract_views.py](../core_apps/features/company_contract_views.py) | Structural + selected trace | 3 | 117 / 6 |
| [core_apps/features/company_execution_admin.py](../core_apps/features/company_execution_admin.py) | Structural + selected trace | 6 | 110 / 5 |
| [core_apps/features/company_models.py](../core_apps/features/company_models.py) | Structural + selected trace | 3 | 322 / 0 |
| [core_apps/features/company_negotiation_models.py](../core_apps/features/company_negotiation_models.py) | Structural + selected trace | 3 | 60 / 0 |
| [core_apps/features/company_negotiation_serializers.py](../core_apps/features/company_negotiation_serializers.py) | Structural + selected trace | 3 | 26 / 0 |
| [core_apps/features/company_negotiation_views.py](../core_apps/features/company_negotiation_views.py) | Structural + selected trace | 3 | 115 / 3 |
| [core_apps/features/company_rental_value_views.py](../core_apps/features/company_rental_value_views.py) | Structural + selected trace | 3 | 86 / 6 |
| [core_apps/features/company_responsibility_views.py](../core_apps/features/company_responsibility_views.py) | Structural + selected trace | 3 | 43 / 4 |
| [core_apps/features/company_saved_models.py](../core_apps/features/company_saved_models.py) | Structural + selected trace | 3 | 54 / 0 |
| [core_apps/features/company_saved_views.py](../core_apps/features/company_saved_views.py) | Structural + selected trace | 3 | 108 / 7 |
| [core_apps/features/company_serializers.py](../core_apps/features/company_serializers.py) | Structural + selected trace | 3 | 311 / 7 |
| [core_apps/features/company_service_form.py](../core_apps/features/company_service_form.py) | Structural + selected trace | 3 | 126 / 2 |
| [core_apps/features/company_staff_models.py](../core_apps/features/company_staff_models.py) | Structural + selected trace | 3 | 122 / 0 |
| [core_apps/features/company_staff_serializers.py](../core_apps/features/company_staff_serializers.py) | Structural + selected trace | 3 | 74 / 1 |
| [core_apps/features/company_staff_views.py](../core_apps/features/company_staff_views.py) | Structural + selected trace | 3 | 191 / 11 |
| [core_apps/features/company_tenancy_serializers.py](../core_apps/features/company_tenancy_serializers.py) | Structural + selected trace | 3 | 124 / 1 |
| [core_apps/features/company_tenancy_views.py](../core_apps/features/company_tenancy_views.py) | Structural + selected trace | 3 | 272 / 13 |
| [core_apps/features/company_urls.py](../core_apps/features/company_urls.py) | Structural + selected trace | 3 | 147 / 0 |
| [core_apps/features/company_views.py](../core_apps/features/company_views.py) | Structural + selected trace | 3 | 626 / 33 |
| [core_apps/features/company_work_views.py](../core_apps/features/company_work_views.py) | Structural + selected trace | 3 | 49 / 4 |
| [core_apps/features/continuation_views.py](../core_apps/features/continuation_views.py) | Structural + selected trace | 3 | 120 / 2 |
| [core_apps/features/decision_models.py](../core_apps/features/decision_models.py) | Structural + selected trace | 3 | 58 / 0 |
| [core_apps/features/decision_views.py](../core_apps/features/decision_views.py) | Structural + selected trace | 3 | 53 / 3 |
| [core_apps/features/experience/__init__.py](../core_apps/features/experience/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/experience/access.py](../core_apps/features/experience/access.py) | Structural + selected trace | 3 | 47 / 4 |
| [core_apps/features/experience/action_center.py](../core_apps/features/experience/action_center.py) | Structural + selected trace | 3 | 175 / 5 |
| [core_apps/features/experience/calendar.py](../core_apps/features/experience/calendar.py) | Structural + selected trace | 3 | 27 / 1 |
| [core_apps/features/experience/discovery.py](../core_apps/features/experience/discovery.py) | Structural + selected trace | 3 | 186 / 5 |
| [core_apps/features/experience/media.py](../core_apps/features/experience/media.py) | Structural + selected trace | 3 | 14 / 1 |
| [core_apps/features/experience/models.py](../core_apps/features/experience/models.py) | Structural + selected trace | 3 | 92 / 0 |
| [core_apps/features/experience/preparation.py](../core_apps/features/experience/preparation.py) | Structural + selected trace | 3 | 150 / 3 |
| [core_apps/features/experience/quality.py](../core_apps/features/experience/quality.py) | Structural + selected trace | 3 | 230 / 9 |
| [core_apps/features/experience/suggestions.py](../core_apps/features/experience/suggestions.py) | Structural + selected trace | 3 | 149 / 8 |
| [core_apps/features/experience/sync.py](../core_apps/features/experience/sync.py) | Structural + selected trace | 3 | 136 / 5 |
| [core_apps/features/experience/urls.py](../core_apps/features/experience/urls.py) | Structural + selected trace | 3 | 22 / 0 |
| [core_apps/features/experience/views.py](../core_apps/features/experience/views.py) | Structural + selected trace | 3 | 28 / 2 |
| [core_apps/features/housing_scenario_models.py](../core_apps/features/housing_scenario_models.py) | Structural + selected trace | 3 | 70 / 0 |
| [core_apps/features/housing_scenario_urls.py](../core_apps/features/housing_scenario_urls.py) | Structural + selected trace | 3 | 23 / 0 |
| [core_apps/features/housing_scenario_views.py](../core_apps/features/housing_scenario_views.py) | Structural + selected trace | 3 | 267 / 12 |
| [core_apps/features/living_lab_models.py](../core_apps/features/living_lab_models.py) | Structural + selected trace | 3 | 145 / 0 |
| [core_apps/features/living_lab_urls.py](../core_apps/features/living_lab_urls.py) | Structural + selected trace | 3 | 57 / 0 |
| [core_apps/features/living_lab_views.py](../core_apps/features/living_lab_views.py) | Structural + selected trace | 3 | 82 / 5 |
| [core_apps/features/management/__init__.py](../core_apps/features/management/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/billing_qa.py](../core_apps/features/management/billing_qa.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/__init__.py](../core_apps/features/management/commands/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/backfill_review_ancestry.py](../core_apps/features/management/commands/backfill_review_ancestry.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/configure_advanced_mock.py](../core_apps/features/management/commands/configure_advanced_mock.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/configure_rental_lifecycle_policy.py](../core_apps/features/management/commands/configure_rental_lifecycle_policy.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/import_student_catalog.py](../core_apps/features/management/commands/import_student_catalog.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/migrate_legacy_reviews.py](../core_apps/features/management/commands/migrate_legacy_reviews.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/prepare_billing_qa.py](../core_apps/features/management/commands/prepare_billing_qa.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/prepare_owner_tenant_cycle_qa.py](../core_apps/features/management/commands/prepare_owner_tenant_cycle_qa.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/prepare_rental_device_qa.py](../core_apps/features/management/commands/prepare_rental_device_qa.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/process_advanced_housing_jobs.py](../core_apps/features/management/commands/process_advanced_housing_jobs.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/process_payment_fulfillments.py](../core_apps/features/management/commands/process_payment_fulfillments.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/process_paymob_payouts.py](../core_apps/features/management/commands/process_paymob_payouts.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/process_paymob_refunds.py](../core_apps/features/management/commands/process_paymob_refunds.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/process_transition_matches.py](../core_apps/features/management/commands/process_transition_matches.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/publish_business_policies.py](../core_apps/features/management/commands/publish_business_policies.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/purge_living_lab_private_data.py](../core_apps/features/management/commands/purge_living_lab_private_data.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/reconcile_cancelled_rental_closure.py](../core_apps/features/management/commands/reconcile_cancelled_rental_closure.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/reconcile_legacy_rentals.py](../core_apps/features/management/commands/reconcile_legacy_rentals.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/reconcile_paymob_payments.py](../core_apps/features/management/commands/reconcile_paymob_payments.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/reconcile_rental_inventory.py](../core_apps/features/management/commands/reconcile_rental_inventory.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/reconcile_reviews.py](../core_apps/features/management/commands/reconcile_reviews.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/recover_review_outage.py](../core_apps/features/management/commands/recover_review_outage.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/rent_payment_notifications.py](../core_apps/features/management/commands/rent_payment_notifications.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/rental_closure_status.py](../core_apps/features/management/commands/rental_closure_status.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/seed_commerce_test_catalog.py](../core_apps/features/management/commands/seed_commerce_test_catalog.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/seed_review_demo.py](../core_apps/features/management/commands/seed_review_demo.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/commands/verify_paymob_sandbox.py](../core_apps/features/management/commands/verify_paymob_sandbox.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/management/cycle_qa.py](../core_apps/features/management/cycle_qa.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0001_initial.py](../core_apps/features/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0002_tenancyinvitation_alter_lease_options_and_more.py](../core_apps/features/migrations/0002_tenancyinvitation_alter_lease_options_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0003_idempotencyrecord_is_rental_operation_and_more.py](../core_apps/features/migrations/0003_idempotencyrecord_is_rental_operation_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0004_owneronboardingsession_ownerpaymentprofile_and_more.py](../core_apps/features/migrations/0004_owneronboardingsession_ownerpaymentprofile_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0005_seed_rental_policy_v1.py](../core_apps/features/migrations/0005_seed_rental_policy_v1.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0006_billingperiod_paymentattempt_and_more.py](../core_apps/features/migrations/0006_billingperiod_paymentattempt_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0007_payoutbatch_rentalevidence_rentalpayout_and_more.py](../core_apps/features/migrations/0007_payoutbatch_rentalevidence_rentalpayout_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0008_rentalchange_maintenancerequest_maintenanceevent_and_more.py](../core_apps/features/migrations/0008_rentalchange_maintenancerequest_maintenanceevent_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0009_alter_paymentattempt_payment_status_rentalreview_and_more.py](../core_apps/features/migrations/0009_alter_paymentattempt_payment_status_rentalreview_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0010_alter_idempotencyrecord_operation.py](../core_apps/features/migrations/0010_alter_idempotencyrecord_operation.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0011_settlement_execution_and_refund_allocations.py](../core_apps/features/migrations/0011_settlement_execution_and_refund_allocations.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0012_planning_cycles.py](../core_apps/features/migrations/0012_planning_cycles.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0013_planning_completion.py](../core_apps/features/migrations/0013_planning_completion.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0014_planning_report_integrity.py](../core_apps/features/migrations/0014_planning_report_integrity.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0015_post_visit_invitation_compatibility.py](../core_apps/features/migrations/0015_post_visit_invitation_compatibility.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0016_planning_snapshot_backfill.py](../core_apps/features/migrations/0016_planning_snapshot_backfill.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0017_renewal_effective_dates.py](../core_apps/features/migrations/0017_renewal_effective_dates.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0018_billing_subscriptions.py](../core_apps/features/migrations/0018_billing_subscriptions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0019_dashboard_promotion_catalog.py](../core_apps/features/migrations/0019_dashboard_promotion_catalog.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0020_retire_group_archiving.py](../core_apps/features/migrations/0020_retire_group_archiving.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0021_applicationaccessgrant_applicationprofile_and_more.py](../core_apps/features/migrations/0021_applicationaccessgrant_applicationprofile_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0022_maintenancerequest_access_approved_version_and_more.py](../core_apps/features/migrations/0022_maintenancerequest_access_approved_version_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0023_rentalpayout_beneficiary_account_id_and_more.py](../core_apps/features/migrations/0023_rentalpayout_beneficiary_account_id_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0024_academichousingplan_academicplanparticipant_and_more.py](../core_apps/features/migrations/0024_academichousingplan_academicplanparticipant_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0025_rentalinterest_academic_plan_and_more.py](../core_apps/features/migrations/0025_rentalinterest_academic_plan_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0026_housingoffer_student_policy_snapshot.py](../core_apps/features/migrations/0026_housingoffer_student_policy_snapshot.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0027_rentalsummarygrant_and_more.py](../core_apps/features/migrations/0027_rentalsummarygrant_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0028_remove_campus_campus_valid_coordinates_and_more.py](../core_apps/features/migrations/0028_remove_campus_campus_valid_coordinates_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0029_academichousingplan_access_group_revision.py](../core_apps/features/migrations/0029_academichousingplan_access_group_revision.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0030_company_portfolio_foundations.py](../core_apps/features/migrations/0030_company_portfolio_foundations.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0031_company_authority_review.py](../core_apps/features/migrations/0031_company_authority_review.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0032_company_staff_access_and_approval_routing.py](../core_apps/features/migrations/0032_company_staff_access_and_approval_routing.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0033_company_staff_batch_recovery.py](../core_apps/features/migrations/0033_company_staff_batch_recovery.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0034_company_work_contact_proof.py](../core_apps/features/migrations/0034_company_work_contact_proof.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0035_reviewcase_reviewopportunity_reviewsubmission_and_more.py](../core_apps/features/migrations/0035_reviewcase_reviewopportunity_reviewsubmission_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0036_reviewdecisionnotice_and_more.py](../core_apps/features/migrations/0036_reviewdecisionnotice_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0037_advanced_housing_planning.py](../core_apps/features/migrations/0037_advanced_housing_planning.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0038_tender_membership_period_access.py](../core_apps/features/migrations/0038_tender_membership_period_access.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0039_rating_experience_integrations.py](../core_apps/features/migrations/0039_rating_experience_integrations.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0040_advanced_housing_mock_execution.py](../core_apps/features/migrations/0040_advanced_housing_mock_execution.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0041_advanced_execution_actor_inbox.py](../core_apps/features/migrations/0041_advanced_execution_actor_inbox.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0042_tender_package_jobs_and_bid_revisions.py](../core_apps/features/migrations/0042_tender_package_jobs_and_bid_revisions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0043_maintenance_access_window.py](../core_apps/features/migrations/0043_maintenance_access_window.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0044_remove_tenancyinvitation_unique_live_visit_invitation_and_more.py](../core_apps/features/migrations/0044_remove_tenancyinvitation_unique_live_visit_invitation_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0045_policydecision_and_more.py](../core_apps/features/migrations/0045_policydecision_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0046_habitabilityrestriction_and_more.py](../core_apps/features/migrations/0046_habitabilityrestriction_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0047_assetwarrantyreference_provider_result_and_more.py](../core_apps/features/migrations/0047_assetwarrantyreference_provider_result_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0048_policy_decision_evidence.py](../core_apps/features/migrations/0048_policy_decision_evidence.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0049_search_alert_dispatch_cursor.py](../core_apps/features/migrations/0049_search_alert_dispatch_cursor.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0050_alter_rentaldocument_options_and_more.py](../core_apps/features/migrations/0050_alter_rentaldocument_options_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0051_retire_mislabeled_document_artifacts.py](../core_apps/features/migrations/0051_retire_mislabeled_document_artifacts.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0052_company_contract_preparation.py](../core_apps/features/migrations/0052_company_contract_preparation.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0053_company_tenancy.py](../core_apps/features/migrations/0053_company_tenancy.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0054_company_maintenance_consent.py](../core_apps/features/migrations/0054_company_maintenance_consent.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0055_company_tenancy_coordinator.py](../core_apps/features/migrations/0055_company_tenancy_coordinator.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0056_company_continuations.py](../core_apps/features/migrations/0056_company_continuations.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0057_company_viewing_provenance.py](../core_apps/features/migrations/0057_company_viewing_provenance.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0058_canonical_company_review_party.py](../core_apps/features/migrations/0058_canonical_company_review_party.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0059_business_policy_publication.py](../core_apps/features/migrations/0059_business_policy_publication.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0060_canonical_chargeback_resolution.py](../core_apps/features/migrations/0060_canonical_chargeback_resolution.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0061_company_rental_value.py](../core_apps/features/migrations/0061_company_rental_value.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0062_companysavedlist_companysaveditem_and_more.py](../core_apps/features/migrations/0062_companysavedlist_companysaveditem_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0063_evidence_inspection_lease.py](../core_apps/features/migrations/0063_evidence_inspection_lease.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0064_rolling_writer_compatibility.py](../core_apps/features/migrations/0064_rolling_writer_compatibility.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0065_evidence_media_metadata.py](../core_apps/features/migrations/0065_evidence_media_metadata.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0066_commercefeature_storeaccount_storeproduct_and_more.py](../core_apps/features/migrations/0066_commercefeature_storeaccount_storeproduct_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0066_shared_housing_plans.py](../core_apps/features/migrations/0066_shared_housing_plans.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0067_commerce_transition_grants.py](../core_apps/features/migrations/0067_commerce_transition_grants.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0068_paymobpayment.py](../core_apps/features/migrations/0068_paymobpayment.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0069_paymobrefund.py](../core_apps/features/migrations/0069_paymobrefund.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0070_merge_commerce_shared_housing.py](../core_apps/features/migrations/0070_merge_commerce_shared_housing.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0071_hosted_payment_fulfillment.py](../core_apps/features/migrations/0071_hosted_payment_fulfillment.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0072_housing_request_reviews.py](../core_apps/features/migrations/0072_housing_request_reviews.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0073_companybookingitem_replaces_and_more.py](../core_apps/features/migrations/0073_companybookingitem_replaces_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0074_decisionnotebook_decisionnotebookversion_and_more.py](../core_apps/features/migrations/0074_decisionnotebook_decisionnotebookversion_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0075_termsproposal_author_termsproposal_content_revision_and_more.py](../core_apps/features/migrations/0075_termsproposal_author_termsproposal_content_revision_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0076_rentalchange_content_revision_rentalchangeversion_and_more.py](../core_apps/features/migrations/0076_rentalchange_content_revision_rentalchangeversion_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0077_remove_assetanalysissuggestion_job_and_more.py](../core_apps/features/migrations/0077_remove_assetanalysissuggestion_job_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0078_paymentfulfillment_case.py](../core_apps/features/migrations/0078_paymentfulfillment_case.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0079_campus_revision_campus_sort_order_and_more.py](../core_apps/features/migrations/0079_campus_revision_campus_sort_order_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0080_rentalsigningdocument_rentalsigninghint_and_more.py](../core_apps/features/migrations/0080_rentalsigningdocument_rentalsigninghint_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0081_group_process_membership_scope.py](../core_apps/features/migrations/0081_group_process_membership_scope.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0082_paymob_payout_instruction.py](../core_apps/features/migrations/0082_paymob_payout_instruction.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0083_paymob_payout_attempt_history.py](../core_apps/features/migrations/0083_paymob_payout_attempt_history.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0084_refund_execution_authority.py](../core_apps/features/migrations/0084_refund_execution_authority.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0085_payment_renewal_claim.py](../core_apps/features/migrations/0085_payment_renewal_claim.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0086_group_booking_terms_versions.py](../core_apps/features/migrations/0086_group_booking_terms_versions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0087_company_negotiation_versions.py](../core_apps/features/migrations/0087_company_negotiation_versions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0088_refund_attempt_history.py](../core_apps/features/migrations/0088_refund_attempt_history.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0089_housing_offer_source_history.py](../core_apps/features/migrations/0089_housing_offer_source_history.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0090_commerce_benefit_revisions.py](../core_apps/features/migrations/0090_commerce_benefit_revisions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0091_commerce_expiration_processing.py](../core_apps/features/migrations/0091_commerce_expiration_processing.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0092_staff_setup_and_beneficiary_details.py](../core_apps/features/migrations/0092_staff_setup_and_beneficiary_details.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0093_rentalchange_termination_notice_snapshot.py](../core_apps/features/migrations/0093_rentalchange_termination_notice_snapshot.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0094_rentaldocument_generation_requested_at.py](../core_apps/features/migrations/0094_rentaldocument_generation_requested_at.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0095_ownerrentalachievement_ownermilestone_and_more.py](../core_apps/features/migrations/0095_ownerrentalachievement_ownermilestone_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/0096_experience_tools.py](../core_apps/features/migrations/0096_experience_tools.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/migrations/__init__.py](../core_apps/features/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/features/mock_provider_views.py](../core_apps/features/mock_provider_views.py) | Structural + selected trace | 3 | 229 / 7 |
| [core_apps/features/model_parts/__init__.py](../core_apps/features/model_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/model_parts/agreements.py](../core_apps/features/model_parts/agreements.py) | Structural + selected trace | 3 | 168 / 0 |
| [core_apps/features/model_parts/application_profiles.py](../core_apps/features/model_parts/application_profiles.py) | Structural + selected trace | 3 | 151 / 0 |
| [core_apps/features/model_parts/chargebacks.py](../core_apps/features/model_parts/chargebacks.py) | Structural + selected trace | 4 | 123 / 1 |
| [core_apps/features/model_parts/condition.py](../core_apps/features/model_parts/condition.py) | Structural + selected trace | 3 | 131 / 0 |
| [core_apps/features/model_parts/decision_facts.py](../core_apps/features/model_parts/decision_facts.py) | Structural + selected trace | 3 | 51 / 0 |
| [core_apps/features/model_parts/documents.py](../core_apps/features/model_parts/documents.py) | Structural + selected trace | 3 | 115 / 0 |
| [core_apps/features/model_parts/group_bookings.py](../core_apps/features/model_parts/group_bookings.py) | Structural + selected trace | 3 | 131 / 0 |
| [core_apps/features/model_parts/habitability.py](../core_apps/features/model_parts/habitability.py) | Structural + selected trace | 3 | 47 / 0 |
| [core_apps/features/model_parts/invoices.py](../core_apps/features/model_parts/invoices.py) | Structural + selected trace | 3 | 188 / 1 |
| [core_apps/features/model_parts/ledger.py](../core_apps/features/model_parts/ledger.py) | Structural + selected trace | 3 | 156 / 0 |
| [core_apps/features/model_parts/maintenance_changes.py](../core_apps/features/model_parts/maintenance_changes.py) | Structural + selected trace | 3 | 174 / 0 |
| [core_apps/features/model_parts/marketplace.py](../core_apps/features/model_parts/marketplace.py) | Structural + selected trace | 3 | 75 / 0 |
| [core_apps/features/model_parts/offers.py](../core_apps/features/model_parts/offers.py) | Structural + selected trace | 3 | 261 / 0 |
| [core_apps/features/model_parts/operational_cases.py](../core_apps/features/model_parts/operational_cases.py) | Structural + selected trace | 3 | 124 / 0 |
| [core_apps/features/model_parts/owner_achievements.py](../core_apps/features/model_parts/owner_achievements.py) | Structural + selected trace | 3 | 24 / 0 |
| [core_apps/features/model_parts/owner_payments.py](../core_apps/features/model_parts/owner_payments.py) | Structural + selected trace | 4 | 98 / 0 |
| [core_apps/features/model_parts/payments.py](../core_apps/features/model_parts/payments.py) | Structural + selected trace | 4 | 138 / 0 |
| [core_apps/features/model_parts/policy_decisions.py](../core_apps/features/model_parts/policy_decisions.py) | Structural + selected trace | 3 | 142 / 2 |
| [core_apps/features/model_parts/recovery.py](../core_apps/features/model_parts/recovery.py) | Structural + selected trace | 3 | 121 / 0 |
| [core_apps/features/model_parts/rental_experiences.py](../core_apps/features/model_parts/rental_experiences.py) | Structural + selected trace | 3 | 145 / 0 |
| [core_apps/features/model_parts/reputation.py](../core_apps/features/model_parts/reputation.py) | Structural + selected trace | 3 | 291 / 0 |
| [core_apps/features/model_parts/reservations.py](../core_apps/features/model_parts/reservations.py) | Structural + selected trace | 3 | 105 / 1 |
| [core_apps/features/model_parts/settlements.py](../core_apps/features/model_parts/settlements.py) | Structural + selected trace | 4 | 161 / 0 |
| [core_apps/features/model_parts/summary_sharing.py](../core_apps/features/model_parts/summary_sharing.py) | Structural + selected trace | 3 | 38 / 0 |
| [core_apps/features/models.py](../core_apps/features/models.py) | Structural + selected trace | 3 | 263 / 0 |
| [core_apps/features/pagination.py](../core_apps/features/pagination.py) | Structural + selected trace | 3 | 21 / 1 |
| [core_apps/features/payment_resume_views.py](../core_apps/features/payment_resume_views.py) | Structural + selected trace | 4 | 31 / 1 |
| [core_apps/features/paymob_models.py](../core_apps/features/paymob_models.py) | Structural + selected trace | 4 | 130 / 0 |
| [core_apps/features/permissions.py](../core_apps/features/permissions.py) | Structural + selected trace | 3 | 19 / 1 |
| [core_apps/features/planning_condition_views.py](../core_apps/features/planning_condition_views.py) | Structural + selected trace | 3 | 47 / 0 |
| [core_apps/features/planning_condition_views_parts/__init__.py](../core_apps/features/planning_condition_views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/planning_condition_views_parts/condition_report_action.py](../core_apps/features/planning_condition_views_parts/condition_report_action.py) | Structural + selected trace | 3 | 180 / 5 |
| [core_apps/features/planning_condition_views_parts/condition_report_context.py](../core_apps/features/planning_condition_views_parts/condition_report_context.py) | Structural + selected trace | 3 | 206 / 9 |
| [core_apps/features/planning_condition_views_parts/report_snapshot.py](../core_apps/features/planning_condition_views_parts/report_snapshot.py) | Structural + selected trace | 3 | 149 / 2 |
| [core_apps/features/planning_discovery_views.py](../core_apps/features/planning_discovery_views.py) | Structural + selected trace | 3 | 61 / 0 |
| [core_apps/features/planning_discovery_views_parts/__init__.py](../core_apps/features/planning_discovery_views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/planning_discovery_views_parts/assistant_context.py](../core_apps/features/planning_discovery_views_parts/assistant_context.py) | Structural + selected trace | 3 | 71 / 1 |
| [core_apps/features/planning_discovery_views_parts/assistant_grounding.py](../core_apps/features/planning_discovery_views_parts/assistant_grounding.py) | Structural + selected trace | 3 | 108 / 2 |
| [core_apps/features/planning_discovery_views_parts/assistant_reply.py](../core_apps/features/planning_discovery_views_parts/assistant_reply.py) | Structural + selected trace | 3 | 107 / 1 |
| [core_apps/features/planning_discovery_views_parts/catalog_matches.py](../core_apps/features/planning_discovery_views_parts/catalog_matches.py) | Structural + selected trace | 3 | 167 / 2 |
| [core_apps/features/planning_discovery_views_parts/commute_results.py](../core_apps/features/planning_discovery_views_parts/commute_results.py) | Structural + selected trace | 3 | 57 / 3 |
| [core_apps/features/planning_discovery_views_parts/commute_searches.py](../core_apps/features/planning_discovery_views_parts/commute_searches.py) | Structural + selected trace | 3 | 181 / 5 |
| [core_apps/features/planning_discovery_views_parts/mock_duration.py](../core_apps/features/planning_discovery_views_parts/mock_duration.py) | Structural + selected trace | 3 | 24 / 1 |
| [core_apps/features/planning_discovery_views_parts/tenant_assistant_turns.py](../core_apps/features/planning_discovery_views_parts/tenant_assistant_turns.py) | Structural + selected trace | 3 | 132 / 2 |
| [core_apps/features/planning_group_views.py](../core_apps/features/planning_group_views.py) | Structural + selected trace | 3 | 92 / 0 |
| [core_apps/features/planning_group_views_parts/__init__.py](../core_apps/features/planning_group_views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/planning_group_views_parts/dispatch_process.py](../core_apps/features/planning_group_views_parts/dispatch_process.py) | Structural + selected trace | 3 | 185 / 2 |
| [core_apps/features/planning_group_views_parts/group_invitation_join.py](../core_apps/features/planning_group_views_parts/group_invitation_join.py) | Structural + selected trace | 3 | 141 / 8 |
| [core_apps/features/planning_group_views_parts/group_join_decision.py](../core_apps/features/planning_group_views_parts/group_join_decision.py) | Structural + selected trace | 3 | 167 / 9 |
| [core_apps/features/planning_group_views_parts/group_payload.py](../core_apps/features/planning_group_views_parts/group_payload.py) | Structural + selected trace | 3 | 192 / 6 |
| [core_apps/features/planning_group_views_parts/housing_group_action.py](../core_apps/features/planning_group_views_parts/housing_group_action.py) | Structural + selected trace | 3 | 289 / 2 |
| [core_apps/features/planning_group_views_parts/housing_groups.py](../core_apps/features/planning_group_views_parts/housing_groups.py) | Structural + selected trace | 3 | 52 / 3 |
| [core_apps/features/planning_group_views_parts/invitation_from_token.py](../core_apps/features/planning_group_views_parts/invitation_from_token.py) | Structural + selected trace | 3 | 186 / 4 |
| [core_apps/features/planning_group_views_parts/process_payload.py](../core_apps/features/planning_group_views_parts/process_payload.py) | Structural + selected trace | 3 | 249 / 10 |
| [core_apps/features/planning_home_views.py](../core_apps/features/planning_home_views.py) | Structural + selected trace | 3 | 99 / 1 |
| [core_apps/features/planning_housing_views.py](../core_apps/features/planning_housing_views.py) | Structural + selected trace | 3 | 56 / 0 |
| [core_apps/features/planning_housing_views_parts/__init__.py](../core_apps/features/planning_housing_views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/planning_housing_views_parts/housing_offer_inventory.py](../core_apps/features/planning_housing_views_parts/housing_offer_inventory.py) | Structural + selected trace | 3 | 49 / 1 |
| [core_apps/features/planning_housing_views_parts/housing_offers.py](../core_apps/features/planning_housing_views_parts/housing_offers.py) | Structural + selected trace | 3 | 205 / 6 |
| [core_apps/features/planning_housing_views_parts/housing_request_action.py](../core_apps/features/planning_housing_views_parts/housing_request_action.py) | Structural + selected trace | 3 | 187 / 7 |
| [core_apps/features/planning_housing_views_parts/housing_requests.py](../core_apps/features/planning_housing_views_parts/housing_requests.py) | Structural + selected trace | 3 | 247 / 12 |
| [core_apps/features/planning_housing_views_parts/owner_housing_offers.py](../core_apps/features/planning_housing_views_parts/owner_housing_offers.py) | Structural + selected trace | 3 | 19 / 1 |
| [core_apps/features/planning_models.py](../core_apps/features/planning_models.py) | Structural + selected trace | 3 | 29 / 0 |
| [core_apps/features/planning_models_parts/__init__.py](../core_apps/features/planning_models_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/planning_models_parts/housing_request_change.py](../core_apps/features/planning_models_parts/housing_request_change.py) | Structural + selected trace | 3 | 25 / 0 |
| [core_apps/features/planning_models_parts/roommate_connection.py](../core_apps/features/planning_models_parts/roommate_connection.py) | Structural + selected trace | 3 | 197 / 0 |
| [core_apps/features/planning_models_parts/tenancy_transition.py](../core_apps/features/planning_models_parts/tenancy_transition.py) | Structural + selected trace | 3 | 140 / 0 |
| [core_apps/features/planning_roommate_views.py](../core_apps/features/planning_roommate_views.py) | Structural + selected trace | 3 | 46 / 0 |
| [core_apps/features/planning_roommate_views_parts/__init__.py](../core_apps/features/planning_roommate_views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/planning_roommate_views_parts/profile_values.py](../core_apps/features/planning_roommate_views_parts/profile_values.py) | Structural + selected trace | 3 | 166 / 8 |
| [core_apps/features/planning_roommate_views_parts/roommate_candidate_action.py](../core_apps/features/planning_roommate_views_parts/roommate_candidate_action.py) | Structural + selected trace | 3 | 188 / 6 |
| [core_apps/features/planning_roommate_views_parts/roommate_connection_action.py](../core_apps/features/planning_roommate_views_parts/roommate_connection_action.py) | Structural + selected trace | 3 | 47 / 2 |
| [core_apps/features/planning_transition_views.py](../core_apps/features/planning_transition_views.py) | Structural + selected trace | 3 | 48 / 0 |
| [core_apps/features/planning_transition_views_parts/__init__.py](../core_apps/features/planning_transition_views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/planning_transition_views_parts/reconcile_transitions.py](../core_apps/features/planning_transition_views_parts/reconcile_transitions.py) | Structural + selected trace | 3 | 162 / 7 |
| [core_apps/features/planning_transition_views_parts/transition_detail_action.py](../core_apps/features/planning_transition_views_parts/transition_detail_action.py) | Structural + selected trace | 3 | 174 / 6 |
| [core_apps/features/planning_transition_views_parts/transition_projection.py](../core_apps/features/planning_transition_views_parts/transition_projection.py) | Structural + selected trace | 3 | 131 / 6 |
| [core_apps/features/planning_urls.py](../core_apps/features/planning_urls.py) | Structural + selected trace | 3 | 135 / 0 |
| [core_apps/features/portfolio_admin.py](../core_apps/features/portfolio_admin.py) | Structural + selected trace | 6 | 106 / 5 |
| [core_apps/features/portfolio_fields.py](../core_apps/features/portfolio_fields.py) | Structural + selected trace | 3 | 100 / 2 |
| [core_apps/features/portfolio_serializers.py](../core_apps/features/portfolio_serializers.py) | Structural + selected trace | 3 | 96 / 3 |
| [core_apps/features/portfolio_views.py](../core_apps/features/portfolio_views.py) | Structural + selected trace | 3 | 169 / 9 |
| [core_apps/features/providers.py](../core_apps/features/providers.py) | Structural + selected trace | 3 | 207 / 23 |
| [core_apps/features/purchase_routing_views.py](../core_apps/features/purchase_routing_views.py) | Structural + selected trace | 4 | 39 / 1 |
| [core_apps/features/refund_operations.py](../core_apps/features/refund_operations.py) | Structural + selected trace | 4 | 349 / 9 |
| [core_apps/features/renderers.py](../core_apps/features/renderers.py) | Structural + selected trace | 3 | 12 / 1 |
| [core_apps/features/rental_lifecycle_serializers.py](../core_apps/features/rental_lifecycle_serializers.py) | Structural + selected trace | 3 | 218 / 4 |
| [core_apps/features/rental_lifecycle_urls.py](../core_apps/features/rental_lifecycle_urls.py) | Structural + selected trace | 3 | 92 / 0 |
| [core_apps/features/rental_lifecycle_views/__init__.py](../core_apps/features/rental_lifecycle_views/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/rental_lifecycle_views/applications.py](../core_apps/features/rental_lifecycle_views/applications.py) | Structural + selected trace | 3 | 127 / 13 |
| [core_apps/features/rental_lifecycle_views/cases.py](../core_apps/features/rental_lifecycle_views/cases.py) | Structural + selected trace | 3 | 89 / 4 |
| [core_apps/features/rental_lifecycle_views/claims.py](../core_apps/features/rental_lifecycle_views/claims.py) | Structural + selected trace | 3 | 78 / 6 |
| [core_apps/features/rental_lifecycle_views/common.py](../core_apps/features/rental_lifecycle_views/common.py) | Structural + selected trace | 3 | 42 / 5 |
| [core_apps/features/rental_lifecycle_views/deals.py](../core_apps/features/rental_lifecycle_views/deals.py) | Structural + selected trace | 3 | 27 / 2 |
| [core_apps/features/rental_lifecycle_views/decisions.py](../core_apps/features/rental_lifecycle_views/decisions.py) | Structural + selected trace | 3 | 131 / 5 |
| [core_apps/features/rental_lifecycle_views/group_bookings.py](../core_apps/features/rental_lifecycle_views/group_bookings.py) | Structural + selected trace | 3 | 138 / 8 |
| [core_apps/features/rental_lifecycle_views/habitability.py](../core_apps/features/rental_lifecycle_views/habitability.py) | Structural + selected trace | 3 | 33 / 3 |
| [core_apps/features/rental_lifecycle_views/reservations.py](../core_apps/features/rental_lifecycle_views/reservations.py) | Structural + selected trace | 3 | 63 / 4 |
| [core_apps/features/rental_lifecycle_views/terms.py](../core_apps/features/rental_lifecycle_views/terms.py) | Structural + selected trace | 3 | 38 / 3 |
| [core_apps/features/rental_phase2_views.py](../core_apps/features/rental_phase2_views.py) | Structural + selected trace | 3 | 124 / 0 |
| [core_apps/features/rental_phase2_views_parts/__init__.py](../core_apps/features/rental_phase2_views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/rental_phase2_views_parts/apply_fake_rental_event.py](../core_apps/features/rental_phase2_views_parts/apply_fake_rental_event.py) | Structural + selected trace | 3 | 89 / 2 |
| [core_apps/features/rental_phase2_views_parts/create_interest_invitation.py](../core_apps/features/rental_phase2_views_parts/create_interest_invitation.py) | Structural + selected trace | 3 | 114 / 6 |
| [core_apps/features/rental_phase2_views_parts/create_structured_lease.py](../core_apps/features/rental_phase2_views_parts/create_structured_lease.py) | Structural + selected trace | 3 | 188 / 1 |
| [core_apps/features/rental_phase2_views_parts/create_structured_signing_session.py](../core_apps/features/rental_phase2_views_parts/create_structured_signing_session.py) | Structural + selected trace | 3 | 187 / 2 |
| [core_apps/features/rental_phase2_views_parts/lease_billing_schedule.py](../core_apps/features/rental_phase2_views_parts/lease_billing_schedule.py) | Structural + selected trace | 4 | 67 / 2 |
| [core_apps/features/rental_phase2_views_parts/owner_onboarding_session.py](../core_apps/features/rental_phase2_views_parts/owner_onboarding_session.py) | Structural + selected trace | 3 | 121 / 1 |
| [core_apps/features/rental_phase2_views_parts/owner_payment_profile.py](../core_apps/features/rental_phase2_views_parts/owner_payment_profile.py) | Structural + selected trace | 4 | 214 / 9 |
| [core_apps/features/rental_phase2_views_parts/rental_interests.py](../core_apps/features/rental_phase2_views_parts/rental_interests.py) | Structural + selected trace | 3 | 285 / 3 |
| [core_apps/features/rental_phase2_views_parts/tenancy_invitation_revoke.py](../core_apps/features/rental_phase2_views_parts/tenancy_invitation_revoke.py) | Structural + selected trace | 3 | 78 / 1 |
| [core_apps/features/rental_phase2_views_parts/terms_proposals.py](../core_apps/features/rental_phase2_views_parts/terms_proposals.py) | Structural + selected trace | 3 | 140 / 9 |
| [core_apps/features/rental_phase2_views_parts/update_structured_lease.py](../core_apps/features/rental_phase2_views_parts/update_structured_lease.py) | Structural + selected trace | 3 | 157 / 2 |
| [core_apps/features/rental_phase3_views.py](../core_apps/features/rental_phase3_views.py) | Structural + selected trace | 4 | 75 / 0 |
| [core_apps/features/rental_phase3_views_parts/__init__.py](../core_apps/features/rental_phase3_views_parts/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/features/rental_phase3_views_parts/owner_payables.py](../core_apps/features/rental_phase3_views_parts/owner_payables.py) | Structural + selected trace | 4 | 238 / 7 |
| [core_apps/features/rental_phase3_views_parts/rent_invoice_checkout.py](../core_apps/features/rental_phase3_views_parts/rent_invoice_checkout.py) | Structural + selected trace | 4 | 199 / 2 |
| [core_apps/features/rental_phase3_views_parts/rent_invoice_payments.py](../core_apps/features/rental_phase3_views_parts/rent_invoice_payments.py) | Structural + selected trace | 4 | 31 / 1 |
| [core_apps/features/rental_phase3_views_parts/rent_invoice_quote.py](../core_apps/features/rental_phase3_views_parts/rent_invoice_quote.py) | Structural + selected trace | 4 | 196 / 6 |
| [core_apps/features/rental_phase4_views.py](../core_apps/features/rental_phase4_views.py) | Structural + selected trace | 4 | 81 / 0 |
| [core_apps/features/rental_phase4_views_parts/__init__.py](../core_apps/features/rental_phase4_views_parts/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/features/rental_phase4_views_parts/handover_payload.py](../core_apps/features/rental_phase4_views_parts/handover_payload.py) | Structural + selected trace | 4 | 117 / 7 |
| [core_apps/features/rental_phase4_views_parts/handover_respond.py](../core_apps/features/rental_phase4_views_parts/handover_respond.py) | Structural + selected trace | 4 | 230 / 4 |
| [core_apps/features/rental_phase4_views_parts/lease_handovers.py](../core_apps/features/rental_phase4_views_parts/lease_handovers.py) | Structural + selected trace | 4 | 183 / 3 |
| [core_apps/features/rental_phase4_views_parts/operations_execute_payout.py](../core_apps/features/rental_phase4_views_parts/operations_execute_payout.py) | Structural + selected trace | 4 | 189 / 4 |
| [core_apps/features/rental_phase4_views_parts/operations_reconcile_payout.py](../core_apps/features/rental_phase4_views_parts/operations_reconcile_payout.py) | Structural + selected trace | 4 | 107 / 1 |
| [core_apps/features/rental_phase4_views_parts/payout_review.py](../core_apps/features/rental_phase4_views_parts/payout_review.py) | Structural + selected trace | 4 | 449 / 9 |
| [core_apps/features/rental_phase4_views_parts/rental_evidence_upload.py](../core_apps/features/rental_phase4_views_parts/rental_evidence_upload.py) | Structural + selected trace | 4 | 231 / 6 |
| [core_apps/features/rental_phase5_views.py](../core_apps/features/rental_phase5_views.py) | Structural + selected trace | 3 | 70 / 0 |
| [core_apps/features/rental_phase5_views_parts/__init__.py](../core_apps/features/rental_phase5_views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/rental_phase5_views_parts/change_collection.py](../core_apps/features/rental_phase5_views_parts/change_collection.py) | Structural + selected trace | 3 | 229 / 2 |
| [core_apps/features/rental_phase5_views_parts/change_respond.py](../core_apps/features/rental_phase5_views_parts/change_respond.py) | Structural + selected trace | 3 | 213 / 10 |
| [core_apps/features/rental_phase5_views_parts/change_signing_session.py](../core_apps/features/rental_phase5_views_parts/change_signing_session.py) | Structural + selected trace | 3 | 204 / 3 |
| [core_apps/features/rental_phase5_views_parts/maintenance_action.py](../core_apps/features/rental_phase5_views_parts/maintenance_action.py) | Structural + selected trace | 3 | 314 / 3 |
| [core_apps/features/rental_phase5_views_parts/maintenance_payload.py](../core_apps/features/rental_phase5_views_parts/maintenance_payload.py) | Structural + selected trace | 3 | 164 / 6 |
| [core_apps/features/rental_phase5_views_parts/maintenance_requests.py](../core_apps/features/rental_phase5_views_parts/maintenance_requests.py) | Structural + selected trace | 3 | 108 / 2 |
| [core_apps/features/rental_phase6_views.py](../core_apps/features/rental_phase6_views.py) | Structural + selected trace | 4 | 96 / 0 |
| [core_apps/features/rental_phase6_views_parts/__init__.py](../core_apps/features/rental_phase6_views_parts/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/features/rental_phase6_views_parts/disputes.py](../core_apps/features/rental_phase6_views_parts/disputes.py) | Structural + selected trace | 4 | 198 / 4 |
| [core_apps/features/rental_phase6_views_parts/final_settlement_propose.py](../core_apps/features/rental_phase6_views_parts/final_settlement_propose.py) | Structural + selected trace | 4 | 210 / 6 |
| [core_apps/features/rental_phase6_views_parts/final_settlement_respond.py](../core_apps/features/rental_phase6_views_parts/final_settlement_respond.py) | Structural + selected trace | 4 | 143 / 3 |
| [core_apps/features/rental_phase6_views_parts/lease_reviews.py](../core_apps/features/rental_phase6_views_parts/lease_reviews.py) | Structural + selected trace | 4 | 240 / 7 |
| [core_apps/features/rental_phase6_views_parts/refund_execute.py](../core_apps/features/rental_phase6_views_parts/refund_execute.py) | Structural + selected trace | 4 | 187 / 3 |
| [core_apps/features/rental_phase6_views_parts/refund_requests.py](../core_apps/features/rental_phase6_views_parts/refund_requests.py) | Structural + selected trace | 4 | 197 / 3 |
| [core_apps/features/rental_phase6_views_parts/rental_center.py](../core_apps/features/rental_phase6_views_parts/rental_center.py) | Structural + selected trace | 4 | 114 / 1 |
| [core_apps/features/rental_serializers.py](../core_apps/features/rental_serializers.py) | Structural + selected trace | 3 | 33 / 0 |
| [core_apps/features/rental_serializers_parts/__init__.py](../core_apps/features/rental_serializers_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/rental_serializers_parts/lease_phase2_serializer.py](../core_apps/features/rental_serializers_parts/lease_phase2_serializer.py) | Structural + selected trace | 3 | 75 / 5 |
| [core_apps/features/rental_serializers_parts/maintenance_cost_decision_serializer.py](../core_apps/features/rental_serializers_parts/maintenance_cost_decision_serializer.py) | Structural + selected trace | 3 | 22 / 1 |
| [core_apps/features/rental_serializers_parts/owner_payment_profile_serializer.py](../core_apps/features/rental_serializers_parts/owner_payment_profile_serializer.py) | Structural + selected trace | 4 | 267 / 11 |
| [core_apps/features/rental_serializers_parts/rental_interest_serializer.py](../core_apps/features/rental_serializers_parts/rental_interest_serializer.py) | Structural + selected trace | 3 | 216 / 14 |
| [core_apps/features/rental_serializers_parts/termination_notice_serializer.py](../core_apps/features/rental_serializers_parts/termination_notice_serializer.py) | Structural + selected trace | 3 | 23 / 1 |
| [core_apps/features/rental_summary_views.py](../core_apps/features/rental_summary_views.py) | Structural + selected trace | 3 | 248 / 11 |
| [core_apps/features/reputation_admin.py](../core_apps/features/reputation_admin.py) | Structural + selected trace | 6 | 264 / 13 |
| [core_apps/features/reputation_experience_views.py](../core_apps/features/reputation_experience_views.py) | Structural + selected trace | 3 | 314 / 22 |
| [core_apps/features/reputation_urls.py](../core_apps/features/reputation_urls.py) | Structural + selected trace | 3 | 100 / 0 |
| [core_apps/features/reputation_views.py](../core_apps/features/reputation_views.py) | Structural + selected trace | 3 | 743 / 43 |
| [core_apps/features/serializers.py](../core_apps/features/serializers.py) | Structural + selected trace | 3 | 36 / 0 |
| [core_apps/features/serializers_parts/__init__.py](../core_apps/features/serializers_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/serializers_parts/lease_serializer.py](../core_apps/features/serializers_parts/lease_serializer.py) | Structural + selected trace | 3 | 220 / 12 |
| [core_apps/features/serializers_parts/rent_invoice_serializer.py](../core_apps/features/serializers_parts/rent_invoice_serializer.py) | Structural + selected trace | 3 | 201 / 12 |
| [core_apps/features/serializers_parts/tenancy_invitation_serializer.py](../core_apps/features/serializers_parts/tenancy_invitation_serializer.py) | Structural + selected trace | 3 | 152 / 5 |
| [core_apps/features/services/__init__.py](../core_apps/features/services/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/advanced_execution/__init__.py](../core_apps/features/services/advanced_execution/__init__.py) | Structural + selected trace | 3 | 3 / 0 |
| [core_apps/features/services/advanced_execution/canonical.py](../core_apps/features/services/advanced_execution/canonical.py) | Structural + selected trace | 3 | 312 / 4 |
| [core_apps/features/services/advanced_execution/engine.py](../core_apps/features/services/advanced_execution/engine.py) | Structural + selected trace | 3 | 342 / 9 |
| [core_apps/features/services/advanced_execution/notifications.py](../core_apps/features/services/advanced_execution/notifications.py) | Structural + selected trace | 3 | 111 / 3 |
| [core_apps/features/services/advanced_execution/plans.py](../core_apps/features/services/advanced_execution/plans.py) | Structural + selected trace | 3 | 321 / 9 |
| [core_apps/features/services/advanced_execution/progress.py](../core_apps/features/services/advanced_execution/progress.py) | Structural + selected trace | 3 | 224 / 6 |
| [core_apps/features/services/advanced_execution/projections.py](../core_apps/features/services/advanced_execution/projections.py) | Structural + selected trace | 3 | 169 / 1 |
| [core_apps/features/services/advanced_execution/provider.py](../core_apps/features/services/advanced_execution/provider.py) | Structural + selected trace | 3 | 120 / 2 |
| [core_apps/features/services/advanced_execution/registry.py](../core_apps/features/services/advanced_execution/registry.py) | Structural + selected trace | 3 | 21 / 1 |
| [core_apps/features/services/advanced_housing_access.py](../core_apps/features/services/advanced_housing_access.py) | Structural + selected trace | 3 | 61 / 2 |
| [core_apps/features/services/advanced_housing_jobs.py](../core_apps/features/services/advanced_housing_jobs.py) | Structural + selected trace | 3 | 18 / 2 |
| [core_apps/features/services/advanced_planning_notifications.py](../core_apps/features/services/advanced_planning_notifications.py) | Structural + selected trace | 3 | 222 / 7 |
| [core_apps/features/services/beneficiary_confirmation.py](../core_apps/features/services/beneficiary_confirmation.py) | Structural + selected trace | 4 | 143 / 6 |
| [core_apps/features/services/beneficiary_details.py](../core_apps/features/services/beneficiary_details.py) | Structural + selected trace | 4 | 175 / 6 |
| [core_apps/features/services/billing_advertising.py](../core_apps/features/services/billing_advertising.py) | Structural + selected trace | 4 | 111 / 3 |
| [core_apps/features/services/billing_catalog.py](../core_apps/features/services/billing_catalog.py) | Structural + selected trace | 4 | 137 / 7 |
| [core_apps/features/services/billing_invoices.py](../core_apps/features/services/billing_invoices.py) | Structural + selected trace | 4 | 341 / 6 |
| [core_apps/features/services/billing_notifications.py](../core_apps/features/services/billing_notifications.py) | Structural + selected trace | 4 | 111 / 4 |
| [core_apps/features/services/billing_payments.py](../core_apps/features/services/billing_payments.py) | Structural + selected trace | 4 | 279 / 4 |
| [core_apps/features/services/billing_projection.py](../core_apps/features/services/billing_projection.py) | Structural + selected trace | 4 | 267 / 5 |
| [core_apps/features/services/billing_settlement.py](../core_apps/features/services/billing_settlement.py) | Structural + selected trace | 4 | 159 / 2 |
| [core_apps/features/services/billing_sources.py](../core_apps/features/services/billing_sources.py) | Structural + selected trace | 4 | 185 / 7 |
| [core_apps/features/services/business_policies.py](../core_apps/features/services/business_policies.py) | Structural + selected trace | 3 | 239 / 11 |
| [core_apps/features/services/business_policy_catalog.py](../core_apps/features/services/business_policy_catalog.py) | Structural + selected trace | 3 | 253 / 2 |
| [core_apps/features/services/business_policy_mvp.py](../core_apps/features/services/business_policy_mvp.py) | Structural + selected trace | 3 | 31 / 2 |
| [core_apps/features/services/change_terms.py](../core_apps/features/services/change_terms.py) | Structural + selected trace | 3 | 49 / 4 |
| [core_apps/features/services/change_versions.py](../core_apps/features/services/change_versions.py) | Structural + selected trace | 3 | 135 / 6 |
| [core_apps/features/services/chargebacks/__init__.py](../core_apps/features/services/chargebacks/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/features/services/chargebacks/facts.py](../core_apps/features/services/chargebacks/facts.py) | Structural + selected trace | 4 | 343 / 6 |
| [core_apps/features/services/chargebacks/funding.py](../core_apps/features/services/chargebacks/funding.py) | Structural + selected trace | 4 | 194 / 9 |
| [core_apps/features/services/chargebacks/operations.py](../core_apps/features/services/chargebacks/operations.py) | Structural + selected trace | 4 | 108 / 5 |
| [core_apps/features/services/chargebacks/projection.py](../core_apps/features/services/chargebacks/projection.py) | Structural + selected trace | 4 | 187 / 7 |
| [core_apps/features/services/chargebacks/refunds.py](../core_apps/features/services/chargebacks/refunds.py) | Structural + selected trace | 4 | 90 / 3 |
| [core_apps/features/services/commands.py](../core_apps/features/services/commands.py) | Structural + selected trace | 3 | 39 / 2 |
| [core_apps/features/services/commerce_access.py](../core_apps/features/services/commerce_access.py) | Structural + selected trace | 4 | 56 / 1 |
| [core_apps/features/services/commerce_expiration.py](../core_apps/features/services/commerce_expiration.py) | Structural + selected trace | 4 | 72 / 3 |
| [core_apps/features/services/commerce_expiration_notifications.py](../core_apps/features/services/commerce_expiration_notifications.py) | Structural + selected trace | 4 | 107 / 2 |
| [core_apps/features/services/commute_jobs.py](../core_apps/features/services/commute_jobs.py) | Structural + selected trace | 3 | 194 / 3 |
| [core_apps/features/services/company/__init__.py](../core_apps/features/services/company/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/company/access.py](../core_apps/features/services/company/access.py) | Structural + selected trace | 3 | 518 / 12 |
| [core_apps/features/services/company/activation_delivery.py](../core_apps/features/services/company/activation_delivery.py) | Structural + selected trace | 3 | 160 / 3 |
| [core_apps/features/services/company/administration.py](../core_apps/features/services/company/administration.py) | Structural + selected trace | 3 | 107 / 3 |
| [core_apps/features/services/company/approval_routing.py](../core_apps/features/services/company/approval_routing.py) | Structural + selected trace | 3 | 320 / 9 |
| [core_apps/features/services/company/assignment_locks.py](../core_apps/features/services/company/assignment_locks.py) | Structural + selected trace | 3 | 36 / 2 |
| [core_apps/features/services/company/bookings.py](../core_apps/features/services/company/bookings.py) | Structural + selected trace | 3 | 938 / 9 |
| [core_apps/features/services/company/contact_proof.py](../core_apps/features/services/company/contact_proof.py) | Structural + selected trace | 3 | 127 / 5 |
| [core_apps/features/services/company/contexts.py](../core_apps/features/services/company/contexts.py) | Structural + selected trace | 3 | 60 / 1 |
| [core_apps/features/services/company/continuation_capabilities.py](../core_apps/features/services/company/continuation_capabilities.py) | Structural + selected trace | 3 | 65 / 3 |
| [core_apps/features/services/company/contract_access.py](../core_apps/features/services/company/contract_access.py) | Structural + selected trace | 3 | 139 / 5 |
| [core_apps/features/services/company/contract_preparation.py](../core_apps/features/services/company/contract_preparation.py) | Structural + selected trace | 3 | 281 / 11 |
| [core_apps/features/services/company/contract_projection.py](../core_apps/features/services/company/contract_projection.py) | Structural + selected trace | 3 | 223 / 4 |
| [core_apps/features/services/company/contract_snapshot.py](../core_apps/features/services/company/contract_snapshot.py) | Structural + selected trace | 3 | 271 / 4 |
| [core_apps/features/services/company/discovery.py](../core_apps/features/services/company/discovery.py) | Structural + selected trace | 3 | 167 / 6 |
| [core_apps/features/services/company/grant_security.py](../core_apps/features/services/company/grant_security.py) | Structural + selected trace | 3 | 16 / 1 |
| [core_apps/features/services/company/housing_report.py](../core_apps/features/services/company/housing_report.py) | Structural + selected trace | 3 | 304 / 7 |
| [core_apps/features/services/company/listing_changes.py](../core_apps/features/services/company/listing_changes.py) | Structural + selected trace | 3 | 218 / 12 |
| [core_apps/features/services/company/mandates.py](../core_apps/features/services/company/mandates.py) | Structural + selected trace | 3 | 271 / 7 |
| [core_apps/features/services/company/membership.py](../core_apps/features/services/company/membership.py) | Structural + selected trace | 3 | 160 / 4 |
| [core_apps/features/services/company/negotiation.py](../core_apps/features/services/company/negotiation.py) | Structural + selected trace | 3 | 265 / 7 |
| [core_apps/features/services/company/negotiation_access.py](../core_apps/features/services/company/negotiation_access.py) | Structural + selected trace | 3 | 74 / 5 |
| [core_apps/features/services/company/negotiation_binding.py](../core_apps/features/services/company/negotiation_binding.py) | Structural + selected trace | 3 | 281 / 10 |
| [core_apps/features/services/company/negotiation_projection.py](../core_apps/features/services/company/negotiation_projection.py) | Structural + selected trace | 3 | 163 / 5 |
| [core_apps/features/services/company/offers.py](../core_apps/features/services/company/offers.py) | Structural + selected trace | 3 | 326 / 5 |
| [core_apps/features/services/company/portfolio.py](../core_apps/features/services/company/portfolio.py) | Structural + selected trace | 3 | 522 / 12 |
| [core_apps/features/services/company/portfolio_changes.py](../core_apps/features/services/company/portfolio_changes.py) | Structural + selected trace | 3 | 328 / 11 |
| [core_apps/features/services/company/portfolio_media.py](../core_apps/features/services/company/portfolio_media.py) | Structural + selected trace | 3 | 150 / 6 |
| [core_apps/features/services/company/portfolio_topology.py](../core_apps/features/services/company/portfolio_topology.py) | Structural + selected trace | 3 | 267 / 5 |
| [core_apps/features/services/company/projections.py](../core_apps/features/services/company/projections.py) | Structural + selected trace | 3 | 141 / 2 |
| [core_apps/features/services/company/read_snapshot.py](../core_apps/features/services/company/read_snapshot.py) | Structural + selected trace | 3 | 18 / 1 |
| [core_apps/features/services/company/rental_summary.py](../core_apps/features/services/company/rental_summary.py) | Structural + selected trace | 3 | 200 / 3 |
| [core_apps/features/services/company/request_period.py](../core_apps/features/services/company/request_period.py) | Structural + selected trace | 3 | 57 / 2 |
| [core_apps/features/services/company/request_versions.py](../core_apps/features/services/company/request_versions.py) | Structural + selected trace | 3 | 236 / 8 |
| [core_apps/features/services/company/responsibility_management.py](../core_apps/features/services/company/responsibility_management.py) | Structural + selected trace | 3 | 168 / 6 |
| [core_apps/features/services/company/role_cases.py](../core_apps/features/services/company/role_cases.py) | Structural + selected trace | 3 | 60 / 3 |
| [core_apps/features/services/company/role_context.py](../core_apps/features/services/company/role_context.py) | Structural + selected trace | 3 | 211 / 13 |
| [core_apps/features/services/company/role_evidence.py](../core_apps/features/services/company/role_evidence.py) | Structural + selected trace | 3 | 34 / 1 |
| [core_apps/features/services/company/role_housing.py](../core_apps/features/services/company/role_housing.py) | Structural + selected trace | 3 | 72 / 4 |
| [core_apps/features/services/company/role_notifications.py](../core_apps/features/services/company/role_notifications.py) | Structural + selected trace | 3 | 57 / 3 |
| [core_apps/features/services/company/role_projections.py](../core_apps/features/services/company/role_projections.py) | Structural + selected trace | 3 | 485 / 6 |
| [core_apps/features/services/company/role_routes.py](../core_apps/features/services/company/role_routes.py) | Structural + selected trace | 3 | 95 / 1 |
| [core_apps/features/services/company/role_work.py](../core_apps/features/services/company/role_work.py) | Structural + selected trace | 3 | 156 / 2 |
| [core_apps/features/services/company/saved_lists.py](../core_apps/features/services/company/saved_lists.py) | Structural + selected trace | 3 | 136 / 6 |
| [core_apps/features/services/company/service_requests.py](../core_apps/features/services/company/service_requests.py) | Structural + selected trace | 3 | 226 / 11 |
| [core_apps/features/services/company/sourcing.py](../core_apps/features/services/company/sourcing.py) | Structural + selected trace | 3 | 182 / 5 |
| [core_apps/features/services/company/staff.py](../core_apps/features/services/company/staff.py) | Structural + selected trace | 3 | 460 / 15 |
| [core_apps/features/services/company/staff_import.py](../core_apps/features/services/company/staff_import.py) | Structural + selected trace | 3 | 105 / 1 |
| [core_apps/features/services/company/tenancy_access.py](../core_apps/features/services/company/tenancy_access.py) | Structural + selected trace | 3 | 366 / 16 |
| [core_apps/features/services/company/tenancy_adjustments.py](../core_apps/features/services/company/tenancy_adjustments.py) | Structural + selected trace | 3 | 133 / 5 |
| [core_apps/features/services/company/tenancy_changes.py](../core_apps/features/services/company/tenancy_changes.py) | Structural + selected trace | 3 | 365 / 8 |
| [core_apps/features/services/company/tenancy_closure.py](../core_apps/features/services/company/tenancy_closure.py) | Structural + selected trace | 3 | 390 / 9 |
| [core_apps/features/services/company/tenancy_commercial.py](../core_apps/features/services/company/tenancy_commercial.py) | Structural + selected trace | 3 | 488 / 13 |
| [core_apps/features/services/company/tenancy_continuation_projection.py](../core_apps/features/services/company/tenancy_continuation_projection.py) | Structural + selected trace | 3 | 65 / 1 |
| [core_apps/features/services/company/tenancy_continuation_signing.py](../core_apps/features/services/company/tenancy_continuation_signing.py) | Structural + selected trace | 3 | 197 / 6 |
| [core_apps/features/services/company/tenancy_contracts.py](../core_apps/features/services/company/tenancy_contracts.py) | Structural + selected trace | 3 | 565 / 8 |
| [core_apps/features/services/company/tenancy_events.py](../core_apps/features/services/company/tenancy_events.py) | Structural + selected trace | 3 | 149 / 5 |
| [core_apps/features/services/company/tenancy_expiry.py](../core_apps/features/services/company/tenancy_expiry.py) | Structural + selected trace | 3 | 68 / 2 |
| [core_apps/features/services/company/tenancy_initial_recovery.py](../core_apps/features/services/company/tenancy_initial_recovery.py) | Structural + selected trace | 3 | 286 / 13 |
| [core_apps/features/services/company/tenancy_maintenance.py](../core_apps/features/services/company/tenancy_maintenance.py) | Structural + selected trace | 3 | 330 / 5 |
| [core_apps/features/services/company/tenancy_occupancy.py](../core_apps/features/services/company/tenancy_occupancy.py) | Structural + selected trace | 3 | 407 / 8 |
| [core_apps/features/services/company/tenancy_operation_recovery.py](../core_apps/features/services/company/tenancy_operation_recovery.py) | Structural + selected trace | 3 | 87 / 2 |
| [core_apps/features/services/company/tenancy_ownership.py](../core_apps/features/services/company/tenancy_ownership.py) | Structural + selected trace | 3 | 102 / 4 |
| [core_apps/features/services/company/tenancy_projection.py](../core_apps/features/services/company/tenancy_projection.py) | Structural + selected trace | 3 | 682 / 6 |
| [core_apps/features/services/company/tenancy_resolution.py](../core_apps/features/services/company/tenancy_resolution.py) | Structural + selected trace | 3 | 147 / 5 |
| [core_apps/features/services/company/viewing_handoff.py](../core_apps/features/services/company/viewing_handoff.py) | Structural + selected trace | 3 | 199 / 5 |
| [core_apps/features/services/cycle_permissions.py](../core_apps/features/services/cycle_permissions.py) | Structural + selected trace | 3 | 222 / 1 |
| [core_apps/features/services/decision_notebooks.py](../core_apps/features/services/decision_notebooks.py) | Structural + selected trace | 3 | 236 / 10 |
| [core_apps/features/services/entitlements.py](../core_apps/features/services/entitlements.py) | Structural + selected trace | 4 | 100 / 2 |
| [core_apps/features/services/evidence_storage.py](../core_apps/features/services/evidence_storage.py) | Structural + selected trace | 3 | 174 / 8 |
| [core_apps/features/services/financial_authority.py](../core_apps/features/services/financial_authority.py) | Structural + selected trace | 4 | 55 / 2 |
| [core_apps/features/services/fulfillment_cases.py](../core_apps/features/services/fulfillment_cases.py) | Structural + selected trace | 4 | 150 / 7 |
| [core_apps/features/services/group_application_listing_changes.py](../core_apps/features/services/group_application_listing_changes.py) | Structural + selected trace | 3 | 61 / 3 |
| [core_apps/features/services/group_booking_listing_changes.py](../core_apps/features/services/group_booking_listing_changes.py) | Structural + selected trace | 3 | 166 / 8 |
| [core_apps/features/services/group_process_events.py](../core_apps/features/services/group_process_events.py) | Structural + selected trace | 3 | 88 / 2 |
| [core_apps/features/services/group_visit_listing_changes.py](../core_apps/features/services/group_visit_listing_changes.py) | Structural + selected trace | 3 | 85 / 3 |
| [core_apps/features/services/housing_offer_matching.py](../core_apps/features/services/housing_offer_matching.py) | Structural + selected trace | 3 | 53 / 2 |
| [core_apps/features/services/housing_offer_source_changes.py](../core_apps/features/services/housing_offer_source_changes.py) | Structural + selected trace | 3 | 144 / 4 |
| [core_apps/features/services/housing_request_notifications.py](../core_apps/features/services/housing_request_notifications.py) | Structural + selected trace | 3 | 78 / 1 |
| [core_apps/features/services/housing_request_reviews.py](../core_apps/features/services/housing_request_reviews.py) | Structural + selected trace | 3 | 279 / 12 |
| [core_apps/features/services/housing_scenarios/__init__.py](../core_apps/features/services/housing_scenarios/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/housing_scenarios/access.py](../core_apps/features/services/housing_scenarios/access.py) | Structural + selected trace | 3 | 107 / 6 |
| [core_apps/features/services/housing_scenarios/assumptions.py](../core_apps/features/services/housing_scenarios/assumptions.py) | Structural + selected trace | 3 | 249 / 4 |
| [core_apps/features/services/housing_scenarios/commands.py](../core_apps/features/services/housing_scenarios/commands.py) | Structural + selected trace | 3 | 52 / 2 |
| [core_apps/features/services/housing_scenarios/decisions.py](../core_apps/features/services/housing_scenarios/decisions.py) | Structural + selected trace | 3 | 294 / 7 |
| [core_apps/features/services/housing_scenarios/execution.py](../core_apps/features/services/housing_scenarios/execution.py) | Structural + selected trace | 3 | 501 / 14 |
| [core_apps/features/services/housing_scenarios/execution_canonical.py](../core_apps/features/services/housing_scenarios/execution_canonical.py) | Structural + selected trace | 3 | 134 / 2 |
| [core_apps/features/services/housing_scenarios/jobs.py](../core_apps/features/services/housing_scenarios/jobs.py) | Structural + selected trace | 3 | 147 / 5 |
| [core_apps/features/services/housing_scenarios/projections.py](../core_apps/features/services/housing_scenarios/projections.py) | Structural + selected trace | 3 | 80 / 2 |
| [core_apps/features/services/housing_scenarios/routes.py](../core_apps/features/services/housing_scenarios/routes.py) | Structural + selected trace | 3 | 165 / 4 |
| [core_apps/features/services/housing_scenarios/snapshots.py](../core_apps/features/services/housing_scenarios/snapshots.py) | Structural + selected trace | 3 | 289 / 6 |
| [core_apps/features/services/housing_scenarios/solver.py](../core_apps/features/services/housing_scenarios/solver.py) | Structural + selected trace | 3 | 286 / 5 |
| [core_apps/features/services/housing_tenders/__init__.py](../core_apps/features/services/housing_tenders/__init__.py) | Structural + selected trace | 3 | 0 / 0 |
| [core_apps/features/services/housing_tenders/access.py](../core_apps/features/services/housing_tenders/access.py) | Structural + selected trace | 3 | 251 / 9 |
| [core_apps/features/services/housing_tenders/commands.py](../core_apps/features/services/housing_tenders/commands.py) | Structural + selected trace | 3 | 666 / 12 |
| [core_apps/features/services/housing_tenders/construction.py](../core_apps/features/services/housing_tenders/construction.py) | Structural + selected trace | 3 | 280 / 6 |
| [core_apps/features/services/housing_tenders/execution.py](../core_apps/features/services/housing_tenders/execution.py) | Structural + selected trace | 3 | 135 / 4 |
| [core_apps/features/services/housing_tenders/jobs.py](../core_apps/features/services/housing_tenders/jobs.py) | Structural + selected trace | 3 | 52 / 2 |
| [core_apps/features/services/housing_tenders/pricing.py](../core_apps/features/services/housing_tenders/pricing.py) | Structural + selected trace | 3 | 94 / 3 |
| [core_apps/features/services/housing_tenders/projections.py](../core_apps/features/services/housing_tenders/projections.py) | Structural + selected trace | 3 | 207 / 4 |
| [core_apps/features/services/lease_permissions.py](../core_apps/features/services/lease_permissions.py) | Structural + selected trace | 3 | 169 / 9 |
| [core_apps/features/services/legal_lifecycle.py](../core_apps/features/services/legal_lifecycle.py) | Structural + selected trace | 3 | 92 / 3 |
| [core_apps/features/services/lifestyle_matching.py](../core_apps/features/services/lifestyle_matching.py) | Structural + selected trace | 3 | 16 / 0 |
| [core_apps/features/services/lifestyle_matching_parts/__init__.py](../core_apps/features/services/lifestyle_matching_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/lifestyle_matching_parts/disclosure_scope.py](../core_apps/features/services/lifestyle_matching_parts/disclosure_scope.py) | Structural + selected trace | 3 | 27 / 1 |
| [core_apps/features/services/lifestyle_matching_parts/profile_extensions.py](../core_apps/features/services/lifestyle_matching_parts/profile_extensions.py) | Structural + selected trace | 3 | 179 / 2 |
| [core_apps/features/services/listing_assistant.py](../core_apps/features/services/listing_assistant.py) | Structural + selected trace | 3 | 165 / 3 |
| [core_apps/features/services/listing_suggestion_commands.py](../core_apps/features/services/listing_suggestion_commands.py) | Structural + selected trace | 3 | 173 / 3 |
| [core_apps/features/services/living_lab/__init__.py](../core_apps/features/services/living_lab/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/living_lab/access.py](../core_apps/features/services/living_lab/access.py) | Structural + selected trace | 3 | 135 / 6 |
| [core_apps/features/services/living_lab/commands.py](../core_apps/features/services/living_lab/commands.py) | Structural + selected trace | 3 | 451 / 8 |
| [core_apps/features/services/living_lab/journeys.py](../core_apps/features/services/living_lab/journeys.py) | Structural + selected trace | 3 | 333 / 6 |
| [core_apps/features/services/living_lab/notifications.py](../core_apps/features/services/living_lab/notifications.py) | Structural + selected trace | 3 | 95 / 3 |
| [core_apps/features/services/living_lab/policies.py](../core_apps/features/services/living_lab/policies.py) | Structural + selected trace | 3 | 217 / 9 |
| [core_apps/features/services/living_lab/projections.py](../core_apps/features/services/living_lab/projections.py) | Structural + selected trace | 3 | 222 / 3 |
| [core_apps/features/services/living_lab/retention.py](../core_apps/features/services/living_lab/retention.py) | Structural + selected trace | 3 | 140 / 3 |
| [core_apps/features/services/living_lab/solver.py](../core_apps/features/services/living_lab/solver.py) | Structural + selected trace | 3 | 240 / 5 |
| [core_apps/features/services/maintenance_access.py](../core_apps/features/services/maintenance_access.py) | Structural + selected trace | 3 | 23 / 2 |
| [core_apps/features/services/negotiation_terms.py](../core_apps/features/services/negotiation_terms.py) | Structural + selected trace | 3 | 299 / 17 |
| [core_apps/features/services/owner_achievements.py](../core_apps/features/services/owner_achievements.py) | Structural + selected trace | 3 | 78 / 4 |
| [core_apps/features/services/payment_fulfillment.py](../core_apps/features/services/payment_fulfillment.py) | Structural + selected trace | 4 | 58 / 1 |
| [core_apps/features/services/payment_resume.py](../core_apps/features/services/payment_resume.py) | Structural + selected trace | 4 | 196 / 4 |
| [core_apps/features/services/payment_session_proof.py](../core_apps/features/services/payment_session_proof.py) | Structural + selected trace | 4 | 88 / 1 |
| [core_apps/features/services/paymob_client.py](../core_apps/features/services/paymob_client.py) | Structural + selected trace | 4 | 330 / 15 |
| [core_apps/features/services/paymob_payments.py](../core_apps/features/services/paymob_payments.py) | Structural + selected trace | 4 | 573 / 11 |
| [core_apps/features/services/paymob_payout_client.py](../core_apps/features/services/paymob_payout_client.py) | Structural + selected trace | 4 | 139 / 7 |
| [core_apps/features/services/paymob_payout_targets.py](../core_apps/features/services/paymob_payout_targets.py) | Structural + selected trace | 4 | 124 / 5 |
| [core_apps/features/services/paymob_payouts.py](../core_apps/features/services/paymob_payouts.py) | Structural + selected trace | 4 | 333 / 10 |
| [core_apps/features/services/paymob_refunds.py](../core_apps/features/services/paymob_refunds.py) | Structural + selected trace | 4 | 426 / 7 |
| [core_apps/features/services/payout_notifications.py](../core_apps/features/services/payout_notifications.py) | Structural + selected trace | 4 | 43 / 2 |
| [core_apps/features/services/planning.py](../core_apps/features/services/planning.py) | Structural + selected trace | 3 | 51 / 0 |
| [core_apps/features/services/planning_access.py](../core_apps/features/services/planning_access.py) | Structural + selected trace | 3 | 232 / 2 |
| [core_apps/features/services/planning_notifications.py](../core_apps/features/services/planning_notifications.py) | Structural + selected trace | 3 | 19 / 0 |
| [core_apps/features/services/planning_notifications_parts/__init__.py](../core_apps/features/services/planning_notifications_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/planning_notifications_parts/deliver_planning_events.py](../core_apps/features/services/planning_notifications_parts/deliver_planning_events.py) | Structural + selected trace | 3 | 152 / 2 |
| [core_apps/features/services/planning_notifications_parts/event_copy.py](../core_apps/features/services/planning_notifications_parts/event_copy.py) | Structural + selected trace | 3 | 318 / 1 |
| [core_apps/features/services/planning_notifications_parts/record_event.py](../core_apps/features/services/planning_notifications_parts/record_event.py) | Structural + selected trace | 3 | 268 / 2 |
| [core_apps/features/services/planning_parts/__init__.py](../core_apps/features/services/planning_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/planning_parts/criteria.py](../core_apps/features/services/planning_parts/criteria.py) | Structural + selected trace | 3 | 201 / 4 |
| [core_apps/features/services/planning_parts/districts.py](../core_apps/features/services/planning_parts/districts.py) | Structural + selected trace | 3 | 85 / 4 |
| [core_apps/features/services/planning_parts/selection_payload.py](../core_apps/features/services/planning_parts/selection_payload.py) | Structural + selected trace | 3 | 201 / 11 |
| [core_apps/features/services/planning_parts/validate_payload_types.py](../core_apps/features/services/planning_parts/validate_payload_types.py) | Structural + selected trace | 3 | 211 / 7 |
| [core_apps/features/services/planning_providers.py](../core_apps/features/services/planning_providers.py) | Structural + selected trace | 3 | 28 / 0 |
| [core_apps/features/services/planning_providers_parts/__init__.py](../core_apps/features/services/planning_providers_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/planning_providers_parts/extract_criteria.py](../core_apps/features/services/planning_providers_parts/extract_criteria.py) | Structural + selected trace | 3 | 130 / 1 |
| [core_apps/features/services/planning_providers_parts/route_matrix.py](../core_apps/features/services/planning_providers_parts/route_matrix.py) | Structural + selected trace | 3 | 218 / 6 |
| [core_apps/features/services/planning_transitions.py](../core_apps/features/services/planning_transitions.py) | Structural + selected trace | 3 | 43 / 2 |
| [core_apps/features/services/platform_rent_payments.py](../core_apps/features/services/platform_rent_payments.py) | Structural + selected trace | 4 | 47 / 2 |
| [core_apps/features/services/policy_registry.py](../core_apps/features/services/policy_registry.py) | Structural + selected trace | 3 | 15 / 1 |
| [core_apps/features/services/private_rental_documents.py](../core_apps/features/services/private_rental_documents.py) | Structural + selected trace | 3 | 294 / 4 |
| [core_apps/features/services/promotion_commands.py](../core_apps/features/services/promotion_commands.py) | Structural + selected trace | 3 | 152 / 4 |
| [core_apps/features/services/purchase_routing.py](../core_apps/features/services/purchase_routing.py) | Structural + selected trace | 4 | 173 / 4 |
| [core_apps/features/services/purchase_service_state.py](../core_apps/features/services/purchase_service_state.py) | Structural + selected trace | 4 | 50 / 1 |
| [core_apps/features/services/refund_notifications.py](../core_apps/features/services/refund_notifications.py) | Structural + selected trace | 4 | 142 / 5 |
| [core_apps/features/services/refunds.py](../core_apps/features/services/refunds.py) | Structural + selected trace | 4 | 30 / 0 |
| [core_apps/features/services/refunds_parts/__init__.py](../core_apps/features/services/refunds_parts/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/features/services/refunds_parts/execute_refund.py](../core_apps/features/services/refunds_parts/execute_refund.py) | Structural + selected trace | 4 | 239 / 1 |
| [core_apps/features/services/refunds_parts/remaining_components.py](../core_apps/features/services/refunds_parts/remaining_components.py) | Structural + selected trace | 4 | 115 / 3 |
| [core_apps/features/services/rent_payment_recipients.py](../core_apps/features/services/rent_payment_recipients.py) | Structural + selected trace | 4 | 29 / 2 |
| [core_apps/features/services/rent_payment_reminders.py](../core_apps/features/services/rent_payment_reminders.py) | Structural + selected trace | 4 | 187 / 8 |
| [core_apps/features/services/rental_application_records.py](../core_apps/features/services/rental_application_records.py) | Structural + selected trace | 3 | 71 / 3 |
| [core_apps/features/services/rental_foundation.py](../core_apps/features/services/rental_foundation.py) | Structural + selected trace | 3 | 53 / 0 |
| [core_apps/features/services/rental_foundation_parts/__init__.py](../core_apps/features/services/rental_foundation_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/rental_foundation_parts/capabilities_for.py](../core_apps/features/services/rental_foundation_parts/capabilities_for.py) | Structural + selected trace | 3 | 247 / 2 |
| [core_apps/features/services/rental_foundation_parts/get_authorized_rental_subject.py](../core_apps/features/services/rental_foundation_parts/get_authorized_rental_subject.py) | Structural + selected trace | 3 | 273 / 1 |
| [core_apps/features/services/rental_lifecycle/__init__.py](../core_apps/features/services/rental_lifecycle/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/rental_lifecycle/access.py](../core_apps/features/services/rental_lifecycle/access.py) | Structural + selected trace | 3 | 85 / 4 |
| [core_apps/features/services/rental_lifecycle/applications.py](../core_apps/features/services/rental_lifecycle/applications.py) | Structural + selected trace | 3 | 205 / 8 |
| [core_apps/features/services/rental_lifecycle/capabilities.py](../core_apps/features/services/rental_lifecycle/capabilities.py) | Structural + selected trace | 3 | 71 / 1 |
| [core_apps/features/services/rental_lifecycle/case_commands.py](../core_apps/features/services/rental_lifecycle/case_commands.py) | Structural + selected trace | 3 | 74 / 3 |
| [core_apps/features/services/rental_lifecycle/cases.py](../core_apps/features/services/rental_lifecycle/cases.py) | Structural + selected trace | 3 | 733 / 7 |
| [core_apps/features/services/rental_lifecycle/claims.py](../core_apps/features/services/rental_lifecycle/claims.py) | Structural + selected trace | 3 | 97 / 4 |
| [core_apps/features/services/rental_lifecycle/common.py](../core_apps/features/services/rental_lifecycle/common.py) | Structural + selected trace | 3 | 188 / 11 |
| [core_apps/features/services/rental_lifecycle/consents.py](../core_apps/features/services/rental_lifecycle/consents.py) | Structural + selected trace | 3 | 25 / 1 |
| [core_apps/features/services/rental_lifecycle/deals.py](../core_apps/features/services/rental_lifecycle/deals.py) | Structural + selected trace | 3 | 137 / 1 |
| [core_apps/features/services/rental_lifecycle/decisions.py](../core_apps/features/services/rental_lifecycle/decisions.py) | Structural + selected trace | 3 | 221 / 3 |
| [core_apps/features/services/rental_lifecycle/discovery.py](../core_apps/features/services/rental_lifecycle/discovery.py) | Structural + selected trace | 3 | 155 / 4 |
| [core_apps/features/services/rental_lifecycle/group_bookings.py](../core_apps/features/services/rental_lifecycle/group_bookings.py) | Structural + selected trace | 3 | 548 / 5 |
| [core_apps/features/services/rental_lifecycle/group_terms.py](../core_apps/features/services/rental_lifecycle/group_terms.py) | Structural + selected trace | 3 | 380 / 12 |
| [core_apps/features/services/rental_lifecycle/habitability.py](../core_apps/features/services/rental_lifecycle/habitability.py) | Structural + selected trace | 3 | 250 / 7 |
| [core_apps/features/services/rental_lifecycle/inventory.py](../core_apps/features/services/rental_lifecycle/inventory.py) | Structural + selected trace | 3 | 358 / 11 |
| [core_apps/features/services/rental_lifecycle/jobs.py](../core_apps/features/services/rental_lifecycle/jobs.py) | Structural + selected trace | 3 | 50 / 1 |
| [core_apps/features/services/rental_lifecycle/journey.py](../core_apps/features/services/rental_lifecycle/journey.py) | Structural + selected trace | 3 | 267 / 4 |
| [core_apps/features/services/rental_lifecycle/locks.py](../core_apps/features/services/rental_lifecycle/locks.py) | Structural + selected trace | 3 | 24 / 2 |
| [core_apps/features/services/rental_lifecycle/notifications.py](../core_apps/features/services/rental_lifecycle/notifications.py) | Structural + selected trace | 3 | 37 / 1 |
| [core_apps/features/services/rental_lifecycle/provider_instructions.py](../core_apps/features/services/rental_lifecycle/provider_instructions.py) | Structural + selected trace | 3 | 203 / 5 |
| [core_apps/features/services/rental_lifecycle/reservations.py](../core_apps/features/services/rental_lifecycle/reservations.py) | Structural + selected trace | 3 | 324 / 7 |
| [core_apps/features/services/rental_lifecycle/terms.py](../core_apps/features/services/rental_lifecycle/terms.py) | Structural + selected trace | 3 | 93 / 5 |
| [core_apps/features/services/rental_notes.py](../core_apps/features/services/rental_notes.py) | Structural + selected trace | 3 | 46 / 3 |
| [core_apps/features/services/rental_phase2.py](../core_apps/features/services/rental_phase2.py) | Structural + selected trace | 3 | 37 / 0 |
| [core_apps/features/services/rental_phase2_parts/__init__.py](../core_apps/features/services/rental_phase2_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/rental_phase2_parts/remember_mutation.py](../core_apps/features/services/rental_phase2_parts/remember_mutation.py) | Structural + selected trace | 3 | 192 / 9 |
| [core_apps/features/services/rental_phase2_parts/reserve_inventory_days.py](../core_apps/features/services/rental_phase2_parts/reserve_inventory_days.py) | Structural + selected trace | 3 | 42 / 2 |
| [core_apps/features/services/rental_phase3.py](../core_apps/features/services/rental_phase3.py) | Structural + selected trace | 4 | 58 / 0 |
| [core_apps/features/services/rental_phase3_parts/__init__.py](../core_apps/features/services/rental_phase3_parts/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/features/services/rental_phase3_parts/capture_attempt.py](../core_apps/features/services/rental_phase3_parts/capture_attempt.py) | Structural + selected trace | 4 | 178 / 1 |
| [core_apps/features/services/rental_phase3_parts/issue_invoice.py](../core_apps/features/services/rental_phase3_parts/issue_invoice.py) | Structural + selected trace | 4 | 247 / 4 |
| [core_apps/features/services/rental_phase3_parts/payment_attempt_payload.py](../core_apps/features/services/rental_phase3_parts/payment_attempt_payload.py) | Structural + selected trace | 4 | 244 / 5 |
| [core_apps/features/services/rental_phase3_parts/process_provider_event.py](../core_apps/features/services/rental_phase3_parts/process_provider_event.py) | Structural + selected trace | 4 | 166 / 2 |
| [core_apps/features/services/rental_phase6.py](../core_apps/features/services/rental_phase6.py) | Structural + selected trace | 4 | 159 / 4 |
| [core_apps/features/services/rental_statement_delivery.py](../core_apps/features/services/rental_statement_delivery.py) | Structural + selected trace | 3 | 51 / 1 |
| [core_apps/features/services/reputation/__init__.py](../core_apps/features/services/reputation/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/reputation/ancestry.py](../core_apps/features/services/reputation/ancestry.py) | Structural + selected trace | 3 | 63 / 4 |
| [core_apps/features/services/reputation/case_history.py](../core_apps/features/services/reputation/case_history.py) | Structural + selected trace | 3 | 58 / 3 |
| [core_apps/features/services/reputation/company_authority.py](../core_apps/features/services/reputation/company_authority.py) | Structural + selected trace | 3 | 159 / 6 |
| [core_apps/features/services/reputation/company_bindings.py](../core_apps/features/services/reputation/company_bindings.py) | Structural + selected trace | 3 | 366 / 13 |
| [core_apps/features/services/reputation/company_generation.py](../core_apps/features/services/reputation/company_generation.py) | Structural + selected trace | 3 | 195 / 5 |
| [core_apps/features/services/reputation/corporate_experience.py](../core_apps/features/services/reputation/corporate_experience.py) | Structural + selected trace | 3 | 185 / 6 |
| [core_apps/features/services/reputation/eligibility.py](../core_apps/features/services/reputation/eligibility.py) | Structural + selected trace | 3 | 255 / 9 |
| [core_apps/features/services/reputation/employee_occupancy.py](../core_apps/features/services/reputation/employee_occupancy.py) | Structural + selected trace | 3 | 369 / 15 |
| [core_apps/features/services/reputation/generation.py](../core_apps/features/services/reputation/generation.py) | Structural + selected trace | 3 | 310 / 7 |
| [core_apps/features/services/reputation/grants.py](../core_apps/features/services/reputation/grants.py) | Structural + selected trace | 3 | 104 / 7 |
| [core_apps/features/services/reputation/legacy.py](../core_apps/features/services/reputation/legacy.py) | Structural + selected trace | 3 | 140 / 2 |
| [core_apps/features/services/reputation/moderation.py](../core_apps/features/services/reputation/moderation.py) | Structural + selected trace | 3 | 416 / 15 |
| [core_apps/features/services/reputation/policy.py](../core_apps/features/services/reputation/policy.py) | Structural + selected trace | 3 | 352 / 8 |
| [core_apps/features/services/reputation/public_summary.py](../core_apps/features/services/reputation/public_summary.py) | Structural + selected trace | 3 | 138 / 2 |
| [core_apps/features/services/reputation/recovery.py](../core_apps/features/services/reputation/recovery.py) | Structural + selected trace | 3 | 223 / 6 |
| [core_apps/features/services/reputation/responsibility.py](../core_apps/features/services/reputation/responsibility.py) | Structural + selected trace | 3 | 207 / 10 |
| [core_apps/features/services/reputation/rollups.py](../core_apps/features/services/reputation/rollups.py) | Structural + selected trace | 3 | 79 / 3 |
| [core_apps/features/services/reputation/submission.py](../core_apps/features/services/reputation/submission.py) | Structural + selected trace | 3 | 249 / 9 |
| [core_apps/features/services/reputation/tasks.py](../core_apps/features/services/reputation/tasks.py) | Structural + selected trace | 3 | 143 / 2 |
| [core_apps/features/services/reputation/visibility.py](../core_apps/features/services/reputation/visibility.py) | Structural + selected trace | 3 | 410 / 22 |
| [core_apps/features/services/request_counts.py](../core_apps/features/services/request_counts.py) | Structural + selected trace | 3 | 127 / 2 |
| [core_apps/features/services/search_alert_delivery.py](../core_apps/features/services/search_alert_delivery.py) | Structural + selected trace | 3 | 109 / 1 |
| [core_apps/features/services/settlement_notes.py](../core_apps/features/services/settlement_notes.py) | Structural + selected trace | 4 | 62 / 3 |
| [core_apps/features/services/settlements.py](../core_apps/features/services/settlements.py) | Structural + selected trace | 4 | 37 / 0 |
| [core_apps/features/services/settlements_parts/__init__.py](../core_apps/features/services/settlements_parts/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/features/services/settlements_parts/apply_credit.py](../core_apps/features/services/settlements_parts/apply_credit.py) | Structural + selected trace | 4 | 42 / 1 |
| [core_apps/features/services/settlements_parts/execute_settlement.py](../core_apps/features/services/settlements_parts/execute_settlement.py) | Structural + selected trace | 4 | 200 / 1 |
| [core_apps/features/services/settlements_parts/financial_snapshot.py](../core_apps/features/services/settlements_parts/financial_snapshot.py) | Structural + selected trace | 4 | 76 / 1 |
| [core_apps/features/services/settlements_parts/prepare_settlement.py](../core_apps/features/services/settlements_parts/prepare_settlement.py) | Structural + selected trace | 4 | 228 / 2 |
| [core_apps/features/services/shared_housing/__init__.py](../core_apps/features/services/shared_housing/__init__.py) | Structural + selected trace | 3 | 0 / 0 |
| [core_apps/features/services/shared_housing/access.py](../core_apps/features/services/shared_housing/access.py) | Structural + selected trace | 3 | 125 / 9 |
| [core_apps/features/services/shared_housing/commands.py](../core_apps/features/services/shared_housing/commands.py) | Structural + selected trace | 3 | 401 / 11 |
| [core_apps/features/services/shared_housing/counts.py](../core_apps/features/services/shared_housing/counts.py) | Structural + selected trace | 3 | 49 / 1 |
| [core_apps/features/services/shared_housing/projections.py](../core_apps/features/services/shared_housing/projections.py) | Structural + selected trace | 3 | 161 / 4 |
| [core_apps/features/services/shared_housing/validation.py](../core_apps/features/services/shared_housing/validation.py) | Structural + selected trace | 3 | 128 / 2 |
| [core_apps/features/services/signing_completion.py](../core_apps/features/services/signing_completion.py) | Structural + selected trace | 3 | 105 / 1 |
| [core_apps/features/services/signing_documents.py](../core_apps/features/services/signing_documents.py) | Structural + selected trace | 3 | 339 / 11 |
| [core_apps/features/services/signing_jobs.py](../core_apps/features/services/signing_jobs.py) | Structural + selected trace | 3 | 341 / 8 |
| [core_apps/features/services/signwell_client.py](../core_apps/features/services/signwell_client.py) | Structural + selected trace | 3 | 195 / 8 |
| [core_apps/features/services/store_notifications.py](../core_apps/features/services/store_notifications.py) | Structural + selected trace | 4 | 347 / 3 |
| [core_apps/features/services/store_payments.py](../core_apps/features/services/store_payments.py) | Structural + selected trace | 4 | 369 / 9 |
| [core_apps/features/services/student_housing/__init__.py](../core_apps/features/services/student_housing/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/student_housing/access.py](../core_apps/features/services/student_housing/access.py) | Structural + selected trace | 3 | 174 / 6 |
| [core_apps/features/services/student_housing/applications.py](../core_apps/features/services/student_housing/applications.py) | Structural + selected trace | 3 | 85 / 2 |
| [core_apps/features/services/student_housing/arrangements.py](../core_apps/features/services/student_housing/arrangements.py) | Structural + selected trace | 3 | 239 / 9 |
| [core_apps/features/services/student_housing/discovery.py](../core_apps/features/services/student_housing/discovery.py) | Structural + selected trace | 3 | 47 / 1 |
| [core_apps/features/services/student_housing/groups.py](../core_apps/features/services/student_housing/groups.py) | Structural + selected trace | 3 | 246 / 8 |
| [core_apps/features/services/student_housing/notifications.py](../core_apps/features/services/student_housing/notifications.py) | Structural + selected trace | 3 | 135 / 2 |
| [core_apps/features/services/student_housing/plans.py](../core_apps/features/services/student_housing/plans.py) | Structural + selected trace | 3 | 400 / 10 |
| [core_apps/features/services/student_housing/policies.py](../core_apps/features/services/student_housing/policies.py) | Structural + selected trace | 3 | 160 / 7 |
| [core_apps/features/services/student_housing/profiles.py](../core_apps/features/services/student_housing/profiles.py) | Structural + selected trace | 3 | 166 / 6 |
| [core_apps/features/services/student_housing/progress.py](../core_apps/features/services/student_housing/progress.py) | Structural + selected trace | 3 | 58 / 1 |
| [core_apps/features/services/student_housing/publication.py](../core_apps/features/services/student_housing/publication.py) | Structural + selected trace | 3 | 167 / 5 |
| [core_apps/features/services/tenancy_invitations.py](../core_apps/features/services/tenancy_invitations.py) | Structural + selected trace | 3 | 33 / 0 |
| [core_apps/features/services/tenancy_invitations_parts/__init__.py](../core_apps/features/services/tenancy_invitations_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/tenancy_invitations_parts/notify_after_commit.py](../core_apps/features/services/tenancy_invitations_parts/notify_after_commit.py) | Structural + selected trace | 3 | 104 / 5 |
| [core_apps/features/services/tenancy_invitations_parts/resolve_offer_snapshot.py](../core_apps/features/services/tenancy_invitations_parts/resolve_offer_snapshot.py) | Structural + selected trace | 3 | 192 / 4 |
| [core_apps/features/services/tenancy_invitations_parts/validate_accounts.py](../core_apps/features/services/tenancy_invitations_parts/validate_accounts.py) | Structural + selected trace | 3 | 103 / 3 |
| [core_apps/features/services/termination_notice.py](../core_apps/features/services/termination_notice.py) | Structural + selected trace | 3 | 335 / 13 |
| [core_apps/features/services/transition_network/__init__.py](../core_apps/features/services/transition_network/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/services/transition_network/access.py](../core_apps/features/services/transition_network/access.py) | Structural + selected trace | 3 | 82 / 5 |
| [core_apps/features/services/transition_network/commands.py](../core_apps/features/services/transition_network/commands.py) | Structural + selected trace | 3 | 184 / 8 |
| [core_apps/features/services/transition_network/execution.py](../core_apps/features/services/transition_network/execution.py) | Structural + selected trace | 3 | 106 / 4 |
| [core_apps/features/services/transition_network/jobs.py](../core_apps/features/services/transition_network/jobs.py) | Structural + selected trace | 3 | 49 / 2 |
| [core_apps/features/services/transition_network/projections.py](../core_apps/features/services/transition_network/projections.py) | Structural + selected trace | 3 | 190 / 6 |
| [core_apps/features/services/transition_network/solver.py](../core_apps/features/services/transition_network/solver.py) | Structural + selected trace | 3 | 344 / 5 |
| [core_apps/features/services/transition_network/vacancies.py](../core_apps/features/services/transition_network/vacancies.py) | Structural + selected trace | 3 | 129 / 3 |
| [core_apps/features/services/version_comparison.py](../core_apps/features/services/version_comparison.py) | Structural + selected trace | 3 | 26 / 1 |
| [core_apps/features/shared_housing_models.py](../core_apps/features/shared_housing_models.py) | Structural + selected trace | 3 | 95 / 0 |
| [core_apps/features/shared_housing_views.py](../core_apps/features/shared_housing_views.py) | Structural + selected trace | 3 | 141 / 8 |
| [core_apps/features/signing_models.py](../core_apps/features/signing_models.py) | Structural + selected trace | 3 | 65 / 0 |
| [core_apps/features/signing_views.py](../core_apps/features/signing_views.py) | Structural + selected trace | 3 | 122 / 3 |
| [core_apps/features/student_admin.py](../core_apps/features/student_admin.py) | Structural + selected trace | 6 | 27 / 0 |
| [core_apps/features/student_models.py](../core_apps/features/student_models.py) | Structural + selected trace | 3 | 224 / 0 |
| [core_apps/features/student_serializers.py](../core_apps/features/student_serializers.py) | Structural + selected trace | 3 | 199 / 2 |
| [core_apps/features/student_urls.py](../core_apps/features/student_urls.py) | Structural + selected trace | 3 | 37 / 0 |
| [core_apps/features/student_verification_views.py](../core_apps/features/student_verification_views.py) | Structural + selected trace | 3 | 276 / 6 |
| [core_apps/features/student_views.py](../core_apps/features/student_views.py) | Structural + selected trace | 3 | 347 / 13 |
| [core_apps/features/subscription_views.py](../core_apps/features/subscription_views.py) | Structural + selected trace | 3 | 102 / 3 |
| [core_apps/features/tasks.py](../core_apps/features/tasks.py) | Structural + selected trace | 3 | 91 / 5 |
| [core_apps/features/tasks_parts/__init__.py](../core_apps/features/tasks_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/tasks_parts/expire_rental_sources_and_holds.py](../core_apps/features/tasks_parts/expire_rental_sources_and_holds.py) | Structural + selected trace | 3 | 240 / 6 |
| [core_apps/features/tasks_parts/process_rental_changes.py](../core_apps/features/tasks_parts/process_rental_changes.py) | Structural + selected trace | 3 | 353 / 3 |
| [core_apps/features/tasks_parts/process_rental_closure.py](../core_apps/features/tasks_parts/process_rental_closure.py) | Structural + selected trace | 3 | 106 / 1 |
| [core_apps/features/tasks_parts/rent_payment_notifications.py](../core_apps/features/tasks_parts/rent_payment_notifications.py) | Structural + selected trace | 4 | 19 / 1 |
| [core_apps/features/tasks_parts/rental_statement_delivery.py](../core_apps/features/tasks_parts/rental_statement_delivery.py) | Structural + selected trace | 3 | 11 / 1 |
| [core_apps/features/tests/__init__.py](../core_apps/features/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/cycle_http_sources.py](../core_apps/features/tests/cycle_http_sources.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_academic_request_versions.py](../core_apps/features/tests/test_academic_request_versions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_addendum_provider_boundaries.py](../core_apps/features/tests/test_addendum_provider_boundaries.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_canonical_execution.py](../core_apps/features/tests/test_advanced_canonical_execution.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_company_passport.py](../core_apps/features/tests/test_advanced_company_passport.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_company_passport_v2.py](../core_apps/features/tests/test_advanced_company_passport_v2.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_execution.py](../core_apps/features/tests/test_advanced_execution.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_execution_concurrency.py](../core_apps/features/tests/test_advanced_execution_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_execution_notifications.py](../core_apps/features/tests/test_advanced_execution_notifications.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_housing_configuration.py](../core_apps/features/tests/test_advanced_housing_configuration.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_mock_operations.py](../core_apps/features/tests/test_advanced_mock_operations.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_planning_notifications.py](../core_apps/features/tests/test_advanced_planning_notifications.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_tender_construction.py](../core_apps/features/tests/test_advanced_tender_construction.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_advanced_tenders.py](../core_apps/features/tests/test_advanced_tenders.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_api.py](../core_apps/features/tests/test_api.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_asset_retirement.py](../core_apps/features/tests/test_asset_retirement.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_audit_change_terms.py](../core_apps/features/tests/test_audit_change_terms.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_audit_concurrency.py](../core_apps/features/tests/test_audit_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_audit_disputes.py](../core_apps/features/tests/test_audit_disputes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_audit_documents.py](../core_apps/features/tests/test_audit_documents.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_audit_private_changes.py](../core_apps/features/tests/test_audit_private_changes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_audit_rental_contracts.py](../core_apps/features/tests/test_audit_rental_contracts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_beneficiary_confirmation.py](../core_apps/features/tests/test_beneficiary_confirmation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_billing_contract_guards.py](../core_apps/features/tests/test_billing_contract_guards.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_billing_migrations.py](../core_apps/features/tests/test_billing_migrations.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_billing_qa_command.py](../core_apps/features/tests/test_billing_qa_command.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_billing_rental_projection.py](../core_apps/features/tests/test_billing_rental_projection.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_billing_subscriptions.py](../core_apps/features/tests/test_billing_subscriptions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_business_policies.py](../core_apps/features/tests/test_business_policies.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_business_policy_company_adjustment.py](../core_apps/features/tests/test_business_policy_company_adjustment.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_business_policy_private_export.py](../core_apps/features/tests/test_business_policy_private_export.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_cancellation_revision.py](../core_apps/features/tests/test_cancellation_revision.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_cancelled_closure_repair.py](../core_apps/features/tests/test_cancelled_closure_repair.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_canonical_company_reputation.py](../core_apps/features/tests/test_canonical_company_reputation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_change_base_conflicts.py](../core_apps/features/tests/test_change_base_conflicts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_change_recovery.py](../core_apps/features/tests/test_change_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_change_signature_notes.py](../core_apps/features/tests/test_change_signature_notes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_change_versions.py](../core_apps/features/tests/test_change_versions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_chargeback_company.py](../core_apps/features/tests/test_chargeback_company.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_chargeback_deposit_payable.py](../core_apps/features/tests/test_chargeback_deposit_payable.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_chargeback_resolution.py](../core_apps/features/tests/test_chargeback_resolution.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_checkout_absence_recovery.py](../core_apps/features/tests/test_checkout_absence_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_closure_case_authority.py](../core_apps/features/tests/test_closure_case_authority.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_closure_continuation.py](../core_apps/features/tests/test_closure_continuation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_closure_maintenance.py](../core_apps/features/tests/test_closure_maintenance.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_closure_operator_console.py](../core_apps/features/tests/test_closure_operator_console.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_closure_status_command.py](../core_apps/features/tests/test_closure_status_command.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_combined_invoice_refunds.py](../core_apps/features/tests/test_combined_invoice_refunds.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_commerce_expiration.py](../core_apps/features/tests/test_commerce_expiration.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_commerce_test_catalog.py](../core_apps/features/tests/test_commerce_test_catalog.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_commerce_v1.py](../core_apps/features/tests/test_commerce_v1.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_closure_events.py](../core_apps/features/tests/test_company_closure_events.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_continuation_capabilities.py](../core_apps/features/tests/test_company_continuation_capabilities.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_continuation_resolution.py](../core_apps/features/tests/test_company_continuation_resolution.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_continuations.py](../core_apps/features/tests/test_company_continuations.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_contract_preparation.py](../core_apps/features/tests/test_company_contract_preparation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_core_closure.py](../core_apps/features/tests/test_company_core_closure.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_discussions.py](../core_apps/features/tests/test_company_discussions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_housing.py](../core_apps/features/tests/test_company_housing.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_initial_recovery.py](../core_apps/features/tests/test_company_initial_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_listing_changes.py](../core_apps/features/tests/test_company_listing_changes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_negotiation.py](../core_apps/features/tests/test_company_negotiation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_operation_recovery.py](../core_apps/features/tests/test_company_operation_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_preparation_account_closure.py](../core_apps/features/tests/test_company_preparation_account_closure.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_preparation_requote.py](../core_apps/features/tests/test_company_preparation_requote.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_property_agreements.py](../core_apps/features/tests/test_company_property_agreements.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_publication_changes.py](../core_apps/features/tests/test_company_publication_changes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_recovery_availability.py](../core_apps/features/tests/test_company_recovery_availability.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_rental_value.py](../core_apps/features/tests/test_company_rental_value.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_rental_value_reports.py](../core_apps/features/tests/test_company_rental_value_reports.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_request_correction.py](../core_apps/features/tests/test_company_request_correction.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_request_versions.py](../core_apps/features/tests/test_company_request_versions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_responsibility_management.py](../core_apps/features/tests/test_company_responsibility_management.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_role_contexts.py](../core_apps/features/tests/test_company_role_contexts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_selection_account_closure.py](../core_apps/features/tests/test_company_selection_account_closure.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_service_requests.py](../core_apps/features/tests/test_company_service_requests.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_settlement_projection.py](../core_apps/features/tests/test_company_settlement_projection.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_staff.py](../core_apps/features/tests/test_company_staff.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_tenancy.py](../core_apps/features/tests/test_company_tenancy.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_tenancy_lease_filter.py](../core_apps/features/tests/test_company_tenancy_lease_filter.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_tenancy_list_authority.py](../core_apps/features/tests/test_company_tenancy_list_authority.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_viewing_handoff.py](../core_apps/features/tests/test_company_viewing_handoff.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_company_work_contact.py](../core_apps/features/tests/test_company_work_contact.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_connected_authority_concurrency.py](../core_apps/features/tests/test_connected_authority_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_current_cycle_contract.py](../core_apps/features/tests/test_current_cycle_contract.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_cycle_concurrency.py](../core_apps/features/tests/test_cycle_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_cycle_qa_setup.py](../core_apps/features/tests/test_cycle_qa_setup.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_decision_notebooks.py](../core_apps/features/tests/test_decision_notebooks.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_discovery_provider_boundaries.py](../core_apps/features/tests/test_discovery_provider_boundaries.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_evidence_independence.py](../core_apps/features/tests/test_evidence_independence.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_experience_tools.py](../core_apps/features/tests/test_experience_tools.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_field_audit_maintenance.py](../core_apps/features/tests/test_field_audit_maintenance.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_field_audit_queries.py](../core_apps/features/tests/test_field_audit_queries.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_field_audit_rental_payment.py](../core_apps/features/tests/test_field_audit_rental_payment.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_field_audit_response_notes.py](../core_apps/features/tests/test_field_audit_response_notes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_field_audit_settlement_notes.py](../core_apps/features/tests/test_field_audit_settlement_notes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_financial_admin_access.py](../core_apps/features/tests/test_financial_admin_access.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_flutter_request_roundtrip.py](../core_apps/features/tests/test_flutter_request_roundtrip.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_fulfillment_cases.py](../core_apps/features/tests/test_fulfillment_cases.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_full_cycle_http.py](../core_apps/features/tests/test_full_cycle_http.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_funded_settlement.py](../core_apps/features/tests/test_funded_settlement.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_group_application_listing_changes.py](../core_apps/features/tests/test_group_application_listing_changes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_group_booking_listing_changes.py](../core_apps/features/tests/test_group_booking_listing_changes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_group_booking_negotiation.py](../core_apps/features/tests/test_group_booking_negotiation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_group_process_history.py](../core_apps/features/tests/test_group_process_history.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_group_property_agreements.py](../core_apps/features/tests/test_group_property_agreements.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_habitability_closure.py](../core_apps/features/tests/test_habitability_closure.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_hosted_checkout_all_products.py](../core_apps/features/tests/test_hosted_checkout_all_products.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_housing_demand_discovery.py](../core_apps/features/tests/test_housing_demand_discovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_housing_districts.py](../core_apps/features/tests/test_housing_districts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_housing_group_management.py](../core_apps/features/tests/test_housing_group_management.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_housing_offer_eligibility.py](../core_apps/features/tests/test_housing_offer_eligibility.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_housing_offer_source_changes.py](../core_apps/features/tests/test_housing_offer_source_changes.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_housing_request_reads.py](../core_apps/features/tests/test_housing_request_reads.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_housing_request_reviews.py](../core_apps/features/tests/test_housing_request_reviews.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_individual_simplification.py](../core_apps/features/tests/test_individual_simplification.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_invitation_create_recovery.py](../core_apps/features/tests/test_invitation_create_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_invitation_list_contract.py](../core_apps/features/tests/test_invitation_list_contract.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_invitation_response_recovery.py](../core_apps/features/tests/test_invitation_response_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_invitation_review_pause.py](../core_apps/features/tests/test_invitation_review_pause.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_invoice_read_recovery.py](../core_apps/features/tests/test_invoice_read_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_legacy_classification_stages.py](../core_apps/features/tests/test_legacy_classification_stages.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_listing_assistant_provider.py](../core_apps/features/tests/test_listing_assistant_provider.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_living_lab.py](../core_apps/features/tests/test_living_lab.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_living_lab_journeys.py](../core_apps/features/tests/test_living_lab_journeys.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_living_lab_notifications.py](../core_apps/features/tests/test_living_lab_notifications.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_maintenance_event_labels.py](../core_apps/features/tests/test_maintenance_event_labels.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mobile_field_contract.py](../core_apps/features/tests/test_mobile_field_contract.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mobile_field_http.py](../core_apps/features/tests/test_mobile_field_http.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mock_provider_api.py](../core_apps/features/tests/test_mock_provider_api.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mvp_account_policies.py](../core_apps/features/tests/test_mvp_account_policies.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mvp_advisory_safety.py](../core_apps/features/tests/test_mvp_advisory_safety.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mvp_experience_boundary.py](../core_apps/features/tests/test_mvp_experience_boundary.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mvp_owner_portfolio.py](../core_apps/features/tests/test_mvp_owner_portfolio.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mvp_portfolio_capacity.py](../core_apps/features/tests/test_mvp_portfolio_capacity.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_mvp_public_reviews.py](../core_apps/features/tests/test_mvp_public_reviews.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_negotiation_account_closure.py](../core_apps/features/tests/test_negotiation_account_closure.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_negotiation_versions.py](../core_apps/features/tests/test_negotiation_versions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_ongoing_cycle_http.py](../core_apps/features/tests/test_ongoing_cycle_http.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_owner_analytics_export.py](../core_apps/features/tests/test_owner_analytics_export.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_owner_revenue_projection.py](../core_apps/features/tests/test_owner_revenue_projection.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_payment_extension_entry.py](../core_apps/features/tests/test_payment_extension_entry.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_paymob_invoice_payments.py](../core_apps/features/tests/test_paymob_invoice_payments.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_paymob_order_inquiry_contract.py](../core_apps/features/tests/test_paymob_order_inquiry_contract.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_paymob_payouts.py](../core_apps/features/tests/test_paymob_payouts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_paymob_reconcile_fairness.py](../core_apps/features/tests/test_paymob_reconcile_fairness.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_pending_group_visit_listing.py](../core_apps/features/tests/test_pending_group_visit_listing.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_planning_boundaries.py](../core_apps/features/tests/test_planning_boundaries.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_planning_completion.py](../core_apps/features/tests/test_planning_completion.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_planning_configuration.py](../core_apps/features/tests/test_planning_configuration.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_planning_cycles.py](../core_apps/features/tests/test_planning_cycles.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_planning_list_scope.py](../core_apps/features/tests/test_planning_list_scope.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_planning_push_outbox.py](../core_apps/features/tests/test_planning_push_outbox.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_planning_targeted_outbox.py](../core_apps/features/tests/test_planning_targeted_outbox.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_policy_decisions.py](../core_apps/features/tests/test_policy_decisions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_portfolio_owner_workflows.py](../core_apps/features/tests/test_portfolio_owner_workflows.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_private_evidence_projections.py](../core_apps/features/tests/test_private_evidence_projections.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_promotion_recovery.py](../core_apps/features/tests/test_promotion_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_promotion_visibility.py](../core_apps/features/tests/test_promotion_visibility.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_public_owner_features.py](../core_apps/features/tests/test_public_owner_features.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_purchase_events.py](../core_apps/features/tests/test_purchase_events.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_recovery_fence.py](../core_apps/features/tests/test_recovery_fence.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_refund_execution_recovery.py](../core_apps/features/tests/test_refund_execution_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_remaining_concurrency.py](../core_apps/features/tests/test_remaining_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rent_payment_reminders.py](../core_apps/features/tests/test_rent_payment_reminders.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_device_qa_command.py](../core_apps/features/tests/test_rental_device_qa_command.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_foundation.py](../core_apps/features/tests/test_rental_foundation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_interests_without_provider.py](../core_apps/features/tests/test_rental_interests_without_provider.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_lifecycle.py](../core_apps/features/tests/test_rental_lifecycle.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_lifecycle_safety.py](../core_apps/features/tests/test_rental_lifecycle_safety.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_list_filters.py](../core_apps/features/tests/test_rental_list_filters.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_payment_history.py](../core_apps/features/tests/test_rental_payment_history.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_phase2.py](../core_apps/features/tests/test_rental_phase2.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_phase3.py](../core_apps/features/tests/test_rental_phase3.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_phase4.py](../core_apps/features/tests/test_rental_phase4.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_phase5.py](../core_apps/features/tests/test_rental_phase5.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_phase6.py](../core_apps/features/tests/test_rental_phase6.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_rental_statement_delivery.py](../core_apps/features/tests/test_rental_statement_delivery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_reputation.py](../core_apps/features/tests/test_reputation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_reputation_admin.py](../core_apps/features/tests/test_reputation_admin.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_reputation_integrations.py](../core_apps/features/tests/test_reputation_integrations.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_request_counts.py](../core_apps/features/tests/test_request_counts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_review_backfill_dry_run.py](../core_apps/features/tests/test_review_backfill_dry_run.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_review_case_discovery.py](../core_apps/features/tests/test_review_case_discovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_search_alert_delivery.py](../core_apps/features/tests/test_search_alert_delivery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_shared_housing.py](../core_apps/features/tests/test_shared_housing.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_shared_housing_concurrency.py](../core_apps/features/tests/test_shared_housing_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_shared_housing_guards.py](../core_apps/features/tests/test_shared_housing_guards.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_shared_housing_lifecycle.py](../core_apps/features/tests/test_shared_housing_lifecycle.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_signwell_company.py](../core_apps/features/tests/test_signwell_company.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_signwell_documents.py](../core_apps/features/tests/test_signwell_documents.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_staging_simulation_opt_in.py](../core_apps/features/tests/test_staging_simulation_opt_in.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_structured_termination_document.py](../core_apps/features/tests/test_structured_termination_document.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_boundaries.py](../core_apps/features/tests/test_student_boundaries.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_catalog_import.py](../core_apps/features/tests/test_student_catalog_import.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_events.py](../core_apps/features/tests/test_student_events.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_group_decisions.py](../core_apps/features/tests/test_student_group_decisions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_housing.py](../core_apps/features/tests/test_student_housing.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_journeys.py](../core_apps/features/tests/test_student_journeys.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_listing_source.py](../core_apps/features/tests/test_student_listing_source.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_relocation.py](../core_apps/features/tests/test_student_relocation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_student_simplification.py](../core_apps/features/tests/test_student_simplification.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_subscription_sandbox.py](../core_apps/features/tests/test_subscription_sandbox.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_temporal_cycle_boundaries.py](../core_apps/features/tests/test_temporal_cycle_boundaries.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_tenancy_invitation_revoke.py](../core_apps/features/tests/test_tenancy_invitation_revoke.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_tenancy_invitations.py](../core_apps/features/tests/test_tenancy_invitations.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_termination_notice.py](../core_apps/features/tests/test_termination_notice.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_transition_execution.py](../core_apps/features/tests/test_transition_execution.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_transition_network.py](../core_apps/features/tests/test_transition_network.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_typed_private_evidence.py](../core_apps/features/tests/test_typed_private_evidence.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_ux60_privacy.py](../core_apps/features/tests/test_ux60_privacy.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_ux60_version_comparison.py](../core_apps/features/tests/test_ux60_version_comparison.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_ux_document_context.py](../core_apps/features/tests/test_ux_document_context.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/tests/test_workspace_saved_lists.py](../core_apps/features/tests/test_workspace_saved_lists.py) | test; syntax/support | Supporting scope | — |
| [core_apps/features/transition_network_models.py](../core_apps/features/transition_network_models.py) | Structural + selected trace | 3 | 78 / 0 |
| [core_apps/features/transition_network_urls.py](../core_apps/features/transition_network_urls.py) | Structural + selected trace | 3 | 17 / 0 |
| [core_apps/features/transition_network_views.py](../core_apps/features/transition_network_views.py) | Structural + selected trace | 3 | 144 / 10 |
| [core_apps/features/urls.py](../core_apps/features/urls.py) | Structural + selected trace | 3 | 578 / 0 |
| [core_apps/features/views.py](../core_apps/features/views.py) | Structural + selected trace | 3 | 129 / 0 |
| [core_apps/features/views_parts/__init__.py](../core_apps/features/views_parts/__init__.py) | Structural + selected trace | 3 | 1 / 0 |
| [core_apps/features/views_parts/boost_campaigns.py](../core_apps/features/views_parts/boost_campaigns.py) | Structural + selected trace | 3 | 187 / 5 |
| [core_apps/features/views_parts/lease_cancel.py](../core_apps/features/views_parts/lease_cancel.py) | Structural + selected trace | 3 | 207 / 6 |
| [core_apps/features/views_parts/lease_configuration.py](../core_apps/features/views_parts/lease_configuration.py) | Structural + selected trace | 3 | 100 / 2 |
| [core_apps/features/views_parts/leases.py](../core_apps/features/views_parts/leases.py) | Structural + selected trace | 3 | 239 / 3 |
| [core_apps/features/views_parts/listing_suggestions.py](../core_apps/features/views_parts/listing_suggestions.py) | Structural + selected trace | 3 | 140 / 5 |
| [core_apps/features/views_parts/planning_capabilities.py](../core_apps/features/views_parts/planning_capabilities.py) | Structural + selected trace | 3 | 155 / 2 |
| [core_apps/features/views_parts/rent_invoice_checkout.py](../core_apps/features/views_parts/rent_invoice_checkout.py) | Structural + selected trace | 3 | 83 / 1 |
| [core_apps/features/views_parts/rental_operation_lookup.py](../core_apps/features/views_parts/rental_operation_lookup.py) | Structural + selected trace | 3 | 169 / 6 |
| [core_apps/features/views_parts/tenancy_invitation_list.py](../core_apps/features/views_parts/tenancy_invitation_list.py) | Structural + selected trace | 3 | 30 / 1 |
| [core_apps/features/views_parts/tenancy_invitation_recovery.py](../core_apps/features/views_parts/tenancy_invitation_recovery.py) | Structural + selected trace | 3 | 116 / 2 |
| [core_apps/features/views_parts/tenancy_invitation_respond.py](../core_apps/features/views_parts/tenancy_invitation_respond.py) | Structural + selected trace | 3 | 142 / 4 |
| [core_apps/features/views_parts/tenancy_invitations.py](../core_apps/features/views_parts/tenancy_invitations.py) | Structural + selected trace | 3 | 204 / 1 |
| [core_apps/features/workspace_views.py](../core_apps/features/workspace_views.py) | Structural + selected trace | 3 | 70 / 1 |

## core_apps/advertising

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/advertising/__init__.py](../core_apps/advertising/__init__.py) | Structural + selected trace | 4 | 0 / 0 |
| [core_apps/advertising/admin.py](../core_apps/advertising/admin.py) | Structural + selected trace | 6 | 61 / 3 |
| [core_apps/advertising/apps.py](../core_apps/advertising/apps.py) | Structural + selected trace | 4 | 7 / 0 |
| [core_apps/advertising/audit_asset.py](../core_apps/advertising/audit_asset.py) | Structural + selected trace | 4 | 30 / 1 |
| [core_apps/advertising/management/__init__.py](../core_apps/advertising/management/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/advertising/management/commands/__init__.py](../core_apps/advertising/management/commands/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/advertising/management/commands/expire_advertisements.py](../core_apps/advertising/management/commands/expire_advertisements.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/advertising/migrations/0001_initial.py](../core_apps/advertising/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/advertising/migrations/0002_seed_advertising_plans.py](../core_apps/advertising/migrations/0002_seed_advertising_plans.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/advertising/migrations/0003_expiration_processing.py](../core_apps/advertising/migrations/0003_expiration_processing.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/advertising/migrations/__init__.py](../core_apps/advertising/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/advertising/models.py](../core_apps/advertising/models.py) | Structural + selected trace | 4 | 150 / 3 |
| [core_apps/advertising/renderers.py](../core_apps/advertising/renderers.py) | Structural + selected trace | 4 | 17 / 1 |
| [core_apps/advertising/serializers.py](../core_apps/advertising/serializers.py) | Structural + selected trace | 4 | 30 / 1 |
| [core_apps/advertising/services.py](../core_apps/advertising/services.py) | Structural + selected trace | 4 | 54 / 0 |
| [core_apps/advertising/services_parts/__init__.py](../core_apps/advertising/services_parts/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/advertising/services_parts/activate_with_mock_payment.py](../core_apps/advertising/services_parts/activate_with_mock_payment.py) | Structural + selected trace | 4 | 154 / 2 |
| [core_apps/advertising/services_parts/create_advertisement.py](../core_apps/advertising/services_parts/create_advertisement.py) | Structural + selected trace | 4 | 160 / 3 |
| [core_apps/advertising/services_parts/ensure_media_persisted.py](../core_apps/advertising/services_parts/ensure_media_persisted.py) | Structural + selected trace | 4 | 175 / 6 |
| [core_apps/advertising/services_parts/validate_banner.py](../core_apps/advertising/services_parts/validate_banner.py) | Structural + selected trace | 4 | 141 / 8 |
| [core_apps/advertising/tasks.py](../core_apps/advertising/tasks.py) | Structural + selected trace | 4 | 8 / 1 |
| [core_apps/advertising/tests/__init__.py](../core_apps/advertising/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/advertising/tests/test_advertising_api.py](../core_apps/advertising/tests/test_advertising_api.py) | test; syntax/support | Supporting scope | — |
| [core_apps/advertising/urls.py](../core_apps/advertising/urls.py) | Structural + selected trace | 4 | 36 / 0 |
| [core_apps/advertising/views.py](../core_apps/advertising/views.py) | Structural + selected trace | 4 | 61 / 0 |
| [core_apps/advertising/views_parts/__init__.py](../core_apps/advertising/views_parts/__init__.py) | Structural + selected trace | 4 | 1 / 0 |
| [core_apps/advertising/views_parts/language.py](../core_apps/advertising/views_parts/language.py) | Structural + selected trace | 4 | 150 / 7 |
| [core_apps/advertising/views_parts/owner_advertisement_collection.py](../core_apps/advertising/views_parts/owner_advertisement_collection.py) | Structural + selected trace | 4 | 173 / 6 |
| [core_apps/advertising/views_parts/tenant_home_placement.py](../core_apps/advertising/views_parts/tenant_home_placement.py) | Structural + selected trace | 4 | 186 / 4 |

## core_apps/chat

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/chat/__init__.py](../core_apps/chat/__init__.py) | Structural + selected trace | 5 | 1 / 0 |
| [core_apps/chat/admin.py](../core_apps/chat/admin.py) | Structural + selected trace | 6 | 25 / 0 |
| [core_apps/chat/apps.py](../core_apps/chat/apps.py) | Structural + selected trace | 5 | 11 / 1 |
| [core_apps/chat/consumers.py](../core_apps/chat/consumers.py) | Structural + selected trace | 5 | 179 / 8 |
| [core_apps/chat/group_consumer.py](../core_apps/chat/group_consumer.py) | Structural + selected trace | 5 | 139 / 6 |
| [core_apps/chat/group_urls.py](../core_apps/chat/group_urls.py) | Structural + selected trace | 5 | 91 / 0 |
| [core_apps/chat/management/__init__.py](../core_apps/chat/management/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/chat/management/commands/__init__.py](../core_apps/chat/management/commands/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/chat/management/commands/backfill_chat_search.py](../core_apps/chat/management/commands/backfill_chat_search.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/chat/management/commands/backfill_group_chats.py](../core_apps/chat/management/commands/backfill_group_chats.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/chat/management/commands/backfill_private_chat_media.py](../core_apps/chat/management/commands/backfill_private_chat_media.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/chat/management/commands/run_chat_policy_worker.py](../core_apps/chat/management/commands/run_chat_policy_worker.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0001_initial.py](../core_apps/chat/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0002_rename_chat_message_conv_created_idx_chat_messag_convers_3154fc_idx.py](../core_apps/chat/migrations/0002_rename_chat_message_conv_created_idx_chat_messag_convers_3154fc_idx.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0003_message_client_message_id_and_more.py](../core_apps/chat/migrations/0003_message_client_message_id_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0004_group_chat_media_events.py](../core_apps/chat/migrations/0004_group_chat_media_events.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0005_backfill_housing_group_chats.py](../core_apps/chat/migrations/0005_backfill_housing_group_chats.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0006_conversation_group_constraint.py](../core_apps/chat/migrations/0006_conversation_group_constraint.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0007_company_request_discussions.py](../core_apps/chat/migrations/0007_company_request_discussions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0008_backfill_company_discussions.py](../core_apps/chat/migrations/0008_backfill_company_discussions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0009_conversation_direct_pair_key.py](../core_apps/chat/migrations/0009_conversation_direct_pair_key.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0010_message_edit_revision.py](../core_apps/chat/migrations/0010_message_edit_revision.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0011_conversationworkspace_and_more.py](../core_apps/chat/migrations/0011_conversationworkspace_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0012_accountrestriction_chatmediaanalysis_and_more.py](../core_apps/chat/migrations/0012_accountrestriction_chatmediaanalysis_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0013_chatmoderationcase_notification_and_more.py](../core_apps/chat/migrations/0013_chatmoderationcase_notification_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0014_rich_attachments_location_waveform.py](../core_apps/chat/migrations/0014_rich_attachments_location_waveform.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0015_search_document.py](../core_apps/chat/migrations/0015_search_document.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0016_conversation_direct_context_key_and_more.py](../core_apps/chat/migrations/0016_conversation_direct_context_key_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0017_remove_chatlist_unique_private_chat_list_and_more.py](../core_apps/chat/migrations/0017_remove_chatlist_unique_private_chat_list_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0018_conversation_consent_revision.py](../core_apps/chat/migrations/0018_conversation_consent_revision.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0019_classify_existing_direct_chats.py](../core_apps/chat/migrations/0019_classify_existing_direct_chats.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0020_preserve_rollout_compatibility.py](../core_apps/chat/migrations/0020_preserve_rollout_compatibility.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0021_message_property_reference.py](../core_apps/chat/migrations/0021_message_property_reference.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0022_message_reactions_mentions.py](../core_apps/chat/migrations/0022_message_reactions_mentions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0023_messagemention_and_more.py](../core_apps/chat/migrations/0023_messagemention_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0024_message_forwarded.py](../core_apps/chat/migrations/0024_message_forwarded.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0025_message_productivity.py](../core_apps/chat/migrations/0025_message_productivity.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0026_inbox_preferences.py](../core_apps/chat/migrations/0026_inbox_preferences.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0027_group_notification_preferences.py](../core_apps/chat/migrations/0027_group_notification_preferences.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/0028_voicetranscription.py](../core_apps/chat/migrations/0028_voicetranscription.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/migrations/__init__.py](../core_apps/chat/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/chat/models/__init__.py](../core_apps/chat/models/__init__.py) | Structural + selected trace | 5 | 33 / 0 |
| [core_apps/chat/models/attachment.py](../core_apps/chat/models/attachment.py) | Structural + selected trace | 5 | 39 / 0 |
| [core_apps/chat/models/conversation.py](../core_apps/chat/models/conversation.py) | Structural + selected trace | 5 | 134 / 2 |
| [core_apps/chat/models/event.py](../core_apps/chat/models/event.py) | Structural + selected trace | 5 | 46 / 0 |
| [core_apps/chat/models/mention.py](../core_apps/chat/models/mention.py) | Structural + selected trace | 5 | 21 / 0 |
| [core_apps/chat/models/message.py](../core_apps/chat/models/message.py) | Structural + selected trace | 5 | 61 / 1 |
| [core_apps/chat/models/moderation.py](../core_apps/chat/models/moderation.py) | Structural + selected trace | 5 | 157 / 0 |
| [core_apps/chat/models/preferences.py](../core_apps/chat/models/preferences.py) | Structural + selected trace | 5 | 35 / 0 |
| [core_apps/chat/models/productivity.py](../core_apps/chat/models/productivity.py) | Structural + selected trace | 5 | 71 / 0 |
| [core_apps/chat/models/reaction.py](../core_apps/chat/models/reaction.py) | Structural + selected trace | 5 | 19 / 0 |
| [core_apps/chat/models/search.py](../core_apps/chat/models/search.py) | Structural + selected trace | 5 | 15 / 0 |
| [core_apps/chat/models/transcription.py](../core_apps/chat/models/transcription.py) | Structural + selected trace | 5 | 16 / 0 |
| [core_apps/chat/models/workspace.py](../core_apps/chat/models/workspace.py) | Structural + selected trace | 5 | 22 / 0 |
| [core_apps/chat/moderation/__init__.py](../core_apps/chat/moderation/__init__.py) | Structural + selected trace | 5 | 0 / 0 |
| [core_apps/chat/moderation/decisions.py](../core_apps/chat/moderation/decisions.py) | Structural + selected trace | 5 | 374 / 7 |
| [core_apps/chat/moderation/notifications.py](../core_apps/chat/moderation/notifications.py) | Structural + selected trace | 5 | 57 / 2 |
| [core_apps/chat/moderation/policy.py](../core_apps/chat/moderation/policy.py) | Structural + selected trace | 5 | 264 / 11 |
| [core_apps/chat/moderation/property_projection.py](../core_apps/chat/moderation/property_projection.py) | Structural + selected trace | 5 | 49 / 2 |
| [core_apps/chat/moderation/provider.py](../core_apps/chat/moderation/provider.py) | Structural + selected trace | 5 | 302 / 7 |
| [core_apps/chat/moderation/queue.py](../core_apps/chat/moderation/queue.py) | Structural + selected trace | 5 | 382 / 7 |
| [core_apps/chat/moderation/sealed.py](../core_apps/chat/moderation/sealed.py) | Structural + selected trace | 5 | 33 / 3 |
| [core_apps/chat/moderation/urls.py](../core_apps/chat/moderation/urls.py) | Structural + selected trace | 5 | 25 / 0 |
| [core_apps/chat/moderation/views.py](../core_apps/chat/moderation/views.py) | Structural + selected trace | 5 | 225 / 10 |
| [core_apps/chat/permissions.py](../core_apps/chat/permissions.py) | Structural + selected trace | 5 | 14 / 1 |
| [core_apps/chat/routing.py](../core_apps/chat/routing.py) | Structural + selected trace | 5 | 8 / 0 |
| [core_apps/chat/serializers/__init__.py](../core_apps/chat/serializers/__init__.py) | Structural + selected trace | 5 | 11 / 0 |
| [core_apps/chat/serializers/conversation.py](../core_apps/chat/serializers/conversation.py) | Structural + selected trace | 5 | 157 / 12 |
| [core_apps/chat/serializers/message.py](../core_apps/chat/serializers/message.py) | Structural + selected trace | 5 | 38 / 1 |
| [core_apps/chat/serializers/participant.py](../core_apps/chat/serializers/participant.py) | Structural + selected trace | 5 | 38 / 3 |
| [core_apps/chat/services/__init__.py](../core_apps/chat/services/__init__.py) | Structural + selected trace | 5 | 15 / 0 |
| [core_apps/chat/services/company_access.py](../core_apps/chat/services/company_access.py) | Structural + selected trace | 5 | 149 / 7 |
| [core_apps/chat/services/conversation_preferences.py](../core_apps/chat/services/conversation_preferences.py) | Structural + selected trace | 5 | 248 / 4 |
| [core_apps/chat/services/direct_access.py](../core_apps/chat/services/direct_access.py) | Structural + selected trace | 5 | 125 / 5 |
| [core_apps/chat/services/forward_batch.py](../core_apps/chat/services/forward_batch.py) | Structural + selected trace | 5 | 96 / 2 |
| [core_apps/chat/services/forwarding.py](../core_apps/chat/services/forwarding.py) | Structural + selected trace | 5 | 174 / 4 |
| [core_apps/chat/services/group_access.py](../core_apps/chat/services/group_access.py) | Structural + selected trace | 5 | 148 / 7 |
| [core_apps/chat/services/group_cursors.py](../core_apps/chat/services/group_cursors.py) | Structural + selected trace | 5 | 45 / 3 |
| [core_apps/chat/services/group_events.py](../core_apps/chat/services/group_events.py) | Structural + selected trace | 5 | 123 / 4 |
| [core_apps/chat/services/group_limits.py](../core_apps/chat/services/group_limits.py) | Structural + selected trace | 5 | 52 / 1 |
| [core_apps/chat/services/group_media_process.py](../core_apps/chat/services/group_media_process.py) | Structural + selected trace | 5 | 25 / 1 |
| [core_apps/chat/services/group_media_remote.py](../core_apps/chat/services/group_media_remote.py) | Structural + selected trace | 5 | 97 / 7 |
| [core_apps/chat/services/group_media_storage.py](../core_apps/chat/services/group_media_storage.py) | Structural + selected trace | 5 | 240 / 6 |
| [core_apps/chat/services/group_media_validation.py](../core_apps/chat/services/group_media_validation.py) | Structural + selected trace | 5 | 139 / 2 |
| [core_apps/chat/services/group_notification_preferences.py](../core_apps/chat/services/group_notification_preferences.py) | Structural + selected trace | 5 | 73 / 3 |
| [core_apps/chat/services/group_operations.py](../core_apps/chat/services/group_operations.py) | Structural + selected trace | 5 | 124 / 3 |
| [core_apps/chat/services/group_outbox.py](../core_apps/chat/services/group_outbox.py) | Structural + selected trace | 5 | 228 / 5 |
| [core_apps/chat/services/group_projection.py](../core_apps/chat/services/group_projection.py) | Structural + selected trace | 5 | 273 / 6 |
| [core_apps/chat/services/group_provisioning.py](../core_apps/chat/services/group_provisioning.py) | Structural + selected trace | 5 | 87 / 3 |
| [core_apps/chat/services/group_rate_limit.py](../core_apps/chat/services/group_rate_limit.py) | Structural + selected trace | 5 | 18 / 1 |
| [core_apps/chat/services/group_send.py](../core_apps/chat/services/group_send.py) | Structural + selected trace | 5 | 230 / 2 |
| [core_apps/chat/services/group_typing.py](../core_apps/chat/services/group_typing.py) | Structural + selected trace | 5 | 67 / 2 |
| [core_apps/chat/services/inbox_preferences.py](../core_apps/chat/services/inbox_preferences.py) | Structural + selected trace | 5 | 92 / 4 |
| [core_apps/chat/services/mention_navigation.py](../core_apps/chat/services/mention_navigation.py) | Structural + selected trace | 5 | 49 / 3 |
| [core_apps/chat/services/mentions.py](../core_apps/chat/services/mentions.py) | Structural + selected trace | 5 | 141 / 8 |
| [core_apps/chat/services/message_mutations.py](../core_apps/chat/services/message_mutations.py) | Structural + selected trace | 5 | 112 / 1 |
| [core_apps/chat/services/message_service.py](../core_apps/chat/services/message_service.py) | Structural + selected trace | 5 | 34 / 0 |
| [core_apps/chat/services/message_service_parts/__init__.py](../core_apps/chat/services/message_service_parts/__init__.py) | Structural + selected trace | 5 | 1 / 0 |
| [core_apps/chat/services/message_service_parts/get_or_create_direct_conversation.py](../core_apps/chat/services/message_service_parts/get_or_create_direct_conversation.py) | Structural + selected trace | 5 | 199 / 6 |
| [core_apps/chat/services/message_service_parts/send_message.py](../core_apps/chat/services/message_service_parts/send_message.py) | Structural + selected trace | 5 | 176 / 3 |
| [core_apps/chat/services/message_tools.py](../core_apps/chat/services/message_tools.py) | Structural + selected trace | 5 | 186 / 8 |
| [core_apps/chat/services/polls.py](../core_apps/chat/services/polls.py) | Structural + selected trace | 5 | 145 / 6 |
| [core_apps/chat/services/property_sharing.py](../core_apps/chat/services/property_sharing.py) | Structural + selected trace | 5 | 122 / 5 |
| [core_apps/chat/services/quick_replies.py](../core_apps/chat/services/quick_replies.py) | Structural + selected trace | 5 | 62 / 3 |
| [core_apps/chat/services/reactions.py](../core_apps/chat/services/reactions.py) | Structural + selected trace | 5 | 107 / 4 |
| [core_apps/chat/services/rich_media.py](../core_apps/chat/services/rich_media.py) | Structural + selected trace | 5 | 217 / 7 |
| [core_apps/chat/services/search.py](../core_apps/chat/services/search.py) | Structural + selected trace | 5 | 224 / 4 |
| [core_apps/chat/services/search_index.py](../core_apps/chat/services/search_index.py) | Structural + selected trace | 5 | 57 / 4 |
| [core_apps/chat/services/transcript_segments.py](../core_apps/chat/services/transcript_segments.py) | Structural + selected trace | 5 | 21 / 1 |
| [core_apps/chat/services/transcription.py](../core_apps/chat/services/transcription.py) | Structural + selected trace | 5 | 199 / 4 |
| [core_apps/chat/services/workspace_inbox.py](../core_apps/chat/services/workspace_inbox.py) | Structural + selected trace | 5 | 82 / 2 |
| [core_apps/chat/tasks.py](../core_apps/chat/tasks.py) | Structural + selected trace | 5 | 23 / 3 |
| [core_apps/chat/tests/__init__.py](../core_apps/chat/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/conftest.py](../core_apps/chat/tests/conftest.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_all_mentions_navigation.py](../core_apps/chat/tests/test_all_mentions_navigation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_consumers.py](../core_apps/chat/tests/test_consumers.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_deployed_acceptance.py](../core_apps/chat/tests/test_deployed_acceptance.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_direct_media.py](../core_apps/chat/tests/test_direct_media.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_discovery.py](../core_apps/chat/tests/test_discovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_durable_chat_push.py](../core_apps/chat/tests/test_durable_chat_push.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_existing_chat_classification.py](../core_apps/chat/tests/test_existing_chat_classification.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_forwarding.py](../core_apps/chat/tests/test_forwarding.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_group_api.py](../core_apps/chat/tests/test_group_api.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_group_concurrency.py](../core_apps/chat/tests/test_group_concurrency.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_group_media.py](../core_apps/chat/tests/test_group_media.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_group_media_remote.py](../core_apps/chat/tests/test_group_media_remote.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_group_messages.py](../core_apps/chat/tests/test_group_messages.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_group_native_media.py](../core_apps/chat/tests/test_group_native_media.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_group_notification_preferences.py](../core_apps/chat/tests/test_group_notification_preferences.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_group_socket.py](../core_apps/chat/tests/test_group_socket.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_inbox_actions.py](../core_apps/chat/tests/test_inbox_actions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_inbox_receipts.py](../core_apps/chat/tests/test_inbox_receipts.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_independent_review.py](../core_apps/chat/tests/test_independent_review.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_media_runtime.py](../core_apps/chat/tests/test_media_runtime.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_message_mutations.py](../core_apps/chat/tests/test_message_mutations.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_models.py](../core_apps/chat/tests/test_models.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_mvp_direct_tools.py](../core_apps/chat/tests/test_mvp_direct_tools.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_mvp_forward_media.py](../core_apps/chat/tests/test_mvp_forward_media.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_mvp_policy_review_authority.py](../core_apps/chat/tests/test_mvp_policy_review_authority.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_policy_push_outbox.py](../core_apps/chat/tests/test_policy_push_outbox.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_private_workspace_preferences.py](../core_apps/chat/tests/test_private_workspace_preferences.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_productivity.py](../core_apps/chat/tests/test_productivity.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_property_sharing.py](../core_apps/chat/tests/test_property_sharing.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_provider_evaluation.py](../core_apps/chat/tests/test_provider_evaluation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_reactions_mentions.py](../core_apps/chat/tests/test_reactions_mentions.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_read_authorization.py](../core_apps/chat/tests/test_read_authorization.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_rental_moderation.py](../core_apps/chat/tests/test_rental_moderation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_rental_policy_commitments.py](../core_apps/chat/tests/test_rental_policy_commitments.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_rich_attachments.py](../core_apps/chat/tests/test_rich_attachments.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_search_migration.py](../core_apps/chat/tests/test_search_migration.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_serializers.py](../core_apps/chat/tests/test_serializers.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_services.py](../core_apps/chat/tests/test_services.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_shortlist_polls.py](../core_apps/chat/tests/test_shortlist_polls.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_transcript_segments.py](../core_apps/chat/tests/test_transcript_segments.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_typing_privacy.py](../core_apps/chat/tests/test_typing_privacy.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_views.py](../core_apps/chat/tests/test_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_voice_transcription.py](../core_apps/chat/tests/test_voice_transcription.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_workspace_group_scope.py](../core_apps/chat/tests/test_workspace_group_scope.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/tests/test_workspace_inbox.py](../core_apps/chat/tests/test_workspace_inbox.py) | test; syntax/support | Supporting scope | — |
| [core_apps/chat/urls.py](../core_apps/chat/urls.py) | Structural + selected trace | 5 | 62 / 0 |
| [core_apps/chat/views/__init__.py](../core_apps/chat/views/__init__.py) | Structural + selected trace | 5 | 14 / 0 |
| [core_apps/chat/views/conversation.py](../core_apps/chat/views/conversation.py) | Structural + selected trace | 5 | 185 / 6 |
| [core_apps/chat/views/forwarding.py](../core_apps/chat/views/forwarding.py) | Structural + selected trace | 5 | 29 / 2 |
| [core_apps/chat/views/group_attachments.py](../core_apps/chat/views/group_attachments.py) | Structural + selected trace | 5 | 150 / 7 |
| [core_apps/chat/views/group_commands.py](../core_apps/chat/views/group_commands.py) | Structural + selected trace | 5 | 36 / 2 |
| [core_apps/chat/views/group_history.py](../core_apps/chat/views/group_history.py) | Structural + selected trace | 5 | 205 / 6 |
| [core_apps/chat/views/interactions.py](../core_apps/chat/views/interactions.py) | Structural + selected trace | 5 | 46 / 2 |
| [core_apps/chat/views/mentions.py](../core_apps/chat/views/mentions.py) | Structural + selected trace | 5 | 28 / 2 |
| [core_apps/chat/views/message.py](../core_apps/chat/views/message.py) | Structural + selected trace | 5 | 104 / 5 |
| [core_apps/chat/views/notification_actions.py](../core_apps/chat/views/notification_actions.py) | Structural + selected trace | 5 | 88 / 1 |
| [core_apps/chat/views/preferences.py](../core_apps/chat/views/preferences.py) | Structural + selected trace | 5 | 63 / 6 |
| [core_apps/chat/views/productivity.py](../core_apps/chat/views/productivity.py) | Structural + selected trace | 5 | 98 / 10 |
| [core_apps/chat/views/search.py](../core_apps/chat/views/search.py) | Structural + selected trace | 5 | 22 / 2 |
| [core_apps/chat/views/transcription.py](../core_apps/chat/views/transcription.py) | Structural + selected trace | 5 | 50 / 3 |

## core_apps/notifications

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/notifications/__init__.py](../core_apps/notifications/__init__.py) | Structural + selected trace | 5 | 1 / 0 |
| [core_apps/notifications/admin.py](../core_apps/notifications/admin.py) | Structural + selected trace | 6 | 31 / 1 |
| [core_apps/notifications/apps.py](../core_apps/notifications/apps.py) | Structural + selected trace | 5 | 8 / 0 |
| [core_apps/notifications/delivery_policy_views.py](../core_apps/notifications/delivery_policy_views.py) | Structural + selected trace | 5 | 69 / 5 |
| [core_apps/notifications/migrations/0001_initial.py](../core_apps/notifications/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0002_rename_devtok_user_active_idx_notificatio_user_id_f0e72c_idx_and_more.py](../core_apps/notifications/migrations/0002_rename_devtok_user_active_idx_notificatio_user_id_f0e72c_idx_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0003_alter_notification_options.py](../core_apps/notifications/migrations/0003_alter_notification_options.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0004_alter_notification_notification_type.py](../core_apps/notifications/migrations/0004_alter_notification_notification_type.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0005_alter_notification_notification_type.py](../core_apps/notifications/migrations/0005_alter_notification_notification_type.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0006_alter_notification_notification_type.py](../core_apps/notifications/migrations/0006_alter_notification_notification_type.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0007_alter_notification_notification_type.py](../core_apps/notifications/migrations/0007_alter_notification_notification_type.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0008_alter_notification_notification_type.py](../core_apps/notifications/migrations/0008_alter_notification_notification_type.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0009_devicetoken_auth_session.py](../core_apps/notifications/migrations/0009_devicetoken_auth_session.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0010_rent_payment_reminders.py](../core_apps/notifications/migrations/0010_rent_payment_reminders.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0011_discovery_and_push.py](../core_apps/notifications/migrations/0011_discovery_and_push.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0012_push_delivery.py](../core_apps/notifications/migrations/0012_push_delivery.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0013_device_chat_actions.py](../core_apps/notifications/migrations/0013_device_chat_actions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0014_notificationscopepreference_notification_scope_and_more.py](../core_apps/notifications/migrations/0014_notificationscopepreference_notification_scope_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/0015_delivery_policy_and_digest_holds.py](../core_apps/notifications/migrations/0015_delivery_policy_and_digest_holds.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/migrations/__init__.py](../core_apps/notifications/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/notifications/models/__init__.py](../core_apps/notifications/models/__init__.py) | Structural + selected trace | 5 | 7 / 0 |
| [core_apps/notifications/models/delivery_policy.py](../core_apps/notifications/models/delivery_policy.py) | Structural + selected trace | 5 | 30 / 0 |
| [core_apps/notifications/models/device.py](../core_apps/notifications/models/device.py) | Structural + selected trace | 5 | 53 / 1 |
| [core_apps/notifications/models/notification.py](../core_apps/notifications/models/notification.py) | Structural + selected trace | 5 | 106 / 2 |
| [core_apps/notifications/models/preferences.py](../core_apps/notifications/models/preferences.py) | Structural + selected trace | 5 | 25 / 0 |
| [core_apps/notifications/models/push_delivery.py](../core_apps/notifications/models/push_delivery.py) | Structural + selected trace | 5 | 13 / 0 |
| [core_apps/notifications/serializers/__init__.py](../core_apps/notifications/serializers/__init__.py) | Structural + selected trace | 5 | 16 / 0 |
| [core_apps/notifications/serializers/device.py](../core_apps/notifications/serializers/device.py) | Structural + selected trace | 5 | 34 / 0 |
| [core_apps/notifications/serializers/notification.py](../core_apps/notifications/serializers/notification.py) | Structural + selected trace | 5 | 205 / 8 |
| [core_apps/notifications/services/__init__.py](../core_apps/notifications/services/__init__.py) | Structural + selected trace | 5 | 4 / 0 |
| [core_apps/notifications/services/delivery_policy.py](../core_apps/notifications/services/delivery_policy.py) | Structural + selected trace | 5 | 209 / 10 |
| [core_apps/notifications/services/fcm_service.py](../core_apps/notifications/services/fcm_service.py) | Structural + selected trace | 5 | 347 / 5 |
| [core_apps/notifications/services/inbox_scope.py](../core_apps/notifications/services/inbox_scope.py) | Structural + selected trace | 5 | 109 / 5 |
| [core_apps/notifications/services/notification_service.py](../core_apps/notifications/services/notification_service.py) | Structural + selected trace | 5 | 20 / 0 |
| [core_apps/notifications/services/notification_service_parts/__init__.py](../core_apps/notifications/services/notification_service_parts/__init__.py) | Structural + selected trace | 5 | 1 / 0 |
| [core_apps/notifications/services/notification_service_parts/logger.py](../core_apps/notifications/services/notification_service_parts/logger.py) | Structural + selected trace | 5 | 6 / 0 |
| [core_apps/notifications/services/notification_service_parts/notification_service.py](../core_apps/notifications/services/notification_service_parts/notification_service.py) | Structural + selected trace | 5 | 29 / 0 |
| [core_apps/notifications/services/notification_service_parts/notification_service_operations/__init__.py](../core_apps/notifications/services/notification_service_parts/notification_service_operations/__init__.py) | Structural + selected trace | 5 | 1 / 0 |
| [core_apps/notifications/services/notification_service_parts/notification_service_operations/notification_devices.py](../core_apps/notifications/services/notification_service_parts/notification_service_operations/notification_devices.py) | Structural + selected trace | 5 | 72 / 2 |
| [core_apps/notifications/services/notification_service_parts/notification_service_operations/notification_events.py](../core_apps/notifications/services/notification_service_parts/notification_service_operations/notification_events.py) | Structural + selected trace | 5 | 102 / 4 |
| [core_apps/notifications/services/notification_service_parts/notification_service_operations/notification_inbox.py](../core_apps/notifications/services/notification_service_parts/notification_service_operations/notification_inbox.py) | Structural + selected trace | 5 | 121 / 6 |
| [core_apps/notifications/services/preferences.py](../core_apps/notifications/services/preferences.py) | Structural + selected trace | 5 | 112 / 5 |
| [core_apps/notifications/services/push_delivery.py](../core_apps/notifications/services/push_delivery.py) | Structural + selected trace | 5 | 318 / 3 |
| [core_apps/notifications/services/push_privacy.py](../core_apps/notifications/services/push_privacy.py) | Structural + selected trace | 5 | 71 / 2 |
| [core_apps/notifications/tasks.py](../core_apps/notifications/tasks.py) | Structural + selected trace | 5 | 12 / 2 |
| [core_apps/notifications/tests/__init__.py](../core_apps/notifications/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_account_scope.py](../core_apps/notifications/tests/test_account_scope.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_delivery_policy.py](../core_apps/notifications/tests/test_delivery_policy.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_fcm_service.py](../core_apps/notifications/tests/test_fcm_service.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_models.py](../core_apps/notifications/tests/test_models.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_mvp_workspace_api.py](../core_apps/notifications/tests/test_mvp_workspace_api.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_push_delivery.py](../core_apps/notifications/tests/test_push_delivery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_push_privacy.py](../core_apps/notifications/tests/test_push_privacy.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_serializers.py](../core_apps/notifications/tests/test_serializers.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_services.py](../core_apps/notifications/tests/test_services.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_views.py](../core_apps/notifications/tests/test_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/tests/test_workspace_scope.py](../core_apps/notifications/tests/test_workspace_scope.py) | test; syntax/support | Supporting scope | — |
| [core_apps/notifications/urls.py](../core_apps/notifications/urls.py) | Structural + selected trace | 5 | 31 / 0 |
| [core_apps/notifications/views/__init__.py](../core_apps/notifications/views/__init__.py) | Structural + selected trace | 5 | 20 / 0 |
| [core_apps/notifications/views/device.py](../core_apps/notifications/views/device.py) | Structural + selected trace | 5 | 84 / 4 |
| [core_apps/notifications/views/notification.py](../core_apps/notifications/views/notification.py) | Structural + selected trace | 5 | 167 / 9 |

## core_apps/support

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/support/__init__.py](../core_apps/support/__init__.py) | Structural + selected trace | 5 | 1 / 0 |
| [core_apps/support/admin.py](../core_apps/support/admin.py) | Structural + selected trace | 6 | 29 / 2 |
| [core_apps/support/apps.py](../core_apps/support/apps.py) | Structural + selected trace | 5 | 8 / 0 |
| [core_apps/support/management/__init__.py](../core_apps/support/management/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/support/management/commands/__init__.py](../core_apps/support/management/commands/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/support/management/commands/backfill_support_private_storage.py](../core_apps/support/management/commands/backfill_support_private_storage.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/support/management/commands/privatize_support_attachments.py](../core_apps/support/management/commands/privatize_support_attachments.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0001_initial.py](../core_apps/support/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0002_ticket_rental_context.py](../core_apps/support/migrations/0002_ticket_rental_context.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0003_helparticle_helpcontact.py](../core_apps/support/migrations/0003_helparticle_helpcontact.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0004_seed_help_content.py](../core_apps/support/migrations/0004_seed_help_content.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0005_ticket_revision.py](../core_apps/support/migrations/0005_ticket_revision.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0006_private_attachments.py](../core_apps/support/migrations/0006_private_attachments.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0007_attachment_content_digest.py](../core_apps/support/migrations/0007_attachment_content_digest.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0008_rolling_writer_compatibility.py](../core_apps/support/migrations/0008_rolling_writer_compatibility.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0009_staged_media.py](../core_apps/support/migrations/0009_staged_media.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0010_ticket_assigned_to_ticket_escalated_and_more.py](../core_apps/support/migrations/0010_ticket_assigned_to_ticket_escalated_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0011_alter_helparticle_workspace_and_more.py](../core_apps/support/migrations/0011_alter_helparticle_workspace_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0012_information_requests.py](../core_apps/support/migrations/0012_information_requests.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0013_evidence_requirement_versions.py](../core_apps/support/migrations/0013_evidence_requirement_versions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/0014_ticketmessage_stable_order.py](../core_apps/support/migrations/0014_ticketmessage_stable_order.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/migrations/__init__.py](../core_apps/support/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/support/models/__init__.py](../core_apps/support/models/__init__.py) | Structural + selected trace | 5 | 9 / 0 |
| [core_apps/support/models/attachment.py](../core_apps/support/models/attachment.py) | Structural + selected trace | 5 | 73 / 2 |
| [core_apps/support/models/help_content.py](../core_apps/support/models/help_content.py) | Structural + selected trace | 5 | 45 / 3 |
| [core_apps/support/models/information.py](../core_apps/support/models/information.py) | Structural + selected trace | 5 | 41 / 0 |
| [core_apps/support/models/message.py](../core_apps/support/models/message.py) | Structural + selected trace | 5 | 42 / 1 |
| [core_apps/support/models/operations.py](../core_apps/support/models/operations.py) | Structural + selected trace | 5 | 33 / 0 |
| [core_apps/support/models/ticket.py](../core_apps/support/models/ticket.py) | Structural + selected trace | 5 | 82 / 1 |
| [core_apps/support/pagination.py](../core_apps/support/pagination.py) | Structural + selected trace | 5 | 11 / 0 |
| [core_apps/support/serializers/__init__.py](../core_apps/support/serializers/__init__.py) | Structural + selected trace | 5 | 20 / 0 |
| [core_apps/support/serializers/help_center.py](../core_apps/support/serializers/help_center.py) | Structural + selected trace | 5 | 16 / 0 |
| [core_apps/support/serializers/ticket.py](../core_apps/support/serializers/ticket.py) | Structural + selected trace | 5 | 134 / 4 |
| [core_apps/support/services/__init__.py](../core_apps/support/services/__init__.py) | Structural + selected trace | 5 | 17 / 0 |
| [core_apps/support/services/help_center_service.py](../core_apps/support/services/help_center_service.py) | Structural + selected trace | 5 | 28 / 1 |
| [core_apps/support/services/information.py](../core_apps/support/services/information.py) | Structural + selected trace | 5 | 115 / 6 |
| [core_apps/support/services/information_evidence.py](../core_apps/support/services/information_evidence.py) | Structural + selected trace | 5 | 67 / 6 |
| [core_apps/support/services/operations.py](../core_apps/support/services/operations.py) | Structural + selected trace | 5 | 292 / 10 |
| [core_apps/support/services/payment_reports.py](../core_apps/support/services/payment_reports.py) | Structural + selected trace | 5 | 112 / 5 |
| [core_apps/support/services/private_attachments.py](../core_apps/support/services/private_attachments.py) | Structural + selected trace | 5 | 55 / 2 |
| [core_apps/support/services/staff_replies.py](../core_apps/support/services/staff_replies.py) | Structural + selected trace | 5 | 158 / 4 |
| [core_apps/support/services/staged_attachments.py](../core_apps/support/services/staged_attachments.py) | Structural + selected trace | 5 | 179 / 4 |
| [core_apps/support/services/ticket_service.py](../core_apps/support/services/ticket_service.py) | Structural + selected trace | 5 | 27 / 0 |
| [core_apps/support/services/ticket_service_parts/__init__.py](../core_apps/support/services/ticket_service_parts/__init__.py) | Structural + selected trace | 5 | 1 / 0 |
| [core_apps/support/services/ticket_service_parts/create_ticket.py](../core_apps/support/services/ticket_service_parts/create_ticket.py) | Structural + selected trace | 5 | 228 / 3 |
| [core_apps/support/services/ticket_service_parts/get_ticket_detail.py](../core_apps/support/services/ticket_service_parts/get_ticket_detail.py) | Structural + selected trace | 5 | 81 / 2 |
| [core_apps/support/services/workspace.py](../core_apps/support/services/workspace.py) | Structural + selected trace | 5 | 14 / 1 |
| [core_apps/support/storage.py](../core_apps/support/storage.py) | Structural + selected trace | 5 | 12 / 0 |
| [core_apps/support/tasks.py](../core_apps/support/tasks.py) | Structural + selected trace | 5 | 8 / 1 |
| [core_apps/support/tests/__init__.py](../core_apps/support/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/conftest.py](../core_apps/support/tests/conftest.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_creation_recovery.py](../core_apps/support/tests/test_creation_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_durable_storage.py](../core_apps/support/tests/test_durable_storage.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_information_evidence.py](../core_apps/support/tests/test_information_evidence.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_information_requests.py](../core_apps/support/tests/test_information_requests.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_inquiry_resolution.py](../core_apps/support/tests/test_inquiry_resolution.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_models.py](../core_apps/support/tests/test_models.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_mvp_message_ordering.py](../core_apps/support/tests/test_mvp_message_ordering.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_operator_console.py](../core_apps/support/tests/test_operator_console.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_platform_payment_reports.py](../core_apps/support/tests/test_platform_payment_reports.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_private_attachments.py](../core_apps/support/tests/test_private_attachments.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_scope_roundtrip.py](../core_apps/support/tests/test_scope_roundtrip.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_services.py](../core_apps/support/tests/test_services.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_shared_admin.py](../core_apps/support/tests/test_shared_admin.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_staff_replies.py](../core_apps/support/tests/test_staff_replies.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_staged_media.py](../core_apps/support/tests/test_staged_media.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_upload_recovery.py](../core_apps/support/tests/test_upload_recovery.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/tests/test_views.py](../core_apps/support/tests/test_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/support/ticket_admin.py](../core_apps/support/ticket_admin.py) | Structural + selected trace | 6 | 185 / 13 |
| [core_apps/support/urls.py](../core_apps/support/urls.py) | Structural + selected trace | 5 | 57 / 0 |
| [core_apps/support/views/__init__.py](../core_apps/support/views/__init__.py) | Structural + selected trace | 5 | 13 / 0 |
| [core_apps/support/views/attachments.py](../core_apps/support/views/attachments.py) | Structural + selected trace | 5 | 94 / 1 |
| [core_apps/support/views/help_center.py](../core_apps/support/views/help_center.py) | Structural + selected trace | 5 | 29 / 1 |
| [core_apps/support/views/recovery.py](../core_apps/support/views/recovery.py) | Structural + selected trace | 5 | 70 / 3 |
| [core_apps/support/views/reply_recovery.py](../core_apps/support/views/reply_recovery.py) | Structural + selected trace | 5 | 69 / 3 |
| [core_apps/support/views/ticket.py](../core_apps/support/views/ticket.py) | Structural + selected trace | 5 | 196 / 7 |
| [core_apps/support/views/uploads.py](../core_apps/support/views/uploads.py) | Structural + selected trace | 5 | 167 / 4 |

## core_apps/admin_api

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/admin_api/admin.py](../core_apps/admin_api/admin.py) | Structural + selected trace | 6 | 153 / 12 |
| [core_apps/admin_api/apps.py](../core_apps/admin_api/apps.py) | Structural + selected trace | 6 | 8 / 0 |
| [core_apps/admin_api/filters.py](../core_apps/admin_api/filters.py) | Structural + selected trace | 6 | 84 / 5 |
| [core_apps/admin_api/migrations/0001_initial.py](../core_apps/admin_api/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0002_alter_staffprofile_role_name.py](../core_apps/admin_api/migrations/0002_alter_staffprofile_role_name.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0003_platformpreferenceaudit_platformpreferences_and_more.py](../core_apps/admin_api/migrations/0003_platformpreferenceaudit_platformpreferences_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0004_staffauthorityaudit.py](../core_apps/admin_api/migrations/0004_staffauthorityaudit.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0005_kycsubmission_evidence_digest_and_more.py](../core_apps/admin_api/migrations/0005_kycsubmission_evidence_digest_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0006_reconcile_legacy_identity.py](../core_apps/admin_api/migrations/0006_reconcile_legacy_identity.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0007_durable_push_campaigns.py](../core_apps/admin_api/migrations/0007_durable_push_campaigns.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0008_alter_staffprofile_role_name.py](../core_apps/admin_api/migrations/0008_alter_staffprofile_role_name.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0009_remove_campaignrecipient_campaign_one_recipient_and_more.py](../core_apps/admin_api/migrations/0009_remove_campaignrecipient_campaign_one_recipient_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/0010_kyc_document_decisions.py](../core_apps/admin_api/migrations/0010_kyc_document_decisions.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/migrations/__init__.py](../core_apps/admin_api/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/admin_api/models/__init__.py](../core_apps/admin_api/models/__init__.py) | Structural + selected trace | 6 | 9 / 0 |
| [core_apps/admin_api/models/kyc_submission.py](../core_apps/admin_api/models/kyc_submission.py) | Structural + selected trace | 6 | 73 / 2 |
| [core_apps/admin_api/models/platform_preferences.py](../core_apps/admin_api/models/platform_preferences.py) | Structural + selected trace | 6 | 49 / 2 |
| [core_apps/admin_api/models/push_campaign.py](../core_apps/admin_api/models/push_campaign.py) | Structural + selected trace | 6 | 69 / 0 |
| [core_apps/admin_api/models/staff_authority_audit.py](../core_apps/admin_api/models/staff_authority_audit.py) | Structural + selected trace | 6 | 20 / 0 |
| [core_apps/admin_api/models/staff_profile.py](../core_apps/admin_api/models/staff_profile.py) | Structural + selected trace | 6 | 47 / 1 |
| [core_apps/admin_api/models/user_report.py](../core_apps/admin_api/models/user_report.py) | Structural + selected trace | 6 | 78 / 1 |
| [core_apps/admin_api/pagination.py](../core_apps/admin_api/pagination.py) | Structural + selected trace | 6 | 8 / 0 |
| [core_apps/admin_api/permissions.py](../core_apps/admin_api/permissions.py) | Structural + selected trace | 6 | 135 / 5 |
| [core_apps/admin_api/serializers/__init__.py](../core_apps/admin_api/serializers/__init__.py) | Structural + selected trace | 6 | 43 / 0 |
| [core_apps/admin_api/serializers/admin_user_serializers.py](../core_apps/admin_api/serializers/admin_user_serializers.py) | Structural + selected trace | 6 | 89 / 8 |
| [core_apps/admin_api/serializers/kyc_serializers.py](../core_apps/admin_api/serializers/kyc_serializers.py) | Structural + selected trace | 6 | 72 / 7 |
| [core_apps/admin_api/serializers/moderation_serializers.py](../core_apps/admin_api/serializers/moderation_serializers.py) | Structural + selected trace | 6 | 62 / 6 |
| [core_apps/admin_api/serializers/property_serializers.py](../core_apps/admin_api/serializers/property_serializers.py) | Structural + selected trace | 6 | 109 / 9 |
| [core_apps/admin_api/serializers/report_serializers.py](../core_apps/admin_api/serializers/report_serializers.py) | Structural + selected trace | 6 | 16 / 0 |
| [core_apps/admin_api/serializers/report_serializers_parts/__init__.py](../core_apps/admin_api/serializers/report_serializers_parts/__init__.py) | Structural + selected trace | 6 | 1 / 0 |
| [core_apps/admin_api/serializers/report_serializers_parts/overview_ticket_serializer.py](../core_apps/admin_api/serializers/report_serializers_parts/overview_ticket_serializer.py) | Structural + selected trace | 6 | 63 / 6 |
| [core_apps/admin_api/serializers/report_serializers_parts/support_ticket_serializer.py](../core_apps/admin_api/serializers/report_serializers_parts/support_ticket_serializer.py) | Structural + selected trace | 6 | 88 / 9 |
| [core_apps/admin_api/serializers/staff_serializers.py](../core_apps/admin_api/serializers/staff_serializers.py) | Structural + selected trace | 6 | 62 / 5 |
| [core_apps/admin_api/services/__init__.py](../core_apps/admin_api/services/__init__.py) | Structural + selected trace | 6 | 87 / 0 |
| [core_apps/admin_api/services/analytics_service.py](../core_apps/admin_api/services/analytics_service.py) | Structural + selected trace | 6 | 151 / 2 |
| [core_apps/admin_api/services/catalog_registry.py](../core_apps/admin_api/services/catalog_registry.py) | Structural + selected trace | 6 | 93 / 2 |
| [core_apps/admin_api/services/commerce_benefit_editor.py](../core_apps/admin_api/services/commerce_benefit_editor.py) | Structural + selected trace | 6 | 37 / 2 |
| [core_apps/admin_api/services/commerce_catalog_registry.py](../core_apps/admin_api/services/commerce_catalog_registry.py) | Structural + selected trace | 6 | 175 / 3 |
| [core_apps/admin_api/services/content_editor.py](../core_apps/admin_api/services/content_editor.py) | Structural + selected trace | 6 | 123 / 4 |
| [core_apps/admin_api/services/content_mvp.py](../core_apps/admin_api/services/content_mvp.py) | Structural + selected trace | 6 | 34 / 5 |
| [core_apps/admin_api/services/content_registry.py](../core_apps/admin_api/services/content_registry.py) | Structural + selected trace | 6 | 253 / 7 |
| [core_apps/admin_api/services/dashboard_service.py](../core_apps/admin_api/services/dashboard_service.py) | Structural + selected trace | 6 | 23 / 0 |
| [core_apps/admin_api/services/dashboard_service_parts/__init__.py](../core_apps/admin_api/services/dashboard_service_parts/__init__.py) | Structural + selected trace | 6 | 1 / 0 |
| [core_apps/admin_api/services/dashboard_service_parts/get_dashboard_overview_stats.py](../core_apps/admin_api/services/dashboard_service_parts/get_dashboard_overview_stats.py) | Structural + selected trace | 6 | 157 / 1 |
| [core_apps/admin_api/services/dashboard_service_parts/get_executive_dashboard_stats.py](../core_apps/admin_api/services/dashboard_service_parts/get_executive_dashboard_stats.py) | Structural + selected trace | 6 | 116 / 2 |
| [core_apps/admin_api/services/financials_service.py](../core_apps/admin_api/services/financials_service.py) | Structural + selected trace | 6 | 19 / 0 |
| [core_apps/admin_api/services/financials_service_parts/__init__.py](../core_apps/admin_api/services/financials_service_parts/__init__.py) | Structural + selected trace | 6 | 1 / 0 |
| [core_apps/admin_api/services/financials_service_parts/get_financial_summary.py](../core_apps/admin_api/services/financials_service_parts/get_financial_summary.py) | Structural + selected trace | 6 | 87 / 3 |
| [core_apps/admin_api/services/financials_service_parts/get_transactions_list.py](../core_apps/admin_api/services/financials_service_parts/get_transactions_list.py) | Structural + selected trace | 6 | 65 / 1 |
| [core_apps/admin_api/services/kyc_service.py](../core_apps/admin_api/services/kyc_service.py) | Structural + selected trace | 6 | 248 / 7 |
| [core_apps/admin_api/services/moderation_service.py](../core_apps/admin_api/services/moderation_service.py) | Structural + selected trace | 6 | 77 / 3 |
| [core_apps/admin_api/services/navigation.py](../core_apps/admin_api/services/navigation.py) | Structural + selected trace | 6 | 65 / 1 |
| [core_apps/admin_api/services/property_service.py](../core_apps/admin_api/services/property_service.py) | Structural + selected trace | 6 | 35 / 0 |
| [core_apps/admin_api/services/property_service_parts/__init__.py](../core_apps/admin_api/services/property_service_parts/__init__.py) | Structural + selected trace | 6 | 1 / 0 |
| [core_apps/admin_api/services/property_service_parts/get_admin_properties_queryset.py](../core_apps/admin_api/services/property_service_parts/get_admin_properties_queryset.py) | Structural + selected trace | 6 | 131 / 3 |
| [core_apps/admin_api/services/property_service_parts/get_admin_property_detail.py](../core_apps/admin_api/services/property_service_parts/get_admin_property_detail.py) | Structural + selected trace | 6 | 171 / 4 |
| [core_apps/admin_api/services/push_campaigns.py](../core_apps/admin_api/services/push_campaigns.py) | Structural + selected trace | 6 | 235 / 8 |
| [core_apps/admin_api/services/report_service.py](../core_apps/admin_api/services/report_service.py) | Structural + selected trace | 6 | 157 / 6 |
| [core_apps/admin_api/services/settings_service.py](../core_apps/admin_api/services/settings_service.py) | Structural + selected trace | 6 | 22 / 2 |
| [core_apps/admin_api/services/staff_service.py](../core_apps/admin_api/services/staff_service.py) | Structural + selected trace | 6 | 309 / 7 |
| [core_apps/admin_api/services/system_service.py](../core_apps/admin_api/services/system_service.py) | Structural + selected trace | 6 | 25 / 0 |
| [core_apps/admin_api/services/system_service_parts/__init__.py](../core_apps/admin_api/services/system_service_parts/__init__.py) | Structural + selected trace | 6 | 1 / 0 |
| [core_apps/admin_api/services/system_service_parts/get_audit_logs.py](../core_apps/admin_api/services/system_service_parts/get_audit_logs.py) | Structural + selected trace | 6 | 112 / 2 |
| [core_apps/admin_api/services/system_service_parts/get_system_health.py](../core_apps/admin_api/services/system_service_parts/get_system_health.py) | Structural + selected trace | 6 | 57 / 3 |
| [core_apps/admin_api/services/system_service_parts/logger.py](../core_apps/admin_api/services/system_service_parts/logger.py) | Structural + selected trace | 6 | 4 / 0 |
| [core_apps/admin_api/services/user_service.py](../core_apps/admin_api/services/user_service.py) | Structural + selected trace | 6 | 209 / 5 |
| [core_apps/admin_api/services/workspace_campaigns.py](../core_apps/admin_api/services/workspace_campaigns.py) | Structural + selected trace | 6 | 361 / 10 |
| [core_apps/admin_api/tasks.py](../core_apps/admin_api/tasks.py) | Structural + selected trace | 6 | 7 / 1 |
| [core_apps/admin_api/tests/__init__.py](../core_apps/admin_api/tests/__init__.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_analytics_periods.py](../core_apps/admin_api/tests/test_analytics_periods.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_audit_authority.py](../core_apps/admin_api/tests/test_audit_authority.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_audit_projections.py](../core_apps/admin_api/tests/test_audit_projections.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_catalog_editor.py](../core_apps/admin_api/tests/test_catalog_editor.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_commerce_catalog_editor.py](../core_apps/admin_api/tests/test_commerce_catalog_editor.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_content_editor.py](../core_apps/admin_api/tests/test_content_editor.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_dashboard_truth.py](../core_apps/admin_api/tests/test_dashboard_truth.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_followups.py](../core_apps/admin_api/tests/test_followups.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_kyc_admin.py](../core_apps/admin_api/tests/test_kyc_admin.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_models.py](../core_apps/admin_api/tests/test_models.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_mvp_boundaries.py](../core_apps/admin_api/tests/test_mvp_boundaries.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_mvp_campaign_cancellation.py](../core_apps/admin_api/tests/test_mvp_campaign_cancellation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_mvp_campaigns.py](../core_apps/admin_api/tests/test_mvp_campaigns.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_mvp_content.py](../core_apps/admin_api/tests/test_mvp_content.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_navigation.py](../core_apps/admin_api/tests/test_navigation.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_pagination_contract.py](../core_apps/admin_api/tests/test_pagination_contract.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_plan_benefit_editor.py](../core_apps/admin_api/tests/test_plan_benefit_editor.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_property_type_catalog.py](../core_apps/admin_api/tests/test_property_type_catalog.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_push_campaigns.py](../core_apps/admin_api/tests/test_push_campaigns.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_services.py](../core_apps/admin_api/tests/test_services.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_views.py](../core_apps/admin_api/tests/test_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/tests/test_workspace_campaigns.py](../core_apps/admin_api/tests/test_workspace_campaigns.py) | test; syntax/support | Supporting scope | — |
| [core_apps/admin_api/urls.py](../core_apps/admin_api/urls.py) | Structural + selected trace | 6 | 159 / 0 |
| [core_apps/admin_api/views/__init__.py](../core_apps/admin_api/views/__init__.py) | Structural + selected trace | 6 | 99 / 0 |
| [core_apps/admin_api/views/analytics.py](../core_apps/admin_api/views/analytics.py) | Structural + selected trace | 6 | 28 / 1 |
| [core_apps/admin_api/views/content.py](../core_apps/admin_api/views/content.py) | Structural + selected trace | 6 | 139 / 4 |
| [core_apps/admin_api/views/dashboard.py](../core_apps/admin_api/views/dashboard.py) | Structural + selected trace | 6 | 37 / 2 |
| [core_apps/admin_api/views/financials.py](../core_apps/admin_api/views/financials.py) | Structural + selected trace | 6 | 52 / 2 |
| [core_apps/admin_api/views/followups.py](../core_apps/admin_api/views/followups.py) | Structural + selected trace | 6 | 100 / 3 |
| [core_apps/admin_api/views/kyc.py](../core_apps/admin_api/views/kyc.py) | Structural + selected trace | 6 | 122 / 6 |
| [core_apps/admin_api/views/moderation.py](../core_apps/admin_api/views/moderation.py) | Structural + selected trace | 6 | 56 / 3 |
| [core_apps/admin_api/views/property_views.py](../core_apps/admin_api/views/property_views.py) | Structural + selected trace | 6 | 131 / 6 |
| [core_apps/admin_api/views/reports.py](../core_apps/admin_api/views/reports.py) | Structural + selected trace | 6 | 152 / 7 |
| [core_apps/admin_api/views/session.py](../core_apps/admin_api/views/session.py) | Structural + selected trace | 6 | 35 / 1 |
| [core_apps/admin_api/views/settings.py](../core_apps/admin_api/views/settings.py) | Structural + selected trace | 6 | 27 / 2 |
| [core_apps/admin_api/views/staff.py](../core_apps/admin_api/views/staff.py) | Structural + selected trace | 6 | 110 / 5 |
| [core_apps/admin_api/views/support.py](../core_apps/admin_api/views/support.py) | Structural + selected trace | 6 | 119 / 5 |
| [core_apps/admin_api/views/system.py](../core_apps/admin_api/views/system.py) | Structural + selected trace | 6 | 117 / 7 |
| [core_apps/admin_api/views/users.py](../core_apps/admin_api/views/users.py) | Structural + selected trace | 6 | 92 / 4 |

## core_apps/common

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [core_apps/common/__init__.py](../core_apps/common/__init__.py) | Structural + selected trace | 6 | 0 / 0 |
| [core_apps/common/admin.py](../core_apps/common/admin.py) | Structural + selected trace | 6 | 17 / 0 |
| [core_apps/common/admin_apps.py](../core_apps/common/admin_apps.py) | Structural + selected trace | 6 | 7 / 0 |
| [core_apps/common/admin_site.py](../core_apps/common/admin_site.py) | Structural + selected trace | 6 | 28 / 2 |
| [core_apps/common/advanced_housing_translations.py](../core_apps/common/advanced_housing_translations.py) | Structural + selected trace | 6 | 416 / 0 |
| [core_apps/common/advanced_housing_v2_translations.py](../core_apps/common/advanced_housing_v2_translations.py) | Structural + selected trace | 6 | 340 / 0 |
| [core_apps/common/api_usage_plugin.py](../core_apps/common/api_usage_plugin.py) | Structural + selected trace | 6 | 68 / 5 |
| [core_apps/common/app_associations.py](../core_apps/common/app_associations.py) | Structural + selected trace | 6 | 60 / 3 |
| [core_apps/common/apps.py](../core_apps/common/apps.py) | Structural + selected trace | 6 | 12 / 1 |
| [core_apps/common/billing_translations.py](../core_apps/common/billing_translations.py) | Structural + selected trace | 4 | 34 / 0 |
| [core_apps/common/catalog_admin.py](../core_apps/common/catalog_admin.py) | Structural + selected trace | 6 | 14 / 3 |
| [core_apps/common/company_translations.py](../core_apps/common/company_translations.py) | Structural + selected trace | 6 | 288 / 0 |
| [core_apps/common/conftest.py](../core_apps/common/conftest.py) | Structural + selected trace | 6 | 15 / 1 |
| [core_apps/common/consumers.py](../core_apps/common/consumers.py) | Structural + selected trace | 6 | 67 / 6 |
| [core_apps/common/content/public_pages_v2.py](../core_apps/common/content/public_pages_v2.py) | Structural + selected trace | 6 | 123 / 0 |
| [core_apps/common/content_admin.py](../core_apps/common/content_admin.py) | Structural + selected trace | 6 | 56 / 3 |
| [core_apps/common/content_audience.py](../core_apps/common/content_audience.py) | Structural + selected trace | 6 | 19 / 2 |
| [core_apps/common/content_models.py](../core_apps/common/content_models.py) | Structural + selected trace | 6 | 108 / 4 |
| [core_apps/common/contract_testing.py](../core_apps/common/contract_testing.py) | Structural + selected trace | 6 | 29 / 1 |
| [core_apps/common/cookie_auth.py](../core_apps/common/cookie_auth.py) | Structural + selected trace | 6 | 36 / 1 |
| [core_apps/common/cors_middleware.py](../core_apps/common/cors_middleware.py) | Structural + selected trace | 6 | 45 / 3 |
| [core_apps/common/demo_seed/__init__.py](../core_apps/common/demo_seed/__init__.py) | Structural + selected trace | 6 | 1 / 0 |
| [core_apps/common/demo_seed/scenarios.py](../core_apps/common/demo_seed/scenarios.py) | Structural + selected trace | 6 | 39 / 1 |
| [core_apps/common/demo_seed/schema.py](../core_apps/common/demo_seed/schema.py) | Structural + selected trace | 6 | 220 / 7 |
| [core_apps/common/idempotency.py](../core_apps/common/idempotency.py) | Structural + selected trace | 6 | 249 / 10 |
| [core_apps/common/locale_middleware.py](../core_apps/common/locale_middleware.py) | Structural + selected trace | 6 | 105 / 4 |
| [core_apps/common/management/__init__.py](../core_apps/common/management/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/__init__.py](../core_apps/common/management/commands/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/audit_release_catalog.py](../core_apps/common/management/commands/audit_release_catalog.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/export_api_inventory.py](../core_apps/common/management/commands/export_api_inventory.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/migrate_release.py](../core_apps/common/management/commands/migrate_release.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/recovery_journal_readiness.py](../core_apps/common/management/commands/recovery_journal_readiness.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/run_general_worker.py](../core_apps/common/management/commands/run_general_worker.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/runtime_readiness.py](../core_apps/common/management/commands/runtime_readiness.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/seed_data.py](../core_apps/common/management/commands/seed_data.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/seed_db.py](../core_apps/common/management/commands/seed_db.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/management/commands/seed_system_demo.py](../core_apps/common/management/commands/seed_system_demo.py) | application/support; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0001_initial.py](../core_apps/common/migrations/0001_initial.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0002_alter_contentview_created_at.py](../core_apps/common/migrations/0002_alter_contentview_created_at.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0003_publiccontentpage.py](../core_apps/common/migrations/0003_publiccontentpage.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0004_seed_public_content.py](../core_apps/common/migrations/0004_seed_public_content.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0005_releasenote_and_more.py](../core_apps/common/migrations/0005_releasenote_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0006_seed_release_notes.py](../core_apps/common/migrations/0006_seed_release_notes.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0007_paymobcallbackevent.py](../core_apps/common/migrations/0007_paymobcallbackevent.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0008_runtime_incidents.py](../core_apps/common/migrations/0008_runtime_incidents.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0009_public_content_v2.py](../core_apps/common/migrations/0009_public_content_v2.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/0010_alter_releasenote_workspace_contenteditaudit_and_more.py](../core_apps/common/migrations/0010_alter_releasenote_workspace_contenteditaudit_and_more.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/migrations/__init__.py](../core_apps/common/migrations/__init__.py) | migration; syntax/support | Supporting scope | — |
| [core_apps/common/models.py](../core_apps/common/models.py) | Structural + selected trace | 6 | 80 / 2 |
| [core_apps/common/mvp_scope.py](../core_apps/common/mvp_scope.py) | Structural + selected trace | 6 | 92 / 5 |
| [core_apps/common/pages_serializers.py](../core_apps/common/pages_serializers.py) | Structural + selected trace | 6 | 11 / 0 |
| [core_apps/common/pages_urls.py](../core_apps/common/pages_urls.py) | Structural + selected trace | 6 | 20 / 0 |
| [core_apps/common/pages_views.py](../core_apps/common/pages_views.py) | Structural + selected trace | 6 | 68 / 3 |
| [core_apps/common/pagination.py](../core_apps/common/pagination.py) | Structural + selected trace | 6 | 52 / 2 |
| [core_apps/common/paymob.py](../core_apps/common/paymob.py) | Structural + selected trace | 4 | 97 / 3 |
| [core_apps/common/paymob_checkout.py](../core_apps/common/paymob_checkout.py) | Structural + selected trace | 4 | 137 / 3 |
| [core_apps/common/paymob_models.py](../core_apps/common/paymob_models.py) | Structural + selected trace | 4 | 19 / 0 |
| [core_apps/common/paymob_views.py](../core_apps/common/paymob_views.py) | Structural + selected trace | 4 | 118 / 3 |
| [core_apps/common/pdf_inspection.py](../core_apps/common/pdf_inspection.py) | Structural + selected trace | 6 | 117 / 2 |
| [core_apps/common/private_media_policy.py](../core_apps/common/private_media_policy.py) | Structural + selected trace | 6 | 152 / 3 |
| [core_apps/common/private_storage.py](../core_apps/common/private_storage.py) | Structural + selected trace | 6 | 197 / 15 |
| [core_apps/common/recovery.py](../core_apps/common/recovery.py) | Structural + selected trace | 6 | 290 / 13 |
| [core_apps/common/recovery_postgres.py](../core_apps/common/recovery_postgres.py) | Structural + selected trace | 6 | 160 / 8 |
| [core_apps/common/release_views.py](../core_apps/common/release_views.py) | Structural + selected trace | 6 | 55 / 1 |
| [core_apps/common/renderers.py](../core_apps/common/renderers.py) | Structural + selected trace | 6 | 54 / 2 |
| [core_apps/common/response_messages.py](../core_apps/common/response_messages.py) | Structural + selected trace | 6 | 89 / 5 |
| [core_apps/common/response_policy.py](../core_apps/common/response_policy.py) | Structural + selected trace | 6 | 140 / 5 |
| [core_apps/common/routing.py](../core_apps/common/routing.py) | Structural + selected trace | 6 | 7 / 0 |
| [core_apps/common/runtime_metrics.py](../core_apps/common/runtime_metrics.py) | Structural + selected trace | 6 | 183 / 7 |
| [core_apps/common/runtime_models.py](../core_apps/common/runtime_models.py) | Structural + selected trace | 6 | 11 / 0 |
| [core_apps/common/runtime_views.py](../core_apps/common/runtime_views.py) | Structural + selected trace | 6 | 17 / 1 |
| [core_apps/common/shared_housing_translations.py](../core_apps/common/shared_housing_translations.py) | Structural + selected trace | 6 | 36 / 0 |
| [core_apps/common/tasks.py](../core_apps/common/tasks.py) | Structural + selected trace | 6 | 43 / 4 |
| [core_apps/common/test_app_associations.py](../core_apps/common/test_app_associations.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_background_scope.py](../core_apps/common/test_background_scope.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_catalog_audit.py](../core_apps/common/test_catalog_audit.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_company_probe.py](../core_apps/common/test_company_probe.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_consumers.py](../core_apps/common/test_consumers.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_digitalocean_runtime.py](../core_apps/common/test_digitalocean_runtime.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_managed_content.py](../core_apps/common/test_managed_content.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_mobile_locale.py](../core_apps/common/test_mobile_locale.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_mvp_help_truth.py](../core_apps/common/test_mvp_help_truth.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_pages_views.py](../core_apps/common/test_pages_views.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_paymob_callbacks.py](../core_apps/common/test_paymob_callbacks.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_paymob_checkout.py](../core_apps/common/test_paymob_checkout.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_recovery_postgres.py](../core_apps/common/test_recovery_postgres.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_release_compatibility.py](../core_apps/common/test_release_compatibility.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_release_schema.py](../core_apps/common/test_release_schema.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_response_contract.py](../core_apps/common/test_response_contract.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_rolling_writer_compatibility.py](../core_apps/common/test_rolling_writer_compatibility.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_runtime.py](../core_apps/common/test_runtime.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/test_runtime_metrics.py](../core_apps/common/test_runtime_metrics.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/testing.py](../core_apps/common/testing.py) | Structural + selected trace | 6 | 40 / 5 |
| [core_apps/common/tests.py](../core_apps/common/tests.py) | test; syntax/support | Supporting scope | — |
| [core_apps/common/tests_mvp_scope.py](../core_apps/common/tests_mvp_scope.py) | Structural + selected trace | 6 | 94 / 10 |
| [core_apps/common/translation.py](../core_apps/common/translation.py) | Structural + selected trace | 6 | 91 / 4 |
| [core_apps/common/translation_catalog.py](../core_apps/common/translation_catalog.py) | Structural + selected trace | 6 | 336 / 0 |
| [core_apps/common/ws_auth.py](../core_apps/common/ws_auth.py) | Structural + selected trace | 6 | 119 / 7 |

## config

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [config/__init__.py](../config/__init__.py) | Structural + selected trace | 6 | 3 / 0 |
| [config/advanced_housing.py](../config/advanced_housing.py) | Structural + selected trace | 6 | 110 / 8 |
| [config/asgi.py](../config/asgi.py) | Structural + selected trace | 6 | 45 / 0 |
| [config/background.py](../config/background.py) | Structural + selected trace | 6 | 122 / 3 |
| [config/celery.py](../config/celery.py) | Structural + selected trace | 6 | 10 / 0 |
| [config/planning.py](../config/planning.py) | Structural + selected trace | 6 | 36 / 1 |
| [config/rental_simulation.py](../config/rental_simulation.py) | Structural + selected trace | 6 | 8 / 1 |
| [config/runtime.py](../config/runtime.py) | Structural + selected trace | 6 | 239 / 13 |
| [config/settings/__init__.py](../config/settings/__init__.py) | Structural + selected trace | 6 | 0 / 0 |
| [config/settings/advanced_mock.py](../config/settings/advanced_mock.py) | Structural + selected trace | 6 | 28 / 0 |
| [config/settings/background_probe.py](../config/settings/background_probe.py) | Structural + selected trace | 6 | 21 / 0 |
| [config/settings/base.py](../config/settings/base.py) | Structural + selected trace | 6 | 774 / 1 |
| [config/settings/build.py](../config/settings/build.py) | Structural + selected trace | 6 | 8 / 0 |
| [config/settings/capture_dev.py](../config/settings/capture_dev.py) | Structural + selected trace | 6 | 29 / 0 |
| [config/settings/commerce_sandbox.py](../config/settings/commerce_sandbox.py) | Structural + selected trace | 6 | 14 / 0 |
| [config/settings/demo.py](../config/settings/demo.py) | Structural + selected trace | 6 | 21 / 0 |
| [config/settings/local.py](../config/settings/local.py) | Structural + selected trace | 6 | 82 / 0 |
| [config/settings/local_sqlite.py](../config/settings/local_sqlite.py) | Structural + selected trace | 6 | 50 / 0 |
| [config/settings/mvp_http_test.py](../config/settings/mvp_http_test.py) | application/support; syntax/support | Supporting scope | — |
| [config/settings/postgres_test.py](../config/settings/postgres_test.py) | application/support; syntax/support | Supporting scope | — |
| [config/settings/production.py](../config/settings/production.py) | Structural + selected trace | 6 | 53 / 0 |
| [config/settings/staging.py](../config/settings/staging.py) | Structural + selected trace | 6 | 12 / 0 |
| [config/settings/staging_mock.py](../config/settings/staging_mock.py) | Structural + selected trace | 6 | 23 / 0 |
| [config/settings/test.py](../config/settings/test.py) | Structural + selected trace | 6 | 67 / 0 |
| [config/student_housing.py](../config/student_housing.py) | Structural + selected trace | 6 | 35 / 1 |
| [config/urls.py](../config/urls.py) | Structural + selected trace | 6 | 90 / 0 |
| [config/wsgi.py](../config/wsgi.py) | Structural + selected trace | 6 | 16 / 0 |

## scripts

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [scripts/ai_review.py](../scripts/ai_review.py) | Assigned script + syntax | 6 | — |
| [scripts/company_probe_plan.py](../scripts/company_probe_plan.py) | Assigned script + syntax | 6 | — |
| [scripts/dev.py](../scripts/dev.py) | Assigned script + syntax | 6 | — |
| [scripts/digitalocean_runtime.py](../scripts/digitalocean_runtime.py) | Assigned script + syntax | 6 | — |
| [scripts/install_tour_validators.py](../scripts/install_tour_validators.py) | Assigned script + syntax | 6 | — |
| [scripts/run_api.py](../scripts/run_api.py) | Assigned script + syntax | 6 | — |
| [scripts/run_local_recovery_drill.py](../scripts/run_local_recovery_drill.py) | Assigned script + syntax | 6 | — |

## tools

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [tools/chat_policy/evaluate_synthetic.py](../tools/chat_policy/evaluate_synthetic.py) | application/support; syntax/support | Supporting scope | — |
| [tools/chat_policy/independent_review.py](../tools/chat_policy/independent_review.py) | application/support; syntax/support | Supporting scope | — |
| [tools/chat_policy/synthetic_media.py](../tools/chat_policy/synthetic_media.py) | application/support; syntax/support | Supporting scope | — |
| [tools/chat_policy/verify_deployed_acceptance.py](../tools/chat_policy/verify_deployed_acceptance.py) | application/support; syntax/support | Supporting scope | — |
| [tools/export_rental_lifecycle_contract.py](../tools/export_rental_lifecycle_contract.py) | application/support; syntax/support | Supporting scope | — |
| [tools/qa/mvp_collection.py](../tools/qa/mvp_collection.py) | application/support; syntax/support | Supporting scope | — |
| [tools/qa/prepare_mvp_http_fixture.py](../tools/qa/prepare_mvp_http_fixture.py) | application/support; syntax/support | Supporting scope | — |
| [tools/qa/verify_chat_network.py](../tools/qa/verify_chat_network.py) | application/support; syntax/support | Supporting scope | — |
| [tools/qa/verify_cycle_workers.py](../tools/qa/verify_cycle_workers.py) | application/support; syntax/support | Supporting scope | — |
| [tools/run_mvp_scope_tests.py](../tools/run_mvp_scope_tests.py) | application/support; syntax/support | Supporting scope | — |
| [tools/virtual_tours/capture_dev_postgres.py](../tools/virtual_tours/capture_dev_postgres.py) | application/support; syntax/support | Supporting scope | — |
| [tools/virtual_tours/generate_calibration.py](../tools/virtual_tours/generate_calibration.py) | application/support; syntax/support | Supporting scope | — |
| [tools/virtual_tours/reconstruction/__init__.py](../tools/virtual_tours/reconstruction/__init__.py) | application/support; syntax/support | Supporting scope | — |
| [tools/virtual_tours/reconstruction/gaussian.py](../tools/virtual_tours/reconstruction/gaussian.py) | application/support; syntax/support | Supporting scope | — |
| [tools/virtual_tours/reconstruction/geometry.py](../tools/virtual_tours/reconstruction/geometry.py) | application/support; syntax/support | Supporting scope | — |
| [tools/virtual_tours/reconstruction/run.py](../tools/virtual_tours/reconstruction/run.py) | application/support; syntax/support | Supporting scope | — |
| [tools/virtual_tours/reconstruction/sfm.py](../tools/virtual_tours/reconstruction/sfm.py) | application/support; syntax/support | Supporting scope | — |

## other

| File | Scan | Area | Lines / functions |
|---|---|---|---|
| [conftest.py](../conftest.py) | application/support; syntax/support | Supporting scope | — |
| [manage.py](../manage.py) | application/support; syntax/support | Supporting scope | — |

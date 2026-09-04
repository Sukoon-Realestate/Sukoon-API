import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const UserModel tenant = UserModel(
    id: 1,
    name: 'محمد أحمد',
    phone: '01012345432',
    email: 'm.ahmed@email.com',
    type: 'tenant',
  );
  const UserModel owner = UserModel(
    id: 2,
    name: 'أحمد محمد',
    phone: '01112345876',
    email: 'a.mohamed@email.com',
    type: 'owner',
  );

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, (call) async {
          return call.method == 'getAll' ? <String, Object>{} : true;
        });
    await EasyLocalization.ensureInitialized();
  });

  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(sharedPreferencesChannel, null);
  });

  Widget buildScreen(Widget screen) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar')],
      path: 'unused',
      assetLoader: const _ProfileTranslationsAssetLoader(),
      startLocale: const Locale('ar'),
      fallbackLocale: const Locale('ar'),
      child: ScreenUtilInit(
        designSize: Size(ScreenSizes.width, ScreenSizes.height),
        builder: (context, _) {
          return MaterialApp(
            navigatorKey: Go.navigatorKey,
            localizationsDelegates: context.localizationDelegates,
            supportedLocales: context.supportedLocales,
            locale: context.locale,
            home: screen,
          );
        },
      ),
    );
  }

  void configurePhoneViewport(WidgetTester tester) {
    tester.view.physicalSize = const Size(390, 844);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
  }

  testWidgets('renders T-PROFILE-01 and opens T-SUMMARY-01', (tester) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(
      buildScreen(const TenantProfileScreen(user: tenant)),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('T-PROFILE-01')), findsOneWidget);
    expect(find.text(tenant.name), findsWidgets);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byKey(const ValueKey('tenant-profile-summary')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('T-SUMMARY-01')), findsOneWidget);
    expect(find.text(tenant.name), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('renders O-MORE-01 and opens O-PROFILE-01', (tester) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(buildScreen(const OwnerMoreScreen(user: owner)));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('O-MORE-01')), findsOneWidget);
    expect(find.text(owner.name), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byKey(const ValueKey('owner-more-profile-header')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('O-PROFILE-01')), findsOneWidget);
    expect(find.text(owner.name), findsWidgets);
    expect(tester.takeException(), isNull);
  });

  testWidgets('T-EDIT-01 prefills registration fields from initialValue', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(
      buildScreen(const TenantEditProfileScreen(initialValue: tenant)),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('T-EDIT-01')), findsOneWidget);
    _expectPrefilledFields(tester, tenant);
    expect(tester.takeException(), isNull);
  });

  testWidgets('O-EDIT-P-01 prefills registration fields from initialValue', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(
      buildScreen(const OwnerEditProfileScreen(initialValue: owner)),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('O-EDIT-P-01')), findsOneWidget);
    _expectPrefilledFields(tester, owner);
    expect(tester.takeException(), isNull);
  });
}

void _expectPrefilledFields(WidgetTester tester, UserModel user) {
  final SokoonNameField nameField = tester.widget(
    find.byKey(const ValueKey('profile-name-field')),
  );
  final SokoonPhoneField phoneField = tester.widget(
    find.byKey(const ValueKey('profile-phone-field')),
  );
  final SokoonEmailField emailField = tester.widget(
    find.byKey(const ValueKey('profile-email-field')),
  );

  expect(nameField.controller.text, user.name);
  expect(phoneField.controller.text, user.phone);
  expect(emailField.controller.text, user.email);
}

class _ProfileTranslationsAssetLoader extends AssetLoader {
  const _ProfileTranslationsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    const List<String> keys = [
      'profile_my_account',
      'profile_owner_title',
      'profile_summary_title',
      'profile_tenant_member_since',
      'profile_tenant_summary_member_since',
      'profile_owner_member_since',
      'profile_verified_owner',
      'profile_fallback_name',
      'profile_saved',
      'profile_visits',
      'profile_reviews',
      'profile_properties',
      'profile_acceptance',
      'profile_visit_requests',
      'profile_visit_requests_count',
      'profile_contracts',
      'profile_active_contract_count',
      'profile_my_reviews',
      'profile_reviews_count',
      'profile_verification_and_privacy',
      'profile_account_data',
      'profile_mobile',
      'profile_logout',
      'profile_completion',
      'profile_identity_verified',
      'profile_identity_verified_description',
      'profile_saved_properties',
      'profile_completed_visits',
      'profile_active_chats',
      'profile_visit_history',
      'profile_identity_verification',
      'profile_complete_status',
      'profile_owner_rating_summary',
      'profile_owner_phone_privacy',
      'profile_latest_reviews',
      'profile_review_sara_name',
      'profile_review_sara_text',
      'profile_review_mohamed_name',
      'profile_review_mohamed_text',
      'profile_view_personal_profile',
      'profile_account_and_profile',
      'profile_my_profile',
      'profile_verification_documents',
      'profile_privacy_security',
      'profile_property_management',
      'profile_analytics_statistics',
      'profile_visit_schedule',
      'profile_support',
      'profile_help_center',
      'profile_terms_policies',
      'profile_tenant_edit_title',
      'profile_owner_edit_title',
      'profile_save',
      'profile_change_photo',
      'profile_birth_date',
      'profile_male',
      'profile_cairo',
      'profile_verified_account',
      'profile_verified_account_description',
      'name',
      'email',
      'verified',
      'not_set_yet',
      'full_name',
      'full_name_hint',
      'phone_number',
      'city',
      'gender',
      'owner_properties_title',
    ];
    return {for (final String key in keys) key: 'نص'};
  }
}

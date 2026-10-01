import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/shared_widgets/shared_widgets.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  const UserModel tenant = UserModel(
    id: '1',
    name: 'محمد أحمد',
    phone: '01012345432',
    email: 'm.ahmed@email.com',
    type: 'tenant',
  );
  const UserModel owner = UserModel(
    id: '2',
    name: 'أحمد محمد',
    phone: '01112345876',
    email: 'a.mohamed@email.com',
    type: 'owner',
  );

  const MethodChannel sharedPreferencesChannel = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  late _ProfileRepository repository;

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

  setUp(() async {
    await injector.reset();
    repository = _ProfileRepository();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: repository),
    );
  });

  tearDown(() => injector.reset());

  Widget buildScreen(Widget screen) {
    return EasyLocalization(
      supportedLocales: const [Locale('ar'), Locale('en')],
      path: 'unused',
      assetLoader: const _ProfileTranslationsAssetLoader(),
      startLocale: const Locale('ar'),
      fallbackLocale: const Locale('ar'),
      saveLocale: false,
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

  for (final screen in <Widget>[
    const TenantProfileScreen(user: tenant),
    const OwnerProfileScreen(user: owner),
    const TenantAccountSummaryScreen(),
  ]) {
    testWidgets('${screen.runtimeType} reloads its data on pull-down', (
      tester,
    ) async {
      configurePhoneViewport(tester);
      await tester.pumpWidget(buildScreen(screen));
      await tester.pumpAndSettle();
      final int initialRequests = repository.requestCount;
      final String endpoint = repository.lastApi;

      await tester.drag(find.byType(Scrollable).first, const Offset(0, 350));
      await tester.pumpAndSettle();

      expect(repository.requestCount, initialRequests + 1);
      expect(repository.lastApi, endpoint);
      expect(tester.takeException(), isNull);
    });
  }

  test('maps and serializes the owner profile response', () {
    final OwnerProfileContent profile = OwnerProfileContent.fromJson(
      _ownerProfileResponse,
    );

    expect(profile.owner.fullName, 'Zeayd Mohammed');
    expect(profile.owner.isVerified, isFalse);
    expect(profile.stats.propertiesCount, 2);
    expect(profile.stats.displayAcceptanceRate, '96%');
    expect(profile.accountDetails.displayPhone, '010****972');
    expect(profile.privacyNotice.icon, 'lock');
    expect(profile.recentReviews, isEmpty);
    expect(OwnerProfileContent.fromJson(profile.toJson()), profile);
  });

  test('maps and serializes the tenant profile response', () {
    final TenantProfileContent profile = TenantProfileContent.fromJson(
      _tenantProfileResponse,
    );

    expect(profile.user.fullName, 'Zeayd Mohammed');
    expect(profile.user.roleLabel, 'مستأجر');
    expect(profile.stats.visitsCount, 2);
    expect(profile.menuItems.contracts.count, 1);
    expect(profile.menuItems.verification.isVerified, isFalse);
    expect(profile.accountDetails.email, 'zeyaddd@gmail.com');
    expect(TenantProfileContent.fromJson(profile.toJson()), profile);
  });

  test('maps and serializes the tenant account summary response', () {
    final TenantAccountSummaryContent summary =
        TenantAccountSummaryContent.fromJson(_tenantAccountSummaryResponse);

    expect(summary.user.fullName, 'Zeayd Mohammed');
    expect(summary.user.initial, 'Z');
    expect(summary.user.profileCompletionPercentage, 55);
    expect(summary.identityVerification.isVerified, isFalse);
    expect(summary.identityVerification.statusLabel, 'غير مكتمل');
    expect(summary.stats.completedVisitsCount, 2);
    expect(summary.shortcuts.savedProperties.label, '0 عقار');
    expect(summary.shortcuts.identityVerification.status, 'incomplete');
    expect(TenantAccountSummaryContent.fromJson(summary.toJson()), summary);
  });

  test('loads profile screens from their GET endpoints', () async {
    final OwnerProfileCubit ownerCubit = OwnerProfileCubit();
    final TenantProfileCubit tenantCubit = TenantProfileCubit();
    final TenantAccountSummaryCubit summaryCubit = TenantAccountSummaryCubit();
    addTearDown(ownerCubit.close);
    addTearDown(tenantCubit.close);
    addTearDown(summaryCubit.close);

    await ownerCubit.getProfile();
    expect(repository.lastApi, ApiConstants.ownerProfile);
    expect(repository.lastMethod, HttpRequestType.get);
    expect(repository.lastCacheKey, OwnerProfileContent.cacheKey);
    expect(ownerCubit.data.owner.fullName, 'Zeayd Mohammed');

    await tenantCubit.getProfile();
    expect(repository.lastApi, ApiConstants.getAccData);
    expect(repository.lastMethod, HttpRequestType.get);
    expect(repository.lastCacheKey, TenantProfileContent.cacheKey);
    expect(tenantCubit.data.stats.visitsCount, 2);

    await summaryCubit.getSummary();
    expect(repository.lastApi, ApiConstants.tenantAccountSummary);
    expect(repository.lastApi, 'profiles/account-summary/');
    expect(repository.lastMethod, HttpRequestType.get);
    expect(repository.lastCacheKey, TenantAccountSummaryContent.cacheKey);
    expect(summaryCubit.data.user.profileCompletionPercentage, 55);
  });

  test('serializes the typed profile edit multipart body', () {
    final File avatar = File('/tmp/profile-avatar.jpg');
    final ProfileEditBody body = ProfileEditBody(
      avatar: avatar,
      fullName: 'Zeayd Mohammed',
      gender: ProfileGender.male.apiValue,
      phoneNumber: '01017595972',
    );

    expect(body.toJson(), {
      'avatar': avatar,
      'full_name': 'Zeayd Mohammed',
      'gender': 'male',
      'phone_number': '01017595972',
    });
    expect(
      const ProfileEditBody.initial().copyWith(fullName: 'Updated').toJson(),
      {'full_name': 'Updated', 'gender': '', 'phone_number': ''},
    );
  });

  test('patches the shared owner and tenant profile edit endpoint', () async {
    final ProfileEditCubit cubit = ProfileEditCubit();
    addTearDown(cubit.close);
    bool wasUpdated = false;
    const ProfileEditBody body = ProfileEditBody(
      avatar: null,
      fullName: 'Updated Name',
      gender: 'female',
      phoneNumber: '01012345678',
    );

    await cubit.editProfile(body: body, onSuccess: () => wasUpdated = true);

    expect(repository.lastApi, ApiConstants.editProfile);
    expect(repository.lastApi, 'profiles/edit/');
    expect(repository.lastMethod, HttpRequestType.patch);
    expect(repository.lastBody, body.toJson());
    expect(repository.lastIsFromData, isTrue);
    expect(wasUpdated, isTrue);
  });

  test('deletes the account through the shared auth endpoint', () async {
    final ProfileDeleteAccountCubit cubit = ProfileDeleteAccountCubit();
    addTearDown(cubit.close);
    bool wasDeleted = false;

    await cubit.deleteAccount(onSuccess: () => wasDeleted = true);

    expect(repository.lastApi, ApiConstants.deleteAccount);
    expect(repository.lastApi, 'auth/delete-account/');
    expect(repository.lastMethod, HttpRequestType.delete);
    expect(repository.lastCacheKey, isNull);
    expect(wasDeleted, isTrue);
  });

  testWidgets('asks for confirmation before deleting an account', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(
      buildScreen(const Scaffold(body: ProfileDeleteAccountButton())),
    );
    await tester.pumpAndSettle();

    expect(find.byType(ProfileDeleteAccountButton), findsOneWidget);
    await tester.tap(find.byType(ProfileDeleteAccountButton));
    await tester.pumpAndSettle();

    expect(find.byType(FilledButton), findsOneWidget);
    expect(find.byType(TextButton), findsOneWidget);
    await tester.tap(find.byType(TextButton));
    await tester.pumpAndSettle();

    expect(repository.lastApi, isEmpty);
    expect(tester.takeException(), isNull);
  });

  testWidgets('renders T-PROFILE-01 and opens T-SUMMARY-01', (tester) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(
      buildScreen(const TenantProfileScreen(user: tenant)),
    );
    await tester.pumpAndSettle();

    expect(find.byType(TenantProfileScreen), findsOneWidget);
    expect(find.text('Zeayd Mohammed'), findsWidgets);
    expect(find.text('2'), findsWidgets);
    await tester.drag(find.byType(ListView).last, const Offset(0, -900));
    await tester.pumpAndSettle();
    expect(find.byType(ProfileDeleteAccountButton), findsOneWidget);
    expect(repository.lastApi, ApiConstants.getAccData);
    expect(repository.lastMethod, HttpRequestType.get);
    expect(tester.takeException(), isNull);

    await tester.tap(find.widgetWithIcon(IconButton, Icons.settings_outlined));
    await tester.pumpAndSettle();

    expect(find.byType(TenantAccountSummaryScreen), findsOneWidget);
    expect(find.text('Zeayd Mohammed'), findsOneWidget);
    expect(find.text('55%'), findsOneWidget);
    expect(find.text('غير مكتمل'), findsWidgets);
    expect(find.text('0 عقار'), findsOneWidget);
    expect(find.text('2 زيارة'), findsOneWidget);
    expect(repository.lastApi, ApiConstants.tenantAccountSummary);
    expect(repository.lastMethod, HttpRequestType.get);
    expect(tester.takeException(), isNull);
  });

  testWidgets('renders O-MORE-01 and opens O-PROFILE-01', (tester) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(buildScreen(const OwnerMoreScreen(user: owner)));
    await tester.pumpAndSettle();

    expect(find.byType(OwnerMoreScreen), findsOneWidget);
    expect(find.text(owner.name), findsOneWidget);
    expect(tester.takeException(), isNull);

    await tester.tap(
      find.ancestor(of: find.text(owner.name), matching: find.byType(InkWell)),
    );
    await tester.pumpAndSettle();

    expect(find.byType(OwnerProfileScreen), findsOneWidget);
    expect(find.text('Zeayd Mohammed'), findsWidgets);
    expect(find.text('96%'), findsOneWidget);
    expect(find.text('010****972'), findsOneWidget);
    await tester.drag(find.byType(ListView).last, const Offset(0, -900));
    await tester.pumpAndSettle();
    expect(find.byType(ProfileDeleteAccountButton), findsOneWidget);
    expect(repository.lastApi, ApiConstants.ownerProfile);
    expect(repository.lastMethod, HttpRequestType.get);
    expect(tester.takeException(), isNull);
  });

  for (final bool isOwner in [false, true]) {
    testWidgets('${isOwner ? 'owner' : 'tenant'} profile changes language', (
      tester,
    ) async {
      configurePhoneViewport(tester);
      await tester.pumpWidget(
        buildScreen(
          isOwner
              ? const OwnerMoreScreen(user: owner)
              : const TenantProfileScreen(user: tenant),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.language_rounded));
      await tester.pumpAndSettle();
      expect(find.byType(LanguageSelectionScreen), findsOneWidget);
      await tester.tap(find.text('English'));
      await tester.pump();
      await tester.tap(find.text('تأكيد'));
      await tester.pumpAndSettle();

      expect(find.byType(LanguageSelectionScreen), findsNothing);
      expect(Go.context.locale, const Locale('en'));
      expect(find.text('Change language'), findsOneWidget);
      expect(
        find.text(
          isOwner
              ? 'English profile_account_and_profile'
              : 'English profile_my_account',
        ),
        findsOneWidget,
      );
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('T-EDIT-01 loads the editable profile from the server', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    repository.editableUser = tenant;
    await tester.pumpWidget(
      buildScreen(const TenantEditProfileScreen(initialValue: tenant)),
    );
    await tester.pumpAndSettle();

    expect(find.byType(TenantEditProfileScreen), findsOneWidget);
    _expectPrefilledFields(tester, tenant);
    expect(repository.lastApi, ApiConstants.userProfile);
    expect(tester.takeException(), isNull);
  });

  testWidgets('O-EDIT-P-01 loads the editable profile from the server', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    repository.editableUser = owner;
    await tester.pumpWidget(
      buildScreen(const OwnerEditProfileScreen(initialValue: owner)),
    );
    await tester.pumpAndSettle();

    expect(find.byType(OwnerEditProfileScreen), findsOneWidget);
    _expectPrefilledFields(tester, owner);
    expect(repository.lastApi, ApiConstants.userProfile);
    expect(tester.takeException(), isNull);
  });
}

const Map<String, dynamic> _ownerProfileResponse = {
  'owner': {
    'id': '803447a0-cfcf-49bd-b9d3-d0effe1fb4f8',
    'full_name': 'Zeayd Mohammed',
    'avatar': null,
    'is_verified': false,
    'role_badge': 'مالك',
    'average_rating': 0,
    'reviews_count': 0,
    'rating_label': '0.0 (0 تقييم)',
    'member_since_label': 'عضو منذ أغسطس 2026',
  },
  'stats': {
    'properties_count': 2,
    'properties_label': 'عقارات',
    'reviews_count': 0,
    'reviews_label': 'تقييم',
    'acceptance_rate': 96,
    'acceptance_label': 'قبول',
    'formatted_acceptance_rate': '96%',
  },
  'account_details': {
    'name': 'Zeayd Mohammed',
    'email': 'zeyaddd@gmail.com',
    'phone_number': '01017595972',
    'masked_phone_number': '010****972',
  },
  'privacy_notice': {
    'icon': 'lock',
    'text': 'رقمك لا يُعرض للمستأجرين – يظهر فقط بعد القبول',
  },
  'recent_reviews': <Map<String, dynamic>>[],
};

const Map<String, dynamic> _tenantProfileResponse = {
  'user': {
    'id': '803447a0-cfcf-49bd-b9d3-d0effe1fb4f8',
    'full_name': 'Zeayd Mohammed',
    'first_name': 'Zeayd',
    'last_name': 'Mohammed',
    'avatar': null,
    'is_verified': false,
    'verification_badge': 'غير موثّق',
    'role_label': 'مستأجر',
    'member_since_label': 'عضو منذ أغسطس 2026',
    'member_since_year': 2026,
    'member_since_month': 'أغسطس',
  },
  'stats': {'saved_count': 0, 'visits_count': 2, 'reviews_count': 0},
  'menu_items': {
    'visit_requests': {
      'title': 'طلبات الزيارة',
      'count': 2,
      'subtitle': '2 طلب',
    },
    'contracts': {'title': 'عقودي', 'count': 1, 'subtitle': '1 عقد نشط'},
    'reviews': {'title': 'تقييماتي', 'count': 0, 'subtitle': '0 تقييم'},
    'verification': {
      'title': 'التوثيق والخصوصية',
      'is_verified': false,
      'subtitle': 'غير موثّق',
    },
  },
  'account_details': {'name': 'Zeayd Mohammed', 'email': 'zeyaddd@gmail.com'},
};

const Map<String, dynamic> _tenantAccountSummaryResponse = {
  'user': {
    'id': '803447a0-cfcf-49bd-b9d3-d0effe1fb4f8',
    'full_name': 'Zeayd Mohammed',
    'avatar': null,
    'initial': 'Z',
    'role_label': 'مستأجر',
    'member_since_label': 'منذ أغسطس 2026',
    'profile_completion_percentage': 55,
    'profile_completion_label': 'اكتمال الملف',
  },
  'identity_verification': {
    'is_verified': false,
    'title': 'التحقق من الهوية',
    'subtitle': 'يرجى رفع بطاقة الهوية للتحقق',
    'status_label': 'غير مكتمل',
  },
  'stats': {
    'saved_properties_count': 0,
    'completed_visits_count': 2,
    'active_chats_count': 0,
  },
  'shortcuts': {
    'saved_properties': {
      'title': 'العقارات المحفوظة',
      'count': 0,
      'label': '0 عقار',
    },
    'visits_history': {'title': 'سجل الزيارات', 'count': 2, 'label': '2 زيارة'},
    'identity_verification': {
      'title': 'التحقق من الهوية',
      'status': 'incomplete',
      'label': 'غير مكتمل',
    },
  },
};

class _ProfileRepository implements BaseRepository {
  int requestCount = 0;
  UserModel? editableUser;
  String lastApi = '';
  HttpRequestType? lastMethod;
  String? lastCacheKey;
  Map<String, dynamic>? lastBody;
  bool lastIsFromData = false;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    requestCount++;
    lastApi = params.api;
    lastMethod = params.httpRequestType;
    lastCacheKey = params.cacheKey;
    lastBody = params.body;
    lastIsFromData = params.isFromData;
    final dynamic response = switch (params.api) {
      ApiConstants.userProfile => {
        'id': editableUser?.id,
        'full_name': editableUser?.name,
        'phone_number': editableUser?.phone,
        'gender': 'male',
        'birth_date': '1990-01-15',
      },
      ApiConstants.ownerProfile => _ownerProfileResponse,
      ApiConstants.getAccData => _tenantProfileResponse,
      ApiConstants.tenantAccountSummary => _tenantAccountSummaryResponse,
      ApiConstants.editProfile => const <String, dynamic>{'updated': true},
      ApiConstants.deleteAccount => const <String, dynamic>{'deleted': true},
      _ => null,
    };
    final T data = params.mapper!(response);
    return Success(BaseModel<T>(key: '', msg: '', data: data));
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => throw UnimplementedError();
}

void _expectPrefilledFields(WidgetTester tester, UserModel user) {
  final SokoonNameField nameField = tester.widget(find.byType(SokoonNameField));
  final SokoonPhoneField phoneField = tester.widget(
    find.byType(SokoonPhoneField),
  );
  final SokoonEmailField emailField = tester.widget(
    find.byType(SokoonEmailField),
  );

  expect(nameField.controller.text, user.name);
  expect(phoneField.controller.text, user.phone);
  expect(emailField.controller.text, user.email);
  expect(emailField.readOnly, isTrue);
  expect(find.byType(FormField<ProfileGender>), findsOneWidget);
}

class _ProfileTranslationsAssetLoader extends AssetLoader {
  const _ProfileTranslationsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async {
    const List<String> keys = [
      'change_language',
      'language_selection_title',
      'language_selection_subtitle',
      'language_arabic_name',
      'language_arabic_translation',
      'language_english_native_name',
      'language_english_translation',
      'confirm',
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
      'profile_no_reviews_title',
      'profile_no_reviews_description',
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
      'profile_female',
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
      'delete_account',
      'are_you_sure_you_want_to_delete_your_account',
      'deleting_will_remove_all_your_data',
      'cancel',
    ];
    return {
      for (final String key in keys)
        key: locale.languageCode == 'ar' ? 'نص' : 'English $key',
      'language_english_native_name': 'English',
      'confirm': locale.languageCode == 'ar' ? 'تأكيد' : 'Confirm',
      'change_language': locale.languageCode == 'ar'
          ? 'تغيير اللغة'
          : 'Change language',
    };
  }
}

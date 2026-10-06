import 'dart:async';
import 'dart:convert';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'helpers/account_test_dependencies.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/account_cubit.dart';
import 'dart:io';

import 'package:easy_localization/easy_localization.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
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
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
          (_) async => null,
        );
    await EasyLocalization.ensureInitialized();
    await CacheStorage.init();
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
    await registerAuthenticatedTestAccount(user: tenant);
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
    final AccountContent profile = AccountContent.fromJson(
      _tenantProfileResponse,
    );

    expect(profile.user.fullName, 'Zeayd Mohammed');
    expect(profile.user.roleLabel, 'مستأجر');
    expect(profile.stats.visitsCount, 2);
    expect(profile.menuItems.contracts.count, 1);
    expect(profile.menuItems.verification.isVerified, isFalse);
    expect(profile.accountDetails.email, 'zeyaddd@gmail.com');
    expect(AccountContent.fromJson(profile.toJson()), profile);
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
    final AccountCubit tenantCubit = AccountCubit();
    final TenantAccountSummaryCubit summaryCubit = TenantAccountSummaryCubit();
    addTearDown(ownerCubit.close);
    addTearDown(tenantCubit.close);
    addTearDown(summaryCubit.close);

    await ownerCubit.getProfile();
    expect(repository.lastApi, ApiConstants.ownerProfile);
    expect(repository.lastMethod, HttpRequestType.get);
    expect(repository.lastCacheKey, OwnerProfileContent.cacheKey);
    expect(ownerCubit.data.owner.fullName, 'Zeayd Mohammed');

    await tenantCubit.getAccount();
    expect(repository.lastApi, ApiConstants.getAccData);
    expect(repository.lastMethod, HttpRequestType.get);
    expect(repository.lastCacheKey, AccountContent.cacheKey);
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

  test('profile metadata does not erase known account identity', () {
    final UserModel fromEmpty = const UserProfileContent.initial().toUser(
      tenant,
    );
    expect(fromEmpty.toJson(), tenant.toJson());
    final UserModel fromPartial = UserProfileContent.fromJson({
      'first_name': 'Updated',
      'last_name': 'Account',
      'email': 'updated@example.com',
    }).toUser(tenant);
    expect(fromPartial.name, 'Updated Account');
    expect(fromPartial.phone, tenant.phone);
    expect(fromPartial.email, 'updated@example.com');
    expect(fromPartial.id, tenant.id);
  });

  test('profile PATCH omits unknown gender without clearing it', () {
    final ProfileEditBody body = const ProfileEditBody.initial().copyWith(
      fullName: 'Updated Account',
      phoneNumber: tenant.phone,
      updateGender: false,
    );
    expect(body.toJson(), {
      'full_name': 'Updated Account',
      'phone_number': tenant.phone,
    });
    expect(body.toUserJson(), {
      'first_name': 'Updated',
      'last_name': 'Account',
      'phone_number': tenant.phone,
    });
    expect(
      body.copyWith(gender: 'female', updateGender: true).toJson(),
      containsPair('gender', 'female'),
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

    expect(find.byType(ProfileDeleteAccountScreen), findsOneWidget);
    expect(
      tester.widget<CheckboxListTile>(find.byType(CheckboxListTile)).value,
      isFalse,
    );
    Go.back();
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
    expect(find.byType(ProfileDeleteAccountButton), findsNothing);
    expect(repository.lastApi, ApiConstants.getAccData);
    expect(repository.lastMethod, HttpRequestType.get);
    expect(tester.takeException(), isNull);

    await tester.tap(find.byIcon(Icons.account_circle_outlined));
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

  testWidgets('owner Profile opens directly with identity and revenue', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(
      buildScreen(
        const ProfileScreen(workspace: AppWorkspace.owner, user: owner),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(OwnerProfileScreen), findsOneWidget);
    expect(find.byType(ProfileScreen), findsOneWidget);
    expect(find.text('الملف الشخصي'), findsOneWidget);
    expect(find.byIcon(Icons.settings_outlined), findsOneWidget);
    expect(find.byIcon(Icons.support_agent_rounded), findsOneWidget);
    expect(find.text('Zeayd Mohammed'), findsWidgets);
    expect(find.text('96%'), findsOneWidget);
    expect(find.text('010****972'), findsOneWidget);
    await tester.drag(find.byType(ListView).last, const Offset(0, -900));
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.account_balance_wallet_outlined), findsOneWidget);
    expect(find.byType(ProfileDeleteAccountButton), findsNothing);
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
          ProfileScreen(
            workspace: isOwner ? AppWorkspace.owner : AppWorkspace.tenant,
            user: isOwner ? owner : tenant,
          ),
        ),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.byIcon(Icons.settings_outlined));
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
      expect(find.text(LocaleKeys.changeLanguage), findsOneWidget);
      expect(find.byType(ProfileSettingsScreen), findsOneWidget);
      Go.back();
      await tester.pumpAndSettle();
      expect(find.text('Profile'), findsOneWidget);
      expect(find.text('Edit profile'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('T-EDIT-01 loads the editable profile from the server', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    final UserModel serverUser = tenant.copyWith(name: 'Updated server name');
    repository.editableUser = serverUser;
    await tester.pumpWidget(
      buildScreen(
        const ProfileEditScreen(
          initialValue: tenant,
          workspace: AppWorkspace.tenant,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(ProfileEditScreen), findsOneWidget);
    _expectPrefilledFields(tester, serverUser);
    expect(
      tester.widget<ProfileAvatar>(find.byType(ProfileAvatar)).name,
      serverUser.name,
    );
    expect(repository.lastApi, ApiConstants.userProfile);
    expect(tester.takeException(), isNull);
  });

  testWidgets('O-EDIT-P-01 loads the editable profile from the server', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    repository.editableUser = owner;
    await tester.pumpWidget(
      buildScreen(
        const ProfileEditScreen(
          initialValue: owner,
          workspace: AppWorkspace.owner,
        ),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(ProfileEditScreen), findsOneWidget);
    _expectPrefilledFields(tester, owner);
    expect(repository.lastApi, ApiConstants.userProfile);
    expect(tester.takeException(), isNull);
  });

  for (final workspace in AppWorkspace.values) {
    testWidgets(
      '${workspace.name} saving changed gender blocks duplicate submissions',
      (tester) async {
        configurePhoneViewport(tester);
        repository.editableUser = tenant;
        await tester.pumpWidget(
          buildScreen(ProfileScreen(workspace: workspace, user: tenant)),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.profileEditAction));
        await tester.pumpAndSettle();
        final gender = find.byType(FormField<ProfileGender>);
        await tester.ensureVisible(gender);
        await tester.pumpAndSettle();
        await tester.tap(
          find.descendant(of: gender, matching: find.byType(InkWell)).first,
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.profileFemale));
        await tester.pumpAndSettle();
        final pending = Completer<void>();
        repository.profileWriteGate = pending;
        await tester.ensureVisible(find.byType(SokoonNameField));
        await tester.pumpAndSettle();
        await tester.enterText(
          find.descendant(
            of: find.byType(SokoonNameField),
            matching: find.byType(TextFormField),
          ),
          'Submitted account draft',
        );
        await tester.tap(find.text(LocaleKeys.profileSave));
        await tester.pump();
        expect(repository.profileWriteCount, 1);
        expect(repository.lastWriteBody, {
          'full_name': 'Submitted account draft',
          'phone_number': tenant.phone,
          'gender': 'female',
        });
        expect(
          tester
              .widget<EditableText>(
                find.descendant(
                  of: find.byType(SokoonNameField),
                  matching: find.byType(EditableText),
                ),
              )
              .focusNode
              .hasFocus,
          isFalse,
        );
        expect(
          tester
              .widget<AbsorbPointer>(
                find.descendant(
                  of: find.byType(ProfileEditView),
                  matching: find.byType(AbsorbPointer),
                ),
              )
              .absorbing,
          isTrue,
        );
        final save = find.descendant(
          of: find.byType(AppBar),
          matching: find.byType(TextButton),
        );
        await tester.tap(save, warnIfMissed: false);
        await tester.pump();
        expect(repository.profileWriteCount, 1);
        pending.complete();
        await tester.pumpAndSettle();
        expect(find.byType(ProfileEditScreen), findsNothing);
        expect(find.text('Submitted account draft'), findsWidgets);
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets(
      '${workspace.name} editor can go back while details are pending',
      (tester) async {
        configurePhoneViewport(tester);
        final pending = Completer<void>();
        repository.editableReadGate = pending;
        repository.editableUser = tenant;
        await tester.pumpWidget(
          buildScreen(ProfileScreen(workspace: workspace, user: tenant)),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.profileEditAction));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 600));
        final editor = tester.widget<ProfileEditScreen>(
          find.byType(ProfileEditScreen),
        );
        _expectPrefilledFields(tester, editor.initialValue, hasMetadata: false);
        expect(find.byType(SokoonBackButton), findsOneWidget);
        expect(find.text(LocaleKeys.profileEditLoadingDetails), findsOneWidget);
        expect(find.byType(ProfileCitySelector), findsNothing);
        await tester.tap(find.byType(SokoonBackButton));
        await tester.pumpAndSettle();
        expect(find.byType(ProfileEditScreen), findsNothing);
        expect(find.byType(ProfileScreen), findsOneWidget);
        pending.complete();
        await tester.pumpAndSettle();
        expect(repository.lastWriteBody, isNull);
        expect(tester.takeException(), isNull);
      },
    );

    testWidgets(
      '${workspace.name} delayed details preserve name and phone drafts',
      (tester) async {
        configurePhoneViewport(tester);
        final pending = Completer<void>();
        repository.editableReadGate = pending;
        repository.editableUser = tenant;
        await tester.pumpWidget(
          buildScreen(ProfileScreen(workspace: workspace, user: tenant)),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.profileEditAction));
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 600));
        await tester.enterText(
          find.descendant(
            of: find.byType(SokoonNameField),
            matching: find.byType(TextFormField),
          ),
          'Delayed account draft',
        );
        await tester.enterText(
          find.descendant(
            of: find.byType(SokoonPhoneField),
            matching: find.byType(TextFormField),
          ),
          '01055556789',
        );
        final String draftPhone = tester
            .widget<SokoonPhoneField>(find.byType(SokoonPhoneField))
            .controller
            .text;
        await tester.tap(find.text(LocaleKeys.profileSave));
        await tester.pump();
        expect(repository.lastWriteBody, isNull);
        pending.complete();
        await tester.pumpAndSettle();
        expect(
          tester
              .widget<SokoonNameField>(find.byType(SokoonNameField))
              .controller
              .text,
          'Delayed account draft',
        );
        expect(
          tester
              .widget<SokoonPhoneField>(find.byType(SokoonPhoneField))
              .controller
              .text,
          draftPhone,
        );
        await tester.tap(find.text(LocaleKeys.profileSave));
        await tester.pumpAndSettle();
        expect(repository.lastWriteBody, {
          'full_name': 'Delayed account draft',
          'phone_number': '+201055556789',
        });
        expect(find.byType(ProfileEditScreen), findsNothing);
        expect(find.text('Delayed account draft'), findsWidgets);
        expect(tester.takeException(), isNull);
      },
    );

    testWidgets(
      '${workspace.name} failed save keeps the draft and allows retry',
      (tester) async {
        configurePhoneViewport(tester);
        repository.editableUser = tenant;
        repository.failProfileWrite = true;
        await tester.pumpWidget(
          buildScreen(ProfileScreen(workspace: workspace, user: tenant)),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.profileEditAction));
        await tester.pumpAndSettle();
        final String originalAccountName = UserModel.currentUser!.name;
        await tester.enterText(
          find.descendant(
            of: find.byType(SokoonNameField),
            matching: find.byType(TextFormField),
          ),
          'Unsaved account draft',
        );
        await tester.tap(find.text(LocaleKeys.profileSave));
        await tester.pumpAndSettle();
        expect(find.byType(ProfileEditScreen), findsOneWidget);
        expect(
          tester
              .widget<SokoonNameField>(find.byType(SokoonNameField))
              .controller
              .text,
          'Unsaved account draft',
        );
        expect(UserModel.currentUser!.name, originalAccountName);
        expect(repository.profileWriteCount, 1);
        repository.failProfileWrite = false;
        await tester.tap(find.text(LocaleKeys.profileSave));
        await tester.pumpAndSettle();
        expect(repository.profileWriteCount, 2);
        expect(find.byType(ProfileEditScreen), findsNothing);
        expect(find.text('Unsaved account draft'), findsWidgets);
        expect(UserModel.currentUser!.name, 'Unsaved account draft');
        expect(tester.takeException(), isNull);
      },
    );

    testWidgets(
      '${workspace.name} edit remains usable when the details GET fails',
      (tester) async {
        configurePhoneViewport(tester);
        repository.failEditableRead = true;
        await tester.pumpWidget(
          buildScreen(ProfileScreen(workspace: workspace, user: tenant)),
        );
        await tester.pumpAndSettle();
        await tester.tap(find.text(LocaleKeys.profileEditAction));
        await tester.pumpAndSettle();
        final editor = tester.widget<ProfileEditScreen>(
          find.byType(ProfileEditScreen),
        );
        expect(find.byType(SokoonNameField), findsOneWidget);
        expect(find.byType(SokoonPhoneField), findsOneWidget);
        expect(find.byType(SokoonBackButton), findsOneWidget);
        expect(
          find.text('Editable profile temporarily unavailable'),
          findsOneWidget,
        );
        expect(
          tester
              .widget<SokoonNameField>(find.byType(SokoonNameField))
              .controller
              .text,
          editor.initialValue.name,
        );
        expect(find.byType(ProfileCitySelector), findsNothing);
        expect(find.byType(FormField<ProfileGender>), findsNothing);

        await tester.enterText(
          find.descendant(
            of: find.byType(SokoonNameField),
            matching: find.byType(TextFormField),
          ),
          'Updated account name',
        );
        await tester.tap(find.text(LocaleKeys.profileSave));
        await tester.pumpAndSettle();
        expect(repository.lastWriteBody, {
          'full_name': 'Updated account name',
          'phone_number': editor.initialValue.phone,
        });
        expect(find.byType(ProfileEditScreen), findsNothing);
        expect(find.byType(ProfileScreen), findsOneWidget);
        expect(find.text('Updated account name'), findsWidgets);
        expect(tester.takeException(), isNull);
      },
    );
    testWidgets('${workspace.name} retrying details preserves an edited name', (
      tester,
    ) async {
      configurePhoneViewport(tester);
      repository.failEditableRead = true;
      repository.editableUser = tenant;
      await tester.pumpWidget(
        buildScreen(ProfileScreen(workspace: workspace, user: tenant)),
      );
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.profileEditAction));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.descendant(
          of: find.byType(SokoonNameField),
          matching: find.byType(TextFormField),
        ),
        'Draft account name',
      );
      repository.failEditableRead = false;
      await tester.tap(find.text(LocaleKeys.ownerRetryAction));
      await tester.pumpAndSettle();
      expect(
        tester
            .widget<SokoonNameField>(find.byType(SokoonNameField))
            .controller
            .text,
        'Draft account name',
      );
      expect(find.byType(ProfileCitySelector), findsOneWidget);
      await tester.tap(find.text(LocaleKeys.profileSave));
      await tester.pumpAndSettle();
      expect(repository.lastWriteBody?['full_name'], 'Draft account name');
      expect(find.byType(ProfileEditScreen), findsNothing);
      expect(find.text('Draft account name'), findsWidgets);
      expect(tester.takeException(), isNull);
    });
  }

  testWidgets('offline details keep the editor scaffold and retry action', (
    tester,
  ) async {
    configurePhoneViewport(tester);
    await tester.pumpWidget(
      buildScreen(
        const ProfileScreen(workspace: AppWorkspace.owner, user: owner),
      ),
    );
    await tester.pumpAndSettle();
    repository.failEditableRead = true;
    repository.editableReadError = LocaleKeys.checkInternet;
    await tester.tap(find.text(LocaleKeys.profileEditAction));
    await tester.pumpAndSettle();
    expect(find.byType(SokoonNameField), findsOneWidget);
    expect(find.byType(SokoonBackButton), findsOneWidget);
    expect(find.text(LocaleKeys.checkInternet), findsOneWidget);
    expect(find.text(LocaleKeys.ownerRetryAction), findsOneWidget);
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
  bool failEditableRead = false;
  String editableReadError = 'Editable profile temporarily unavailable';
  bool failProfileWrite = false;
  int profileWriteCount = 0;
  Completer<void>? editableReadGate;
  Completer<void>? profileWriteGate;
  Map<String, dynamic>? lastWriteBody;
  UserModel? _savedUser;

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
    if (params.api == ApiConstants.userProfile) {
      await editableReadGate?.future;
      if (failEditableRead) {
        return Error(Failure(editableReadError));
      }
    }
    if (params.api == ApiConstants.editProfile) {
      profileWriteCount++;
      lastWriteBody = params.body;
      await profileWriteGate?.future;
      if (failProfileWrite) {
        return const Error(Failure('Profile update failed'));
      }
      _savedUser =
          (editableUser ?? UserModel.currentUser ?? UserModel.initial())
              .copyWith(
                name: params.body?['full_name'],
                phone: params.body?['phone_number'],
              );
      editableUser = _savedUser;
    }
    final dynamic response = switch (params.api) {
      ApiConstants.userProfile => {
        'id': editableUser?.id,
        'full_name': editableUser?.name,
        'phone_number': editableUser?.phone,
        'gender': 'male',
        'birth_date': '1990-01-15',
      },
      ApiConstants.ownerProfile => {
        ..._ownerProfileResponse,
        if (_savedUser != null)
          'owner': {
            ..._ownerProfileResponse['owner'] as Map,
            'full_name': _savedUser!.name,
          },
        if (_savedUser != null)
          'account_details': {
            ..._ownerProfileResponse['account_details'] as Map,
            'name': _savedUser!.name,
            'phone_number': _savedUser!.phone,
          },
      },
      ApiConstants.getAccData => {
        ..._tenantProfileResponse,
        if (_savedUser != null)
          'user': {
            ..._tenantProfileResponse['user'] as Map,
            'full_name': _savedUser!.name,
          },
        if (_savedUser != null)
          'account_details': {
            ..._tenantProfileResponse['account_details'] as Map,
            'name': _savedUser!.name,
            'phone_number': _savedUser!.phone,
          },
      },
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

void _expectPrefilledFields(
  WidgetTester tester,
  UserModel user, {
  bool hasMetadata = true,
}) {
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
  expect(
    find.byType(FormField<ProfileGender>),
    hasMetadata ? findsOneWidget : findsNothing,
  );
}

class _ProfileTranslationsAssetLoader extends AssetLoader {
  const _ProfileTranslationsAssetLoader();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      jsonDecode(
            File(
              '../../packages/core/assets/translations/${locale.languageCode}.json',
            ).readAsStringSync(),
          )
          as Map<String, dynamic>;
}

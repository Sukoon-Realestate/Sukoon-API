import 'dart:async';
import 'dart:convert';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/core/base_crud/code/domain/base_domain_imports.dart';
import 'package:melos_core/core/base_crud/code/domain/usecases/pagination_response.dart';
import 'package:melos_core/core/error/failure.dart';
import 'package:melos_core/core/network/api_endpoints.dart';
import 'package:multiple_result/multiple_result.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/network/network_request.dart';
import 'package:melos_core/core/network/network_service.dart';
import 'package:melos_core/core/shared/models/user_models/user_model.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/data/workspace_preferences.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'package:sokoun_app/features/main_view/presentation/screens/view.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_bottom_navigation.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_home_screen.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/chat_unread_cubit.dart';
import 'package:sokoun_app/features/shared/chat/data/models/chat_unread_content.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/notification_push_handler.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/home/presentation/cubits/home_page_cubit.dart';
import 'package:sokoun_app/shared_widgets/unsaved_changes_guard.dart';

import 'package:melos_core/core/widgets/notification_permission_view.dart';
import 'package:melos_core/core/widgets/permissions/permission_actions.dart';
import 'package:sokoun_app/features/shared/permissions/data/device_permission_data.dart';
import 'package:sokoun_app/features/shared/permissions/data/enums/device_permission.dart';

import 'helpers/account_test_dependencies.dart';
import 'helpers/home_page_test_dependencies.dart';

final Map<String, Map<String, dynamic>> _translations = {};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late _AccountStatsRepository accountRepository;
  const MethodChannel preferences = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const MethodChannel connectivity = MethodChannel(
    'dev.fluttercommunity.plus/connectivity',
  );
  const MethodChannel connectivityStatus = MethodChannel(
    'dev.fluttercommunity.plus/connectivity_status',
  );
  const MethodChannel secureStorage = MethodChannel(
    'plugins.it_nomads.com/flutter_secure_storage',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          preferences,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await CacheStorage.init();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(secureStorage, (_) async => null);
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          connectivity,
          (call) async => call.method == 'check' ? <String>['wifi'] : null,
        );
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(connectivityStatus, (_) async => null);
    await EasyLocalization.ensureInitialized();
    for (final String language in ['en', 'ar']) {
      _translations[language] =
          jsonDecode(
                await rootBundle.loadString(
                  'packages/melos_core/assets/translations/$language.json',
                ),
              )
              as Map<String, dynamic>;
    }
    PackageInfo.setMockInitialValues(
      appName: 'Sokoun',
      packageName: 'test.sokoun',
      version: '1.0.0',
      buildNumber: '1',
      buildSignature: '',
    );
  });
  setUp(() async {
    await injector.reset();
    await CacheStorage.deleteAll();
    AccountSession.end();
    WorkspaceNavigation.clearPending();
    registerHomePageTestDependencies();
    accountRepository = _AccountStatsRepository(
      injector<BaseCrudUseCase>().repository,
    );
    await injector.unregister<BaseCrudUseCase>();
    injector.registerSingleton<BaseCrudUseCase>(
      BaseCrudUseCase(repository: accountRepository),
    );
  });
  tearDown(() async {
    WorkspaceNavigation.clearPending();
    await injector.reset();
  });
  tearDownAll(() {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(secureStorage, null);
  });

  testWidgets('authenticated home explains notifications once after launch', (
    tester,
  ) async {
    _phone(tester);
    await registerAuthenticatedTestAccount();
    final permissions = _HomePermissionSource();
    injector.registerSingleton<DevicePermissionDataSource>(permissions);
    await tester.pumpWidget(_app(const HomeScreen(), 'en'));
    await tester.pumpAndSettle();
    expect(find.byType(NotificationPermissionView), findsOneWidget);
    expect(permissions.requests, 0);
    final skip = find
        .descendant(
          of: find.byType(PermissionActions),
          matching: find.byType(ElevatedButton),
        )
        .last;
    await tester.ensureVisible(skip);
    await tester.tap(skip);
    await tester.pumpAndSettle();
    expect(permissions.seen, isTrue);
    expect(permissions.requests, 0);

    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    await tester.pumpWidget(_app(const HomeScreen(), 'en'));
    await tester.pumpAndSettle();
    expect(find.byType(NotificationPermissionView), findsNothing);
    expect(permissions.requests, 0);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  });

  for (final bool hasCachedUser in [false, true]) {
    testWidgets(
      'home caches account and restores owner workspace with ${hasCachedUser ? 'cached identity' : 'login cookies only'}',
      (tester) async {
        _phone(tester);
        if (hasCachedUser) {
          await registerAuthenticatedTestAccount();
        } else {
          injector.registerSingleton<UserCubit>(
            UserCubit(),
            dispose: (cubit) => cubit.close(),
          );
          final NetworkService fallback = injector<NetworkService>();
          await injector.unregister<NetworkService>();
          injector.registerSingleton<NetworkService>(
            _CookieSessionNetwork(fallback),
          );
        }
        await WorkspacePreferences.write('1', AppWorkspace.owner);
        injector.registerSingleton<DevicePermissionDataSource>(
          _HomePermissionSource()..seen = true,
        );
        await tester.pumpWidget(_app(const HomeScreen(), 'en'));
        await tester.pumpAndSettle();

        expect(accountRepository.profileRequests, 1);
        expect(UserModel.currentUser?.email, 'refreshed@example.com');
        expect(UserCubit.instance.isUserLoggedIn, isTrue);
        expect(WorkspaceCubit.instance.userId, '1');
        expect(WorkspaceCubit.instance.state, AppWorkspace.owner);
        expect(find.byType(OwnerHomeScreen), findsOneWidget);

        await tester.pumpWidget(_app(const HomeScreen(), 'en'));
        await tester.pumpAndSettle();
        expect(accountRepository.profileRequests, 1);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pumpAndSettle();
      },
    );
  }

  testWidgets(
    'cookie-only login restarts home requests under the saved account',
    (tester) async {
      _phone(tester);
      injector.registerSingleton<UserCubit>(
        UserCubit(),
        dispose: (cubit) => cubit.close(),
      );
      final NetworkService fallback = injector<NetworkService>();
      await injector.unregister<NetworkService>();
      injector.registerSingleton<NetworkService>(
        _CookieSessionNetwork(fallback),
      );
      injector.registerSingleton<DevicePermissionDataSource>(
        _HomePermissionSource()..seen = true,
      );
      accountRepository.homeGate = Completer<void>();

      await tester.pumpWidget(_app(const HomeScreen(), 'en'));
      await tester.pumpAndSettle();

      expect(accountRepository.profileRequests, 1);
      expect(accountRepository.homeRequests, 2);
      final HomePageCubit home = tester
          .element(find.byType(RefreshIndicator))
          .read<HomePageCubit>();
      expect(home.state.isSuccess, isTrue);
      expect(UserModel.currentUser?.id, '1');
      accountRepository.homeGate!.complete();
      await tester.pumpAndSettle();
      expect(home.state.isSuccess, isTrue);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    },
  );

  testWidgets('guest home never asks for notification permission', (
    tester,
  ) async {
    _phone(tester);
    final permissions = _HomePermissionSource();
    injector.registerSingleton<DevicePermissionDataSource>(permissions);
    await tester.pumpWidget(_app(const HomeScreen(), 'en'));
    await tester.pumpAndSettle();
    expect(find.byType(NotificationPermissionView), findsNothing);
    expect(permissions.seen, isFalse);
    expect(permissions.requests, 0);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    expect(accountRepository.profileRequests, 0);
  });

  test('coalesces simultaneous my-account requests', () async {
    accountRepository.profileGate = Completer<void>();
    final TenantProfileCubit cubit = TenantProfileCubit();
    addTearDown(cubit.close);

    final Future<void> first = cubit.getProfile();
    final Future<void> second = cubit.getProfile();
    expect(second, same(first));
    expect(accountRepository.profileRequests, 1);

    accountRepository.profileGate!.complete();
    await Future.wait([first, second]);
    expect(cubit.state.isSuccess, isTrue);
    await cubit.getProfile();
    expect(accountRepository.profileRequests, 2);
  });

  testWidgets('standalone tenant profile owns and closes its cubit', (
    tester,
  ) async {
    _phone(tester);
    await registerAuthenticatedTestAccount();
    await tester.pumpWidget(_app(const TenantProfileScreen(), 'en'));
    await tester.pumpAndSettle();
    final TenantProfileCubit profile = tester
        .element(find.byType(TenantProfileContentView))
        .read<TenantProfileCubit>();
    expect(accountRepository.profileRequests, 1);
    expect(profile.state.isSuccess, isTrue);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    expect(profile.isClosed, isTrue);
  });

  for (final String language in ['en', 'ar']) {
    testWidgets(
      'shows and refreshes my-account badges only in tenant workspace in $language',
      (tester) async {
        _phone(tester);
        await registerAuthenticatedTestAccount();
        accountRepository.stats = {
          'saved_count': 120,
          'visits_count': 4,
          'reviews_count': 2,
        };
        await tester.pumpWidget(_app(const HomeScreen(), language));
        await tester.pumpAndSettle();
        tester
            .element(find.byType(HomeBottomNavigation))
            .read<ChatUnreadCubit>()
            .updateData(const ChatUnreadContent(count: 7));
        await tester.pumpAndSettle();

        HomeBottomNavigation navigation() => tester
            .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation));
        List<int> badgeCounts() => navigation().destinations
            .map((destination) => destination.badgeCount)
            .toList();
        final Finder bottomBar = find.byType(HomeBottomNavigation);
        expect(badgeCounts(), [0, 120, 7, 4, 2]);
        expect(
          find.descendant(of: bottomBar, matching: find.text('99+')),
          findsOneWidget,
        );
        expect(find.byType(TenantProfileScreen), findsNothing);
        expect(accountRepository.profileRequests, 1);
        final TenantProfileCubit sharedProfile = tester
            .element(bottomBar)
            .read<TenantProfileCubit>();

        accountRepository.stats = {
          'saved_count': 6,
          'visits_count': 5,
          'reviews_count': 3,
        };
        navigation().onDestinationSelected(4);
        await tester.pumpAndSettle();
        expect(find.byType(TenantProfileScreen), findsOneWidget);
        expect(badgeCounts(), [0, 6, 7, 5, 3]);
        expect(accountRepository.profileRequests, 2);
        expect(
          tester
              .element(find.byType(TenantProfileContentView))
              .read<TenantProfileCubit>(),
          same(sharedProfile),
        );

        unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.owner));
        await tester.pumpAndSettle();
        expect(badgeCounts(), [0, 0, 0, 7, 0]);
        expect(accountRepository.profileRequests, 2);
        expect(sharedProfile.isClosed, isFalse);

        accountRepository.stats = {
          'saved_count': 0,
          'visits_count': 0,
          'reviews_count': 0,
        };
        unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.tenant));
        await tester.pumpAndSettle();
        expect(badgeCounts(), [0, 0, 7, 0, 0]);
        expect(accountRepository.profileRequests, 3);
        expect(
          find.descendant(of: bottomBar, matching: find.text('0')),
          findsNothing,
        );

        accountRepository.stats = {
          'saved_count': 3,
          'visits_count': 2,
          'reviews_count': 1,
        };
        tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.paused);
        tester.binding.handleAppLifecycleStateChanged(
          AppLifecycleState.resumed,
        );
        await tester.pumpAndSettle();
        expect(badgeCounts(), [0, 3, 7, 2, 1]);
        expect(accountRepository.profileRequests, 4);
        expect(tester.takeException(), isNull);

        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pumpAndSettle();
        expect(sharedProfile.isClosed, isTrue);
      },
    );

    testWidgets(
      'switches workspace, retains tab state and shares one session in $language',
      (tester) async {
        _phone(tester);
        await registerAuthenticatedTestAccount();
        final int generation = AccountSession.generation;
        await tester.pumpWidget(_app(const HomeScreen(), language));
        await tester.pumpAndSettle(
          const Duration(milliseconds: 100),
          EnginePhase.sendSemanticsUpdate,
          const Duration(seconds: 5),
        );
        expect(find.byType(TenantHomeScreen), findsOneWidget);
        expect(find.byType(OwnerHomeScreen, skipOffstage: false), findsNothing);
        final State tenantState = tester.state(find.byType(TenantHomeScreen));
        final ChatUnreadCubit unread = tester
            .element(find.byType(HomeBottomNavigation))
            .read<ChatUnreadCubit>();

        await tester.tap(
          find.widgetWithText(ChoiceChip, LocaleKeys.workspaceOwner),
        );
        await tester.pumpAndSettle(
          const Duration(milliseconds: 100),
          EnginePhase.sendSemanticsUpdate,
          const Duration(seconds: 5),
        );
        expect(find.byType(OwnerHomeScreen), findsOneWidget);
        expect(WorkspaceCubit.instance.state, AppWorkspace.owner);
        tester
            .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation))
            .onDestinationSelected(1);
        await tester.pumpAndSettle(
          const Duration(milliseconds: 100),
          EnginePhase.sendSemanticsUpdate,
          const Duration(seconds: 5),
        );

        unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.tenant));
        await tester.pumpAndSettle(
          const Duration(milliseconds: 100),
          EnginePhase.sendSemanticsUpdate,
          const Duration(seconds: 5),
        );
        expect(tester.state(find.byType(TenantHomeScreen)), same(tenantState));
        tester
            .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation))
            .onDestinationSelected(1);
        await tester.pumpAndSettle(
          const Duration(milliseconds: 100),
          EnginePhase.sendSemanticsUpdate,
          const Duration(seconds: 5),
        );
        unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.owner));
        await tester.pumpAndSettle(
          const Duration(milliseconds: 100),
          EnginePhase.sendSemanticsUpdate,
          const Duration(seconds: 5),
        );
        expect(
          tester
              .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation))
              .currentIndex,
          1,
        );
        expect(
          tester
              .element(find.byType(HomeBottomNavigation))
              .read<ChatUnreadCubit>(),
          same(unread),
        );
        expect(AccountSession.generation, generation);
        expect(UserCubit.instance.user.id, '1');
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pumpAndSettle(
          const Duration(milliseconds: 100),
          EnginePhase.sendSemanticsUpdate,
          const Duration(seconds: 5),
        );
      },
    );
  }

  testWidgets('cross-workspace navigation asks before discarding an edit', (
    tester,
  ) async {
    _phone(tester);
    await registerAuthenticatedTestAccount();
    await tester.pumpWidget(_app(const HomeScreen(), 'en'));
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    unawaited(
      Go.to<void>(
        Scaffold(
          body: UnsavedChangesGuard(
            hasChanges: () => true,
            isSaving: () => false,
            child: const Text('Unsaved listing'),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.owner));
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    await tester.tap(find.text(LocaleKeys.workspaceStay));
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    expect(find.text('Unsaved listing'), findsOneWidget);
    expect(WorkspaceCubit.instance.state, AppWorkspace.tenant);
    unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.owner));
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    await tester.tap(find.text(LocaleKeys.workspaceDiscard));
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    expect(find.text('Unsaved listing'), findsNothing);
    expect(WorkspaceCubit.instance.state, AppWorkspace.owner);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
  });

  testWidgets('cancelling login discards the deferred workspace target', (
    tester,
  ) async {
    _phone(tester);
    await tester.pumpWidget(_app(const Scaffold(), 'en'));
    await tester.pumpAndSettle();
    unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.owner));
    await tester.pumpAndSettle();
    expect(find.byType(LoginScreen), findsOneWidget);
    Go.back();
    await tester.pumpAndSettle();
    await registerAuthenticatedTestAccount();
    unawaited(Go.offAll<void, void>(const HomeScreen()));
    await tester.pumpAndSettle();
    expect(WorkspaceCubit.instance.state, AppWorkspace.tenant);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  });

  testWidgets('owner notification survives login and opens the owner request', (
    tester,
  ) async {
    _phone(tester);
    await tester.pumpWidget(_app(const Scaffold(), 'en'));
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    unawaited(
      NotificationPushHandler.handle({
        'notification_type': 'visit_request',
        'visit_id': 'request-1',
        'action_type': 'view_visit',
      }),
    );
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    expect(find.byType(LoginScreen), findsOneWidget);
    await registerAuthenticatedTestAccount();
    unawaited(Go.offAll<void, void>(const HomeScreen()));
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
    expect(WorkspaceCubit.instance.state, AppWorkspace.owner);
    expect(find.byType(OwnerRequestDetailsScreen), findsOneWidget);
    expect(
      tester
          .widget<OwnerRequestDetailsScreen>(
            find.byType(OwnerRequestDetailsScreen),
          )
          .requestId,
      'request-1',
    );
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle(
      const Duration(milliseconds: 100),
      EnginePhase.sendSemanticsUpdate,
      const Duration(seconds: 5),
    );
  });
}

void _phone(WidgetTester tester) {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

Widget _app(Widget home, String language) => EasyLocalization(
  supportedLocales: const [Locale('en'), Locale('ar')],
  startLocale: Locale(language),
  saveLocale: false,
  path: 'unused',
  assetLoader: const _Translations(),
  child: ScreenUtilInit(
    designSize: const Size(360, 690),
    builder: (context, _) => MaterialApp(
      navigatorKey: Go.navigatorKey,
      navigatorObservers: [AppNavigationObserver.instance],
      localizationsDelegates: context.localizationDelegates,
      supportedLocales: context.supportedLocales,
      locale: context.locale,
      home: Builder(
        builder: (context) => MediaQuery(
          data: MediaQuery.of(context).copyWith(disableAnimations: true),
          child: home,
        ),
      ),
    ),
  ),
);

class _Translations extends AssetLoader {
  const _Translations();

  @override
  Future<Map<String, dynamic>> load(String path, Locale locale) async =>
      _translations[locale.languageCode]!;
}

class _HomePermissionSource implements DevicePermissionDataSource {
  bool seen = false;
  int requests = 0;
  @override
  bool get hasSeenNotificationPrompt => seen;
  @override
  Future<void> markNotificationPromptSeen() async => seen = true;
  @override
  Future<DevicePermissionStatus> status(DevicePermission permission) async =>
      DevicePermissionStatus.denied;
  @override
  Future<DevicePermissionStatus> request(DevicePermission permission) async {
    requests++;
    return DevicePermissionStatus.granted;
  }

  @override
  Future<bool> openSettings() async => true;
}

class _AccountStatsRepository implements BaseRepository {
  _AccountStatsRepository(this.fallback);

  final BaseRepository fallback;
  Map<String, dynamic> stats = const {
    'saved_count': 0,
    'visits_count': 0,
    'reviews_count': 0,
  };
  int profileRequests = 0;
  int homeRequests = 0;
  Completer<void>? profileGate;
  Completer<void>? homeGate;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    final Map<String, dynamic> response;
    if (params.api == ApiConstants.getAccData) {
      profileRequests++;
      await profileGate?.future;
      response = {
        'user': {'id': '1', 'full_name': 'Test account'},
        'account_details': {'email': 'refreshed@example.com'},
        'stats': stats,
      };
    } else {
      if (params.api == ApiConstants.homePage) {
        homeRequests++;
        if (homeRequests == 1) await homeGate?.future;
      }
      return fallback.crudCall(params);
    }
    expectSync(params.httpRequestType, HttpRequestType.get);
    return Success(
      BaseModel<T>(key: '', msg: '', data: params.mapper!(response)),
    );
  }

  @override
  Future<Result<List<T>, Failure>> getBaseIdAndNameEntity<T extends BaseEntity>(
    GetBaseEntityParams? param,
  ) => fallback.getBaseIdAndNameEntity<T>(param);
}

class _CookieSessionNetwork implements NetworkService {
  _CookieSessionNetwork(this.fallback);

  final NetworkService fallback;

  @override
  Future<bool> hasSessionCookies() async => true;

  @override
  Future<void> clearSessionCookies() => fallback.clearSessionCookies();

  @override
  Future<void> updateBaseUrl() => fallback.updateBaseUrl();

  @override
  Future<BaseModel<T>> callApi<T>(
    NetworkRequest request, {
    T Function(dynamic)? mapper,
  }) => fallback.callApi<T>(request, mapper: mapper);
}

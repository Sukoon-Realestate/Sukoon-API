import 'package:sokoun_app/features/main_view/presentation/cubits/account_cubit.dart';
import 'package:sokoun_app/features/tenant/home/presentation/widgets/tenant_widgets/tenant_home_content.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_navigation_rail.dart';
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
import 'package:sokoun_app/features/shared/auth/presentation/screens/welcome_screen.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_realtime_service.dart';
import 'package:sokoun_app/features/shared/chat/data/chat_socket_data.dart';
import 'package:sokoun_app/features/shared/unread_counts/presentation/cubits/unread_counts_cubit.dart';
import 'package:sokoun_app/features/shared/notifications/data/notification_device_data.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/notification_push_handler.dart';
import 'package:sokoun_app/features/shared/profile/imports.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/features/tenant/visits/imports.dart';
import 'package:melos_core/core/widgets/app_pagify.dart';
import 'package:sokoun_app/features/tenant/home/data/models/home_page_model.dart';
import 'package:sokoun_app/shared_widgets/unsaved_changes_guard.dart';

import 'package:melos_core/core/widgets/notification_permission_view.dart';
import 'package:melos_core/core/widgets/permissions/permission_actions.dart';
import 'package:sokoun_app/features/shared/permissions/data/device_permission_data.dart';
import 'package:sokoun_app/features/shared/permissions/data/enums/device_permission.dart';

import 'helpers/account_test_dependencies.dart';
import 'helpers/home_page_test_dependencies.dart';
import 'helpers/recording_chat_socket.dart';

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
    ChatRealtimeService.instance.setActiveConversation(null);
    await ChatRealtimeService.instance.disconnect();
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
      accountRepository.profileGate = Completer<void>();

      await tester.pumpWidget(_app(const HomeScreen(), 'en'));
      await tester.pumpAndSettle();
      expect(accountRepository.homeRequests, 1);
      accountRepository.profileGate!.complete();
      await tester.pumpAndSettle();

      expect(accountRepository.profileRequests, 1);
      expect(accountRepository.homeRequests, 2);
      final home = tester
          .widget<AppPagify<HomePropertyModel>>(
            find.byType(AppPagify<HomePropertyModel>),
          )
          .pagifyController;
      expect(home.isSuccess, isTrue);
      expect(UserModel.currentUser?.id, '1');
      accountRepository.homeGate!.complete();
      await tester.pumpAndSettle();
      expect(home.isSuccess, isTrue);
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
    await registerAuthenticatedTestAccount();
    accountRepository.profileGate = Completer<void>();
    final AccountCubit cubit = AccountCubit();
    addTearDown(cubit.close);

    final Future<void> first = cubit.getAccount();
    final Future<void> second = cubit.getAccount();
    expect(second, same(first));
    expect(accountRepository.profileRequests, 1);

    accountRepository.profileGate!.complete();
    await Future.wait([first, second]);
    expect(cubit.state.isSuccess, isTrue);
    await cubit.getAccount();
    expect(accountRepository.profileRequests, 2);
  });

  testWidgets('standalone tenant profile owns and closes its cubit', (
    tester,
  ) async {
    _phone(tester);
    await registerAuthenticatedTestAccount();
    await tester.pumpWidget(_app(const TenantProfileScreen(), 'en'));
    await tester.pumpAndSettle();
    final AccountCubit profile = tester
        .element(find.byType(TenantProfileContentView))
        .read<AccountCubit>();
    expect(accountRepository.profileRequests, 1);
    expect(profile.state.isSuccess, isTrue);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
    expect(profile.isClosed, isTrue);
  });

  for (final String language in ['en', 'ar']) {
    testWidgets(
      'loads role counts on entry and keeps them across tabs in $language',
      (tester) async {
        _phone(tester);
        await registerAuthenticatedTestAccount();
        accountRepository.stats = {
          'saved_count': 120,
          'visits_count': 4,
          'reviews_count': 2,
        };
        accountRepository.tenantCounts = {
          'unread_chat_messages_count': 7,
          'favorites_count': 120,
          'visit_requests_count': 4,
        };
        accountRepository.ownerCounts = {'visit_requests_count': 9};
        await tester.pumpWidget(_app(const HomeScreen(), language));
        await tester.pumpAndSettle();

        HomeBottomNavigation navigation() => tester
            .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation));
        List<int> badgeCounts() => navigation().destinations
            .map((destination) => destination.badgeCount)
            .toList();
        final Finder bottomBar = find.byType(HomeBottomNavigation);
        expect(badgeCounts(), [0, 0, 7, 0, 0]);
        expect(
          find.descendant(of: bottomBar, matching: find.text('99+')),
          findsNothing,
        );
        expect(find.byType(TenantProfileScreen), findsNothing);
        expect(accountRepository.profileRequests, 1);
        final int initialCountRequests = accountRepository.countRequests;
        expect(initialCountRequests, 2);
        final AccountCubit sharedProfile = tester
            .element(bottomBar)
            .read<AccountCubit>();

        accountRepository.stats = {
          'saved_count': 6,
          'visits_count': 5,
          'reviews_count': 3,
        };
        accountRepository.tenantCounts = {
          'unread_chat_messages_count': 7,
          'favorites_count': 6,
          'visit_requests_count': 5,
        };
        navigation().onDestinationSelected(4);
        await tester.pumpAndSettle();
        expect(find.byType(TenantProfileScreen), findsOneWidget);
        expect(badgeCounts(), [0, 0, 7, 0, 0]);
        expect(accountRepository.profileRequests, 1);
        expect(accountRepository.countRequests, initialCountRequests);
        expect(
          tester
              .element(find.byType(TenantProfileContentView))
              .read<AccountCubit>(),
          same(sharedProfile),
        );

        unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.owner));
        await tester.pumpAndSettle();
        expect(badgeCounts(), [0, 0, 7, 0, 0]);
        expect(accountRepository.profileRequests, 1);
        expect(accountRepository.countRequests, initialCountRequests);
        expect(sharedProfile.isClosed, isFalse);

        accountRepository.stats = {
          'saved_count': 0,
          'visits_count': 0,
          'reviews_count': 0,
        };
        accountRepository.tenantCounts = {
          'unread_chat_messages_count': 7,
          'favorites_count': 0,
          'visit_requests_count': 0,
        };
        unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.tenant));
        await tester.pumpAndSettle();
        expect(badgeCounts(), [0, 0, 7, 0, 0]);
        for (final int index in [0, 1, 2, 3, 4, 0]) {
          navigation().onDestinationSelected(index);
          await tester.pumpAndSettle();
        }
        expect(accountRepository.profileRequests, 1);
        expect(accountRepository.countRequests, initialCountRequests);

        accountRepository.stats = {
          'saved_count': 3,
          'visits_count': 2,
          'reviews_count': 1,
        };
        accountRepository.tenantCounts = {
          'unread_chat_messages_count': 7,
          'favorites_count': 3,
          'visit_requests_count': 2,
        };
        for (final AppLifecycleState lifecycle in [
          AppLifecycleState.inactive,
          AppLifecycleState.hidden,
          AppLifecycleState.paused,
          AppLifecycleState.hidden,
          AppLifecycleState.inactive,
          AppLifecycleState.resumed,
        ]) {
          tester.binding.handleAppLifecycleStateChanged(lifecycle);
        }
        await tester.pumpAndSettle();
        expect(badgeCounts(), [0, 0, 7, 0, 0]);
        expect(accountRepository.profileRequests, 2);
        expect(accountRepository.countRequests, initialCountRequests + 2);
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
        final State tenantState = tester.state(find.byType(TenantHomeContent));
        tester.view.physicalSize = const Size(1024, 768);
        await tester.pumpAndSettle();
        expect(find.byType(HomeNavigationRail), findsOneWidget);
        expect(find.byType(HomeBottomNavigation), findsNothing);
        expect(tester.state(find.byType(TenantHomeContent)), same(tenantState));
        tester.view.physicalSize = const Size(390, 844);
        await tester.pumpAndSettle();
        expect(find.byType(HomeNavigationRail), findsNothing);
        expect(tester.state(find.byType(TenantHomeContent)), same(tenantState));
        final UnreadCountsCubit unread = tester
            .element(find.byType(HomeBottomNavigation))
            .read<UnreadCountsCubit>();

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
        expect(tester.state(find.byType(TenantHomeContent)), same(tenantState));
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
              .read<UnreadCountsCubit>(),
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

  testWidgets(
    'a booking draft survives cancelled workspace switching and cannot leave while submitting',
    (tester) async {
      _phone(tester);
      await registerAuthenticatedTestAccount();
      await tester.pumpWidget(_app(const HomeScreen(), 'en'));
      await tester.pumpAndSettle();
      unawaited(
        Go.to(
          const BookVisitScreen(
            property: VisitPropertyContent(
              id: 'property-1',
              ownerId: 'another-owner',
              title: 'Apartment',
              meta: 'Cairo',
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();
      BookVisitForm form() =>
          tester.widget<BookVisitForm>(find.byType(BookVisitForm));
      form().noteController.text = 'Please call before the visit';
      form().onTimeSelected(const TimeOfDay(hour: 14, minute: 30));
      await tester.pump();
      unawaited(WorkspaceNavigation.open(workspace: AppWorkspace.owner));
      await tester.pumpAndSettle();
      await tester.tap(find.text(LocaleKeys.workspaceStay));
      await tester.pumpAndSettle();
      expect(form().noteController.text, 'Please call before the visit');
      expect(WorkspaceCubit.instance.state, AppWorkspace.tenant);
      final gate = Completer<void>();
      accountRepository.bookingGate = gate;
      final submission = form().onConfirmPressed(
        tester.element(find.byType(BookVisitForm)),
      );
      await tester.pump();
      await WorkspaceNavigation.open(workspace: AppWorkspace.owner);
      await tester.pump();
      expect(find.byType(BookVisitScreen), findsOneWidget);
      expect(WorkspaceCubit.instance.state, AppWorkspace.tenant);
      gate.complete();
      await submission;
      await tester.pumpAndSettle();
      expect(find.byType(VisitConfirmedScreen), findsOneWidget);
      expect(accountRepository.bookings, 1);
      expect(tester.takeException(), isNull);
    },
  );

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
  for (final workspace in AppWorkspace.values) {
    for (final notificationType in ['account_verification', 'security_alert']) {
      testWidgets(
        '${workspace.name} $notificationType opens its detail without a second Profile',
        (tester) async {
          _phone(tester);
          await registerAuthenticatedTestAccount();
          await WorkspacePreferences.write('1', workspace);
          injector.registerSingleton<DevicePermissionDataSource>(
            _HomePermissionSource()..seen = true,
          );
          await tester.pumpWidget(_app(const HomeScreen(), 'en'));
          await tester.pumpAndSettle();
          unawaited(
            NotificationPushHandler.handle({
              'notification_type': notificationType,
            }),
          );
          await tester.pumpAndSettle();
          expect(WorkspaceCubit.instance.state, workspace);
          if (notificationType == 'account_verification') {
            expect(find.byType(ProfileVerificationScreen), findsOneWidget);
            expect(
              tester
                  .widget<ProfileVerificationScreen>(
                    find.byType(ProfileVerificationScreen),
                  )
                  .workspace,
              workspace,
            );
          } else {
            expect(find.byType(ProfileSettingsScreen), findsOneWidget);
            expect(
              tester
                  .widget<ProfileSettingsScreen>(
                    find.byType(ProfileSettingsScreen),
                  )
                  .workspace,
              workspace,
            );
          }
          Go.back();
          await tester.pumpAndSettle();
          expect(find.byType(ProfileScreen), findsOneWidget);
          expect(
            tester
                .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation))
                .currentIndex,
            4,
          );
          expect(find.byType(ProfileVerificationScreen), findsNothing);
          expect(find.byType(ProfileSettingsScreen), findsNothing);
          expect(tester.takeException(), isNull);
        },
      );
    }
    testWidgets('${workspace.name} last tab opens Profile directly', (
      tester,
    ) async {
      _phone(tester);
      await registerAuthenticatedTestAccount();
      await WorkspacePreferences.write('1', workspace);
      injector.registerSingleton<DevicePermissionDataSource>(
        _HomePermissionSource()..seen = true,
      );
      await tester.pumpWidget(_app(const HomeScreen(), 'en'));
      await tester.pumpAndSettle();
      final navigation = tester.widget<HomeBottomNavigation>(
        find.byType(HomeBottomNavigation),
      );
      expect(navigation.destinations.last.label, 'Profile');
      navigation.onDestinationSelected(4);
      await tester.pumpAndSettle();
      expect(find.byType(ProfileScreen), findsOneWidget);
      expect(
        tester.widget<ProfileScreen>(find.byType(ProfileScreen)).workspace,
        workspace,
      );
      expect(
        find.byType(
          workspace.isOwner ? OwnerProfileScreen : TenantProfileScreen,
        ),
        findsOneWidget,
      );
      expect(find.byType(ProfileHeaderCard), findsOneWidget);
      expect(find.byIcon(Icons.settings_outlined), findsOneWidget);
      expect(find.byIcon(Icons.support_agent_rounded), findsOneWidget);
      expect(find.text('More'), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }

  for (final (workspace, deleteAccount) in [
    for (final workspace in AppWorkspace.values)
      for (final deleteAccount in [false, true]) (workspace, deleteAccount),
  ]) {
    testWidgets(
      '${workspace.name} ${deleteAccount ? 'deleting the account' : 'logout'} sends only its action endpoint',
      (tester) async {
        _phone(tester);
        await registerAuthenticatedTestAccount();
        await WorkspacePreferences.write('1', workspace);
        _listenForLogout();
        final devices = _HomeNotificationDeviceSource();
        injector.registerSingleton<NotificationDeviceDataSource>(devices);
        injector.registerSingleton<DevicePermissionDataSource>(
          _HomePermissionSource()..seen = true,
        );
        await tester.pumpWidget(_app(const HomeScreen(), 'en'));
        await tester.pumpAndSettle();
        tester
            .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation))
            .onDestinationSelected(4);
        await tester.pumpAndSettle();
        expect(find.byType(IndexedStack), findsOneWidget);
        await tester.tap(find.byIcon(Icons.settings_outlined));
        await tester.pumpAndSettle();
        expect(find.byType(ProfileSettingsScreen), findsOneWidget);
        final int homeRequests = accountRepository.homeRequests;
        final int requests = accountRepository.endpoints.length;

        final button = find.byType(
          deleteAccount ? ProfileDeleteAccountButton : ProfileLogoutButton,
        );
        await tester.scrollUntilVisible(
          button,
          300,
          scrollable: find.descendant(
            of: find.byType(ProfileSettingsContentView),
            matching: find.byType(Scrollable),
          ),
        );
        await tester.pumpAndSettle();
        await tester.ensureVisible(button);
        await tester.pumpAndSettle();
        await tester.tap(button);
        if (deleteAccount) {
          await tester.pumpAndSettle();
          await tester.tap(find.byType(CheckboxListTile));
          await tester.pumpAndSettle();
          await tester.tap(find.text(LocaleKeys.settingsDeletePermanently));
        } else {
          await tester.pumpAndSettle();
          await tester.tap(find.text(LocaleKeys.profileLogout).last);
        }
        await tester.pumpAndSettle();

        expect(accountRepository.endpoints.skip(requests), [
          deleteAccount ? ApiConstants.deleteAccount : ApiConstants.logout,
        ]);
        expect(accountRepository.homeRequests, homeRequests);
        expect(devices.localStops, 1);
        expect(devices.serverUnregisters, 0);
        expect(UserCubit.instance.isUserLoggedIn, isFalse);
        expect(find.byType(WelcomeScreen), findsOneWidget);
        expect(tester.takeException(), isNull);
        await tester.pumpWidget(const SizedBox.shrink());
        await tester.pumpAndSettle();
      },
    );
  }

  testWidgets('home and the messages tab leave the socket disconnected', (
    tester,
  ) async {
    _phone(tester);
    await registerAuthenticatedTestAccount();
    injector.registerSingleton<DevicePermissionDataSource>(
      _HomePermissionSource()..seen = true,
    );
    final sockets = RecordingChatSocketSource();
    injector.registerSingleton<ChatSocketDataSource>(sockets);
    await tester.pumpWidget(_app(const HomeScreen(), 'en'));
    await tester.pumpAndSettle();
    tester
        .widget<HomeBottomNavigation>(find.byType(HomeBottomNavigation))
        .onDestinationSelected(2);
    await tester.pumpAndSettle();
    for (final state in [
      AppLifecycleState.inactive,
      AppLifecycleState.hidden,
      AppLifecycleState.paused,
      AppLifecycleState.hidden,
      AppLifecycleState.inactive,
      AppLifecycleState.resumed,
    ]) {
      tester.binding.handleAppLifecycleStateChanged(state);
    }
    await tester.pumpAndSettle();

    expect(sockets.creations, 0);
    expect(sockets.connections, 0);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    await tester.pumpAndSettle();
  });

  testWidgets(
    'late account startup cannot restart home features after logout',
    (tester) async {
      _phone(tester);
      await registerAuthenticatedTestAccount();
      _listenForLogout();
      final devices = _HomeNotificationDeviceSource();
      injector.registerSingleton<NotificationDeviceDataSource>(devices);
      accountRepository.profileGate = Completer<void>();
      await tester.pumpWidget(_app(const HomeScreen(), 'en'));
      await tester.pump();
      expect(accountRepository.profileRequests, 1);
      await UserCubit.instance.logout();
      accountRepository.profileGate!.complete();
      tester.binding.handleAppLifecycleStateChanged(AppLifecycleState.resumed);
      await tester.pumpAndSettle();

      expect(accountRepository.countRequests, 0);
      expect(accountRepository.homeRequests, 1);
      expect(devices.starts, 0);
      expect(find.byType(WelcomeScreen), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
      await tester.pumpAndSettle();
    },
  );
}

void _phone(WidgetTester tester) {
  tester.view.physicalSize = const Size(390, 844);
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
}

void _listenForLogout() {
  final subscription = UserCubit.instance.stream.listen((state) {
    if (state.userStatus != UserStatus.loggedOut) return;
    WorkspaceNavigation.clearPending();
    WorkspaceCubit.instance.reset();
    unawaited(Go.offAll(const WelcomeScreen()));
  });
  addTearDown(subscription.cancel);
}

Widget _app(Widget home, String language) => EasyLocalization(
  supportedLocales: const [Locale('en'), Locale('ar')],
  startLocale: Locale(language),
  saveLocale: false,
  path: 'unused',
  assetLoader: const _Translations(),
  child: ScreenUtilInit(
    designSize: const Size(360, 690),
    enableScaleWH: () => false,
    enableScaleText: () => false,
    fontSizeResolver: (size, _) => size.toDouble(),
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

class _HomeNotificationDeviceSource implements NotificationDeviceDataSource {
  int starts = 0;
  int localStops = 0;
  int serverUnregisters = 0;

  @override
  Future<void> start() async => starts++;
  @override
  Future<void> registerCurrentDevice() async {}
  @override
  Future<void> registerToken(String token) async {}
  @override
  Future<void> unregisterCurrentDevice({bool notifyServer = true}) async {
    if (notifyServer) {
      serverUnregisters++;
    } else {
      localStops++;
    }
  }
}

class _AccountStatsRepository implements BaseRepository {
  _AccountStatsRepository(this.fallback);

  final BaseRepository fallback;
  Map<String, dynamic> tenantCounts = const {};
  Map<String, dynamic> ownerCounts = const {};
  Map<String, dynamic> stats = const {
    'saved_count': 0,
    'visits_count': 0,
    'reviews_count': 0,
  };
  int profileRequests = 0;
  int countRequests = 0;
  int homeRequests = 0;
  final List<String> endpoints = [];
  Completer<void>? profileGate;
  Completer<void>? homeGate;
  Completer<void>? bookingGate;
  int bookings = 0;

  @override
  Future<Result<BaseModel<T>, Failure>> crudCall<T>(
    CrudBaseParmas<T> params,
  ) async {
    endpoints.add(params.api);
    if (params.api == ApiConstants.propertyVisits('property-1') &&
        params.httpRequestType == HttpRequestType.post) {
      bookings++;
      await bookingGate?.future;
      return Success(
        BaseModel<T>(
          key: '',
          msg: '',
          data: params.mapper!(<String, dynamic>{}),
        ),
      );
    }
    final Map<String, dynamic> response;
    if (params.api == ApiConstants.tenantUnreadCounts) {
      countRequests++;
      response = tenantCounts;
    } else if (params.api == ApiConstants.ownerUnreadCounts) {
      countRequests++;
      response = ownerCounts;
    } else if (params.api == ApiConstants.getAccData) {
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

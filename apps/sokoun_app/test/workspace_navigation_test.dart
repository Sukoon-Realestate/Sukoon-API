import 'dart:async';
import 'dart:convert';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:melos_core/config/res/config_imports.dart';
import 'package:melos_core/config/language/locale_keys.g.dart';
import 'package:melos_core/core/helpers/cache_service.dart';
import 'package:melos_core/core/navigation/navigator.dart';
import 'package:melos_core/core/network/account_session.dart';
import 'package:melos_core/core/shared/route_observer.dart';
import 'package:melos_core/core/shared/user_cubit/user_cubit.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:sokoun_app/features/main_view/data/enums/app_workspace.dart';
import 'package:sokoun_app/features/main_view/presentation/cubits/workspace_cubit.dart';
import 'package:sokoun_app/features/main_view/presentation/screens/view.dart';
import 'package:sokoun_app/features/main_view/presentation/widgets/home_bottom_navigation.dart';
import 'package:sokoun_app/features/main_view/presentation/workspace_navigation.dart';
import 'package:sokoun_app/features/owner/home/presentation/screens/owner_home_screen.dart';
import 'package:sokoun_app/features/owner/visits/imports.dart';
import 'package:sokoun_app/features/shared/auth/presentation/screens/login_screen.dart';
import 'package:sokoun_app/features/shared/chat/presentation/cubits/chat_unread_cubit.dart';
import 'package:sokoun_app/features/shared/notifications/presentation/notification_push_handler.dart';
import 'package:sokoun_app/features/tenant/home/presentation/screens/tenant_home_screen.dart';
import 'package:sokoun_app/shared_widgets/unsaved_changes_guard.dart';

import 'helpers/account_test_dependencies.dart';
import 'helpers/home_page_test_dependencies.dart';

final Map<String, Map<String, dynamic>> _translations = {};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  const MethodChannel preferences = MethodChannel(
    'plugins.flutter.io/shared_preferences',
  );
  const MethodChannel connectivity = MethodChannel(
    'dev.fluttercommunity.plus/connectivity',
  );
  const MethodChannel connectivityStatus = MethodChannel(
    'dev.fluttercommunity.plus/connectivity_status',
  );

  setUpAll(() async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          preferences,
          (call) async => call.method == 'getAll' ? <String, Object>{} : true,
        );
    await CacheStorage.init();
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
  });
  tearDown(() async {
    WorkspaceNavigation.clearPending();
    await injector.reset();
  });

  for (final String language in ['en', 'ar']) {
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
